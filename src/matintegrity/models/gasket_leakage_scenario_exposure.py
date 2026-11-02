"""Compose a computed gasket leakage-rate scenario snapshot into exposure amount."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Positive, RunContext, canonical_digest
from ..registry import ModelSpec


class GasketLeakageScenarioExposure(Contract):
    """Integrate a pinned finite scenario envelope under an explicit constant-state window."""

    assessment_id: str = Field(min_length=1)
    source_leakage_result: AssessmentResult
    source_leakage_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    exposure_start_time_s: float = Field(ge=0)
    exposure_duration_s: Positive
    constant_leakage_state_over_window_reviewed: bool
    time_basis_and_window_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def pinned_source_and_window(self):
        source = self.source_leakage_result
        if source.model_id != "fabrication.gasket_correlated_scenario_envelope" or source.status != "computed":
            raise ValueError("a computed correlated gasket leakage scenario envelope is required")
        expected_input = canonical_digest({
            "model_id": source.model_id,
            "model_version": source.model_version,
            "inputs": source.inputs,
            "context": source.context.model_dump(mode="json"),
        })
        if source.input_digest != expected_input:
            raise ValueError("source leakage result input/context digest mismatch")
        if canonical_digest(source.model_dump(mode="json")) != self.source_leakage_result_sha256:
            raise ValueError("source leakage result digest mismatch")
        if self.exposure_start_time_s != source.values.get("time_s"):
            raise ValueError("exposure start must match the evaluated leakage snapshot time")
        if not math.isfinite(self.exposure_start_time_s + self.exposure_duration_s):
            raise ValueError("exposure end time exceeds finite numeric support")
        if not source.values.get("scenario_results"):
            raise ValueError("source result lacks its finite scenario rate rows")
        scenario_rows = source.values["scenario_results"]
        if source.values.get("scenario_results_sha256") != canonical_digest(scenario_rows):
            raise ValueError("source scenario-row digest mismatch")
        scenario_ids = [row.get("scenario_id") for row in scenario_rows if isinstance(row, dict)]
        if len(scenario_ids) != len(scenario_rows) or len(set(scenario_ids)) != len(scenario_ids):
            raise ValueError("source scenario rows must have unique scenario IDs")
        if not all((self.constant_leakage_state_over_window_reviewed,
                    self.time_basis_and_window_reviewed, self.computational_use_authorized)):
            raise ValueError("constant-state, time-window and computational-use reviews are required")
        return self


def gasket_leakage_scenario_exposure(x: GasketLeakageScenarioExposure) -> Calculation:
    source = x.source_leakage_result
    rows = source.values["scenario_results"]
    input_digest = canonical_digest(x.model_dump(mode="json"))
    amounts = []
    for row in rows:
        rate = row.get("molar_leak_rate_mol_s")
        if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate < 0:
            return Calculation(status="out_of_scope", values={
                "assessment_id": x.assessment_id,
                "source_leakage_result_sha256": x.source_leakage_result_sha256,
                "input_digest": input_digest,
                "reason": "invalid_or_negative_scenario_rate",
                "completed_scenario_count": len(amounts),
            })
        amount = rate * x.exposure_duration_s
        if not math.isfinite(amount):
            return Calculation(status="out_of_scope", values={
                "assessment_id": x.assessment_id,
                "source_leakage_result_sha256": x.source_leakage_result_sha256,
                "input_digest": input_digest,
                "reason": "scenario_exposure_amount_overflow",
                "completed_scenario_count": len(amounts),
            })
        amounts.append({
            "scenario_id": row["scenario_id"],
            "snapshot_molar_leak_rate_mol_s": rate,
            "constant_state_exposure_amount_mol": amount,
        })
    minimum = min(amounts, key=lambda row: row["constant_state_exposure_amount_mol"])
    maximum = max(amounts, key=lambda row: row["constant_state_exposure_amount_mol"])
    return Calculation(values={
        "assessment_id": x.assessment_id,
        "asset_id": source.context.asset_id,
        "location_id": source.context.location_id,
        "time_basis": source.context.time_basis,
        "exposure_start_time_s": x.exposure_start_time_s,
        "exposure_end_time_s": x.exposure_start_time_s + x.exposure_duration_s,
        "exposure_duration_s": x.exposure_duration_s,
        "source_leakage_result_sha256": x.source_leakage_result_sha256,
        "source_input_digest": source.input_digest,
        "source_scenario_results_sha256": source.values["scenario_results_sha256"],
        "input_digest": input_digest,
        "scenario_exposure_amounts": amounts,
        "minimum_scenario_exposure_amount_mol": minimum["constant_state_exposure_amount_mol"],
        "minimum_witness_scenario_id": minimum["scenario_id"],
        "maximum_scenario_exposure_amount_mol": maximum["constant_state_exposure_amount_mol"],
        "maximum_witness_scenario_id": maximum["scenario_id"],
        "scenario_count": len(amounts),
        "meaning": "finite scenario amounts under a constant leakage snapshot over the explicitly reviewed duration; not a probability or time-varying forecast",
    }, notes=(
        "Each scenario molar leak rate is multiplied by the caller-supplied constant-state exposure duration.",
        "No pressure, contact, area, calibration or leakage-rate evolution between snapshot time and exposure end is inferred.",
    ))


def _validate_context(x: GasketLeakageScenarioExposure, context: RunContext) -> None:
    source_context = x.source_leakage_result.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        source_context.asset_id, source_context.location_id, source_context.time_basis
    ):
        raise ValueError("exposure RunContext must match the source leakage result identity and clock basis")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.gasket_leakage_scenario_exposure",
        GasketLeakageScenarioExposure,
        gasket_leakage_scenario_exposure,
        {"exposure_start_time_s": "s", "exposure_end_time_s": "s", "exposure_duration_s": "s",
         "scenario_exposure_amounts[].snapshot_molar_leak_rate_mol_s": "mol/s",
         "scenario_exposure_amounts[].constant_state_exposure_amount_mol": "mol",
         "minimum_scenario_exposure_amount_mol": "mol", "maximum_scenario_exposure_amount_mol": "mol"},
        (
            "Only a digest-pinned computed finite correlated leakage scenario snapshot is accepted.",
            "Molar leak rate is multiplied by an explicit duration under a caller-reviewed constant-state assumption; no transient state or probability is inferred.",
        ),
        ("caller_constant_state_gasket_leakage_scenario_exposure",),
        qualification="user_model",
        context_validator=_validate_context,
    )]

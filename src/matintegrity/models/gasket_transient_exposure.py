"""Integrate correlated gasket leakage scenarios between endpoint snapshots."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, RunContext, canonical_digest
from ..registry import ModelSpec


class GasketLeakageScenarioRateInterval(Contract):
    """Caller-reviewed linear-in-time reconstruction of matched scenario rates."""

    assessment_id: str = Field(min_length=1)
    start_result: AssessmentResult
    start_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    end_result: AssessmentResult
    end_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    maximum_scenario_count: int = Field(default=100_000, ge=1, le=1_000_000)
    scenario_identity_continuity_reviewed: bool
    piecewise_linear_rate_reconstruction_reviewed: bool
    time_window_and_basis_reviewed: bool
    computational_use_authorized: bool
    descriptive_rate_threshold_mol_s: float | None = Field(default=None, ge=0.0)
    descriptive_threshold_basis: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def endpoint_pair_is_coherent(self):
        if (self.descriptive_rate_threshold_mol_s is None) != (self.descriptive_threshold_basis is None):
            raise ValueError("a descriptive rate threshold and its basis must be supplied together")
        start, end = self.start_result, self.end_result
        for label, result, digest in (
            ("start", start, self.start_result_sha256),
            ("end", end, self.end_result_sha256),
        ):
            if result.model_id != "fabrication.gasket_correlated_scenario_envelope" or result.status != "computed":
                raise ValueError(f"{label} endpoint must be a computed gasket correlated scenario envelope")
            expected_input = canonical_digest({
                "model_id": result.model_id,
                "model_version": result.model_version,
                "inputs": result.inputs,
                "context": result.context.model_dump(mode="json"),
            })
            if result.input_digest != expected_input:
                raise ValueError(f"{label} endpoint input/context digest mismatch")
            if canonical_digest(result.model_dump(mode="json")) != digest:
                raise ValueError(f"{label} endpoint result digest mismatch")
            rows = result.values.get("scenario_results")
            if not isinstance(rows, list) or not rows or len(rows) > self.maximum_scenario_count:
                raise ValueError(f"{label} endpoint scenario count is empty or over the declared budget")
            if result.values.get("scenario_results_sha256") != canonical_digest(rows):
                raise ValueError(f"{label} endpoint scenario rows digest mismatch")
        if self.start_result.values.get("scenario_count") != self.end_result.values.get("scenario_count"):
            raise ValueError("both endpoints must report the same finite scenario count")
        sv, ev = self.start_result.values, self.end_result.values
        identical_fields = (
            "asset_id", "joint_id", "physical_scope_id",
            "scenario_provider_id", "scenario_provider_revision", "calibration_provider_id",
            "calibration_provider_revision", "calibration_record_sha256", "calibration_map_sha256",
            "node_ids", "usage_license_id",
        )
        for key in identical_fields:
            if sv.get(key) != ev.get(key):
                raise ValueError(f"endpoint leakage envelopes disagree on {key}")
        if (self.start_result.context.asset_id, self.start_result.context.location_id,
            self.start_result.context.time_basis) != (
            self.end_result.context.asset_id, self.end_result.context.location_id,
            self.end_result.context.time_basis,
        ):
            raise ValueError("endpoint RunContexts must share asset, location and time basis")
        t0, t1 = sv.get("time_s"), ev.get("time_s")
        if (isinstance(t0, bool) or not isinstance(t0, (int, float)) or not math.isfinite(t0)
                or isinstance(t1, bool) or not isinstance(t1, (int, float)) or not math.isfinite(t1)
                or t1 <= t0):
            raise ValueError("endpoint snapshot times must be finite and strictly increasing")
        if not math.isfinite(t1 - t0):
            raise ValueError("endpoint time difference exceeds finite numeric support")
        if not all((self.scenario_identity_continuity_reviewed,
                    self.piecewise_linear_rate_reconstruction_reviewed,
                    self.time_window_and_basis_reviewed, self.computational_use_authorized)):
            raise ValueError("scenario continuity, rate reconstruction, time basis and use reviews are required")
        start_rows, end_rows = _rows_by_scenario(sv["scenario_results"]), _rows_by_scenario(ev["scenario_results"])
        if set(start_rows) != set(end_rows):
            raise ValueError("the same scenario IDs must be present at both time endpoints")
        node_ids = sv.get("node_ids")
        if not isinstance(node_ids, list) or not node_ids:
            raise ValueError("endpoint results require a nonempty ordered node ID list")
        for scenario_id in start_rows:
            left, right = start_rows[scenario_id], end_rows[scenario_id]
            if left.get("calibration_flux_sha256") != right.get("calibration_flux_sha256"):
                raise ValueError(f"scenario {scenario_id} calibration realization differs between endpoints")
            for row in (left, right):
                rate = row.get("molar_leak_rate_mol_s")
                nodes = row.get("node_responses")
                if (isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate < 0
                        or not isinstance(nodes, list)
                        or [node.get("node_id") for node in nodes if isinstance(node, dict)] != node_ids):
                    raise ValueError(f"scenario {scenario_id} has invalid rate or node response identity")
        return self


def _rows_by_scenario(rows: list[dict]) -> dict[str, dict]:
    ids = [row.get("scenario_id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or any(not isinstance(value, str) or not value for value in ids):
        raise ValueError("scenario rows require nonempty string IDs")
    if len(set(ids)) != len(ids):
        raise ValueError("scenario row IDs must be unique")
    return {row["scenario_id"]: row for row in rows}


def integrate_gasket_leakage_scenario_rate_interval(x: GasketLeakageScenarioRateInterval) -> Calculation:
    """Integrate each matched endpoint rate exactly for a linear time reconstruction."""
    left_values, right_values = x.start_result.values, x.end_result.values
    start_rows = _rows_by_scenario(left_values["scenario_results"])
    end_rows = _rows_by_scenario(right_values["scenario_results"])
    t0, t1 = float(left_values["time_s"]), float(right_values["time_s"])
    duration = t1 - t0
    amounts = []
    for scenario_id in sorted(start_rows):
        q0 = float(start_rows[scenario_id]["molar_leak_rate_mol_s"])
        q1 = float(end_rows[scenario_id]["molar_leak_rate_mol_s"])
        amount = (q0 * 0.5 + q1 * 0.5) * duration
        if not math.isfinite(amount):
            return Calculation(status="out_of_scope", values={
                "assessment_id": x.assessment_id,
                "start_result_sha256": x.start_result_sha256,
                "end_result_sha256": x.end_result_sha256,
                "completed_scenario_count": len(amounts),
                "reason": "scenario_integral_exceeded_finite_numeric_support",
            })
        amounts.append({
            "scenario_id": scenario_id,
            "start_rate_mol_s": q0,
            "end_rate_mol_s": q1,
            "linear_reconstruction_interval_amount_mol": amount,
            "start_scenario_row_sha256": canonical_digest(start_rows[scenario_id]),
            "end_scenario_row_sha256": canonical_digest(end_rows[scenario_id]),
        })
        if x.descriptive_rate_threshold_mol_s is not None:
            threshold = x.descriptive_rate_threshold_mol_s
            low, high = sorted((q0, q1))
            if high <= threshold:
                above_duration, excess = 0.0, 0.0
            elif low >= threshold:
                above_duration = duration
                excess = ((q0 - threshold) * 0.5 + (q1 - threshold) * 0.5) * duration
            else:
                above_duration = duration * ((high - threshold) / (high - low))
                excess = (high - threshold) * 0.5 * above_duration
            amounts[-1].update({
                "strictly_above_threshold_duration_s": above_duration,
                "integrated_positive_rate_excess_mol": excess,
                "above_threshold_interval_start_s": (
                    None if above_duration == 0.0 else t0 if q0 > threshold else t1 - above_duration
                ),
                "above_threshold_interval_end_s": (
                    None if above_duration == 0.0 else t1 if q1 > threshold else t0 + above_duration
                ),
            })
    minimum = min(amounts, key=lambda row: row["linear_reconstruction_interval_amount_mol"])
    maximum = max(amounts, key=lambda row: row["linear_reconstruction_interval_amount_mol"])
    request_digest = canonical_digest(x.model_dump(mode="json"))
    return Calculation(values={
        "assessment_id": x.assessment_id,
        "asset_id": x.start_result.context.asset_id,
        "location_id": x.start_result.context.location_id,
        "time_basis": x.start_result.context.time_basis,
        "interval_start_time_s": t0,
        "interval_end_time_s": t1,
        "interval_duration_s": duration,
        "start_result_sha256": x.start_result_sha256,
        "end_result_sha256": x.end_result_sha256,
        "start_input_digest": x.start_result.input_digest,
        "end_input_digest": x.end_result.input_digest,
        "start_scenario_results_sha256": left_values["scenario_results_sha256"],
        "end_scenario_results_sha256": right_values["scenario_results_sha256"],
        "request_sha256": request_digest,
        "scenario_amounts": amounts,
        "minimum_scenario_amount_mol": minimum["linear_reconstruction_interval_amount_mol"],
        "minimum_witness_scenario_id": minimum["scenario_id"],
        "maximum_scenario_amount_mol": maximum["linear_reconstruction_interval_amount_mol"],
        "maximum_witness_scenario_id": maximum["scenario_id"],
        "scenario_count": len(amounts),
        "descriptive_rate_threshold_mol_s": x.descriptive_rate_threshold_mol_s,
        "descriptive_threshold_basis": x.descriptive_threshold_basis,
        "reconstruction": "piecewise_linear_molar_leakage_rate_between_two_matched_snapshots; exact trapezoid integral",
        "probability_inferred": False,
        "meaning": "finite scenario amounts over one endpoint interval only; neither scenario probabilities nor unsampled transient extrema are inferred",
    }, notes=(
        "The trapezoid integral is exact only for the explicitly caller-reviewed linear-in-time leakage-rate reconstruction between the two supplied snapshots.",
        "Scenario continuity is caller-reviewed. No interpolation of pressure, contact state, gasket relaxation or calibration response is performed.",
    ))


def _validate_context(x: GasketLeakageScenarioRateInterval, context: RunContext) -> None:
    source = x.start_result.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        source.asset_id, source.location_id, source.time_basis
    ):
        raise ValueError("integration RunContext must match both endpoint asset/location/time identities")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.gasket_leakage_scenario_rate_interval",
        GasketLeakageScenarioRateInterval,
        integrate_gasket_leakage_scenario_rate_interval,
        {"interval_start_time_s": "s", "interval_end_time_s": "s", "interval_duration_s": "s",
         "scenario_amounts[].linear_reconstruction_interval_amount_mol": "mol",
         "scenario_amounts[].strictly_above_threshold_duration_s": "s",
         "scenario_amounts[].integrated_positive_rate_excess_mol": "mol",
         "scenario_amounts[].above_threshold_interval_start_s": "s",
         "scenario_amounts[].above_threshold_interval_end_s": "s",
         "minimum_scenario_amount_mol": "mol", "maximum_scenario_amount_mol": "mol"},
        (
            "Only two digest-pinned computed envelopes with identical joint/scenario/calibration identity and node order are accepted.",
            "Each matched scenario rate is integrated with a trapezoid that is exact for the explicitly reviewed linear-in-time rate reconstruction; no scenario probability or unsampled transient bound is inferred.",
        ),
        ("caller_piecewise_linear_gasket_leakage_scenario_rate_interval",),
        qualification="user_model",
        context_validator=_validate_context,
    )]

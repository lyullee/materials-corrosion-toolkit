"""Correlation-preserving finite scenario envelope for computed multiaxial life results."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, RunContext, canonical_digest
from ..registry import ModelSpec


class MultiaxialLifeScenario(Contract):
    """One complete, already-computed multiaxial life scenario and its lineage."""

    scenario_id: str = Field(min_length=1)
    life_result: AssessmentResult
    life_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def pinned_computed_campaign(self):
        result = self.life_result
        if result.model_id != "fatigue.multiaxial_life_campaign" or result.status != "computed":
            raise ValueError("each scenario must contain a computed fatigue.multiaxial_life_campaign result")
        expected_input = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input:
            raise ValueError("scenario result input/context digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != self.life_result_sha256:
            raise ValueError("scenario result digest mismatch")
        if not isinstance(result.values.get("life_result"), dict):
            raise ValueError("campaign result must retain its nested life result")
        life = result.values["life_result"]
        cycles = life.get("cycles_to_failure")
        if cycles is None and isinstance(life.get("values"), dict):
            cycles = life["values"].get("cycles_to_failure")
        if life.get("status") != "computed" or isinstance(cycles, bool) or not isinstance(cycles, (int, float)):
            raise ValueError("scenario life must have a computed finite cycle count")
        if not math.isfinite(cycles) or cycles <= 0:
            raise ValueError("scenario life cycle count must be finite and positive")
        calibration_sha = result.values.get("calibration_sha256")
        factor_sha = result.values.get("factor_result_sha256")
        if not isinstance(calibration_sha, str) or len(calibration_sha) != 64:
            raise ValueError("campaign result must expose its calibration digest")
        if not isinstance(factor_sha, str) or len(factor_sha) != 64:
            raise ValueError("campaign result must expose its plane-factor digest")
        return self


class MultiaxialLifeScenarioEnvelope(Contract):
    """Return extrema among complete correlated finite scenarios only."""

    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    scenario_provider_id: str = Field(min_length=1)
    scenario_provider_revision: str = Field(min_length=1)
    scenarios_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scenarios: tuple[MultiaxialLifeScenario, ...] = Field(min_length=1, max_length=10000)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_license_id: str = Field(min_length=1)
    joint_scenario_dependence_reviewed: bool
    scenario_coverage_and_bounds_reviewed: bool
    scenario_lineage_and_calibration_match_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_scenario_set(self):
        ids = [row.scenario_id for row in self.scenarios]
        if len(set(ids)) != len(ids):
            raise ValueError("scenario IDs must be unique")
        payload = [row.model_dump(mode="json") for row in self.scenarios]
        if canonical_digest(payload) != self.scenarios_sha256:
            raise ValueError("ordered finite scenario set digest mismatch")
        if not any(row.source_id == self.scenario_provider_id and row.sha256 == self.scenarios_sha256
                   for row in self.evidence):
            raise ValueError("scenario set digest must be attributed to matching provider Evidence")
        if not any(row.license_id == self.usage_license_id for row in self.usage_rights_evidence):
            raise ValueError("usage-rights Evidence must identify the declared license/rights basis")
        identities = set()
        for row in self.scenarios:
            result = row.life_result
            values = result.values
            inputs = result.inputs
            history = inputs.get("history", {})
            identities.add((
                result.model_id,
                result.model_version,
                values.get("calibration_sha256"),
                inputs.get("calibration_material_condition_id"),
                history.get("material_condition_id"),
                inputs.get("minimum_valid_cycles"),
                inputs.get("maximum_valid_cycles"),
                result.context.asset_id,
                result.context.location_id,
                result.context.time_basis,
            ))
            if (result.context.asset_id, result.context.location_id, result.context.time_basis) != (
                self.asset_id, self.location_id, self.time_basis
            ):
                raise ValueError("scenario RunContext asset/location/time basis differs from envelope")
        if len(identities) != 1:
            raise ValueError("scenarios must share model revision, calibration, material condition, cycle support and context")
        if not all((self.joint_scenario_dependence_reviewed,
                    self.scenario_coverage_and_bounds_reviewed,
                    self.scenario_lineage_and_calibration_match_reviewed,
                    self.usage_rights_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("dependence, coverage, lineage, rights and use reviews are required")
        return self


def evaluate_multiaxial_life_scenario_envelope(request: MultiaxialLifeScenarioEnvelope) -> Calculation:
    """Compute finite-scenario life extrema without inventing a distribution or continuous bound."""
    rows = []
    for scenario in request.scenarios:
        result = scenario.life_result
        nested = result.values["life_result"]
        cycles = nested.get("cycles_to_failure")
        if cycles is None and isinstance(nested.get("values"), dict):
            cycles = nested["values"].get("cycles_to_failure")
        rows.append({
            "scenario_id": scenario.scenario_id,
            "life_result_sha256": scenario.life_result_sha256,
            "input_digest": result.input_digest,
            "calibration_sha256": result.values["calibration_sha256"],
            "factor_result_sha256": result.values["factor_result_sha256"],
            "plane_id": nested.get("plane_id"),
            "cycles_to_failure": cycles,
        })
    minimum = min(rows, key=lambda row: row["cycles_to_failure"])
    maximum = max(rows, key=lambda row: row["cycles_to_failure"])
    return Calculation(values={
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "time_basis": request.time_basis,
        "scenario_provider_id": request.scenario_provider_id,
        "scenario_provider_revision": request.scenario_provider_revision,
        "scenarios_sha256": request.scenarios_sha256,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "calibration_sha256": rows[0]["calibration_sha256"],
        "scenario_lives": rows,
        "scenario_count": len(rows),
        "minimum_cycles_to_failure": minimum["cycles_to_failure"],
        "minimum_witness_scenario_id": minimum["scenario_id"],
        "maximum_cycles_to_failure": maximum["cycles_to_failure"],
        "maximum_witness_scenario_id": maximum["scenario_id"],
        "meaning": "finite caller-supplied joint scenario envelope only; not a probability, confidence interval or continuous parameter bound",
    }, notes=(
        "Each scenario is a complete independently computed multiaxial-life AssessmentResult with matching calibration and context lineage.",
        "Scenario correlations are retained by evaluating complete rows. No independent parameter-wise recombination, probability assignment or extrapolation is performed.",
    ))


def _validate_context(request: MultiaxialLifeScenarioEnvelope, context: RunContext) -> None:
    if (context.asset_id, context.location_id, context.time_basis) != (
        request.asset_id, request.location_id, request.time_basis
    ):
        raise ValueError("envelope RunContext must match declared asset/location/time basis")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.multiaxial_life_scenario_envelope",
        MultiaxialLifeScenarioEnvelope,
        evaluate_multiaxial_life_scenario_envelope,
        {"minimum_cycles_to_failure": "cycle", "maximum_cycles_to_failure": "cycle"},
        (
            "The envelope consumes only digest-pinned computed results from the registered multiaxial critical-plane life campaign.",
            "All scenarios share a calibration/material/support/context basis and remain complete joint cases; results are finite-set extrema, not probabilities or continuous bounds.",
        ),
        ("caller_correlated_finite_multiaxial_life_scenario_envelope",),
        qualification="user_model",
        context_validator=_validate_context,
    )]

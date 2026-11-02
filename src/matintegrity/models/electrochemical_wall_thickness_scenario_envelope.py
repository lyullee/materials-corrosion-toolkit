"""Finite joint-scenario envelope for computed electrochemical wall histories."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, RunContext, canonical_digest
from ..registry import ModelSpec


class ElectrochemicalWallThicknessScenario(Contract):
    """One complete computed wall-thickness history and its immutable identity."""

    scenario_id: str = Field(min_length=1)
    wall_result: AssessmentResult
    wall_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def pinned_computed_result(self):
        result = self.wall_result
        if (result.model_id != "integration.electrochemical_metal_loss_wall_thickness_history"
                or result.status != "computed"):
            raise ValueError("scenario must contain a computed electrochemical wall-thickness history result")
        expected_input = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input:
            raise ValueError("wall-history scenario input/context digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != self.wall_result_sha256:
            raise ValueError("wall-history scenario result digest mismatch")
        history = result.values.get("wall_thickness_history")
        if not isinstance(history, list) or len(history) < 2:
            raise ValueError("wall-history scenario must contain baseline and at least one calculated knot")
        for row in history:
            if not isinstance(row, dict):
                raise ValueError("wall-history knots must be objects")
            for key in ("time_s", "remaining_thickness_m", "required_thickness_m", "margin_m"):
                value = row.get(key)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ValueError(f"wall-history knot requires finite {key}")
        if result.values.get("projection_sha256") != canonical_digest(history):
            raise ValueError("wall-history projection digest mismatch")
        return self


class ElectrochemicalWallThicknessScenarioEnvelope(Contract):
    """Pointwise extrema among complete, caller-enumerated joint scenarios."""

    schema_version: Literal["matintegrity.electrochemical_wall_thickness_scenario_envelope.v1"] = (
        "matintegrity.electrochemical_wall_thickness_scenario_envelope.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    baseline_id: str = Field(min_length=1)
    baseline_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scenario_provider_id: str = Field(min_length=1)
    scenario_provider_revision: str = Field(min_length=1)
    scenarios_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scenarios: tuple[ElectrochemicalWallThicknessScenario, ...] = Field(min_length=1, max_length=10000)
    scenario_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_license_id: str = Field(min_length=1)
    complete_scenario_set_reviewed: bool
    joint_scenario_dependence_reviewed: bool
    baseline_and_scope_match_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_scenario_set(self):
        ids = [row.scenario_id for row in self.scenarios]
        if len(set(ids)) != len(ids):
            raise ValueError("scenario IDs must be unique")
        serialized = [row.model_dump(mode="json") for row in self.scenarios]
        if canonical_digest(serialized) != self.scenarios_sha256:
            raise ValueError("ordered joint-scenario manifest digest mismatch")
        if not any(row.source_id == self.scenario_provider_id and row.sha256 == self.scenarios_sha256
                   for row in self.scenario_evidence):
            raise ValueError("scenario provider Evidence must pin the exact ordered scenario manifest")
        if not any(row.license_id == self.usage_license_id for row in self.usage_rights_evidence):
            raise ValueError("rights Evidence must identify the declared use-rights basis")

        reference_identity = None
        reference_times = None
        for scenario in self.scenarios:
            result = scenario.wall_result
            values = result.values
            history = values["wall_thickness_history"]
            identity = (
                result.model_id,
                result.model_version,
                result.context.asset_id,
                result.context.location_id,
                result.context.time_basis,
                values.get("physical_scope_id"),
                values.get("material_condition_id"),
                values.get("baseline_id"),
                values.get("baseline_record_sha256"),
                tuple(row.get("required_thickness_m") for row in history),
            )
            if (result.context.asset_id, result.context.location_id, result.context.time_basis) != (
                self.asset_id, self.location_id, self.time_basis
            ):
                raise ValueError("scenario context asset/location/time basis differs from the envelope")
            if (values.get("physical_scope_id"), values.get("material_condition_id"),
                    values.get("baseline_id"), values.get("baseline_record_sha256")) != (
                    self.physical_scope_id, self.material_condition_id,
                    self.baseline_id, self.baseline_record_sha256):
                raise ValueError("scenario physical/material scope and measured baseline must match the envelope")
            times = tuple(row["time_s"] for row in history)
            if reference_times is None:
                reference_times = times
            elif times != reference_times:
                raise ValueError("all scenarios must have the exact same ordered time knots")
            if reference_identity is None:
                reference_identity = identity
            elif identity != reference_identity:
                raise ValueError("scenarios must share model revision, scope, baseline and required-thickness history")
        if not all((
            self.complete_scenario_set_reviewed,
            self.joint_scenario_dependence_reviewed,
            self.baseline_and_scope_match_reviewed,
            self.usage_rights_reviewed,
            self.computational_use_authorized,
        )):
            raise ValueError("scenario coverage/dependence, common baseline/scope, rights and use reviews are required")
        return self


def evaluate_electrochemical_wall_thickness_scenario_envelope(
    request: ElectrochemicalWallThicknessScenarioEnvelope,
) -> Calculation:
    """Report knotwise finite-set thickness/margin extrema without assigning probability."""
    scenario_rows = []
    for scenario in request.scenarios:
        result = scenario.wall_result
        scenario_rows.append({
            "scenario_id": scenario.scenario_id,
            "wall_result_sha256": scenario.wall_result_sha256,
            "input_digest": result.input_digest,
            "metal_loss_result_sha256": result.values["metal_loss_result_sha256"],
            "projection_sha256": result.values["projection_sha256"],
            "history": result.values["wall_thickness_history"],
        })
    knotwise = []
    for index, time_s in enumerate(scenario_rows[0]["history"]):
        rows = []
        for scenario in scenario_rows:
            knot = scenario["history"][index]
            rows.append({
                "scenario_id": scenario["scenario_id"],
                "remaining_thickness_m": knot["remaining_thickness_m"],
                "margin_m": knot["margin_m"],
            })
        minimum_thickness = min(rows, key=lambda row: row["remaining_thickness_m"])
        maximum_thickness = max(rows, key=lambda row: row["remaining_thickness_m"])
        minimum_margin = min(rows, key=lambda row: row["margin_m"])
        maximum_margin = max(rows, key=lambda row: row["margin_m"])
        knotwise.append({
            "time_s": time_s["time_s"],
            "minimum_remaining_thickness_m": minimum_thickness["remaining_thickness_m"],
            "minimum_thickness_witness_scenario_id": minimum_thickness["scenario_id"],
            "maximum_remaining_thickness_m": maximum_thickness["remaining_thickness_m"],
            "maximum_thickness_witness_scenario_id": maximum_thickness["scenario_id"],
            "minimum_margin_m": minimum_margin["margin_m"],
            "minimum_margin_witness_scenario_id": minimum_margin["scenario_id"],
            "maximum_margin_m": maximum_margin["margin_m"],
            "maximum_margin_witness_scenario_id": maximum_margin["scenario_id"],
        })
    values = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "time_basis": request.time_basis,
        "physical_scope_id": request.physical_scope_id,
        "material_condition_id": request.material_condition_id,
        "baseline_id": request.baseline_id,
        "baseline_record_sha256": request.baseline_record_sha256,
        "scenario_provider_id": request.scenario_provider_id,
        "scenario_provider_revision": request.scenario_provider_revision,
        "scenarios_sha256": request.scenarios_sha256,
        "scenario_count": len(scenario_rows),
        "scenario_results": [
            {key: row[key] for key in (
                "scenario_id", "wall_result_sha256", "input_digest",
                "metal_loss_result_sha256", "projection_sha256",
            )}
            for row in scenario_rows
        ],
        "knotwise_extrema": knotwise,
        "meaning": "pointwise extrema over the finite caller-supplied scenario set only; extrema may have different witnesses at different knots; no probability or continuous bound",
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
    }
    return Calculation(values=values, notes=(
        "Each scenario is a complete, digest-pinned electrochemical wall-thickness AssessmentResult sharing the same physical/material scope, baseline and exact ordered time knots.",
        "Extrema are computed independently at each supplied knot; witness scenario IDs are reported separately for thickness and margin. No interpolation, scenario weighting, probability assignment or unsampled bound is inferred.",
        "This envelope is not a corrosion-life prediction, first-passage probability, fitness-for-service decision or acceptance result.",
    ))


def _validate_context(request: ElectrochemicalWallThicknessScenarioEnvelope, context: RunContext) -> None:
    if (context.asset_id, context.location_id, context.time_basis) != (
        request.asset_id, request.location_id, request.time_basis
    ):
        raise ValueError("envelope RunContext must match declared asset/location/time basis")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.electrochemical_wall_thickness_scenario_envelope",
        ElectrochemicalWallThicknessScenarioEnvelope,
        evaluate_electrochemical_wall_thickness_scenario_envelope,
        {
            "knotwise_extrema[].time_s": "s",
            "knotwise_extrema[].minimum_remaining_thickness_m": "m",
            "knotwise_extrema[].maximum_remaining_thickness_m": "m",
            "knotwise_extrema[].minimum_margin_m": "m",
            "knotwise_extrema[].maximum_margin_m": "m",
        },
        (
            "Consumes only complete digest-pinned computed wall-thickness history AssessmentResults on one common physical/material scope and measured baseline.",
            "Every scenario must share the exact ordered time knots and required-thickness history; scenario dependence is preserved by evaluating complete rows.",
            "Knotwise extrema over the finite supplied set are deterministic pointwise bounds only. No scenario probability, weighting, temporal interpolation or continuous parameter bound is inferred.",
        ),
        ("electrochemical_metal_loss_wall_thickness_finite_scenario_envelope",),
        qualification="user_model",
        context_validator=_validate_context,
    )]

"""Project reviewed electrochemical metal loss onto a measured wall baseline."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import (
    AssessmentResult,
    Calculation,
    Contract,
    Evidence,
    Positive,
    RunContext,
    canonical_digest,
)
from ..registry import ModelSpec
from .erosion_corrosion import ErosionCorrosionWallThicknessBaseline


class ElectrochemicalWallThicknessHistory(Contract):
    """Deterministic gross-anodic loss projection for one reviewed wall area."""

    schema_version: Literal["matintegrity.electrochemical_wall_thickness_history.v1"] = (
        "matintegrity.electrochemical_wall_thickness_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    metal_loss_result: AssessmentResult
    metal_loss_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    baseline: ErosionCorrosionWallThicknessBaseline
    assessed_wall_area_m2: Positive
    effective_density_kg_m3: Positive
    wall_area_relative_tolerance: float = Field(ge=0.0, le=0.1)
    density_provider_id: str = Field(min_length=1)
    density_provider_revision: str = Field(min_length=1)
    density_record_id: str = Field(min_length=1)
    density_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    density_evidence: tuple[Evidence, ...] = Field(min_length=1)
    material_to_effective_density_reviewed: bool
    complete_reaction_set_reviewed: bool
    common_wall_area_mapping_reviewed: bool
    anodic_only_noncrediting_projection_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_source_and_scope(self):
        result = self.metal_loss_result
        if result.model_id != "integration.electrochemical_partial_current_metal_loss" or result.status != "computed":
            raise ValueError("a computed electrochemical metal-loss AssessmentResult is required")
        expected_input_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input_digest:
            raise ValueError("metal-loss input digest does not match request and context")
        if canonical_digest(result.model_dump(mode="json")) != self.metal_loss_result_sha256:
            raise ValueError("metal-loss result digest mismatch")
        if not any(row.source_id == self.density_provider_id and row.sha256 == self.density_record_sha256
                   for row in self.density_evidence):
            raise ValueError("effective density provider and record digest must match density Evidence")
        intervals = result.values.get("interval_metal_loss")
        if not isinstance(intervals, list) or not intervals:
            raise ValueError("metal-loss result must contain at least one interval")
        mappings = result.values.get("reaction_to_metal_mapping")
        if not isinstance(mappings, list) or not mappings:
            raise ValueError("metal-loss result must expose its selected reaction mappings")
        reaction_ids = tuple(row.get("reaction_id") for row in mappings if isinstance(row, dict))
        if len(reaction_ids) != len(mappings) or len(set(reaction_ids)) != len(reaction_ids):
            raise ValueError("upstream reaction mapping identities must be unique")
        if self.baseline.baseline_time_s != intervals[0].get("start_time_s"):
            raise ValueError("wall baseline time must equal the first metal-loss interval start")
        if (self.baseline.asset_id, self.baseline.location_id, self.baseline.physical_scope_id,
                self.baseline.material_condition_id) != (
                result.values.get("asset_id"), result.values.get("location_id"),
                result.values.get("physical_scope_id"), result.values.get("material_condition_id")):
            raise ValueError("wall baseline physical and material scope must match the metal-loss result")
        previous_end = intervals[0].get("start_time_s")
        for interval in intervals:
            start, end = interval.get("start_time_s"), interval.get("end_time_s")
            if (isinstance(start, bool) or not isinstance(start, (int, float)) or not math.isfinite(start)
                    or isinstance(end, bool) or not isinstance(end, (int, float)) or not math.isfinite(end)
                    or end <= start or start != previous_end):
                raise ValueError("metal-loss intervals must have finite, positive and contiguous time bounds")
            rows = interval.get("reaction_metal_loss")
            if not isinstance(rows, list) or tuple(row.get("reaction_id") for row in rows) != reaction_ids:
                raise ValueError("every interval must contain the exact ordered selected reaction set")
            for row in rows:
                area = row.get("exposed_area_m2")
                mass = row.get("anodic_mass_loss_kg")
                if (isinstance(area, bool) or not isinstance(area, (int, float)) or not math.isfinite(area)
                        or area <= 0.0 or isinstance(mass, bool) or not isinstance(mass, (int, float))
                        or not math.isfinite(mass) or mass < 0.0):
                    raise ValueError("reaction exposed areas and gross anodic masses must be finite and nonnegative")
                relative = abs(area - self.assessed_wall_area_m2) / self.assessed_wall_area_m2
                if relative > self.wall_area_relative_tolerance:
                    raise ValueError("upstream reaction exposed area is incompatible with the assessed wall area")
            previous_end = end
        return self


def electrochemical_wall_thickness_history(x: ElectrochemicalWallThicknessHistory) -> Calculation:
    upstream = x.metal_loss_result
    gate = {
        "material_to_effective_density_reviewed": x.material_to_effective_density_reviewed,
        "complete_reaction_set_reviewed": x.complete_reaction_set_reviewed,
        "common_wall_area_mapping_reviewed": x.common_wall_area_mapping_reviewed,
        "anodic_only_noncrediting_projection_reviewed": x.anodic_only_noncrediting_projection_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    missing = [name for name, value in gate.items() if not value]
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": upstream.values["asset_id"],
        "location_id": upstream.values["location_id"],
        "physical_scope_id": upstream.values["physical_scope_id"],
        "material_condition_id": upstream.values["material_condition_id"],
        "baseline_id": x.baseline.baseline_id,
        "baseline_record_sha256": x.baseline.record_sha256,
        "metal_loss_result_sha256": x.metal_loss_result_sha256,
        "metal_loss_history_sha256": upstream.values["metal_loss_history_sha256"],
        "assessed_wall_area_m2": x.assessed_wall_area_m2,
        "effective_density_kg_m3": x.effective_density_kg_m3,
        "density_provider_id": x.density_provider_id,
        "density_provider_revision": x.density_provider_revision,
        "density_record_id": x.density_record_id,
        "density_record_sha256": x.density_record_sha256,
        "reviews": gate,
    }
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    thickness = x.baseline.measured_thickness_m
    required = x.baseline.required_thickness_m
    cumulative_loss = 0.0
    output = [{"time_s": x.baseline.baseline_time_s, "gross_anodic_loss_m": 0.0,
               "remaining_thickness_m": thickness, "required_thickness_m": required,
               "margin_m": thickness - required}]
    rows_out = []
    first_crossing = None
    for interval in upstream.values["interval_metal_loss"]:
        gross_mass = math.fsum(row["anodic_mass_loss_kg"] for row in interval["reaction_metal_loss"])
        loss = gross_mass / (x.effective_density_kg_m3 * x.assessed_wall_area_m2)
        next_thickness = thickness - loss
        if not all(math.isfinite(value) for value in (gross_mass, loss, next_thickness)) or loss < 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "computed_prefix": rows_out,
                "failed_interval_start_s": interval["start_time_s"],
                "failed_interval_end_s": interval["end_time_s"],
                "failure_reason": "wall_thickness_projection_outside_finite_numeric_support",
            })
        margin = next_thickness - required
        row = {"start_time_s": interval["start_time_s"], "end_time_s": interval["end_time_s"],
               "gross_anodic_mass_loss_kg": gross_mass, "gross_anodic_loss_m": loss,
               "remaining_thickness_m": next_thickness, "required_thickness_m": required,
               "margin_m": margin}
        rows_out.append(row)
        cumulative_loss += loss
        output.append({"time_s": interval["end_time_s"], "gross_anodic_loss_m": cumulative_loss,
                       "remaining_thickness_m": next_thickness, "required_thickness_m": required,
                       "margin_m": margin})
        if first_crossing is None and output[-2]["margin_m"] > 0.0 and margin <= 0.0:
            first_crossing = {"interval_start_s": interval["start_time_s"],
                              "interval_end_s": interval["end_time_s"],
                              "bracket_only": True}
        thickness = next_thickness
    return Calculation(values=base | {
        "wall_thickness_history": output,
        "interval_projection": rows_out,
        "baseline_already_below_required": x.baseline.measured_thickness_m <= required,
        "first_limit_crossing_bracket": first_crossing,
        "projection_sha256": canonical_digest(output),
    }, notes=(
        "The projection sums caller-selected gross anodic metal loss, converts it using the reviewed effective density and common wall area, and subtracts from a digest-linked measured baseline.",
        "Cathodic metal equivalents and signed net transfer are not credited against wall loss. A crossing is localized to a supplied interval only; no within-interval crossing time is interpolated.",
        "This deterministic history is limited to the supplied electrochemical horizon and is not a corrosion-rate qualification, remaining-life forecast, acceptance decision or failure probability.",
    ))


def _same_wall_context(x: ElectrochemicalWallThicknessHistory, context: RunContext) -> None:
    upstream = x.metal_loss_result.context
    if (context.asset_id, context.location_id, context.time_basis) != (
            upstream.asset_id, upstream.location_id, upstream.time_basis):
        raise ValueError("wall-thickness projection context must match upstream asset, location and time basis")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.electrochemical_metal_loss_wall_thickness_history",
        ElectrochemicalWallThicknessHistory,
        electrochemical_wall_thickness_history,
        {
            "assessed_wall_area_m2": "m2", "effective_density_kg_m3": "kg/m3",
            "wall_thickness_history[].time_s": "s",
            "wall_thickness_history[].gross_anodic_loss_m": "m",
            "wall_thickness_history[].remaining_thickness_m": "m",
            "wall_thickness_history[].required_thickness_m": "m",
            "wall_thickness_history[].margin_m": "m",
            "interval_projection[].start_time_s": "s", "interval_projection[].end_time_s": "s",
            "interval_projection[].gross_anodic_mass_loss_kg": "kg",
            "interval_projection[].gross_anodic_loss_m": "m",
            "interval_projection[].remaining_thickness_m": "m",
            "interval_projection[].required_thickness_m": "m",
            "interval_projection[].margin_m": "m",
        },
        (
            "Requires a computed digest-pinned electrochemical metal-loss result and an Evidence-linked measured wall-thickness baseline at the first interval start.",
            "Every selected reaction must be represented in every interval, and each upstream exposed area must match the caller-reviewed common assessed wall area within an explicit tolerance.",
            "Gross anodic mass only is converted with the caller's Evidence-linked effective density; cathodic equivalents and signed net mass do not offset wall loss.",
            "The result reports deterministic supplied-horizon thickness margins and interval crossing brackets only; no rate extrapolation, life prediction, acceptance or probability is produced.",
        ),
        ("electrochemical_metal_loss_to_wall_thickness_history",),
        qualification="user_model",
        context_validator=_same_wall_context,
    )]

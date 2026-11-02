"""Narrow forming-geometry summaries under an explicit bend convention."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class FormingGeometryRecord(Contract):
    record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    forming_mode: Literal["cold", "hot"]
    forming_direction_id: str = Field(min_length=1)
    geometry_convention: Literal["mid_thickness_neutral_axis_circular_arc"]
    strain_convention: Literal["engineering", "true"]
    original_thickness_m: Positive | None = None
    final_thickness_m: Positive | None = None
    inside_radius_m: Nonnegative | None = None
    bend_angle_rad: Positive | None = None
    thickness_standard_uncertainty_m: Positive | None = None
    radius_standard_uncertainty_m: Positive | None = None
    angle_standard_uncertainty_rad: Positive | None = None
    record_status: Literal["valid", "missing", "invalid"]
    missing_or_invalid_basis: str | None = None
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def status_fields(self):
        measurements = (
            self.original_thickness_m,
            self.final_thickness_m,
            self.inside_radius_m,
            self.bend_angle_rad,
            self.thickness_standard_uncertainty_m,
            self.radius_standard_uncertainty_m,
            self.angle_standard_uncertainty_rad,
        )
        if self.record_status == "valid":
            if any(value is None for value in measurements):
                raise ValueError("valid forming records require geometry and uncertainty fields")
            if self.missing_or_invalid_basis is not None:
                raise ValueError("valid forming records cannot carry a missing basis")
        elif any(value is not None for value in measurements) or not self.missing_or_invalid_basis:
            raise ValueError("missing or invalid forming records require a basis and no measurements")
        return self


class FormingGeometryHistory(Contract):
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    strain_convention: Literal["engineering", "true"]
    records: tuple[FormingGeometryRecord, ...] = Field(min_length=1)
    minimum_supported_radius_to_original_thickness: Nonnegative
    maximum_supported_radius_to_original_thickness: Positive
    maximum_supported_bend_angle_rad: Positive
    caller_maximum_tensile_surface_strain: Positive | None = None
    caller_maximum_thinning_measure: Positive | None = None
    material_condition_mode_and_direction_reviewed: bool
    original_final_thickness_and_geometry_reviewed: bool
    geometry_and_strain_conventions_reviewed: bool
    measurement_uncertainty_and_record_status_reviewed: bool
    specimen_source_identity_and_digests_reviewed: bool
    support_and_caller_threshold_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def identities_and_support(self):
        if (
            self.maximum_supported_radius_to_original_thickness
            < self.minimum_supported_radius_to_original_thickness
        ):
            raise ValueError("forming radius/thickness support must be ordered")
        identifiers = [row.record_id for row in self.records]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("forming geometry record IDs must be unique")
        for row in self.records:
            if row.material_condition_id != self.material_condition_id:
                raise ValueError("all forming records must share material condition")
            if row.strain_convention != self.strain_convention:
                raise ValueError("engineering and true strain conventions cannot be mixed")
        return self


def forming_geometry_history(x: FormingGeometryHistory) -> Calculation:
    review_fields = (
        "material_condition_mode_and_direction_reviewed",
        "original_final_thickness_and_geometry_reviewed",
        "geometry_and_strain_conventions_reviewed",
        "measurement_uncertainty_and_record_status_reviewed",
        "specimen_source_identity_and_digests_reviewed",
        "support_and_caller_threshold_authority_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    excluded = [row.record_id for row in x.records if row.record_status != "valid"]
    valid = [row for row in x.records if row.record_status == "valid"]
    if missing_reviews or not valid:
        return Calculation(
            status="needs_data",
            values={
                "history_id": x.history_id,
                "missing_reviews": missing_reviews,
                "excluded_missing_or_invalid_record_ids": excluded,
            },
            notes=("Forming summary is withheld until reviewed valid geometry records are available.",),
        )
    rows = []
    outside = []
    for record in valid:
        ratio = record.inside_radius_m / record.original_thickness_m
        engineering_surface = 1.0 / (2.0 * (record.inside_radius_m / record.final_thickness_m) + 1.0)
        reasons = []
        if x.strain_convention == "engineering":
            tensile = engineering_surface
            compressive = -engineering_surface
            thinning = (record.original_thickness_m - record.final_thickness_m) / record.original_thickness_m
        else:
            tensile = math.log1p(engineering_surface)
            if record.inside_radius_m == 0.0:
                compressive = None
                reasons.append("zero_inside_radius_true_compressive_strain_singular")
            else:
                # Evaluate log(2r/(2r+t)) without subtracting a rounded strain from one.
                log_ratio = (
                    math.log(2.0) + math.log(record.inside_radius_m) - math.log(record.final_thickness_m)
                )
                compressive = (
                    -math.log1p(math.exp(-log_ratio))
                    if log_ratio > 0.0
                    else log_ratio - math.log1p(math.exp(log_ratio))
                )
            thinning = math.log(record.original_thickness_m / record.final_thickness_m)
        if not (
            x.minimum_supported_radius_to_original_thickness
            <= ratio
            <= x.maximum_supported_radius_to_original_thickness
        ):
            reasons.append("radius_to_original_thickness")
        if record.bend_angle_rad > x.maximum_supported_bend_angle_rad:
            reasons.append("bend_angle")
        if reasons:
            outside.append(record.record_id)
        rows.append(
            {
                "record_id": record.record_id,
                "physical_specimen_id": record.physical_specimen_id,
                "source_group_id": record.source_group_id,
                "forming_mode": record.forming_mode,
                "forming_direction_id": record.forming_direction_id,
                "radius_to_original_thickness": ratio,
                "tensile_surface_strain": tensile,
                "compressive_surface_strain": compressive,
                "thinning_measure": thinning,
                "tensile_surface_strain_margin": (
                    x.caller_maximum_tensile_surface_strain - tensile
                    if x.caller_maximum_tensile_surface_strain is not None
                    else None
                ),
                "thinning_measure_margin": (
                    x.caller_maximum_thinning_measure - thinning
                    if x.caller_maximum_thinning_measure is not None
                    else None
                ),
                "outside_support_reasons": reasons,
            }
        )
    values = {
        "history_id": x.history_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "component_id": x.component_id,
        "strain_convention": x.strain_convention,
        "record_summaries": rows,
        "outside_support_record_ids": outside,
        "excluded_missing_or_invalid_record_ids": excluded,
    }
    notes = (
        "Surface strain uses only the declared circular-arc, mid-thickness neutral-axis geometry; no forming simulation is inferred.",
        "Engineering and true strain definitions are never mixed, and caller thresholds produce signed margins only.",
        "No code limit, heat-treatment requirement, acceptance, remaining life or failure probability is produced.",
    )
    if outside:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("forming geometry history asset and location must match the run context")

    return [
        ModelSpec(
            "fabrication.forming_geometry_history",
            FormingGeometryHistory,
            forming_geometry_history,
            {
                "history_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "component_id": "1",
                "strain_convention": "1",
                "record_summaries": "mixed",
                "outside_support_record_ids": "1",
                "excluded_missing_or_invalid_record_ids": "1",
            },
            (
                "Caller-reviewed circular-arc bend geometry with a mid-thickness neutral axis.",
                "Original/final thickness, inside radius, angle and uncertainties retain specimen and source identity.",
                "Thresholds are optional caller values used only for signed arithmetic margins.",
            ),
            ("reviewed_forming_geometry_strain_summary",),
            version="1.0.1",
            context_validator=same_identity,
        )
    ]

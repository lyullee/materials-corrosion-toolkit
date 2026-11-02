"""Caller-segmented thermal-spray cross-section geometry summaries."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class CrossSectionFrameCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    x_scale_m_per_px: Positive
    y_scale_m_per_px: Positive
    x_scale_expanded_uncertainty_m_per_px: Nonnegative
    y_scale_expanded_uncertainty_m_per_px: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_record(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid cross-section frame calibration requires a basis")
        return self


class ThicknessPoint(Contract):
    point_id: str = Field(min_length=1)
    x_coordinate: Nonnegative
    y_coordinate: Nonnegative
    coordinate_unit_token: Literal["px", "m"]
    thickness_m: Positive
    expanded_uncertainty_m: Nonnegative


class ThicknessTraverse(Contract):
    traverse_id: str = Field(min_length=1)
    points: tuple[ThicknessPoint, ...] = Field(min_length=2)
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_valid_points(self):
        point_ids = [row.point_id for row in self.points]
        if len(point_ids) != len(set(point_ids)):
            raise ValueError("thermal-spray thickness point identifiers must be unique")
        if len({row.coordinate_unit_token for row in self.points}) != 1:
            raise ValueError("one thickness traverse must use one coordinate unit")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid thickness traverse requires a basis")
        return self


class SegmentedPoreGeometry(Contract):
    pore_id: str = Field(min_length=1)
    area_value: Positive
    area_unit_token: Literal["px^2", "m^2"]
    coordinate_unit_token: Literal["px", "m"]
    minimum_x: Nonnegative
    maximum_x: Nonnegative
    minimum_y: Nonnegative
    maximum_y: Nonnegative
    touches_field_edge: bool
    overlaps_pore_ids: tuple[str, ...] = ()
    segmentation_method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_valid_geometry(self):
        if self.maximum_x <= self.minimum_x or self.maximum_y <= self.minimum_y:
            raise ValueError("segmented pore bounds must have positive width and height")
        if self.pore_id in self.overlaps_pore_ids:
            raise ValueError("a pore cannot overlap itself")
        if len(self.overlaps_pore_ids) != len(set(self.overlaps_pore_ids)):
            raise ValueError("overlap pore identifiers must be unique")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid pore geometry requires a basis")
        return self


class ThermalSprayCrossSectionField(Contract):
    field_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    physical_location_id: str = Field(min_length=1)
    layer_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    spray_batch_id: str = Field(min_length=1)
    process_condition_id: str = Field(min_length=1)
    field_basis: Literal["calibrated_image", "si_measurement"]
    coordinate_frame_id: str = Field(min_length=1)
    frame_calibration_id: str | None = None
    width_px: int | None = Field(default=None, ge=1)
    height_px: int | None = Field(default=None, ge=1)
    width_m: Positive | None = None
    height_m: Positive | None = None
    declared_field_area_m2: Positive
    thickness_traverses: tuple[ThicknessTraverse, ...] = Field(min_length=1)
    pores: tuple[SegmentedPoreGeometry, ...] = ()
    field_method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_field(self):
        traverse_ids = [row.traverse_id for row in self.thickness_traverses]
        pore_ids = [row.pore_id for row in self.pores]
        if len(traverse_ids) != len(set(traverse_ids)):
            raise ValueError("thermal-spray traverse identifiers must be unique per field")
        if len(pore_ids) != len(set(pore_ids)):
            raise ValueError("thermal-spray pore identifiers must be unique per field")
        if self.field_basis == "calibrated_image":
            if self.frame_calibration_id is None or self.width_px is None or self.height_px is None:
                raise ValueError("calibrated image fields require calibration and pixel dimensions")
            if self.width_m is not None or self.height_m is not None:
                raise ValueError("calibrated image fields cannot also declare SI dimensions")
            expected_coordinate, expected_area = "px", "px^2"
        else:
            if self.width_m is None or self.height_m is None:
                raise ValueError("SI measurement fields require metre dimensions")
            if (
                self.frame_calibration_id is not None
                or self.width_px is not None
                or self.height_px is not None
            ):
                raise ValueError("SI measurement fields cannot carry pixel calibration fields")
            expected_coordinate, expected_area = "m", "m^2"
        if any(
            point.coordinate_unit_token != expected_coordinate
            for traverse in self.thickness_traverses
            for point in traverse.points
        ):
            raise ValueError("thickness coordinates must match the field coordinate basis")
        if any(
            pore.coordinate_unit_token != expected_coordinate or pore.area_unit_token != expected_area
            for pore in self.pores
        ):
            raise ValueError("pore coordinate and area units must match the field basis")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid thermal-spray field requires a basis")
        return self


class ThermalSprayCrossSectionSummary(Contract):
    summary_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    coating_system_id: str = Field(min_length=1)
    layer_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    spray_batch_id: str = Field(min_length=1)
    process_condition_id: str = Field(min_length=1)
    frame_calibrations: tuple[CrossSectionFrameCalibration, ...] = ()
    fields: tuple[ThermalSprayCrossSectionField, ...] = Field(min_length=3)
    field_area_relative_tolerance: Nonnegative
    specimen_location_layer_and_substrate_reviewed: bool
    spray_batch_and_process_condition_reviewed: bool
    frame_calibration_and_field_area_reviewed: bool
    thickness_traverses_units_uncertainty_and_bounds_reviewed: bool
    caller_segmentation_pore_area_edge_and_overlap_reviewed: bool
    specimen_source_and_independence_partitions_reviewed: bool
    method_provider_revision_and_digests_reviewed: bool
    missing_invalid_and_support_policy_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_partitioned_fields(self):
        calibration_ids = [row.calibration_id for row in self.frame_calibrations]
        field_ids = [row.field_id for row in self.fields]
        if len(calibration_ids) != len(set(calibration_ids)):
            raise ValueError("cross-section frame calibration identifiers must be unique")
        if len(field_ids) != len(set(field_ids)):
            raise ValueError("cross-section field identifiers must be unique")
        if {row.partition for row in self.fields} != {"calibration", "holdout"}:
            raise ValueError("thermal-spray fields require calibration and holdout partitions")
        for attribute, label in (
            ("physical_specimen_id", "physical specimen"),
            ("source_group_id", "source group"),
            ("independence_group_id", "independence group"),
        ):
            calibration = {getattr(row, attribute) for row in self.fields if row.partition == "calibration"}
            holdout = {getattr(row, attribute) for row in self.fields if row.partition == "holdout"}
            if calibration & holdout:
                raise ValueError(f"thermal-spray {label} cannot cross calibration and holdout")
        return self


def thermal_spray_cross_section_summary(x: ThermalSprayCrossSectionSummary) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "specimen_location_layer_and_substrate_reviewed",
            "spray_batch_and_process_condition_reviewed",
            "frame_calibration_and_field_area_reviewed",
            "thickness_traverses_units_uncertainty_and_bounds_reviewed",
            "caller_segmentation_pore_area_edge_and_overlap_reviewed",
            "specimen_source_and_independence_partitions_reviewed",
            "method_provider_revision_and_digests_reviewed",
            "missing_invalid_and_support_policy_reviewed",
        )
        if not getattr(x, name)
    ]
    calibration_by_id = {row.calibration_id: row for row in x.frame_calibrations}
    invalid_calibration_ids = [row.calibration_id for row in x.frame_calibrations if not row.record_valid]
    invalid_field_ids = [row.field_id for row in x.fields if not row.record_valid]
    invalid_traverse_ids = [
        row.traverse_id for field in x.fields for row in field.thickness_traverses if not row.record_valid
    ]
    invalid_pore_ids = [row.pore_id for field in x.fields for row in field.pores if not row.record_valid]
    identity_mismatch_field_ids = [
        row.field_id
        for row in x.fields
        if row.layer_id != x.layer_id
        or row.substrate_condition_id != x.substrate_condition_id
        or row.spray_batch_id != x.spray_batch_id
        or row.process_condition_id != x.process_condition_id
    ]
    unlinked_field_ids = [
        row.field_id
        for row in x.fields
        if row.field_basis == "calibrated_image"
        and (
            row.frame_calibration_id not in calibration_by_id
            or (
                row.frame_calibration_id in calibration_by_id
                and row.coordinate_frame_id != calibration_by_id[row.frame_calibration_id].coordinate_frame_id
            )
        )
    ]
    overlapping_pore_ids = sorted(
        {
            pore_id
            for field in x.fields
            for pore in field.pores
            for pore_id in (pore.pore_id, *pore.overlaps_pore_ids)
            if pore.overlaps_pore_ids
        }
    )
    duplicate_geometry_ids = []
    for field in x.fields:
        seen = {}
        for pore in field.pores:
            key = (
                pore.area_value,
                pore.area_unit_token,
                pore.minimum_x,
                pore.maximum_x,
                pore.minimum_y,
                pore.maximum_y,
            )
            if key in seen:
                duplicate_geometry_ids.extend([seen[key], pore.pore_id])
            else:
                seen[key] = pore.pore_id
    if (
        missing_reviews
        or invalid_calibration_ids
        or invalid_field_ids
        or invalid_traverse_ids
        or invalid_pore_ids
        or identity_mismatch_field_ids
        or unlinked_field_ids
        or overlapping_pore_ids
        or duplicate_geometry_ids
    ):
        return Calculation(
            status="needs_data",
            values={
                "summary_id": x.summary_id,
                "missing_reviews": missing_reviews,
                "invalid_calibration_ids": invalid_calibration_ids,
                "invalid_field_ids": invalid_field_ids,
                "invalid_traverse_ids": invalid_traverse_ids,
                "invalid_pore_ids": invalid_pore_ids,
                "identity_mismatch_field_ids": identity_mismatch_field_ids,
                "unlinked_field_ids": unlinked_field_ids,
                "overlapping_pore_ids": overlapping_pore_ids,
                "duplicate_pore_geometry_ids": sorted(set(duplicate_geometry_ids)),
            },
            notes=("Reviewed nonoverlapping, nonduplicate and valid caller geometry is required.",),
        )

    out_of_bounds_ids = []
    area_mismatch_field_ids = []
    field_rows = []
    for field in x.fields:
        if field.field_basis == "calibrated_image":
            calibration = calibration_by_id[field.frame_calibration_id]
            width, height = float(field.width_px), float(field.height_px)
            calculated_area = width * calibration.x_scale_m_per_px * height * calibration.y_scale_m_per_px
            area_scale = calibration.x_scale_m_per_px * calibration.y_scale_m_per_px
        else:
            width, height = field.width_m, field.height_m
            calculated_area = width * height
            area_scale = 1.0
        if (
            abs(calculated_area - field.declared_field_area_m2) / field.declared_field_area_m2
            > x.field_area_relative_tolerance
        ):
            area_mismatch_field_ids.append(field.field_id)
        thickness_values = []
        for traverse in field.thickness_traverses:
            for point in traverse.points:
                if point.x_coordinate > width or point.y_coordinate > height:
                    out_of_bounds_ids.append(point.point_id)
                thickness_values.append(point.thickness_m)
        pore_area_m2 = 0.0
        edge_pore_ids = []
        for pore in field.pores:
            if pore.maximum_x > width or pore.maximum_y > height:
                out_of_bounds_ids.append(pore.pore_id)
            pore_area_m2 += pore.area_value * area_scale
            if pore.touches_field_edge:
                edge_pore_ids.append(pore.pore_id)
        porosity_fraction = pore_area_m2 / field.declared_field_area_m2
        if porosity_fraction > 1 + 1e-12:
            out_of_bounds_ids.append(f"{field.field_id}:pore_area_exceeds_field")
        field_rows.append(
            {
                "field_id": field.field_id,
                "partition": field.partition,
                "physical_specimen_id": field.physical_specimen_id,
                "declared_field_area_m2": field.declared_field_area_m2,
                "calculated_field_area_m2": calculated_area,
                "thickness_point_count": len(thickness_values),
                "mean_thickness_m": sum(thickness_values) / len(thickness_values),
                "minimum_thickness_m": min(thickness_values),
                "maximum_thickness_m": max(thickness_values),
                "segmented_pore_count": len(field.pores),
                "segmented_pore_area_m2": pore_area_m2,
                "area_porosity_fraction": porosity_fraction,
                "edge_pore_ids": edge_pore_ids,
            }
        )
    if area_mismatch_field_ids or out_of_bounds_ids:
        return Calculation(
            status="needs_data",
            values={
                "summary_id": x.summary_id,
                "area_mismatch_field_ids": area_mismatch_field_ids,
                "out_of_bounds_geometry_ids": out_of_bounds_ids,
                "field_rows": field_rows,
            },
            notes=(
                "Field-area consistency and all caller geometry bounds must be resolved before aggregation.",
            ),
        )

    calibration_areas = [
        row["declared_field_area_m2"] for row in field_rows if row["partition"] == "calibration"
    ]
    outside_support_holdout_ids = [
        row["field_id"]
        for row in field_rows
        if row["partition"] == "holdout"
        and not min(calibration_areas) <= row["declared_field_area_m2"] <= max(calibration_areas)
    ]

    def partition_summary(partition):
        selected = [row for row in field_rows if row["partition"] == partition]
        thickness = [row["mean_thickness_m"] for row in selected]
        porosity = [row["area_porosity_fraction"] for row in selected]

        def sample_repeatability(values):
            if len(values) < 2:
                return None
            mean = sum(values) / len(values)
            return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))

        return {
            "partition": partition,
            "field_count": len(selected),
            "field_ids": [row["field_id"] for row in selected],
            "mean_of_field_mean_thickness_m": sum(thickness) / len(thickness),
            "minimum_field_mean_thickness_m": min(thickness),
            "maximum_field_mean_thickness_m": max(thickness),
            "field_mean_thickness_repeatability_m": sample_repeatability(thickness),
            "mean_area_porosity_fraction": sum(porosity) / len(porosity),
            "minimum_area_porosity_fraction": min(porosity),
            "maximum_area_porosity_fraction": max(porosity),
            "area_porosity_repeatability_fraction": sample_repeatability(porosity),
        }

    return Calculation(
        status="out_of_scope" if outside_support_holdout_ids else "computed",
        values={
            "summary_id": x.summary_id,
            "physical_scope_id": x.physical_scope_id,
            "coating_system_id": x.coating_system_id,
            "field_rows": field_rows,
            "partition_summaries": [
                partition_summary("calibration"),
                partition_summary("holdout"),
            ],
            "outside_calibration_field_area_support_holdout_ids": outside_support_holdout_ids,
        },
        notes=(
            "Pore geometry and thickness points are caller-supplied; this model performs no image segmentation or pore classification.",
            "Area porosity is the sum of reviewed nonoverlapping caller pore areas divided by the declared calibrated field area.",
            "Thickness and porosity summaries do not infer bond strength, specification compliance, service life or failure probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError(
                "thermal-spray cross-section summary asset and location must match the run context"
            )

    return [
        ModelSpec(
            "fabrication.thermal_spray_cross_section_summary",
            ThermalSprayCrossSectionSummary,
            thermal_spray_cross_section_summary,
            {
                "summary_id": "1",
                "physical_scope_id": "1",
                "coating_system_id": "1",
                "field_rows": "mixed",
                "partition_summaries": "mixed",
                "outside_calibration_field_area_support_holdout_ids": "1",
            },
            (
                "Caller-supplied thickness points and segmented pore areas share one calibrated field geometry.",
                "Calibration and holdout specimen, source and independence groups are disjoint.",
                "Duplicate, overlap, bounds, edge and missing/invalid states remain explicit.",
            ),
            ("authored_partitioned_thermal_spray_cross_section_geometry_summary",),
            context_validator=same_identity,
        )
    ]

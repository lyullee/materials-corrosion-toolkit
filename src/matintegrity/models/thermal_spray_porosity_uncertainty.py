"""Uncertainty summaries for caller-segmented thermal-spray porosity fields."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Nonnegative, Positive
from ..registry import ModelSpec


class PorosityPixelAreaCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    pixel_area_scale_m2_per_px2: Positive
    pixel_area_scale_standard_uncertainty_m2_per_px2: Nonnegative
    minimum_supported_field_area_px2: Positive
    maximum_supported_field_area_px2: Positive
    maximum_supported_single_pore_area_px2: Positive
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_valid_support(self):
        if self.maximum_supported_field_area_px2 <= self.minimum_supported_field_area_px2:
            raise ValueError("pixel-area calibration field support must have positive width")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid pixel-area calibration requires a basis")
        return self


class CallerSegmentedPoreArea(Contract):
    pore_id: str = Field(min_length=1)
    segmented_area_px2: Positive
    segmented_area_standard_uncertainty_px2: Nonnegative
    area_unit_token: Literal["px^2"]
    touches_field_edge: bool
    segmentation_method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_record(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid caller-segmented pore area requires a basis")
        return self


class PorosityReferenceEvidence(Contract):
    reference_id: str = Field(min_length=1)
    porosity_area_fraction: Fraction
    porosity_standard_uncertainty_fraction: Nonnegative
    minimum_supported_field_area_m2: Positive
    maximum_supported_field_area_m2: Positive
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    source_lineage_id: str = Field(min_length=1)
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_valid_support(self):
        if self.maximum_supported_field_area_m2 <= self.minimum_supported_field_area_m2:
            raise ValueError("porosity reference field-area support must have positive width")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid porosity reference requires a basis")
        return self


class ThermalSprayPorosityField(Contract):
    field_id: str = Field(min_length=1)
    replicate_group_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    spatial_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    physical_location_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    width_px: int = Field(ge=1)
    height_px: int = Field(ge=1)
    pixel_area_calibration_id: str = Field(min_length=1)
    layer_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    spray_batch_id: str = Field(min_length=1)
    process_condition_id: str = Field(min_length=1)
    pores: tuple[CallerSegmentedPoreArea, ...] = ()
    reference: PorosityReferenceEvidence | None = None
    field_provider_id: str = Field(min_length=1)
    field_provider_revision: str = Field(min_length=1)
    field_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_complete_field(self):
        pore_ids = [row.pore_id for row in self.pores]
        if len(pore_ids) != len(set(pore_ids)):
            raise ValueError("caller-segmented pore identifiers must be unique per field")
        if self.partition == "holdout" and self.reference is None:
            raise ValueError("holdout porosity fields require independent reference evidence")
        return self


class ThermalSprayPorosityUncertainty(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    coating_system_id: str = Field(min_length=1)
    layer_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    spray_batch_id: str = Field(min_length=1)
    process_condition_id: str = Field(min_length=1)
    calibrations: tuple[PorosityPixelAreaCalibration, ...] = Field(min_length=1)
    fields: tuple[ThermalSprayPorosityField, ...] = Field(min_length=3)
    minimum_replicates_per_group: int = Field(ge=2)
    expanded_uncertainty_coverage_factor: Positive
    specimen_field_layer_and_process_identity_reviewed: bool
    pixel_area_calibration_units_uncertainty_and_support_reviewed: bool
    caller_segmentation_area_uncertainty_edge_status_and_digests_reviewed: bool
    replicate_and_spatial_group_independence_reviewed: bool
    specimen_source_independence_spatial_and_partition_groups_reviewed: bool
    holdout_reference_lineage_digest_uncertainty_and_support_reviewed: bool
    uncertainty_propagation_and_coverage_factor_reviewed: bool
    missing_invalid_and_out_of_support_policy_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_partitioned_fields(self):
        calibration_ids = [row.calibration_id for row in self.calibrations]
        field_ids = [row.field_id for row in self.fields]
        if len(calibration_ids) != len(set(calibration_ids)):
            raise ValueError("porosity pixel-area calibration identifiers must be unique")
        if len(field_ids) != len(set(field_ids)):
            raise ValueError("thermal-spray porosity field identifiers must be unique")
        if {row.partition for row in self.fields} != {"calibration", "holdout"}:
            raise ValueError("porosity uncertainty requires calibration and holdout fields")
        for attribute, label in (
            ("physical_specimen_id", "physical specimen"),
            ("source_group_id", "source group"),
            ("independence_group_id", "independence group"),
            ("spatial_group_id", "spatial group"),
            ("replicate_group_id", "replicate group"),
        ):
            calibration = {getattr(row, attribute) for row in self.fields if row.partition == "calibration"}
            holdout = {getattr(row, attribute) for row in self.fields if row.partition == "holdout"}
            if calibration & holdout:
                raise ValueError(f"porosity {label} cannot cross calibration and holdout")
        return self


def _sample_sd(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def thermal_spray_porosity_uncertainty(x: ThermalSprayPorosityUncertainty) -> Calculation:
    review_names = (
        "specimen_field_layer_and_process_identity_reviewed",
        "pixel_area_calibration_units_uncertainty_and_support_reviewed",
        "caller_segmentation_area_uncertainty_edge_status_and_digests_reviewed",
        "replicate_and_spatial_group_independence_reviewed",
        "specimen_source_independence_spatial_and_partition_groups_reviewed",
        "holdout_reference_lineage_digest_uncertainty_and_support_reviewed",
        "uncertainty_propagation_and_coverage_factor_reviewed",
        "missing_invalid_and_out_of_support_policy_reviewed",
    )
    missing_reviews = [name for name in review_names if not getattr(x, name)]
    calibration_by_id = {row.calibration_id: row for row in x.calibrations}
    invalid_calibration_ids = [row.calibration_id for row in x.calibrations if not row.record_valid]
    invalid_pore_ids = [pore.pore_id for field in x.fields for pore in field.pores if not pore.record_valid]
    invalid_reference_ids = [
        field.reference.reference_id
        for field in x.fields
        if field.reference is not None and not field.reference.record_valid
    ]
    unlinked_field_ids = [
        field.field_id
        for field in x.fields
        if field.pixel_area_calibration_id not in calibration_by_id
        or (
            field.pixel_area_calibration_id in calibration_by_id
            and field.coordinate_frame_id
            != calibration_by_id[field.pixel_area_calibration_id].coordinate_frame_id
        )
    ]
    identity_mismatch_field_ids = [
        field.field_id
        for field in x.fields
        if field.layer_id != x.layer_id
        or field.substrate_condition_id != x.substrate_condition_id
        or field.spray_batch_id != x.spray_batch_id
        or field.process_condition_id != x.process_condition_id
    ]
    group_counts: dict[tuple[str, str], int] = {}
    for field in x.fields:
        key = (field.partition, field.replicate_group_id)
        group_counts[key] = group_counts.get(key, 0) + 1
    insufficient_replicate_groups = [
        f"{partition}:{group_id}"
        for (partition, group_id), count in sorted(group_counts.items())
        if count < x.minimum_replicates_per_group
    ]
    if (
        missing_reviews
        or invalid_calibration_ids
        or invalid_pore_ids
        or invalid_reference_ids
        or unlinked_field_ids
        or identity_mismatch_field_ids
        or insufficient_replicate_groups
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "invalid_calibration_ids": invalid_calibration_ids,
                "invalid_pore_ids": invalid_pore_ids,
                "invalid_reference_ids": invalid_reference_ids,
                "unlinked_field_ids": unlinked_field_ids,
                "identity_mismatch_field_ids": identity_mismatch_field_ids,
                "insufficient_replicate_groups": insufficient_replicate_groups,
            },
            notes=("Reviewed, linked field evidence and sufficient independent replicates are required.",),
        )

    outside_calibration_support_ids: list[str] = []
    outside_reference_support_ids: list[str] = []
    field_rows = []
    for field in x.fields:
        calibration = calibration_by_id[field.pixel_area_calibration_id]
        field_area_px2 = float(field.width_px * field.height_px)
        field_area_m2 = field_area_px2 * calibration.pixel_area_scale_m2_per_px2
        field_area_standard_uncertainty_m2 = (
            field_area_px2 * calibration.pixel_area_scale_standard_uncertainty_m2_per_px2
        )
        pore_area_px2 = sum(pore.segmented_area_px2 for pore in field.pores)
        if not (
            calibration.minimum_supported_field_area_px2
            <= field_area_px2
            <= calibration.maximum_supported_field_area_px2
        ):
            outside_calibration_support_ids.append(field.field_id)
        outside_calibration_support_ids.extend(
            f"{field.field_id}:{pore.pore_id}"
            for pore in field.pores
            if pore.segmented_area_px2 > calibration.maximum_supported_single_pore_area_px2
        )
        if pore_area_px2 > field_area_px2:
            return Calculation(
                status="needs_data",
                values={
                    "assessment_id": x.assessment_id,
                    "pore_area_exceeds_field_ids": [field.field_id],
                },
                notes=("Caller-segmented pore area cannot exceed its field area.",),
            )
        pore_area_m2 = pore_area_px2 * calibration.pixel_area_scale_m2_per_px2
        segmentation_u_px2 = math.sqrt(
            sum(pore.segmented_area_standard_uncertainty_px2**2 for pore in field.pores)
        )
        segmentation_u_fraction = segmentation_u_px2 / field_area_px2
        fraction = pore_area_px2 / field_area_px2
        reference_error = None
        reference_combined_u = None
        standardized_error = None
        if field.reference is not None:
            reference = field.reference
            if not (
                reference.minimum_supported_field_area_m2
                <= field_area_m2
                <= reference.maximum_supported_field_area_m2
            ):
                outside_reference_support_ids.append(field.field_id)
            reference_error = fraction - reference.porosity_area_fraction
            reference_combined_u = math.sqrt(
                segmentation_u_fraction**2 + reference.porosity_standard_uncertainty_fraction**2
            )
            standardized_error = reference_error / reference_combined_u if reference_combined_u > 0 else None
        field_rows.append(
            {
                "field_id": field.field_id,
                "partition": field.partition,
                "replicate_group_id": field.replicate_group_id,
                "physical_specimen_id": field.physical_specimen_id,
                "spatial_group_id": field.spatial_group_id,
                "field_area_px2": field_area_px2,
                "field_area_m2": field_area_m2,
                "field_area_standard_uncertainty_m2": field_area_standard_uncertainty_m2,
                "segmented_pore_count": len(field.pores),
                "segmented_pore_area_px2": pore_area_px2,
                "segmented_pore_area_m2": pore_area_m2,
                "porosity_area_fraction": fraction,
                "segmentation_standard_uncertainty_fraction": segmentation_u_fraction,
                "edge_pore_ids": [pore.pore_id for pore in field.pores if pore.touches_field_edge],
                "reference_id": field.reference.reference_id if field.reference else None,
                "reference_error_fraction": reference_error,
                "reference_combined_standard_uncertainty_fraction": reference_combined_u,
                "reference_standardized_error": standardized_error,
            }
        )

    group_rows = []
    for partition, group_id in sorted(group_counts):
        selected = [
            row
            for row in field_rows
            if row["partition"] == partition and row["replicate_group_id"] == group_id
        ]
        fractions = [row["porosity_area_fraction"] for row in selected]
        segmentation_u = math.sqrt(
            sum(row["segmentation_standard_uncertainty_fraction"] ** 2 for row in selected)
        ) / len(selected)
        repeatability_sd = _sample_sd(fractions)
        repeatability_u = repeatability_sd / math.sqrt(len(selected))
        combined_u = math.sqrt(segmentation_u**2 + repeatability_u**2)
        group_rows.append(
            {
                "partition": partition,
                "replicate_group_id": group_id,
                "field_ids": [row["field_id"] for row in selected],
                "field_count": len(selected),
                "mean_porosity_area_fraction": sum(fractions) / len(fractions),
                "minimum_porosity_area_fraction": min(fractions),
                "maximum_porosity_area_fraction": max(fractions),
                "replicate_repeatability_standard_deviation_fraction": repeatability_sd,
                "replicate_repeatability_standard_uncertainty_fraction": repeatability_u,
                "mean_segmentation_standard_uncertainty_fraction": segmentation_u,
                "combined_standard_uncertainty_fraction": combined_u,
                "expanded_uncertainty_fraction": (x.expanded_uncertainty_coverage_factor * combined_u),
            }
        )

    holdout_errors = [
        row["reference_error_fraction"]
        for row in field_rows
        if row["partition"] == "holdout" and row["reference_error_fraction"] is not None
    ]
    holdout_standardized = [
        abs(row["reference_standardized_error"])
        for row in field_rows
        if row["partition"] == "holdout" and row["reference_standardized_error"] is not None
    ]
    status = (
        "out_of_scope" if outside_calibration_support_ids or outside_reference_support_ids else "computed"
    )
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "physical_scope_id": x.physical_scope_id,
            "coating_system_id": x.coating_system_id,
            "field_rows": field_rows,
            "replicate_group_rows": group_rows,
            "holdout_diagnostics": {
                "field_count": len(holdout_errors),
                "mean_error_fraction": sum(holdout_errors) / len(holdout_errors),
                "root_mean_squared_error_fraction": math.sqrt(
                    sum(value**2 for value in holdout_errors) / len(holdout_errors)
                ),
                "mean_absolute_standardized_error": (
                    sum(holdout_standardized) / len(holdout_standardized) if holdout_standardized else None
                ),
            },
            "outside_pixel_area_calibration_support_ids": outside_calibration_support_ids,
            "outside_reference_support_field_ids": outside_reference_support_ids,
        },
        notes=(
            "Pore areas and their uncertainty are caller/provider supplied; no image segmentation or pore classification is performed.",
            "A shared pixel-area scale cancels in the area fraction; its uncertainty remains reported for physical SI areas rather than double-counted in the fraction.",
            "Summaries do not infer bond strength, acceptance, service life or failure probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError(
                "thermal-spray porosity uncertainty asset and location must match the run context"
            )

    return [
        ModelSpec(
            "fabrication.thermal_spray_porosity_uncertainty",
            ThermalSprayPorosityUncertainty,
            thermal_spray_porosity_uncertainty,
            {
                "assessment_id": "1",
                "physical_scope_id": "1",
                "coating_system_id": "1",
                "field_rows": "mixed",
                "replicate_group_rows": "mixed",
                "holdout_diagnostics": "mixed",
            },
            (
                "Caller-segmented pixel areas are converted with reviewed pixel-area calibration evidence.",
                "Replicate, specimen, source, independence and spatial groups remain partition-disjoint.",
                "Independent holdout references retain lineage, digests, uncertainty and field-area support.",
            ),
            ("authored_partitioned_thermal_spray_porosity_uncertainty",),
            context_validator=same_identity,
        )
    ]

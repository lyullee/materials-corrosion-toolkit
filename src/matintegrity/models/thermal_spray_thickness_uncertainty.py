"""Repeated thermal-spray thickness summaries with calibration uncertainty."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class ThicknessInstrumentCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    instrument_id: str = Field(min_length=1)
    instrument_configuration_id: str = Field(min_length=1)
    additive_bias_correction_m: float
    calibration_standard_uncertainty_m: Nonnegative
    minimum_supported_thickness_m: Positive
    maximum_supported_thickness_m: Positive
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_valid_calibration(self):
        if self.maximum_supported_thickness_m <= self.minimum_supported_thickness_m:
            raise ValueError("thickness-calibration support must have positive width")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid thickness calibration requires a basis")
        return self


class RepeatedThicknessMeasurement(Contract):
    measurement_id: str = Field(min_length=1)
    calibration_id: str = Field(min_length=1)
    measured_thickness_m: Positive
    thickness_unit_token: Literal["m"]
    measurement_standard_uncertainty_m: Nonnegative
    method_id: str = Field(min_length=1)
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
            raise ValueError("an invalid repeated thickness measurement requires a basis")
        return self


class ThermalSprayThicknessLocation(Contract):
    location_record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    spatial_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    physical_location_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    x_coordinate_m: float
    y_coordinate_m: float
    layer_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    spray_batch_id: str = Field(min_length=1)
    process_condition_id: str = Field(min_length=1)
    measurements: tuple[RepeatedThicknessMeasurement, ...] = Field(min_length=2)
    reference_thickness_m: Positive | None = None
    reference_standard_uncertainty_m: Nonnegative | None = None
    reference_provider_id: str | None = None
    reference_result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_reference_complete(self):
        measurement_ids = [row.measurement_id for row in self.measurements]
        if len(measurement_ids) != len(set(measurement_ids)):
            raise ValueError("repeated thickness measurement identifiers must be unique per location")
        reference_fields = (
            self.reference_thickness_m,
            self.reference_standard_uncertainty_m,
            self.reference_provider_id,
            self.reference_result_digest,
        )
        if self.partition == "holdout" and not all(value is not None for value in reference_fields):
            raise ValueError("holdout thickness locations require complete independent reference evidence")
        if (
            self.partition == "calibration"
            and any(value is not None for value in reference_fields)
            and not all(value is not None for value in reference_fields)
        ):
            raise ValueError("optional calibration reference evidence must be complete")
        return self


class ThermalSprayThicknessUncertainty(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    coating_system_id: str = Field(min_length=1)
    layer_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    spray_batch_id: str = Field(min_length=1)
    process_condition_id: str = Field(min_length=1)
    calibrations: tuple[ThicknessInstrumentCalibration, ...] = Field(min_length=1)
    locations: tuple[ThermalSprayThicknessLocation, ...] = Field(min_length=3)
    minimum_repeats_per_location: int = Field(ge=2)
    expanded_uncertainty_coverage_factor: Positive
    specimen_location_layer_and_process_identity_reviewed: bool
    instrument_calibration_support_and_uncertainty_reviewed: bool
    repeated_measurement_method_units_and_digests_reviewed: bool
    spatial_groups_and_coordinate_frame_reviewed: bool
    specimen_source_independence_and_spatial_partitions_reviewed: bool
    holdout_reference_identity_and_uncertainty_reviewed: bool
    uncertainty_independence_and_coverage_factor_reviewed: bool
    missing_invalid_and_support_policy_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_partitioned_records(self):
        calibration_ids = [row.calibration_id for row in self.calibrations]
        location_ids = [row.location_record_id for row in self.locations]
        if len(calibration_ids) != len(set(calibration_ids)):
            raise ValueError("thickness calibration identifiers must be unique")
        if len(location_ids) != len(set(location_ids)):
            raise ValueError("thickness location-record identifiers must be unique")
        if {row.partition for row in self.locations} != {"calibration", "holdout"}:
            raise ValueError("thickness uncertainty requires calibration and holdout locations")
        for attribute, label in (
            ("physical_specimen_id", "physical specimen"),
            ("source_group_id", "source group"),
            ("independence_group_id", "independence group"),
            ("spatial_group_id", "spatial group"),
        ):
            calibration = {
                getattr(row, attribute) for row in self.locations if row.partition == "calibration"
            }
            holdout = {getattr(row, attribute) for row in self.locations if row.partition == "holdout"}
            if calibration & holdout:
                raise ValueError(f"thickness {label} cannot cross calibration and holdout")
        return self


def thermal_spray_thickness_uncertainty(x: ThermalSprayThicknessUncertainty) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "specimen_location_layer_and_process_identity_reviewed",
            "instrument_calibration_support_and_uncertainty_reviewed",
            "repeated_measurement_method_units_and_digests_reviewed",
            "spatial_groups_and_coordinate_frame_reviewed",
            "specimen_source_independence_and_spatial_partitions_reviewed",
            "holdout_reference_identity_and_uncertainty_reviewed",
            "uncertainty_independence_and_coverage_factor_reviewed",
            "missing_invalid_and_support_policy_reviewed",
        )
        if not getattr(x, name)
    ]
    calibration_by_id = {row.calibration_id: row for row in x.calibrations}
    invalid_calibration_ids = [row.calibration_id for row in x.calibrations if not row.record_valid]
    identity_mismatch_location_ids = [
        row.location_record_id
        for row in x.locations
        if row.layer_id != x.layer_id
        or row.substrate_condition_id != x.substrate_condition_id
        or row.spray_batch_id != x.spray_batch_id
        or row.process_condition_id != x.process_condition_id
    ]
    invalid_measurement_ids = [
        row.measurement_id
        for location in x.locations
        for row in location.measurements
        if not row.record_valid
    ]
    unlinked_measurement_ids = [
        row.measurement_id
        for location in x.locations
        for row in location.measurements
        if row.calibration_id not in calibration_by_id
    ]
    insufficient_repeat_location_ids = [
        row.location_record_id
        for row in x.locations
        if len(row.measurements) < x.minimum_repeats_per_location
    ]
    if (
        missing_reviews
        or invalid_calibration_ids
        or identity_mismatch_location_ids
        or invalid_measurement_ids
        or unlinked_measurement_ids
        or insufficient_repeat_location_ids
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "invalid_calibration_ids": invalid_calibration_ids,
                "identity_mismatch_location_ids": identity_mismatch_location_ids,
                "invalid_measurement_ids": invalid_measurement_ids,
                "unlinked_measurement_ids": unlinked_measurement_ids,
                "insufficient_repeat_location_ids": insufficient_repeat_location_ids,
            },
            notes=("Reviewed identities, valid repeated measurements and linked calibrations are required.",),
        )

    outside_support_measurement_ids = [
        row.measurement_id
        for location in x.locations
        for row in location.measurements
        if not calibration_by_id[row.calibration_id].minimum_supported_thickness_m
        <= row.measured_thickness_m
        <= calibration_by_id[row.calibration_id].maximum_supported_thickness_m
    ]
    if outside_support_measurement_ids:
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "outside_calibration_support_measurement_ids": outside_support_measurement_ids,
            },
            notes=("Thickness calibration support is not extrapolated.",),
        )

    location_rows = []
    for location in x.locations:
        corrected = []
        measurement_uncertainties = []
        calibration_uncertainties = []
        for measurement in location.measurements:
            calibration = calibration_by_id[measurement.calibration_id]
            corrected.append(measurement.measured_thickness_m + calibration.additive_bias_correction_m)
            measurement_uncertainties.append(measurement.measurement_standard_uncertainty_m)
            calibration_uncertainties.append(calibration.calibration_standard_uncertainty_m)
        count = len(corrected)
        mean = sum(corrected) / count
        sample_standard_deviation = math.sqrt(sum((value - mean) ** 2 for value in corrected) / (count - 1))
        repeatability_standard_uncertainty = sample_standard_deviation / math.sqrt(count)
        mean_measurement_standard_uncertainty = (
            math.sqrt(sum(value**2 for value in measurement_uncertainties)) / count
        )
        unique_calibration_ids = {row.calibration_id for row in location.measurements}
        calibration_standard_uncertainty = math.sqrt(
            sum(
                calibration_by_id[identifier].calibration_standard_uncertainty_m ** 2
                for identifier in unique_calibration_ids
            )
        )
        combined_standard_uncertainty = math.sqrt(
            repeatability_standard_uncertainty**2
            + mean_measurement_standard_uncertainty**2
            + calibration_standard_uncertainty**2
        )
        expanded_uncertainty = x.expanded_uncertainty_coverage_factor * combined_standard_uncertainty
        holdout_error = None
        holdout_combined_standard_uncertainty = None
        holdout_standardized_error = None
        if location.partition == "holdout":
            holdout_error = mean - location.reference_thickness_m
            holdout_combined_standard_uncertainty = math.sqrt(
                combined_standard_uncertainty**2 + location.reference_standard_uncertainty_m**2
            )
            holdout_standardized_error = holdout_error / holdout_combined_standard_uncertainty
        location_rows.append(
            {
                "location_record_id": location.location_record_id,
                "partition": location.partition,
                "physical_location_id": location.physical_location_id,
                "coordinate_frame_id": location.coordinate_frame_id,
                "x_coordinate_m": location.x_coordinate_m,
                "y_coordinate_m": location.y_coordinate_m,
                "spatial_group_id": location.spatial_group_id,
                "measurement_count": count,
                "mean_corrected_thickness_m": mean,
                "minimum_corrected_thickness_m": min(corrected),
                "maximum_corrected_thickness_m": max(corrected),
                "sample_standard_deviation_m": sample_standard_deviation,
                "repeatability_standard_uncertainty_m": repeatability_standard_uncertainty,
                "mean_measurement_standard_uncertainty_m": mean_measurement_standard_uncertainty,
                "calibration_standard_uncertainty_m": calibration_standard_uncertainty,
                "combined_standard_uncertainty_m": combined_standard_uncertainty,
                "expanded_uncertainty_m": expanded_uncertainty,
                "reference_thickness_m": location.reference_thickness_m,
                "holdout_error_m": holdout_error,
                "holdout_combined_standard_uncertainty_m": holdout_combined_standard_uncertainty,
                "holdout_standardized_error": holdout_standardized_error,
            }
        )

    def partition_summary(partition):
        rows = [row for row in location_rows if row["partition"] == partition]
        means = [row["mean_corrected_thickness_m"] for row in rows]
        summary = {
            "partition": partition,
            "location_count": len(rows),
            "location_record_ids": [row["location_record_id"] for row in rows],
            "mean_location_thickness_m": sum(means) / len(means),
            "minimum_location_thickness_m": min(means),
            "maximum_location_thickness_m": max(means),
        }
        if len(means) > 1:
            overall_mean = sum(means) / len(means)
            summary["between_location_repeatability_m"] = math.sqrt(
                sum((value - overall_mean) ** 2 for value in means) / (len(means) - 1)
            )
        else:
            summary["between_location_repeatability_m"] = None
        if partition == "holdout":
            errors = [row["holdout_error_m"] for row in rows]
            summary["holdout_mean_error_m"] = sum(errors) / len(errors)
            summary["holdout_rmse_m"] = math.sqrt(sum(value**2 for value in errors) / len(errors))
            summary["holdout_mean_absolute_standardized_error"] = sum(
                abs(row["holdout_standardized_error"]) for row in rows
            ) / len(rows)
        return summary

    return Calculation(
        status="computed",
        values={
            "assessment_id": x.assessment_id,
            "physical_scope_id": x.physical_scope_id,
            "coating_system_id": x.coating_system_id,
            "expanded_uncertainty_coverage_factor": x.expanded_uncertainty_coverage_factor,
            "location_rows": location_rows,
            "partition_summaries": [
                partition_summary("calibration"),
                partition_summary("holdout"),
            ],
        },
        notes=(
            "Bias corrections and calibration uncertainty are caller/provider inputs; the model does not infer calibration from coating data.",
            "The uncertainty combination assumes reviewed independence among repeatability, measurement and calibration components.",
            "Thickness summaries do not perform segmentation or infer bond strength, acceptance, service life or probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError(
                "thermal-spray thickness uncertainty asset and location must match the run context"
            )

    return [
        ModelSpec(
            "fabrication.thermal_spray_thickness_uncertainty",
            ThermalSprayThicknessUncertainty,
            thermal_spray_thickness_uncertainty,
            {
                "assessment_id": "1",
                "physical_scope_id": "1",
                "coating_system_id": "1",
                "expanded_uncertainty_coverage_factor": "1",
                "location_rows": "mixed",
                "partition_summaries": "mixed",
            },
            (
                "Repeated SI thickness measurements receive caller-provided additive calibration corrections.",
                "Calibration, measurement and repeatability uncertainty components are combined under reviewed independence.",
                "Calibration and holdout specimen, source, independence and spatial groups are disjoint.",
            ),
            ("authored_partitioned_thermal_spray_thickness_uncertainty",),
            context_validator=same_identity,
        )
    ]

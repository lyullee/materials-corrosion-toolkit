"""Offset-yield intersection from a reviewed raw engineering stress-strain branch."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class EngineeringStressStrainPoint(Contract):
    point_id: str = Field(min_length=1)
    engineering_strain: Nonnegative
    engineering_stress_Pa: Nonnegative
    elastic_fit_weight: Positive
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid tensile curve point requires a basis")
        return self


class OffsetYieldReferenceComparison(Contract):
    reference_record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    reference_method_id: str = Field(min_length=1)
    offset_strain: Positive
    offset_yield_stress_Pa: Positive
    expanded_uncertainty_Pa: Nonnegative
    uncertainty_coverage_factor: Positive
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid offset-yield reference requires a basis")
        return self


class TensileOffsetYieldCurveAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    tensile_test_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    specimen_geometry_id: str = Field(min_length=1)
    extensometer_id: str = Field(min_length=1)
    gauge_length_m: Positive
    instrument_provider_id: str = Field(min_length=1)
    instrument_provider_revision: str = Field(min_length=1)
    instrument_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    extensometer_calibration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_provider_id: str = Field(min_length=1)
    result_provider_revision: str = Field(min_length=1)
    result_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    engineering_strain_unit_token: Literal["1"] = "1"
    engineering_stress_unit_token: Literal["Pa"] = "Pa"
    curve_points: tuple[EngineeringStressStrainPoint, ...] = Field(min_length=4)
    elastic_fit_start_point_id: str = Field(min_length=1)
    elastic_fit_end_point_id: str = Field(min_length=1)
    analysis_start_point_id: str = Field(min_length=1)
    analysis_end_point_id: str = Field(min_length=1)
    offset_strain: Positive
    crossing_zero_tolerance_Pa: Nonnegative
    reference_comparison: OffsetYieldReferenceComparison | None = None
    specimen_gauge_and_extensometer_identity_reviewed: bool
    instrument_calibration_configuration_and_digests_reviewed: bool
    engineering_units_and_raw_curve_reviewed: bool
    monotonic_loading_branch_reviewed: bool
    elastic_fit_window_and_weights_reviewed: bool
    offset_and_linear_interpolation_reviewed: bool
    pre_necking_analysis_window_reviewed: bool
    crossing_uniqueness_reviewed: bool
    optional_reference_comparison_reviewed: bool

    @model_validator(mode="after")
    def ordered_curve_and_windows(self):
        identifiers = [row.point_id for row in self.curve_points]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("tensile curve point identifiers must be unique")
        strains = [row.engineering_strain for row in self.curve_points]
        if any(second <= first for first, second in zip(strains, strains[1:], strict=False)):
            raise ValueError("raw engineering strain must be strictly increasing")
        index = {identifier: position for position, identifier in enumerate(identifiers)}
        required = {
            self.elastic_fit_start_point_id,
            self.elastic_fit_end_point_id,
            self.analysis_start_point_id,
            self.analysis_end_point_id,
        }
        if not required.issubset(index):
            raise ValueError("elastic-fit and analysis window points must belong to the raw curve")
        elastic_start = index[self.elastic_fit_start_point_id]
        elastic_end = index[self.elastic_fit_end_point_id]
        analysis_start = index[self.analysis_start_point_id]
        analysis_end = index[self.analysis_end_point_id]
        if elastic_end <= elastic_start:
            raise ValueError("elastic-fit window requires at least two ordered points")
        if analysis_end <= analysis_start:
            raise ValueError("analysis window requires at least two ordered points")
        if not analysis_start <= elastic_start < elastic_end <= analysis_end:
            raise ValueError("elastic-fit window must lie inside the reviewed analysis window")
        reference = self.reference_comparison
        if reference is not None and (
            reference.physical_specimen_id == self.physical_specimen_id
            or reference.source_group_id == self.source_group_id
            or reference.independence_group_id == self.independence_group_id
        ):
            raise ValueError("optional reference comparison must be independent of the analyzed curve")
        return self


def tensile_offset_yield_curve(x: TensileOffsetYieldCurveAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "specimen_gauge_and_extensometer_identity_reviewed",
            "instrument_calibration_configuration_and_digests_reviewed",
            "engineering_units_and_raw_curve_reviewed",
            "monotonic_loading_branch_reviewed",
            "elastic_fit_window_and_weights_reviewed",
            "offset_and_linear_interpolation_reviewed",
            "pre_necking_analysis_window_reviewed",
            "crossing_uniqueness_reviewed",
            "optional_reference_comparison_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_point_ids = [row.point_id for row in x.curve_points if not row.record_valid]
    invalid_reference = x.reference_comparison is not None and not x.reference_comparison.record_valid
    if missing_reviews or invalid_point_ids or invalid_reference:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "invalid_curve_point_ids": invalid_point_ids,
                "reference_record_valid": (
                    None if x.reference_comparison is None else x.reference_comparison.record_valid
                ),
            },
            notes=("Reviewed, valid curve and optional reference records are required.",),
        )

    point_index = {row.point_id: index for index, row in enumerate(x.curve_points)}
    elastic_start = point_index[x.elastic_fit_start_point_id]
    elastic_end = point_index[x.elastic_fit_end_point_id]
    analysis_start = point_index[x.analysis_start_point_id]
    analysis_end = point_index[x.analysis_end_point_id]
    elastic_points = x.curve_points[elastic_start : elastic_end + 1]
    weight_sum = math.fsum(row.elastic_fit_weight for row in elastic_points)
    mean_strain = (
        math.fsum(row.elastic_fit_weight * row.engineering_strain for row in elastic_points) / weight_sum
    )
    mean_stress = (
        math.fsum(row.elastic_fit_weight * row.engineering_stress_Pa for row in elastic_points) / weight_sum
    )
    weighted_strain_variance = math.fsum(
        row.elastic_fit_weight * (row.engineering_strain - mean_strain) ** 2 for row in elastic_points
    )
    if weighted_strain_variance <= 0.0:
        return Calculation(
            status="needs_data",
            values={"assessment_id": x.assessment_id, "elastic_fit_identifiable": False},
            notes=("The elastic-fit strain window does not identify a slope.",),
        )
    elastic_modulus = (
        math.fsum(
            row.elastic_fit_weight
            * (row.engineering_strain - mean_strain)
            * (row.engineering_stress_Pa - mean_stress)
            for row in elastic_points
        )
        / weighted_strain_variance
    )
    intercept = mean_stress - elastic_modulus * mean_strain
    if elastic_modulus <= 0.0:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "fitted_elastic_modulus_Pa": elastic_modulus,
            },
            notes=("The reviewed elastic-fit window produced a nonpositive slope.",),
        )
    elastic_sse = math.fsum(
        row.elastic_fit_weight
        * (row.engineering_stress_Pa - (intercept + elastic_modulus * row.engineering_strain)) ** 2
        for row in elastic_points
    )
    elastic_sst = math.fsum(
        row.elastic_fit_weight * (row.engineering_stress_Pa - mean_stress) ** 2 for row in elastic_points
    )
    elastic_r_squared = None if elastic_sst == 0.0 else 1.0 - elastic_sse / elastic_sst

    analyzed_points = x.curve_points[analysis_start : analysis_end + 1]
    residuals = [
        row.engineering_stress_Pa - (intercept + elastic_modulus * (row.engineering_strain - x.offset_strain))
        for row in analyzed_points
    ]
    candidates = []
    for local_index, residual in enumerate(residuals):
        if abs(residual) <= x.crossing_zero_tolerance_Pa:
            row = analyzed_points[local_index]
            candidates.append(
                {
                    "kind": "exact_point",
                    "point_ids": [row.point_id],
                    "engineering_strain": row.engineering_strain,
                    "engineering_stress_Pa": row.engineering_stress_Pa,
                }
            )
    for local_index, (first_residual, second_residual) in enumerate(
        zip(residuals, residuals[1:], strict=False)
    ):
        first_is_zero = abs(first_residual) <= x.crossing_zero_tolerance_Pa
        second_is_zero = abs(second_residual) <= x.crossing_zero_tolerance_Pa
        if first_is_zero or second_is_zero or first_residual * second_residual >= 0.0:
            continue
        first = analyzed_points[local_index]
        second = analyzed_points[local_index + 1]
        fraction = first_residual / (first_residual - second_residual)
        candidates.append(
            {
                "kind": "linear_segment_intersection",
                "point_ids": [first.point_id, second.point_id],
                "engineering_strain": first.engineering_strain
                + fraction * (second.engineering_strain - first.engineering_strain),
                "engineering_stress_Pa": first.engineering_stress_Pa
                + fraction * (second.engineering_stress_Pa - first.engineering_stress_Pa),
            }
        )
    base_values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "tensile_test_id": x.tensile_test_id,
        "physical_specimen_id": x.physical_specimen_id,
        "elastic_fit_point_ids": [row.point_id for row in elastic_points],
        "analysis_point_ids": [row.point_id for row in analyzed_points],
        "fitted_elastic_modulus_Pa": elastic_modulus,
        "fitted_elastic_intercept_Pa": intercept,
        "elastic_fit_weighted_sse_Pa2": elastic_sse,
        "elastic_fit_weighted_r_squared": elastic_r_squared,
        "offset_strain": x.offset_strain,
        "crossing_candidates": candidates,
    }
    if len(candidates) != 1:
        return Calculation(
            status="needs_data",
            values=base_values,
            notes=(
                "Exactly one reviewed offset-line crossing is required; no crossing or multiple crossings are not resolved automatically.",
            ),
        )
    crossing = candidates[0]
    base_values.update(
        {
            "offset_yield_stress_Pa": crossing["engineering_stress_Pa"],
            "intersection_engineering_strain": crossing["engineering_strain"],
            "intersection_kind": crossing["kind"],
            "intersection_point_ids": crossing["point_ids"],
        }
    )
    reference = x.reference_comparison
    if reference is not None:
        difference = crossing["engineering_stress_Pa"] - reference.offset_yield_stress_Pa
        base_values["reference_comparison"] = {
            "reference_record_id": reference.reference_record_id,
            "reference_offset_yield_stress_Pa": reference.offset_yield_stress_Pa,
            "reference_expanded_uncertainty_Pa": reference.expanded_uncertainty_Pa,
            "signed_difference_Pa": difference,
            "relative_difference": difference / reference.offset_yield_stress_Pa,
        }
    else:
        base_values["reference_comparison"] = None
    return Calculation(
        values=base_values,
        notes=(
            "The elastic line is a weighted fit over the caller-reviewed window; the offset line is parallel and shifted by the declared engineering strain.",
            "The crossing uses only exact points or linear interpolation between adjacent raw engineering curve points.",
            "No true-stress conversion, post-necking inference, specification acceptance or failure probability is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("tensile offset-yield assessment asset and location must match run context")

    return [
        ModelSpec(
            "inspection.tensile_offset_yield_curve",
            TensileOffsetYieldCurveAssessment,
            tensile_offset_yield_curve,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "tensile_test_id": "1",
                "physical_specimen_id": "1",
                "elastic_fit_point_ids": "1",
                "analysis_point_ids": "1",
                "fitted_elastic_modulus_Pa": "Pa",
                "fitted_elastic_intercept_Pa": "Pa",
                "elastic_fit_weighted_sse_Pa2": "Pa^2*weight",
                "elastic_fit_weighted_r_squared": "1",
                "offset_strain": "1",
                "crossing_candidates": "mixed",
                "offset_yield_stress_Pa": "Pa",
                "intersection_engineering_strain": "1",
                "intersection_kind": "1",
                "intersection_point_ids": "1",
                "reference_comparison": "mixed",
            },
            (
                "The supplied curve is a reviewed monotonic engineering-strain loading branch inside a pre-necking analysis window.",
                "Elastic fit weights, offset and crossing tolerance are caller-reviewed inputs.",
                "A unique adjacent-point crossing is descriptive test reduction, not specification acceptance.",
            ),
            ("authored_weighted_elastic_offset_line_intersection",),
            context_validator=same_identity,
        )
    ]

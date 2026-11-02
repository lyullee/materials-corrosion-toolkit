"""Reviewed geometric summaries of replica-metallography segmentation features."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class ReplicaFrameCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    coordinate_unit: Literal["m", "px"]
    frame_width: Positive
    frame_height: Positive
    pixel_size_x_m_per_px: Positive | None = None
    pixel_size_y_m_per_px: Positive | None = None
    expanded_pixel_size_x_uncertainty_m_per_px: Nonnegative | None = None
    expanded_pixel_size_y_uncertainty_m_per_px: Nonnegative | None = None
    uncertainty_coverage_factor: Positive
    calibration_provider_id: str = Field(min_length=1)
    calibration_provider_revision: str = Field(min_length=1)
    calibration_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_scale(self):
        scale_values = (
            self.pixel_size_x_m_per_px,
            self.pixel_size_y_m_per_px,
            self.expanded_pixel_size_x_uncertainty_m_per_px,
            self.expanded_pixel_size_y_uncertainty_m_per_px,
        )
        if self.coordinate_unit == "px" and any(value is None for value in scale_values):
            raise ValueError("pixel-coordinate frames require both pixel scales and uncertainties")
        if self.coordinate_unit == "m" and any(value is not None for value in scale_values):
            raise ValueError("SI-coordinate frames cannot also declare a pixel scale")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid frame calibration records require a basis")
        return self


class ReplicaSegmentationFeature(Contract):
    feature_id: str = Field(min_length=1)
    caller_feature_type: str = Field(min_length=1)
    centroid_x: Nonnegative
    centroid_y: Nonnegative
    bounding_box_min_x: Nonnegative
    bounding_box_min_y: Nonnegative
    bounding_box_max_x: Positive
    bounding_box_max_y: Positive
    segmented_area: Positive
    expanded_centroid_uncertainty: Nonnegative
    expanded_area_uncertainty: Nonnegative
    uncertainty_coverage_factor: Positive
    segmentation_feature_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    overlaps_feature_ids: tuple[str, ...] = ()
    touches_frame_edge: bool
    include_in_summary: bool
    edge_censoring_basis: str | None = None
    record_available: bool
    record_valid: bool
    missing_or_invalid_basis: str | None = None
    observer_review_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_geometry_and_review(self):
        if self.bounding_box_max_x <= self.bounding_box_min_x:
            raise ValueError("feature bounding-box x limits must be ordered")
        if self.bounding_box_max_y <= self.bounding_box_min_y:
            raise ValueError("feature bounding-box y limits must be ordered")
        if not self.bounding_box_min_x <= self.centroid_x <= self.bounding_box_max_x:
            raise ValueError("feature centroid x must lie inside its bounding box")
        if not self.bounding_box_min_y <= self.centroid_y <= self.bounding_box_max_y:
            raise ValueError("feature centroid y must lie inside its bounding box")
        if self.feature_id in self.overlaps_feature_ids:
            raise ValueError("a feature cannot overlap itself")
        if len(set(self.overlaps_feature_ids)) != len(self.overlaps_feature_ids):
            raise ValueError("overlap feature identifiers must be unique")
        if self.touches_frame_edge and not self.edge_censoring_basis:
            raise ValueError("edge-touching features require an edge-censoring basis")
        if not self.record_available or not self.record_valid:
            if not self.missing_or_invalid_basis:
                raise ValueError("missing or invalid features require a basis")
            if self.include_in_summary:
                raise ValueError("missing or invalid features cannot be included in summaries")
        return self


class ReplicaReviewedField(Contract):
    field_id: str = Field(min_length=1)
    replica_id: str = Field(min_length=1)
    frame_id: str = Field(min_length=1)
    physical_source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    calibration: ReplicaFrameCalibration
    segmentation_method_id: str = Field(min_length=1)
    segmentation_provider_id: str = Field(min_length=1)
    segmentation_provider_revision: str = Field(min_length=1)
    segmentation_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    segmentation_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    segmentation_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observer_review_id: str = Field(min_length=1)
    observer_review_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    feature_inventory_complete: bool
    field_record_valid: bool
    invalid_or_missing_basis: str | None = None
    features: tuple[ReplicaSegmentationFeature, ...]
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_and_bounded_features(self):
        identifiers = [row.feature_id for row in self.features]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("replica feature identifiers must be unique within a field")
        digests = [row.segmentation_feature_digest for row in self.features]
        if len(set(digests)) != len(digests):
            raise ValueError("duplicate replica segmentation feature digests are not allowed")
        declared = set(identifiers)
        for row in self.features:
            if not set(row.overlaps_feature_ids) <= declared:
                raise ValueError("overlap references must identify features in the same field")
            if row.bounding_box_max_x > self.calibration.frame_width:
                raise ValueError("feature geometry exceeds the calibrated frame width")
            if row.bounding_box_max_y > self.calibration.frame_height:
                raise ValueError("feature geometry exceeds the calibrated frame height")
        overlaps = {row.feature_id: set(row.overlaps_feature_ids) for row in self.features}
        for feature_id, other_ids in overlaps.items():
            if any(feature_id not in overlaps[other_id] for other_id in other_ids):
                raise ValueError("reviewed feature-overlap declarations must be symmetric")
        if not self.field_record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid replica fields require a basis")
        return self


class ReplicaFeatureDensityAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    replica_campaign_id: str = Field(min_length=1)
    physical_location_definition: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    service_exposure_id: str = Field(min_length=1)
    service_clock_definition: str = Field(min_length=1)
    service_exposure_duration_s: Nonnegative
    minimum_service_temperature_K: Positive
    maximum_service_temperature_K: Positive
    fields: tuple[ReplicaReviewedField, ...] = Field(min_length=1)
    replica_location_material_and_service_exposure_reviewed: bool
    frame_and_calibration_identity_reviewed: bool
    si_scale_units_and_uncertainty_reviewed: bool
    segmentation_provider_revision_and_digests_reviewed: bool
    observer_review_and_feature_inventory_reviewed: bool
    feature_ids_types_coordinates_and_geometry_reviewed: bool
    duplicate_overlap_and_edge_censoring_reviewed: bool
    physical_source_and_independence_groups_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_assessment(self):
        if self.maximum_service_temperature_K < self.minimum_service_temperature_K:
            raise ValueError("service-temperature bounds must be ordered")
        field_ids = [row.field_id for row in self.fields]
        frame_ids = [row.frame_id for row in self.fields]
        if len(set(field_ids)) != len(field_ids):
            raise ValueError("replica field identifiers must be unique")
        if len(set(frame_ids)) != len(frame_ids):
            raise ValueError("replica frame identifiers must be unique")
        return self


def _si_scale(calibration: ReplicaFrameCalibration) -> tuple[float, float]:
    if calibration.coordinate_unit == "m":
        return 1.0, 1.0
    return calibration.pixel_size_x_m_per_px, calibration.pixel_size_y_m_per_px


def replica_feature_density_summary(x: ReplicaFeatureDensityAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "replica_location_material_and_service_exposure_reviewed",
            "frame_and_calibration_identity_reviewed",
            "si_scale_units_and_uncertainty_reviewed",
            "segmentation_provider_revision_and_digests_reviewed",
            "observer_review_and_feature_inventory_reviewed",
            "feature_ids_types_coordinates_and_geometry_reviewed",
            "duplicate_overlap_and_edge_censoring_reviewed",
            "physical_source_and_independence_groups_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_field_ids = [
        row.field_id for row in x.fields if not row.field_record_valid or not row.calibration.record_valid
    ]
    incomplete_inventory_field_ids = [row.field_id for row in x.fields if not row.feature_inventory_complete]
    invalid_feature_ids = [
        f"{field.field_id}:{feature.feature_id}"
        for field in x.fields
        for feature in field.features
        if not feature.record_available or not feature.record_valid
    ]
    overlapping_feature_ids = sorted(
        {
            f"{field.field_id}:{feature.feature_id}"
            for field in x.fields
            for feature in field.features
            if feature.overlaps_feature_ids
        }
    )
    incomplete = (
        missing_reviews
        or invalid_field_ids
        or incomplete_inventory_field_ids
        or invalid_feature_ids
        or overlapping_feature_ids
    )
    if incomplete:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "invalid_field_ids": invalid_field_ids,
                "incomplete_inventory_field_ids": incomplete_inventory_field_ids,
                "invalid_feature_ids": invalid_feature_ids,
                "overlapping_feature_ids": overlapping_feature_ids,
            },
            notes=(
                "Every field requires reviewed calibration, a complete inventory and valid nonoverlapping feature records.",
            ),
        )

    field_summaries = []
    for field in x.fields:
        scale_x, scale_y = _si_scale(field.calibration)
        field_area_m2 = field.calibration.frame_width * scale_x * field.calibration.frame_height * scale_y
        included = [feature for feature in field.features if feature.include_in_summary]
        excluded_edge_ids = [
            feature.feature_id
            for feature in field.features
            if feature.touches_frame_edge and not feature.include_in_summary
        ]
        centers_m = [(row.centroid_x * scale_x, row.centroid_y * scale_y) for row in included]
        nearest_neighbor_spacings_m = []
        for index, center in enumerate(centers_m):
            distances = [
                math.hypot(center[0] - other[0], center[1] - other[1])
                for other_index, other in enumerate(centers_m)
                if other_index != index
            ]
            if distances:
                nearest_neighbor_spacings_m.append(min(distances))
        total_feature_area_m2 = sum(row.segmented_area * scale_x * scale_y for row in included)
        feature_count = len(included)
        field_summaries.append(
            {
                "field_id": field.field_id,
                "replica_id": field.replica_id,
                "frame_id": field.frame_id,
                "physical_source_group_id": field.physical_source_group_id,
                "independence_group_id": field.independence_group_id,
                "coordinate_unit": field.calibration.coordinate_unit,
                "field_area_m2": field_area_m2,
                "reviewed_feature_count": feature_count,
                "caller_feature_types": sorted({row.caller_feature_type for row in included}),
                "feature_count_density_per_m2": feature_count / field_area_m2,
                "total_segmented_feature_area_m2": total_feature_area_m2,
                "segmented_feature_area_fraction": total_feature_area_m2 / field_area_m2,
                "mean_nearest_neighbor_spacing_m": (
                    sum(nearest_neighbor_spacings_m) / len(nearest_neighbor_spacings_m)
                    if nearest_neighbor_spacings_m
                    else None
                ),
                "minimum_nearest_neighbor_spacing_m": (
                    min(nearest_neighbor_spacings_m) if nearest_neighbor_spacings_m else None
                ),
                "nearest_neighbor_spacing_count": len(nearest_neighbor_spacings_m),
                "excluded_edge_feature_ids": excluded_edge_ids,
                "included_edge_feature_ids": [row.feature_id for row in included if row.touches_frame_edge],
                "segmentation_method_id": field.segmentation_method_id,
                "segmentation_provider_id": field.segmentation_provider_id,
                "segmentation_provider_revision": field.segmentation_provider_revision,
                "segmentation_result_digest": field.segmentation_result_digest,
                "observer_review_id": field.observer_review_id,
            }
        )
    return Calculation(
        status="computed",
        values={
            "assessment_id": x.assessment_id,
            "component_id": x.component_id,
            "material_id": x.material_id,
            "material_condition_id": x.material_condition_id,
            "service_exposure_id": x.service_exposure_id,
            "field_count": len(x.fields),
            "field_summaries": field_summaries,
            "missing_reviews": [],
        },
        notes=(
            "Summaries are geometric reductions of caller-reviewed segmentation records and preserve caller feature labels.",
            "Nearest-neighbor spacing uses included feature centroids after the declared SI calibration.",
            "No feature is identified as a creep cavity and no damage grade, life, acceptance or probability is inferred.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("replica feature assessment asset and location must match the run context")

    return [
        ModelSpec(
            "inspection.replica_feature_density_summary",
            ReplicaFeatureDensityAssessment,
            replica_feature_density_summary,
            {
                "assessment_id": "1",
                "component_id": "1",
                "material_id": "1",
                "material_condition_id": "1",
                "service_exposure_id": "1",
                "field_count": "1",
                "field_summaries": "mixed",
                "missing_reviews": "1",
            },
            (
                "Frame calibration, SI scale and uncertainty are caller-reviewed and traceable.",
                "Feature inventory, identifiers, coordinates, geometry, overlap and edge handling are reviewed.",
                "Outputs are geometric field summaries and retain source, provider and observer lineage.",
            ),
            ("authored_replica_feature_geometry_reduction",),
            context_validator=same_identity,
        )
    ]

"""Procedure-bound radiographic records and transparent projection geometry."""

from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class RadiographicImageIndication(Contract):
    indication_id: str = Field(min_length=1)
    image_id: str = Field(min_length=1)
    reported_indication_type: str = Field(min_length=1)
    location_description: str = Field(min_length=1)
    bounding_box_x_px: Nonnegative
    bounding_box_y_px: Nonnegative
    bounding_box_width_px: Positive
    bounding_box_height_px: Positive
    physical_location_id: str | None = Field(default=None, min_length=1)
    object_mapping_basis: str | None = Field(default=None, min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_object_mapping(self):
        if (self.physical_location_id is None) != (self.object_mapping_basis is None):
            raise ValueError("physical location and object-mapping basis must be supplied together")
        return self


class RadiographicImageQualityRecord(Contract):
    iqi_id: str = Field(min_length=1)
    iqi_type: str = Field(min_length=1)
    placement: Literal["source_side", "detector_side", "other"]
    placement_basis: str = Field(min_length=1)
    reported_image_quality_result: str = Field(min_length=1)
    result_basis: str = Field(min_length=1)
    reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)


class RadiographicExamination(Contract):
    examination_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    source_kind: Literal["x_ray", "gamma"]
    source_equipment_id: str = Field(min_length=1)
    tube_voltage_V: Positive | None = None
    isotope_id: str | None = Field(default=None, min_length=1)
    source_activity_Bq: Positive | None = None
    source_activity_reference: str | None = Field(default=None, min_length=1)
    focal_spot_size_m: Positive | None = None
    exposure_time_s: Positive
    source_object_distance_m: Positive | None = None
    object_detector_distance_m: Nonnegative | None = None
    nominal_object_thickness_m: Positive
    detector_kind: Literal["film", "computed_radiography", "digital_detector_array", "other"]
    detector_id: str = Field(min_length=1)
    detector_calibration_basis: str = Field(min_length=1)
    image_id: str = Field(min_length=1)
    image_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    image_width_px: int = Field(gt=0)
    image_height_px: int = Field(gt=0)
    detector_pixel_pitch_m: Positive | None = None
    image_quality_records: list[RadiographicImageQualityRecord] = Field(min_length=1)
    indications: list[RadiographicImageIndication] = Field(default_factory=list)
    source_configuration_reviewed: bool
    projection_geometry_reviewed: bool
    exposure_reviewed: bool
    detector_calibration_reviewed: bool
    image_identity_reviewed: bool
    image_quality_reviewed: bool
    indication_mapping_reviewed: bool
    negative_result_reviewed: bool = False
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_source_and_image(self):
        if self.source_kind == "x_ray":
            if self.tube_voltage_V is None:
                raise ValueError("x-ray records require tube voltage")
            if self.isotope_id is not None or self.source_activity_Bq is not None:
                raise ValueError("x-ray records cannot carry gamma-source identity or activity")
        else:
            if self.isotope_id is None:
                raise ValueError("gamma records require isotope identity")
            if self.tube_voltage_V is not None:
                raise ValueError("gamma records cannot carry x-ray tube voltage")
        if (self.source_activity_Bq is None) != (self.source_activity_reference is None):
            raise ValueError("source activity and its reference must be supplied together")
        indication_ids = [item.indication_id for item in self.indications]
        if len(set(indication_ids)) != len(indication_ids):
            raise ValueError("radiographic indication IDs must be unique")
        if {item.image_id for item in self.indications} - {self.image_id}:
            raise ValueError("every indication must reference the examination image")
        for item in self.indications:
            if item.bounding_box_x_px + item.bounding_box_width_px > self.image_width_px:
                raise ValueError("indication bounding box exceeds image width")
            if item.bounding_box_y_px + item.bounding_box_height_px > self.image_height_px:
                raise ValueError("indication bounding box exceeds image height")
        iqi_ids = [item.iqi_id for item in self.image_quality_records]
        if len(set(iqi_ids)) != len(iqi_ids):
            raise ValueError("image-quality record IDs must be unique")
        return self


def radiographic_geometry_summary(x: RadiographicExamination) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "source_configuration_reviewed",
            "projection_geometry_reviewed",
            "exposure_reviewed",
            "detector_calibration_reviewed",
            "image_identity_reviewed",
            "image_quality_reviewed",
            "indication_mapping_reviewed",
        )
        if not getattr(x, name)
    ]
    if not x.indications and not x.negative_result_reviewed:
        missing_reviews.append("negative_result_reviewed")
    if not all(item.reviewed for item in x.image_quality_records):
        missing_reviews.append("image_quality_record_reviewed")

    missing_geometry_fields = [
        name
        for name in ("source_object_distance_m", "object_detector_distance_m")
        if getattr(x, name) is None
    ]
    unmapped_indication_ids = [
        item.indication_id for item in x.indications if item.physical_location_id is None
    ]

    magnification = None
    geometric_unsharpness_m = None
    object_plane_pixel_pitch_m = None
    source_detector_distance_m = None
    if not missing_geometry_fields:
        source_object_distance_m = x.source_object_distance_m
        object_detector_distance_m = x.object_detector_distance_m
        assert source_object_distance_m is not None
        assert object_detector_distance_m is not None
        source_detector_distance_m = source_object_distance_m + object_detector_distance_m
        magnification = source_detector_distance_m / source_object_distance_m
        if x.focal_spot_size_m is not None:
            geometric_unsharpness_m = (
                x.focal_spot_size_m * object_detector_distance_m / source_object_distance_m
            )
        if x.detector_pixel_pitch_m is not None:
            object_plane_pixel_pitch_m = x.detector_pixel_pitch_m / magnification

    status = (
        "needs_data" if missing_reviews or missing_geometry_fields or unmapped_indication_ids else "computed"
    )
    return Calculation(
        status=status,
        values={
            "examination_id": x.examination_id,
            "procedure_id": x.procedure_id,
            "procedure_revision": x.procedure_revision,
            "physical_scope_id": x.physical_scope_id,
            "source_kind": x.source_kind,
            "detector_kind": x.detector_kind,
            "image_id": x.image_id,
            "exposure_time_s": x.exposure_time_s,
            "nominal_object_thickness_m": x.nominal_object_thickness_m,
            "source_detector_distance_m": source_detector_distance_m,
            "magnification": magnification,
            "geometric_unsharpness_m": geometric_unsharpness_m,
            "object_plane_pixel_pitch_m": object_plane_pixel_pitch_m,
            "image_quality_record_count": len(x.image_quality_records),
            "indication_count": len(x.indications),
            "indication_counts_by_reported_type": dict(
                Counter(item.reported_indication_type for item in x.indications)
            ),
            "unmapped_indication_ids": unmapped_indication_ids,
            "missing_geometry_fields": missing_geometry_fields,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Projection quantities use only declared pinhole geometry and do not qualify image quality or procedure compliance.",
            "Geometric unsharpness is reported only when focal-spot size and both distances are supplied; it is not total system resolution.",
            "Image-space indications are not defect identity, physical dimensions, acceptance, probability of detection, remaining life or failure probability.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "inspection.radiographic_geometry_summary",
            RadiographicExamination,
            radiographic_geometry_summary,
            {
                "exposure_time_s": "s",
                "nominal_object_thickness_m": "m",
                "source_detector_distance_m": "m",
                "magnification": "1",
                "geometric_unsharpness_m": "m",
                "object_plane_pixel_pitch_m": "m",
            },
            (
                "Caller-controlled radiographic source, exposure, detector, image, IQI, projection geometry and indication record; no embedded acceptance rule.",
            ),
            ("radiographic_examination_geometry_definition",),
        )
    ]

"""Build a radiographic geometry record directly with Python objects."""

from matintegrity.contracts import Evidence
from matintegrity.models.radiography import (
    RadiographicExamination,
    RadiographicImageQualityRecord,
    radiographic_geometry_summary,
)

record = Evidence(
    source_id="user-radiographic-record",
    origin="user_declared",
    citation="replace with the controlled examination record",
)
examination = RadiographicExamination(
    examination_id="rt-001",
    procedure_id="user-rt-procedure",
    procedure_revision="1",
    physical_scope_id="weld-17",
    material_condition_id="steel-weld-condition-a",
    source_kind="x_ray",
    source_equipment_id="xray-set-2",
    tube_voltage_V=200000.0,
    focal_spot_size_m=0.001,
    exposure_time_s=20.0,
    source_object_distance_m=1.0,
    object_detector_distance_m=0.2,
    nominal_object_thickness_m=0.02,
    detector_kind="digital_detector_array",
    detector_id="dda-4",
    detector_calibration_basis="replace with controlled calibration record",
    image_id="image-0001",
    image_sha256="a" * 64,
    image_width_px=2000,
    image_height_px=1000,
    detector_pixel_pitch_m=0.0002,
    image_quality_records=[
        RadiographicImageQualityRecord(
            iqi_id="iqi-1",
            iqi_type="caller-selected wire indicator",
            placement="source_side",
            placement_basis="replace with placement record",
            reported_image_quality_result="replace with reviewed result",
            result_basis="replace with controlled image review",
            reviewed=True,
            evidence=[record],
        )
    ],
    source_configuration_reviewed=True,
    projection_geometry_reviewed=True,
    exposure_reviewed=True,
    detector_calibration_reviewed=True,
    image_identity_reviewed=True,
    image_quality_reviewed=True,
    indication_mapping_reviewed=True,
    negative_result_reviewed=True,
    evidence=[record],
)

print(radiographic_geometry_summary(examination).model_dump_json(indent=2))

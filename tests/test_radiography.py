import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.models.radiography import (
    RadiographicExamination,
    radiographic_geometry_summary,
)
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "user-radiographic-record",
    "origin": "user_declared",
    "citation": "caller-controlled radiographic examination record",
}


def _record(**updates):
    values = {
        "examination_id": "rt-001",
        "procedure_id": "user-rt-procedure",
        "procedure_revision": "3",
        "physical_scope_id": "weld-17",
        "material_condition_id": "steel-weld-condition-a",
        "source_kind": "x_ray",
        "source_equipment_id": "xray-set-2",
        "tube_voltage_V": 200000.0,
        "focal_spot_size_m": 0.001,
        "exposure_time_s": 20.0,
        "source_object_distance_m": 1.0,
        "object_detector_distance_m": 0.2,
        "nominal_object_thickness_m": 0.02,
        "detector_kind": "digital_detector_array",
        "detector_id": "dda-4",
        "detector_calibration_basis": "caller-controlled calibration record",
        "image_id": "image-0001",
        "image_sha256": "a" * 64,
        "image_width_px": 2000,
        "image_height_px": 1000,
        "detector_pixel_pitch_m": 0.0002,
        "image_quality_records": [
            {
                "iqi_id": "iqi-1",
                "iqi_type": "caller-selected wire indicator",
                "placement": "source_side",
                "placement_basis": "visible placement marker and examination record",
                "reported_image_quality_result": "caller-reported visible element",
                "result_basis": "caller-controlled image review",
                "reviewed": True,
                "evidence": [EVIDENCE],
            }
        ],
        "indications": [
            {
                "indication_id": "ind-1",
                "image_id": "image-0001",
                "reported_indication_type": "rounded indication",
                "location_description": "image coordinates from original pixels",
                "bounding_box_x_px": 100.0,
                "bounding_box_y_px": 200.0,
                "bounding_box_width_px": 20.0,
                "bounding_box_height_px": 30.0,
                "physical_location_id": "weld-17-clock-2",
                "object_mapping_basis": "caller-controlled marker mapping",
                "evidence": [EVIDENCE],
            }
        ],
        "source_configuration_reviewed": True,
        "projection_geometry_reviewed": True,
        "exposure_reviewed": True,
        "detector_calibration_reviewed": True,
        "image_identity_reviewed": True,
        "image_quality_reviewed": True,
        "indication_mapping_reviewed": True,
        "negative_result_reviewed": False,
        "evidence": [EVIDENCE],
    }
    values.update(updates)
    return values


def test_radiographic_geometry_matches_pinhole_algebra():
    result = radiographic_geometry_summary(RadiographicExamination.model_validate(_record()))
    assert result.status == "computed"
    assert result.values["source_detector_distance_m"] == pytest.approx(1.2)
    assert result.values["magnification"] == pytest.approx(1.2)
    assert result.values["geometric_unsharpness_m"] == pytest.approx(0.0002)
    assert result.values["object_plane_pixel_pitch_m"] == pytest.approx(0.0002 / 1.2)
    assert not any("accept" in key for key in result.values)


def test_missing_geometry_is_preserved_as_needs_data():
    result = radiographic_geometry_summary(
        RadiographicExamination.model_validate(
            _record(source_object_distance_m=None, object_detector_distance_m=None)
        )
    )
    assert result.status == "needs_data"
    assert result.values["magnification"] is None
    assert result.values["missing_geometry_fields"] == [
        "source_object_distance_m",
        "object_detector_distance_m",
    ]


def test_image_space_indication_without_object_mapping_is_needs_data():
    values = _record()
    values["indications"][0]["physical_location_id"] = None
    values["indications"][0]["object_mapping_basis"] = None
    result = radiographic_geometry_summary(RadiographicExamination.model_validate(values))
    assert result.status == "needs_data"
    assert result.values["unmapped_indication_ids"] == ["ind-1"]


def test_negative_record_requires_separate_review():
    pending = radiographic_geometry_summary(RadiographicExamination.model_validate(_record(indications=[])))
    assert pending.status == "needs_data"
    reviewed = radiographic_geometry_summary(
        RadiographicExamination.model_validate(_record(indications=[], negative_result_reviewed=True))
    )
    assert reviewed.status == "computed"


@pytest.mark.parametrize(
    "updates",
    [
        {"source_kind": "x_ray", "tube_voltage_V": None},
        {"source_kind": "x_ray", "isotope_id": "Ir-192"},
        {"source_kind": "gamma", "tube_voltage_V": 200000.0, "isotope_id": "Ir-192"},
        {"source_kind": "gamma", "tube_voltage_V": None, "isotope_id": None},
    ],
)
def test_source_kind_fields_cannot_be_mixed_or_omitted(updates):
    with pytest.raises(ValidationError):
        RadiographicExamination.model_validate(_record(**updates))


def test_gamma_source_and_optional_activity_are_explicit():
    record = RadiographicExamination.model_validate(
        _record(
            source_kind="gamma",
            tube_voltage_V=None,
            isotope_id="Ir-192",
            source_activity_Bq=1.0e12,
            source_activity_reference="activity at caller-recorded reference time",
        )
    )
    assert record.isotope_id == "Ir-192"


def test_image_identity_bounds_and_mapping_are_validated():
    bad_image = _record()
    bad_image["indications"][0]["image_id"] = "another-image"
    with pytest.raises(ValidationError):
        RadiographicExamination.model_validate(bad_image)
    bad_bounds = _record()
    bad_bounds["indications"][0]["bounding_box_x_px"] = 1990.0
    with pytest.raises(ValidationError):
        RadiographicExamination.model_validate(bad_bounds)
    incomplete_mapping = _record()
    incomplete_mapping["indications"][0]["object_mapping_basis"] = None
    with pytest.raises(ValidationError):
        RadiographicExamination.model_validate(incomplete_mapping)


def test_registry_route_has_no_probability_semantics():
    result = default_registry().run(
        "inspection.radiographic_geometry_summary",
        _record(),
        RunContext(asset_id="asset-1", location_id="weld-17", time_basis="campaign-1"),
    )
    assert result.status == "computed"
    assert result.source_ids == ("radiographic_examination_geometry_definition",)
    assert result.probability_semantics == {}

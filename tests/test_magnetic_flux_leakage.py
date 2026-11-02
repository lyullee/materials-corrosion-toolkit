from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.magnetic_flux_leakage import (
    MflExamination,
    magnetic_flux_leakage_acquisition_summary,
)
from matintegrity.registry import default_registry


def _evidence():
    return [
        Evidence(
            source_id="authored-mfl-fixture",
            origin="synthetic",
            citation="authored MFL fixture",
        )
    ]


def _record():
    evidence = _evidence()
    return {
        "examination_id": "mfl-exam-1",
        "procedure_id": "mfl-procedure",
        "procedure_revision": "A",
        "physical_scope_id": "plate-zone-1",
        "material_id": "steel-fixture",
        "material_condition_id": "authored-condition",
        "surface_condition": "clean authored plate",
        "magnetizer": {
            "magnetizer_id": "magnetizer-1",
            "excitation_type": "electromagnet",
            "nominal_magnetization_direction": "axial",
            "pole_spacing_m": 0.1,
            "excitation_current_A": 4.0,
            "excitation_current_basis": "authored current setting",
            "magnetization_control_basis": "authored fixture",
            "evidence": evidence,
        },
        "sensor_arrays": [
            {
                "sensor_array_id": "array-1",
                "channel_ids": ["bx", "bz"],
                "measured_components": ["axial", "radial"],
                "channel_component_by_id": {"bx": "axial", "bz": "radial"},
                "nominal_channel_pitch_m": 0.002,
                "lift_off_control_basis": "fixed authored spacer",
                "calibration_id": "cal-1",
                "calibration_basis": "authored synthetic calibration",
                "evidence": evidence,
            }
        ],
        "reference_standard": {
            "reference_standard_id": "standard-1",
            "material_id": "steel-fixture",
            "material_condition_id": "authored-condition",
            "wall_thickness_m": 0.01,
            "applicable_magnetizer_ids": ["magnetizer-1"],
            "applicable_sensor_array_ids": ["array-1"],
            "features": [
                {
                    "feature_id": "feature-1",
                    "feature_kind": "flat_bottom_recess",
                    "surface": "external",
                    "geometry_description": "authored rectangular recess",
                    "nominal_depth_m": 0.002,
                    "nominal_length_m": 0.01,
                    "nominal_width_m": 0.006,
                    "physical_feature_identity_reviewed": True,
                    "evidence": evidence,
                }
            ],
            "evidence": evidence,
        },
        "magnetic_field_checkpoints": [
            {
                "checkpoint_id": "field-1",
                "physical_location_description": "authored plate centre",
                "coordinate_frame": "x axial, y circumferential, z outward",
                "magnetic_field_strength_A_m": (3000.0, 4000.0, 0.0),
                "magnetic_flux_density_T": (0.6, 0.8, 0.0),
                "measurement_temperature_K": 293.15,
                "measurement_basis": "authored exact vector",
                "state_identity_reviewed": True,
                "evidence": evidence,
            }
        ],
        "scans": [
            {
                "scan_id": "scan-1",
                "magnetizer_id": "magnetizer-1",
                "sensor_array_id": "array-1",
                "active_channel_ids": ["bx", "bz"],
                "data_sha256": "1" * 64,
                "sample_count": 6,
                "signal_encoding": "authored float fixture",
                "signal_unit_token": "T",
                "pass_direction": "forward",
                "scan_speed_m_s": 0.05,
                "scan_speed_basis": "authored constant speed",
                "sample_spacing_m": 0.002,
                "encoder_origin_m": 0.1,
                "coordinate_mapping_basis": "authored linear encoder",
                "acquisition_order": 0,
                "time_basis": "authored scan order",
            }
        ],
        "indications": [
            {
                "indication_id": "indication-1",
                "scan_ids": ["scan-1"],
                "reported_indication_type": "provider response region",
                "signal_response_description": "authored evidence-bound response",
                "reference_feature_ids": ["feature-1"],
                "physical_location_id": "plate-zone-1-location-1",
                "object_mapping_basis": "authored coordinate mapping",
                "evidence": evidence,
            }
        ],
        "magnetizer_identity_reviewed": True,
        "sensor_calibration_reviewed": True,
        "reference_standard_reviewed": True,
        "magnetization_state_reviewed": True,
        "lift_off_and_surface_condition_reviewed": True,
        "encoder_calibration_reviewed": True,
        "scan_identity_reviewed": True,
        "indication_mapping_reviewed": True,
        "negative_result_reviewed": False,
        "evidence": evidence,
    }


def test_mfl_summary_reports_only_bounded_descriptors():
    result = magnetic_flux_leakage_acquisition_summary(MflExamination.model_validate(_record()))
    assert result.status == "computed"
    assert result.values["scan_geometry_by_id"]["scan-1"]["encoded_span_m"] == pytest.approx(0.01)
    checkpoint = result.values["magnetic_field_checkpoints"]["field-1"]
    assert checkpoint["magnetic_field_strength_magnitude_A_m"] == 5000.0
    assert checkpoint["magnetic_flux_density_magnitude_T"] == 1.0
    assert checkpoint["magnitude_ratio_B_T_per_H_A_m"] == pytest.approx(2e-4)
    assert all("probability" not in key for key in result.values)


def test_mfl_vector_magnitude_matches_independent_norm():
    result = magnetic_flux_leakage_acquisition_summary(MflExamination.model_validate(_record()))
    checkpoint = result.values["magnetic_field_checkpoints"]["field-1"]
    assert checkpoint["magnetic_field_strength_magnitude_A_m"] == math.hypot(3000.0, 4000.0)
    assert checkpoint["magnetic_flux_density_magnitude_T"] == math.hypot(0.6, 0.8)


@pytest.mark.parametrize(
    ("field", "missing_name"),
    [
        ("magnetizer_identity_reviewed", "magnetizer_identity_reviewed"),
        ("sensor_calibration_reviewed", "sensor_calibration_reviewed"),
        ("magnetization_state_reviewed", "magnetization_state_reviewed"),
    ],
)
def test_mfl_missing_reviews_remain_needs_data(field, missing_name):
    values = _record()
    values[field] = False
    result = magnetic_flux_leakage_acquisition_summary(MflExamination.model_validate(values))
    assert result.status == "needs_data"
    assert missing_name in result.values["missing_reviews"]


def test_mfl_missing_checkpoint_and_unreviewed_negative_result_remain_needs_data():
    values = _record()
    values["magnetic_field_checkpoints"] = []
    values["indications"] = []
    result = magnetic_flux_leakage_acquisition_summary(MflExamination.model_validate(values))
    assert result.status == "needs_data"
    assert "magnetic_field_checkpoint" in result.values["missing_reviews"]
    assert "negative_result_reviewed" in result.values["missing_reviews"]
    values["negative_result_reviewed"] = True
    assert (
        magnetic_flux_leakage_acquisition_summary(MflExamination.model_validate(values)).status
        == "needs_data"
    )


def test_mfl_unmapped_indication_remains_needs_data():
    values = _record()
    values["indications"][0]["physical_location_id"] = None
    values["indications"][0]["object_mapping_basis"] = None
    result = magnetic_flux_leakage_acquisition_summary(MflExamination.model_validate(values))
    assert result.status == "needs_data"
    assert result.values["unmapped_indication_ids"] == ["indication-1"]


def test_mfl_rejects_incomplete_current_and_coordinate_pairs():
    values = _record()
    values["magnetizer"]["excitation_current_basis"] = None
    with pytest.raises(ValidationError, match="current and basis"):
        MflExamination.model_validate(values)
    values = _record()
    values["scans"][0]["sample_spacing_m"] = None
    with pytest.raises(ValidationError, match="coordinates require"):
        MflExamination.model_validate(values)


def test_mfl_rejects_channel_mapping_and_scan_channel_mismatches():
    values = _record()
    values["sensor_arrays"][0]["channel_component_by_id"] = {"bx": "axial"}
    with pytest.raises(ValidationError, match="cover every channel"):
        MflExamination.model_validate(values)
    values = _record()
    values["scans"][0]["active_channel_ids"].append("unknown")
    with pytest.raises(ValidationError, match="absent from its sensor array"):
        MflExamination.model_validate(values)


def test_mfl_rejects_reference_and_identity_mismatches():
    values = _record()
    values["reference_standard"]["applicable_magnetizer_ids"] = ["other"]
    with pytest.raises(ValidationError, match="does not cover the examination magnetizer"):
        MflExamination.model_validate(values)
    values = _record()
    values["indications"][0]["reference_feature_ids"] = ["unknown"]
    with pytest.raises(ValidationError, match="reference feature"):
        MflExamination.model_validate(values)


def test_mfl_rejects_nonfinite_and_empty_field_checkpoint():
    values = _record()
    values["magnetic_field_checkpoints"][0]["magnetic_field_strength_A_m"] = None
    values["magnetic_field_checkpoints"][0]["magnetic_flux_density_T"] = None
    with pytest.raises(ValidationError, match="requires H or B"):
        MflExamination.model_validate(values)
    values = _record()
    values["magnetic_field_checkpoints"][0]["magnetic_flux_density_T"] = (
        float("inf"),
        0.0,
        0.0,
    )
    with pytest.raises(ValidationError, match="finite"):
        MflExamination.model_validate(values)


def test_registry_exposes_mfl_contract_without_probability_semantics():
    registry = default_registry()
    description = registry.describe("inspection.magnetic_flux_leakage_acquisition_summary")
    assert description["input_schema"]["title"] == "MflExamination"
    result = registry.run(
        "inspection.magnetic_flux_leakage_acquisition_summary",
        _record(),
        RunContext(asset_id="asset", location_id="plate", time_basis="scan order"),
    )
    assert result.source_ids == ("magnetic_flux_leakage_acquisition_definition",)
    assert result.probability_semantics == {}

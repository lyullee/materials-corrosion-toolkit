from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.eddy_current import (
    VACUUM_PERMEABILITY_H_M,
    EddyCurrentExamination,
    eddy_current_acquisition_summary,
)
from matintegrity.registry import default_registry


def _evidence():
    return Evidence(source_id="authored-ec", origin="synthetic", citation="authored eddy-current case")


def _record():
    return {
        "examination_id": "ec-exam-1",
        "procedure_id": "ec-procedure",
        "procedure_revision": "1",
        "physical_scope_id": "surface-1",
        "material_id": "copper",
        "material_condition_id": "annealed",
        "probe": {
            "probe_id": "probe-1",
            "probe_mode": "absolute",
            "coil_configuration": "authored single coil",
            "nominal_excitation_frequencies_Hz": [100000.0],
            "active_channel_ids": ["real", "imaginary"],
            "probe_geometry_basis": "authored geometry",
            "lift_off_control_basis": "authored fixed lift-off",
            "evidence": [_evidence()],
        },
        "reference_standard": {
            "reference_standard_id": "reference-1",
            "material_id": "copper",
            "material_condition_id": "annealed",
            "applicable_probe_ids": ["probe-1"],
            "applicable_frequencies_Hz": [100000.0],
            "conductivity_S_m": 58e6,
            "relative_magnetic_permeability": 1.0,
            "property_temperature_K": 293.15,
            "electromagnetic_property_basis": "authored exact properties",
            "features": [
                {
                    "feature_id": "slot-1",
                    "feature_kind": "electrical-discharge-machined slot",
                    "geometry_description": "authored reference feature",
                    "nominal_depth_m": 0.001,
                    "nominal_length_m": 0.005,
                    "nominal_width_m": 0.0002,
                    "physical_feature_identity_reviewed": True,
                    "evidence": [_evidence()],
                }
            ],
            "evidence": [_evidence()],
        },
        "scans": [
            {
                "scan_id": "scan-1",
                "probe_id": "probe-1",
                "excitation_frequency_Hz": 100000.0,
                "data_sha256": "1" * 64,
                "row_count": 3,
                "column_count": 4,
                "component_order": ["real", "imaginary"],
                "signal_encoding": "signed_int16_with_external_scale",
                "signal_unit_token": "provider_voltage_token",
                "x_increment_m": 0.001,
                "y_increment_m": 0.002,
                "coordinate_mapping_basis": "authored raster map",
                "scan_origin_x_m": 0.0,
                "scan_origin_y_m": 0.0,
                "acquisition_order": 0,
                "time_basis": "authored scan order",
            }
        ],
        "indications": [
            {
                "indication_id": "indication-1",
                "scan_ids": ["scan-1"],
                "reported_indication_type": "user-reported response",
                "signal_response_description": "response near reference-like location",
                "reference_feature_ids": ["slot-1"],
                "physical_location_id": "surface-location-1",
                "object_mapping_basis": "authored raster-to-part map",
                "evidence": [_evidence()],
            }
        ],
        "probe_identity_reviewed": True,
        "reference_standard_reviewed": True,
        "excitation_and_receiver_settings_reviewed": True,
        "lift_off_and_surface_condition_reviewed": True,
        "encoder_calibration_reviewed": True,
        "scan_identity_reviewed": True,
        "indication_mapping_reviewed": True,
        "linear_homogeneous_skin_depth_applicable": True,
        "evidence": [_evidence()],
    }


def test_eddy_current_summary_computes_only_reviewed_geometry_and_skin_depth():
    result = eddy_current_acquisition_summary(EddyCurrentExamination.model_validate(_record()))
    assert result.status == "computed"
    geometry = result.values["scan_geometry_by_id"]["scan-1"]
    assert geometry["x_span_m"] == pytest.approx(0.003)
    assert geometry["y_span_m"] == pytest.approx(0.004)
    assert geometry["sample_position_count"] == 12
    expected = math.sqrt(1 / (math.pi * 100000.0 * VACUUM_PERMEABILITY_H_M * 58e6))
    assert result.values["skin_depth_m_by_frequency_Hz"]["100000.0"] == pytest.approx(expected)
    assert result.values["skin_depth_model_applied"] is True


def test_missing_coordinates_remain_unmapped_without_synthesized_spacing():
    values = _record()
    scan = values["scans"][0]
    for key in (
        "x_increment_m",
        "y_increment_m",
        "coordinate_mapping_basis",
        "scan_origin_x_m",
        "scan_origin_y_m",
    ):
        scan[key] = None
    result = eddy_current_acquisition_summary(EddyCurrentExamination.model_validate(values))
    geometry = result.values["scan_geometry_by_id"]["scan-1"]
    assert geometry["coordinate_mapping_available"] is False
    assert geometry["x_span_m"] is None
    assert result.status == "computed"


def test_skin_depth_requires_complete_properties_and_applicability_review():
    values = _record()
    standard = values["reference_standard"]
    for key in (
        "conductivity_S_m",
        "relative_magnetic_permeability",
        "property_temperature_K",
        "electromagnetic_property_basis",
    ):
        standard[key] = None
    pending = eddy_current_acquisition_summary(EddyCurrentExamination.model_validate(values))
    assert pending.status == "needs_data"
    assert "electromagnetic_property_values" in pending.values["missing_reviews"]
    values["linear_homogeneous_skin_depth_applicable"] = False
    bounded = eddy_current_acquisition_summary(EddyCurrentExamination.model_validate(values))
    assert bounded.status == "computed"
    assert bounded.values["skin_depth_m_by_frequency_Hz"] == {}


def test_unmapped_indication_and_unreviewed_reference_feature_need_data():
    values = _record()
    values["indications"][0]["physical_location_id"] = None
    values["indications"][0]["object_mapping_basis"] = None
    values["reference_standard"]["features"][0]["physical_feature_identity_reviewed"] = False
    result = eddy_current_acquisition_summary(EddyCurrentExamination.model_validate(values))
    assert result.status == "needs_data"
    assert result.values["unmapped_indication_ids"] == ["indication-1"]
    assert "reference_feature_identity_reviewed" in result.values["missing_reviews"]


def test_empty_indications_require_separate_negative_result_review():
    values = _record()
    values["indications"] = []
    pending = eddy_current_acquisition_summary(EddyCurrentExamination.model_validate(values))
    assert pending.status == "needs_data"
    values["negative_result_reviewed"] = True
    assert (
        eddy_current_acquisition_summary(EddyCurrentExamination.model_validate(values)).status == "computed"
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda x: x["scans"][0].update(probe_id="other"), "examination probe"),
        (lambda x: x["scans"][0].update(excitation_frequency_Hz=200000.0), "not declared"),
        (lambda x: x["indications"][0].update(scan_ids=["missing"]), "scan must be declared"),
        (
            lambda x: x["indications"][0].update(reference_feature_ids=["missing"]),
            "feature must be declared",
        ),
    ],
)
def test_rejects_broken_probe_frequency_scan_and_reference_links(mutation, message):
    values = _record()
    mutation(values)
    with pytest.raises(ValidationError, match=message):
        EddyCurrentExamination.model_validate(values)


def test_rejects_partial_property_and_coordinate_contracts():
    values = _record()
    values["reference_standard"]["relative_magnetic_permeability"] = None
    with pytest.raises(ValidationError, match="properties require"):
        EddyCurrentExamination.model_validate(values)
    values = _record()
    values["scans"][0]["x_increment_m"] = None
    with pytest.raises(ValidationError, match="coordinates require"):
        EddyCurrentExamination.model_validate(values)


def test_rejects_duplicate_channels_components_and_acquisition_order():
    values = _record()
    values["probe"]["active_channel_ids"] = ["real", "real"]
    with pytest.raises(ValidationError, match="channel IDs"):
        EddyCurrentExamination.model_validate(values)
    values = _record()
    values["scans"][0]["component_order"] = ["real", "real"]
    with pytest.raises(ValidationError, match="components"):
        EddyCurrentExamination.model_validate(values)
    values = _record()
    values["scans"].append({**values["scans"][0], "scan_id": "scan-2"})
    with pytest.raises(ValidationError, match="acquisition order"):
        EddyCurrentExamination.model_validate(values)


def test_registry_exposes_eddy_current_contract_without_probability_semantics():
    registry = default_registry()
    description = registry.describe("inspection.eddy_current_acquisition_summary")
    assert description["input_schema"]["title"] == "EddyCurrentExamination"
    result = registry.run(
        "inspection.eddy_current_acquisition_summary",
        _record(),
        RunContext(asset_id="asset", location_id="surface", time_basis="scan order"),
    )
    assert result.source_ids == ("eddy_current_acquisition_definition",)
    assert result.probability_semantics == {}

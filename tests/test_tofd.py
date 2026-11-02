from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.tofd import TofdExamination, tofd_acquisition_summary
from matintegrity.registry import default_registry


def _evidence():
    return Evidence(source_id="authored-tofd", origin="synthetic", citation="authored geometry case")


def _delay(depth, separation=0.04, velocity=5900.0):
    return (2 * math.hypot(separation / 2, depth) - separation) / velocity


def _record():
    lateral = 10e-6
    return {
        "examination_id": "tofd-exam-1",
        "procedure_id": "tofd-procedure",
        "procedure_revision": "1",
        "physical_scope_id": "weld-volume-1",
        "material_condition_id": "steel-condition-1",
        "specimen_longitudinal_velocity_m_s": 5900.0,
        "specimen_velocity_basis": "reviewed reference block",
        "wall_thickness_m": 0.025,
        "wall_thickness_basis": "reviewed local thickness",
        "probe_pair": {
            "pair_id": "pair-1",
            "transmit_probe_id": "tx-1",
            "receive_probe_id": "rx-1",
            "transmit_wedge_id": "tx-wedge",
            "receive_wedge_id": "rx-wedge",
            "probe_index_separation_m": 0.04,
            "center_frequency_Hz": 10e6,
            "nominal_refracted_angle_rad": 1.0,
            "index_separation_basis": "measured index points",
            "evidence": [_evidence()],
        },
        "encoder_id": "encoder-1",
        "encoder_direction": "increasing",
        "frames": [
            {
                "frame_id": "frame-1",
                "encoder_position_m": 0.0,
                "data_sha256": "1" * 64,
                "sample_count": 1000,
                "sample_interval_s": 1e-8,
                "amplitude_encoding": "signed_int16",
                "time_zero_basis": "reviewed acquisition clock",
                "lateral_wave_arrival_time_s": lateral,
                "backwall_echo_arrival_time_s": lateral + _delay(0.025),
            },
            {
                "frame_id": "frame-2",
                "encoder_position_m": 0.001,
                "data_sha256": "2" * 64,
                "sample_count": 1000,
                "sample_interval_s": 1e-8,
                "amplitude_encoding": "signed_int16",
                "time_zero_basis": "reviewed acquisition clock",
                "lateral_wave_arrival_time_s": lateral,
                "backwall_echo_arrival_time_s": lateral + _delay(0.025),
            },
        ],
        "diffraction_picks": [
            {
                "pick_id": "upper-1",
                "frame_id": "frame-1",
                "reported_role": "upper_tip",
                "arrival_time_s": lateral + _delay(0.005),
                "picking_basis": "authored synthetic pick",
                "evidence": [_evidence()],
            },
            {
                "pick_id": "lower-1",
                "frame_id": "frame-1",
                "reported_role": "lower_tip",
                "arrival_time_s": lateral + _delay(0.015),
                "picking_basis": "authored synthetic pick",
                "evidence": [_evidence()],
            },
        ],
        "indications": [
            {
                "indication_id": "indication-1",
                "upper_tip_pick_id": "upper-1",
                "lower_tip_pick_id": "lower-1",
                "reported_indication_type": "provider-reported diffraction pair",
                "acquisition_location_description": "frame 1",
                "physical_location_id": "weld-location-1",
                "object_mapping_basis": "reviewed encoder-to-weld map",
                "evidence": [_evidence()],
            }
        ],
        "probe_pair_identity_reviewed": True,
        "specimen_velocity_reviewed": True,
        "wall_thickness_reviewed": True,
        "encoder_calibration_reviewed": True,
        "acquisition_calibration_reviewed": True,
        "frame_identity_reviewed": True,
        "time_picks_reviewed": True,
        "indication_mapping_reviewed": True,
        "symmetric_path_applicable": True,
        "evidence": [_evidence()],
    }


def test_tofd_summary_recovers_authored_tip_and_backwall_geometry():
    result = tofd_acquisition_summary(TofdExamination.model_validate(_record()))
    assert result.status == "computed"
    assert result.values["tip_depth_by_pick_id"]["upper-1"] == pytest.approx(0.005)
    assert result.values["tip_depth_by_pick_id"]["lower-1"] == pytest.approx(0.015)
    geometry = result.values["indication_geometry_by_id"]["indication-1"]
    assert geometry["tip_separation_height_m"] == pytest.approx(0.01)
    assert geometry["remaining_backwall_ligament_m"] == pytest.approx(0.01)
    backwall = result.values["backwall_timing_diagnostics_by_frame_id"]["frame-1"]
    assert backwall["equivalent_backwall_depth_m"] == pytest.approx(0.025)
    assert backwall["equivalent_depth_minus_declared_wall_m"] == pytest.approx(0.0, abs=1e-15)


def test_frame_order_and_duplicate_encoder_positions_are_preserved():
    values = _record()
    values["frames"][1]["encoder_position_m"] = 0.0
    result = tofd_acquisition_summary(TofdExamination.model_validate(values))
    assert result.values["duplicate_adjacent_encoder_position_count"] == 1
    assert result.values["unique_encoder_position_count"] == 1
    assert result.values["encoder_span_m"] == 0.0


def test_missing_lateral_reference_keeps_pick_visible_as_needs_data():
    values = _record()
    values["frames"][0]["lateral_wave_arrival_time_s"] = None
    values["frames"][0]["backwall_echo_arrival_time_s"] = None
    result = tofd_acquisition_summary(TofdExamination.model_validate(values))
    assert result.status == "needs_data"
    assert result.values["tip_depth_by_pick_id"] == {"upper-1": None, "lower-1": None}
    assert result.values["invalid_pick_ids"] == ["upper-1", "lower-1"]


def test_pick_before_lateral_wave_is_not_converted_to_depth():
    values = _record()
    values["diffraction_picks"][0]["arrival_time_s"] = 9e-6
    result = tofd_acquisition_summary(TofdExamination.model_validate(values))
    assert result.status == "needs_data"
    assert result.values["tip_depth_by_pick_id"]["upper-1"] is None


def test_reversed_reported_tip_order_is_diagnostic_not_silently_swapped():
    values = _record()
    values["diffraction_picks"][0]["arrival_time_s"] = 10e-6 + _delay(0.02)
    result = tofd_acquisition_summary(TofdExamination.model_validate(values))
    assert result.status == "needs_data"
    assert result.values["inconsistent_indication_ids"] == ["indication-1"]
    geometry = result.values["indication_geometry_by_id"]["indication-1"]
    assert geometry["upper_tip_depth_m"] == pytest.approx(0.02)
    assert geometry["lower_tip_depth_m"] == pytest.approx(0.015)
    assert geometry["tip_separation_height_m"] is None


def test_unmapped_indication_and_unreviewed_assumption_are_needs_data():
    values = _record()
    values["indications"][0]["physical_location_id"] = None
    values["indications"][0]["object_mapping_basis"] = None
    values["symmetric_path_applicable"] = False
    result = tofd_acquisition_summary(TofdExamination.model_validate(values))
    assert result.status == "needs_data"
    assert result.values["unmapped_indication_ids"] == ["indication-1"]
    assert "symmetric_path_applicable" in result.values["missing_reviews"]


def test_empty_indications_require_explicit_negative_result_review():
    values = _record()
    values["diffraction_picks"] = []
    values["indications"] = []
    pending = tofd_acquisition_summary(TofdExamination.model_validate(values))
    assert pending.status == "needs_data"
    values["negative_result_reviewed"] = True
    reviewed = tofd_acquisition_summary(TofdExamination.model_validate(values))
    assert reviewed.status == "computed"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda x: x["diffraction_picks"][0].update(frame_id="missing"), "declared frame"),
        (lambda x: x["indications"][0].update(upper_tip_pick_id="missing"), "pick must be declared"),
        (
            lambda x: x["indications"][0].update(upper_tip_pick_id="lower-1", lower_tip_pick_id=None),
            "tip role conflicts",
        ),
        (lambda x: x["frames"][1].update(encoder_position_m=-0.001), "encoder positions"),
    ],
)
def test_rejects_broken_identity_role_and_encoder_links(mutation, message):
    values = _record()
    mutation(values)
    with pytest.raises(ValidationError, match=message):
        TofdExamination.model_validate(values)


def test_rejects_shared_tip_pick_and_backwall_before_lateral():
    values = _record()
    values["indications"].append(
        {
            **values["indications"][0],
            "indication_id": "indication-2",
            "lower_tip_pick_id": None,
        }
    )
    with pytest.raises(ValidationError, match="multiple indications"):
        TofdExamination.model_validate(values)

    values = _record()
    values["frames"][0]["backwall_echo_arrival_time_s"] = 9e-6
    with pytest.raises(ValidationError, match="backwall arrival"):
        TofdExamination.model_validate(values)


def test_registry_exposes_tofd_contract_without_probability_semantics():
    registry = default_registry()
    spec = registry.describe("inspection.tofd_acquisition_summary")
    assert spec["input_schema"]["title"] == "TofdExamination"
    assert spec["source_ids"] == ("tofd_acquisition_definition",)
    result = registry.run(
        "inspection.tofd_acquisition_summary",
        _record(),
        RunContext(asset_id="asset", location_id="weld", time_basis="acquisition clock"),
    )
    assert result.status == "computed"
    assert result.probability_semantics == {}

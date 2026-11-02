import copy

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.models.phased_array import (
    PhasedArrayExamination,
    phased_array_acquisition_summary,
)
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "user-paut-record",
    "origin": "user_declared",
    "citation": "caller-controlled phased-array acquisition record",
}


def _record(**updates):
    values = {
        "examination_id": "paut-001",
        "procedure_id": "user-paut-procedure",
        "procedure_revision": "2",
        "physical_scope_id": "weld-22",
        "material_condition_id": "steel-weld-condition-a",
        "acquisition_mode": "transmit_receive",
        "specimen_wave_velocity_m_s": 5900.0,
        "specimen_wave_velocity_basis": "caller-reviewed reference-block record",
        "encoder_id": "encoder-1",
        "encoder_direction": "increasing",
        "probes": [
            {
                "probe_id": "tx",
                "role": "transmit",
                "element_count": 4,
                "element_pitch_m": 0.001,
                "element_width_m": 0.0008,
                "center_frequency_Hz": 5.0e6,
                "element_layout_basis": "caller-controlled probe datasheet",
                "evidence": [EVIDENCE],
            },
            {
                "probe_id": "rx",
                "role": "receive",
                "element_count": 4,
                "element_pitch_m": 0.001,
                "element_width_m": 0.0008,
                "center_frequency_Hz": 5.0e6,
                "element_layout_basis": "caller-controlled probe datasheet",
                "evidence": [EVIDENCE],
            },
        ],
        "wedges": [
            {
                "wedge_id": "wedge-tx",
                "probe_id": "tx",
                "wedge_material_id": "polymer-a",
                "wedge_longitudinal_velocity_m_s": 2300.0,
                "nominal_exit_point_offset_m": 0.01,
                "mounting_orientation": "transmit side",
                "evidence": [EVIDENCE],
            },
            {
                "wedge_id": "wedge-rx",
                "probe_id": "rx",
                "wedge_material_id": "polymer-a",
                "wedge_longitudinal_velocity_m_s": 2300.0,
                "nominal_exit_point_offset_m": -0.01,
                "mounting_orientation": "receive side",
                "evidence": [EVIDENCE],
            },
        ],
        "beam_laws": [
            {
                "law_id": "law-a",
                "transmit_probe_id": "tx",
                "receive_probe_id": "rx",
                "refracted_angle_rad": 0.6,
                "refracted_wave_mode": "longitudinal",
                "focus_distance_m": 0.02,
                "first_transmit_element": 0,
                "transmit_element_count": 4,
                "transmit_delay_s": [0.0, 1.0e-8, 2.0e-8, 3.0e-8],
                "first_receive_element": 0,
                "receive_element_count": 4,
                "receive_delay_s": [3.0e-8, 2.0e-8, 1.0e-8, 0.0],
                "law_generation_basis": "caller-controlled focal-law export",
            },
            {
                "law_id": "law-b",
                "transmit_probe_id": "tx",
                "receive_probe_id": "rx",
                "refracted_angle_rad": 0.8,
                "refracted_wave_mode": "longitudinal",
                "focus_distance_m": 0.02,
                "first_transmit_element": 0,
                "transmit_element_count": 4,
                "transmit_delay_s": [0.0, 2.0e-8, 4.0e-8, 6.0e-8],
                "first_receive_element": 0,
                "receive_element_count": 4,
                "receive_delay_s": [6.0e-8, 4.0e-8, 2.0e-8, 0.0],
                "law_generation_basis": "caller-controlled focal-law export",
            },
        ],
        "frames": [
            {
                "frame_id": "frame-0-a",
                "encoder_position_m": 0.0,
                "beam_law_id": "law-a",
                "data_sha256": "a" * 64,
                "sample_count": 1024,
                "sample_interval_s": 1.0e-8,
                "transmit_event_count": 1,
                "receive_channel_count": 4,
                "amplitude_encoding": "signed-int16",
                "time_zero_basis": "caller-controlled acquisition clock",
            },
            {
                "frame_id": "frame-0-b",
                "encoder_position_m": 0.0,
                "beam_law_id": "law-b",
                "data_sha256": "b" * 64,
                "sample_count": 1024,
                "sample_interval_s": 1.0e-8,
                "transmit_event_count": 1,
                "receive_channel_count": 4,
                "amplitude_encoding": "signed-int16",
                "time_zero_basis": "caller-controlled acquisition clock",
            },
            {
                "frame_id": "frame-1-a",
                "encoder_position_m": 0.001,
                "beam_law_id": "law-a",
                "data_sha256": "c" * 64,
                "sample_count": 1024,
                "sample_interval_s": 1.0e-8,
                "transmit_event_count": 1,
                "receive_channel_count": 4,
                "amplitude_encoding": "signed-int16",
                "time_zero_basis": "caller-controlled acquisition clock",
            },
            {
                "frame_id": "frame-1-b",
                "encoder_position_m": 0.001,
                "beam_law_id": "law-b",
                "data_sha256": "d" * 64,
                "sample_count": 1024,
                "sample_interval_s": 1.0e-8,
                "transmit_event_count": 1,
                "receive_channel_count": 4,
                "amplitude_encoding": "signed-int16",
                "time_zero_basis": "caller-controlled acquisition clock",
            },
        ],
        "indications": [],
        "probe_and_wedge_identity_reviewed": True,
        "material_velocity_reviewed": True,
        "beam_law_reviewed": True,
        "encoder_calibration_reviewed": True,
        "acquisition_calibration_reviewed": True,
        "frame_identity_reviewed": True,
        "indication_mapping_reviewed": True,
        "negative_result_reviewed": True,
        "evidence": [EVIDENCE],
    }
    values.update(updates)
    return copy.deepcopy(values)


def test_probe_and_encoder_descriptors_match_independent_arithmetic():
    result = phased_array_acquisition_summary(PhasedArrayExamination.model_validate(_record()))
    assert result.status == "computed"
    probe = result.values["probe_geometry_by_id"]["tx"]
    assert probe["physical_aperture_m"] == pytest.approx(0.0038)
    assert probe["nominal_specimen_wavelength_m"] == pytest.approx(5900.0 / 5.0e6)
    assert probe["pitch_to_nominal_wavelength_ratio"] == pytest.approx(0.001 / (5900 / 5e6))
    assert result.values["encoder_span_m"] == pytest.approx(0.001)
    assert result.values["minimum_nonzero_encoder_increment_m"] == pytest.approx(0.001)
    assert result.values["duplicate_adjacent_encoder_position_count"] == 2
    assert result.values["frame_count_by_beam_law_id"] == {"law-a": 2, "law-b": 2}


def test_delay_spans_are_descriptive_and_no_acceptance_is_returned():
    result = phased_array_acquisition_summary(PhasedArrayExamination.model_validate(_record()))
    assert result.values["beam_law_delay_span_by_id"]["law-a"] == {
        "transmit_delay_span_s": pytest.approx(3.0e-8),
        "receive_delay_span_s": pytest.approx(3.0e-8),
    }
    assert not any("accept" in key for key in result.values)


def test_unmapped_indication_is_preserved_as_needs_data():
    indication = {
        "indication_id": "ind-1",
        "frame_ids": ["frame-0-a", "frame-0-b"],
        "reported_indication_type": "caller-reported response",
        "acquisition_location_description": "encoded position zero",
        "evidence": [EVIDENCE],
    }
    result = phased_array_acquisition_summary(
        PhasedArrayExamination.model_validate(_record(indications=[indication]))
    )
    assert result.status == "needs_data"
    assert result.values["unmapped_indication_ids"] == ["ind-1"]


def test_empty_indication_list_requires_negative_result_review():
    result = phased_array_acquisition_summary(
        PhasedArrayExamination.model_validate(_record(negative_result_reviewed=False))
    )
    assert result.status == "needs_data"
    assert result.values["missing_reviews"] == ["negative_result_reviewed"]


def test_full_matrix_capture_uses_frames_without_beam_law():
    values = _record(acquisition_mode="full_matrix_capture", beam_laws=[])
    for frame in values["frames"]:
        frame["beam_law_id"] = None
        frame["transmit_event_count"] = 4
    result = phased_array_acquisition_summary(PhasedArrayExamination.model_validate(values))
    assert result.status == "computed"
    assert result.values["beam_law_count"] == 0
    assert result.values["frame_count_by_beam_law_id"] == {"full_matrix_capture": 4}


@pytest.mark.parametrize(
    "mutator",
    [
        lambda x: x["beam_laws"][0].update(transmit_delay_s=[0.0]),
        lambda x: x["beam_laws"][0].update(first_transmit_element=2),
        lambda x: x["frames"][2].update(encoder_position_m=-0.001),
        lambda x: x["frames"][0].update(beam_law_id="unknown"),
        lambda x: x["wedges"][0].update(probe_id="unknown"),
    ],
)
def test_linkage_delay_aperture_and_encoder_errors_are_rejected(mutator):
    values = _record()
    mutator(values)
    with pytest.raises(ValidationError):
        PhasedArrayExamination.model_validate(values)


def test_registry_route_has_no_probability_semantics():
    result = default_registry().run(
        "inspection.phased_array_acquisition_summary",
        _record(),
        RunContext(asset_id="asset-1", location_id="weld-22", time_basis="campaign-1"),
    )
    assert result.status == "computed"
    assert result.source_ids == ("phased_array_acquisition_definition",)
    assert result.probability_semantics == {}

import json
import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.acoustic_emission_speed import (
    AcousticEmissionWaveSpeedCalibration,
    acoustic_emission_wave_speed_calibration,
    specifications,
)
from matintegrity.registry import ModelRegistry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored"}
D = "a" * 64


def payload(**updates):
    sensors = [
        {
            "sensor_id": "s0",
            "channel_id": "c0",
            "coordinate_frame_id": "f",
            "position_m": [0, 0, 0],
            "calibration_id": "cal",
            "calibration_state_digest": D,
            "evidence": [E],
        },
        {
            "sensor_id": "s1",
            "channel_id": "c1",
            "coordinate_frame_id": "f",
            "position_m": [2, 0, 0],
            "calibration_id": "cal",
            "calibration_state_digest": D,
            "evidence": [E],
        },
    ]
    sources = [
        {
            "source_id": "src1",
            "physical_specimen_id": "p1",
            "source_group_id": "g1",
            "partition": "calibration",
            "coordinate_frame_id": "f",
            "position_m": [0.5, 0, 0],
            "emission_reference_time_s": 0.01,
            "source_definition_id": "known",
            "source_record_digest": D,
            "evidence": [E],
        },
        {
            "source_id": "src2",
            "physical_specimen_id": "p2",
            "source_group_id": "g2",
            "partition": "calibration",
            "coordinate_frame_id": "f",
            "position_m": [1, 0, 0],
            "emission_reference_time_s": 0.02,
            "source_definition_id": "known",
            "source_record_digest": D,
            "evidence": [E],
        },
        {
            "source_id": "src3",
            "physical_specimen_id": "p3",
            "source_group_id": "g3",
            "partition": "holdout",
            "coordinate_frame_id": "f",
            "position_m": [0.75, 0, 0],
            "emission_reference_time_s": 0.03,
            "source_definition_id": "known",
            "source_record_digest": D,
            "evidence": [E],
        },
    ]
    speed = 5000.0
    offset = 0.001
    picks = []
    for src in sources:
        for sensor in sensors:
            dist = math.dist(src["position_m"], sensor["position_m"])
            picks.append(
                {
                    "pick_id": src["source_id"] + sensor["sensor_id"],
                    "source_id": src["source_id"],
                    "sensor_id": sensor["sensor_id"],
                    "channel_id": sensor["channel_id"],
                    "clock_id": "clock",
                    "arrival_time_s": src["emission_reference_time_s"] + offset + dist / speed,
                    "standard_uncertainty_s": 1e-6,
                    "pick_method_id": "method",
                    "source_trace_digest": D,
                    "result_digest": D,
                    "record_status": "valid",
                    "evidence": [E],
                }
            )
    v = {
        "calibration_id": "fit",
        "asset_id": "a",
        "location_id": "l",
        "coordinate_frame_id": "f",
        "clock_id": "clock",
        "sensors": sensors,
        "known_sources": sources,
        "picks": picks,
        "minimum_supported_wave_speed_m_s": 4000,
        "maximum_supported_wave_speed_m_s": 6000,
        "minimum_calibration_distance_span_m": 0.5,
        "minimum_calibration_source_count": 2,
        "minimum_holdout_source_count": 1,
        "sensor_source_coordinates_and_frame_reviewed": True,
        "clock_and_emission_reference_reviewed": True,
        "pick_methods_uncertainties_and_digests_reviewed": True,
        "source_specimen_groups_and_partitions_reviewed": True,
        "homogeneous_isotropic_constant_speed_assumption_reviewed": True,
        "support_and_no_extrapolation_reviewed": True,
        "evidence": [E],
    }
    v.update(updates)
    return AcousticEmissionWaveSpeedCalibration.model_validate_json(json.dumps(v))


def test_fit():
    r = acoustic_emission_wave_speed_calibration(payload())
    assert r.status == "computed"
    assert r.values["wave_speed_m_s"] == pytest.approx(5000)
    assert r.values["clock_offset_s"] == pytest.approx(0.001)
    assert r.values["holdout_weighted_time_rmse_s"] < 1e-12


def test_review():
    assert (
        acoustic_emission_wave_speed_calibration(payload(clock_and_emission_reference_reviewed=False)).status
        == "needs_data"
    )


def test_support():
    assert (
        acoustic_emission_wave_speed_calibration(payload(maximum_supported_wave_speed_m_s=4500)).status
        == "out_of_scope"
    )


def test_partition_context():
    b = payload()
    s = b.known_sources[-1].model_copy(update={"physical_specimen_id": "p1"})
    with pytest.raises(ValueError, match="cannot cross"):
        AcousticEmissionWaveSpeedCalibration(
            **b.model_dump(exclude={"known_sources"}), known_sources=b.known_sources[:-1] + (s,)
        )
    r = ModelRegistry()
    r.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        r.run(
            "inspection.acoustic_emission_wave_speed_calibration",
            b,
            RunContext(asset_id="other", location_id="l", time_basis="clock"),
        )

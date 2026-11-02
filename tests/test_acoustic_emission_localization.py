import json
import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.acoustic_emission_localization import (
    AEArrivalLocalization,
    acoustic_emission_arrival_localization,
    specifications,
)
from matintegrity.registry import ModelRegistry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored"}
D = "a" * 64


def payload(**updates):
    speed = 5000.0
    positions = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 1.0, 1.0)]
    sensors = [
        {
            "sensor_id": f"s{i}",
            "channel_id": f"c{i}",
            "coordinate_frame_id": "frame-1",
            "position_m": p,
            "calibration_id": "cal-1",
            "coupling_state_id": "coupling-1",
            "calibration_state_digest": D,
            "coupling_state_digest": D,
            "evidence": [E],
        }
        for i, p in enumerate(positions)
    ]

    def event(eid, part, source, group, pos, t0):
        picks = [
            {
                "pick_id": f"{eid}-p{i}",
                "sensor_id": f"s{i}",
                "channel_id": f"c{i}",
                "clock_id": "clock-1",
                "arrival_time_s": t0 + math.dist(pos, p) / speed,
                "standard_uncertainty_s": 1e-6,
                "pick_method_id": "method-1",
                "provider_id": "provider-1",
                "provider_revision": "1",
                "source_trace_digest": D,
                "result_digest": D,
                "record_status": "valid",
                "evidence": [E],
            }
            for i, p in enumerate(positions)
        ]
        return {
            "event_id": eid,
            "physical_source_id": source,
            "source_group_id": group,
            "partition": part,
            "clock_id": "clock-1",
            "picks": picks,
            "known_source_position_m": pos,
            "known_source_position_digest": D,
            "evidence": [E],
        }

    v = {
        "assessment_id": "ae-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "coordinate_frame_id": "frame-1",
        "sensors": sensors,
        "events": [
            event("e1", "calibration", "src1", "g1", (0.2, 0.3, 0.4), 0.01),
            event("e2", "holdout", "src2", "g2", (0.3, 0.2, 0.25), 0.02),
        ],
        "wave_speed_m_s": speed,
        "wave_speed_standard_uncertainty_m_s": 10.0,
        "wave_speed_provider_id": "speed-provider",
        "wave_speed_provider_revision": "1",
        "wave_speed_state_digest": D,
        "minimum_supported_wave_speed_m_s": 4000.0,
        "maximum_supported_wave_speed_m_s": 6000.0,
        "support_minimum_position_m": [0.0, 0.0, 0.0],
        "support_maximum_position_m": [1.0, 1.0, 1.0],
        "maximum_iterations": 30,
        "position_tolerance_m": 1e-10,
        "sensor_frame_channel_calibration_and_coupling_reviewed": True,
        "homogeneous_isotropic_constant_speed_assumption_reviewed": True,
        "pick_clock_method_uncertainty_and_digests_reviewed": True,
        "physical_source_partitions_and_independence_reviewed": True,
        "caller_position_support_reviewed": True,
        "evidence": [E],
    }
    v.update(updates)
    return AEArrivalLocalization.model_validate_json(json.dumps(v))


def test_localization():
    r = acoustic_emission_arrival_localization(payload())
    assert r.status == "computed"
    assert r.values["holdout_position_errors_m"][0] < 1e-6


def test_speed_scope():
    assert acoustic_emission_arrival_localization(payload(wave_speed_m_s=7000.0)).status == "out_of_scope"


def test_missing():
    b = payload()
    p = (
        b.events[0]
        .picks[0]
        .model_copy(
            update={
                "arrival_time_s": None,
                "standard_uncertainty_s": None,
                "result_digest": None,
                "record_status": "missing",
                "missing_or_invalid_basis": "no pick",
            }
        )
    )
    e = b.events[0].model_copy(update={"picks": (p,) + b.events[0].picks[1:]})
    assert (
        acoustic_emission_arrival_localization(b.model_copy(update={"events": (e, b.events[1])})).status
        == "needs_data"
    )


def test_partition_context():
    b = payload()
    e = b.events[1].model_copy(update={"physical_source_id": "src1"})
    with pytest.raises(ValueError, match="cannot cross"):
        AEArrivalLocalization(**b.model_dump(exclude={"events"}), events=(b.events[0], e))
    r = ModelRegistry()
    r.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        r.run(
            "inspection.acoustic_emission_arrival_localization",
            b,
            RunContext(asset_id="other", location_id="location-1", time_basis="clock-1"),
        )

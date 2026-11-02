"""Run an authored TOFD acquisition summary without waveform processing or acceptance rules."""

import math

from matintegrity import evaluate
from matintegrity.contracts import RunContext

separation = 0.04
velocity = 5900.0
lateral = 10e-6


def delay(depth):
    return (2 * math.hypot(separation / 2, depth) - separation) / velocity


evidence = {"source_id": "user-tofd", "origin": "user_declared", "citation": "user procedure"}
inputs = {
    "examination_id": "exam-1",
    "procedure_id": "procedure-1",
    "procedure_revision": "1",
    "physical_scope_id": "weld-volume-1",
    "material_condition_id": "material-condition-1",
    "specimen_longitudinal_velocity_m_s": velocity,
    "specimen_velocity_basis": "user-reviewed reference block",
    "wall_thickness_m": 0.025,
    "wall_thickness_basis": "user-reviewed local thickness",
    "probe_pair": {
        "pair_id": "pair-1",
        "transmit_probe_id": "tx",
        "receive_probe_id": "rx",
        "transmit_wedge_id": "tx-wedge",
        "receive_wedge_id": "rx-wedge",
        "probe_index_separation_m": separation,
        "center_frequency_Hz": 10e6,
        "nominal_refracted_angle_rad": 1.0,
        "index_separation_basis": "user measurement",
        "evidence": [evidence],
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
            "time_zero_basis": "user-reviewed acquisition clock",
            "lateral_wave_arrival_time_s": lateral,
            "backwall_echo_arrival_time_s": lateral + delay(0.025),
        }
    ],
    "diffraction_picks": [
        {
            "pick_id": identity,
            "frame_id": "frame-1",
            "reported_role": role,
            "arrival_time_s": lateral + delay(depth),
            "picking_basis": "user-reviewed manual pick",
            "evidence": [evidence],
        }
        for identity, role, depth in (
            ("upper", "upper_tip", 0.005),
            ("lower", "lower_tip", 0.015),
        )
    ],
    "indications": [
        {
            "indication_id": "indication-1",
            "upper_tip_pick_id": "upper",
            "lower_tip_pick_id": "lower",
            "reported_indication_type": "user-reported diffraction pair",
            "acquisition_location_description": "frame 1",
            "physical_location_id": "weld-location-1",
            "object_mapping_basis": "user-reviewed encoder map",
            "evidence": [evidence],
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
    "evidence": [evidence],
}

result = evaluate(
    "inspection.tofd_acquisition_summary",
    inputs,
    RunContext(asset_id="asset-1", location_id="weld-location-1", time_basis="acquisition clock"),
)
print(result.status, result.values["indication_geometry_by_id"])

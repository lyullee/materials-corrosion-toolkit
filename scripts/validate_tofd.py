"""Verify independently authored TOFD symmetric-path identities."""

import json
import math
from pathlib import Path

from matintegrity.contracts import Evidence
from matintegrity.models.tofd import TofdExamination, tofd_acquisition_summary

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "validation/tofd_math.json"


def delay(depth_m: float, separation_m: float, velocity_m_s: float) -> float:
    return (2 * math.hypot(separation_m / 2, depth_m) - separation_m) / velocity_m_s


def main():
    separation = 0.04
    velocity = 5900.0
    wall = 0.025
    lateral = 10e-6
    evidence = Evidence(source_id="authored-tofd", origin="synthetic", citation="authored identity")
    examination = TofdExamination.model_validate(
        {
            "examination_id": "authored-tofd-exam",
            "procedure_id": "authored-tofd-procedure",
            "procedure_revision": "1",
            "physical_scope_id": "synthetic-weld-volume",
            "material_condition_id": "synthetic-homogeneous-material",
            "specimen_longitudinal_velocity_m_s": velocity,
            "specimen_velocity_basis": "authored exact value",
            "wall_thickness_m": wall,
            "wall_thickness_basis": "authored exact value",
            "probe_pair": {
                "pair_id": "pair",
                "transmit_probe_id": "tx",
                "receive_probe_id": "rx",
                "transmit_wedge_id": "tx-wedge",
                "receive_wedge_id": "rx-wedge",
                "probe_index_separation_m": separation,
                "center_frequency_Hz": 10e6,
                "nominal_refracted_angle_rad": 1.0,
                "index_separation_basis": "authored exact value",
                "evidence": [evidence],
            },
            "encoder_id": "encoder",
            "encoder_direction": "increasing",
            "frames": [
                {
                    "frame_id": "frame",
                    "encoder_position_m": 0.0,
                    "data_sha256": "1" * 64,
                    "sample_count": 1000,
                    "sample_interval_s": 1e-8,
                    "amplitude_encoding": "synthetic",
                    "time_zero_basis": "authored clock",
                    "lateral_wave_arrival_time_s": lateral,
                    "backwall_echo_arrival_time_s": lateral + delay(wall, separation, velocity),
                }
            ],
            "diffraction_picks": [
                {
                    "pick_id": identity,
                    "frame_id": "frame",
                    "reported_role": role,
                    "arrival_time_s": lateral + delay(depth, separation, velocity),
                    "picking_basis": "authored exact arrival",
                    "evidence": [evidence],
                }
                for identity, role, depth in (
                    ("upper", "upper_tip", 0.005),
                    ("lower", "lower_tip", 0.015),
                )
            ],
            "indications": [
                {
                    "indication_id": "indication",
                    "upper_tip_pick_id": "upper",
                    "lower_tip_pick_id": "lower",
                    "reported_indication_type": "authored paired tips",
                    "acquisition_location_description": "synthetic frame",
                    "physical_location_id": "synthetic-location",
                    "object_mapping_basis": "authored direct map",
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
    )
    result = tofd_acquisition_summary(examination)
    geometry = result.values["indication_geometry_by_id"]["indication"]
    observed = {
        "upper_tip_depth_m": result.values["tip_depth_by_pick_id"]["upper"],
        "lower_tip_depth_m": result.values["tip_depth_by_pick_id"]["lower"],
        "tip_separation_height_m": geometry["tip_separation_height_m"],
        "equivalent_backwall_depth_m": result.values["backwall_timing_diagnostics_by_frame_id"]["frame"][
            "equivalent_backwall_depth_m"
        ],
    }
    expected = {
        "upper_tip_depth_m": 0.005,
        "lower_tip_depth_m": 0.015,
        "tip_separation_height_m": 0.01,
        "equivalent_backwall_depth_m": wall,
    }
    errors = {key: abs(observed[key] - expected[key]) for key in expected}
    if result.status != "computed" or max(errors.values()) > 1e-14:
        raise AssertionError("TOFD authored geometry verification failed")
    report = {
        "schema_version": "matintegrity.validation.tofd_math.v1",
        "model_id": "inspection.tofd_acquisition_summary",
        "case": "authored symmetric straight-path identity",
        "expected": expected,
        "observed": observed,
        "absolute_error": errors,
        "qualification": "Mathematical identity and contract verification only; no waveform, dead-zone, sizing, POD or acceptance qualification.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

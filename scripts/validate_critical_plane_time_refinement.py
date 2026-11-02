"""Verify fixed-plane time-refinement reporting against a sampled sine cycle."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.models import fatigue
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def _sampling(sampling_id: str, intervals: int, phase: float):
    times = [index / intervals for index in range(intervals + 1)]
    amplitudes = [math.sin(2 * math.pi * time + phase) for time in times]
    return {
        "sampling_id": sampling_id,
        "sample_ids": [f"{sampling_id}-s{index}" for index in range(len(times))],
        "sample_times_s": times,
        "stress_tensor_components_Pa": [[value * 100e6, 0.0, 0.0, 0.0, 0.0, 0.0] for value in amplitudes],
        "strain_tensor_components": [[value * 5e-4, 0.0, 0.0, 0.0, 0.0, 0.0] for value in amplitudes],
    }


def main():
    root = math.sqrt(0.5)
    phase = 0.31
    levels = [_sampling(f"n{intervals}", intervals, phase) for intervals in (4, 8, 16, 32)]
    inputs = {
        "history_id": "analytic-phase-shifted-sine",
        "material_condition_id": "synthetic",
        "location_id": "analytic-point",
        "tensor_source_id": "closed-form-sine",
        "candidate_planes": [
            {
                "plane_id": "normal-x",
                "normal": [1.0, 0.0, 0.0],
                "in_plane_direction": [0.0, 1.0, 0.0],
            },
            {
                "plane_id": "xy-45",
                "normal": [root, root, 0.0],
                "in_plane_direction": [-root, root, 0.0],
            },
        ],
        "sampling_levels": levels,
        "representative_cycle_declared": True,
        "maximum_stress_closure_error_Pa": 1e-7,
        "maximum_strain_closure_error": 1e-15,
        "maximum_nested_time_match_error_s": 0.0,
        "fatemi_socie_coefficient": 0.3,
        "normalization_stress_Pa": 400e6,
        "declared_maximum_relative_factor_change": 0.02,
        "declared_maximum_plane_rotation_rad": 0.0,
    }
    result = default_registry().run(
        "fatigue.critical_plane_time_refinement",
        inputs,
        RunContext(
            asset_id="synthetic-time-refinement",
            location_id="analytic-point",
            time_basis="one second closed synthetic cycle",
        ),
    )
    expected_rows = []
    maximum_sampled_fs_error = 0.0
    maximum_sampled_swt_error_Pa = 0.0
    for sampling, row in zip(levels, result.values["levels"], strict=True):
        stresses = [tensor[0] for tensor in sampling["stress_tensor_components_Pa"]]
        strains = [tensor[0] for tensor in sampling["strain_tensor_components"]]
        strain_amplitude = (max(strains) - min(strains)) / 2
        expected_fs = strain_amplitude * (1 + 0.3 * (max(stresses) / 2) / 400e6)
        expected_swt = max(stresses) * strain_amplitude
        maximum_sampled_fs_error = max(
            maximum_sampled_fs_error, abs(row["maximum_fatemi_socie_factor"] - expected_fs)
        )
        maximum_sampled_swt_error_Pa = max(
            maximum_sampled_swt_error_Pa, abs(row["maximum_swt_factor_Pa"] - expected_swt)
        )
        expected_rows.append(
            {
                "sampling_id": sampling["sampling_id"],
                "sample_count": len(sampling["sample_ids"]),
                "expected_fatemi_socie_factor": expected_fs,
                "expected_swt_factor_Pa": expected_swt,
            }
        )
    continuous_fs = 5e-4 * (1 + 0.3 * 50e6 / 400e6)
    continuous_swt_Pa = 100e6 * 5e-4
    fs_errors_to_continuous = [
        abs(row["maximum_fatemi_socie_factor"] - continuous_fs) for row in result.values["levels"]
    ]
    swt_errors_to_continuous = [
        abs(row["maximum_swt_factor_Pa"] - continuous_swt_Pa) for row in result.values["levels"]
    ]
    if maximum_sampled_fs_error > 1e-15 or maximum_sampled_swt_error_Pa > 1e-8:
        raise AssertionError("time-refinement levels do not match independent sampled-path expressions")
    if any(
        fine > coarse + 1e-15
        for coarse, fine in zip(fs_errors_to_continuous, fs_errors_to_continuous[1:], strict=False)
    ):
        raise AssertionError(
            "nested FS sampled maxima do not approach the continuous sine limit monotonically"
        )
    if any(
        fine > coarse + 1e-8
        for coarse, fine in zip(swt_errors_to_continuous, swt_errors_to_continuous[1:], strict=False)
    ):
        raise AssertionError(
            "nested SWT sampled maxima do not approach the continuous sine limit monotonically"
        )
    if not result.values["final_transition_within_declared_tolerances"]:
        raise AssertionError("final nested transition exceeds the declared diagnostic tolerance")
    record = {
        "schema_version": "matintegrity.critical_plane_time_refinement_math.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_id": "fatigue.critical_plane_time_refinement",
        "model_source_sha256": hashlib.sha256(Path(fatigue.__file__).read_bytes()).hexdigest(),
        "benchmark_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sampled_expectations": expected_rows,
        "maximum_absolute_sampled_fatemi_socie_error": maximum_sampled_fs_error,
        "maximum_absolute_sampled_swt_error_Pa": maximum_sampled_swt_error_Pa,
        "continuous_sine_fatemi_socie_limit": continuous_fs,
        "absolute_fatemi_socie_errors_to_continuous_limit": fs_errors_to_continuous,
        "continuous_sine_swt_limit_Pa": continuous_swt_Pa,
        "absolute_swt_errors_to_continuous_limit_Pa": swt_errors_to_continuous,
        "final_transition_within_declared_tolerances": result.values[
            "final_transition_within_declared_tolerances"
        ],
        "qualification": "Authored nested samples of one analytic phase-shifted sine cycle on two fixed planes. This verifies discrete reporting and observed approach to this known limit only; it does not provide a general between-sample error bound, continuous-plane convergence, fatigue-life calibration or experimental validity.",
    }
    target = ROOT / "validation/critical_plane_time_refinement_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

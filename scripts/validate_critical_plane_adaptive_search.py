"""Verify adaptive orientation reporting against an inclined uniaxial closed form."""

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


def main():
    axis = [1 / math.sqrt(14), 2 / math.sqrt(14), 3 / math.sqrt(14)]
    dyad = [
        axis[0] ** 2,
        axis[1] ** 2,
        axis[2] ** 2,
        axis[0] * axis[1],
        axis[1] * axis[2],
        axis[2] * axis[0],
    ]
    amplitudes = [0.0, 1.0, 0.0, -1.0, 0.0]
    payload = {
        "history_id": "inclined-uniaxial-cycle",
        "material_condition_id": "synthetic",
        "location_id": "analytic-point",
        "tensor_source_id": "closed-form-uniaxial",
        "sample_ids": [f"s{index}" for index in range(len(amplitudes))],
        "stress_tensor_components_Pa": [
            [value * 100e6 * component for component in dyad] for value in amplitudes
        ],
        "strain_tensor_components": [
            [value * 5e-4 * component for component in dyad] for value in amplitudes
        ],
        "seed_grid": {"grid_id": "seed", "candidate_count": 16, "azimuth_phase_rad": 0.17},
        "representative_cycle_declared": True,
        "maximum_stress_closure_error_Pa": 0.0,
        "maximum_strain_closure_error": 0.0,
        "fatemi_socie_coefficient": 0.3,
        "normalization_stress_Pa": 400e6,
        "refinement_rounds": 6,
        "ring_points": 24,
        "initial_radius_rad": math.pi / 8,
        "radius_reduction_factor": 0.5,
        "declared_maximum_final_relative_factor_change": 1e-4,
        "declared_maximum_final_plane_rotation_rad": 0.02,
    }
    result = default_registry().run(
        "fatigue.critical_plane_adaptive_search",
        payload,
        RunContext(
            asset_id="synthetic-adaptive-search",
            location_id="analytic-point",
            time_basis="one closed synthetic cycle",
        ),
    )
    fs = result.values["fatemi_socie_search"]
    swt = result.values["swt_search"]
    alpha = 0.3 * 100e6 / 400e6
    optimal_squared_cosine = (-(2 - 3 * alpha) + math.sqrt((2 - 3 * alpha) ** 2 + 16 * alpha)) / (8 * alpha)
    expected_fs = (
        2
        * 5e-4
        * math.sqrt(optimal_squared_cosine * (1 - optimal_squared_cosine))
        * (1 + alpha * optimal_squared_cosine)
    )
    expected_swt = 100e6 * 5e-4
    fs_relative_error = abs(fs["final_factor"] - expected_fs) / expected_fs
    swt_relative_error = abs(swt["final_factor"] - expected_swt) / expected_swt
    swt_alignment = abs(sum(a * b for a, b in zip(axis, swt["final_plane_normal"], strict=True)))
    swt_plane_error = math.acos(min(1.0, swt_alignment))
    if fs["final_factor"] < fs["seed_factor"] or swt["final_factor"] < swt["seed_factor"]:
        raise AssertionError("center-retaining adaptive search decreased an objective")
    if fs_relative_error > 1e-5 or swt_relative_error > 1e-4 or swt_plane_error > 0.01:
        raise AssertionError("adaptive benchmark no longer approaches the inclined uniaxial solution")
    record = {
        "schema_version": "matintegrity.critical_plane_adaptive_search_math.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_id": "fatigue.critical_plane_adaptive_search",
        "model_source_sha256": hashlib.sha256(Path(fatigue.__file__).read_bytes()).hexdigest(),
        "benchmark_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seed_grid_family": result.values["seed_grid_family"],
        "seed_candidate_count": result.values["seed_candidate_count"],
        "refinement_rounds": result.values["refinement_rounds"],
        "ring_points": result.values["ring_points"],
        "expected_continuous_fatemi_socie_factor": expected_fs,
        "final_fatemi_socie_factor": fs["final_factor"],
        "fatemi_socie_relative_error": fs_relative_error,
        "expected_continuous_swt_factor_Pa": expected_swt,
        "final_swt_factor_Pa": swt["final_factor"],
        "swt_relative_error": swt_relative_error,
        "swt_plane_error_rad": swt_plane_error,
        "final_transition_diagnostic_satisfied": result.values[
            "both_final_transitions_within_declared_tolerances"
        ],
        "qualification": "Authored inclined uniaxial closed form verifies deterministic local refinement and trace reporting. It does not prove a global optimum for general histories, convergence, fatigue-life calibration or experimental validity.",
    }
    target = ROOT / "validation/critical_plane_adaptive_search_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

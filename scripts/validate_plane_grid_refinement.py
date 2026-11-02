"""Verify finite-grid refinement reporting against a closed-form uniaxial path."""

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
    amplitudes = [0.0, 1.0, 0.0, -1.0, 0.0]
    stress_amplitude = 100e6
    strain_amplitude = 5e-4
    fs_coefficient = 0.3
    normalization_stress = 400e6
    inputs = {
        "history_id": "analytic-uniaxial-cycle",
        "material_condition_id": "synthetic",
        "location_id": "analytic-point",
        "tensor_source_id": "closed-form-uniaxial",
        "sample_ids": [f"s{index}" for index in range(len(amplitudes))],
        "stress_tensor_components_Pa": [
            [value * stress_amplitude, 0.0, 0.0, 0.0, 0.0, 0.0] for value in amplitudes
        ],
        "strain_tensor_components": [
            [value * strain_amplitude, 0.0, 0.0, 0.0, 0.0, 0.0] for value in amplitudes
        ],
        "representative_cycle_declared": True,
        "maximum_stress_closure_error_Pa": 0.0,
        "maximum_strain_closure_error": 0.0,
        "fatemi_socie_coefficient": fs_coefficient,
        "normalization_stress_Pa": normalization_stress,
        "refinement_levels": [
            {"grid_id": "level-1", "polar_divisions": 2, "azimuthal_divisions": 8},
            {"grid_id": "level-2", "polar_divisions": 4, "azimuthal_divisions": 16},
            {"grid_id": "level-3", "polar_divisions": 8, "azimuthal_divisions": 32},
        ],
        "declared_maximum_relative_factor_change": 1e-12,
        "declared_maximum_plane_rotation_rad": math.pi / 2,
    }
    result = default_registry().run(
        "fatigue.critical_plane_grid_refinement",
        inputs,
        RunContext(
            asset_id="synthetic-grid-refinement",
            location_id="analytic-point",
            time_basis="one closed synthetic cycle",
        ),
    )
    expected_fs = strain_amplitude * (1 + fs_coefficient * (stress_amplitude / 2) / normalization_stress)
    expected_swt = stress_amplitude * strain_amplitude
    maximum_fs_error = max(
        abs(row["maximum_fatemi_socie_factor"] - expected_fs) for row in result.values["levels"]
    )
    maximum_swt_error_Pa = max(
        abs(row["maximum_swt_factor_Pa"] - expected_swt) for row in result.values["levels"]
    )
    candidate_counts = [row["candidate_count"] for row in result.values["levels"]]
    if candidate_counts != [13, 57, 241]:
        raise AssertionError("refinement candidate counts changed")
    if maximum_fs_error > 1e-15 or maximum_swt_error_Pa > 1e-8:
        raise AssertionError("finite-grid maxima do not recover the represented analytic orientations")
    if not result.values["all_transitions_within_declared_tolerances"]:
        raise AssertionError("nested represented optima should satisfy the declared diagnostic tolerances")
    record = {
        "schema_version": "matintegrity.critical_plane_grid_refinement_math.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_id": "fatigue.critical_plane_grid_refinement",
        "model_source_sha256": hashlib.sha256(Path(fatigue.__file__).read_bytes()).hexdigest(),
        "benchmark_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "grid_candidate_counts": candidate_counts,
        "expected_fatemi_socie_factor": expected_fs,
        "maximum_absolute_fatemi_socie_error": maximum_fs_error,
        "expected_swt_factor_Pa": expected_swt,
        "maximum_absolute_swt_error_Pa": maximum_swt_error_Pa,
        "all_transitions_within_declared_tolerances": result.values[
            "all_transitions_within_declared_tolerances"
        ],
        "qualification": "Closed-form uniaxial orientations represented on three nested finite grids. This checks reporting and exact represented maxima only; it does not prove unsampled orientation error, continuous-plane or time convergence, fatigue-life calibration or experimental validity.",
    }
    target = ROOT / "validation/critical_plane_grid_refinement_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

"""Verify cross-grid critical-factor reporting against a uniaxial closed form."""

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


def _relative_change(first: float, second: float) -> float:
    return abs(first - second) / max(abs(first), abs(second))


def main():
    amplitudes = [0.0, 1.0, 0.0, -1.0, 0.0]
    inputs = {
        "history_id": "analytic-uniaxial-cycle",
        "material_condition_id": "synthetic",
        "location_id": "analytic-point",
        "tensor_source_id": "closed-form-uniaxial",
        "sample_ids": [f"s{index}" for index in range(len(amplitudes))],
        "stress_tensor_components_Pa": [[value * 100e6, 0.0, 0.0, 0.0, 0.0, 0.0] for value in amplitudes],
        "strain_tensor_components": [[value * 5e-4, 0.0, 0.0, 0.0, 0.0, 0.0] for value in amplitudes],
        "grid_definitions": [
            {"grid_id": "latitude-reference", "polar_divisions": 8, "azimuthal_divisions": 32},
            {"grid_id": "fibonacci-phase-0", "candidate_count": 128, "azimuth_phase_rad": 0.0},
            {"grid_id": "fibonacci-phase-037", "candidate_count": 128, "azimuth_phase_rad": 0.37},
        ],
        "reference_grid_id": "latitude-reference",
        "representative_cycle_declared": True,
        "maximum_stress_closure_error_Pa": 0.0,
        "maximum_strain_closure_error": 0.0,
        "fatemi_socie_coefficient": 0.3,
        "normalization_stress_Pa": 400e6,
        "declared_maximum_relative_factor_change": 0.001,
        "declared_maximum_plane_rotation_rad": math.radians(1),
    }
    result = default_registry().run(
        "fatigue.critical_plane_grid_family_comparison",
        inputs,
        RunContext(
            asset_id="synthetic-grid-family-comparison",
            location_id="analytic-point",
            time_basis="one closed synthetic cycle",
        ),
    )
    rows = result.values["grids"]
    reference = rows[0]
    expected_fs = 5e-4 * (1 + 0.3 * 50e6 / 400e6)
    expected_swt_Pa = 100e6 * 5e-4
    reference_fs_error = abs(reference["maximum_fatemi_socie_factor"] - expected_fs)
    reference_swt_error_Pa = abs(reference["maximum_swt_factor_Pa"] - expected_swt_Pa)
    maximum_comparison_error = 0.0
    for row in rows[1:]:
        comparison = row["comparison_to_reference"]
        maximum_comparison_error = max(
            maximum_comparison_error,
            abs(
                comparison["fatemi_socie_relative_change"]
                - _relative_change(
                    reference["maximum_fatemi_socie_factor"], row["maximum_fatemi_socie_factor"]
                )
            ),
            abs(
                comparison["swt_relative_change"]
                - _relative_change(reference["maximum_swt_factor_Pa"], row["maximum_swt_factor_Pa"])
            ),
        )
    if [row["candidate_count"] for row in rows] != [241, 128, 128]:
        raise AssertionError("declared cross-grid candidate counts changed")
    if reference_fs_error > 1e-15 or reference_swt_error_Pa > 1e-8:
        raise AssertionError("latitude reference no longer contains the analytic uniaxial optima")
    if maximum_comparison_error > 1e-15:
        raise AssertionError("reported cross-grid relative changes do not match independent expressions")
    if result.values["all_comparisons_within_declared_tolerances"] is not False:
        raise AssertionError("strict benchmark tolerances should expose finite-grid sensitivity")
    record = {
        "schema_version": "matintegrity.critical_plane_grid_family_comparison_math.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_id": "fatigue.critical_plane_grid_family_comparison",
        "model_source_sha256": hashlib.sha256(Path(fatigue.__file__).read_bytes()).hexdigest(),
        "benchmark_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "grid_ids": [row["grid_id"] for row in rows],
        "grid_families": [row["grid_family"] for row in rows],
        "candidate_counts": [row["candidate_count"] for row in rows],
        "expected_reference_fatemi_socie_factor": expected_fs,
        "reference_fatemi_socie_absolute_error": reference_fs_error,
        "expected_reference_swt_factor_Pa": expected_swt_Pa,
        "reference_swt_absolute_error_Pa": reference_swt_error_Pa,
        "maximum_cross_grid_relative_change_reporting_error": maximum_comparison_error,
        "comparisons_to_reference": [row["comparison_to_reference"] for row in rows[1:]],
        "expected_all_comparisons_within_declared_tolerances": False,
        "all_comparisons_within_declared_tolerances": result.values[
            "all_comparisons_within_declared_tolerances"
        ],
        "qualification": "Authored uniaxial closed form with one finite latitude reference and two finite Fibonacci phases. This verifies composition and comparison reporting only; agreement with the finite reference is not an orientation-error bound, continuous optimum, fatigue-life calibration or experimental validity.",
    }
    target = ROOT / "validation/critical_plane_grid_family_comparison_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

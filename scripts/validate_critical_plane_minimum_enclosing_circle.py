"""Verify finite shear-path enclosing circles against authored planar geometry."""

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
    strain_radius = 0.002
    stress_radius = 40e6
    points = [
        (1.0, 0.0),
        (-0.5, math.sqrt(3) / 2),
        (-0.5, -math.sqrt(3) / 2),
        (1.0, 0.0),
    ]
    payload = {
        "history_id": "equilateral-shear-cycle",
        "material_condition_id": "synthetic",
        "location_id": "analytic-point",
        "tensor_source_id": "authored-planar-geometry",
        "sample_ids": ["v0", "v1", "v2", "v0-close"],
        "stress_tensor_components_Pa": [
            [0.0, 0.0, 0.0, stress_radius * x, 0.0, stress_radius * y] for x, y in points
        ],
        "strain_tensor_components": [
            [0.0, 0.0, 0.0, strain_radius * x / 2, 0.0, strain_radius * y / 2] for x, y in points
        ],
        "candidate_planes": [
            {
                "plane_id": "normal-x",
                "normal": [1.0, 0.0, 0.0],
                "in_plane_direction": [0.0, 1.0, 0.0],
            }
        ],
        "representative_cycle_declared": True,
        "maximum_stress_closure_error_Pa": 0.0,
        "maximum_strain_closure_error": 0.0,
        "fatemi_socie_coefficient": 0.3,
        "normalization_stress_Pa": 400e6,
    }
    result = default_registry().run(
        "fatigue.critical_plane_minimum_enclosing_circle_factors",
        payload,
        RunContext(
            asset_id="synthetic-enclosing-circle",
            location_id="analytic-point",
            time_basis="one closed synthetic cycle",
        ),
    )
    row = result.values["candidate_factors"][0]
    expected_chord_strain = strain_radius * math.sqrt(3) / 2
    expected_chord_stress = stress_radius * math.sqrt(3) / 2
    comparisons = {
        "strain_circle_radius": (
            row["shear_strain_minimum_enclosing_circle_amplitude"],
            strain_radius,
        ),
        "strain_half_maximum_chord": (
            row["shear_strain_vector_chord_amplitude"],
            expected_chord_strain,
        ),
        "stress_circle_radius_Pa": (
            row["shear_stress_minimum_enclosing_circle_amplitude_Pa"],
            stress_radius,
        ),
        "stress_half_maximum_chord_Pa": (
            row["shear_stress_vector_chord_amplitude_Pa"],
            expected_chord_stress,
        ),
        "circle_to_chord_ratio": (
            row["shear_strain_circle_to_chord_amplitude_ratio"],
            2 / math.sqrt(3),
        ),
    }
    records = []
    for case_id, (actual, expected) in comparisons.items():
        absolute_error = abs(actual - expected)
        tolerance = 1e-12 * max(abs(expected), 1.0)
        if absolute_error > tolerance:
            raise AssertionError(f"{case_id}: {actual} != {expected}")
        records.append(
            {
                "case_id": case_id,
                "actual": actual,
                "expected": expected,
                "absolute_error": absolute_error,
            }
        )
    if set(row["shear_strain_circle_support_sample_ids"]) != {"v0", "v1", "v2"}:
        raise AssertionError("equilateral circle must retain its three unique support vertices")
    record = {
        "schema_version": "matintegrity.critical_plane_minimum_enclosing_circle_math.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_id": "fatigue.critical_plane_minimum_enclosing_circle_factors",
        "model_source_sha256": hashlib.sha256(Path(fatigue.__file__).read_bytes()).hexdigest(),
        "benchmark_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "support_sample_ids": row["shear_strain_circle_support_sample_ids"],
        "comparisons": records,
        "qualification": "Authored equilateral finite shear path verifies the enclosing-circle radius, support identities and explicit chord comparison. It does not verify continuous-time extrema, cycle counting, orientation convergence, fatigue-life calibration or experiment agreement.",
    }
    target = ROOT / "validation/critical_plane_minimum_enclosing_circle_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

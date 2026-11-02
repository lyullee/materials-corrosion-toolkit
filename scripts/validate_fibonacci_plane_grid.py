"""Verify area-stratified golden-angle plane-grid geometry and quadrature metadata."""

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
    count = 100
    inputs = {"grid_id": "analytic-fibonacci", "candidate_count": count, "azimuth_phase_rad": 0.37}
    result = default_registry().run(
        "fatigue.area_uniform_fibonacci_plane_grid",
        inputs,
        RunContext(
            asset_id="synthetic-fibonacci-grid",
            location_id="orientation-space",
            time_basis="deterministic geometry generation",
        ),
    )
    candidates = result.values["candidate_planes"]
    positions = result.values["sampling_positions"]
    expected_golden_angle = math.pi * (3 - math.sqrt(5))
    weight = result.values["nominal_solid_angle_weight_sr"]
    maximum_normal_error = 0.0
    maximum_direction_error = 0.0
    maximum_orthogonality_error = 0.0
    maximum_z_midpoint_error = 0.0
    maximum_duplicate_alignment = 0.0
    for index, (candidate, position) in enumerate(zip(candidates, positions, strict=True)):
        normal = candidate["normal"]
        direction = candidate["in_plane_direction"]
        maximum_normal_error = max(
            maximum_normal_error, abs(math.sqrt(sum(value * value for value in normal)) - 1)
        )
        maximum_direction_error = max(
            maximum_direction_error, abs(math.sqrt(sum(value * value for value in direction)) - 1)
        )
        maximum_orthogonality_error = max(
            maximum_orthogonality_error,
            abs(sum(a * b for a, b in zip(normal, direction, strict=True))),
        )
        maximum_z_midpoint_error = max(
            maximum_z_midpoint_error,
            abs(position["equal_area_coordinate_z"] - (index + 0.5) / count),
        )
    for first in range(len(candidates) - 1):
        for second in range(first + 1, len(candidates)):
            alignment = abs(
                sum(
                    a * b
                    for a, b in zip(candidates[first]["normal"], candidates[second]["normal"], strict=True)
                )
            )
            maximum_duplicate_alignment = max(maximum_duplicate_alignment, alignment)
    weighted_mean_z = sum(row["equal_area_coordinate_z"] * weight for row in positions) / (2 * math.pi)
    weighted_mean_z_squared = sum(row["equal_area_coordinate_z"] ** 2 * weight for row in positions) / (
        2 * math.pi
    )
    expected_midpoint_z_squared = 1 / 3 - 1 / (12 * count * count)
    if result.values["candidate_count"] != count:
        raise AssertionError("candidate count changed")
    if abs(result.values["golden_angle_rad"] - expected_golden_angle) > 1e-15:
        raise AssertionError("golden-angle increment changed")
    if abs(result.values["nominal_weight_sum_sr"] - 2 * math.pi) > 1e-14:
        raise AssertionError("nominal hemisphere weights do not sum to 2 pi")
    if max(maximum_normal_error, maximum_direction_error, maximum_orthogonality_error) > 1e-14:
        raise AssertionError("generated plane frames are not orthonormal within tolerance")
    if maximum_z_midpoint_error > 1e-15:
        raise AssertionError("equal-area z midpoint sequence changed")
    if maximum_duplicate_alignment >= 1 - 1e-12:
        raise AssertionError("an exact plane-sign duplicate remains in the grid")
    if abs(weighted_mean_z - 0.5) > 1e-15:
        raise AssertionError("midpoint quadrature no longer integrates z exactly")
    if abs(weighted_mean_z_squared - expected_midpoint_z_squared) > 1e-15:
        raise AssertionError("midpoint quadrature no longer matches the finite-sum z-squared value")
    record = {
        "schema_version": "matintegrity.area_uniform_fibonacci_plane_grid_math.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_id": "fatigue.area_uniform_fibonacci_plane_grid",
        "model_source_sha256": hashlib.sha256(Path(fatigue.__file__).read_bytes()).hexdigest(),
        "benchmark_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "inputs": inputs,
        "candidate_count": len(candidates),
        "maximum_normal_norm_error": maximum_normal_error,
        "maximum_direction_norm_error": maximum_direction_error,
        "maximum_orthogonality_error": maximum_orthogonality_error,
        "maximum_equal_area_z_midpoint_error": maximum_z_midpoint_error,
        "maximum_absolute_alignment_between_distinct_planes": maximum_duplicate_alignment,
        "nominal_weight_sum_error_sr": abs(result.values["nominal_weight_sum_sr"] - 2 * math.pi),
        "weighted_mean_z_error": abs(weighted_mean_z - 0.5),
        "weighted_mean_z_squared_midpoint_error": abs(weighted_mean_z_squared - expected_midpoint_z_squared),
        "qualification": "Authored area-stratified sequence and nominal quadrature checks only. No exact Voronoi-cell equality, covering-radius bound, nested refinement, continuous critical-plane optimum or experimental validity is qualified.",
    }
    target = ROOT / "validation/area_uniform_fibonacci_plane_grid_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

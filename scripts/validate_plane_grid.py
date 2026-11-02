"""Verify deterministic unoriented-plane grid geometry."""

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
    inputs = {"grid_id": "analytic-grid", "polar_divisions": 6, "azimuthal_divisions": 16}
    context = RunContext(
        asset_id="synthetic-plane-grid",
        location_id="orientation-space",
        time_basis="deterministic geometry generation",
    )
    result = default_registry().run("fatigue.hemisphere_plane_grid", inputs, context)
    candidates = result.values["candidate_planes"]
    expected_count = (
        1
        + (inputs["polar_divisions"] - 1) * inputs["azimuthal_divisions"]
        + inputs["azimuthal_divisions"] // 2
    )
    maximum_normal_error = 0.0
    maximum_direction_error = 0.0
    maximum_orthogonality_error = 0.0
    maximum_duplicate_alignment = 0.0
    for row in candidates:
        normal = row["normal"]
        direction = row["in_plane_direction"]
        maximum_normal_error = max(maximum_normal_error, abs(math.sqrt(sum(v * v for v in normal)) - 1))
        maximum_direction_error = max(
            maximum_direction_error, abs(math.sqrt(sum(v * v for v in direction)) - 1)
        )
        maximum_orthogonality_error = max(
            maximum_orthogonality_error,
            abs(sum(a * b for a, b in zip(normal, direction, strict=True))),
        )
    for first in range(len(candidates) - 1):
        for second in range(first + 1, len(candidates)):
            dot = abs(
                sum(
                    a * b
                    for a, b in zip(candidates[first]["normal"], candidates[second]["normal"], strict=True)
                )
            )
            maximum_duplicate_alignment = max(maximum_duplicate_alignment, dot)
    if result.values["candidate_count"] != expected_count:
        raise AssertionError("plane-grid count does not match the closed-form count")
    if max(maximum_normal_error, maximum_direction_error, maximum_orthogonality_error) > 1e-14:
        raise AssertionError("generated plane frames are not orthonormal within tolerance")
    if maximum_duplicate_alignment >= 1 - 1e-12:
        raise AssertionError("an exact plane-sign duplicate remains in the grid")
    record = {
        "schema_version": "matintegrity.hemisphere_plane_grid_math.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_id": "fatigue.hemisphere_plane_grid",
        "model_source_sha256": hashlib.sha256(Path(fatigue.__file__).read_bytes()).hexdigest(),
        "benchmark_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "inputs": inputs,
        "expected_candidate_count": expected_count,
        "actual_candidate_count": result.values["candidate_count"],
        "maximum_normal_norm_error": maximum_normal_error,
        "maximum_direction_norm_error": maximum_direction_error,
        "maximum_orthogonality_error": maximum_orthogonality_error,
        "maximum_absolute_alignment_between_distinct_planes": maximum_duplicate_alignment,
        "qualification": "Authored finite-grid geometry check only. Angular coverage, equal-area sampling, refinement convergence and a continuous critical-plane optimum are not qualified.",
    }
    target = ROOT / "validation/hemisphere_plane_grid_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

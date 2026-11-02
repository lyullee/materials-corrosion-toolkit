"""Verify discrete critical-plane tensor projections against independent closed forms."""

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


def _history(kind: str) -> dict:
    root_half = math.sqrt(0.5)
    if kind == "uniaxial":
        stress = [[value, 0.0, 0.0, 0.0, 0.0, 0.0] for value in (0.0, 100e6, 0.0, -100e6, 0.0)]
        strain = [[value, 0.0, 0.0, 0.0, 0.0, 0.0] for value in (0.0, 5e-4, 0.0, -5e-4, 0.0)]
    else:
        stress = [[0.0, 0.0, 0.0, value, 0.0, 0.0] for value in (0.0, 30e6, 0.0, -30e6, 0.0)]
        strain = [[0.0, 0.0, 0.0, value, 0.0, 0.0] for value in (0.0, 0.001, 0.0, -0.001, 0.0)]
    return {
        "history_id": f"synthetic-{kind}",
        "material_condition_id": "synthetic",
        "location_id": "closed-form-point",
        "tensor_source_id": "authored-analytic-history",
        "sample_ids": ["s0", "s1", "s2", "s3", "s4"],
        "stress_tensor_components_Pa": stress,
        "strain_tensor_components": strain,
        "candidate_planes": [
            {"plane_id": "xy", "normal": [1.0, 0.0, 0.0], "in_plane_direction": [0.0, 1.0, 0.0]},
            {
                "plane_id": "xy-45",
                "normal": [root_half, root_half, 0.0],
                "in_plane_direction": [-root_half, root_half, 0.0],
            },
        ],
        "representative_cycle_declared": True,
        "maximum_stress_closure_error_Pa": 0.0,
        "maximum_strain_closure_error": 0.0,
        "fatemi_socie_coefficient": 0.3,
        "normalization_stress_Pa": 400e6,
    }


def main():
    context = RunContext(asset_id="synthetic", location_id="closed-form-point", time_basis="one closed cycle")
    registry = default_registry()
    uniaxial = registry.run("fatigue.critical_plane_factors", _history("uniaxial"), context)
    shear = registry.run("fatigue.critical_plane_factors", _history("pure_tensor_shear"), context)
    vector_input = _history("pure_tensor_shear")
    component = 0.002 / math.sqrt(2) / 2
    stress_component = 40e6 / math.sqrt(2)
    vector_input["sample_ids"] = ["zero-start", "positive", "negative", "zero-end"]
    vector_input["stress_tensor_components_Pa"] = [
        [0.0, 0.0, 0.0, value, 0.0, value] for value in (0.0, stress_component, -stress_component, 0.0)
    ]
    vector_input["strain_tensor_components"] = [
        [0.0, 0.0, 0.0, value, 0.0, value] for value in (0.0, component, -component, 0.0)
    ]
    vector = registry.run("fatigue.critical_plane_vector_path_factors", vector_input, context)
    uniaxial_rows = {row["plane_id"]: row for row in uniaxial.values["candidate_factors"]}
    shear_rows = {row["plane_id"]: row for row in shear.values["candidate_factors"]}
    vector_rows = {row["plane_id"]: row for row in vector.values["candidate_factors"]}
    comparisons = {
        "uniaxial_axial_swt_Pa": (uniaxial_rows["xy"]["swt_factor_Pa"], 50_000.0),
        "uniaxial_rotated_shear_strain_amplitude": (uniaxial_rows["xy-45"]["shear_strain_amplitude"], 5e-4),
        "uniaxial_rotated_fs_factor": (
            uniaxial_rows["xy-45"]["fatemi_socie_factor"],
            5e-4 * (1 + 0.3 * 0.125),
        ),
        "pure_shear_engineering_amplitude": (shear_rows["xy"]["shear_strain_amplitude"], 0.002),
        "pure_shear_stress_amplitude_Pa": (shear_rows["xy"]["shear_stress_amplitude_Pa"], 30e6),
        "oblique_vector_chord_strain_amplitude": (
            vector_rows["xy"]["shear_strain_vector_chord_amplitude"],
            0.002,
        ),
        "oblique_vector_chord_stress_amplitude_Pa": (
            vector_rows["xy"]["shear_stress_vector_chord_amplitude_Pa"],
            40e6,
        ),
    }
    records = []
    for name, (actual, expected) in comparisons.items():
        absolute_error = abs(actual - expected)
        tolerance = 1e-12 * max(abs(expected), 1.0)
        if absolute_error > tolerance:
            raise AssertionError(f"{name}: {actual} != {expected}")
        records.append(
            {"case_id": name, "actual": actual, "expected": expected, "absolute_error": absolute_error}
        )
    record = {
        "schema_version": "matintegrity.critical_plane_math.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_ids": [
            "fatigue.critical_plane_factors",
            "fatigue.critical_plane_vector_path_factors",
        ],
        "model_source_sha256": hashlib.sha256(Path(fatigue.__file__).read_bytes()).hexdigest(),
        "benchmark_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "comparisons": records,
        "qualification": "Authored closed-form tensor-projection and sampled vector-chord checks only. No fatigue-life calibration, continuous-time or orientation-search convergence, notch solution or independent experiment is qualified.",
    }
    target = ROOT / "validation/critical_plane_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

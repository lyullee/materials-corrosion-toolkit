"""Verify qualified local-tensor exchange and critical-plane range composition."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.adapters import (
    LocalTensorHistory,
    critical_plane_inputs_from_local_tensor_history,
)
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def main():
    points = [
        (1.0, 0.0),
        (-0.5, math.sqrt(3) / 2),
        (-0.5, -math.sqrt(3) / 2),
        (1.0, 0.0),
    ]
    history = LocalTensorHistory(
        history_id="qualified-local-cycle",
        asset_id="synthetic-coupon",
        material_condition_id="synthetic-condition",
        location_id="notch-integration-point",
        load_case_id="nonproportional-cycle",
        tensor_source_id="synthetic-fe-export",
        provider_id="example-fe-adapter",
        provider_version="1.0.0",
        solver_name="synthetic-solver",
        solver_version="1.0",
        analysis_id="analysis-001",
        solution_revision="rev-a",
        mesh_id="mesh-001",
        field_location_kind="integration_point",
        field_location_id="element-42:ip-3",
        spatial_averaging="none",
        coordinate_frame_id="global-cartesian",
        coordinate_basis_vectors_global=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        stress_measure="cauchy",
        strain_measure="infinitesimal",
        strain_shear_convention="engineering",
        sample_ids=["v0", "v1", "v2", "v0-close"],
        sample_times_s=[0.0, 1.0, 2.0, 3.0],
        sample_valid=[True, True, True, True],
        stress_tensor_components_Pa=[[0.0, 0.0, 0.0, 40e6 * x, 0.0, 40e6 * y] for x, y in points],
        strain_tensor_components=[[0.0, 0.0, 0.0, 0.002 * x, 0.0, 0.002 * y] for x, y in points],
        representative_cycle_declared=True,
        tensor_field_review_status="qualified_by_caller",
        source_content_sha256="a" * 64,
        provider_configuration_digest="b" * 64,
    )
    context = RunContext(
        asset_id="synthetic-coupon",
        location_id="notch-integration-point",
        time_basis="one reviewed synthetic cycle",
    )
    payload = critical_plane_inputs_from_local_tensor_history(
        history,
        context=context,
        candidate_planes=(
            {
                "plane_id": "normal-x",
                "normal": [1.0, 0.0, 0.0],
                "in_plane_direction": [0.0, 1.0, 0.0],
            },
        ),
        maximum_stress_closure_error_Pa=0.0,
        maximum_strain_closure_error=0.0,
        fatemi_socie_coefficient=0.3,
        normalization_stress_Pa=400e6,
    )
    registry = default_registry()
    chord = registry.run("fatigue.critical_plane_vector_path_factors", payload, context)
    circle = registry.run("fatigue.critical_plane_minimum_enclosing_circle_factors", payload, context)
    chord_amplitude = chord.values["candidate_factors"][0]["shear_strain_vector_chord_amplitude"]
    circle_row = circle.values["candidate_factors"][0]
    circle_amplitude = circle_row["shear_strain_minimum_enclosing_circle_amplitude"]
    expected_chord = 0.002 * math.sqrt(3) / 2
    expected_circle = 0.002
    if abs(chord_amplitude - expected_chord) > 1e-15:
        raise AssertionError("engineering-shear conversion or chord composition changed")
    if abs(circle_amplitude - expected_circle) > 1e-15:
        raise AssertionError("engineering-shear conversion or circle composition changed")
    record = {
        "schema_version": "matintegrity.local_tensor_adapter_math.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "interface_id": "integration.local_tensor_history",
        "adapter_source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/adapters.py").read_bytes()
        ).hexdigest(),
        "benchmark_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "tensor_history_record_digest": payload["tensor_history_record_digest"],
        "preserved_identity": {
            key: payload[key]
            for key in (
                "load_case_id",
                "analysis_id",
                "mesh_id",
                "field_location_id",
                "coordinate_frame_id",
            )
        },
        "expected_chord_amplitude": expected_chord,
        "actual_chord_amplitude": chord_amplitude,
        "expected_circle_amplitude": expected_circle,
        "actual_circle_amplitude": circle_amplitude,
        "circle_to_chord_ratio": circle_row["shear_strain_circle_to_chord_amplitude_ratio"],
        "qualification": "Authored engineering-shear exchange record verifies identity, convention conversion and composition with two finite sampled range definitions. It is not a qualified FE solution, mesh-convergence result, local-field validation, fatigue-life calibration or experiment agreement.",
    }
    target = ROOT / "validation/local_tensor_adapter_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

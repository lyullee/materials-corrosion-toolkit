"""Compose a qualified local tensor exchange record with two critical-plane ranges."""

import math

from matintegrity.adapters import (
    LocalTensorHistory,
    critical_plane_inputs_from_local_tensor_history,
)
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


def main():
    points = [
        (1.0, 0.0),
        (-0.5, math.sqrt(3) / 2),
        (-0.5, -math.sqrt(3) / 2),
        (1.0, 0.0),
    ]
    record = LocalTensorHistory(
        history_id="synthetic-cycle",
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
        asset_id=record.asset_id,
        location_id=record.location_id,
        time_basis="one reviewed synthetic cycle",
    )
    inputs = critical_plane_inputs_from_local_tensor_history(
        record,
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
    chord = registry.run("fatigue.critical_plane_vector_path_factors", inputs, context)
    circle = registry.run("fatigue.critical_plane_minimum_enclosing_circle_factors", inputs, context)
    print(chord.values["maximum_fatemi_socie_factor"])
    print(circle.values["maximum_fatemi_socie_factor"])


if __name__ == "__main__":
    main()

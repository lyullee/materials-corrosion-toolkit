import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


@pytest.fixture
def context():
    return RunContext(
        asset_id="synthetic-plane-grid",
        location_id="orientation-space",
        time_basis="deterministic geometry generation",
    )


def run(context, **overrides):
    inputs = {"grid_id": "grid", "polar_divisions": 2, "azimuthal_divisions": 8}
    return default_registry().run("fatigue.hemisphere_plane_grid", inputs | overrides, context)


def test_grid_count_and_exact_duplicate_policy(context):
    result = run(context)
    assert result.values["candidate_count"] == 1 + 8 + 4
    assert result.values["polar_step_rad"] == pytest.approx(math.pi / 4)
    assert result.values["azimuthal_step_rad"] == pytest.approx(math.pi / 4)
    candidates = result.values["candidate_planes"]
    assert candidates[0]["normal"] == [0.0, 0.0, 1.0]
    equator = candidates[-4:]
    assert all(row["normal"][2] == 0.0 for row in equator)
    assert len({row["plane_id"] for row in candidates}) == len(candidates)


def test_frames_are_orthonormal_and_normals_are_unique_up_to_sign(context):
    candidates = run(context, polar_divisions=4, azimuthal_divisions=12).values["candidate_planes"]
    normals = []
    for row in candidates:
        normal = row["normal"]
        direction = row["in_plane_direction"]
        assert math.sqrt(sum(value * value for value in normal)) == pytest.approx(1.0)
        assert math.sqrt(sum(value * value for value in direction)) == pytest.approx(1.0)
        assert sum(a * b for a, b in zip(normal, direction, strict=True)) == pytest.approx(0.0, abs=1e-15)
        normals.append(normal)
    for first in range(len(normals) - 1):
        for second in range(first + 1, len(normals)):
            dot = sum(a * b for a, b in zip(normals[first], normals[second], strict=True))
            assert abs(dot) < 1 - 1e-12


def test_generation_is_deterministic_and_angles_are_separate_metadata(context):
    first = run(context).values
    second = run(context).values
    assert first == second
    assert [row["plane_id"] for row in first["candidate_planes"]] == [
        row["plane_id"] for row in first["candidate_angles"]
    ]
    assert all(set(row) == {"plane_id", "normal", "in_plane_direction"} for row in first["candidate_planes"])


@pytest.mark.parametrize(
    "overrides",
    [
        {"polar_divisions": 0},
        {"azimuthal_divisions": 2},
        {"azimuthal_divisions": 5},
    ],
)
def test_invalid_grid_resolution_is_rejected(context, overrides):
    with pytest.raises(ValidationError):
        run(context, **overrides)


def test_generated_candidates_feed_vector_path_model_without_repair(context):
    candidates = run(context, polar_divisions=1, azimuthal_divisions=4).values["candidate_planes"]
    tensor_values = (0.0, 1e-4, -1e-4, 0.0)
    history = {
        "history_id": "grid-integration",
        "material_condition_id": "synthetic",
        "location_id": "point",
        "tensor_source_id": "closed-form",
        "sample_ids": ["s0", "s1", "s2", "s3"],
        "stress_tensor_components_Pa": [[value * 1e11, 0.0, 0.0, 0.0, 0.0, 0.0] for value in tensor_values],
        "strain_tensor_components": [[value, 0.0, 0.0, 0.0, 0.0, 0.0] for value in tensor_values],
        "candidate_planes": candidates,
        "representative_cycle_declared": True,
        "maximum_stress_closure_error_Pa": 0.0,
        "maximum_strain_closure_error": 0.0,
        "fatemi_socie_coefficient": 0.2,
        "normalization_stress_Pa": 400e6,
    }
    result = default_registry().run("fatigue.critical_plane_vector_path_factors", history, context)
    assert result.status == "computed"
    assert result.values["candidate_count"] == len(candidates)

import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


@pytest.fixture
def context():
    return RunContext(
        asset_id="synthetic-fibonacci-grid",
        location_id="orientation-space",
        time_basis="deterministic geometry generation",
    )


def run(context, **overrides):
    inputs = {"grid_id": "fib", "candidate_count": 16, "azimuth_phase_rad": 0.0}
    return default_registry().run("fatigue.area_uniform_fibonacci_plane_grid", inputs | overrides, context)


def test_equal_area_coordinate_midpoints_and_weights(context):
    result = run(context)
    assert result.values["candidate_count"] == 16
    positions = result.values["sampling_positions"]
    assert [row["equal_area_coordinate_z"] for row in positions] == pytest.approx(
        [(index + 0.5) / 16 for index in range(16)]
    )
    assert result.values["nominal_solid_angle_weight_sr"] == pytest.approx(2 * math.pi / 16)
    assert result.values["nominal_weight_sum_sr"] == pytest.approx(2 * math.pi)
    weighted_mean_z = (
        sum(row["equal_area_coordinate_z"] * row["nominal_solid_angle_weight_sr"] for row in positions)
        / result.values["nominal_weight_sum_sr"]
    )
    assert weighted_mean_z == pytest.approx(0.5)


def test_frames_are_orthonormal_and_planes_are_unique_up_to_sign(context):
    candidates = run(context, candidate_count=31).values["candidate_planes"]
    for row in candidates:
        normal = row["normal"]
        direction = row["in_plane_direction"]
        assert normal[2] > 0
        assert math.sqrt(sum(value * value for value in normal)) == pytest.approx(1.0)
        assert math.sqrt(sum(value * value for value in direction)) == pytest.approx(1.0)
        assert sum(a * b for a, b in zip(normal, direction, strict=True)) == pytest.approx(0.0, abs=1e-15)
    for first in range(len(candidates) - 1):
        for second in range(first + 1, len(candidates)):
            alignment = abs(
                sum(
                    a * b
                    for a, b in zip(candidates[first]["normal"], candidates[second]["normal"], strict=True)
                )
            )
            assert alignment < 1 - 1e-12


def test_generation_is_deterministic_and_phase_is_explicit(context):
    first = run(context).values
    assert first == run(context).values
    shifted = run(context, azimuth_phase_rad=0.25).values
    assert first["candidate_planes"] != shifted["candidate_planes"]
    assert [row["equal_area_coordinate_z"] for row in first["sampling_positions"]] == [
        row["equal_area_coordinate_z"] for row in shifted["sampling_positions"]
    ]
    assert all(set(row) == {"plane_id", "normal", "in_plane_direction"} for row in first["candidate_planes"])


@pytest.mark.parametrize(
    "overrides",
    [
        {"candidate_count": 3},
        {"azimuth_phase_rad": -0.1},
        {"azimuth_phase_rad": 2 * math.pi},
    ],
)
def test_invalid_grid_parameters_are_rejected(context, overrides):
    with pytest.raises(ValidationError):
        run(context, **overrides)


def test_generated_candidates_feed_vector_path_model_without_repair(context):
    candidates = run(context, candidate_count=8).values["candidate_planes"]
    tensor_values = (0.0, 1e-4, -1e-4, 0.0)
    history = {
        "history_id": "fibonacci-integration",
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
    assert result.values["candidate_count"] == 8

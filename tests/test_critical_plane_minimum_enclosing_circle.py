import math
from itertools import combinations

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.fatigue import _minimum_enclosing_circle
from matintegrity.registry import default_registry


@pytest.fixture
def context():
    return RunContext(
        asset_id="synthetic-enclosing-circle",
        location_id="reviewed-point",
        time_basis="one closed synthetic cycle",
    )


def equilateral_inputs(direction=(0.0, 1.0, 0.0)):
    strain_radius = 0.002
    stress_radius = 40e6
    points = [
        (1.0, 0.0),
        (-0.5, math.sqrt(3) / 2),
        (-0.5, -math.sqrt(3) / 2),
        (1.0, 0.0),
    ]
    return {
        "history_id": "equilateral-shear-cycle",
        "material_condition_id": "synthetic",
        "location_id": "point",
        "tensor_source_id": "closed-form",
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
                "in_plane_direction": list(direction),
            }
        ],
        "representative_cycle_declared": True,
        "maximum_stress_closure_error_Pa": 0.0,
        "maximum_strain_closure_error": 0.0,
        "fatemi_socie_coefficient": 0.3,
        "normalization_stress_Pa": 400e6,
    }


def run(context, payload=None, **overrides):
    return default_registry().run(
        "fatigue.critical_plane_minimum_enclosing_circle_factors",
        (payload or equilateral_inputs()) | overrides,
        context,
    )


def row(result):
    return result.values["candidate_factors"][0]


def exhaustive_circle(points):
    candidates = []
    for point in points:
        candidates.append((point, 0.0))
    for first, second in combinations(points, 2):
        center = ((first[0] + second[0]) / 2, (first[1] + second[1]) / 2)
        candidates.append((center, math.dist(center, first)))
    for first, second, third in combinations(points, 3):
        determinant = 2 * (
            first[0] * (second[1] - third[1])
            + second[0] * (third[1] - first[1])
            + third[0] * (first[1] - second[1])
        )
        if abs(determinant) < 1e-14:
            continue
        squares = [point[0] ** 2 + point[1] ** 2 for point in (first, second, third)]
        center = (
            (
                squares[0] * (second[1] - third[1])
                + squares[1] * (third[1] - first[1])
                + squares[2] * (first[1] - second[1])
            )
            / determinant,
            (
                squares[0] * (third[0] - second[0])
                + squares[1] * (first[0] - third[0])
                + squares[2] * (second[0] - first[0])
            )
            / determinant,
        )
        candidates.append((center, math.dist(center, first)))
    valid = [
        circle
        for circle in candidates
        if all(math.dist(circle[0], point) <= circle[1] + 1e-12 for point in points)
    ]
    return min(valid, key=lambda circle: circle[1])


def test_equilateral_path_distinguishes_circle_from_chord(context):
    result = run(context)
    candidate = row(result)
    assert result.status == "computed"
    assert result.values["shear_path_range_method"] == "minimum_enclosing_circle_radius"
    assert candidate["shear_strain_minimum_enclosing_circle_amplitude"] == pytest.approx(0.002)
    assert candidate["shear_strain_vector_chord_amplitude"] == pytest.approx(0.002 * math.sqrt(3) / 2)
    assert candidate["shear_strain_circle_to_chord_amplitude_ratio"] == pytest.approx(2 / math.sqrt(3))
    assert candidate["fatemi_socie_factor"] == pytest.approx(0.002)
    assert set(candidate["shear_strain_circle_support_sample_ids"]) == {"v0", "v1", "v2"}


def test_stress_circle_matches_independent_equilateral_radius(context):
    candidate = row(run(context))
    assert candidate["shear_stress_minimum_enclosing_circle_amplitude_Pa"] == pytest.approx(40e6)
    assert candidate["shear_stress_vector_chord_amplitude_Pa"] == pytest.approx(40e6 * math.sqrt(3) / 2)
    assert candidate["shear_stress_circle_center_Pa"] == pytest.approx([0.0, 0.0], abs=1e-8)


def test_radius_is_invariant_to_in_plane_basis_rotation_and_reversal(context):
    angle = 0.37
    directions = (
        (0.0, 1.0, 0.0),
        (0.0, math.cos(angle), math.sin(angle)),
        (0.0, -1.0, 0.0),
    )
    radii = [
        row(run(context, equilateral_inputs(direction)))["shear_strain_minimum_enclosing_circle_amplitude"]
        for direction in directions
    ]
    assert radii == pytest.approx([0.002] * 3)


def test_collinear_path_circle_equals_half_maximum_chord(context):
    values = [0.0, 0.001, 0.0, -0.001, 0.0]
    payload = equilateral_inputs() | {
        "sample_ids": [f"s{index}" for index in range(5)],
        "stress_tensor_components_Pa": [[0.0, 0.0, 0.0, value * 30e9, 0.0, 0.0] for value in values],
        "strain_tensor_components": [[0.0, 0.0, 0.0, value, 0.0, 0.0] for value in values],
    }
    candidate = row(run(context, payload))
    assert candidate["shear_strain_minimum_enclosing_circle_amplitude"] == pytest.approx(0.002)
    assert candidate["shear_strain_vector_chord_amplitude"] == pytest.approx(0.002)
    assert candidate["shear_strain_circle_to_chord_amplitude_ratio"] == pytest.approx(1.0)


def test_incremental_circle_matches_independent_exhaustive_construction():
    points = [(-1.2, 0.4), (0.3, 1.8), (2.1, -0.2), (0.7, -1.4), (-0.4, 0.1)]
    expected_center, expected_radius = exhaustive_circle(points)
    center, radius, support = _minimum_enclosing_circle(points, [f"p{index}" for index in range(len(points))])
    assert center == pytest.approx(expected_center)
    assert radius == pytest.approx(expected_radius)
    assert 2 <= len(support) <= 3


def test_circle_radius_is_order_scale_and_translation_invariant():
    base = [(-1.2, 0.4), (0.3, 1.8), (2.1, -0.2), (0.7, -1.4), (-0.4, 0.1)]
    _, base_radius, _ = _minimum_enclosing_circle(base, [f"b{i}" for i in range(len(base))])
    transformed = [(point[0] * 1e9 + 7e10, point[1] * 1e9 - 3e10) for point in reversed(base)]
    _, transformed_radius, _ = _minimum_enclosing_circle(
        transformed, [f"t{i}" for i in range(len(transformed))]
    )
    assert transformed_radius == pytest.approx(base_radius * 1e9, rel=1e-12)


def test_open_history_returns_needs_data_without_circle_claim(context):
    result = run(context, representative_cycle_declared=False)
    assert result.status == "needs_data"
    assert result.values["candidate_factors"] == []
    assert result.values["maximum_fatemi_socie_factor"] is None


def test_output_does_not_claim_life_acceptance_or_probability(context):
    result = run(context)
    keys = " ".join(result.values).lower()
    assert not any(token in keys for token in ("life", "accept", "probability"))
    assert result.probability_semantics == {}

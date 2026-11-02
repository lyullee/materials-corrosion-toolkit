import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


@pytest.fixture
def context():
    return RunContext(
        asset_id="synthetic-adaptive-search",
        location_id="reviewed-point",
        time_basis="one closed synthetic cycle",
    )


def inputs(**overrides):
    axis = [1 / math.sqrt(14), 2 / math.sqrt(14), 3 / math.sqrt(14)]
    dyad = [
        axis[0] ** 2,
        axis[1] ** 2,
        axis[2] ** 2,
        axis[0] * axis[1],
        axis[1] * axis[2],
        axis[2] * axis[0],
    ]
    amplitudes = [0.0, 1.0, 0.0, -1.0, 0.0]
    base = {
        "history_id": "inclined-uniaxial-cycle",
        "material_condition_id": "synthetic",
        "location_id": "point",
        "tensor_source_id": "closed-form",
        "sample_ids": [f"s{index}" for index in range(len(amplitudes))],
        "stress_tensor_components_Pa": [
            [value * 100e6 * component for component in dyad] for value in amplitudes
        ],
        "strain_tensor_components": [
            [value * 5e-4 * component for component in dyad] for value in amplitudes
        ],
        "seed_grid": {"grid_id": "seed", "candidate_count": 16, "azimuth_phase_rad": 0.17},
        "representative_cycle_declared": True,
        "maximum_stress_closure_error_Pa": 0.0,
        "maximum_strain_closure_error": 0.0,
        "fatemi_socie_coefficient": 0.3,
        "normalization_stress_Pa": 400e6,
        "refinement_rounds": 6,
        "ring_points": 24,
        "initial_radius_rad": math.pi / 8,
        "radius_reduction_factor": 0.5,
        "declared_maximum_final_relative_factor_change": 1e-4,
        "declared_maximum_final_plane_rotation_rad": 0.02,
    }
    return base | overrides


def run(context, **overrides):
    return default_registry().run("fatigue.critical_plane_adaptive_search", inputs(**overrides), context)


def test_separate_searches_improve_finite_grid_seeds(context):
    result = run(context)
    assert result.status == "computed"
    assert result.values["seed_grid_family"] == "area_uniform_fibonacci"
    assert result.values["seed_candidate_count"] == 16
    for key in ("fatemi_socie_search", "swt_search"):
        search = result.values[key]
        assert search["final_factor"] >= search["seed_factor"]
        assert len(search["rounds"]) == 6
        assert all(row["candidate_count"] == 25 for row in search["rounds"])


def test_swt_search_approaches_inclined_uniaxial_closed_form(context):
    result = run(context)
    search = result.values["swt_search"]
    expected_factor = 100e6 * 5e-4
    assert abs(search["final_factor"] - expected_factor) / expected_factor < 1e-4
    axis = [1 / math.sqrt(14), 2 / math.sqrt(14), 3 / math.sqrt(14)]
    alignment = abs(sum(a * b for a, b in zip(axis, search["final_plane_normal"], strict=True)))
    assert math.acos(min(1.0, alignment)) < 0.01


def test_round_radii_and_reported_transitions_are_reproducible(context):
    first = run(context).values
    second = run(context).values
    assert first == second
    for search in (first["fatemi_socie_search"], first["swt_search"]):
        previous_factor = search["seed_factor"]
        previous_normal = search["seed_plane_normal"]
        for index, row in enumerate(search["rounds"]):
            assert row["search_radius_rad"] == pytest.approx(math.pi / 8 * 0.5**index)
            expected_change = abs(row["factor"] - previous_factor) / max(
                abs(row["factor"]), abs(previous_factor)
            )
            alignment = abs(
                sum(a * b for a, b in zip(previous_normal, row["selected_plane_normal"], strict=True))
            )
            assert row["relative_factor_change"] == pytest.approx(expected_change)
            assert row["plane_rotation_rad"] == pytest.approx(math.acos(min(1.0, max(0.0, alignment))))
            previous_factor = row["factor"]
            previous_normal = row["selected_plane_normal"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("refinement_rounds", 0),
        ("ring_points", 3),
        ("initial_radius_rad", math.pi / 2),
        ("radius_reduction_factor", 1.0),
    ],
)
def test_invalid_search_schedules_are_rejected(context, field, value):
    with pytest.raises(ValidationError):
        run(context, **{field: value})


def test_open_history_returns_needs_data_without_local_search(context):
    result = run(context, representative_cycle_declared=False)
    assert result.status == "needs_data"
    assert result.values["evaluated_refinement_rounds"] == 0
    assert result.values["fatemi_socie_search"] is None
    assert result.values["swt_search"] is None
    assert result.values["both_final_transitions_within_declared_tolerances"] is None

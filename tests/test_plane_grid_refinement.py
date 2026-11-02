import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


@pytest.fixture
def context():
    return RunContext(
        asset_id="synthetic-grid-refinement",
        location_id="reviewed-point",
        time_basis="one closed synthetic cycle",
    )


def inputs(**overrides):
    amplitudes = [0.0, 1.0, 0.0, -1.0, 0.0]
    base = {
        "history_id": "closed-uniaxial",
        "material_condition_id": "synthetic",
        "location_id": "point",
        "tensor_source_id": "closed-form",
        "sample_ids": [f"s{index}" for index in range(len(amplitudes))],
        "stress_tensor_components_Pa": [[value * 100e6, 0.0, 0.0, 0.0, 0.0, 0.0] for value in amplitudes],
        "strain_tensor_components": [[value * 5e-4, 0.0, 0.0, 0.0, 0.0, 0.0] for value in amplitudes],
        "representative_cycle_declared": True,
        "maximum_stress_closure_error_Pa": 0.0,
        "maximum_strain_closure_error": 0.0,
        "fatemi_socie_coefficient": 0.3,
        "normalization_stress_Pa": 400e6,
        "refinement_levels": [
            {"grid_id": "coarse", "polar_divisions": 2, "azimuthal_divisions": 8},
            {"grid_id": "medium", "polar_divisions": 4, "azimuthal_divisions": 16},
            {"grid_id": "fine", "polar_divisions": 8, "azimuthal_divisions": 32},
        ],
        "declared_maximum_relative_factor_change": 1e-12,
        "declared_maximum_plane_rotation_rad": math.pi / 2,
    }
    return base | overrides


def run(context, **overrides):
    return default_registry().run("fatigue.critical_plane_grid_refinement", inputs(**overrides), context)


def test_uniaxial_exact_orientations_are_stable_across_nested_grids(context):
    result = run(context)
    assert result.status == "computed"
    assert result.values["refinement_level_count"] == 3
    assert result.values["evaluated_level_count"] == 3
    assert [row["candidate_count"] for row in result.values["levels"]] == [13, 57, 241]
    assert result.values["all_transitions_within_declared_tolerances"] is True
    for row in result.values["levels"]:
        assert row["maximum_fatemi_socie_factor"] == pytest.approx(0.00051875)
        assert row["maximum_swt_factor_Pa"] == pytest.approx(50000.0)
    for row in result.values["levels"][1:]:
        transition = row["transition_from_previous"]
        assert transition["fatemi_socie_relative_change"] == pytest.approx(0.0, abs=1e-15)
        assert transition["swt_relative_change"] == pytest.approx(0.0, abs=1e-15)


def test_each_level_matches_direct_vector_path_evaluation(context):
    definitions = [
        {"grid_id": "g1", "polar_divisions": 1, "azimuthal_divisions": 4},
        {"grid_id": "g2", "polar_divisions": 3, "azimuthal_divisions": 12},
    ]
    result = run(context, refinement_levels=definitions)
    registry = default_registry()
    for definition, row in zip(definitions, result.values["levels"], strict=True):
        grid = registry.run("fatigue.hemisphere_plane_grid", definition, context)
        history = inputs()
        for key in (
            "refinement_levels",
            "declared_maximum_relative_factor_change",
            "declared_maximum_plane_rotation_rad",
        ):
            history.pop(key)
        history["candidate_planes"] = grid.values["candidate_planes"]
        direct = registry.run("fatigue.critical_plane_vector_path_factors", history, context)
        assert row["maximum_fatemi_socie_factor"] == direct.values["maximum_fatemi_socie_factor"]
        assert row["maximum_swt_factor_Pa"] == direct.values["maximum_swt_factor_Pa"]


@pytest.mark.parametrize(
    "levels",
    [
        [
            {"grid_id": "same", "polar_divisions": 2, "azimuthal_divisions": 8},
            {"grid_id": "same", "polar_divisions": 4, "azimuthal_divisions": 16},
        ],
        [
            {"grid_id": "fine", "polar_divisions": 4, "azimuthal_divisions": 16},
            {"grid_id": "coarse", "polar_divisions": 2, "azimuthal_divisions": 8},
        ],
        [
            {"grid_id": "a", "polar_divisions": 2, "azimuthal_divisions": 8},
            {"grid_id": "b", "polar_divisions": 2, "azimuthal_divisions": 8},
        ],
    ],
)
def test_invalid_refinement_sequences_are_rejected(context, levels):
    with pytest.raises(ValidationError):
        run(context, refinement_levels=levels)


def test_open_history_returns_needs_data_without_stability_claim(context):
    result = run(context, representative_cycle_declared=False)
    assert result.status == "needs_data"
    assert result.values["evaluated_level_count"] == 0
    assert result.values["levels"] == []
    assert result.values["final_transition_within_declared_tolerances"] is None
    assert result.values["all_transitions_within_declared_tolerances"] is None

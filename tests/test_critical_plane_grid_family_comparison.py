import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


@pytest.fixture
def context():
    return RunContext(
        asset_id="synthetic-grid-family-comparison",
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
        "grid_definitions": [
            {"grid_id": "latitude-reference", "polar_divisions": 4, "azimuthal_divisions": 16},
            {"grid_id": "fibonacci-zero", "candidate_count": 64, "azimuth_phase_rad": 0.0},
            {"grid_id": "fibonacci-shifted", "candidate_count": 64, "azimuth_phase_rad": 0.31},
        ],
        "reference_grid_id": "latitude-reference",
        "representative_cycle_declared": True,
        "maximum_stress_closure_error_Pa": 0.0,
        "maximum_strain_closure_error": 0.0,
        "fatemi_socie_coefficient": 0.3,
        "normalization_stress_Pa": 400e6,
        "declared_maximum_relative_factor_change": 1.0,
        "declared_maximum_plane_rotation_rad": math.pi / 2,
    }
    return base | overrides


def run(context, **overrides):
    return default_registry().run(
        "fatigue.critical_plane_grid_family_comparison", inputs(**overrides), context
    )


def test_grid_families_counts_phases_and_reference_comparisons(context):
    result = run(context)
    assert result.status == "computed"
    assert result.values["grid_count"] == 3
    assert result.values["evaluated_grid_count"] == 3
    assert result.values["all_comparisons_within_declared_tolerances"] is True
    reference, zero, shifted = result.values["grids"]
    assert reference["grid_family"] == "latitude_azimuth"
    assert reference["candidate_count"] == 57
    assert reference["comparison_to_reference"] is None
    assert zero["grid_family"] == shifted["grid_family"] == "area_uniform_fibonacci"
    assert zero["candidate_count"] == shifted["candidate_count"] == 64
    assert zero["grid_definition"]["azimuth_phase_rad"] == 0.0
    assert shifted["grid_definition"]["azimuth_phase_rad"] == 0.31
    assert zero["comparison_to_reference"]["reference_grid_id"] == "latitude-reference"
    assert shifted["comparison_to_reference"]["reference_grid_id"] == "latitude-reference"


def test_each_grid_matches_direct_generation_and_vector_evaluation(context):
    payload = inputs()
    result = default_registry().run("fatigue.critical_plane_grid_family_comparison", payload, context)
    registry = default_registry()
    for definition, row in zip(payload["grid_definitions"], result.values["grids"], strict=True):
        generator = (
            "fatigue.hemisphere_plane_grid"
            if "polar_divisions" in definition
            else "fatigue.area_uniform_fibonacci_plane_grid"
        )
        candidates = registry.run(generator, definition, context).values["candidate_planes"]
        history = {
            key: payload[key]
            for key in (
                "history_id",
                "material_condition_id",
                "location_id",
                "tensor_source_id",
                "sample_ids",
                "stress_tensor_components_Pa",
                "strain_tensor_components",
                "representative_cycle_declared",
                "maximum_stress_closure_error_Pa",
                "maximum_strain_closure_error",
                "fatemi_socie_coefficient",
                "normalization_stress_Pa",
            )
        }
        history["candidate_planes"] = candidates
        direct = registry.run("fatigue.critical_plane_vector_path_factors", history, context)
        assert row["maximum_fatemi_socie_factor"] == direct.values["maximum_fatemi_socie_factor"]
        assert row["maximum_swt_factor_Pa"] == direct.values["maximum_swt_factor_Pa"]


def test_reported_relative_changes_match_definition(context):
    rows = run(context).values["grids"]
    reference = rows[0]
    for row in rows[1:]:
        comparison = row["comparison_to_reference"]
        expected_fs = abs(
            row["maximum_fatemi_socie_factor"] - reference["maximum_fatemi_socie_factor"]
        ) / max(row["maximum_fatemi_socie_factor"], reference["maximum_fatemi_socie_factor"])
        expected_swt = abs(row["maximum_swt_factor_Pa"] - reference["maximum_swt_factor_Pa"]) / max(
            row["maximum_swt_factor_Pa"], reference["maximum_swt_factor_Pa"]
        )
        assert comparison["fatemi_socie_relative_change"] == pytest.approx(expected_fs)
        assert comparison["swt_relative_change"] == pytest.approx(expected_swt)


@pytest.mark.parametrize(
    ("definitions", "reference"),
    [
        (
            [
                {"grid_id": "same", "polar_divisions": 2, "azimuthal_divisions": 8},
                {"grid_id": "same", "candidate_count": 32, "azimuth_phase_rad": 0.0},
            ],
            "same",
        ),
        (
            [
                {"grid_id": "latitude", "polar_divisions": 2, "azimuthal_divisions": 8},
                {"grid_id": "fibonacci", "candidate_count": 32, "azimuth_phase_rad": 0.0},
            ],
            "missing",
        ),
    ],
)
def test_duplicate_or_missing_reference_grid_is_rejected(context, definitions, reference):
    with pytest.raises(ValidationError):
        run(context, grid_definitions=definitions, reference_grid_id=reference)


def test_open_history_returns_needs_data_without_comparison_claim(context):
    result = run(context, representative_cycle_declared=False)
    assert result.status == "needs_data"
    assert result.values["evaluated_grid_count"] == 0
    assert result.values["grids"] == []
    assert result.values["all_comparisons_within_declared_tolerances"] is None

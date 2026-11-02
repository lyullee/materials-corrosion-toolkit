import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


@pytest.fixture
def context():
    return RunContext(
        asset_id="synthetic-local-history",
        location_id="reviewed-integration-point",
        time_basis="one declared representative cycle",
    )


def base_inputs():
    root_half = math.sqrt(0.5)
    stress = [0.0, 100e6, 0.0, -100e6, 0.0]
    strain = [0.0, 5e-4, 0.0, -5e-4, 0.0]
    return {
        "history_id": "closed-uniaxial-cycle",
        "material_condition_id": "synthetic-condition",
        "location_id": "reviewed-integration-point",
        "tensor_source_id": "independent-closed-form",
        "sample_ids": ["s0", "s1", "s2", "s3", "s4"],
        "stress_tensor_components_Pa": [[value, 0.0, 0.0, 0.0, 0.0, 0.0] for value in stress],
        "strain_tensor_components": [[value, 0.0, 0.0, 0.0, 0.0, 0.0] for value in strain],
        "candidate_planes": [
            {
                "plane_id": "normal-x",
                "normal": [1.0, 0.0, 0.0],
                "in_plane_direction": [0.0, 1.0, 0.0],
            },
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


def run(context, **overrides):
    return default_registry().run("fatigue.critical_plane_factors", base_inputs() | overrides, context)


def run_vector(context, **overrides):
    return default_registry().run(
        "fatigue.critical_plane_vector_path_factors", base_inputs() | overrides, context
    )


def by_id(result, plane_id):
    return next(row for row in result.values["candidate_factors"] if row["plane_id"] == plane_id)


def test_uniaxial_closed_form_swt_and_rotated_fs(context):
    result = run(context)
    axial = by_id(result, "normal-x")
    rotated = by_id(result, "xy-45")
    assert axial["normal_strain_amplitude"] == pytest.approx(5e-4)
    assert axial["maximum_tensile_normal_stress_Pa"] == pytest.approx(100e6)
    assert axial["swt_factor_Pa"] == pytest.approx(50_000.0)
    assert rotated["shear_strain_amplitude"] == pytest.approx(5e-4)
    assert rotated["maximum_tensile_normal_stress_Pa"] == pytest.approx(50e6)
    assert rotated["fatemi_socie_factor"] == pytest.approx(5e-4 * (1 + 0.3 * 0.125))
    assert result.values["swt_plane_id"] == "normal-x"
    assert result.values["fatemi_socie_plane_id"] == "xy-45"


def test_tensor_shear_is_converted_to_engineering_shear(context):
    tensor_shear_strain = [0.0, 0.001, 0.0, -0.001, 0.0]
    shear_stress = [0.0, 30e6, 0.0, -30e6, 0.0]
    result = run(
        context,
        stress_tensor_components_Pa=[[0.0, 0.0, 0.0, value, 0.0, 0.0] for value in shear_stress],
        strain_tensor_components=[[0.0, 0.0, 0.0, value, 0.0, 0.0] for value in tensor_shear_strain],
        candidate_planes=[
            {
                "plane_id": "xy",
                "normal": [1.0, 0.0, 0.0],
                "in_plane_direction": [0.0, 1.0, 0.0],
            }
        ],
    )
    row = by_id(result, "xy")
    assert row["shear_strain_amplitude"] == pytest.approx(0.002)
    assert row["shear_stress_amplitude_Pa"] == pytest.approx(30e6)
    assert row["fatemi_socie_factor"] == pytest.approx(0.002)
    assert row["swt_factor_Pa"] == 0.0


@pytest.mark.parametrize(
    "overrides",
    [
        {"representative_cycle_declared": False},
        {
            "stress_tensor_components_Pa": [[1.0, 0.0, 0.0, 0.0, 0.0, 0.0]] * 4
            + [[2.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
        },
        {
            "strain_tensor_components": [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]] * 4
            + [[1e-6, 0.0, 0.0, 0.0, 0.0, 0.0]]
        },
    ],
)
def test_undeclared_or_open_cycle_needs_data(context, overrides):
    result = run(context, **overrides)
    assert result.status == "needs_data"
    assert result.values["representative_cycle_usable"] is False
    assert result.values["candidate_factors"] == []
    assert result.values["maximum_fatemi_socie_factor"] is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"sample_ids": ["s0", "s1", "s1", "s3", "s4"]},
        {"stress_tensor_components_Pa": [[0.0] * 6] * 4},
        {"strain_tensor_components": [[0.0] * 6] * 4},
        {"stress_tensor_components_Pa": [[0.0] * 5] * 5},
        {
            "candidate_planes": [
                {
                    "plane_id": "bad",
                    "normal": [2.0, 0.0, 0.0],
                    "in_plane_direction": [0.0, 1.0, 0.0],
                }
            ]
        },
        {
            "candidate_planes": [
                {
                    "plane_id": "bad",
                    "normal": [1.0, 0.0, 0.0],
                    "in_plane_direction": [1.0, 0.0, 0.0],
                }
            ]
        },
    ],
)
def test_invalid_tensor_history_or_plane_is_rejected(context, overrides):
    with pytest.raises(ValidationError):
        run(context, **overrides)


def test_duplicate_plane_identifiers_are_rejected(context):
    plane = base_inputs()["candidate_planes"][0]
    with pytest.raises(ValidationError):
        run(context, candidate_planes=[plane, plane])


def test_outputs_do_not_claim_life_strength_acceptance_or_probability(context):
    result = run(context)
    encoded_keys = " ".join(result.values).lower()
    assert "life" not in encoded_keys
    assert "strength" not in encoded_keys
    assert "accept" not in encoded_keys
    assert "probability" not in encoded_keys
    assert result.probability_semantics == {}


def oblique_shear_inputs(reference_direction):
    radius = 0.002
    tensor_component = radius / math.sqrt(2) / 2
    stress_component = 40e6 / math.sqrt(2)
    strain_path = [0.0, tensor_component, -tensor_component, 0.0]
    stress_path = [0.0, stress_component, -stress_component, 0.0]
    return {
        "sample_ids": ["zero-start", "positive", "negative", "zero-end"],
        "stress_tensor_components_Pa": [[0.0, 0.0, 0.0, value, 0.0, value] for value in stress_path],
        "strain_tensor_components": [[0.0, 0.0, 0.0, value, 0.0, value] for value in strain_path],
        "candidate_planes": [
            {
                "plane_id": "normal-x",
                "normal": [1.0, 0.0, 0.0],
                "in_plane_direction": reference_direction,
            }
        ],
    }


def test_vector_chord_retains_oblique_in_plane_path(context):
    inputs = oblique_shear_inputs([0.0, 1.0, 0.0])
    vector = run_vector(context, **inputs)
    scalar = run(context, **inputs)
    row = by_id(vector, "normal-x")
    scalar_row = by_id(scalar, "normal-x")
    assert row["shear_strain_vector_chord_amplitude"] == pytest.approx(0.002)
    assert scalar_row["shear_strain_amplitude"] == pytest.approx(0.002 / math.sqrt(2))
    assert row["shear_stress_vector_chord_amplitude_Pa"] == pytest.approx(40e6)
    assert row["shear_strain_chord_start_sample_id"] == "positive"
    assert row["shear_strain_chord_end_sample_id"] == "negative"
    assert vector.values["shear_path_range_method"] == "maximum_pairwise_euclidean_chord"


def test_vector_chord_is_invariant_to_in_plane_basis_rotation_and_reversal(context):
    angle = 0.37
    directions = [
        [0.0, 1.0, 0.0],
        [0.0, math.cos(angle), math.sin(angle)],
        [0.0, -1.0, 0.0],
    ]
    amplitudes = []
    stress_amplitudes = []
    for direction in directions:
        result = run_vector(context, **oblique_shear_inputs(direction))
        row = by_id(result, "normal-x")
        amplitudes.append(row["shear_strain_vector_chord_amplitude"])
        stress_amplitudes.append(row["shear_stress_vector_chord_amplitude_Pa"])
    assert amplitudes == pytest.approx([0.002] * 3)
    assert stress_amplitudes == pytest.approx([40e6] * 3)


def test_vector_path_matches_scalar_range_for_collinear_path(context):
    vector = run_vector(context)
    scalar = run(context)
    for plane_id in ("normal-x", "xy-45"):
        assert by_id(vector, plane_id)["shear_strain_vector_chord_amplitude"] == pytest.approx(
            by_id(scalar, plane_id)["shear_strain_amplitude"]
        )


def test_vector_path_open_cycle_needs_data(context):
    result = run_vector(context, representative_cycle_declared=False)
    assert result.status == "needs_data"
    assert result.values["candidate_factors"] == []
    assert result.values["maximum_fatemi_socie_factor"] is None


def test_vector_path_does_not_claim_life_or_probability(context):
    result = run_vector(context, **oblique_shear_inputs([0.0, 1.0, 0.0]))
    assert not any(
        token in key.lower()
        for key in result.values
        for token in ("life", "strength", "accept", "probability")
    )
    assert result.probability_semantics == {}

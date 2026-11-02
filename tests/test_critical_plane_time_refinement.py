import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


@pytest.fixture
def context():
    return RunContext(
        asset_id="synthetic-time-refinement",
        location_id="reviewed-point",
        time_basis="one second closed synthetic cycle",
    )


def sampling(sampling_id, intervals, phase=0.31):
    times = [index / intervals for index in range(intervals + 1)]
    amplitudes = [math.sin(2 * math.pi * time + phase) for time in times]
    return {
        "sampling_id": sampling_id,
        "sample_ids": [f"{sampling_id}-s{index}" for index in range(len(times))],
        "sample_times_s": times,
        "stress_tensor_components_Pa": [[value * 100e6, 0.0, 0.0, 0.0, 0.0, 0.0] for value in amplitudes],
        "strain_tensor_components": [[value * 5e-4, 0.0, 0.0, 0.0, 0.0, 0.0] for value in amplitudes],
    }


def inputs(**overrides):
    root = math.sqrt(0.5)
    base = {
        "history_id": "phase-shifted-uniaxial",
        "material_condition_id": "synthetic",
        "location_id": "point",
        "tensor_source_id": "closed-form-sine",
        "candidate_planes": [
            {
                "plane_id": "normal-x",
                "normal": [1.0, 0.0, 0.0],
                "in_plane_direction": [0.0, 1.0, 0.0],
            },
            {
                "plane_id": "xy-45",
                "normal": [root, root, 0.0],
                "in_plane_direction": [-root, root, 0.0],
            },
        ],
        "sampling_levels": [sampling("coarse", 4), sampling("medium", 8), sampling("fine", 16)],
        "representative_cycle_declared": True,
        "maximum_stress_closure_error_Pa": 1e-7,
        "maximum_strain_closure_error": 1e-15,
        "maximum_nested_time_match_error_s": 0.0,
        "fatemi_socie_coefficient": 0.3,
        "normalization_stress_Pa": 400e6,
        "declared_maximum_relative_factor_change": 0.1,
        "declared_maximum_plane_rotation_rad": 0.0,
    }
    return base | overrides


def run(context, **overrides):
    return default_registry().run("fatigue.critical_plane_time_refinement", inputs(**overrides), context)


def test_nested_time_refinement_reports_factor_changes(context):
    result = run(context)
    assert result.status == "computed"
    assert result.values["candidate_count"] == 2
    assert result.values["refinement_level_count"] == 3
    assert result.values["evaluated_level_count"] == 3
    assert [row["sample_count"] for row in result.values["levels"]] == [5, 9, 17]
    assert [row["maximum_time_step_s"] for row in result.values["levels"]] == pytest.approx(
        [0.25, 0.125, 0.0625]
    )
    for row in result.values["levels"][1:]:
        transition = row["transition_from_previous"]
        assert transition["maximum_nested_time_match_error_s"] == 0.0
        assert transition["fatemi_socie_plane_rotation_rad"] == 0.0
        assert transition["swt_plane_rotation_rad"] == 0.0
    assert result.values["final_transition_within_declared_tolerances"] is True


def test_each_level_matches_direct_vector_path_evaluation(context):
    payload = inputs()
    result = default_registry().run("fatigue.critical_plane_time_refinement", payload, context)
    registry = default_registry()
    for level, row in zip(payload["sampling_levels"], result.values["levels"], strict=True):
        direct_input = {
            key: payload[key]
            for key in (
                "history_id",
                "material_condition_id",
                "location_id",
                "tensor_source_id",
                "candidate_planes",
                "representative_cycle_declared",
                "maximum_stress_closure_error_Pa",
                "maximum_strain_closure_error",
                "fatemi_socie_coefficient",
                "normalization_stress_Pa",
            )
        }
        direct_input.update(
            sample_ids=level["sample_ids"],
            stress_tensor_components_Pa=level["stress_tensor_components_Pa"],
            strain_tensor_components=level["strain_tensor_components"],
        )
        direct = registry.run("fatigue.critical_plane_vector_path_factors", direct_input, context)
        assert row["maximum_fatemi_socie_factor"] == direct.values["maximum_fatemi_socie_factor"]
        assert row["maximum_swt_factor_Pa"] == direct.values["maximum_swt_factor_Pa"]


@pytest.mark.parametrize(
    "levels",
    [
        [sampling("same", 4), sampling("same", 8)],
        [sampling("fine", 8), sampling("coarse", 4)],
        [sampling("coarse", 4), sampling("not-nested", 6)],
        [
            sampling("coarse", 4),
            sampling("shifted-end", 8)
            | {
                "sample_times_s": [index / 8 for index in range(8)] + [1.01],
            },
        ],
    ],
)
def test_invalid_time_refinement_sequences_are_rejected(context, levels):
    with pytest.raises(ValidationError):
        run(context, sampling_levels=levels)


def test_nonincreasing_time_axis_is_rejected(context):
    bad = sampling("bad", 4)
    bad["sample_times_s"][2] = bad["sample_times_s"][1]
    with pytest.raises(ValidationError):
        run(context, sampling_levels=[bad, sampling("fine", 8)])


def test_open_history_returns_needs_data_without_stability_claim(context):
    result = run(context, representative_cycle_declared=False)
    assert result.status == "needs_data"
    assert result.values["evaluated_level_count"] == 0
    assert result.values["levels"] == []
    assert result.values["final_transition_within_declared_tolerances"] is None
    assert result.values["all_transitions_within_declared_tolerances"] is None

import copy
import json
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

INPUT = json.loads(
    (Path(__file__).resolve().parents[1] / "examples/model_inputs.json").read_text(encoding="utf-8")
)["models"]["structural.profile_capacity_corrosion_scenario"]
CONTEXT = RunContext(
    asset_id="synthetic", location_id="synthetic", time_basis="declared fixed-horizon scenario"
)


def run(inputs):
    return default_registry().run_json(
        "structural.profile_capacity_corrosion_scenario", json.dumps(inputs), CONTEXT
    )


def test_uniform_loss_scenario_reuses_profile_providers_and_reduces_capacity():
    result = run(INPUT)
    assert result.status == "computed"
    assert result.values["forecast_status"] == "computed"
    assert result.values["uniform_metal_loss_m"] == 1e-4
    assert result.values["forecast_minimum_thickness_m"] == 0.0049
    assert (
        result.values["forecast_pressure_difference_capacity_Pa"]
        < result.values["baseline_pressure_difference_capacity_Pa"]
    )
    assert result.values["capacity_change_Pa"] > 0


def test_zero_loss_preserves_baseline_capacity():
    inputs = copy.deepcopy(INPUT)
    inputs["uniform_loss_rate_m_s"] = 0.0
    result = run(inputs)
    assert result.status == "computed"
    assert (
        result.values["forecast_pressure_difference_capacity_Pa"]
        == result.values["baseline_pressure_difference_capacity_Pa"]
    )
    assert result.values["capacity_loss_fraction_of_baseline"] == 0.0


def test_zero_ligament_projection_refuses_pressure_capacity():
    inputs = copy.deepcopy(INPUT)
    inputs["uniform_loss_rate_m_s"] = 1e-8
    result = run(inputs)
    assert result.status == "out_of_scope"
    assert result.values["forecast_pressure_difference_capacity_Pa"] is None
    assert result.values["forecast_minimum_thickness_m"] <= 0


def test_rate_field_scenario_matches_uniform_constant_rate_case():
    rate_field = {
        "scenario_id": "constant-rate-equivalence",
        "profile": INPUT["profile"],
        "time_s": [0.0, 1_000_000.0],
        "corrosion_rate_m_s": [[1e-10, 1e-10] for _ in INPUT["profile"]["axial_position_m"]],
        "forecast_horizon_s": 1_000_000.0,
    }
    result = default_registry().run_json(
        "structural.profile_capacity_rate_field_scenario", json.dumps(rate_field), CONTEXT
    )
    uniform = run(INPUT)
    assert result.status == "computed"
    assert (
        result.values["forecast_pressure_difference_capacity_Pa"]
        == uniform.values["forecast_pressure_difference_capacity_Pa"]
    )
    assert result.values["integrated_metal_loss_by_node_m"] == [1e-4] * 5


def test_rate_field_integrates_piecewise_linear_history_with_partial_final_interval():
    rate_field = {
        "scenario_id": "linear-rate-history",
        "profile": INPUT["profile"],
        "time_s": [0.0, 10.0, 20.0],
        "corrosion_rate_m_s": [[0.0, 2e-9, 4e-9] for _ in INPUT["profile"]["axial_position_m"]],
        "forecast_horizon_s": 15.0,
    }
    result = default_registry().run_json(
        "structural.profile_capacity_rate_field_scenario", json.dumps(rate_field), CONTEXT
    )
    assert result.values["integrated_metal_loss_by_node_m"] == [22.5e-9] * 5


def test_rate_field_support_and_node_alignment_are_required():
    import pytest
    from pydantic import ValidationError

    from matintegrity.registry import default_registry

    invalid = {
        "scenario_id": "unsupported-horizon",
        "profile": INPUT["profile"],
        "time_s": [0.0, 10.0],
        "corrosion_rate_m_s": [[0.0, 0.0] for _ in INPUT["profile"]["axial_position_m"]],
        "forecast_horizon_s": 11.0,
    }
    with pytest.raises(ValidationError, match="beyond supplied rate-field support"):
        default_registry().run_json(
            "structural.profile_capacity_rate_field_scenario", json.dumps(invalid), CONTEXT
        )
    invalid["forecast_horizon_s"] = 10.0
    invalid["corrosion_rate_m_s"].pop()
    with pytest.raises(ValidationError, match="one rate-field row"):
        default_registry().run_json(
            "structural.profile_capacity_rate_field_scenario", json.dumps(invalid), CONTEXT
        )

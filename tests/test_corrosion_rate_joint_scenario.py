import json

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.models.corrosion import CorrosionRateJointScenario, corrosion_rate_joint_scenario
from matintegrity.registry import default_registry


def _input(**overrides):
    value = {
        "sample": {
            "observations": [
                {
                    "observation_id": "rate-1",
                    "physical_specimen_id": "coupon-1",
                    "material_id": "steel-A",
                    "rate_m_s": 1e-9,
                    "condition_signature": {"temperature_K": 298.15},
                    "condition_group_id": "water-1",
                    "source_group_id": "study-1",
                    "measurement_method": "weight_loss",
                },
                {
                    "observation_id": "rate-2",
                    "physical_specimen_id": "coupon-2",
                    "material_id": "steel-A",
                    "rate_m_s": 1.5e-9,
                    "condition_signature": {"temperature_K": 298.15},
                    "condition_group_id": "water-1",
                    "source_group_id": "study-1",
                    "measurement_method": "weight_loss",
                },
            ]
        },
        "current_thickness_m": 0.01,
        "required_thickness_m": 0.009,
        "horizon_s": 1e7,
        "material_state_compatibility_reviewed": True,
        "material_state_review_id": "review-material",
        "condition_transferability_reviewed": True,
        "condition_transfer_review_id": "review-condition",
        "linear_loss_model_reviewed": True,
        "linear_loss_model_review_id": "review-linear",
        "scenario_rate_m_s": [0.0, 2e-10, 2e-9],
        "scenario_weights": [0.2, 0.3, 0.5],
        "scenario_ids": ["no-loss", "moderate", "high"],
        "scenario_set_id": "caller-rate-ensemble-1",
        "scenario_source_digest": "a" * 64,
        "weight_meaning": "caller_declared_scenario_weight",
    }
    value.update(overrides)
    return value


def test_joint_scenario_propagates_rates_and_retains_caller_weight_meaning():
    data = CorrosionRateJointScenario.model_validate(_input())
    result = corrosion_rate_joint_scenario(data)
    assert result.values["scenario_rate_mean_m_s"] == pytest.approx(1.06e-9)
    assert result.values["scenario_remaining_thickness_m"] == pytest.approx([0.01, 0.008, 0.0])
    assert result.values["scenario_threshold_crossed_by_horizon"] == [False, True, True]
    assert result.values["weighted_threshold_crossing_mass"] == pytest.approx(0.8)
    assert result.values["weighted_wall_exhaustion_mass"] == pytest.approx(0.5)
    assert result.status == "out_of_scope"
    assert "not automatically probabilities" in result.notes[1]


def test_joint_scenario_requires_complete_normalized_weighted_scenarios_and_review():
    with pytest.raises(ValidationError, match="sum to one"):
        CorrosionRateJointScenario.model_validate(_input(scenario_weights=[0.2, 0.3, 0.4]))
    with pytest.raises(ValidationError, match="equal lengths"):
        CorrosionRateJointScenario.model_validate(_input(scenario_ids=["one"]))
    with pytest.raises(ValidationError, match="reviews are required"):
        CorrosionRateJointScenario.model_validate(_input(linear_loss_model_reviewed=False))


def test_joint_scenario_is_available_through_registry_json_contract():
    result = default_registry().run_json(
        "corrosion.rate_joint_scenario",
        json.dumps(_input()),
        RunContext(asset_id="asset-1", location_id="wall-1", time_basis="synthetic horizon"),
    )
    assert result.values["scenario_set_id"] == "caller-rate-ensemble-1"
    assert result.values["sample_physical_specimen_ids"] == ["coupon-1", "coupon-2"]

from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity import evaluate
from matintegrity.contracts import RunContext
from matintegrity.models.inspection import (
    InspectionPolicyPath,
    MultiPeriodInspectionPolicyEvaluation,
)

CONTEXT = RunContext(asset_id="asset-1", location_id="cml-7", time_basis="elapsed seconds")


def cost(component_id, amount, factor):
    return {
        "component_id": component_id,
        "category": "policy action",
        "amount_at_stage_time": amount,
        "present_value_factor": factor,
        "basis": "reviewed synthetic present-value factor",
    }


def stage(stage_id, time_s, action_id, costs):
    return {
        "stage_id": stage_id,
        "stage_time_s": time_s,
        "observed_state_id": f"state-before-{stage_id}",
        "action_id": action_id,
        "action_definition": f"reviewed {action_id} action",
        "action_model_id": f"user.{action_id}",
        "action_model_revision": "1",
        "action_model_configuration_sha256": stage_id[0] * 64,
        "action_model_input_sha256": stage_id[-1] * 64,
        "cost_components": costs,
    }


def policy_input():
    return {
        "evaluation_id": "policy-evaluation-1",
        "policy_id": "inspect-monitor-repair-policy",
        "policy_revision": "1",
        "policy_definition": "reviewed finite policy with inspection, monitoring and repair actions",
        "policy_configuration_sha256": "a" * 64,
        "path_generator_id": "user.policy-path-generator",
        "path_generator_revision": "2",
        "path_generator_configuration_sha256": "b" * 64,
        "path_manifest_sha256": "c" * 64,
        "asset_id": "asset-1",
        "location_id": "cml-7",
        "physical_scope_id": "circuit-1/cml-7",
        "event_id": "top-event",
        "event_definition": "first loss of the reviewed integrity function",
        "horizon_start_s": 1000.0,
        "horizon_end_s": 2000.0,
        "conditioning": "integrity function survived through t=1000 s",
        "event_probability_meaning": "conditional_first_failure_in_period",
        "cost_basis_id": "normalized-cost-v1",
        "currency_or_normalized_unit": "normalized_cost_unit",
        "discount_basis_id": "reviewed-present-value-factors-v1",
        "failure_consequence_components": [
            {
                "component_id": "failure",
                "category": "failure consequence",
                "amount": 1000.0,
                "basis": "reviewed synthetic value at event time",
            }
        ],
        "paths": [
            {
                "path_id": "clear-monitor",
                "path_probability_given_start_survival": 0.5,
                "path_source_sha256": "d" * 64,
                "stages": [
                    stage("d1", 1100.0, "inspect", [cost("inspect", 100.0, 1.0)]),
                    stage("d2", 1600.0, "monitor", [cost("monitor", 50.0, 0.9)]),
                ],
                "first_failure_occurred": False,
                "first_failure_time_s": None,
                "failure_consequence_present_value_factor": None,
            },
            {
                "path_id": "indication-repair",
                "path_probability_given_start_survival": 0.3,
                "path_source_sha256": "e" * 64,
                "stages": [
                    stage("e1", 1100.0, "inspect", [cost("inspect", 100.0, 1.0)]),
                    stage("e2", 1300.0, "repair", [cost("repair", 400.0, 0.95)]),
                ],
                "first_failure_occurred": False,
                "first_failure_time_s": None,
                "failure_consequence_present_value_factor": None,
            },
            {
                "path_id": "failure-after-inspection",
                "path_probability_given_start_survival": 0.2,
                "path_source_sha256": "f" * 64,
                "stages": [stage("f1", 1100.0, "inspect", [cost("inspect", 100.0, 1.0)])],
                "first_failure_occurred": True,
                "first_failure_time_s": 1500.0,
                "failure_consequence_present_value_factor": 0.8,
            },
        ],
        "maximum_path_probability_sum_error": 1e-12,
        "complete_path_manifest_reviewed": True,
        "path_probabilities_reviewed": True,
        "policy_actions_reviewed": True,
        "first_failure_events_reviewed": True,
        "costs_and_discount_factors_reviewed": True,
        "evidence": [
            {
                "source_id": "authored-policy-test",
                "origin": "synthetic",
                "citation": "independently authored finite path ensemble",
            }
        ],
    }


def run(payload=None):
    return evaluate(
        "inspection.multi_period_policy_evaluation",
        policy_input() if payload is None else payload,
        CONTEXT,
    )


def test_policy_evaluates_discounted_path_expectations_without_optimization():
    result = run()
    assert result.status == "computed"
    assert result.values["path_probability_sum"] == pytest.approx(1.0)
    assert result.values["conditional_first_failure_probability"] == pytest.approx(0.2)
    assert result.values["expected_discounted_action_cost"] == pytest.approx(236.5)
    assert result.values["expected_discounted_failure_consequence"] == pytest.approx(160.0)
    assert result.values["expected_discounted_total_loss"] == pytest.approx(396.5)
    assert result.values["path_results"][0]["discounted_action_cost_if_path"] == 145.0
    assert result.values["path_results"][2]["discounted_failure_consequence_if_path"] == 800.0
    assert result.values["path_probabilities_or_policy_inferred"] is False
    assert result.values["policy_optimization_performed"] is False
    assert result.values["upper_bound_computed"] is False
    assert (
        result.probability_semantics["conditional_first_failure_probability"]
        == "conditional_first_failure_in_period"
    )


def test_review_gate_withholds_all_path_arithmetic():
    payload = policy_input()
    payload["complete_path_manifest_reviewed"] = False
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["policy_evaluation_state"] == "review_required"
    assert "path_results" not in result.values


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda value: value["paths"][0].update(path_probability_given_start_survival=0.4),
            "sum to one",
        ),
        (lambda value: value["paths"][1].update(path_id="clear-monitor"), "path IDs must be unique"),
        (
            lambda value: value["paths"][0]["stages"][1].update(stage_time_s=1100.0),
            "strictly increase",
        ),
        (
            lambda value: value["paths"][0]["stages"][0].update(stage_time_s=900.0),
            "inside the policy horizon",
        ),
        (
            lambda value: value["paths"][2]["stages"][0].update(stage_time_s=1600.0),
            "after its first failure",
        ),
        (lambda value: value.update(horizon_end_s=1000.0), "positive duration"),
    ],
)
def test_invalid_path_ensemble_is_rejected(mutate, message):
    payload = policy_input()
    mutate(payload)
    with pytest.raises(ValidationError, match=message):
        MultiPeriodInspectionPolicyEvaluation.model_validate(payload)


def test_failure_fields_are_present_exactly_on_failure_paths():
    payload = policy_input()["paths"][2]
    payload["failure_consequence_present_value_factor"] = None
    with pytest.raises(ValidationError, match="required exactly"):
        InspectionPolicyPath.model_validate(payload)

    payload = policy_input()["paths"][0]
    payload["first_failure_time_s"] = 1500.0
    payload["failure_consequence_present_value_factor"] = 0.8
    with pytest.raises(ValidationError, match="required exactly"):
        InspectionPolicyPath.model_validate(payload)


def test_context_and_input_immutability():
    payload = policy_input()
    original = deepcopy(payload)
    run(payload)
    assert payload == original
    wrong = RunContext(asset_id="asset-2", location_id="cml-7", time_basis="elapsed seconds")
    with pytest.raises(ValueError, match="run context"):
        evaluate("inspection.multi_period_policy_evaluation", payload, wrong)

from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity import evaluate
from matintegrity.adapters import multi_period_policy_evaluation_inputs_from_generated_paths
from matintegrity.contracts import RunContext
from matintegrity.models.inspection import FiniteInspectionPolicyPathGeneration

CONTEXT = RunContext(asset_id="asset-1", location_id="cml-7", time_basis="elapsed seconds")


def cost(component_id, amount, factor=1.0):
    return {
        "component_id": component_id,
        "category": "policy action",
        "amount_at_stage_time": amount,
        "present_value_factor": factor,
        "basis": "reviewed synthetic present-value factor",
    }


def epoch(stage_id, stage_time_s, failure_factor):
    digit = "1" if stage_id == "epoch-1" else "2"
    return {
        "stage_id": stage_id,
        "stage_time_s": stage_time_s,
        "observation_probabilities": [
            {"state_id": "healthy", "observation_id": "clear", "probability_given_state": 0.9},
            {"state_id": "healthy", "observation_id": "alert", "probability_given_state": 0.1},
            {"state_id": "degraded", "observation_id": "clear", "probability_given_state": 0.2},
            {"state_id": "degraded", "observation_id": "alert", "probability_given_state": 0.8},
        ],
        "decision_rules": [
            {"observation_id": "clear", "action_id": "monitor"},
            {"observation_id": "alert", "action_id": "repair"},
        ],
        "actions": [
            {
                "action_id": "monitor",
                "action_definition": "reviewed monitoring action",
                "action_model_id": "synthetic.monitor",
                "action_model_revision": "1",
                "action_model_configuration_sha256": digit * 64,
                "action_model_input_sha256": "3" * 64,
                "cost_components": [cost("monitor", 10.0)],
            },
            {
                "action_id": "repair",
                "action_definition": "reviewed repair action",
                "action_model_id": "synthetic.repair",
                "action_model_revision": "1",
                "action_model_configuration_sha256": "4" * 64,
                "action_model_input_sha256": "5" * 64,
                "cost_components": [cost("repair", 50.0)],
            },
        ],
        "transition_probabilities": [
            {
                "from_state_id": "healthy",
                "action_id": "monitor",
                "to_state_id": "healthy",
                "probability_given_state_and_action": 0.95,
                "failure_consequence_present_value_factor": None,
            },
            {
                "from_state_id": "healthy",
                "action_id": "monitor",
                "to_state_id": "failure",
                "probability_given_state_and_action": 0.05,
                "failure_consequence_present_value_factor": failure_factor,
            },
            {
                "from_state_id": "healthy",
                "action_id": "repair",
                "to_state_id": "healthy",
                "probability_given_state_and_action": 1.0,
                "failure_consequence_present_value_factor": None,
            },
            {
                "from_state_id": "degraded",
                "action_id": "monitor",
                "to_state_id": "degraded",
                "probability_given_state_and_action": 0.7,
                "failure_consequence_present_value_factor": None,
            },
            {
                "from_state_id": "degraded",
                "action_id": "monitor",
                "to_state_id": "failure",
                "probability_given_state_and_action": 0.3,
                "failure_consequence_present_value_factor": failure_factor,
            },
            {
                "from_state_id": "degraded",
                "action_id": "repair",
                "to_state_id": "healthy",
                "probability_given_state_and_action": 0.9,
                "failure_consequence_present_value_factor": None,
            },
            {
                "from_state_id": "degraded",
                "action_id": "repair",
                "to_state_id": "failure",
                "probability_given_state_and_action": 0.1,
                "failure_consequence_present_value_factor": failure_factor,
            },
        ],
    }


def generation_input():
    return {
        "generation_id": "finite-policy-generation-1",
        "generator_configuration_sha256": "a" * 64,
        "policy_id": "monitor-repair-policy",
        "policy_revision": "1",
        "policy_definition": "clear observations trigger monitoring and alerts trigger repair",
        "policy_configuration_sha256": "b" * 64,
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
        "states": [
            {"state_id": "healthy", "state_definition": "reviewed healthy state", "is_failure_state": False},
            {
                "state_id": "degraded",
                "state_definition": "reviewed degraded state",
                "is_failure_state": False,
            },
            {
                "state_id": "failure",
                "state_definition": "reviewed first-failure state",
                "is_failure_state": True,
            },
        ],
        "initial_state_probabilities": [
            {"state_id": "healthy", "probability_given_start_survival": 0.8},
            {"state_id": "degraded", "probability_given_start_survival": 0.2},
        ],
        "decision_epochs": [epoch("epoch-1", 1200.0, 0.9), epoch("epoch-2", 1700.0, 0.8)],
        "maximum_probability_sum_error": 1e-12,
        "maximum_generated_paths": 50,
        "state_space_reviewed": True,
        "initial_distribution_reviewed": True,
        "observation_models_reviewed": True,
        "decision_rules_reviewed": True,
        "transition_models_reviewed": True,
        "action_costs_and_discount_factors_reviewed": True,
        "evidence": [
            {
                "source_id": "authored-finite-policy-test",
                "origin": "synthetic",
                "citation": "independently authored finite probability tables",
            }
        ],
    }


def run(payload=None):
    return evaluate(
        "inspection.finite_policy_path_generation",
        generation_input() if payload is None else payload,
        CONTEXT,
    )


def test_exact_path_generation_preserves_probability_and_stops_at_failure():
    result = run()
    assert result.status == "computed"
    assert result.values["generated_path_count"] == 16
    assert result.values["path_probability_sum"] == pytest.approx(1.0)
    assert result.values["observation_transition_or_policy_inferred"] is False
    failure_paths = [row for row in result.values["paths"] if row["first_failure_occurred"]]
    assert sum(row["path_probability_given_start_survival"] for row in failure_paths) == pytest.approx(
        0.10878
    )
    for path in failure_paths:
        assert path["stages"][-1]["stage_time_s"] == path["first_failure_time_s"]
        assert all(stage["stage_time_s"] <= path["first_failure_time_s"] for stage in path["stages"])


def test_generated_paths_feed_existing_policy_evaluation_end_to_end():
    generated = run()
    payload = multi_period_policy_evaluation_inputs_from_generated_paths(
        generated,
        evaluation_id="evaluation-from-generated-paths",
        failure_consequence_components=[
            {
                "component_id": "failure",
                "category": "failure consequence",
                "amount": 1000.0,
                "basis": "reviewed synthetic event-time value",
            }
        ],
        complete_path_manifest_reviewed=True,
        path_probabilities_reviewed=True,
        policy_actions_reviewed=True,
        first_failure_events_reviewed=True,
        costs_and_discount_factors_reviewed=True,
        evidence=[
            {
                "source_id": "authored-generated-evaluation",
                "origin": "synthetic",
                "citation": "independently authored end-to-end test",
            }
        ],
    )
    evaluated = evaluate("inspection.multi_period_policy_evaluation", payload, CONTEXT)
    assert evaluated.status == "computed"
    assert evaluated.values["conditional_first_failure_probability"] == pytest.approx(0.10878)
    assert evaluated.values["expected_discounted_action_cost"] == pytest.approx(33.488)
    assert evaluated.values["expected_discounted_failure_consequence"] == pytest.approx(93.424)
    assert evaluated.values["expected_discounted_total_loss"] == pytest.approx(126.912)
    assert payload["path_manifest_sha256"] == generated.values["path_manifest_sha256"]


def test_review_gate_and_path_limit_are_explicit():
    payload = generation_input()
    payload["transition_models_reviewed"] = False
    assert run(payload).status == "needs_data"

    payload = generation_input()
    payload["maximum_generated_paths"] = 6
    result = run(payload)
    assert result.status == "out_of_scope"
    assert result.values["path_generation_state"] == "path_limit_exceeded"
    assert result.values["decision_epoch_id"] == "epoch-1"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda value: value["initial_state_probabilities"][0].update(
                probability_given_start_survival=0.7
            ),
            "must sum to one",
        ),
        (
            lambda value: value["decision_epochs"][0]["observation_probabilities"][0].update(
                probability_given_state=0.8
            ),
            "observation probabilities must sum to one",
        ),
        (
            lambda value: value["decision_epochs"][0]["decision_rules"].pop(),
            "cover every observation exactly",
        ),
        (
            lambda value: value["decision_epochs"][0]["transition_probabilities"].pop(),
            "transition probabilities must sum to one",
        ),
        (
            lambda value: value["decision_epochs"][0]["transition_probabilities"][0].update(
                failure_consequence_present_value_factor=0.9
            ),
            "required exactly on transitions to failure",
        ),
        (
            lambda value: value["decision_epochs"][1].update(stage_time_s=1200.0),
            "strictly increase",
        ),
    ],
)
def test_invalid_probability_tables_are_rejected(mutate, message):
    payload = generation_input()
    mutate(payload)
    with pytest.raises(ValidationError, match=message):
        FiniteInspectionPolicyPathGeneration.model_validate(payload)


def test_adapter_rejects_incomplete_generation_and_inputs_are_immutable():
    payload = generation_input()
    original = deepcopy(payload)
    generated = run(payload)
    assert payload == original
    incomplete = generated.model_copy(update={"status": "needs_data"})
    with pytest.raises(ValueError, match="noncomputed"):
        multi_period_policy_evaluation_inputs_from_generated_paths(
            incomplete,
            evaluation_id="invalid",
            failure_consequence_components=[],
            complete_path_manifest_reviewed=True,
            path_probabilities_reviewed=True,
            policy_actions_reviewed=True,
            first_failure_events_reviewed=True,
            costs_and_discount_factors_reviewed=True,
            evidence=[],
        )


def test_context_must_match():
    wrong = RunContext(asset_id="asset-2", location_id="cml-7", time_basis="elapsed seconds")
    with pytest.raises(ValueError, match="run context"):
        evaluate("inspection.finite_policy_path_generation", generation_input(), wrong)

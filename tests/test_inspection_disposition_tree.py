from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity import evaluate
from matintegrity.adapters import inspection_action_candidate_from_disposition_tree_result
from matintegrity.contracts import RunContext
from matintegrity.models.inspection import InspectionDispositionDecisionTree

CONTEXT = RunContext(asset_id="asset-1", location_id="cml-7", time_basis="elapsed seconds")


def branch(outcome_id, probability, disposition_id, residual_probability, cost, token):
    return {
        "outcome_id": outcome_id,
        "outcome_label": outcome_id,
        "probability_given_inspection": probability,
        "disposition_id": disposition_id,
        "disposition_label": disposition_id,
        "disposition_definition": f"reviewed {disposition_id} disposition",
        "disposition_effect_model_id": f"user.{disposition_id}",
        "disposition_effect_model_revision": "1",
        "disposition_effect_configuration_sha256": token * 64,
        "disposition_effect_input_sha256": token.upper() * 64,
        "disposition_event_result_sha256": str(int(token) + 3) * 64,
        "residual_failure_probability_given_outcome_and_disposition": residual_probability,
        "disposition_cost_components": []
        if cost == 0.0
        else [
            {
                "component_id": f"{outcome_id}-cost",
                "category": "disposition",
                "amount": cost,
                "basis": "reviewed synthetic value",
            }
        ],
    }


def tree_input():
    return {
        "tree_id": "inspection-tree-1",
        "asset_id": "asset-1",
        "location_id": "cml-7",
        "physical_scope_id": "circuit-1/cml-7",
        "event_id": "top-event",
        "event_definition": "first loss of the reviewed integrity function",
        "horizon_start_s": 1000.0,
        "horizon_end_s": 2000.0,
        "conditioning": "integrity function survived through t=1000 s",
        "event_probability_meaning": "conditional_first_failure_in_period",
        "inspection_action_id": "inspect-and-dispose",
        "inspection_action_label": "inspect and apply disposition table",
        "inspection_action_definition": "one inspection followed by the reviewed branch disposition",
        "inspection_outcome_model_id": "user.inspection-outcomes",
        "inspection_outcome_model_revision": "2",
        "inspection_outcome_configuration_sha256": "a" * 64,
        "inspection_outcome_input_sha256": "b" * 64,
        "risk_model_structure_id": "top-event-with-inspection-v2",
        "common_cause_group_ids": ["shared-environment"],
        "cost_basis_id": "normalized-cost-v1",
        "currency_or_normalized_unit": "normalized_cost_unit",
        "inspection_cost_components": [
            {
                "component_id": "inspection-cost",
                "category": "inspection",
                "amount": 50.0,
                "basis": "reviewed synthetic value",
            }
        ],
        "outcome_branches": [
            branch("clear", 0.7, "continue", 0.10, 0.0, "1"),
            branch("indication", 0.2, "repair", 0.01, 400.0, "2"),
            branch("inconclusive", 0.1, "monitor", 0.05, 100.0, "3"),
        ],
        "maximum_outcome_probability_sum_error": 1e-12,
        "outcome_partition_reviewed": True,
        "outcome_probabilities_reviewed": True,
        "disposition_definitions_reviewed": True,
        "disposition_effects_reviewed": True,
        "costs_reviewed": True,
        "evidence": [
            {
                "source_id": "authored-disposition-tree-test",
                "origin": "synthetic",
                "citation": "independently authored finite tree",
            }
        ],
    }


def run(payload=None):
    return evaluate(
        "inspection.disposition_decision_tree",
        tree_input() if payload is None else payload,
        CONTEXT,
    )


def test_tree_computes_finite_expectations_and_branch_contributions():
    result = run()
    assert result.status == "computed"
    assert result.values["outcome_probability_sum"] == pytest.approx(1.0)
    assert result.values["inspection_cost"] == 50.0
    assert result.values["expected_disposition_cost"] == pytest.approx(90.0)
    assert result.values["expected_total_action_cost"] == pytest.approx(140.0)
    assert result.values["residual_failure_probability_estimate"] == pytest.approx(0.077)
    assert result.values["branch_results"][1]["expected_disposition_cost_contribution"] == 80.0
    assert result.values["branch_results"][2]["residual_failure_probability_contribution"] == pytest.approx(
        0.005
    )
    assert result.values["upper_bound_computed"] is False
    assert result.values["pod_or_false_call_inferred"] is False
    assert (
        result.probability_semantics["residual_failure_probability_estimate"]
        == "conditional_first_failure_in_period"
    )


def test_tree_candidate_composes_with_expected_loss_comparison():
    result = run()
    candidate = inspection_action_candidate_from_disposition_tree_result(result)
    assert candidate["action_id"] == "inspect-and-dispose"
    assert candidate["residual_failure_probability_estimate"] == pytest.approx(0.077)
    assert sum(row["amount"] for row in candidate["action_cost_components"]) == pytest.approx(140.0)
    assert candidate["event_probability_result_sha256"]
    baseline = {
        "action_id": "continue",
        "action_label": "continue",
        "candidate_kind": "baseline",
        "action_definition": "no action",
        "action_effect_model_id": "user.baseline",
        "action_effect_model_revision": "1",
        "action_effect_input_sha256": "c" * 64,
        "action_effect_configuration_sha256": "d" * 64,
        "risk_model_structure_id": "top-event-baseline",
        "event_probability_result_sha256": "e" * 64,
        "common_cause_group_ids": ["shared-environment"],
        "residual_failure_probability_estimate": 0.10,
        "residual_failure_probability_upper_bound": None,
        "action_cost_components": [],
    }
    payload = {
        "comparison_id": "comparison-with-tree",
        "asset_id": "asset-1",
        "location_id": "cml-7",
        "physical_scope_id": "circuit-1/cml-7",
        "event_id": "top-event",
        "event_definition": "first loss of the reviewed integrity function",
        "horizon_start_s": 1000.0,
        "horizon_end_s": 2000.0,
        "conditioning": "integrity function survived through t=1000 s",
        "event_probability_meaning": "conditional_first_failure_in_period",
        "probability_basis": "estimate",
        "cost_basis_id": "normalized-cost-v1",
        "currency_or_normalized_unit": "normalized_cost_unit",
        "failure_consequence_components": [
            {
                "component_id": "failure",
                "category": "failure",
                "amount": 10000.0,
                "basis": "reviewed synthetic value",
            }
        ],
        "candidates": [baseline, candidate],
        "cost_tie_absolute_tolerance": 0.0,
        "action_definitions_reviewed": True,
        "residual_probabilities_reviewed": True,
        "costs_and_consequences_reviewed": True,
        "decision_criterion_user_approved": True,
        "evidence": tree_input()["evidence"],
    }
    comparison = evaluate("inspection.action_expected_loss", payload, CONTEXT)
    assert comparison.values["selected_action_id"] == "inspect-and-dispose"
    assert comparison.values["minimum_total_expected_loss"] == pytest.approx(910.0)


def test_missing_review_gate_withholds_tree_arithmetic():
    payload = tree_input()
    payload["disposition_effects_reviewed"] = False
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["tree_state"] == "review_required"
    assert "branch_results" not in result.values


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda value: value["outcome_branches"][0].update(probability_given_inspection=0.6),
            "sum to one",
        ),
        (
            lambda value: value["outcome_branches"][1].update(outcome_id="clear"),
            "outcome IDs must be unique",
        ),
        (lambda value: value.update(horizon_end_s=1000.0), "positive duration"),
        (
            lambda value: value.update(common_cause_group_ids=["x", "x"]),
            "common-cause group IDs must be unique",
        ),
    ],
)
def test_invalid_tree_structure_is_rejected(mutate, message):
    payload = tree_input()
    mutate(payload)
    with pytest.raises(ValidationError, match=message):
        InspectionDispositionDecisionTree.model_validate(payload)


def test_candidate_adapter_rejects_wrong_or_incomplete_result_and_reserved_collision():
    wrong = evaluate(
        "inspection.ultrasonic_thickness",
        {
            "round_trip_time_s": 1e-6,
            "sound_speed_m_s": 5000.0,
            "time_zero_offset_s": 0.0,
            "incidence_angle_rad": 0.0,
        },
        CONTEXT,
    )
    with pytest.raises(ValueError, match="only an inspection disposition-tree"):
        inspection_action_candidate_from_disposition_tree_result(wrong)

    payload = tree_input()
    payload["costs_reviewed"] = False
    with pytest.raises(ValueError, match="noncomputed"):
        inspection_action_candidate_from_disposition_tree_result(run(payload))

    payload = tree_input()
    payload["inspection_cost_components"][0]["component_id"] = "inspection-tree-1:expected-disposition-cost"
    with pytest.raises(ValueError, match="reserved"):
        inspection_action_candidate_from_disposition_tree_result(run(payload))


def test_context_and_input_immutability():
    payload = tree_input()
    original = deepcopy(payload)
    run(payload)
    assert payload == original
    wrong = RunContext(asset_id="asset-2", location_id="cml-7", time_basis="elapsed seconds")
    with pytest.raises(ValueError, match="run context"):
        evaluate("inspection.disposition_decision_tree", payload, wrong)

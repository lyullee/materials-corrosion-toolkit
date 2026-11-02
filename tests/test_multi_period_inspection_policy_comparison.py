from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity import evaluate
from matintegrity.adapters import inspection_policy_candidate_from_evaluation_result
from matintegrity.contracts import AssessmentResult, RunContext
from matintegrity.models.inspection import MultiPeriodInspectionPolicyComparison

CONTEXT = RunContext(asset_id="asset-1", location_id="cml-7", time_basis="elapsed seconds")


def candidate(policy_id, probability, total, outage, *, probability_bound=None, outage_bound=None):
    action = total * 0.6
    failure = total - action
    return {
        "policy_id": policy_id,
        "policy_revision": "1",
        "policy_definition": f"reviewed {policy_id}",
        "policy_configuration_sha256": policy_id[0] * 64,
        "evaluation_model_id": "inspection.multi_period_policy_evaluation",
        "evaluation_model_revision": "0.1.0",
        "evaluation_configuration_sha256": policy_id[-1] * 64,
        "evaluation_input_sha256": "a" * 64,
        "evaluation_result_sha256": "b" * 64,
        "asset_id": "asset-1",
        "location_id": "cml-7",
        "physical_scope_id": "circuit-1/cml-7",
        "event_id": "top-event",
        "horizon_start_s": 1000.0,
        "horizon_end_s": 2000.0,
        "conditioning": "integrity function survived through t=1000 s",
        "event_probability_meaning": "conditional_first_failure_in_period",
        "cost_basis_id": "normalized-cost-v1",
        "currency_or_normalized_unit": "normalized_cost_unit",
        "discount_basis_id": "reviewed-present-value-factors-v1",
        "conditional_first_failure_probability": probability,
        "conditional_first_failure_probability_upper_bound": probability_bound,
        "expected_discounted_action_cost": action,
        "expected_discounted_failure_consequence": failure,
        "expected_discounted_total_loss": total,
        "resource_usage": [
            {
                "resource_id": "outage-days",
                "unit": "day",
                "expected_usage": outage,
                "upper_bound_usage": outage_bound,
            }
        ],
    }


def comparison_input():
    return {
        "comparison_id": "policy-comparison-1",
        "asset_id": "asset-1",
        "location_id": "cml-7",
        "physical_scope_id": "circuit-1/cml-7",
        "event_id": "top-event",
        "horizon_start_s": 1000.0,
        "horizon_end_s": 2000.0,
        "conditioning": "integrity function survived through t=1000 s",
        "event_probability_meaning": "conditional_first_failure_in_period",
        "cost_basis_id": "normalized-cost-v1",
        "currency_or_normalized_unit": "normalized_cost_unit",
        "discount_basis_id": "reviewed-present-value-factors-v1",
        "probability_basis": "estimate",
        "maximum_conditional_first_failure_probability": 0.15,
        "resource_constraints": [
            {
                "resource_id": "outage-days",
                "unit": "day",
                "comparison_basis": "expected",
                "maximum_usage": 8.0,
                "criterion_basis": "reviewed synthetic outage constraint",
            }
        ],
        "candidates": [
            candidate("c1", 0.20, 400.0, 10.0, probability_bound=0.25, outage_bound=12.0),
            candidate("d2", 0.08, 450.0, 7.0, probability_bound=0.12, outage_bound=9.0),
            candidate("e3", 0.30, 300.0, 4.0, probability_bound=0.35, outage_bound=5.0),
        ],
        "cost_tie_absolute_tolerance": 0.0,
        "complete_policy_set_reviewed": True,
        "policy_evaluations_reviewed": True,
        "probability_criterion_user_approved": True,
        "resource_constraints_user_approved": True,
        "cost_comparison_user_approved": True,
        "evidence": [
            {
                "source_id": "authored-policy-comparison-test",
                "origin": "synthetic",
                "citation": "independently authored constrained finite comparison",
            }
        ],
    }


def run(payload=None):
    return evaluate(
        "inspection.multi_period_policy_comparison",
        comparison_input() if payload is None else payload,
        CONTEXT,
    )


def test_hard_constraints_precede_finite_expected_loss_comparison():
    result = run()
    assert result.status == "computed"
    assert result.values["feasible_policy_count"] == 1
    assert result.values["selected_policy_id"] == "d2"
    assert result.values["minimum_constraint_compliant_expected_loss"] == 450.0
    assert result.values["candidate_results"][0]["violated_constraints"] == [
        "conditional_first_failure_probability",
        "resource:outage-days",
    ]
    assert result.values["candidate_results"][2]["expected_discounted_total_loss"] == 300.0
    assert result.values["policy_search_or_generation_performed"] is False
    assert result.values["global_optimality_claimed"] is False


def test_review_gate_withholds_comparison():
    payload = comparison_input()
    payload["probability_criterion_user_approved"] = False
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["comparison_state"] == "review_required"
    assert "candidate_results" not in result.values


def test_no_constraint_compliant_policy_does_not_relax_constraints():
    payload = comparison_input()
    payload["maximum_conditional_first_failure_probability"] = 0.05
    result = run(payload)
    assert result.status == "out_of_scope"
    assert result.values["comparison_state"] == "no_constraint_compliant_policy"
    assert result.values["selected_policy_id"] is None


def test_cost_tie_is_not_broken_arbitrarily():
    payload = comparison_input()
    payload["candidates"][0]["conditional_first_failure_probability"] = 0.1
    payload["candidates"][0]["resource_usage"][0]["expected_usage"] = 6.0
    payload["candidates"][0]["expected_discounted_action_cost"] = 270.0
    payload["candidates"][0]["expected_discounted_failure_consequence"] = 180.0
    payload["candidates"][0]["expected_discounted_total_loss"] = 450.0
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["comparison_state"] == "minimum_tie"
    assert result.values["tied_minimum_policy_ids"] == ["c1", "d2"]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value["candidates"][1].update(policy_id="c1"), "IDs must be unique"),
        (
            lambda value: value["candidates"][1].update(event_id="other-event"),
            "share the comparison context",
        ),
        (
            lambda value: value["candidates"][1].update(resource_usage=[]),
            "exact resource constraint set",
        ),
        (
            lambda value: value["candidates"][1]["resource_usage"][0].update(unit="hour"),
            "units must match",
        ),
        (
            lambda value: (
                value.update(probability_basis="upper_bound")
                or value["candidates"][1].update(conditional_first_failure_probability_upper_bound=None)
            ),
            "requires a bound for every candidate",
        ),
        (
            lambda value: value["candidates"][1].update(expected_discounted_total_loss=451.0),
            "must equal action and failure components",
        ),
    ],
)
def test_invalid_comparisons_are_rejected(mutate, message):
    payload = comparison_input()
    mutate(payload)
    with pytest.raises(ValidationError, match=message):
        MultiPeriodInspectionPolicyComparison.model_validate(payload)


def test_upper_bound_resource_constraint_requires_all_bounds():
    payload = comparison_input()
    payload["resource_constraints"][0]["comparison_basis"] = "upper_bound"
    payload["candidates"][0]["resource_usage"][0]["upper_bound_usage"] = None
    with pytest.raises(ValidationError, match="require a bound for every candidate"):
        MultiPeriodInspectionPolicyComparison.model_validate(payload)


def test_policy_result_adapter_preserves_result_identity_and_rejects_wrong_state():
    result = AssessmentResult(
        model_id="inspection.multi_period_policy_evaluation",
        model_version="0.1.0",
        status="computed",
        inputs={
            "policy_id": "adapted-policy",
            "policy_revision": "1",
            "policy_definition": "reviewed adapted policy",
            "policy_configuration_sha256": "a" * 64,
            "asset_id": "asset-1",
            "location_id": "cml-7",
            "physical_scope_id": "circuit-1/cml-7",
            "event_id": "top-event",
            "horizon_start_s": 1000.0,
            "horizon_end_s": 2000.0,
            "conditioning": "survived to start",
            "event_probability_meaning": "conditional_first_failure_in_period",
            "cost_basis_id": "normalized-cost-v1",
            "currency_or_normalized_unit": "normalized_cost_unit",
            "discount_basis_id": "discount-v1",
        },
        values={
            "policy_evaluation_state": "computed",
            "conditional_first_failure_probability": 0.1,
            "expected_discounted_action_cost": 100.0,
            "expected_discounted_failure_consequence": 50.0,
            "expected_discounted_total_loss": 150.0,
        },
        units={},
        assumptions=(),
        notes=(),
        context=CONTEXT,
        input_digest="c" * 64,
        source_ids=(),
        qualification="engineering_screening",
        runtime={},
    )
    adapted = inspection_policy_candidate_from_evaluation_result(
        result,
        evaluation_configuration_sha256="d" * 64,
        conditional_first_failure_probability_upper_bound=0.15,
        resource_usage=[
            {
                "resource_id": "outage-days",
                "unit": "day",
                "expected_usage": 2.0,
                "upper_bound_usage": 3.0,
            }
        ],
    )
    assert adapted["evaluation_input_sha256"] == "c" * 64
    assert adapted["expected_discounted_total_loss"] == 150.0
    assert adapted["conditional_first_failure_probability_upper_bound"] == 0.15

    invalid = result.model_copy(update={"status": "needs_data"})
    with pytest.raises(ValueError, match="noncomputed"):
        inspection_policy_candidate_from_evaluation_result(
            invalid,
            evaluation_configuration_sha256="d" * 64,
            resource_usage=[],
        )


def test_input_immutability_and_context():
    payload = comparison_input()
    original = deepcopy(payload)
    run(payload)
    assert payload == original
    wrong = RunContext(asset_id="asset-2", location_id="cml-7", time_basis="elapsed seconds")
    with pytest.raises(ValueError, match="run context"):
        evaluate("inspection.multi_period_policy_comparison", payload, wrong)

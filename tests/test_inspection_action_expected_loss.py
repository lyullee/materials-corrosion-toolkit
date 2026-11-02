from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity import evaluate
from matintegrity.contracts import RunContext
from matintegrity.models.inspection import (
    InspectionActionExpectedLossComparison,
)

CONTEXT = RunContext(asset_id="asset-1", location_id="cml-7", time_basis="elapsed seconds")


def comparison_input():
    return {
        "comparison_id": "risk-action-1",
        "asset_id": "asset-1",
        "location_id": "cml-7",
        "physical_scope_id": "pipe-circuit-1/cml-7",
        "event_id": "minimum-thickness-first-crossing",
        "event_definition": "first crossing of the reviewed minimum remaining thickness",
        "horizon_start_s": 1000.0,
        "horizon_end_s": 2000.0,
        "conditioning": "asset survived without the declared crossing through t=1000 s",
        "event_probability_meaning": "conditional_first_failure_in_period",
        "probability_basis": "estimate",
        "cost_basis_id": "reviewed-2026-normalized-costs",
        "currency_or_normalized_unit": "normalized_cost_unit",
        "failure_consequence_components": [
            {
                "component_id": "repair-after-failure",
                "category": "physical repair",
                "amount": 1000.0,
                "basis": "reviewed synthetic test value",
            },
            {
                "component_id": "outage-after-failure",
                "category": "lost operation",
                "amount": 4000.0,
                "basis": "reviewed synthetic test value",
            },
        ],
        "candidates": [
            {
                "action_id": "continue",
                "action_label": "continue without intervention",
                "candidate_kind": "baseline",
                "action_definition": "no action during the common horizon",
                "action_effect_model_id": "user.no-action-forecast",
                "action_effect_model_revision": "1",
                "action_effect_input_sha256": "a" * 64,
                "action_effect_configuration_sha256": "1" * 64,
                "risk_model_structure_id": "top-event-v1",
                "event_probability_result_sha256": "d" * 64,
                "common_cause_group_ids": ["shared-environment"],
                "residual_failure_probability_estimate": 0.10,
                "residual_failure_probability_upper_bound": 0.12,
                "action_cost_components": [],
            },
            {
                "action_id": "inspect",
                "action_label": "inspect and execute the supplied disposition rule",
                "candidate_kind": "intervention",
                "action_definition": "reviewed inspection and disposition action",
                "action_effect_model_id": "user.inspection-decision-tree",
                "action_effect_model_revision": "3",
                "action_effect_input_sha256": "b" * 64,
                "action_effect_configuration_sha256": "2" * 64,
                "risk_model_structure_id": "top-event-v1-inspection",
                "event_probability_result_sha256": "e" * 64,
                "common_cause_group_ids": ["shared-environment"],
                "residual_failure_probability_estimate": 0.04,
                "residual_failure_probability_upper_bound": 0.10,
                "action_cost_components": [
                    {
                        "component_id": "inspection",
                        "category": "inspection",
                        "amount": 100.0,
                        "basis": "reviewed synthetic test value",
                    }
                ],
            },
            {
                "action_id": "repair",
                "action_label": "execute the supplied repair action",
                "candidate_kind": "intervention",
                "action_definition": "reviewed repair action",
                "action_effect_model_id": "user.repair-forecast",
                "action_effect_model_revision": "2",
                "action_effect_input_sha256": "c" * 64,
                "action_effect_configuration_sha256": "3" * 64,
                "risk_model_structure_id": "top-event-v1-repair",
                "event_probability_result_sha256": "f" * 64,
                "common_cause_group_ids": ["shared-environment"],
                "residual_failure_probability_estimate": 0.01,
                "residual_failure_probability_upper_bound": 0.02,
                "action_cost_components": [
                    {
                        "component_id": "repair",
                        "category": "planned repair",
                        "amount": 400.0,
                        "basis": "reviewed synthetic test value",
                    }
                ],
            },
        ],
        "cost_tie_absolute_tolerance": 0.0,
        "action_definitions_reviewed": True,
        "residual_probabilities_reviewed": True,
        "costs_and_consequences_reviewed": True,
        "decision_criterion_user_approved": True,
        "evidence": [
            {
                "source_id": "authored-action-risk-test",
                "origin": "synthetic",
                "citation": "independently authored arithmetic example",
            }
        ],
    }


def run(payload=None):
    return evaluate(
        "inspection.action_expected_loss",
        comparison_input() if payload is None else payload,
        CONTEXT,
    )


def test_estimate_basis_selects_unique_minimum_and_preserves_breakdown():
    result = run()
    assert result.status == "computed"
    assert result.values["failure_consequence_cost"] == 5000.0
    assert result.values["baseline_total_expected_loss"] == 500.0
    assert result.values["selected_action_id"] == "inspect"
    assert result.values["minimum_total_expected_loss"] == 300.0
    inspect = result.values["candidate_results"][1]
    assert inspect["direct_action_cost"] == 100.0
    assert inspect["expected_failure_loss"] == 200.0
    assert inspect["net_expected_benefit_vs_baseline"] == 200.0
    assert result.values["probability_or_action_effect_inferred"] is False
    assert result.values["regulatory_acceptance_inferred"] is False


def test_upper_bound_basis_can_change_selected_action():
    payload = comparison_input()
    payload["probability_basis"] = "upper_bound"
    result = run(payload)
    assert result.values["selected_action_id"] == "repair"
    assert result.values["minimum_total_expected_loss"] == 500.0
    assert result.values["candidate_results"][1]["total_expected_loss"] == 600.0


def test_tie_withholds_arbitrary_selection_but_preserves_rows():
    payload = comparison_input()
    payload["candidates"][1]["action_cost_components"][0]["amount"] = 300.0
    payload["candidates"][2]["action_cost_components"][0]["amount"] = 500.0
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["comparison_state"] == "minimum_tie"
    assert result.values["selected_action_id"] is None
    assert result.values["tied_minimum_action_ids"] == ["continue", "inspect"]
    assert len(result.values["candidate_results"]) == 3


def test_review_gate_withholds_all_loss_arithmetic():
    payload = comparison_input()
    payload["costs_and_consequences_reviewed"] = False
    result = run(payload)
    assert result.status == "needs_data"
    assert result.values["comparison_state"] == "review_required"
    assert "candidate_results" not in result.values


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value.update(horizon_end_s=1000.0), "positive duration"),
        (
            lambda value: value["candidates"][1].update(action_id="continue"),
            "action IDs must be unique",
        ),
        (
            lambda value: value["candidates"][0].update(candidate_kind="intervention"),
            "exactly one baseline",
        ),
        (
            lambda value: value["candidates"][0].update(
                action_cost_components=[{"component_id": "x", "category": "x", "amount": 1.0, "basis": "x"}]
            ),
            "baseline action cost",
        ),
        (
            lambda value: value["candidates"][1].update(residual_failure_probability_upper_bound=0.03),
            "upper bound cannot be below",
        ),
    ],
)
def test_invalid_comparison_contracts_are_rejected(mutate, message):
    payload = comparison_input()
    mutate(payload)
    with pytest.raises(ValidationError, match=message):
        InspectionActionExpectedLossComparison.model_validate(payload)


def test_upper_bound_basis_requires_all_bounds_and_context_matches():
    payload = comparison_input()
    payload["probability_basis"] = "upper_bound"
    payload["candidates"][1]["residual_failure_probability_upper_bound"] = None
    with pytest.raises(ValidationError, match="bound for every"):
        InspectionActionExpectedLossComparison.model_validate(payload)

    wrong = RunContext(asset_id="asset-2", location_id="cml-7", time_basis="elapsed seconds")
    with pytest.raises(ValueError, match="run context"):
        evaluate("inspection.action_expected_loss", comparison_input(), wrong)


def test_input_is_not_mutated_and_digest_is_repeatable():
    payload = comparison_input()
    original = deepcopy(payload)
    first = run(payload)
    second = run(payload)
    assert payload == original
    assert first.values["comparison_input_sha256"] == second.values["comparison_input_sha256"]

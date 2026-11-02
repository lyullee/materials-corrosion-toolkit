from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity import evaluate
from matintegrity.adapters import (
    ActionEventProbabilityEvaluation,
    inspection_action_expected_loss_inputs,
)
from matintegrity.contracts import EventProbability, RunContext

CONTEXT = RunContext(asset_id="asset-1", location_id="cml-7", time_basis="elapsed seconds")


def event(action_id: str, probability: float, **changes):
    payload = {
        "event_id": "top-event",
        "asset_id": "asset-1",
        "physical_scope_id": "circuit-1/cml-7",
        "failure_mode": "first loss of the declared integrity function",
        "horizon_start_s": 1000.0,
        "horizon_end_s": 2000.0,
        "probability_given_survival": probability,
        "conditioning": "integrity function survived through t=1000 s",
        "model_result_digest": {"continue": "a", "inspect": "b", "repair": "c"}[action_id] * 64,
        "common_cause_groups": ("shared-environment",),
    }
    payload.update(changes)
    return EventProbability.model_validate(payload)


def evaluation(action_id: str, kind: str, probability: float, upper: float):
    return ActionEventProbabilityEvaluation(
        action_id=action_id,
        action_label=action_id,
        candidate_kind=kind,
        action_definition=f"reviewed {action_id} action",
        evaluator_id="external.risk-engine",
        evaluator_revision="git-123",
        evaluator_configuration_sha256="1" * 64,
        evaluator_input_sha256={"continue": "4", "inspect": "5", "repair": "6"}[action_id] * 64,
        risk_model_structure_id=f"top-event:{action_id}",
        evaluation_status="computed",
        event_probability=event(action_id, probability),
        probability_upper_bound=upper,
        status_detail="computed without omitted basic events",
    )


def evaluations():
    return [
        evaluation("continue", "baseline", 0.10, 0.12),
        evaluation("inspect", "intervention", 0.04, 0.10),
        evaluation("repair", "intervention", 0.01, 0.02),
    ]


def adapter_arguments():
    return {
        "expected_action_ids": ["continue", "inspect", "repair"],
        "comparison_id": "comparison-1",
        "location_id": "cml-7",
        "event_definition": "first loss of the reviewed integrity function",
        "probability_basis": "estimate",
        "cost_basis_id": "normalized-cost-v1",
        "currency_or_normalized_unit": "normalized_cost_unit",
        "failure_consequence_components": [
            {
                "component_id": "failure",
                "category": "failure consequence",
                "amount": 5000.0,
                "basis": "reviewed synthetic value",
            }
        ],
        "action_cost_components_by_action_id": {
            "continue": [],
            "inspect": [
                {
                    "component_id": "inspection",
                    "category": "inspection",
                    "amount": 100.0,
                    "basis": "reviewed synthetic value",
                }
            ],
            "repair": [
                {
                    "component_id": "repair",
                    "category": "repair",
                    "amount": 400.0,
                    "basis": "reviewed synthetic value",
                }
            ],
        },
        "cost_tie_absolute_tolerance": 0.0,
        "action_definitions_reviewed": True,
        "residual_probabilities_reviewed": True,
        "costs_and_consequences_reviewed": True,
        "decision_criterion_user_approved": True,
        "evidence": [
            {
                "source_id": "authored-action-adapter-test",
                "origin": "synthetic",
                "citation": "independently authored exchange records",
            }
        ],
    }


def adapt(rows=None, arguments=None):
    return inspection_action_expected_loss_inputs(
        evaluations() if rows is None else rows,
        **(adapter_arguments() if arguments is None else arguments),
    )


def test_adapter_restores_declared_order_and_runs_end_to_end():
    payload = adapt(list(reversed(evaluations())))
    assert [row["action_id"] for row in payload["candidates"]] == [
        "continue",
        "inspect",
        "repair",
    ]
    assert payload["candidates"][1]["event_probability_result_sha256"] == "b" * 64
    assert payload["candidates"][1]["risk_model_structure_id"] == "top-event:inspect"
    assert payload["candidates"][1]["common_cause_group_ids"] == ["shared-environment"]
    result = evaluate("inspection.action_expected_loss", payload, CONTEXT)
    assert result.status == "computed"
    assert result.values["selected_action_id"] == "inspect"
    assert result.values["minimum_total_expected_loss"] == 300.0


def test_missing_extra_duplicate_or_incomplete_actions_cannot_be_hidden():
    with pytest.raises(ValueError, match="coverage differs"):
        adapt(evaluations()[:-1])

    arguments = adapter_arguments()
    arguments["action_cost_components_by_action_id"] = {
        **arguments["action_cost_components_by_action_id"],
        "extra": [],
    }
    with pytest.raises(ValueError, match="action cost coverage differs"):
        adapt(arguments=arguments)

    rows = evaluations()
    rows[2] = rows[2].model_copy(update={"action_id": "inspect"})
    with pytest.raises(ValueError, match="IDs must be unique"):
        adapt(rows)

    rows = evaluations()
    rows[1] = ActionEventProbabilityEvaluation(
        **{
            **rows[1].model_dump(mode="json"),
            "evaluation_status": "needs_data",
            "event_probability": None,
            "probability_upper_bound": None,
            "status_detail": "missing action-effect inputs",
        }
    )
    with pytest.raises(ValueError, match=r"incomplete=\['inspect'\]"):
        adapt(rows)


@pytest.mark.parametrize(
    "field",
    [
        "event_id",
        "asset_id",
        "physical_scope_id",
        "failure_mode",
        "horizon_start_s",
        "horizon_end_s",
        "conditioning",
    ],
)
def test_every_event_context_field_must_align(field):
    rows = evaluations()
    event_payload = rows[1].event_probability.model_dump(mode="python")
    event_payload[field] = {
        "event_id": "different-event",
        "asset_id": "different-asset",
        "physical_scope_id": "different-scope",
        "failure_mode": "different-mode",
        "horizon_start_s": 900.0,
        "horizon_end_s": 2100.0,
        "conditioning": "different conditioning",
    }[field]
    rows[1] = rows[1].model_copy(update={"event_probability": EventProbability.model_validate(event_payload)})
    with pytest.raises(ValueError, match=field):
        adapt(rows)


def test_upper_bound_comparison_requires_complete_bounds():
    rows = evaluations()
    rows[1] = rows[1].model_copy(update={"probability_upper_bound": None})
    arguments = adapter_arguments()
    arguments["probability_basis"] = "upper_bound"
    with pytest.raises(ValidationError, match="bound for every"):
        adapt(rows, arguments)


def test_evaluation_contract_rejects_status_probability_conflicts_and_reversed_bound():
    row = evaluations()[0].model_dump(mode="python")
    row["evaluation_status"] = "execution_failed"
    with pytest.raises(ValidationError, match="noncomputed"):
        ActionEventProbabilityEvaluation.model_validate(row)

    row = evaluations()[0].model_dump(mode="python")
    row["probability_upper_bound"] = 0.09
    with pytest.raises(ValidationError, match="cannot be below"):
        ActionEventProbabilityEvaluation.model_validate(row)


def test_adapter_does_not_mutate_external_records_or_costs():
    rows = evaluations()
    arguments = adapter_arguments()
    original_rows = deepcopy(rows)
    original_arguments = deepcopy(arguments)
    adapt(rows, arguments)
    assert rows == original_rows
    assert arguments == original_arguments

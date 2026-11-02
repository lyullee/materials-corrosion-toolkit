"""Verify action expected-loss arithmetic against an independent direct calculation."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.adapters import (
    ActionEventProbabilityEvaluation,
    inspection_action_expected_loss_inputs,
)
from matintegrity.contracts import EventProbability, RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def candidate(action_id: str, kind: str, estimate: float, upper: float, cost: float, token: str):
    return {
        "action_id": action_id,
        "action_label": action_id,
        "candidate_kind": kind,
        "action_definition": f"authored {action_id} alternative",
        "action_effect_model_id": f"authored.{action_id}",
        "action_effect_model_revision": "1",
        "action_effect_input_sha256": token * 64,
        "action_effect_configuration_sha256": hashlib.sha256(
            f"authored-configuration:{action_id}".encode()
        ).hexdigest(),
        "risk_model_structure_id": f"authored-top-event:{action_id}",
        "event_probability_result_sha256": hashlib.sha256(
            f"authored-event-result:{action_id}".encode()
        ).hexdigest(),
        "common_cause_group_ids": ["authored-shared-environment"],
        "residual_failure_probability_estimate": estimate,
        "residual_failure_probability_upper_bound": upper,
        "action_cost_components": []
        if cost == 0.0
        else [
            {
                "component_id": f"{action_id}-cost",
                "category": "authored action cost",
                "amount": cost,
                "basis": "independently authored exact arithmetic",
            }
        ],
    }


def main() -> None:
    consequence = 5000.0
    candidates = [
        candidate("continue", "baseline", 0.10, 0.12, 0.0, "a"),
        candidate("inspect", "intervention", 0.04, 0.10, 100.0, "b"),
        candidate("repair", "intervention", 0.01, 0.02, 400.0, "c"),
    ]
    payload = {
        "comparison_id": "authored-action-risk",
        "asset_id": "authored",
        "location_id": "cml-1",
        "physical_scope_id": "authored-circuit/cml-1",
        "event_id": "authored-first-crossing",
        "event_definition": "first crossing of an authored threshold",
        "horizon_start_s": 0.0,
        "horizon_end_s": 31_557_600.0,
        "conditioning": "authored asset remains above the threshold at horizon start",
        "event_probability_meaning": "conditional_first_failure_in_period",
        "probability_basis": "estimate",
        "cost_basis_id": "authored-normalized-costs",
        "currency_or_normalized_unit": "normalized_cost_unit",
        "failure_consequence_components": [
            {
                "component_id": "failure-consequence",
                "category": "authored consequence",
                "amount": consequence,
                "basis": "independently authored exact arithmetic",
            }
        ],
        "candidates": candidates,
        "cost_tie_absolute_tolerance": 0.0,
        "action_definitions_reviewed": True,
        "residual_probabilities_reviewed": True,
        "costs_and_consequences_reviewed": True,
        "decision_criterion_user_approved": True,
        "evidence": [
            {
                "source_id": "authored-action-risk-validation",
                "origin": "synthetic",
                "citation": "independently authored exact arithmetic",
            }
        ],
    }
    context = RunContext(asset_id="authored", location_id="cml-1", time_basis="elapsed seconds")
    registry = default_registry()
    action_evaluations = [
        ActionEventProbabilityEvaluation(
            action_id=row["action_id"],
            action_label=row["action_label"],
            candidate_kind=row["candidate_kind"],
            action_definition=row["action_definition"],
            evaluator_id=row["action_effect_model_id"],
            evaluator_revision=row["action_effect_model_revision"],
            evaluator_configuration_sha256=row["action_effect_configuration_sha256"],
            evaluator_input_sha256=row["action_effect_input_sha256"],
            risk_model_structure_id=row["risk_model_structure_id"],
            evaluation_status="computed",
            event_probability=EventProbability(
                event_id=payload["event_id"],
                asset_id=payload["asset_id"],
                physical_scope_id=payload["physical_scope_id"],
                failure_mode="first crossing of the authored threshold",
                horizon_start_s=payload["horizon_start_s"],
                horizon_end_s=payload["horizon_end_s"],
                probability_given_survival=row["residual_failure_probability_estimate"],
                conditioning=payload["conditioning"],
                model_result_digest=row["event_probability_result_sha256"],
                common_cause_groups=tuple(row["common_cause_group_ids"]),
            ),
            probability_upper_bound=row["residual_failure_probability_upper_bound"],
            status_detail="independently authored computed exchange row",
        )
        for row in candidates
    ]
    results = {}
    for basis in ("estimate", "upper_bound"):
        adapted_payload = inspection_action_expected_loss_inputs(
            action_evaluations,
            expected_action_ids=[row["action_id"] for row in candidates],
            comparison_id=payload["comparison_id"],
            location_id=payload["location_id"],
            event_definition=payload["event_definition"],
            probability_basis=basis,
            cost_basis_id=payload["cost_basis_id"],
            currency_or_normalized_unit=payload["currency_or_normalized_unit"],
            failure_consequence_components=payload["failure_consequence_components"],
            action_cost_components_by_action_id={
                row["action_id"]: row["action_cost_components"] for row in candidates
            },
            cost_tie_absolute_tolerance=payload["cost_tie_absolute_tolerance"],
            action_definitions_reviewed=payload["action_definitions_reviewed"],
            residual_probabilities_reviewed=payload["residual_probabilities_reviewed"],
            costs_and_consequences_reviewed=payload["costs_and_consequences_reviewed"],
            decision_criterion_user_approved=payload["decision_criterion_user_approved"],
            evidence=payload["evidence"],
        )
        result = registry.run("inspection.action_expected_loss", adapted_payload, context)
        probability_key = (
            "residual_failure_probability_estimate"
            if basis == "estimate"
            else "residual_failure_probability_upper_bound"
        )
        expected = {
            row["action_id"]: row["action_cost_components"][0]["amount"]
            if row["action_cost_components"]
            else 0.0
            for row in candidates
        }
        for row in candidates:
            expected[row["action_id"]] += row[probability_key] * consequence
        actual = {row["action_id"]: row["total_expected_loss"] for row in result.values["candidate_results"]}
        if actual != expected:
            raise AssertionError(f"{basis} expected-loss arithmetic differs: {actual} != {expected}")
        expected_selection = min(expected, key=expected.get)
        if result.values["selected_action_id"] != expected_selection:
            raise AssertionError(f"{basis} action selection differs from direct calculation")
        results[basis] = {
            "expected_total_loss_by_action": expected,
            "actual_total_loss_by_action": actual,
            "selected_action_id": expected_selection,
            "input_digest": result.input_digest,
            "adapter_input_digest": hashlib.sha256(
                json.dumps(adapted_payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        }
    record = {
        "schema_version": "matintegrity.validation.inspection_action_expected_loss.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": (
            "Independently authored exact arithmetic verification only; not calibration of event "
            "probabilities, action effects, consequences, costs or a decision threshold."
        ),
        "model_id": "inspection.action_expected_loss",
        "failure_consequence_cost": consequence,
        "results": results,
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/inspection.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/inspection_action_expected_loss_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

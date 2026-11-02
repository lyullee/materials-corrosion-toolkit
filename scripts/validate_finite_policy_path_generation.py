"""Verify finite observation-action-transition path expansion and evaluation composition."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.adapters import multi_period_policy_evaluation_inputs_from_generated_paths
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    payload = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"][
        "inspection.finite_policy_path_generation"
    ]
    context = RunContext(
        asset_id=payload["asset_id"],
        location_id=payload["location_id"],
        time_basis="elapsed seconds",
    )
    registry = default_registry()
    generated = registry.run("inspection.finite_policy_path_generation", payload, context)
    expected = {
        "generated_path_count": 7,
        "path_probability_sum": 1.0,
        "conditional_first_failure_probability": 0.064,
        "expected_discounted_action_cost": 19.6,
        "expected_discounted_failure_consequence": 57.6,
        "expected_discounted_total_loss": 77.2,
    }
    if generated.values["generated_path_count"] != expected["generated_path_count"]:
        raise AssertionError("finite-policy generated path count differs")
    if abs(generated.values["path_probability_sum"] - 1.0) > 1e-15:
        raise AssertionError("finite-policy generated path mass differs")
    evaluation_payload = multi_period_policy_evaluation_inputs_from_generated_paths(
        generated,
        evaluation_id="synthetic-generated-policy-evaluation",
        failure_consequence_components=[
            {
                "component_id": "failure",
                "category": "failure consequence",
                "amount": 1000.0,
                "basis": "independently authored synthetic event-time value",
            }
        ],
        complete_path_manifest_reviewed=True,
        path_probabilities_reviewed=True,
        policy_actions_reviewed=True,
        first_failure_events_reviewed=True,
        costs_and_discount_factors_reviewed=True,
        evidence=[
            {
                "source_id": "authored-finite-policy-validation",
                "origin": "synthetic",
                "citation": "independently authored direct-sum validation",
            }
        ],
    )
    evaluated = registry.run("inspection.multi_period_policy_evaluation", evaluation_payload, context)
    for key in (
        "conditional_first_failure_probability",
        "expected_discounted_action_cost",
        "expected_discounted_failure_consequence",
        "expected_discounted_total_loss",
    ):
        if abs(evaluated.values[key] - expected[key]) > 1e-12:
            raise AssertionError(f"finite-policy direct calculation differs for {key}")
    record = {
        "schema_version": "matintegrity.validation.finite_policy_path_generation.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": (
            "Independent finite-table expansion and direct-sum verification only; not empirical validation "
            "of states, observations, transitions, actions, probabilities, costs or policy quality."
        ),
        "generation_model_id": generated.model_id,
        "evaluation_model_id": evaluated.model_id,
        "expected": expected,
        "actual": {
            "generated_path_count": generated.values["generated_path_count"],
            "path_probability_sum": generated.values["path_probability_sum"],
            "conditional_first_failure_probability": evaluated.values[
                "conditional_first_failure_probability"
            ],
            "expected_discounted_action_cost": evaluated.values["expected_discounted_action_cost"],
            "expected_discounted_failure_consequence": evaluated.values[
                "expected_discounted_failure_consequence"
            ],
            "expected_discounted_total_loss": evaluated.values["expected_discounted_total_loss"],
        },
        "generation_input_digest": generated.input_digest,
        "path_manifest_sha256": generated.values["path_manifest_sha256"],
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/inspection.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/finite_policy_path_generation_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

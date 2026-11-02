"""Verify a fixed multi-period inspection policy by an independent finite sum."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    payload = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"][
        "inspection.multi_period_policy_evaluation"
    ]
    context = RunContext(
        asset_id=payload["asset_id"],
        location_id=payload["location_id"],
        time_basis="elapsed seconds",
    )
    result = default_registry().run("inspection.multi_period_policy_evaluation", payload, context)
    action_cost = 0.0
    failure_cost = 0.0
    failure_probability = 0.0
    consequence = sum(row["amount"] for row in payload["failure_consequence_components"])
    for path in payload["paths"]:
        probability = path["path_probability_given_start_survival"]
        path_action = sum(
            component["amount_at_stage_time"] * component["present_value_factor"]
            for stage in path["stages"]
            for component in stage["cost_components"]
        )
        action_cost += probability * path_action
        if path["first_failure_occurred"]:
            failure_probability += probability
            failure_cost += probability * consequence * path["failure_consequence_present_value_factor"]
    expected = {
        "conditional_first_failure_probability": failure_probability,
        "expected_discounted_action_cost": action_cost,
        "expected_discounted_failure_consequence": failure_cost,
        "expected_discounted_total_loss": action_cost + failure_cost,
    }
    actual = {key: result.values[key] for key in expected}
    for key in expected:
        if abs(expected[key] - actual[key]) > 1e-15 * max(1.0, abs(expected[key])):
            raise AssertionError(f"multi-period policy direct sum differs for {key}")
    record = {
        "schema_version": "matintegrity.validation.multi_period_inspection_policy.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": (
            "Independent finite-path arithmetic verification only; not validation of path generation, "
            "inspection effects, costs, discounting, policy optimality or regulatory acceptance."
        ),
        "model_id": result.model_id,
        "expected": expected,
        "actual": actual,
        "path_count": len(payload["paths"]),
        "input_digest": result.input_digest,
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/inspection.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/multi_period_inspection_policy_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

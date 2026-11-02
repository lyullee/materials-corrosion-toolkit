"""Verify finite inspection-disposition expectations by an independent direct sum."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.adapters import inspection_action_candidate_from_disposition_tree_result
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    payload = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"][
        "inspection.disposition_decision_tree"
    ]
    context = RunContext(
        asset_id=payload["asset_id"],
        location_id=payload["location_id"],
        time_basis="elapsed seconds",
    )
    result = default_registry().run("inspection.disposition_decision_tree", payload, context)
    expected_inspection_cost = sum(row["amount"] for row in payload["inspection_cost_components"])
    expected_disposition_cost = sum(
        branch["probability_given_inspection"]
        * sum(row["amount"] for row in branch["disposition_cost_components"])
        for branch in payload["outcome_branches"]
    )
    expected_residual_probability = sum(
        branch["probability_given_inspection"]
        * branch["residual_failure_probability_given_outcome_and_disposition"]
        for branch in payload["outcome_branches"]
    )
    expected = {
        "inspection_cost": expected_inspection_cost,
        "expected_disposition_cost": expected_disposition_cost,
        "expected_total_action_cost": expected_inspection_cost + expected_disposition_cost,
        "residual_failure_probability_estimate": expected_residual_probability,
    }
    actual = {key: result.values[key] for key in expected}
    for key in expected:
        if abs(expected[key] - actual[key]) > 1e-15 * max(1.0, abs(expected[key])):
            raise AssertionError(f"disposition-tree direct sum differs for {key}")
    candidate = inspection_action_candidate_from_disposition_tree_result(result)
    candidate_cost = sum(row["amount"] for row in candidate["action_cost_components"])
    if abs(candidate_cost - expected["expected_total_action_cost"]) > 1e-12:
        raise AssertionError("action candidate does not preserve expected action cost")
    if candidate["residual_failure_probability_estimate"] != actual["residual_failure_probability_estimate"]:
        raise AssertionError("action candidate does not preserve residual event probability")
    record = {
        "schema_version": "matintegrity.validation.inspection_disposition_tree.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": (
            "Independently authored finite-sum and adapter verification only; not calibration of inspection "
            "outcomes, POD, false calls, dispositions, residual risk, costs or regulatory acceptance."
        ),
        "model_id": result.model_id,
        "expected": expected,
        "actual": actual,
        "candidate_action_id": candidate["action_id"],
        "candidate_action_cost": candidate_cost,
        "candidate_result_digest": candidate["event_probability_result_sha256"],
        "input_digest": result.input_digest,
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/inspection.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/inspection_disposition_tree_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

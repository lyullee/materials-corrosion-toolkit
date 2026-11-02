"""Verify hard-constraint filtering before finite policy cost comparison."""

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
        "inspection.multi_period_policy_comparison"
    ]
    result = default_registry().run(
        "inspection.multi_period_policy_comparison",
        payload,
        RunContext(
            asset_id=payload["asset_id"],
            location_id=payload["location_id"],
            time_basis="elapsed seconds",
        ),
    )
    constraint = payload["resource_constraints"][0]
    expected_rows = []
    for candidate in payload["candidates"]:
        probability = candidate["conditional_first_failure_probability"]
        usage = candidate["resource_usage"][0]["expected_usage"]
        compliant = (
            probability <= payload["maximum_conditional_first_failure_probability"]
            and usage <= constraint["maximum_usage"]
        )
        expected_rows.append(
            {
                "policy_id": candidate["policy_id"],
                "constraint_compliant": compliant,
                "expected_discounted_total_loss": candidate["expected_discounted_total_loss"],
            }
        )
    feasible = [row for row in expected_rows if row["constraint_compliant"]]
    minimum = min(row["expected_discounted_total_loss"] for row in feasible)
    selected = [row["policy_id"] for row in feasible if row["expected_discounted_total_loss"] == minimum]
    if selected != [result.values["selected_policy_id"]]:
        raise AssertionError(
            "constraint-first policy selection differs from the independent direct comparison"
        )
    actual_rows = result.values["candidate_results"]
    if [row["constraint_compliant"] for row in actual_rows] != [
        row["constraint_compliant"] for row in expected_rows
    ]:
        raise AssertionError("policy constraint classifications differ")
    if minimum != result.values["minimum_constraint_compliant_expected_loss"]:
        raise AssertionError("minimum compliant expected loss differs")
    record = {
        "schema_version": "matintegrity.validation.multi_period_policy_comparison.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": (
            "Independent hard-constraint and finite-set cost comparison only; not validation of policies, "
            "probabilities, resource use, costs, constraints, global optimality or regulatory acceptance."
        ),
        "model_id": result.model_id,
        "expected_rows": expected_rows,
        "selected_policy_id": result.values["selected_policy_id"],
        "minimum_constraint_compliant_expected_loss": minimum,
        "input_digest": result.input_digest,
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/inspection.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/multi_period_policy_comparison_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

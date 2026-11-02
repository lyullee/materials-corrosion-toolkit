"""Verify finite policy probability fitting, holdout scoring and dataset exclusion."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def observation(record_id, sequence, group, partition, state, label, weight=1.0):
    return {
        "record_id": record_id,
        "sequence_id": sequence,
        "source_group_id": group,
        "partition": partition,
        "observation_time_s": 1.0,
        "true_state_id": state,
        "observed_label_id": label,
        "weight": weight,
    }


def transition(record_id, sequence, group, partition, state, action, next_state, weight=1.0):
    return {
        "record_id": record_id,
        "sequence_id": sequence,
        "source_group_id": group,
        "partition": partition,
        "interval_start_s": 1.0,
        "interval_end_s": 2.0,
        "from_state_id": state,
        "action_id": action,
        "to_state_id": next_state,
        "weight": weight,
    }


def main() -> None:
    payload = {
        "calibration_id": "independent-finite-table-check",
        "states": [
            {"state_id": "healthy", "state_definition": "authored state", "is_failure_state": False},
            {"state_id": "degraded", "state_definition": "authored state", "is_failure_state": False},
            {"state_id": "failure", "state_definition": "authored state", "is_failure_state": True},
        ],
        "observation_labels": [
            {"observation_id": "clear", "observation_definition": "authored label"},
            {"observation_id": "alert", "observation_definition": "authored label"},
        ],
        "actions": [
            {"action_id": "monitor", "action_definition": "authored action"},
            {"action_id": "repair", "action_definition": "authored action"},
        ],
        "observation_records": [
            observation("o1", "fit-oh", "fit-oh", "calibration", "healthy", "clear", 3.0),
            observation("o2", "fit-oh", "fit-oh", "calibration", "healthy", "alert"),
            observation("o3", "fit-od", "fit-od", "calibration", "degraded", "clear"),
            observation("o4", "fit-od", "fit-od", "calibration", "degraded", "alert", 3.0),
            observation("oh1", "hold-oh", "hold-oh", "holdout", "healthy", "clear"),
            observation("oh2", "hold-od", "hold-od", "holdout", "degraded", "alert"),
        ],
        "transition_records": [
            transition("t1", "fit-hm", "fit-hm", "calibration", "healthy", "monitor", "healthy", 4.0),
            transition("t2", "fit-hm", "fit-hm", "calibration", "healthy", "monitor", "failure"),
            transition("t3", "fit-hr", "fit-hr", "calibration", "healthy", "repair", "healthy"),
            transition("t4", "fit-dm", "fit-dm", "calibration", "degraded", "monitor", "degraded", 3.0),
            transition("t5", "fit-dm", "fit-dm", "calibration", "degraded", "monitor", "failure", 2.0),
            transition("t6", "fit-dr", "fit-dr", "calibration", "degraded", "repair", "healthy"),
            transition("th1", "hold-h", "hold-h", "holdout", "healthy", "monitor", "healthy"),
            transition("th2", "hold-d", "hold-d", "holdout", "degraded", "monitor", "failure"),
        ],
        "symmetric_pseudocount": 0.0,
        "state_definitions_reviewed": True,
        "physical_state_truth_reviewed": True,
        "observation_labels_reviewed": True,
        "action_assignments_reviewed": True,
        "calibration_holdout_partition_reviewed": True,
        "smoothing_basis_reviewed": True,
        "evidence": [
            {
                "source_id": "authored-finite-policy-calibration-validation",
                "origin": "synthetic",
                "citation": "independently authored weighted counts",
            }
        ],
    }
    result = default_registry().run(
        "inspection.finite_policy_probability_calibration",
        payload,
        RunContext(asset_id="validation", location_id="validation", time_basis="seconds"),
    )
    observation_table = {
        (row["state_id"], row["observation_id"]): row["probability_given_state"]
        for row in result.values["observation_probabilities"]
    }
    transition_table = {
        (row["from_state_id"], row["action_id"], row["to_state_id"]): row[
            "probability_given_state_and_action"
        ]
        for row in result.values["transition_probabilities"]
    }
    expected = {
        "observation_healthy_clear": 0.75,
        "observation_degraded_alert": 0.75,
        "transition_healthy_monitor_failure": 0.2,
        "transition_degraded_monitor_failure": 0.4,
        "observation_holdout_log_loss": -math.log(0.75),
        "transition_holdout_log_loss": -(math.log(0.8) + math.log(0.4)) / 2.0,
    }
    actual = {
        "observation_healthy_clear": observation_table[("healthy", "clear")],
        "observation_degraded_alert": observation_table[("degraded", "alert")],
        "transition_healthy_monitor_failure": transition_table[("healthy", "monitor", "failure")],
        "transition_degraded_monitor_failure": transition_table[("degraded", "monitor", "failure")],
        "observation_holdout_log_loss": result.values["observation_holdout_metrics"][
            "mean_negative_log_likelihood"
        ],
        "transition_holdout_log_loss": result.values["transition_holdout_metrics"][
            "mean_negative_log_likelihood"
        ],
    }
    if result.status != "computed" or any(abs(actual[key] - expected[key]) > 1e-12 for key in expected):
        raise AssertionError("finite policy probability calibration differs from direct calculation")
    ili_audit = json.loads((ROOT / "validation/pipeline_ili_history_audit.json").read_text(encoding="utf-8"))
    record = {
        "schema_version": "matintegrity.validation.finite_policy_probability_calibration.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": (
            "Independent weighted-frequency and holdout-score verification only; not empirical validation "
            "of physical states, inspection labels, actions or transitions."
        ),
        "expected": expected,
        "actual": actual,
        "calibration_input_digest": result.input_digest,
        "pipeline_ili_dataset_application": {
            "dataset_id": ili_audit["dataset_id"],
            "observation_count": ili_audit["observation_count"],
            "status": "not_qualified_for_probability_calibration",
            "reason": ili_audit["qualification"],
        },
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/inspection.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/finite_policy_probability_calibration_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

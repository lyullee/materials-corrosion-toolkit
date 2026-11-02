"""Verify finite-state CTMC propagation against a closed two-state solution."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    failure_rate = 0.1
    repair_rate = 0.2
    duration_s = 10.0
    payload = {
        "chain_id": "authored-two-state",
        "asset_id": "authored",
        "location_id": "system",
        "physical_scope_id": "system",
        "time_basis": "authored seconds",
        "horizon_start_s": 0.0,
        "horizon_end_s": duration_s,
        "conditioning": "operational at interval start",
        "top_event_id": "first-entry-failed",
        "top_event_definition": "first entry into failed",
        "state_ids": ["operational", "failed"],
        "state_definitions": ["operational", "failed with repair"],
        "initial_state_probabilities": [1.0, 0.0],
        "generator_per_s": [
            [-failure_rate, failure_rate],
            [repair_rate, -repair_rate],
        ],
        "top_event_state_ids": ["failed"],
        "provider_id": "authored-validation",
        "provider_version": "1",
        "source_content_sha256": hashlib.sha256(b"authored CTMC").hexdigest(),
        "common_cause_group_ids": [],
        "generator_time_homogeneous_declared": True,
        "state_semantics_reviewed": True,
        "transition_rates_reviewed": True,
        "normalization_tolerance": 1e-12,
        "generator_row_sum_tolerance_per_s": 1e-12,
        "numerical_probability_tolerance": 1e-12,
    }
    result = default_registry().run(
        "reliability.continuous_time_markov_chain",
        payload,
        RunContext(asset_id="authored", location_id="system", time_basis="authored seconds"),
    )
    total_rate = failure_rate + repair_rate
    failed_occupancy = failure_rate / total_rate * (1 - math.exp(-total_rate * duration_s))
    first_hit = 1 - math.exp(-failure_rate * duration_s)
    failed_time = (
        failure_rate / total_rate * (duration_s - (1 - math.exp(-total_rate * duration_s)) / total_rate)
    )
    expected = {
        "failed_occupancy_probability": failed_occupancy,
        "first_hit_probability": first_hit,
        "failed_occupancy_time_s": failed_time,
    }
    actual = {
        "failed_occupancy_probability": result.values["top_event_state_occupancy_probability"],
        "first_hit_probability": result.values["probability_given_survival"],
        "failed_occupancy_time_s": result.values["expected_top_event_state_occupancy_s"],
    }
    errors = {key: abs(actual[key] - value) for key, value in expected.items()}
    if max(errors.values()) > 1e-12:
        raise AssertionError(f"dynamic reliability mismatch: {errors}")
    record = {
        "schema_version": "matintegrity.validation.dynamic_reliability.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": "Authored two-state CTMC mathematical verification; not calibration of failure, repair or replacement rates.",
        "model_id": result.model_id,
        "input_digest": result.input_digest,
        "expected": expected,
        "actual": actual,
        "absolute_errors": errors,
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/reliability.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/dynamic_reliability_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

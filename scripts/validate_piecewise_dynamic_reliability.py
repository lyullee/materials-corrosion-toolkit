"""Verify a split constant CTMC against the homogeneous implementation and closed form."""

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
    generator = [[-failure_rate, failure_rate], [repair_rate, -repair_rate]]
    common = {
        "chain_id": "authored-split-two-state",
        "asset_id": "authored",
        "location_id": "system",
        "physical_scope_id": "system",
        "time_basis": "authored seconds",
        "horizon_start_s": 0.0,
        "horizon_end_s": 10.0,
        "conditioning": "operational at interval start",
        "top_event_id": "first-entry-failed",
        "top_event_definition": "first entry into failed",
        "state_ids": ["operational", "failed"],
        "state_definitions": ["operational", "failed with repair"],
        "initial_state_probabilities": [1.0, 0.0],
        "top_event_state_ids": ["failed"],
        "provider_id": "authored-validation",
        "provider_version": "1",
        "source_content_sha256": hashlib.sha256(b"authored split CTMC").hexdigest(),
        "common_cause_group_ids": [],
        "state_semantics_reviewed": True,
        "normalization_tolerance": 1e-12,
        "generator_row_sum_tolerance_per_s": 1e-12,
        "numerical_probability_tolerance": 1e-12,
    }
    segment_digest = hashlib.sha256(b"authored constant segment rates").hexdigest()
    piecewise_payload = common | {
        "segments": [
            {
                "segment_id": "first",
                "start_s": 0.0,
                "end_s": 4.0,
                "generator_per_s": generator,
                "transition_basis_id": "authored-constant-rates",
                "provider_revision": "1",
                "source_content_sha256": segment_digest,
                "rates_reviewed": True,
            },
            {
                "segment_id": "second",
                "start_s": 4.0,
                "end_s": 10.0,
                "generator_per_s": generator,
                "transition_basis_id": "authored-constant-rates",
                "provider_revision": "1",
                "source_content_sha256": segment_digest,
                "rates_reviewed": True,
            },
        ],
        "segment_sequence_reviewed": True,
        "boundary_time_tolerance_s": 1e-12,
    }
    homogeneous_payload = common | {
        "generator_per_s": generator,
        "generator_time_homogeneous_declared": True,
        "transition_rates_reviewed": True,
    }
    context = RunContext(asset_id="authored", location_id="system", time_basis="authored seconds")
    registry = default_registry()
    piecewise = registry.run("reliability.piecewise_continuous_time_markov_chain", piecewise_payload, context)
    homogeneous = registry.run("reliability.continuous_time_markov_chain", homogeneous_payload, context)
    duration_s = 10.0
    total_rate = failure_rate + repair_rate
    closed_failed_occupancy = failure_rate / total_rate * (1.0 - math.exp(-total_rate * duration_s))
    closed_first_hit = 1.0 - math.exp(-failure_rate * duration_s)
    comparisons = {
        "closed_form_failed_occupancy": abs(
            piecewise.values["top_event_state_occupancy_probability"] - closed_failed_occupancy
        ),
        "closed_form_first_hit": abs(piecewise.values["probability_given_survival"] - closed_first_hit),
        "homogeneous_failed_occupancy": abs(
            piecewise.values["top_event_state_occupancy_probability"]
            - homogeneous.values["top_event_state_occupancy_probability"]
        ),
        "homogeneous_first_hit": abs(
            piecewise.values["probability_given_survival"] - homogeneous.values["probability_given_survival"]
        ),
        "homogeneous_total_expected_transitions": abs(
            piecewise.values["total_expected_transition_count"]
            - homogeneous.values["total_expected_transition_count"]
        ),
    }
    if max(comparisons.values()) > 1e-12:
        raise AssertionError(f"piecewise dynamic reliability mismatch: {comparisons}")
    record = {
        "schema_version": "matintegrity.validation.piecewise_dynamic_reliability.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": (
            "Authored split-generator mathematical verification; not calibration of failure, repair, "
            "replacement or operating-condition transition rates."
        ),
        "model_id": piecewise.model_id,
        "input_digest": piecewise.input_digest,
        "segment_ids": piecewise.values["segment_ids"],
        "boundary_times_s": piecewise.values["boundary_times_s"],
        "absolute_errors": comparisons,
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/reliability.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/piecewise_dynamic_reliability_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

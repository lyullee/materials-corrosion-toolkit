"""Verify finite joint-state probability calculations with authored exact cases."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    payload = {
        "distribution_id": "authored-two-event",
        "asset_id": "authored",
        "location_id": "system",
        "physical_scope_id": "system",
        "time_basis": "authored interval seconds",
        "horizon_start_s": 0.0,
        "horizon_end_s": 1.0,
        "conditioning": "system intact at interval start",
        "top_event_id": "a-or-b",
        "top_event_definition": "A or B",
        "event_ids": ["a", "b"],
        "event_definitions": ["A", "B"],
        "states": [
            {"event_occurs": [False, False], "probability": 0.75, "top_event_occurs": False},
            {"event_occurs": [True, False], "probability": 0.05, "top_event_occurs": True},
            {"event_occurs": [False, True], "probability": 0.15, "top_event_occurs": True},
            {"event_occurs": [True, True], "probability": 0.05, "top_event_occurs": True},
        ],
        "dependence_basis": "user_supplied_scenario_weights",
        "provider_id": "authored-validation",
        "provider_version": "1",
        "source_content_sha256": hashlib.sha256(b"authored joint distribution").hexdigest(),
        "common_cause_group_ids": ["declared-shared-driver"],
        "state_space_complete_declared": True,
        "distribution_reviewed": True,
        "normalization_tolerance": 1e-12,
    }
    result = default_registry().run(
        "reliability.joint_event_probability",
        payload,
        RunContext(asset_id="authored", location_id="system", time_basis="authored interval seconds"),
    )
    expected = {
        "probability_given_survival": 0.25,
        "marginal_a": 0.10,
        "marginal_b": 0.20,
        "joint_ab": 0.05,
        "covariance_ab": 0.03,
        "phi_ab": 0.25,
        "independent_reference_probability": 0.28,
        "dependence_probability_delta": -0.03,
    }
    actual = {
        "probability_given_survival": result.values["probability_given_survival"],
        "marginal_a": result.values["event_marginal_probabilities"][0],
        "marginal_b": result.values["event_marginal_probabilities"][1],
        "joint_ab": result.values["pairwise_joint_probabilities"][0][1],
        "covariance_ab": result.values["pairwise_covariances"][0][1],
        "phi_ab": result.values["pairwise_phi_coefficients"][0][1],
        "independent_reference_probability": result.values["independent_reference_probability"],
        "dependence_probability_delta": result.values["dependence_probability_delta"],
    }
    errors = {key: abs(actual[key] - value) for key, value in expected.items()}
    if max(errors.values()) > 1e-12:
        raise AssertionError(f"joint-event probability mismatch: {errors}")
    record = {
        "schema_version": "matintegrity.validation.joint_event_probability.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": "Authored finite probability-space arithmetic verification; not calibration of event marginals or common-cause dependence.",
        "model_id": result.model_id,
        "input_digest": result.input_digest,
        "expected": expected,
        "actual": actual,
        "absolute_errors": errors,
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/reliability.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/joint_event_probability_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

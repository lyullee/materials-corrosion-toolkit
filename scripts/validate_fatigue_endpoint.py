"""Verify fatigue endpoint classification with authored, mutually exclusive event cases."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.models import fatigue
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_AUDIT = ROOT / "validation/fabest_hcf_package.json"


def _base(protocol: dict) -> dict:
    return {
        "segments": [
            {
                "segment_id": "reviewed-segment-1",
                "physical_specimen_id": "specimen-1",
                "load_case_id": "load-case-1",
                "valid_loading_cycles": float(protocol["runout_limit_cycles"]),
                "cycle_count_basis": "reviewed_manual",
            }
        ],
        "initial_pressure_Pa": 60e6,
        "observed_pressure_drop_Pa": 0.0,
        "declared_drop_fraction_threshold": protocol["declared_pressure_drop_fraction_threshold"],
        "event_origin": "none",
        "specimen_event_kind": "none",
        "specimen_pressure_loss_confirmed": False,
        "same_physical_specimen_across_segments_declared": True,
        "loading_history_reconstructable": True,
        "runout_limit_cycles": float(protocol["runout_limit_cycles"]),
        "observation_window_closed": True,
    }


def main():
    protocol_audit_bytes = PROTOCOL_AUDIT.read_bytes()
    protocol_audit = json.loads(protocol_audit_bytes)
    protocol = protocol_audit["endpoint_protocol_review"]
    if protocol["blind_results_available"] is not False:
        raise AssertionError("blind outcomes must remain unavailable in this contract check")
    if protocol["specimen_origin_confirmation_required"] is not True:
        raise AssertionError("specimen-origin confirmation requirement is missing")
    threshold_drop_Pa = 60e6 * protocol["declared_pressure_drop_fraction_threshold"]
    context = RunContext(
        asset_id="authored-fatigue-endpoint",
        location_id="pressure-boundary",
        time_basis="reviewed cumulative loading cycles",
    )
    cases = {
        "confirmed_specimen_endpoint": (
            {
                "observed_pressure_drop_Pa": threshold_drop_Pa,
                "event_origin": "specimen",
                "specimen_event_kind": "through_wall_crack",
                "specimen_pressure_loss_confirmed": True,
            },
            "computed",
            "confirmed_specimen_pressure_loss_endpoint",
            "failure_endpoint",
        ),
        "pressure_system_interruption": (
            {
                "observed_pressure_drop_Pa": threshold_drop_Pa,
                "event_origin": "pressure_system",
            },
            "computed",
            "system_or_instrument_interruption",
            "none",
        ),
        "right_censored_runout": ({}, "computed", "runout", "right_censored_runout"),
        "unresolved_origin": (
            {"observed_pressure_drop_Pa": 10e6, "event_origin": "unresolved"},
            "needs_data",
            "unresolved_event_origin",
            "none",
        ),
    }
    registry = default_registry()
    records = []
    for case_id, (overrides, expected_status, expected_classification, expected_censoring) in cases.items():
        inputs = _base(protocol) | overrides
        result = registry.run("fatigue.pressure_loss_endpoint", inputs, context)
        actual = {
            "status": result.status,
            "endpoint_classification": result.values["endpoint_classification"],
            "censoring_role": result.values["censoring_role"],
            "resume_eligible": result.values["resume_eligible"],
            "usable_as_fatigue_observation": result.values["usable_as_fatigue_observation"],
        }
        expected = {
            "status": expected_status,
            "endpoint_classification": expected_classification,
            "censoring_role": expected_censoring,
        }
        if any(actual[key] != value for key, value in expected.items()):
            raise AssertionError(f"endpoint classification mismatch for {case_id}: {actual}")
        records.append(
            {
                "case_id": case_id,
                "input_digest": result.input_digest,
                "expected": expected,
                "actual": actual,
            }
        )

    record = {
        "schema_version": "matintegrity.fatigue_endpoint_contract.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_id": "fatigue.pressure_loss_endpoint",
        "model_source_sha256": hashlib.sha256(Path(fatigue.__file__).read_bytes()).hexdigest(),
        "benchmark_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "protocol_audit_sha256": hashlib.sha256(protocol_audit_bytes).hexdigest(),
        "protocol_scope": protocol["scope"],
        "reviewed_protocol_inputs": {
            "declared_pressure_drop_fraction_threshold": protocol[
                "declared_pressure_drop_fraction_threshold"
            ],
            "runout_limit_cycles": protocol["runout_limit_cycles"],
            "specimen_origin_confirmation_required": protocol["specimen_origin_confirmation_required"],
            "cumulative_valid_loading_cycles_across_restarts": protocol[
                "cumulative_valid_loading_cycles_across_restarts"
            ],
        },
        "cases": records,
        "qualification": (
            "Protocol-to-software contract checks for the fixed FABEST HCF competition package. "
            "They verify that the reviewed threshold, specimen-origin confirmation, system "
            "interruptions, runout limit and cumulative valid segments remain distinct; they do "
            "not validate blind outcomes, fatigue strength, fatigue life or failure probability."
        ),
    }
    target = ROOT / "validation/fatigue_endpoint_contract.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

"""Verify the digest-bound monitoring exchange and its fail-closed semantics."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from matintegrity import adapters, evaluate
from matintegrity.adapters import MonitoringAssessmentRecord, monitoring_record
from matintegrity.contracts import RunContext

ROOT = Path(__file__).resolve().parents[1]
REVIEWED_PROCESS_MONITORING_REVISION = "79b4cf52a0acd0d0cbd3addbe82c3d98d6385e5a"


def main() -> None:
    context = RunContext(
        asset_id="authored-monitoring-exchange",
        location_id="synthetic-pressure-boundary",
        time_basis="authored elapsed seconds",
    )
    result = evaluate(
        "structural.pressure_temperature_envelope",
        {
            "envelope_id": "authored-monitoring-validation",
            "applicability_basis": "synthetic exchange arithmetic only",
            "source_sha256": "a" * 64,
            "knots": [
                {"temperature_K": 250.0, "allowable_pressure_Pa": 12.0e6},
                {"temperature_K": 350.0, "allowable_pressure_Pa": 8.0e6},
            ],
            "operating_points": [{"point_id": "snapshot", "temperature_K": 300.0, "pressure_Pa": 9.0e6}],
            "applicability_reviewed": True,
            "operating_points_reviewed": True,
        },
        context,
    )
    record = monitoring_record(result)
    restored = MonitoringAssessmentRecord.model_validate_json(json.dumps(record, allow_nan=False))
    if restored.values != result.values or restored.input_digest != result.input_digest:
        raise AssertionError("monitoring exchange did not preserve the assessment")

    tampered = deepcopy(record)
    tampered["values"]["minimum_pressure_margin_Pa"] = -123.0
    try:
        MonitoringAssessmentRecord.model_validate_json(json.dumps(tampered, allow_nan=False))
    except ValidationError:
        tamper_rejected = True
    else:
        raise AssertionError("tampered monitoring assessment was accepted")

    incomplete = evaluate(
        "reliability.independent_gate",
        {"probabilities": [0.1, 0.2], "gate": "OR", "independence_declared": False},
        context,
    )
    incomplete_record = monitoring_record(incomplete)
    if incomplete_record["status"] != "needs_data":
        raise AssertionError("needs_data status was not preserved")
    if "alarm" in incomplete_record or "normal" in incomplete_record:
        raise AssertionError("monitoring exchange invented an alarm or normal state")

    validation = {
        "schema_version": "matintegrity.monitoring_exchange_validation.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "adapter_source_sha256": hashlib.sha256(Path(adapters.__file__).read_bytes()).hexdigest(),
        "validation_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "assessment_input_digest": result.input_digest,
        "assessment_snapshot_digest": record["source_digest"],
        "round_trip_preserved": True,
        "tampered_value_rejected": tamper_rejected,
        "needs_data_preserved_without_alarm_label": True,
        "reviewed_process_monitoring_revision": REVIEWED_PROCESS_MONITORING_REVISION,
        "reviewed_process_monitoring_output_schema": "process-monitoring.detection.v1",
        "receiver_for_matintegrity_monitoring_context_present_at_reviewed_revision": False,
        "qualification": (
            "Authored contract, JSON round-trip and negative-control verification. The process-monitoring revision "
            "was inspected read-only; it does not yet consume this schema. This is not live repository integration, "
            "fault diagnosis, alarm qualification or failure-probability validation."
        ),
    }
    target = ROOT / "validation/monitoring_exchange_contract.json"
    target.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

"""Validate human-reliability exchange semantics and optionally a pinned provider checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from matintegrity import human_reliability_exchange
from matintegrity.human_reliability_exchange import (
    HumanReliabilityEstimateRecord,
    human_reliability_estimate_record,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEWED_PROVIDER_REVISION = "d2754bbea16e12d00240e88d13cb4badbe672ac3"
PROVIDER_PROGRAM = r"""
import json
from importlib.resources import files
from human_reliability.assessment import AssessmentCase, AssessmentEngine
case = AssessmentCase.model_validate_json(
    files("human_reliability.data").joinpath("example_case.json").read_text()
)
result = AssessmentEngine().assess(case)
print(json.dumps({
    "event": case.events[0].model_dump(mode="json"),
    "estimate": result["estimates"][0],
    "assessment_input_digest": result["input_digest"],
    "task_id": result["task_id"],
    "context_id": result["context_id"],
    "procedure_version": case.task.procedure_version,
    "empirical_plant_validation_claim": result["empirical_plant_validation_claim"],
}, sort_keys=True))
"""


def authored_source() -> dict:
    return {
        "event": {
            "id": "authored-response-failure",
            "task_id": "authored-task",
            "step_ids": ["respond"],
            "role": "response",
            "failure_definition": "reviewed response is not completed",
            "opportunity_definition": "one authored response opportunity",
            "conditioning": "authored cue is present",
            "deadline_s": None,
            "includes_recovery": False,
            "includes_timing": False,
            "dependency_group": None,
        },
        "estimate": {
            "event_id": "authored-response-failure",
            "method": "authored-exchange-test",
            "probability": 0.1,
            "conditioning": "authored cue is present",
            "evidence_ids": ["authored-evidence"],
            "uncertainty": {},
            "includes": [],
            "status": "research",
            "trace": {"qualification": "exchange arithmetic only"},
        },
        "assessment_input_digest": "1" * 64,
        "task_id": "authored-task",
        "context_id": "authored-context",
        "procedure_version": "authored-procedure",
        "empirical_plant_validation_claim": False,
    }


def provider_source(provider_root: Path) -> dict:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=provider_root, check=True, capture_output=True, text=True
    ).stdout.strip()
    if revision != REVIEWED_PROVIDER_REVISION:
        raise ValueError(f"provider revision differs from the reviewed pin: {revision}")
    candidates = [
        provider_root / ".venv/Scripts/python.exe",
        provider_root / ".venv/bin/python",
    ]
    python = next((path for path in candidates if path.is_file()), None)
    if python is None:
        raise FileNotFoundError("provider checkout needs its prepared .venv Python")
    completed = subprocess.run(
        [str(python), "-c", PROVIDER_PROGRAM],
        cwd=provider_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-root", type=Path)
    args = parser.parse_args()
    source = (
        authored_source() if args.provider_root is None else provider_source(args.provider_root.resolve())
    )
    if source["task_id"] != source["event"]["task_id"]:
        raise AssertionError("provider assessment task differs from the selected event")
    if source["empirical_plant_validation_claim"] is not False:
        raise AssertionError("provider example unexpectedly claims empirical plant validation")

    record = human_reliability_estimate_record(
        provider_id="human-reliability-toolkit",
        provider_revision=REVIEWED_PROVIDER_REVISION,
        assessment_input_digest=source["assessment_input_digest"],
        procedure_version=source["procedure_version"],
        context_id=source["context_id"],
        source_event=source["event"],
        source_estimate=source["estimate"],
        limitations=["Exchange validation only; no operator, plant, or period-risk qualification."],
    )
    restored = HumanReliabilityEstimateRecord.model_validate_json(record.model_dump_json())
    if restored.digest_payload() != record.digest_payload():
        raise AssertionError("human-reliability JSON round trip changed the record")

    tampered = deepcopy(record.model_dump(mode="json"))
    tampered["probability_per_opportunity"] = 0.2
    try:
        HumanReliabilityEstimateRecord.model_validate(tampered)
    except ValidationError:
        tamper_rejected = True
    else:
        raise AssertionError("changed human-reliability probability passed the contract")

    relabelled = deepcopy(record.model_dump(mode="json"))
    relabelled["probability_semantics"] = "conditional_first_failure_in_period"
    try:
        HumanReliabilityEstimateRecord.model_validate(relabelled)
    except ValidationError:
        period_relabelling_rejected = True
    else:
        raise AssertionError("opportunity probability was accepted as a period first-failure probability")

    validation = {
        "schema_version": "matintegrity.human_reliability_exchange_validation.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "contract_source_sha256": hashlib.sha256(
            Path(human_reliability_exchange.__file__).read_bytes()
        ).hexdigest(),
        "validation_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "payload_digest": record.payload_digest,
        "source_estimate_digest": record.source_estimate_digest,
        "json_round_trip_preserved": True,
        "tampered_probability_rejected": tamper_rejected,
        "period_probability_relabelling_rejected": period_relabelling_rejected,
        "reviewed_provider_revision": REVIEWED_PROVIDER_REVISION,
        "provider_example_executed": args.provider_root is not None,
        "provider_empirical_plant_validation_claim": False,
        "qualification": (
            "Provider example execution when provider_example_executed is true, plus authored contract, JSON "
            "round-trip and negative-control checks. This is not human-performance, plant, task-transfer, "
            "dependence, demand-frequency, material-failure, or period-risk validation."
        ),
    }
    target = ROOT / "validation/human_reliability_exchange_contract.json"
    target.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

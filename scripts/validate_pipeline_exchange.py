"""Validate the pipeline-result receipt and optionally execute a provider source tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from matintegrity import pipeline_exchange
from matintegrity.pipeline_exchange import PipelineAssessmentRecord, pipeline_assessment_record

ROOT = Path(__file__).resolve().parents[1]
PROVIDER_PROGRAM = r"""
import json
from pipeline_integrity import evaluate
from pipeline_integrity.contracts import EvidenceRef, RunContext
context = RunContext(
    asset_id="authored-pipe",
    scenario_id="geometry-contract",
    clock_id="elapsed-s",
    origin="synthetic",
    evidence=(EvidenceRef(
        id="authored-geometry",
        citation="authored software exchange fixture",
        origin="synthetic",
    ),),
)
result = evaluate("geometry.pipe", {
    "inner_diameter_m": 0.5,
    "outer_diameter_m": 0.55,
    "length_m": 10.0,
    "wall_density_kg_m3": 7850.0,
}, context)
print(result.model_dump_json())
"""


def source_tree_digest(root: Path) -> tuple[str, int]:
    paths = sorted([root / "pyproject.toml", *(root / "src").rglob("*.py")])
    paths = [path for path in paths if path.is_file()]
    if not paths:
        raise ValueError("provider source tree contains no reviewed Python sources")
    digest = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest(), len(paths)


def authored_source() -> tuple[dict, str, int]:
    source = {
        "schema_version": "pipeline_integrity.result.v1",
        "model_id": "geometry.pipe",
        "model_version": "1.0.0",
        "status": "computed",
        "inputs": {"inner_diameter_m": 0.5},
        "values": {"flow_area_m2": 0.19634954084936207},
        "input_units": {"inner_diameter_m": "m"},
        "output_units": {"flow_area_m2": "m2"},
        "assumptions": ["authored software exchange fixture"],
        "notes": [],
        "source_ids": ["authored"],
        "context": {
            "asset_id": "authored-pipe",
            "scenario_id": "geometry-contract",
            "clock_id": "elapsed-s",
            "origin": "synthetic",
            "evidence": [
                {
                    "id": "authored-geometry",
                    "citation": "authored software exchange fixture",
                    "origin": "synthetic",
                    "locator": "",
                    "sha256": None,
                    "license_id": None,
                    "limitations": [],
                }
            ],
            "metadata": {},
        },
        "input_digest": "1" * 64,
        "model_source_digest": "2" * 64,
        "runtime": {"python": sys.version.split()[0]},
        "qualification": "engineering_screening",
    }
    return source, "0" * 64, 1


def provider_source(provider_root: Path) -> tuple[dict, str, int]:
    tree_sha, file_count = source_tree_digest(provider_root)
    env = os.environ.copy()
    provider_src = str(provider_root / "src")
    env["PYTHONPATH"] = provider_src + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [sys.executable, "-c", PROVIDER_PROGRAM],
        cwd=provider_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout), tree_sha, file_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-root", type=Path)
    args = parser.parse_args()
    source, tree_sha, file_count = (
        authored_source() if args.provider_root is None else provider_source(args.provider_root.resolve())
    )
    record = pipeline_assessment_record(
        provider_id="pipeline-integrity-toolkit",
        provider_package_version="0.1.0.dev0",
        provider_source_tree_sha256=tree_sha,
        provider_source_file_count=file_count,
        source_result=source,
        limitations=[
            "Software exchange validation only; no field, design, code-compliance, or physical-model qualification."
        ],
    )
    restored = PipelineAssessmentRecord.model_validate_json(record.model_dump_json())
    if restored.digest_payload() != record.digest_payload():
        raise AssertionError("pipeline assessment JSON round trip changed the record")

    tampered = deepcopy(record.model_dump(mode="json"))
    tampered["source_result"]["context"]["clock_id"] = "foreign-clock"
    try:
        PipelineAssessmentRecord.model_validate(tampered)
    except ValidationError:
        tamper_rejected = True
    else:
        raise AssertionError("changed pipeline clock passed the exchange contract")

    acceptance = deepcopy(record.model_dump(mode="json"))
    acceptance["field_or_design_acceptance_claim"] = True
    try:
        PipelineAssessmentRecord.model_validate(acceptance)
    except ValidationError:
        acceptance_rejected = True
    else:
        raise AssertionError("pipeline screening result was accepted as field or design acceptance")

    validation = {
        "schema_version": "matintegrity.pipeline_exchange_validation.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "contract_source_sha256": hashlib.sha256(Path(pipeline_exchange.__file__).read_bytes()).hexdigest(),
        "validation_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "payload_digest": record.payload_digest,
        "source_result_digest": record.source_result_digest,
        "provider_source_tree_sha256": tree_sha,
        "provider_source_file_count": file_count,
        "provider_example_executed": args.provider_root is not None,
        "json_round_trip_preserved": True,
        "tampered_clock_rejected": tamper_rejected,
        "field_or_design_acceptance_relabelling_rejected": acceptance_rejected,
        "qualification": (
            "Provider geometry example execution when provider_example_executed is true, plus contract, JSON "
            "round-trip and negative-control checks. This is not hydraulic, structural, corrosion, field, "
            "design-code, or system-risk validation."
        ),
    }
    target = ROOT / "validation/pipeline_exchange_contract.json"
    target.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

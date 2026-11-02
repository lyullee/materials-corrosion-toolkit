"""Metadata-only checks for Ti12Mo5Hf; never open or acquire the source ZIP."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

from matintegrity.contracts import canonical_digest
from matintegrity.ti12mo5hf_corrosion_data import (
    ARCHIVE_BYTES, ARCHIVE_MD5, ARCHIVE_NAME, DATASET_ID, LICENSE_ID,
    PROVIDER_RECORD, README_BYTES, README_MD5, README_NAME, README_SHA256,
    Ti12Mo5HfArchiveAudit, Ti12Mo5HfArchiveAuditRequest, Ti12Mo5HfProviderCondition,
    specifications,
)

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "data.zenodo_ti12mo5hf_archive_audit"
METADATA = ROOT/"metadata/ti12mo_catalog_snapshot.json"


def contracts_checks():
    specs = specifications()
    assert len(specs) == 1
    spec = specs[0]
    assert spec.model_id == MODEL_ID and spec.input_type is Ti12Mo5HfArchiveAuditRequest
    assert spec.source_ids == (DATASET_ID,) and spec.qualification == "data_import"
    assert spec.evaluator.__name__ == "evaluate_archive_audit_request"
    assert spec.units["archive_audit.member_count"] == "1"
    records = []
    for contract in (Ti12Mo5HfArchiveAuditRequest, Ti12Mo5HfArchiveAudit, Ti12Mo5HfProviderCondition):
        actual = json.loads((ROOT/"docs/schemas"/(contract.__name__+".json")).read_text(encoding="utf-8"))
        assert actual == contract.model_json_schema(), contract.__name__
        records.append({"contract": contract.__name__, "schema_sha256": canonical_digest(actual)})
    artifact = json.loads(METADATA.read_text(encoding="utf-8"))
    row = artifact["source_catalogs"]["capabilities"]["row"]
    assert row["id"] == MODEL_ID and row["input_schema"] == spec.input_type.model_json_schema()
    assert row["source_ids"] == list(spec.source_ids)
    tree = ast.parse((ROOT/"src/matintegrity/registry.py").read_text(encoding="utf-8"))
    module_name = "ti12mo5hf_corrosion_data"
    assert any(isinstance(node, ast.ImportFrom) and any(alias.name == module_name for alias in node.names) for node in ast.walk(tree))
    assert any(isinstance(node, ast.For) and isinstance(node.iter, (ast.Tuple, ast.List)) and any(isinstance(item, ast.Name) and item.id == module_name for item in node.iter.elts) for node in ast.walk(tree))
    return {"model_id": MODEL_ID, "schemas": records, "member_count_unit": "1",
            "central_registration_evidence": "AST import and module registration loop; full registry execution not performed",
            "archive_evaluator_called": False}


def provenance_checks():
    artifact = json.loads(METADATA.read_text(encoding="utf-8"))
    for name in ("capabilities", "datasets", "sources"):
        source = artifact["source_catalogs"][name]
        packaged = artifact["package_catalogs"][name]
        assert source["row"] == packaged["row"], name
        assert source["origin_file_sha256"] == packaged["origin_file_sha256"], name
        assert len(source["origin_file_sha256"]) == 64
    dataset = artifact["source_catalogs"]["datasets"]["row"]
    source = artifact["source_catalogs"]["sources"]["row"]
    assert dataset["id"] == source["id"] == DATASET_ID
    assert dataset["license"] == LICENSE_ID == "CC0-1.0"
    assert dataset["acquisition_policy"] == "allowed" and dataset["rights_status"] == "reviewed_license"
    assert dataset["rights_evidence_url"] == "https://zenodo.org/records/19462164"
    assert source["url"] == PROVIDER_RECORD and "CC0" in source["license"]
    assets = {row["filename"]: row for row in dataset["assets"]}
    assert assets[ARCHIVE_NAME]["bytes"] == ARCHIVE_BYTES
    assert assets[ARCHIVE_NAME]["checksum"] == "md5:"+ARCHIVE_MD5
    assert assets[README_NAME]["bytes"] == README_BYTES
    assert assets[README_NAME]["checksum"] == "md5:"+README_MD5
    observed = artifact["local_readme_digest_observation"]
    assert observed["bytes"] == README_BYTES and observed["sha256"] == README_SHA256
    assert observed["md5"] == README_MD5
    for label in ("Ti12Mo5Hf", "Ti12Mo5Hf0.3O"):
        condition = Ti12Mo5HfProviderCondition(alloy_label=label)
        assert condition.metadata_sha256 == observed["sha256"] and condition.license_id == LICENSE_ID
    assert artifact["archive_content_checked"] is False
    assert artifact["raw_archive_copied"] is False and artifact["readme_text_copied"] is False
    assert not (ROOT/"data/raw").exists() and not (ROOT/"data/evidence").exists()
    return {"dataset_id": DATASET_ID, "license_id": LICENSE_ID,
            "source_id": source["id"], "readme_digest_observation": observed,
            "catalog_parity_scope": "selected copied rows and equality of captured full-file hash declarations; full catalog files are not staged",
            "source_rights_record": {key: source[key] for key in ("basis", "license", "reuse", "checked_on")},
            "archive_content_checked": False, "archive_sha256_verified": False,
            "readme_rehashed_on_compute_node": False, "raw_archive_or_readme_text_staged": False,
            "metadata_artifact_sha256": hashlib.sha256(METADATA.read_bytes()).hexdigest()}


def main():
    tasks = {"contracts": contracts_checks, "provenance": provenance_checks}
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=tasks, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        details = tasks[args.task]()
    except Exception as exc:
        args.output.write_text(json.dumps({"task": args.task, "status": "failed", "exception_type": type(exc).__name__, "message": str(exc)}, indent=2), encoding="utf-8")
        raise
    args.output.write_text(json.dumps({"task": args.task, "status": "passed", "details": details,
        "meaning": "metadata/software contract consistency only; source ZIP is not acquired, opened, numerically analyzed, or validated"}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

"""Validate the pinned, read-only GitHub integration catalog without network access."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/catalogs/github_integrations.json"
COMMIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
CONTENT_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def main() -> None:
    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "matintegrity.github_integrations.v1":
        raise ValueError("unexpected GitHub integration catalog schema")
    repositories = payload.get("repositories")
    if not isinstance(repositories, list) or not repositories:
        raise ValueError("GitHub integration catalog requires repositories")
    identities: set[tuple[str, str]] = set()
    consumer_executions = 0
    numeric_pof_provider_executions = 0
    for record in repositories:
        identity = (record["owner"], record["repository"])
        if identity in identities:
            raise ValueError(f"duplicate GitHub integration target: {identity}")
        identities.add(identity)
        if not COMMIT_SHA_PATTERN.fullmatch(record["reviewed_commit"]):
            raise ValueError(f"invalid Git commit for {identity}")
        schema_hashes = record.get("reviewed_schema_sha256")
        if not isinstance(schema_hashes, dict) or not schema_hashes:
            raise ValueError(f"missing reviewed schema hashes for {identity}")
        if any(not CONTENT_SHA256_PATTERN.fullmatch(value) for value in schema_hashes.values()):
            raise ValueError(f"invalid reviewed schema hash for {identity}")
        request_path = ROOT / record["request_document"]
        if not request_path.is_file():
            raise ValueError(f"missing integration request document: {request_path}")
        if record["end_to_end_status"] != "not_run":
            raise ValueError("catalog cannot claim an end-to-end run without a separate immutable receipt")
        receipt_path = record.get("consumer_execution_receipt")
        if receipt_path is not None:
            receipt = json.loads((ROOT / receipt_path).read_text(encoding="utf-8"))
            if not receipt.get("consumer_execution_performed"):
                raise ValueError("consumer execution receipt does not record execution")
            side = "api581" if record["repository"] == "api581-risk-analysis" else "consequence"
            if receipt[side]["commit"] != record["reviewed_commit"]:
                raise ValueError("consumer execution commit differs from catalog")
            if side == "api581" and not receipt[side]["consumer_calculation_executed"]:
                raise ValueError("API 581 consumer calculation was not executed")
            if side == "api581":
                if not receipt[side].get("numeric_pof_provider_executed"):
                    raise ValueError("API 581 numeric frequency/probability provider was not executed")
                numeric_pof_provider_executions += 1
            if side == "consequence" and not receipt[side]["provider_binding_executed"]:
                raise ValueError("consequence provider binding was not executed")
            consumer_executions += 1
        if record["qualification_status"] != "not_claimed":
            raise ValueError("catalog cannot claim engineering qualification")
    print(
        json.dumps(
            {
                "repositories": len(repositories),
                "request_documents_present": len(repositories),
                "end_to_end_runs": 0,
                "consumer_executions": consumer_executions,
                "numeric_pof_provider_executions": numeric_pof_provider_executions,
                "engineering_qualifications": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

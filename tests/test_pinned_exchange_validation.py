import hashlib
import json

import pytest

from matintegrity.external_schema_audit import build_external_schema_audit_record
from matintegrity.pinned_exchange_validation import (
    PinnedSchemaValidationReport,
    build_pinned_exchange_validation_receipt,
    build_pinned_schema_validation_report,
)

REPOSITORY = "example/consumer-schema"
COMMIT = "a" * 40
PATH = "schemas/temperature.json"
SCHEMA_ID = "https://schemas.example.test/temperature"
SCHEMA_VERSION = "1.0.0"
CONFIGURATION_DIGEST = "c" * 64


def producer_payload():
    return {
        "asset": {"id": "asset-1"},
        "temperature": {"value": 300.0, "unit": "K"},
        "probability": {
            "value": 0.01,
            "semantics": "conditional_first_failure_in_period",
        },
    }


def audit(commit=COMMIT, path=PATH):
    schema = {
        "$id": SCHEMA_ID,
        "x-schema-version": SCHEMA_VERSION,
        "type": "object",
        "properties": {
            "asset": {"type": "object"},
            "temperature": {"type": "object"},
            "probability": {"type": "object"},
        },
        "required": ["asset", "temperature", "probability"],
        "additionalProperties": False,
    }
    content = json.dumps(schema, separators=(",", ":")).encode()
    return build_external_schema_audit_record(
        source_url=f"https://raw.githubusercontent.com/{REPOSITORY}/{commit}/{path}",
        repository_id=REPOSITORY,
        pinned_commit=commit,
        repository_path=path,
        schema_content=content,
        expected_content_sha256=hashlib.sha256(content).hexdigest(),
        expected_json_schema_id=SCHEMA_ID,
        expected_json_schema_version=SCHEMA_VERSION,
        limitations=("Synthetic schema audit for authored tests only.",),
    )


def findings(probability_status="passed"):
    return (
        {
            "finding_id": "schema-1",
            "category": "schema",
            "path": "/temperature/value",
            "status": "passed",
            "expected_descriptor": "number",
            "observed_descriptor": "number",
            "basis": "external validator report says the field matched",
        },
        {
            "finding_id": "unit-1",
            "category": "unit",
            "path": "/temperature/unit",
            "status": "passed",
            "expected_descriptor": "K",
            "observed_descriptor": "K",
            "basis": "exact unit token comparison",
        },
        {
            "finding_id": "identity-1",
            "category": "identity",
            "path": "/asset/id",
            "status": "passed",
            "expected_descriptor": "asset-1",
            "observed_descriptor": "asset-1",
            "basis": "exact asset identity comparison",
        },
        {
            "finding_id": "probability-1",
            "category": "probability_semantics",
            "path": "/probability/semantics",
            "status": probability_status,
            "expected_descriptor": "conditional_first_failure_in_period",
            "observed_descriptor": (
                "conditional_first_failure_in_period"
                if probability_status == "passed"
                else "point_in_time_state_probability"
            ),
            "basis": "exact probability-semantics comparison",
        },
    )


def report(schema_audit=None, payload=None, finding_rows=None):
    schema_audit = audit() if schema_audit is None else schema_audit
    payload = producer_payload() if payload is None else payload
    finding_rows = findings() if finding_rows is None else finding_rows
    return build_pinned_schema_validation_report(
        schema_audit=schema_audit,
        producer_payload=payload,
        validator_id="synthetic-json-schema-validator",
        validator_revision="rev-1",
        validator_configuration_digest=CONFIGURATION_DIGEST,
        findings=finding_rows,
        limitations=("Reported structural validation is not end-to-end or physical qualification.",),
    )


def producer_endpoint():
    return {
        "repository_id": "example/producer",
        "schema_id": "producer.temperature",
        "schema_version": "2.0.0",
        "provider_id": "producer-provider",
        "provider_commit": "b" * 40,
        "provider_revision": "producer-rev-1",
    }


def consumer_endpoint(commit=COMMIT):
    return {
        "repository_id": REPOSITORY,
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "provider_id": "consumer-provider",
        "provider_commit": commit,
        "provider_revision": "consumer-rev-1",
    }


def receipt(schema_audit=None, validation_report=None, payload=None, **updates):
    schema_audit = audit() if schema_audit is None else schema_audit
    payload = producer_payload() if payload is None else payload
    validation_report = report(schema_audit, payload) if validation_report is None else validation_report
    arguments = {
        "producer_payload": payload,
        "schema_audit": schema_audit,
        "validation_report": validation_report,
        "producer": producer_endpoint(),
        "consumer": consumer_endpoint(schema_audit.pinned_commit),
        "compatibility_scope": "pinned schema report and declared semantic checks only",
        "limitations": ("No consumer execution was performed.",),
    }
    arguments.update(updates)
    return build_pinned_exchange_validation_receipt(**arguments)


def test_pinned_report_builds_deterministic_accepted_receipt_without_execution_claims():
    schema_audit = audit()
    validation_report = report(schema_audit)
    first = receipt(schema_audit, validation_report)
    second = receipt(schema_audit, validation_report)
    assert first == second
    assert first.status == "accepted"
    assert first.configuration_digest == CONFIGURATION_DIGEST
    assert first.accepted_paths == (
        "/asset/id",
        "/probability/semantics",
        "/temperature/unit",
        "/temperature/value",
    )
    assert validation_report.consumer_executed is False
    assert validation_report.end_to_end_qualification_claimed is False
    assert first.cross_repository_execution_claimed is False
    assert first.physical_validation_claimed is False
    assert any("not end-to-end" in value for value in first.limitations)


def test_failed_probability_semantics_deterministically_rejects_path():
    schema_audit = audit()
    validation_report = report(schema_audit, finding_rows=findings("failed"))
    result = receipt(schema_audit, validation_report)
    assert result.status == "rejected"
    assert result.rejected_paths == ("/probability/semantics",)
    probability_check = [row for row in result.checks if row.category == "probability_semantics"][0]
    assert probability_check.status == "failed"


def test_payload_digest_mismatch_is_blocked_before_receipt_creation():
    schema_audit = audit()
    validation_report = report(schema_audit)
    changed = producer_payload()
    changed["temperature"]["value"] = 301.0
    with pytest.raises(ValueError, match="payload digest does not match"):
        receipt(schema_audit, validation_report, payload=changed)


def test_audit_digest_commit_path_and_consumer_identity_mismatches_are_blocked():
    first_audit = audit()
    validation_report = report(first_audit)
    other_audit = audit(commit="d" * 40, path="schemas/temperature-v2.json")
    with pytest.raises(ValueError, match="does not match external schema audit identity"):
        receipt(other_audit, validation_report)

    with pytest.raises(ValueError, match="consumer repository and commit must match"):
        receipt(first_audit, validation_report, consumer=consumer_endpoint("e" * 40))

    wrong_schema_consumer = consumer_endpoint()
    wrong_schema_consumer["schema_version"] = "other"
    with pytest.raises(ValueError, match="schema identity and version must match"):
        receipt(first_audit, validation_report, consumer=wrong_schema_consumer)


def test_validation_report_is_self_bound_and_requires_all_check_categories():
    validation_report = report()
    data = validation_report.model_dump()
    data["schema_repository_path"] = "schemas/other.json"
    with pytest.raises(ValueError, match="report identifier does not match"):
        PinnedSchemaValidationReport.model_validate(data)

    with pytest.raises(ValueError, match="all compatibility-check categories"):
        report(finding_rows=findings()[:-1])

import hashlib
import json

import pytest

from matintegrity.external_schema_audit import (
    ExternalSchemaAuditRecord,
    build_external_schema_audit_record,
    external_schema_compatibility_input,
)

COMMIT = "a" * 40
REPOSITORY = "example/schema-provider"
PATH = "schemas/thermal-result.schema.json"
URL = f"https://raw.githubusercontent.com/{REPOSITORY}/{COMMIT}/{PATH}"
SCHEMA_ID = "https://schemas.example.test/thermal-result"
SCHEMA_VERSION = "1.2.0"


def schema_bytes(**updates):
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "x-schema-version": SCHEMA_VERSION,
        "type": "object",
        "properties": {
            "asset/id": {"type": "string"},
            "temperature": {"type": "number"},
            "unit": {"const": "K"},
        },
        "required": ["unit", "asset/id", "temperature"],
        "additionalProperties": False,
    }
    schema.update(updates)
    return json.dumps(schema, ensure_ascii=False, separators=(",", ":")).encode()


def build(content=None, **updates):
    content = schema_bytes() if content is None else content
    arguments = {
        "source_url": URL,
        "repository_id": REPOSITORY,
        "pinned_commit": COMMIT,
        "repository_path": PATH,
        "schema_content": content,
        "expected_content_sha256": hashlib.sha256(content).hexdigest(),
        "expected_json_schema_id": SCHEMA_ID,
        "expected_json_schema_version": SCHEMA_VERSION,
        "limitations": (
            "This record does not redistribute or execute the external schema.",
            "Structural metadata does not qualify physical-model compatibility.",
        ),
    }
    arguments.update(updates)
    return build_external_schema_audit_record(**arguments)


def test_builder_keeps_only_deterministic_schema_metadata_and_helper_paths():
    first = build()
    second = build()
    assert first == second
    assert first.content_sha256 == hashlib.sha256(schema_bytes()).hexdigest()
    assert first.required_properties == ("asset/id", "temperature", "unit")
    assert first.top_level_properties == ("asset/id", "temperature", "unit")
    assert first.additional_properties is False
    assert first.network_download_performed is False
    assert first.external_repository_executed is False
    assert first.schema_qualification_claimed is False
    compatibility = external_schema_compatibility_input(first)
    assert compatibility["required_paths"] == ["/asset~1id", "/temperature", "/unit"]
    assert "schema_content" not in compatibility
    assert compatibility["source_content_sha256"] == first.content_sha256


def test_pinned_raw_byte_digest_mismatch_is_rejected():
    content = schema_bytes()
    with pytest.raises(ValueError, match="SHA-256 does not match"):
        build(content, expected_content_sha256="0" * 64)


def test_duplicate_json_key_and_duplicate_required_property_are_rejected():
    duplicate_key = (
        '{"$id":"https://schemas.example.test/thermal-result",'
        '"$id":"https://schemas.example.test/other",'
        '"x-schema-version":"1.2.0","properties":{},"required":[],"additionalProperties":false}'
    ).encode()
    with pytest.raises(ValueError, match="duplicate JSON object key"):
        build(duplicate_key)

    duplicate_required = schema_bytes(required=["unit", "unit"])
    with pytest.raises(ValueError, match="required properties must be unique"):
        build(duplicate_required)


def test_url_commit_path_schema_id_and_version_mismatches_are_rejected():
    wrong_path_url = URL.replace(PATH, "schemas/other.json")
    with pytest.raises(ValueError, match="commit or path does not match"):
        build(source_url=wrong_path_url)

    wrong_id = schema_bytes(**{"$id": "https://schemas.example.test/other"})
    with pytest.raises(ValueError, match=r"\$id does not match"):
        build(wrong_id)

    wrong_version = schema_bytes(**{"x-schema-version": "2.0.0"})
    with pytest.raises(ValueError, match="version does not match"):
        build(wrong_version)


def test_record_summary_identifier_and_digest_are_self_bound():
    record = build()
    data = record.model_dump()
    data["required_properties"] = ("temperature", "unit")
    with pytest.raises(ValueError, match="summary digest does not match"):
        ExternalSchemaAuditRecord.model_validate(data)

    data = record.model_dump()
    data["audit_id"] = f"external-schema-{'0' * 64}"
    with pytest.raises(ValueError, match="identifier does not match"):
        ExternalSchemaAuditRecord.model_validate(data)

    data = record.model_dump()
    data["audit_digest"] = "0" * 64
    with pytest.raises(ValueError, match="audit digest does not match"):
        ExternalSchemaAuditRecord.model_validate(data)

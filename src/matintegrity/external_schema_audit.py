"""Digest-bound audit summaries for pinned external JSON Schemas."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal
from urllib.parse import unquote, urlsplit

from pydantic import Field, ValidationInfo, model_validator

from .contracts import Contract, canonical_digest


class ExternalSchemaAuditRecord(Contract):
    """Metadata-only record for an externally hosted, pinned JSON Schema.

    The schema document itself is intentionally absent.  This record does not
    prove that the URL remains available or that the schema is correct for a
    physical or engineering use.
    """

    schema_version: Literal["matintegrity.external_schema_audit.v1"] = "matintegrity.external_schema_audit.v1"
    audit_id: str = Field(pattern=r"^external-schema-[a-f0-9]{64}$")
    source_url: str = Field(min_length=1)
    repository_id: str = Field(pattern=r"^[^/\s]+/[^/\s]+$")
    pinned_commit: str = Field(pattern=r"^[a-fA-F0-9]{40}$|^[a-fA-F0-9]{64}$")
    repository_path: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_byte_count: int = Field(ge=1)
    json_schema_id: str = Field(min_length=1)
    json_schema_version: str = Field(min_length=1)
    required_properties: tuple[str, ...]
    top_level_properties: tuple[str, ...]
    additional_properties: bool
    compatibility_summary_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    limitations: tuple[str, ...] = Field(min_length=1)
    network_download_performed: Literal[False] = False
    external_repository_executed: Literal[False] = False
    schema_qualification_claimed: Literal[False] = False
    physical_validation_claimed: Literal[False] = False
    audit_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def compatibility_summary(self) -> dict[str, Any]:
        return {
            "json_schema_id": self.json_schema_id,
            "json_schema_version": self.json_schema_version,
            "required_properties": list(self.required_properties),
            "top_level_properties": list(self.top_level_properties),
            "additional_properties": self.additional_properties,
        }

    def identity_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"audit_id", "audit_digest"})

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"audit_digest"})

    @model_validator(mode="after")
    def coherent_and_bound(self, info: ValidationInfo):
        _validate_repository_path(self.repository_path)
        _validate_github_raw_url(
            self.source_url,
            self.repository_id,
            self.pinned_commit,
            self.repository_path,
        )
        if tuple(sorted(set(self.required_properties))) != self.required_properties:
            raise ValueError("required schema properties must be unique and sorted")
        if tuple(sorted(set(self.top_level_properties))) != self.top_level_properties:
            raise ValueError("top-level schema properties must be unique and sorted")
        if not set(self.required_properties) <= set(self.top_level_properties):
            raise ValueError("required schema properties must be declared as top-level properties")
        if any(not value for value in (*self.required_properties, *self.top_level_properties)):
            raise ValueError("schema property names must be nonempty")
        if any(not value.strip() for value in self.limitations):
            raise ValueError("external-schema audit limitations must be nonempty statements")
        if canonical_digest(self.compatibility_summary()) != self.compatibility_summary_digest:
            raise ValueError("external-schema compatibility summary digest does not match metadata")
        if not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest")):
            expected_id = f"external-schema-{canonical_digest(self.identity_payload())}"
            if self.audit_id != expected_id:
                raise ValueError("external-schema audit identifier does not match canonical metadata")
            if self.audit_digest != canonical_digest(self.digest_payload()):
                raise ValueError("external-schema audit digest does not match canonical metadata")
        return self


def _validate_repository_path(path: str) -> None:
    if path.startswith("/") or "\\" in path:
        raise ValueError("external schema repository path must be a relative POSIX path")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("external schema repository path contains an invalid segment")


def _validate_github_raw_url(url: str, repository_id: str, commit: str, path: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "raw.githubusercontent.com":
        raise ValueError("external schema source URL must use GitHub raw HTTPS")
    if parsed.query or parsed.fragment or parsed.username or parsed.password or parsed.port:
        raise ValueError("external schema source URL cannot contain credentials, port, query or fragment")
    url_parts = [unquote(part) for part in parsed.path.split("/") if part]
    repository_parts = repository_id.split("/")
    expected = [*repository_parts, commit, *path.split("/")]
    if url_parts != expected:
        raise ValueError("GitHub raw URL repository, commit or path does not match pinned metadata")


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is not allowed: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key is not allowed: {key!r}")
        result[key] = value
    return result


def _decode_schema(schema_content: bytes) -> dict[str, Any]:
    try:
        text = schema_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("external schema content must be UTF-8 JSON") from exc
    try:
        decoded = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise ValueError("external schema content must be valid JSON") from exc
    if not isinstance(decoded, dict):
        raise ValueError("external JSON Schema must be a top-level object")
    return decoded


def build_external_schema_audit_record(
    *,
    source_url: str,
    repository_id: str,
    pinned_commit: str,
    repository_path: str,
    schema_content: bytes,
    expected_content_sha256: str,
    expected_json_schema_id: str,
    expected_json_schema_version: str,
    limitations: tuple[str, ...],
) -> ExternalSchemaAuditRecord:
    """Audit caller-supplied bytes without downloading, executing or redistributing them."""

    _validate_repository_path(repository_path)
    _validate_github_raw_url(source_url, repository_id, pinned_commit, repository_path)
    actual_sha256 = hashlib.sha256(schema_content).hexdigest()
    if actual_sha256 != expected_content_sha256:
        raise ValueError("external schema content SHA-256 does not match the pinned digest")
    schema = _decode_schema(schema_content)
    schema_id = schema.get("$id")
    if schema_id != expected_json_schema_id:
        raise ValueError("external JSON Schema $id does not match the expected schema identity")
    schema_version = schema.get("x-schema-version")
    if schema_version != expected_json_schema_version:
        raise ValueError("external JSON Schema version does not match the expected version")
    properties = schema.get("properties")
    if not isinstance(properties, dict) or any(not isinstance(key, str) or not key for key in properties):
        raise ValueError("external JSON Schema requires a top-level properties object")
    required = schema.get("required", [])
    if not isinstance(required, list) or any(not isinstance(key, str) or not key for key in required):
        raise ValueError("external JSON Schema required must be a list of nonempty property names")
    if len(set(required)) != len(required):
        raise ValueError("external JSON Schema required properties must be unique")
    if not set(required) <= set(properties):
        raise ValueError("external JSON Schema required properties must exist in properties")
    additional_properties = schema.get("additionalProperties")
    if not isinstance(additional_properties, bool):
        raise ValueError("external JSON Schema additionalProperties must be explicitly boolean")
    required_properties = tuple(sorted(required))
    top_level_properties = tuple(sorted(properties))
    compatibility_summary = {
        "json_schema_id": schema_id,
        "json_schema_version": schema_version,
        "required_properties": list(required_properties),
        "top_level_properties": list(top_level_properties),
        "additional_properties": additional_properties,
    }
    content = {
        "source_url": source_url,
        "repository_id": repository_id,
        "pinned_commit": pinned_commit,
        "repository_path": repository_path,
        "content_sha256": actual_sha256,
        "content_byte_count": len(schema_content),
        "json_schema_id": schema_id,
        "json_schema_version": schema_version,
        "required_properties": required_properties,
        "top_level_properties": top_level_properties,
        "additional_properties": additional_properties,
        "compatibility_summary_digest": canonical_digest(compatibility_summary),
        "limitations": limitations,
    }
    unsigned = ExternalSchemaAuditRecord.model_validate(
        {
            **content,
            "audit_id": f"external-schema-{'0' * 64}",
            "audit_digest": "0" * 64,
        },
        context={"allow_unbound_digest": True},
    )
    audit_id = f"external-schema-{canonical_digest(unsigned.identity_payload())}"
    bound_id = ExternalSchemaAuditRecord.model_validate(
        {**content, "audit_id": audit_id, "audit_digest": "0" * 64},
        context={"allow_unbound_digest": True},
    )
    return ExternalSchemaAuditRecord.model_validate(
        {
            **content,
            "audit_id": audit_id,
            "audit_digest": canonical_digest(bound_id.digest_payload()),
        }
    )


def external_schema_compatibility_input(record: ExternalSchemaAuditRecord) -> dict[str, Any]:
    """Return a content-free compatibility input derived from a validated audit record."""

    return {
        "external_schema_audit_id": record.audit_id,
        "external_schema_audit_digest": record.audit_digest,
        "source_content_sha256": record.content_sha256,
        "json_schema_id": record.json_schema_id,
        "json_schema_version": record.json_schema_version,
        "required_paths": [
            f"/{name.replace('~', '~0').replace('/', '~1')}" for name in record.required_properties
        ],
        "top_level_property_paths": [
            f"/{name.replace('~', '~0').replace('/', '~1')}" for name in record.top_level_properties
        ],
        "additional_properties": record.additional_properties,
        "compatibility_summary_digest": record.compatibility_summary_digest,
    }

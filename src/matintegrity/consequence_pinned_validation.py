"""Offline validation of pinned consequence-provider requests against caller bytes."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import Field

from .consequence_pinned_adapter import (
    PINNED_COMMIT,
    PINNED_PROVIDER_REQUEST_PATH,
    PINNED_PROVIDER_REQUEST_SCHEMA_SHA256,
    PinnedProviderRequestEnvelope,
)
from .contracts import Contract, canonical_digest


class PinnedSchemaValidationIssue(Contract):
    instance_path: str
    schema_path: str
    keyword: str = Field(min_length=1)
    message: str = Field(min_length=1)


class PinnedProviderRequestValidationReport(Contract):
    schema_version: Literal["matintegrity.pinned_provider_request_validation.v1"] = (
        "matintegrity.pinned_provider_request_validation.v1"
    )
    repository_commit: Literal["4106da0020196fcf61c8b6264ae0598e63a881a1"] = PINNED_COMMIT
    provider_request_schema_path: Literal["contracts/ccps.provider_request.v1.schema.json"] = (
        PINNED_PROVIDER_REQUEST_PATH
    )
    expected_schema_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    observed_schema_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    envelope_schema_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    handoff_payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    request_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observed_request_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    schema_draft: str | None = None
    validator_engine: Literal["matintegrity_json_schema_subset_v1"] = "matintegrity_json_schema_subset_v1"
    status: Literal["valid", "invalid"]
    schema_digest_valid: bool
    request_digest_valid: bool
    issue_count: int = Field(ge=0)
    issues: tuple[PinnedSchemaValidationIssue, ...]
    raw_schema_stored_or_distributed: Literal[False] = False
    remote_execution_performed: Literal[False] = False
    validation_report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class PinnedProviderRequestSchemaError(ValueError):
    """Raised with a structured report when pinned schema validation rejects data."""

    def __init__(self, report: PinnedProviderRequestValidationReport):
        self.report = report
        summary = "; ".join(issue.message for issue in report.issues[:3])
        super().__init__(summary or "pinned provider request schema validation failed")


def _pointer(root: dict[str, Any], reference: str) -> Any:
    if not reference.startswith("#/"):
        raise ValueError("only local JSON Schema references are supported")
    value: Any = root
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[token]
    return value


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    return False


def _format_matches(value: str, format_name: str) -> bool:
    if format_name in {"uri", "uri-reference"}:
        parsed = urlparse(value)
        return bool(parsed.scheme) if format_name == "uri" else bool(value)
    if format_name == "date-time":
        return bool(
            re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value)
        )
    return False


def _validate(
    value: Any,
    schema: dict[str, Any],
    root: dict[str, Any],
    instance_path: str,
    schema_path: str,
    issues: list[dict[str, str]],
) -> None:
    if "$ref" in schema:
        reference = schema["$ref"]
        _validate(value, _pointer(root, reference), root, instance_path, reference[1:], issues)
        return
    if "anyOf" in schema:
        alternatives = []
        for index, alternative in enumerate(schema["anyOf"]):
            candidate: list[dict[str, str]] = []
            _validate(
                value,
                alternative,
                root,
                instance_path,
                f"{schema_path}/anyOf/{index}",
                candidate,
            )
            if not candidate:
                break
            alternatives.extend(candidate)
        else:
            issues.append(
                {
                    "instance_path": instance_path,
                    "schema_path": f"{schema_path}/anyOf",
                    "keyword": "anyOf",
                    "message": "value does not satisfy any allowed schema alternative",
                }
            )
        return
    expected_type = schema.get("type")
    if expected_type is not None and not _type_matches(value, expected_type):
        issues.append(
            {
                "instance_path": instance_path,
                "schema_path": f"{schema_path}/type",
                "keyword": "type",
                "message": f"expected JSON type {expected_type}",
            }
        )
        return
    if "const" in schema and value != schema["const"]:
        issues.append(
            {
                "instance_path": instance_path,
                "schema_path": f"{schema_path}/const",
                "keyword": "const",
                "message": "value differs from the required constant",
            }
        )
    if "enum" in schema and value not in schema["enum"]:
        issues.append(
            {
                "instance_path": instance_path,
                "schema_path": f"{schema_path}/enum",
                "keyword": "enum",
                "message": "value is not one of the allowed enum members",
            }
        )
    if isinstance(value, dict):
        required = schema.get("required", [])
        for name in required:
            if name not in value:
                issues.append(
                    {
                        "instance_path": instance_path,
                        "schema_path": f"{schema_path}/required",
                        "keyword": "required",
                        "message": f"required property {name!r} is missing",
                    }
                )
        properties = schema.get("properties", {})
        for name, item in value.items():
            child_path = f"{instance_path}/{name}"
            if name in properties:
                _validate(
                    item,
                    properties[name],
                    root,
                    child_path,
                    f"{schema_path}/properties/{name}",
                    issues,
                )
            elif schema.get("additionalProperties") is False:
                issues.append(
                    {
                        "instance_path": child_path,
                        "schema_path": f"{schema_path}/additionalProperties",
                        "keyword": "additionalProperties",
                        "message": f"additional property {name!r} is not allowed",
                    }
                )
            elif isinstance(schema.get("additionalProperties"), dict):
                _validate(
                    item,
                    schema["additionalProperties"],
                    root,
                    child_path,
                    f"{schema_path}/additionalProperties",
                    issues,
                )
    if isinstance(value, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate(
                    item,
                    item_schema,
                    root,
                    f"{instance_path}/{index}",
                    f"{schema_path}/items",
                    issues,
                )
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            issues.append(
                {
                    "instance_path": instance_path,
                    "schema_path": f"{schema_path}/minLength",
                    "keyword": "minLength",
                    "message": "string is shorter than the schema minimum",
                }
            )
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            issues.append(
                {
                    "instance_path": instance_path,
                    "schema_path": f"{schema_path}/maxLength",
                    "keyword": "maxLength",
                    "message": "string is longer than the schema maximum",
                }
            )
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            issues.append(
                {
                    "instance_path": instance_path,
                    "schema_path": f"{schema_path}/pattern",
                    "keyword": "pattern",
                    "message": "string does not match the required pattern",
                }
            )
        if "format" in schema and not _format_matches(value, schema["format"]):
            issues.append(
                {
                    "instance_path": instance_path,
                    "schema_path": f"{schema_path}/format",
                    "keyword": "format",
                    "message": f"string does not match format {schema['format']}",
                }
            )
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            issues.append(
                {
                    "instance_path": instance_path,
                    "schema_path": f"{schema_path}/minimum",
                    "keyword": "minimum",
                    "message": "number is below the schema minimum",
                }
            )
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            issues.append(
                {
                    "instance_path": instance_path,
                    "schema_path": f"{schema_path}/exclusiveMinimum",
                    "keyword": "exclusiveMinimum",
                    "message": "number is not above the exclusive schema minimum",
                }
            )


def _report(
    envelope: PinnedProviderRequestEnvelope,
    observed_schema_sha256: str,
    observed_request_digest: str,
    schema_draft: str | None,
    issues: list[dict[str, str]],
) -> PinnedProviderRequestValidationReport:
    schema_digest_valid = observed_schema_sha256 == PINNED_PROVIDER_REQUEST_SCHEMA_SHA256
    request_digest_valid = observed_request_digest == envelope.request_digest
    issue_models = tuple(PinnedSchemaValidationIssue(**row) for row in issues)
    values = {
        "expected_schema_sha256": PINNED_PROVIDER_REQUEST_SCHEMA_SHA256,
        "observed_schema_sha256": observed_schema_sha256,
        "envelope_schema_sha256": envelope.provider_request_schema_sha256,
        "handoff_payload_digest": envelope.handoff_payload_digest,
        "request_digest": envelope.request_digest,
        "observed_request_digest": observed_request_digest,
        "schema_draft": schema_draft,
        "status": ("valid" if schema_digest_valid and request_digest_valid and not issues else "invalid"),
        "schema_digest_valid": schema_digest_valid,
        "request_digest_valid": request_digest_valid,
        "issue_count": len(issue_models),
        "issues": issue_models,
    }
    digest_values = {
        **values,
        "issues": [row.model_dump(mode="json") for row in issue_models],
    }
    return PinnedProviderRequestValidationReport(
        **values,
        validation_report_digest=canonical_digest(digest_values),
    )


def validate_pinned_provider_request(
    envelope: PinnedProviderRequestEnvelope,
    raw_provider_request_schema: bytes,
) -> PinnedProviderRequestValidationReport:
    """Validate offline against exact caller bytes; never retain or execute the schema remotely."""

    if not isinstance(raw_provider_request_schema, bytes):
        raise TypeError("raw provider-request schema must be bytes")
    observed_schema_sha256 = hashlib.sha256(raw_provider_request_schema).hexdigest()
    observed_request_digest = canonical_digest(envelope.request)
    issues: list[dict[str, str]] = []
    schema: dict[str, Any] | None = None
    schema_draft = None
    if observed_schema_sha256 != PINNED_PROVIDER_REQUEST_SCHEMA_SHA256:
        issues.append(
            {
                "instance_path": "",
                "schema_path": "",
                "keyword": "schema_sha256",
                "message": "raw provider-request schema bytes do not match the pinned SHA-256",
            }
        )
    elif envelope.provider_request_schema_sha256 != PINNED_PROVIDER_REQUEST_SCHEMA_SHA256:
        issues.append(
            {
                "instance_path": "",
                "schema_path": "",
                "keyword": "envelope_schema_sha256",
                "message": "envelope schema digest differs from the pinned SHA-256",
            }
        )
    else:
        try:
            decoded = json.loads(raw_provider_request_schema.decode("utf-8"))
            if not isinstance(decoded, dict):
                raise ValueError("schema root is not an object")
            schema = decoded
            schema_draft = schema.get("$schema")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            issues.append(
                {
                    "instance_path": "",
                    "schema_path": "",
                    "keyword": "schema_parse",
                    "message": f"raw provider-request schema is not valid UTF-8 JSON: {error}",
                }
            )
    if observed_request_digest != envelope.request_digest:
        issues.append(
            {
                "instance_path": "",
                "schema_path": "",
                "keyword": "request_digest",
                "message": "provider request digest does not match its content",
            }
        )
    if schema is not None:
        _validate(envelope.request, schema, schema, "", "", issues)
    report = _report(
        envelope,
        observed_schema_sha256,
        observed_request_digest,
        schema_draft,
        issues,
    )
    if report.status != "valid":
        raise PinnedProviderRequestSchemaError(report)
    return report

"""In-memory validation against the caller-supplied pinned API schema bytes."""

from __future__ import annotations

import hashlib
import json
from importlib.util import find_spec
from typing import Any, Literal

from pydantic import Field

from .api581_pinned_adapter import (
    PINNED_COMMIT,
    PINNED_REPOSITORY,
    PINNED_SCHEMA_PATH,
    PINNED_SCHEMA_SHA256,
    TARGET_ADDITIONAL_PROPERTIES,
    TARGET_CALCULATION_ID,
    TARGET_REQUIRED_FIELDS,
    PinnedPofMethodSelectionRequest,
)
from .contracts import Contract, canonical_digest

_METHODS = (
    "structural_reliability",
    "statistical_generic_data",
    "expert_judgment",
    "combined",
)


class Api581PinnedSchemaValidationReport(Contract):
    repository: Literal["lyullee/api581-risk-analysis"] = PINNED_REPOSITORY
    commit: Literal["7c8badb829f84b19c7b84d07fbc476601d9194eb"] = PINNED_COMMIT
    schema_path: Literal["docs/python-api.schema.json"] = PINNED_SCHEMA_PATH
    schema_sha256: Literal["bcb2ee8ee001d26e7ca40fe69a23f31358532fd13b29634d3349a9296054b51a"] = (
        PINNED_SCHEMA_SHA256
    )
    calculation_id: Literal["frequency/pof-method-selection"] = TARGET_CALCULATION_ID
    required_fields: tuple[str, ...] = TARGET_REQUIRED_FIELDS
    additional_properties: Literal[False] = TARGET_ADDITIONAL_PROPERTIES
    request_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    validation_engine: Literal["jsonschema", "independent_minimal"]
    valid: Literal[True] = True


def _select_and_check_contract(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError("pinned schema document must be a JSON object")
    contract = document.get(TARGET_CALCULATION_ID)
    if not isinstance(contract, dict):
        raise ValueError("pinned calculation contract is missing")
    schema = contract.get("input_schema")
    if not isinstance(schema, dict):
        raise ValueError("pinned calculation input_schema is missing")
    if schema.get("type") != "object":
        raise ValueError("pinned input schema type mismatch")
    if schema.get("additionalProperties") is not TARGET_ADDITIONAL_PROPERTIES:
        raise ValueError("pinned input additionalProperties mismatch")
    required = schema.get("required")
    if not isinstance(required, list) or tuple(required) != TARGET_REQUIRED_FIELDS:
        raise ValueError("pinned input required fields mismatch")
    properties = schema.get("properties")
    if not isinstance(properties, dict) or tuple(properties) != TARGET_REQUIRED_FIELDS:
        raise ValueError("pinned input property fields mismatch")
    method = properties.get("method")
    basis = properties.get("qualification_basis")
    uncertainty = properties.get("uncertainty_quantified")
    if not isinstance(method, dict) or tuple(method.get("enum", ())) != _METHODS:
        raise ValueError("pinned method enum mismatch")
    if not isinstance(basis, dict) or any(
        basis.get(key) != expected
        for key, expected in (("type", "string"), ("minLength", 1), ("maxLength", 1000))
    ):
        raise ValueError("pinned qualification basis constraints mismatch")
    if not isinstance(uncertainty, dict) or uncertainty.get("type") != "boolean":
        raise ValueError("pinned uncertainty flag constraint mismatch")
    return schema


def _independent_minimal_validate(instance: Any, schema: dict[str, Any]) -> None:
    if not isinstance(instance, dict):
        raise ValueError("request JSON must be an object")
    properties = schema["properties"]
    keys = set(instance)
    required = set(schema["required"])
    if not required.issubset(keys):
        raise ValueError("request JSON is missing required fields")
    if schema["additionalProperties"] is False and not keys.issubset(properties):
        raise ValueError("request JSON contains additional properties")
    method = instance.get("method")
    if not isinstance(method, str) or method not in properties["method"]["enum"]:
        raise ValueError("request method is outside the pinned enum")
    basis = instance.get("qualification_basis")
    if not isinstance(basis, str) or not 1 <= len(basis) <= 1000:
        raise ValueError("request qualification_basis violates pinned length constraints")
    if not isinstance(instance.get("uncertainty_quantified"), bool):
        raise ValueError("request uncertainty_quantified must be boolean")


def validate_pinned_method_selection_request(
    raw_schema_bytes: bytes,
    request: PinnedPofMethodSelectionRequest,
) -> Api581PinnedSchemaValidationReport:
    """Validate one request without retaining or redistributing the raw schema."""

    if not isinstance(raw_schema_bytes, bytes):
        raise TypeError("raw_schema_bytes must be bytes")
    observed_digest = hashlib.sha256(raw_schema_bytes).hexdigest()
    if observed_digest != PINNED_SCHEMA_SHA256:
        raise ValueError("caller-supplied schema SHA256 does not match the pinned digest")
    try:
        document = json.loads(raw_schema_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("caller-supplied schema is not valid UTF-8 JSON") from exc
    schema = _select_and_check_contract(document)
    instance = request.model_dump(mode="json")

    if find_spec("jsonschema") is not None:
        from jsonschema import validate  # type: ignore[import-not-found]

        validate(instance=instance, schema=schema)
        engine: Literal["jsonschema", "independent_minimal"] = "jsonschema"
    else:
        _independent_minimal_validate(instance, schema)
        engine = "independent_minimal"

    return Api581PinnedSchemaValidationReport(
        request_digest=canonical_digest(instance),
        validation_engine=engine,
    )

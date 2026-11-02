import hashlib
import json
from copy import deepcopy

import pytest

import matintegrity.consequence_pinned_validation as validation_module
from matintegrity.consequence_pinned_adapter import (
    PINNED_COMMIT,
    PINNED_PROVIDER_REQUEST_PATH,
    PINNED_PROVIDER_REQUEST_REQUIRED,
    PinnedProviderRequestEnvelope,
)
from matintegrity.consequence_pinned_validation import (
    PinnedProviderRequestSchemaError,
    validate_pinned_provider_request,
)
from matintegrity.contracts import canonical_digest

SHA = "a" * 64


def schema_bytes():
    identifier = {"type": "string", "minLength": 1, "maxLength": 160}
    digest = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": {
            "Evidence": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": identifier,
                    "kind": {
                        "type": "string",
                        "enum": ["public_reference", "synthetic", "user_supplied"],
                    },
                    "citation": identifier,
                    "locator": identifier,
                },
                "required": ["id", "kind", "citation", "locator"],
            }
        },
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "string", "const": "ccps.provider-request.v1"},
            "context": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "asset_id": identifier,
                    "scenario_id": identifier,
                    "operating_case_id": identifier,
                    "mode": {
                        "type": "string",
                        "enum": ["synthetic", "engineering_review_required"],
                    },
                    "evidence": {"type": "array", "items": {"$ref": "#/$defs/Evidence"}},
                },
                "required": ["asset_id", "scenario_id", "operating_case_id"],
            },
            "source": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "schema_version": {
                        "type": "string",
                        "const": "ccps.external-source.v1",
                    },
                    "asset_id": identifier,
                    "scenario_id": identifier,
                    "operating_case_id": identifier,
                    "origin": {
                        "type": "string",
                        "enum": ["api581", "prism", "user_supplied"],
                    },
                    "source_digest": digest,
                    "source_code_digest": digest,
                    "evidence_ids": {"type": "array", "items": identifier},
                    "phase": {
                        "type": "string",
                        "enum": ["vapour", "liquid", "two_phase"],
                    },
                    "mass_rate_kg_s": {"type": "number", "minimum": 0},
                    "duration_s": {"type": "number", "minimum": 0},
                    "released_mass_kg": {"type": "number", "minimum": 0},
                    "history_basis": {"type": "string", "const": "constant_rate"},
                },
                "required": [
                    "asset_id",
                    "scenario_id",
                    "operating_case_id",
                    "origin",
                    "source_digest",
                    "source_code_digest",
                    "evidence_ids",
                    "phase",
                    "mass_rate_kg_s",
                    "duration_s",
                    "released_mass_kg",
                    "history_basis",
                ],
            },
            "engine": {"type": "string", "enum": ["api581", "prism", "user_supplied"]},
            "model_id": identifier,
            "expected_engine_code_digest": digest,
            "receptor_id": identifier,
            "distance_m": {"type": "number", "exclusiveMinimum": 0},
            "quantity": {
                "type": "string",
                "enum": ["concentration_kg_m3", "heat_flux_w_m2", "overpressure_pa"],
            },
            "settings": {
                "type": "object",
                "additionalProperties": True,
                "properties": {"callback_url": {"type": "string", "format": "uri"}},
            },
        },
        "required": sorted(PINNED_PROVIDER_REQUEST_REQUIRED),
    }
    return json.dumps(schema, sort_keys=True, separators=(",", ":")).encode()


def request():
    return {
        "schema_version": "ccps.provider-request.v1",
        "context": {
            "asset_id": "asset-1",
            "scenario_id": "scenario-1",
            "operating_case_id": "case-1",
            "mode": "engineering_review_required",
            "evidence": [
                {
                    "id": "evidence-1",
                    "kind": "user_supplied",
                    "citation": "caller source term",
                    "locator": "record-1",
                }
            ],
        },
        "source": {
            "schema_version": "ccps.external-source.v1",
            "asset_id": "asset-1",
            "scenario_id": "scenario-1",
            "operating_case_id": "case-1",
            "origin": "user_supplied",
            "source_digest": SHA,
            "source_code_digest": SHA,
            "evidence_ids": ["evidence-1"],
            "phase": "vapour",
            "mass_rate_kg_s": 2.0,
            "duration_s": 10.0,
            "released_mass_kg": 20.0,
            "history_basis": "constant_rate",
        },
        "engine": "user_supplied",
        "model_id": "provider-model-1",
        "expected_engine_code_digest": SHA,
        "receptor_id": "receptor-1",
        "distance_m": 25.0,
        "quantity": "concentration_kg_m3",
        "settings": {"callback_url": "https://example.invalid/result"},
    }


def envelope(value, schema_sha, request_digest=None):
    return PinnedProviderRequestEnvelope.model_construct(
        repository="lyullee/process-risk-consequence-toolkit",
        commit=PINNED_COMMIT,
        provider_request_schema_path=PINNED_PROVIDER_REQUEST_PATH,
        provider_request_schema_sha256=schema_sha,
        provider_request_required=tuple(sorted(PINNED_PROVIDER_REQUEST_REQUIRED)),
        provider_request_additional_properties=False,
        handoff_payload_digest=SHA,
        request=value,
        request_digest=request_digest or canonical_digest(value),
        wall_loss_to_opening_conversion_performed=False,
        consequence_to_failure_probability_conversion_performed=False,
    )


def pinned(monkeypatch):
    raw = schema_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    monkeypatch.setattr(validation_module, "PINNED_PROVIDER_REQUEST_SCHEMA_SHA256", digest)
    return raw, digest


def test_validates_request_and_preserves_pin_and_digest_report(monkeypatch):
    raw, digest = pinned(monkeypatch)
    report = validate_pinned_provider_request(envelope(request(), digest), raw)
    assert report.status == "valid"
    assert report.repository_commit == PINNED_COMMIT
    assert report.provider_request_schema_path == PINNED_PROVIDER_REQUEST_PATH
    assert report.expected_schema_sha256 == digest
    assert report.observed_schema_sha256 == digest
    assert report.request_digest_valid
    assert report.issue_count == 0
    assert not report.raw_schema_stored_or_distributed
    assert not report.remote_execution_performed


def test_rejects_raw_schema_bytes_that_do_not_match_pinned_digest(monkeypatch):
    raw, digest = pinned(monkeypatch)
    with pytest.raises(PinnedProviderRequestSchemaError) as caught:
        validate_pinned_provider_request(envelope(request(), digest), raw + b"\n")
    assert caught.value.report.issues[0].keyword == "schema_sha256"
    assert not caught.value.report.schema_digest_valid


@pytest.mark.parametrize(
    ("mutation", "keyword"),
    [
        (lambda value: value.pop("source"), "required"),
        (lambda value: value.update({"unexpected": True}), "additionalProperties"),
        (lambda value: value.update({"engine": "unknown"}), "enum"),
        (lambda value: value.update({"expected_engine_code_digest": "not-a-digest"}), "pattern"),
        (
            lambda value: value["settings"].update({"callback_url": "not an absolute URI"}),
            "format",
        ),
    ],
)
def test_rejects_required_closed_enum_pattern_and_format_mismatch(monkeypatch, mutation, keyword):
    raw, digest = pinned(monkeypatch)
    value = deepcopy(request())
    mutation(value)
    with pytest.raises(PinnedProviderRequestSchemaError) as caught:
        validate_pinned_provider_request(envelope(value, digest), raw)
    assert keyword in {issue.keyword for issue in caught.value.report.issues}


def test_rejects_stale_request_digest(monkeypatch):
    raw, digest = pinned(monkeypatch)
    with pytest.raises(PinnedProviderRequestSchemaError) as caught:
        validate_pinned_provider_request(envelope(request(), digest, request_digest="b" * 64), raw)
    assert "request_digest" in {issue.keyword for issue in caught.value.report.issues}
    assert not caught.value.report.request_digest_valid

"""Pinned adapter for one reviewed process-consequence provider request schema."""

from __future__ import annotations

import json
import math
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .consequence_exchange import ConsequenceScenarioHandoff
from .contracts import Contract, Nonnegative, Positive, canonical_digest, check_finite

PINNED_REPOSITORY = "lyullee/process-risk-consequence-toolkit"
PINNED_COMMIT = "4106da0020196fcf61c8b6264ae0598e63a881a1"
PINNED_PROVIDER_REQUEST_PATH = "contracts/ccps.provider_request.v1.schema.json"
PINNED_PROVIDER_REQUEST_SCHEMA_SHA256 = "cc45aaa17c6c5c704cfec818fb969afc78e02ffa53f56e5aa625040bfea5c605"
PINNED_PROVIDER_REQUEST_REQUIRED = frozenset(
    {
        "context",
        "source",
        "engine",
        "model_id",
        "expected_engine_code_digest",
        "receptor_id",
        "distance_m",
        "quantity",
        "settings",
    }
)
PINNED_PROVIDER_REQUEST_PROPERTIES = PINNED_PROVIDER_REQUEST_REQUIRED | {"schema_version"}
PINNED_PROVIDER_REQUEST_ADDITIONAL_PROPERTIES = False
MATINTEGRITY_SETTINGS_KEY = "matintegrity_handoff_v1"


class PinnedProviderEvidence(Contract):
    id: str = Field(min_length=1, max_length=160)
    kind: Literal["public_reference", "synthetic", "user_supplied"]
    citation: str = Field(min_length=1, max_length=160)
    locator: str = Field(min_length=1, max_length=160)
    sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    url: str | None = None


class PinnedExternalSourceTerm(Contract):
    asset_id: str = Field(min_length=1, max_length=160)
    scenario_id: str = Field(min_length=1, max_length=160)
    operating_case_id: str = Field(min_length=1, max_length=160)
    origin: Literal["api581", "prism", "user_supplied"]
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_code_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_ids: tuple[str, ...]
    phase: Literal["vapour", "liquid", "two_phase"]
    mass_rate_kg_s: Nonnegative
    duration_s: Nonnegative
    released_mass_kg: Nonnegative
    history_basis: Literal["constant_rate"] = "constant_rate"

    @model_validator(mode="after")
    def complete_constant_history(self):
        if len(self.evidence_ids) != len(set(self.evidence_ids)) or any(
            not value or len(value) > 160 for value in self.evidence_ids
        ):
            raise ValueError("external-source evidence IDs must be unique strings of length 1..160")
        expected = self.mass_rate_kg_s * self.duration_s
        if not math.isclose(self.released_mass_kg, expected, rel_tol=1e-12, abs_tol=1e-15):
            raise ValueError("constant-rate released mass must equal mass rate times duration")
        return self


class PinnedProviderRequestOptions(Contract):
    operating_case_id: str = Field(min_length=1, max_length=160)
    context_mode: Literal["synthetic", "engineering_review_required"]
    evidence: tuple[PinnedProviderEvidence, ...] = ()
    source: PinnedExternalSourceTerm
    engine: Literal["api581", "prism", "user_supplied"]
    model_id: str = Field(min_length=1, max_length=160)
    expected_engine_code_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    receptor_id: str = Field(min_length=1, max_length=160)
    distance_m: Positive
    quantity: Literal["concentration_kg_m3", "heat_flux_w_m2", "overpressure_pa"]
    provider_settings: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider_settings")
    @classmethod
    def finite_unreserved_settings(cls, value):
        if MATINTEGRITY_SETTINGS_KEY in value:
            raise ValueError(f"{MATINTEGRITY_SETTINGS_KEY} is reserved by the pinned adapter")
        check_finite(value)
        json.dumps(value, allow_nan=False)
        return value

    @model_validator(mode="after")
    def coherent_evidence_and_source(self):
        evidence_ids = [row.id for row in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("provider-request evidence IDs must be unique")
        if not set(self.source.evidence_ids).issubset(evidence_ids):
            raise ValueError("all external-source evidence IDs must exist in context evidence")
        if self.operating_case_id != self.source.operating_case_id:
            raise ValueError("source and request operating-case IDs must match")
        return self


class PinnedProviderRequestEnvelope(Contract):
    adapter_schema_version: Literal["matintegrity.consequence_pinned_adapter.v1"] = (
        "matintegrity.consequence_pinned_adapter.v1"
    )
    repository: Literal["lyullee/process-risk-consequence-toolkit"] = PINNED_REPOSITORY
    commit: Literal["4106da0020196fcf61c8b6264ae0598e63a881a1"] = PINNED_COMMIT
    provider_request_schema_path: Literal["contracts/ccps.provider_request.v1.schema.json"] = (
        PINNED_PROVIDER_REQUEST_PATH
    )
    provider_request_schema_sha256: Literal[
        "cc45aaa17c6c5c704cfec818fb969afc78e02ffa53f56e5aa625040bfea5c605"
    ] = PINNED_PROVIDER_REQUEST_SCHEMA_SHA256
    provider_request_required: tuple[str, ...]
    provider_request_additional_properties: Literal[False] = False
    handoff_payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    request: dict[str, Any]
    request_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    wall_loss_to_opening_conversion_performed: Literal[False] = False
    consequence_to_failure_probability_conversion_performed: Literal[False] = False

    @model_validator(mode="after")
    def pinned_shape_and_digest(self):
        if set(self.provider_request_required) != PINNED_PROVIDER_REQUEST_REQUIRED:
            raise ValueError("pinned provider-request required fields differ from reviewed schema")
        if set(self.request) != PINNED_PROVIDER_REQUEST_PROPERTIES:
            raise ValueError("provider request fields differ from the closed reviewed schema")
        if not PINNED_PROVIDER_REQUEST_REQUIRED.issubset(self.request):
            raise ValueError("provider request omits a required reviewed field")
        if self.request.get("schema_version") != "ccps.provider-request.v1":
            raise ValueError("provider request schema version differs from the pinned contract")
        context = self.request.get("context")
        source = self.request.get("source")
        if not isinstance(context, dict) or set(context) != {
            "asset_id",
            "scenario_id",
            "operating_case_id",
            "mode",
            "evidence",
        }:
            raise ValueError("provider request context differs from the reviewed closed object")
        if not isinstance(source, dict) or set(source) != {
            "schema_version",
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
        }:
            raise ValueError("provider request source differs from the reviewed closed object")
        settings = self.request.get("settings")
        if not isinstance(settings, dict) or MATINTEGRITY_SETTINGS_KEY not in settings:
            raise ValueError("provider settings omit the lossless MatIntegrity handoff extension")
        extension = settings[MATINTEGRITY_SETTINGS_KEY]
        if not isinstance(extension, dict) or canonical_digest(extension) != self.handoff_payload_digest:
            raise ValueError("provider settings do not preserve the complete MatIntegrity handoff")
        check_finite(self.request)
        if canonical_digest(self.request) != self.request_digest:
            raise ValueError("pinned provider request digest does not match its content")
        return self


def export_pinned_provider_request(
    handoff: ConsequenceScenarioHandoff,
    options: PinnedProviderRequestOptions,
) -> PinnedProviderRequestEnvelope:
    """Export a pinned provider request without deriving a source term or relabelling probability."""

    if handoff.handoff_status != "ready":
        raise ValueError("only a ready consequence handoff can be exported")
    if (options.source.asset_id, options.source.scenario_id) != (
        handoff.event.asset_id,
        handoff.scenario_id,
    ):
        raise ValueError("external source asset and scenario must match the handoff")
    if handoff.release.release_duration_s is not None and not math.isclose(
        options.source.duration_s,
        handoff.release.release_duration_s,
        rel_tol=1e-12,
        abs_tol=1e-15,
    ):
        raise ValueError("external-source duration differs from the handoff release duration")

    extension = handoff.model_dump(mode="json")
    request = {
        "schema_version": "ccps.provider-request.v1",
        "context": {
            "asset_id": handoff.event.asset_id,
            "scenario_id": handoff.scenario_id,
            "operating_case_id": options.operating_case_id,
            "mode": options.context_mode,
            "evidence": [row.model_dump(mode="json") for row in options.evidence],
        },
        "source": {
            "schema_version": "ccps.external-source.v1",
            **options.source.model_dump(mode="json"),
        },
        "engine": options.engine,
        "model_id": options.model_id,
        "expected_engine_code_digest": options.expected_engine_code_digest,
        "receptor_id": options.receptor_id,
        "distance_m": options.distance_m,
        "quantity": options.quantity,
        "settings": {
            **options.provider_settings,
            MATINTEGRITY_SETTINGS_KEY: extension,
        },
    }
    return PinnedProviderRequestEnvelope(
        provider_request_required=tuple(sorted(PINNED_PROVIDER_REQUEST_REQUIRED)),
        handoff_payload_digest=canonical_digest(extension),
        request=request,
        request_digest=canonical_digest(request),
    )

"""Pinned adapter for CCPS Toolkit's time-varying dense gas release-history request.

This module builds a reviewed request only. It does not execute the external
consequence engine, derive a release history from wall loss, or send event
probability to the conditional consequence provider.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Literal

from pydantic import Field, StrictInt, StrictStr, model_validator

from .consequence_exchange import ConsequenceScenarioHandoff
from .contracts import Contract, Fraction, Nonnegative, Positive, ProbabilityMeaning, canonical_digest, check_finite

PINNED_REPOSITORY = "lyullee/process-risk-consequence-toolkit"
PINNED_COMMIT = "4106da0020196fcf61c8b6264ae0598e63a881a1"
PINNED_REQUEST_SCHEMA_PATH = "contracts/ccps.release_history_request.v1.schema.json"
PINNED_RESULT_SCHEMA_PATH = "contracts/ccps.release_history_result.v1.schema.json"
PINNED_REQUEST_SCHEMA_SHA256 = "025c2df40b84dbd75b30295f6445416032500db9a549b343fa2cf0ff656ce707"
PINNED_RESULT_SCHEMA_SHA256 = "4085015227fdee8d2c9e04da06d1e64b5f4a60e5b6f28f913addac66069d2c6d"
PINNED_ENGINE = "slabx"
PINNED_ENGINE_VERSION = "1.0.8"
PINNED_APPLICABILITY = "left_held_ground_vapour_release_history"
PINNED_COUPLING = "independent_constant_segments_no_cloud_interaction"
PINNED_PRETRANSITION_RECONSTRUCTION = "mass_normalized_quasi_steady_growing_cloud"
PINNED_BOUNDARY = "qualified_ground_level_thermalized_pure_vapour"
REQUEST_REQUIRED = frozenset({
    "expected_engine_code_digest",
    "source",
    "substance",
    "atmosphere",
    "receptors",
    "sample_times_s",
    "simulation_end_s",
    "tail_threshold_kg_m3",
    "applicability",
    "plume_distance_limit_m",
    "coupling",
    "pretransition_reconstruction",
})
REQUEST_ALLOWED = REQUEST_REQUIRED | {
    "engine", "required_version", "native_puff_steps", "timeout_s",
}
SOURCE_FIELDS = frozenset({
    "schema_version", "asset_id", "scenario_id", "operating_case_id", "origin",
    "source_digest", "source_code_digest", "evidence_ids", "mode", "intervals",
    "declared_mass_within_history_kg", "area_m2", "temperature_k", "qualification_basis", "boundary",
})


class CcpsReleaseHistoryInterval(Contract):
    """Caller-specified constant mass-rate segment on the source clock."""

    start_s: Nonnegative
    end_s: Positive
    mass_rate_kg_s: Nonnegative

    @model_validator(mode="after")
    def interval_has_positive_width(self):
        if self.end_s <= self.start_s:
            raise ValueError("release interval end must be later than its start")
        return self


class CcpsReleaseHistorySource(Contract):
    """Caller-reviewed source history matching the receiver's closed source contract."""

    asset_id: StrictStr = Field(min_length=1, max_length=160)
    scenario_id: StrictStr = Field(min_length=1, max_length=160)
    operating_case_id: StrictStr = Field(min_length=1, max_length=160)
    origin: Literal["prism", "user_supplied"]
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_code_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_ids: tuple[StrictStr, ...] = ()
    mode: Literal["finite", "continuous_through_window"]
    intervals: tuple[CcpsReleaseHistoryInterval, ...] = Field(min_length=1, max_length=128)
    declared_mass_within_history_kg: Positive
    area_m2: Positive
    temperature_k: Positive
    qualification_basis: StrictStr = Field(min_length=1, max_length=160)
    boundary: Literal[PINNED_BOUNDARY] = PINNED_BOUNDARY
    source_clock_id: StrictStr = Field(min_length=1, max_length=160)
    source_time_basis: StrictStr = Field(min_length=1, max_length=160)

    @model_validator(mode="after")
    def ordered_mass_and_evidence(self):
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("release-history evidence IDs must be unique")
        if any(not value.strip() or len(value) > 160 for value in self.evidence_ids):
            raise ValueError("release-history evidence IDs must be nonempty and at most 160 characters")
        prior_end = -math.inf
        integrated_mass = 0.0
        if self.intervals[0].start_s != 0:
            raise ValueError("release-history intervals must begin at source time zero")
        for interval in self.intervals:
            if interval.start_s < prior_end:
                raise ValueError("release-history intervals must be ordered and non-overlapping")
            if interval.start_s != prior_end and prior_end != -math.inf:
                raise ValueError("release-history intervals must be contiguous; declare zero-rate periods explicitly")
            prior_end = interval.end_s
            integrated_mass += interval.mass_rate_kg_s * (interval.end_s - interval.start_s)
        if integrated_mass <= 0:
            raise ValueError("release history must contain positive released mass")
        if not math.isclose(
            integrated_mass,
            self.declared_mass_within_history_kg,
            rel_tol=1e-9,
            abs_tol=1e-12,
        ):
            raise ValueError("declared history mass must equal the integral of caller-supplied segments")
        return self


class CcpsDenseSubstance(Contract):
    name: StrictStr = Field(min_length=1, max_length=160)
    molecular_weight_kg_mol: Positive
    vapor_heat_capacity_j_kg_k: Positive
    liquid_heat_capacity_j_kg_k: Positive
    latent_heat_j_kg: Positive
    normal_boiling_temperature_k: Positive
    liquid_density_kg_m3: Positive
    property_basis: StrictStr = Field(min_length=1, max_length=160)


class CcpsDenseAtmosphere(Contract):
    wind_speed_m_s: Positive
    wind_reference_height_m: Positive
    temperature_k: Positive
    relative_humidity_fraction: Fraction
    roughness_length_m: Positive
    stability: Literal["A", "B", "C", "D", "E", "F"]
    pressure_pa_abs: Literal[101325.0] = 101325.0


class CcpsDenseReceptor(Contract):
    id: StrictStr = Field(min_length=1, max_length=160)
    downwind_distance_m: Nonnegative
    crosswind_distance_m: float
    height_m: Nonnegative


class CcpsReleaseHistorySettings(Contract):
    """Caller-selected numerical controls for the pinned CCPS release-history API."""

    expected_engine_code_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    substance: CcpsDenseSubstance
    atmosphere: CcpsDenseAtmosphere
    receptors: tuple[CcpsDenseReceptor, ...] = Field(min_length=1, max_length=32)
    sample_times_s: tuple[Nonnegative, ...] = Field(min_length=2, max_length=2001)
    simulation_end_s: Positive = Field(le=86_400)
    native_puff_steps: StrictInt = Field(default=240, ge=80, le=2000)
    timeout_s: Positive = Field(default=60.0, le=300)
    tail_threshold_kg_m3: Positive
    plume_distance_limit_m: Positive = Field(le=100_000)

    @model_validator(mode="after")
    def coherent_sampling(self):
        if len(self.sample_times_s) != len(set(self.sample_times_s)):
            raise ValueError("sample times must be unique")
        if any(right <= left for left, right in zip(self.sample_times_s, self.sample_times_s[1:])):
            raise ValueError("sample times must be strictly increasing")
        if self.sample_times_s[0] < 0 or self.sample_times_s[-1] > self.simulation_end_s:
            raise ValueError("sample times must lie within the simulation interval")
        receptor_ids = [row.id for row in self.receptors]
        if len(receptor_ids) != len(set(receptor_ids)):
            raise ValueError("receptor IDs must be unique")
        return self


class CcpsReleaseHistoryRequestEnvelope(Contract):
    """Pinned provider request plus MatIntegrity's separate event/clock lineage."""

    schema_version: Literal["matintegrity.ccps_release_history_request_envelope.v1"] = (
        "matintegrity.ccps_release_history_request_envelope.v1"
    )
    repository: Literal[PINNED_REPOSITORY] = PINNED_REPOSITORY
    commit: Literal[PINNED_COMMIT] = PINNED_COMMIT
    request_schema_path: Literal[PINNED_REQUEST_SCHEMA_PATH] = PINNED_REQUEST_SCHEMA_PATH
    request_schema_sha256: Literal[PINNED_REQUEST_SCHEMA_SHA256] = PINNED_REQUEST_SCHEMA_SHA256
    result_schema_path: Literal[PINNED_RESULT_SCHEMA_PATH] = PINNED_RESULT_SCHEMA_PATH
    result_schema_sha256: Literal[PINNED_RESULT_SCHEMA_SHA256] = PINNED_RESULT_SCHEMA_SHA256
    handoff_id: StrictStr = Field(min_length=1)
    handoff_payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    event_id: StrictStr = Field(min_length=1)
    event_probability: Fraction
    probability_semantics: ProbabilityMeaning
    probability_conditioning: StrictStr = Field(min_length=1)
    clock_id: StrictStr = Field(min_length=1)
    time_basis: StrictStr = Field(min_length=1)
    source_history_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    request: dict[str, Any]
    request_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    event_probability_in_request: Literal[False] = False
    wall_loss_to_opening_conversion_performed: Literal[False] = False
    external_engine_executed: Literal[False] = False

    @model_validator(mode="after")
    def request_shape_and_digest(self):
        if set(self.request) - REQUEST_ALLOWED or not REQUEST_REQUIRED.issubset(self.request):
            raise ValueError("release-history request differs from the pinned closed provider schema")
        if self.request.get("engine") != PINNED_ENGINE:
            raise ValueError("release-history request engine differs from pinned schema")
        if self.request.get("required_version") != PINNED_ENGINE_VERSION:
            raise ValueError("release-history request engine version differs from pinned schema")
        if self.request.get("applicability") != PINNED_APPLICABILITY:
            raise ValueError("release-history request applicability differs from pinned schema")
        if self.request.get("coupling") != PINNED_COUPLING:
            raise ValueError("release-history request coupling differs from pinned schema")
        if self.request.get("pretransition_reconstruction") != PINNED_PRETRANSITION_RECONSTRUCTION:
            raise ValueError("release-history request reconstruction differs from pinned schema")
        if set(self.request.get("source", {})) != SOURCE_FIELDS:
            raise ValueError("release-history source differs from pinned closed source schema")
        check_finite(self.request)
        json.dumps(self.request, allow_nan=False)
        if canonical_digest(self.request) != self.request_digest:
            raise ValueError("release-history request digest differs from request content")
        if canonical_digest(self.request["source"]) != self.source_history_digest:
            raise ValueError("source history digest differs from serialized provider source")
        return self


def export_ccps_release_history_request(
    handoff: ConsequenceScenarioHandoff,
    source: CcpsReleaseHistorySource,
    settings: CcpsReleaseHistorySettings,
) -> CcpsReleaseHistoryRequestEnvelope:
    """Build a pinned release-history request without deriving mass rate or event probability."""
    if handoff.handoff_status != "ready":
        raise ValueError("only a ready consequence handoff can be exported")
    if (source.asset_id, source.scenario_id) != (handoff.event.asset_id, handoff.scenario_id):
        raise ValueError("caller release-history asset and scenario must match the integrity handoff")
    if source.source_clock_id != handoff.event.clock_id:
        raise ValueError("release-history clock must match the integrity-event clock")
    if source.intervals[-1].end_s > settings.simulation_end_s:
        raise ValueError("simulation end must cover the complete caller release history")
    if source.mode == "finite" and source.intervals[-1].end_s >= settings.simulation_end_s:
        raise ValueError("finite release history must end before the observation window closes")
    if source.mode == "continuous_through_window":
        if source.intervals[-1].end_s != settings.simulation_end_s:
            raise ValueError("continuous release history must cover the full observation window")
        if source.intervals[-1].mass_rate_kg_s <= 0:
            raise ValueError("continuous release history must have positive rate at window end")
    if not math.isclose(
        source.temperature_k,
        settings.substance.normal_boiling_temperature_k,
        rel_tol=1e-9,
        abs_tol=1e-9,
    ):
        raise ValueError("source temperature must match the qualified substance boiling temperature")
    if settings.substance.molecular_weight_kg_mol <= 0.028965:
        raise ValueError("dense-gas boundary requires caller-provided molecular weight above dry air")
    source_payload = {
        "schema_version": "ccps.release-history.v1",
        "asset_id": source.asset_id,
        "scenario_id": source.scenario_id,
        "operating_case_id": source.operating_case_id,
        "origin": source.origin,
        "source_digest": source.source_digest,
        "source_code_digest": source.source_code_digest,
        "evidence_ids": list(source.evidence_ids),
        "mode": source.mode,
        "intervals": [row.model_dump(mode="json") for row in source.intervals],
        "declared_mass_within_history_kg": source.declared_mass_within_history_kg,
        "area_m2": source.area_m2,
        "temperature_k": source.temperature_k,
        "qualification_basis": source.qualification_basis,
        "boundary": source.boundary,
    }
    request = {
        "engine": PINNED_ENGINE,
        "required_version": PINNED_ENGINE_VERSION,
        "expected_engine_code_digest": settings.expected_engine_code_digest,
        "source": source_payload,
        "substance": settings.substance.model_dump(mode="json"),
        "atmosphere": settings.atmosphere.model_dump(mode="json"),
        "receptors": [row.model_dump(mode="json") for row in settings.receptors],
        "sample_times_s": list(settings.sample_times_s),
        "simulation_end_s": settings.simulation_end_s,
        "native_puff_steps": settings.native_puff_steps,
        "timeout_s": settings.timeout_s,
        "tail_threshold_kg_m3": settings.tail_threshold_kg_m3,
        "applicability": PINNED_APPLICABILITY,
        "plume_distance_limit_m": settings.plume_distance_limit_m,
        "coupling": PINNED_COUPLING,
        "pretransition_reconstruction": PINNED_PRETRANSITION_RECONSTRUCTION,
    }
    request_digest = canonical_digest(request)
    return CcpsReleaseHistoryRequestEnvelope(
        handoff_id=handoff.handoff_id,
        handoff_payload_digest=handoff.payload_digest,
        event_id=handoff.event.event_id,
        event_probability=handoff.event.event_probability,
        probability_semantics=handoff.event.probability_semantics,
        probability_conditioning=handoff.event.probability_conditioning,
        clock_id=handoff.event.clock_id,
        time_basis=source.source_time_basis,
        source_history_digest=canonical_digest(source_payload),
        request=request,
        request_digest=request_digest,
    )


def validate_ccps_release_history_schema_bytes(
    envelope: CcpsReleaseHistoryRequestEnvelope,
    *,
    request_schema_bytes: bytes,
    result_schema_bytes: bytes,
) -> dict[str, str]:
    """Check the two caller-supplied official schema byte files against pinned digests."""
    if not isinstance(request_schema_bytes, bytes) or not isinstance(result_schema_bytes, bytes):
        raise TypeError("provider schemas must be supplied as raw bytes")
    request_sha = hashlib.sha256(request_schema_bytes).hexdigest()
    result_sha = hashlib.sha256(result_schema_bytes).hexdigest()
    if request_sha != PINNED_REQUEST_SCHEMA_SHA256:
        raise ValueError("release-history request schema bytes do not match reviewed commit pin")
    if result_sha != PINNED_RESULT_SCHEMA_SHA256:
        raise ValueError("release-history result schema bytes do not match reviewed commit pin")
    if envelope.request_schema_sha256 != request_sha or envelope.result_schema_sha256 != result_sha:
        raise ValueError("envelope schema digests differ from the supplied reviewed schema bytes")
    request_schema = json.loads(request_schema_bytes.decode("utf-8"))
    result_schema = json.loads(result_schema_bytes.decode("utf-8"))
    if not isinstance(request_schema, dict) or not isinstance(result_schema, dict):
        raise ValueError("provider schema roots must be JSON objects")
    request_required = set(request_schema.get("required", ()))
    if request_required != REQUEST_REQUIRED:
        raise ValueError("reviewed provider request required-field set differs from adapter contract")
    if request_schema.get("additionalProperties") is not False:
        raise ValueError("reviewed provider request schema must remain closed")
    if result_schema.get("title") != "ReleaseHistoryOutput":
        raise ValueError("reviewed provider result schema has an unexpected title")
    return {
        "request_schema_sha256": request_sha,
        "result_schema_sha256": result_sha,
        "reviewed_commit": PINNED_COMMIT,
        "request_schema_title": request_schema.get("title", ""),
        "result_schema_title": result_schema["title"],
    }

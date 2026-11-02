"""Auditable, caller-configured coverage checks for NDE POD campaigns.

This module does not prescribe qualification sample counts or acceptance limits.  It
checks a campaign against a profile supplied by the caller so that sparse or
confounded evidence is not silently passed to a POD curve fit.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract


class PODCampaignObservation(Contract):
    observation_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    flaw_size_m: float = Field(gt=0)
    detected: bool
    operator_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    material_group: str = Field(min_length=1)
    geometry_group: str = Field(min_length=1)
    access_group: str = Field(min_length=1)
    is_blind: bool


class PODCampaignRequirementProfile(Contract):
    profile_id: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    minimum_total_observations: int = Field(ge=1)
    minimum_hits: int = Field(ge=1)
    minimum_misses: int = Field(ge=1)
    minimum_distinct_flaw_sizes: int = Field(ge=2)
    minimum_observations_per_operator: int = Field(ge=1)
    required_operator_ids: list[str] = Field(min_length=1)
    required_material_groups: list[str] = Field(min_length=1)
    required_geometry_groups: list[str] = Field(min_length=1)
    required_access_groups: list[str] = Field(min_length=1)
    require_blind_observations: bool = True
    require_one_observation_per_specimen: bool = True

    @model_validator(mode="after")
    def unique_requirements(self):
        for name in (
            "required_operator_ids",
            "required_material_groups",
            "required_geometry_groups",
            "required_access_groups",
        ):
            values = getattr(self, name)
            if len(set(values)) != len(values) or any(not item.strip() for item in values):
                raise ValueError(f"{name} must contain unique nonempty values")
        return self


class PODCampaignAuditRequest(Contract):
    campaign_id: str = Field(min_length=1)
    observations: list[PODCampaignObservation] = Field(min_length=1)
    requirement_profile: PODCampaignRequirementProfile
    flaw_size_resolution_m: float = Field(gt=0)

    @model_validator(mode="after")
    def unique_observations(self):
        ids = [item.observation_id for item in self.observations]
        if len(set(ids)) != len(ids):
            raise ValueError("observation IDs must be unique")
        return self


class PODCampaignFinding(Contract):
    finding_id: str
    status: Literal["satisfied", "not_satisfied"]
    observed: int | bool | list[str]
    required: int | bool | list[str]
    detail: str


class PODCampaignAuditReport(Contract):
    schema_version: Literal["matintegrity.pod_campaign_audit.v1"] = "matintegrity.pod_campaign_audit.v1"
    campaign_id: str
    profile_id: str
    profile_revision: str
    status: Literal["ready_for_model_fit", "coverage_not_satisfied"]
    findings: list[PODCampaignFinding]
    observation_count: int
    hit_count: int
    miss_count: int
    distinct_flaw_size_bins: int
    request_digest: str
    report_digest: str
    qualification_claimed: Literal[False] = False


def _canonical_digest(value: object) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def audit_pod_campaign(request: PODCampaignAuditRequest) -> PODCampaignAuditReport:
    """Check evidence coverage without fitting or qualifying a POD model."""

    observations = request.observations
    profile = request.requirement_profile
    operator_counts = Counter(item.operator_id for item in observations)
    specimen_counts = Counter(item.specimen_id for item in observations)
    size_bins = {round(item.flaw_size_m / request.flaw_size_resolution_m) for item in observations}
    values = {
        "operator": {item.operator_id for item in observations},
        "material": {item.material_group for item in observations},
        "geometry": {item.geometry_group for item in observations},
        "access": {item.access_group for item in observations},
    }
    required = {
        "operator": set(profile.required_operator_ids),
        "material": set(profile.required_material_groups),
        "geometry": set(profile.required_geometry_groups),
        "access": set(profile.required_access_groups),
    }
    findings: list[PODCampaignFinding] = []

    def add(finding_id: str, ok: bool, observed, expected, detail: str) -> None:
        findings.append(
            PODCampaignFinding(
                finding_id=finding_id,
                status="satisfied" if ok else "not_satisfied",
                observed=observed,
                required=expected,
                detail=detail,
            )
        )

    hits = sum(item.detected for item in observations)
    misses = len(observations) - hits
    add(
        "total_observations",
        len(observations) >= profile.minimum_total_observations,
        len(observations),
        profile.minimum_total_observations,
        "Total independent evidence count.",
    )
    add("hits", hits >= profile.minimum_hits, hits, profile.minimum_hits, "Positive response count.")
    add(
        "misses", misses >= profile.minimum_misses, misses, profile.minimum_misses, "Negative response count."
    )
    add(
        "flaw_size_bins",
        len(size_bins) >= profile.minimum_distinct_flaw_sizes,
        len(size_bins),
        profile.minimum_distinct_flaw_sizes,
        "Distinct flaw-size bins at caller resolution.",
    )
    for dimension in ("operator", "material", "geometry", "access"):
        missing = sorted(required[dimension] - values[dimension])
        add(
            f"required_{dimension}_coverage",
            not missing,
            missing,
            [],
            f"Missing required {dimension} groups; an empty observed list means full coverage.",
        )
    sparse_operators = sorted(
        operator
        for operator in profile.required_operator_ids
        if operator_counts[operator] < profile.minimum_observations_per_operator
    )
    add(
        "operator_replication",
        not sparse_operators,
        sparse_operators,
        [],
        "Required operators below the caller's replication count.",
    )
    blind_ok = not profile.require_blind_observations or all(item.is_blind for item in observations)
    add(
        "blind_design",
        blind_ok,
        all(item.is_blind for item in observations),
        profile.require_blind_observations,
        "All observations are blind when requested.",
    )
    repeated = sorted(key for key, count in specimen_counts.items() if count > 1)
    independent_ok = not profile.require_one_observation_per_specimen or not repeated
    add(
        "one_observation_per_specimen",
        independent_ok,
        repeated,
        [],
        "Repeated specimens require a clustered model or a different profile.",
    )
    request_digest = _canonical_digest(request)
    report_payload = {
        "campaign_id": request.campaign_id,
        "profile_id": profile.profile_id,
        "profile_revision": profile.revision,
        "findings": [item.model_dump(mode="json") for item in findings],
        "request_digest": request_digest,
    }
    return PODCampaignAuditReport(
        campaign_id=request.campaign_id,
        profile_id=profile.profile_id,
        profile_revision=profile.revision,
        status=(
            "ready_for_model_fit"
            if all(item.status == "satisfied" for item in findings)
            else "coverage_not_satisfied"
        ),
        findings=findings,
        observation_count=len(observations),
        hit_count=hits,
        miss_count=misses,
        distinct_flaw_size_bins=len(size_bins),
        request_digest=request_digest,
        report_digest=_canonical_digest(report_payload),
    )

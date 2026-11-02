"""Caller-profile production campaign for surface-cleanliness evidence."""

from __future__ import annotations

import math
from statistics import fmean, pstdev
from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

Disposition = Literal["accept", "reject", "review", "insufficient_evidence"]
MODEL_ID = "fabrication.surface_cleanliness_production_campaign_evidence"
SOURCE_ID = "authored_surface_cleanliness_production_campaign_profile"


class PreparationEvent(Contract):
    event_id: str = Field(min_length=1)
    sequence_position: int = Field(ge=1)
    process_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    ambient_temperature_k: Positive
    surface_temperature_k: Positive
    dewpoint_temperature_k: Positive
    provider_id: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("preparation events require positive duration")
        return self


class CleanlinessMeasurement(Contract):
    measurement_id: str = Field(min_length=1)
    area_id: str = Field(min_length=1)
    sample_location_id: str = Field(min_length=1)
    replica_group_id: str = Field(min_length=1)
    metric_kind: Literal[
        "soluble_salt", "dust", "surface_profile", "oil", "visual", "roughness", "user_defined"
    ]
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    status: Literal["available", "missing", "invalid"]
    value: float | None = None
    standard_uncertainty: Nonnegative | None = None
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    missing_or_invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete(self):
        if self.status == "available" and (
            self.value is None or self.standard_uncertainty is None or self.result_digest is None
        ):
            raise ValueError("available cleanliness measurements require value, uncertainty and digest")
        if self.status != "available" and (
            self.value is not None
            or self.standard_uncertainty is not None
            or not self.missing_or_invalid_basis
        ):
            raise ValueError("missing or invalid cleanliness measurements require a basis and no value")
        return self


class CleanlinessCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    metric_kind: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    aggregation: Literal["individual", "replica_mean", "replica_minimum", "replica_maximum"]
    minimum_inclusive: float | None = None
    maximum_inclusive: float | None = None
    uncertainty_policy: Literal["point_value", "interval_must_fit"]
    uncertainty_coverage_factor: Positive = 1.0
    minimum_replicas: int = Field(ge=1)
    missing_disposition: Literal["review", "insufficient_evidence"]
    description: str = Field(min_length=1)

    @model_validator(mode="after")
    def bounds(self):
        if self.minimum_inclusive is None and self.maximum_inclusive is None:
            raise ValueError("cleanliness criteria require a caller bound")
        if (
            self.minimum_inclusive is not None
            and self.maximum_inclusive is not None
            and self.maximum_inclusive < self.minimum_inclusive
        ):
            raise ValueError("cleanliness criterion bounds must be ordered")
        return self


class CallerCleanlinessProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    permitted_substrate_ids: tuple[str, ...] = Field(min_length=1)
    permitted_previous_coating_ids: tuple[str, ...] = Field(min_length=1)
    permitted_contaminant_ids: tuple[str, ...] = Field(min_length=1)
    permitted_process_ids: tuple[str, ...] = Field(min_length=1)
    minimum_surface_above_dewpoint_k: Nonnegative
    criteria: tuple[CleanlinessCriterion, ...] = Field(min_length=1)
    profile_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class SurfaceCleanlinessCampaign(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    substrate_id: str = Field(min_length=1)
    area_ids: tuple[str, ...] = Field(min_length=1)
    previous_coating_id: str = Field(min_length=1)
    contaminant_ids: tuple[str, ...] = Field(min_length=1)
    preparation_events: tuple[PreparationEvent, ...] = Field(min_length=1)
    measurements: tuple[CleanlinessMeasurement, ...] = Field(min_length=1)
    profile: CallerCleanlinessProfile
    identity_and_area_mapping_reviewed: bool
    preparation_event_order_process_and_environment_reviewed: bool
    measurement_locations_replicas_units_uncertainty_and_provenance_reviewed: bool
    caller_profile_authority_and_criteria_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked(self):
        if [r.sequence_position for r in self.preparation_events] != list(
            range(1, len(self.preparation_events) + 1)
        ):
            raise ValueError("preparation events require consecutive sequence")
        for a, b in zip(self.preparation_events, self.preparation_events[1:], strict=False):
            if b.start_time_s < a.end_time_s:
                raise ValueError("preparation events cannot overlap")
        if any(r.area_id not in self.area_ids for r in self.measurements):
            raise ValueError("cleanliness measurements must reference declared areas")
        ids = [r.measurement_id for r in self.measurements]
        if len(ids) != len(set(ids)):
            raise ValueError("cleanliness measurement IDs must be unique")
        return self


class Finding(Contract):
    criterion_id: str
    target_id: str
    outcome: Literal["pass", "fail", "review", "insufficient_evidence"]
    observed_value: float | str | None
    unit_token: str
    evaluated_lower: float | None = None
    evaluated_upper: float | None = None
    basis: str


class SurfaceCleanlinessResult(Contract):
    schema_version: Literal["matintegrity.surface_cleanliness_campaign.v1"] = (
        "matintegrity.surface_cleanliness_campaign.v1"
    )
    model_id: Literal["fabrication.surface_cleanliness_production_campaign_evidence"] = MODEL_ID
    assessment_id: str
    campaign_id: str
    profile_id: str
    disposition: Disposition
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    findings: tuple[Finding, ...]
    review_reasons: tuple[str, ...]
    insufficient_evidence_reasons: tuple[str, ...]
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    automatic_image_interpretation_or_standard_comparator_claim: Literal[False] = False
    coating_qualification_claim: Literal[False] = False
    notes: tuple[str, ...] = Field(min_length=1)

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"result_digest"})

    @model_validator(mode="after")
    def digest(self, info: ValidationInfo):
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.result_digest
        ):
            raise ValueError("surface-cleanliness result digest does not match its content")
        return self


def assess_surface_cleanliness(x: SurfaceCleanlinessCampaign) -> SurfaceCleanlinessResult:
    p = x.profile
    reviews = []
    ins = []
    findings = []
    for ok, msg in (
        (p.profile_reviewed, "profile unreviewed"),
        (x.identity_and_area_mapping_reviewed, "identity/area unreviewed"),
        (x.preparation_event_order_process_and_environment_reviewed, "events/environment unreviewed"),
        (
            x.measurement_locations_replicas_units_uncertainty_and_provenance_reviewed,
            "measurements unreviewed",
        ),
        (x.caller_profile_authority_and_criteria_reviewed, "criteria unreviewed"),
    ):
        if not ok:
            ins.append(msg)
    if (
        x.substrate_id not in p.permitted_substrate_ids
        or x.previous_coating_id not in p.permitted_previous_coating_ids
        or not set(x.contaminant_ids).issubset(p.permitted_contaminant_ids)
    ):
        reviews.append("campaign identity outside caller profile")
    for r in x.preparation_events:
        ok = (
            r.process_id in p.permitted_process_ids
            and r.surface_temperature_k - r.dewpoint_temperature_k >= p.minimum_surface_above_dewpoint_k
        )
        findings.append(
            Finding(
                criterion_id="preparation_environment",
                target_id=r.event_id,
                outcome="pass" if ok else "fail",
                observed_value=r.surface_temperature_k - r.dewpoint_temperature_k,
                unit_token="K",
                basis="caller process and surface-above-dewpoint criterion",
            )
        )
    for c in p.criteria:
        rows = [
            r
            for r in x.measurements
            if r.metric_kind == c.metric_kind and r.metric_id == c.metric_id and r.unit_token == c.unit_token
        ]
        groups = {}
        for r in rows:
            groups.setdefault(r.replica_group_id, []).append(r)
        if not groups:
            out = c.missing_disposition
            (reviews if out == "review" else ins).append(f"{c.criterion_id} lacks evidence")
            continue
        for gid, g in sorted(groups.items()):
            av = [r for r in g if r.status == "available"]
            if len(av) < c.minimum_replicas:
                out = c.missing_disposition
                (reviews if out == "review" else ins).append(f"{c.criterion_id}:{gid} lacks replicas")
                continue
            vals = [r.value for r in av]
            if c.aggregation == "individual":
                sel = [(r.measurement_id, r.value, r.standard_uncertainty) for r in av]
            else:
                v = {"replica_mean": fmean(vals), "replica_minimum": min(vals), "replica_maximum": max(vals)}[
                    c.aggregation
                ]
                rep = pstdev(vals) / math.sqrt(len(vals)) if len(vals) > 1 else 0
                mu = math.sqrt(sum(r.standard_uncertainty**2 for r in av)) / len(av)
                sel = [(gid, v, math.sqrt(rep**2 + mu**2))]
            for target, v, u in sel:
                span = c.uncertainty_coverage_factor * u if c.uncertainty_policy == "interval_must_fit" else 0
                lo, hi = v - span, v + span
                ok = (c.minimum_inclusive is None or lo >= c.minimum_inclusive) and (
                    c.maximum_inclusive is None or hi <= c.maximum_inclusive
                )
                findings.append(
                    Finding(
                        criterion_id=c.criterion_id,
                        target_id=target,
                        outcome="pass" if ok else "fail",
                        observed_value=v,
                        unit_token=c.unit_token,
                        evaluated_lower=lo,
                        evaluated_upper=hi,
                        basis=f"caller {c.aggregation} criterion",
                    )
                )
    disp: Disposition = (
        "insufficient_evidence"
        if ins
        else "reject"
        if any(r.outcome == "fail" for r in findings)
        else "review"
        if reviews
        else "accept"
    )
    vals = dict(
        assessment_id=x.assessment_id,
        campaign_id=x.campaign_id,
        profile_id=p.profile_id,
        disposition=disp,
        input_digest=canonical_digest(x.model_dump(mode="json")),
        findings=tuple(findings),
        review_reasons=tuple(reviews),
        insufficient_evidence_reasons=tuple(ins),
        notes=(
            "Only caller criteria are applied; no image interpretation or standard comparator is embedded.",
            "Preparation order, ambient/dewpoint/surface temperatures and sampled evidence remain traceable.",
            "No coating qualification, life or failure probability is claimed.",
        ),
    )
    u = SurfaceCleanlinessResult.model_validate(
        {**vals, "result_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return SurfaceCleanlinessResult.model_validate(
        {**vals, "result_digest": canonical_digest(u.digest_payload())}
    )


def _calc(x):
    r = assess_surface_cleanliness(x)
    return Calculation(values=r.model_dump(mode="json"), notes=r.notes)


def specifications():
    def same(x, c):
        if (x.asset_id, x.location_id) != (c.asset_id, c.location_id):
            raise ValueError("surface-cleanliness campaign asset and location must match run context")

    return [
        ModelSpec(
            MODEL_ID,
            SurfaceCleanlinessCampaign,
            _calc,
            {"disposition": "1", "findings": "mixed", "result_digest": "1"},
            ("Caller criteria only; no standard comparator.",),
            (SOURCE_ID,),
            context_validator=same,
        )
    ]

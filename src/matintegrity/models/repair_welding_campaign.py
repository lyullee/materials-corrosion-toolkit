"""Caller-profile repair-welding production campaign evidence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

MODEL_ID = "welding.repair_welding"
SOURCE_ID = "authored_repair_welding_production_campaign_profile"
Disposition = Literal["accept", "reject", "review", "insufficient_evidence"]


class RepairIdentity(Contract):
    component_id: str
    repair_id: str
    weld_id: str
    wps_id: str
    wps_revision: str
    welder_ids: tuple[str, ...]
    base_heat_ids: tuple[str, ...]
    consumable_lot_ids: tuple[str, ...]
    repair_sequence_number: int = Field(ge=1)
    previous_repair_ids: tuple[str, ...] = ()
    reviewed: bool
    evidence: tuple[Evidence, ...]


class ExcavationEvidence(Contract):
    defect_id: str
    removal_method_id: str
    excavation_geometry_id: str
    length_m: Nonnegative
    depth_m: Nonnegative
    width_m: Nonnegative
    standard_uncertainty_m: Nonnegative
    provider_id: str
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...]


class RepairEvent(Contract):
    event_id: str
    sequence_position: int = Field(ge=1)
    event_kind: Literal["removal", "preheat", "deposition", "interpass", "pwht", "cooling"]
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_k: Positive
    maximum_temperature_k: Positive
    pass_id: str | None = None
    provider_id: str
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...]

    @model_validator(mode="after")
    def ordered(self):
        if self.end_time_s <= self.start_time_s or self.maximum_temperature_k < self.minimum_temperature_k:
            raise ValueError("repair events require ordered time and temperature")
        return self


class RepairObservation(Contract):
    observation_id: str
    metric_kind: Literal["nde", "hardness", "dimensional", "chemistry", "mechanical", "leak", "user_defined"]
    metric_id: str
    unit_token: str
    status: Literal["available", "missing", "invalid"]
    value: float | None = None
    standard_uncertainty: Nonnegative | None = None
    provider_id: str
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    missing_basis: str | None = None
    evidence: tuple[Evidence, ...]

    @model_validator(mode="after")
    def complete(self):
        if self.status == "available" and (
            self.value is None or self.standard_uncertainty is None or self.result_digest is None
        ):
            raise ValueError("available repair observations require value, uncertainty and digest")
        if self.status != "available" and (
            self.value is not None or self.standard_uncertainty is not None or not self.missing_basis
        ):
            raise ValueError("missing repair observations require basis and no value")
        return self


class Criterion(Contract):
    criterion_id: str
    metric_kind: str
    metric_id: str
    unit_token: str
    minimum_inclusive: float | None = None
    maximum_inclusive: float | None = None
    uncertainty_policy: Literal["point_value", "interval_must_fit"]
    missing_disposition: Literal["review", "insufficient_evidence"]


class Profile(Contract):
    profile_id: str
    profile_revision: str
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    permitted_wps_ids: tuple[str, ...]
    permitted_base_heat_ids: tuple[str, ...]
    permitted_consumable_lots: tuple[str, ...]
    maximum_repair_count: int = Field(ge=1)
    maximum_excavation_depth_m: Nonnegative
    maximum_event_temperature_k: Positive
    criteria: tuple[Criterion, ...]
    profile_reviewed: bool
    evidence: tuple[Evidence, ...]


class RepairWeldingCampaign(Contract):
    assessment_id: str
    asset_id: str
    location_id: str
    identity: RepairIdentity
    excavations: tuple[ExcavationEvidence, ...]
    events: tuple[RepairEvent, ...]
    observations: tuple[RepairObservation, ...]
    profile: Profile
    identity_and_repair_history_reviewed: bool
    defect_removal_excavation_geometry_reviewed: bool
    thermal_deposition_interpass_and_pwht_sequence_reviewed: bool
    observation_units_uncertainty_provenance_and_digests_reviewed: bool
    caller_profile_reviewed: bool
    evidence: tuple[Evidence, ...]

    @model_validator(mode="after")
    def linked(self):
        if [r.sequence_position for r in self.events] != list(range(1, len(self.events) + 1)):
            raise ValueError("repair events require consecutive sequence")
        for a, b in zip(self.events, self.events[1:], strict=False):
            if b.start_time_s < a.end_time_s:
                raise ValueError("repair events cannot overlap")
        if self.identity.repair_id in self.identity.previous_repair_ids:
            raise ValueError("current repair cannot be its own history")
        return self


class Result(Contract):
    schema_version: Literal["matintegrity.repair_welding_campaign.v1"] = (
        "matintegrity.repair_welding_campaign.v1"
    )
    model_id: Literal["welding.repair_welding"] = MODEL_ID
    assessment_id: str
    repair_id: str
    profile_id: str
    disposition: Disposition
    findings: tuple[dict[str, Any], ...]
    reasons: tuple[str, ...]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_wps_qualification_crack_growth_or_remaining_life_claim: Literal[False] = False

    def digest_payload(self):
        return self.model_dump(mode="json", exclude={"result_digest"})

    @model_validator(mode="after")
    def digest(self, info: ValidationInfo):
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.result_digest
        ):
            raise ValueError("repair-welding result digest mismatch")
        return self


def assess_repair_welding(x: RepairWeldingCampaign) -> Result:
    p = x.profile
    findings = []
    reasons = []
    ins = not all(
        (
            p.profile_reviewed,
            x.identity.reviewed,
            x.identity_and_repair_history_reviewed,
            x.defect_removal_excavation_geometry_reviewed,
            x.thermal_deposition_interpass_and_pwht_sequence_reviewed,
            x.observation_units_uncertainty_provenance_and_digests_reviewed,
            x.caller_profile_reviewed,
        )
    )
    review = (
        x.identity.wps_id not in p.permitted_wps_ids
        or not set(x.identity.base_heat_ids).issubset(p.permitted_base_heat_ids)
        or not set(x.identity.consumable_lot_ids).issubset(p.permitted_consumable_lots)
    )
    findings.append(
        {
            "criterion_id": "repair_count",
            "outcome": "pass" if x.identity.repair_sequence_number <= p.maximum_repair_count else "fail",
        }
    )
    for r in x.excavations:
        findings.append(
            {
                "criterion_id": "excavation_depth",
                "target_id": r.defect_id,
                "outcome": "pass"
                if r.depth_m + r.standard_uncertainty_m <= p.maximum_excavation_depth_m
                else "fail",
            }
        )
    for r in x.events:
        findings.append(
            {
                "criterion_id": "event_temperature",
                "target_id": r.event_id,
                "outcome": "pass" if r.maximum_temperature_k <= p.maximum_event_temperature_k else "fail",
            }
        )
    for c in p.criteria:
        rows = [
            r
            for r in x.observations
            if r.metric_kind == c.metric_kind
            and r.metric_id == c.metric_id
            and r.unit_token == c.unit_token
            and r.status == "available"
        ]
        if not rows:
            reasons.append(f"{c.criterion_id} missing")
            ins = c.missing_disposition == "insufficient_evidence" or ins
            review = c.missing_disposition == "review" or review
            continue
        for r in rows:
            span = r.standard_uncertainty if c.uncertainty_policy == "interval_must_fit" else 0
            lo, hi = r.value - span, r.value + span
            ok = (c.minimum_inclusive is None or lo >= c.minimum_inclusive) and (
                c.maximum_inclusive is None or hi <= c.maximum_inclusive
            )
            findings.append(
                {
                    "criterion_id": c.criterion_id,
                    "target_id": r.observation_id,
                    "outcome": "pass" if ok else "fail",
                }
            )
    disp = (
        "insufficient_evidence"
        if ins
        else "reject"
        if any(r["outcome"] == "fail" for r in findings)
        else "review"
        if review
        else "accept"
    )
    vals = dict(
        assessment_id=x.assessment_id,
        repair_id=x.identity.repair_id,
        profile_id=p.profile_id,
        disposition=disp,
        findings=tuple(findings),
        reasons=tuple(reasons),
        input_digest=canonical_digest(x.model_dump(mode="json")),
    )
    u = Result.model_validate({**vals, "result_digest": "0" * 64}, context={"allow_unbound_digest": True})
    return Result.model_validate({**vals, "result_digest": canonical_digest(u.digest_payload())})


def _calc(x):
    r = assess_repair_welding(x)
    return Calculation(values=r.model_dump(mode="json"))


def specifications():
    return [
        ModelSpec(
            MODEL_ID,
            RepairWeldingCampaign,
            _calc,
            {"disposition": "1", "findings": "mixed", "result_digest": "1"},
            ("Caller criteria only; no WPS qualification or life inference.",),
            (SOURCE_ID,),
        )
    ]

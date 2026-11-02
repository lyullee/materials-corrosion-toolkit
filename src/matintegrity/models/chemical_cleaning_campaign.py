"""Caller-profile chemical-cleaning production campaign evidence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

Disposition = Literal["accept", "reject", "review", "insufficient_evidence"]
MODEL_ID = "fabrication.chemical_cleaning_production_campaign_evidence"
SOURCE_ID = "authored_chemical_cleaning_production_campaign_profile"


class ChemicalComponent(Contract):
    component_id: str = Field(min_length=1)
    concentration: Nonnegative
    unit_token: str = Field(min_length=1)


class ChemicalBatch(Contract):
    batch_id: str = Field(min_length=1)
    composition: tuple[ChemicalComponent, ...] = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique(self):
        if len({(r.component_id, r.unit_token) for r in self.composition}) != len(self.composition):
            raise ValueError("chemical component/unit keys must be unique")
        return self


class CleaningEvent(Contract):
    event_id: str = Field(min_length=1)
    sequence_position: int = Field(ge=1)
    event_kind: Literal["fill", "circulate", "soak", "rinse", "neutralize", "dry"]
    batch_id: str | None = None
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_k: Positive
    maximum_temperature_k: Positive
    minimum_pressure_pa_abs: Nonnegative
    maximum_pressure_pa_abs: Nonnegative
    flow_m3_s: Nonnegative | None = None
    ph: float | None = Field(default=None, ge=0, le=14)
    conductivity_s_m: Nonnegative | None = None
    provider_id: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered(self):
        if (
            self.end_time_s <= self.start_time_s
            or self.maximum_temperature_k < self.minimum_temperature_k
            or self.maximum_pressure_pa_abs < self.minimum_pressure_pa_abs
        ):
            raise ValueError("cleaning event time/state ranges must be ordered")
        return self


class CleaningMeasurement(Contract):
    measurement_id: str = Field(min_length=1)
    sample_location_id: str = Field(min_length=1)
    metric_kind: Literal["coupon", "solution", "surface", "residue", "chemistry", "nde", "user_defined"]
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    status: Literal["available", "missing", "invalid"]
    value: float | None = None
    standard_uncertainty: Nonnegative | None = None
    provider_id: str = Field(min_length=1)
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete(self):
        if self.status == "available" and (
            self.value is None or self.standard_uncertainty is None or self.result_digest is None
        ):
            raise ValueError("available cleaning measurements require value, uncertainty and digest")
        if self.status != "available" and (
            self.value is not None or self.standard_uncertainty is not None or not self.missing_basis
        ):
            raise ValueError("missing/invalid cleaning measurements require basis and no value")
        return self


class WasteDisposition(Contract):
    waste_record_id: str = Field(min_length=1)
    waste_stream_id: str = Field(min_length=1)
    disposition_method_id: str = Field(min_length=1)
    destination_id: str = Field(min_length=1)
    manifest_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class Criterion(Contract):
    criterion_id: str
    metric_kind: str
    metric_id: str
    unit_token: str
    minimum_inclusive: float | None = None
    maximum_inclusive: float | None = None
    uncertainty_policy: Literal["point_value", "interval_must_fit"]
    missing_disposition: Literal["review", "insufficient_evidence"]

    @model_validator(mode="after")
    def bounds(self):
        if self.minimum_inclusive is None and self.maximum_inclusive is None:
            raise ValueError("cleaning criteria require a bound")
        return self


class Profile(Contract):
    profile_id: str
    profile_revision: str
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    permitted_material_ids: tuple[str, ...]
    permitted_precondition_ids: tuple[str, ...]
    permitted_component_units: tuple[str, ...]
    maximum_event_temperature_k: Positive
    maximum_pressure_pa_abs: Nonnegative
    criteria: tuple[Criterion, ...]
    profile_reviewed: bool
    evidence: tuple[Evidence, ...]


class ChemicalCleaningCampaign(Contract):
    assessment_id: str
    asset_id: str
    location_id: str
    campaign_id: str
    material_id: str
    area_ids: tuple[str, ...]
    circuit_id: str
    precondition_id: str
    batches: tuple[ChemicalBatch, ...]
    events: tuple[CleaningEvent, ...]
    measurements: tuple[CleaningMeasurement, ...]
    waste_records: tuple[WasteDisposition, ...]
    profile: Profile
    identity_precondition_batch_and_composition_reviewed: bool
    event_sequence_state_units_and_time_reviewed: bool
    measurement_uncertainty_provenance_and_digest_reviewed: bool
    waste_disposition_evidence_reviewed: bool
    caller_profile_reviewed: bool
    evidence: tuple[Evidence, ...]

    @model_validator(mode="after")
    def linked(self):
        bids = {r.batch_id for r in self.batches}
        if [r.sequence_position for r in self.events] != list(range(1, len(self.events) + 1)):
            raise ValueError("cleaning events require consecutive sequence")
        if any(r.batch_id is not None and r.batch_id not in bids for r in self.events):
            raise ValueError("cleaning events must reference declared batches")
        for a, b in zip(self.events, self.events[1:], strict=False):
            if b.start_time_s < a.end_time_s:
                raise ValueError("cleaning events cannot overlap")
        return self


class Result(Contract):
    schema_version: Literal["matintegrity.chemical_cleaning_campaign.v1"] = (
        "matintegrity.chemical_cleaning_campaign.v1"
    )
    model_id: Literal["fabrication.chemical_cleaning_production_campaign_evidence"] = MODEL_ID
    assessment_id: str
    campaign_id: str
    profile_id: str
    disposition: Disposition
    findings: tuple[dict[str, Any], ...]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    reasons: tuple[str, ...]
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    automatic_kinetics_corrosion_compatibility_or_standard_acceptance_claim: Literal[False] = False

    def digest_payload(self):
        return self.model_dump(mode="json", exclude={"result_digest"})

    @model_validator(mode="after")
    def digest(self, info: ValidationInfo):
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.result_digest
        ):
            raise ValueError("chemical-cleaning result digest mismatch")
        return self


def assess_chemical_cleaning(x: ChemicalCleaningCampaign) -> Result:
    p = x.profile
    reasons = []
    findings = []
    ins = not all(
        (
            p.profile_reviewed,
            x.identity_precondition_batch_and_composition_reviewed,
            x.event_sequence_state_units_and_time_reviewed,
            x.measurement_uncertainty_provenance_and_digest_reviewed,
            x.waste_disposition_evidence_reviewed,
            x.caller_profile_reviewed,
            all(r.record_reviewed for r in x.waste_records),
        )
    )
    review = (
        x.material_id not in p.permitted_material_ids or x.precondition_id not in p.permitted_precondition_ids
    )
    if any(c.unit_token not in p.permitted_component_units for b in x.batches for c in b.composition):
        reasons.append("chemical concentration unit outside caller profile")
        ins = True
    for e in x.events:
        ok = (
            e.maximum_temperature_k <= p.maximum_event_temperature_k
            and e.maximum_pressure_pa_abs <= p.maximum_pressure_pa_abs
        )
        findings.append(
            {"criterion_id": "event_state", "target_id": e.event_id, "outcome": "pass" if ok else "fail"}
        )
    for c in p.criteria:
        rows = [
            r
            for r in x.measurements
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
                    "target_id": r.measurement_id,
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
        campaign_id=x.campaign_id,
        profile_id=p.profile_id,
        disposition=disp,
        findings=tuple(findings),
        input_digest=canonical_digest(x.model_dump(mode="json")),
        reasons=tuple(reasons),
    )
    u = Result.model_validate({**vals, "result_digest": "0" * 64}, context={"allow_unbound_digest": True})
    return Result.model_validate({**vals, "result_digest": canonical_digest(u.digest_payload())})


def _calc(x):
    r = assess_chemical_cleaning(x)
    return Calculation(values=r.model_dump(mode="json"))


def specifications():
    return [
        ModelSpec(
            MODEL_ID,
            ChemicalCleaningCampaign,
            _calc,
            {"disposition": "1", "findings": "mixed", "result_digest": "1"},
            ("Caller criteria only; no kinetics or compatibility inference.",),
            (SOURCE_ID,),
        )
    ]

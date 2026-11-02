"""Caller-profile production campaign evidence for brazing and adhesive bonding."""

from __future__ import annotations

import math
from statistics import fmean, pstdev
from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

Disposition = Literal["accept", "reject", "review", "insufficient_evidence"]
MODEL_ID = "welding.brazing_bonding_production_campaign_evidence"
SOURCE_ID = "authored_brazing_bonding_production_campaign_profile"


class ProductionJointRecord(Contract):
    joint_id: str = Field(min_length=1)
    process_kind: Literal["brazing", "adhesive_bonding"]
    base_material_lot_ids: tuple[str, ...] = Field(min_length=1)
    filler_lot_id: str | None = None
    adhesive_lot_id: str | None = None
    surface_preparation_id: str = Field(min_length=1)
    joint_geometry_id: str = Field(min_length=1)
    fitup_gap_m: Nonnegative
    fitup_gap_standard_uncertainty_m: Nonnegative
    atmosphere_id: str | None = None
    flux_lot_id: str | None = None
    fitup_and_identity_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def process_consumables(self):
        if self.process_kind == "brazing" and self.filler_lot_id is None:
            raise ValueError("brazing joints require a filler lot")
        if self.process_kind == "adhesive_bonding" and self.adhesive_lot_id is None:
            raise ValueError("adhesive-bonding joints require an adhesive lot")
        if len(self.base_material_lot_ids) != len(set(self.base_material_lot_ids)):
            raise ValueError("base-material lot IDs must be unique per joint")
        return self


class ProductionCycleInterval(Contract):
    interval_id: str = Field(min_length=1)
    sequence_position: int = Field(ge=1)
    interval_kind: Literal["preheat", "braze_heat", "bond_cure", "pressure_hold", "cooling"]
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_k: Positive
    maximum_temperature_k: Positive
    minimum_pressure_pa_abs: Nonnegative
    maximum_pressure_pa_abs: Nonnegative
    atmosphere_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("production cycle intervals require positive duration")
        if (
            self.maximum_temperature_k < self.minimum_temperature_k
            or self.maximum_pressure_pa_abs < self.minimum_pressure_pa_abs
        ):
            raise ValueError("production cycle state ranges must be ordered")
        return self


class ProductionJointMeasurement(Contract):
    measurement_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    replicate_group_id: str = Field(min_length=1)
    metric_kind: Literal["destructive", "nde", "leak", "strength", "continuity", "user_defined"]
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
        if self.status == "available":
            if self.value is None or self.standard_uncertainty is None or self.result_digest is None:
                raise ValueError("available joint measurements require value, uncertainty and digest")
        elif (
            self.value is not None
            or self.standard_uncertainty is not None
            or not self.missing_or_invalid_basis
        ):
            raise ValueError("missing or invalid joint measurements require a basis and no value")
        return self


class CallerProductionCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    metric_kind: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    aggregation: Literal["individual", "replicate_mean", "replicate_minimum", "replicate_maximum"]
    minimum_inclusive: float | None = None
    maximum_inclusive: float | None = None
    uncertainty_policy: Literal["point_value", "interval_must_fit"]
    uncertainty_coverage_factor: Positive = 1.0
    minimum_replicates: int = Field(ge=1)
    missing_disposition: Literal["review", "insufficient_evidence"]
    description: str = Field(min_length=1)

    @model_validator(mode="after")
    def bounds(self):
        if self.minimum_inclusive is None and self.maximum_inclusive is None:
            raise ValueError("production criteria require a caller bound")
        if (
            self.minimum_inclusive is not None
            and self.maximum_inclusive is not None
            and self.maximum_inclusive < self.minimum_inclusive
        ):
            raise ValueError("production criterion bounds must be ordered")
        return self


class CallerBrazingBondingProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    permitted_base_lot_ids: tuple[str, ...] = Field(min_length=1)
    permitted_filler_lot_ids: tuple[str, ...] = ()
    permitted_adhesive_lot_ids: tuple[str, ...] = ()
    permitted_surface_preparation_ids: tuple[str, ...] = Field(min_length=1)
    permitted_joint_geometry_ids: tuple[str, ...] = Field(min_length=1)
    minimum_fitup_gap_m: Nonnegative
    maximum_fitup_gap_m: Nonnegative
    fitup_uncertainty_policy: Literal["point_value", "interval_must_fit"]
    permitted_atmosphere_ids: tuple[str, ...] = Field(min_length=1)
    permitted_flux_lot_ids: tuple[str, ...] = ()
    minimum_cycle_temperature_k: Positive
    maximum_cycle_temperature_k: Positive
    maximum_cycle_pressure_pa_abs: Nonnegative
    maximum_interval_duration_s: Positive
    criteria: tuple[CallerProductionCriterion, ...] = Field(min_length=1)
    profile_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered(self):
        if (
            self.maximum_fitup_gap_m < self.minimum_fitup_gap_m
            or self.maximum_cycle_temperature_k < self.minimum_cycle_temperature_k
        ):
            raise ValueError("caller production profile ranges must be ordered")
        ids = [row.criterion_id for row in self.criteria]
        if len(ids) != len(set(ids)):
            raise ValueError("production criterion IDs must be unique")
        return self


class BrazingBondingProductionCampaign(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    joints: tuple[ProductionJointRecord, ...] = Field(min_length=1)
    cycle_history: tuple[ProductionCycleInterval, ...] = Field(min_length=1)
    measurements: tuple[ProductionJointMeasurement, ...] = Field(min_length=1)
    profile: CallerBrazingBondingProfile
    material_consumable_surface_prep_fitup_atmosphere_flux_and_geometry_reviewed: bool
    ordered_heat_pressure_cure_cycle_reviewed: bool
    destructive_nde_leak_strength_continuity_measurements_reviewed: bool
    units_uncertainty_methods_provenance_and_digests_reviewed: bool
    caller_profile_authority_and_criteria_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked(self):
        joint_ids = [row.joint_id for row in self.joints]
        if len(joint_ids) != len(set(joint_ids)):
            raise ValueError("production joint IDs must be unique")
        if any(row.joint_id not in joint_ids for row in self.measurements):
            raise ValueError("production measurements must reference declared joints")
        if [row.sequence_position for row in self.cycle_history] != list(
            range(1, len(self.cycle_history) + 1)
        ):
            raise ValueError("production cycle history requires consecutive positions")
        for first, second in zip(self.cycle_history, self.cycle_history[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("production cycle intervals cannot overlap")
        return self


class CampaignFinding(Contract):
    criterion_id: str
    target_id: str
    outcome: Literal["pass", "fail", "review", "insufficient_evidence"]
    observed_value: float | str | None
    unit_token: str
    evaluated_lower: float | None = None
    evaluated_upper: float | None = None
    basis: str


class BrazingBondingCampaignResult(Contract):
    schema_version: Literal["matintegrity.brazing_bonding_campaign.v1"] = (
        "matintegrity.brazing_bonding_campaign.v1"
    )
    model_id: Literal["welding.brazing_bonding_production_campaign_evidence"] = MODEL_ID
    assessment_id: str
    campaign_id: str
    profile_id: str
    disposition: Disposition
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    findings: tuple[CampaignFinding, ...]
    review_reasons: tuple[str, ...]
    insufficient_evidence_reasons: tuple[str, ...]
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    automatic_material_compatibility_or_qualification_claim: Literal[False] = False
    life_or_standard_acceptance_claim: Literal[False] = False
    notes: tuple[str, ...] = Field(min_length=1)

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"result_digest"})

    @model_validator(mode="after")
    def digest(self, info: ValidationInfo):
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.result_digest
        ):
            raise ValueError("brazing/bonding campaign result digest does not match its content")
        return self


def assess_brazing_bonding_campaign(x: BrazingBondingProductionCampaign) -> BrazingBondingCampaignResult:
    p = x.profile
    reviews, insufficient, findings = [], [], []
    for reviewed, reason in (
        (p.profile_reviewed, "caller profile was not reviewed"),
        (
            x.material_consumable_surface_prep_fitup_atmosphere_flux_and_geometry_reviewed,
            "joint identity and fit-up evidence was not reviewed",
        ),
        (x.ordered_heat_pressure_cure_cycle_reviewed, "cycle history was not reviewed"),
        (
            x.destructive_nde_leak_strength_continuity_measurements_reviewed,
            "measurement scope was not reviewed",
        ),
        (x.units_uncertainty_methods_provenance_and_digests_reviewed, "measurement lineage was not reviewed"),
        (x.caller_profile_authority_and_criteria_reviewed, "caller criteria authority was not reviewed"),
    ):
        if not reviewed:
            insufficient.append(reason)
    for joint in x.joints:
        identity_ok = (
            set(joint.base_material_lot_ids).issubset(p.permitted_base_lot_ids)
            and joint.surface_preparation_id in p.permitted_surface_preparation_ids
            and joint.joint_geometry_id in p.permitted_joint_geometry_ids
            and (joint.filler_lot_id is None or joint.filler_lot_id in p.permitted_filler_lot_ids)
            and (joint.adhesive_lot_id is None or joint.adhesive_lot_id in p.permitted_adhesive_lot_ids)
            and (joint.flux_lot_id is None or joint.flux_lot_id in p.permitted_flux_lot_ids)
            and (joint.atmosphere_id is None or joint.atmosphere_id in p.permitted_atmosphere_ids)
        )
        if not identity_ok:
            reviews.append(f"joint {joint.joint_id} identity outside caller profile")
        span = (
            joint.fitup_gap_standard_uncertainty_m
            if p.fitup_uncertainty_policy == "interval_must_fit"
            else 0.0
        )
        low, high = joint.fitup_gap_m - span, joint.fitup_gap_m + span
        within = p.minimum_fitup_gap_m <= low and high <= p.maximum_fitup_gap_m
        findings.append(
            CampaignFinding(
                criterion_id="fitup_gap",
                target_id=joint.joint_id,
                outcome="pass" if within else "fail",
                observed_value=joint.fitup_gap_m,
                unit_token="m",
                evaluated_lower=low,
                evaluated_upper=high,
                basis=f"caller fit-up envelope with {p.fitup_uncertainty_policy}",
            )
        )
    for row in x.cycle_history:
        within = (
            row.atmosphere_id in p.permitted_atmosphere_ids
            and p.minimum_cycle_temperature_k <= row.minimum_temperature_k
            and row.maximum_temperature_k <= p.maximum_cycle_temperature_k
            and row.maximum_pressure_pa_abs <= p.maximum_cycle_pressure_pa_abs
            and row.end_time_s - row.start_time_s <= p.maximum_interval_duration_s
        )
        findings.append(
            CampaignFinding(
                criterion_id="cycle_history",
                target_id=row.interval_id,
                outcome="pass" if within else "fail",
                observed_value=row.maximum_temperature_k,
                unit_token="K",
                basis="caller cycle atmosphere, temperature, pressure and duration envelope",
            )
        )
    for criterion in p.criteria:
        rows = [
            r
            for r in x.measurements
            if r.metric_kind == criterion.metric_kind
            and r.metric_id == criterion.metric_id
            and r.unit_token == criterion.unit_token
        ]
        groups: dict[str, list[ProductionJointMeasurement]] = {}
        for row in rows:
            groups.setdefault(row.replicate_group_id, []).append(row)
        if not groups:
            outcome = criterion.missing_disposition
            (reviews if outcome == "review" else insufficient).append(
                f"{criterion.criterion_id} lacks exact metric/unit evidence"
            )
            continue
        for group_id, group in sorted(groups.items()):
            available = [r for r in group if r.status == "available"]
            if len(available) < criterion.minimum_replicates:
                outcome = criterion.missing_disposition
                (reviews if outcome == "review" else insufficient).append(
                    f"{criterion.criterion_id}:{group_id} lacks replicates"
                )
                findings.append(
                    CampaignFinding(
                        criterion_id=criterion.criterion_id,
                        target_id=group_id,
                        outcome=outcome,
                        observed_value=None,
                        unit_token=criterion.unit_token,
                        basis="caller minimum replicate count not met",
                    )
                )
                continue
            vals = [r.value for r in available]
            if criterion.aggregation == "individual":
                selected = [(r.measurement_id, r.value, r.standard_uncertainty) for r in available]
            else:
                value = {
                    "replicate_mean": fmean(vals),
                    "replicate_minimum": min(vals),
                    "replicate_maximum": max(vals),
                }[criterion.aggregation]
                rep = pstdev(vals) / math.sqrt(len(vals)) if len(vals) > 1 else 0.0
                mu = math.sqrt(sum(r.standard_uncertainty**2 for r in available)) / len(available)
                selected = [(group_id, value, math.sqrt(rep**2 + mu**2))]
            for target, value, uncertainty in selected:
                span = (
                    criterion.uncertainty_coverage_factor * uncertainty
                    if criterion.uncertainty_policy == "interval_must_fit"
                    else 0.0
                )
                low, high = value - span, value + span
                within = (criterion.minimum_inclusive is None or low >= criterion.minimum_inclusive) and (
                    criterion.maximum_inclusive is None or high <= criterion.maximum_inclusive
                )
                findings.append(
                    CampaignFinding(
                        criterion_id=criterion.criterion_id,
                        target_id=target,
                        outcome="pass" if within else "fail",
                        observed_value=value,
                        unit_token=criterion.unit_token,
                        evaluated_lower=low,
                        evaluated_upper=high,
                        basis=f"caller {criterion.aggregation} criterion with {criterion.uncertainty_policy}",
                    )
                )
    disposition: Disposition = (
        "insufficient_evidence"
        if insufficient
        else "reject"
        if any(r.outcome == "fail" for r in findings)
        else "review"
        if reviews or any(r.outcome == "review" for r in findings)
        else "accept"
    )
    values = dict(
        assessment_id=x.assessment_id,
        campaign_id=x.campaign_id,
        profile_id=p.profile_id,
        disposition=disposition,
        input_digest=canonical_digest(x.model_dump(mode="json")),
        findings=tuple(findings),
        review_reasons=tuple(dict.fromkeys(reviews)),
        insufficient_evidence_reasons=tuple(dict.fromkeys(insufficient)),
        notes=(
            "Only caller-owned production criteria are applied; no material compatibility or standard allowable is inferred.",
            "Joint lots, surface preparation, fit-up, atmosphere/flux, cycles and destructive/NDE/leak/strength/continuity evidence remain traceable.",
            "No qualification, life prediction or failure probability is claimed.",
        ),
    )
    unsigned = BrazingBondingCampaignResult.model_validate(
        {**values, "result_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return BrazingBondingCampaignResult.model_validate(
        {**values, "result_digest": canonical_digest(unsigned.digest_payload())}
    )


def _calculation(x: BrazingBondingProductionCampaign) -> Calculation:
    result = assess_brazing_bonding_campaign(x)
    return Calculation(values=result.model_dump(mode="json"), notes=result.notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("brazing/bonding campaign asset and location must match run context")

    return [
        ModelSpec(
            MODEL_ID,
            BrazingBondingProductionCampaign,
            _calculation,
            {"disposition": "1", "findings": "mixed", "result_digest": "1"},
            ("Caller-owned campaign criteria only; no qualification claim.",),
            (SOURCE_ID,),
            context_validator=same_identity,
        )
    ]

"""Caller-profile lot assessment for coating and thermal-spray campaigns."""

from __future__ import annotations

import math
from statistics import fmean, pstdev
from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Contract, Evidence, Nonnegative, Positive, canonical_digest

Disposition = Literal["accept", "reject", "review", "insufficient_evidence"]
MODEL_ID = "fabrication.coating_campaign_lot_profile_assessment"


class CoatingQualityMeasurement(Contract):
    measurement_id: str = Field(min_length=1)
    replicate_group_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    metric_kind: Literal[
        "dft",
        "layer_thickness",
        "adhesion",
        "porosity",
        "holiday_count",
        "defect_count",
        "cure_property",
        "user_defined",
    ]
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    status: Literal["available", "missing", "invalid"]
    value: float | None = None
    standard_uncertainty: Nonnegative | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    missing_or_invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_status(self):
        if self.status == "available":
            if self.value is None or self.standard_uncertainty is None or self.result_digest is None:
                raise ValueError("available coating measurements require value, uncertainty and digest")
        elif (
            self.value is not None
            or self.standard_uncertainty is not None
            or not self.missing_or_invalid_basis
        ):
            raise ValueError("missing or invalid coating measurements require a basis and no value")
        return self


class CoatingCureHeatInterval(Contract):
    interval_id: str = Field(min_length=1)
    sequence_position: int = Field(ge=1)
    clock_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_k: Positive
    maximum_temperature_k: Positive
    temperature_unit_token: Literal["K"] = "K"
    environment_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("coating cure/heat intervals require positive duration")
        if self.maximum_temperature_k < self.minimum_temperature_k:
            raise ValueError("coating cure/heat temperature range must be ordered")
        return self


class CallerCoatingMetricRule(Contract):
    rule_id: str = Field(min_length=1)
    metric_kind: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    aggregation: Literal["individual", "replicate_mean", "replicate_minimum", "replicate_maximum"]
    minimum_inclusive: float | None = None
    maximum_inclusive: float | None = None
    uncertainty_policy: Literal["point_value", "interval_must_fit"]
    uncertainty_coverage_factor: Positive = 1.0
    minimum_replicates_per_group: int = Field(ge=1)
    missing_disposition: Literal["review", "insufficient_evidence"]
    rule_description: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_bounds(self):
        if self.minimum_inclusive is None and self.maximum_inclusive is None:
            raise ValueError("coating metric rules require at least one bound")
        if (
            self.minimum_inclusive is not None
            and self.maximum_inclusive is not None
            and self.maximum_inclusive < self.minimum_inclusive
        ):
            raise ValueError("coating metric-rule bounds must be ordered")
        return self


class CallerCoatingCampaignProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    permitted_substrate_condition_ids: tuple[str, ...] = Field(min_length=1)
    permitted_surface_preparation_ids: tuple[str, ...] = Field(min_length=1)
    permitted_coating_system_ids: tuple[str, ...] = Field(min_length=1)
    permitted_process_condition_ids: tuple[str, ...] = Field(min_length=1)
    permitted_environment_ids: tuple[str, ...] = Field(min_length=1)
    minimum_cure_temperature_k: Positive
    maximum_cure_temperature_k: Positive
    maximum_cure_interval_s: Positive
    metric_rules: tuple[CallerCoatingMetricRule, ...] = Field(min_length=1)
    profile_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_profile(self):
        if self.maximum_cure_temperature_k < self.minimum_cure_temperature_k:
            raise ValueError("caller cure-temperature envelope must be ordered")
        ids = [row.rule_id for row in self.metric_rules]
        if len(ids) != len(set(ids)):
            raise ValueError("caller coating metric-rule IDs must be unique")
        return self


class CoatingCampaignAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    coating_lot_id: str = Field(min_length=1)
    coating_system_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    surface_preparation_id: str = Field(min_length=1)
    batch_id: str = Field(min_length=1)
    process_condition_id: str = Field(min_length=1)
    application_environment_id: str = Field(min_length=1)
    measurements: tuple[CoatingQualityMeasurement, ...] = Field(min_length=1)
    cure_heat_history: tuple[CoatingCureHeatInterval, ...] = Field(min_length=1)
    profile: CallerCoatingCampaignProfile
    campaign_lot_substrate_surface_prep_batch_and_process_identity_reviewed: bool
    metric_definitions_units_replicates_uncertainty_and_provenance_reviewed: bool
    cure_heat_clock_temperature_and_environment_reviewed: bool
    caller_profile_authority_identity_and_rules_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_unique_history(self):
        ids = [row.measurement_id for row in self.measurements]
        if len(ids) != len(set(ids)):
            raise ValueError("coating measurement IDs must be unique")
        intervals = [row.interval_id for row in self.cure_heat_history]
        if len(intervals) != len(set(intervals)):
            raise ValueError("coating cure/heat interval IDs must be unique")
        positions = [row.sequence_position for row in self.cure_heat_history]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("coating cure/heat intervals require consecutive positions")
        for first, second in zip(self.cure_heat_history, self.cure_heat_history[1:], strict=False):
            if second.start_time_s < first.end_time_s or second.clock_id != first.clock_id:
                raise ValueError("coating cure/heat intervals require one nonoverlapping clock")
        return self


class CoatingCampaignFinding(Contract):
    rule_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    outcome: Literal["pass", "fail", "review", "insufficient_evidence"]
    observed_value: float | str | None
    unit_token: str
    evaluated_lower: float | None = None
    evaluated_upper: float | None = None
    basis: str = Field(min_length=1)


class CoatingCampaignAssessmentResult(Contract):
    schema_version: Literal["matintegrity.coating_campaign_profile.v1"] = (
        "matintegrity.coating_campaign_profile.v1"
    )
    model_id: Literal["fabrication.coating_campaign_lot_profile_assessment"] = MODEL_ID
    assessment_id: str
    campaign_id: str
    coating_lot_id: str
    profile_id: str
    disposition: Disposition
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    findings: tuple[CoatingCampaignFinding, ...]
    review_reasons: tuple[str, ...]
    insufficient_evidence_reasons: tuple[str, ...]
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    standard_or_code_qualification_claim: Literal[False] = False
    physical_validation_claim: Literal[False] = False
    notes: tuple[str, ...] = Field(min_length=1)

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"result_digest"})

    @model_validator(mode="after")
    def bound_digest(self, info: ValidationInfo):
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.result_digest
        ):
            raise ValueError("coating campaign result digest does not match its content")
        return self


def assess_coating_campaign(x: CoatingCampaignAssessment) -> CoatingCampaignAssessmentResult:
    """Aggregate campaign evidence and apply only caller-owned lot-release rules."""

    p = x.profile
    reviews, insufficient, findings = [], [], []
    for reviewed, reason in (
        (p.profile_reviewed, "caller coating profile was not reviewed"),
        (
            x.campaign_lot_substrate_surface_prep_batch_and_process_identity_reviewed,
            "campaign, lot, substrate, surface preparation, batch or process identity was not reviewed",
        ),
        (
            x.metric_definitions_units_replicates_uncertainty_and_provenance_reviewed,
            "measurement definitions, units, replicates, uncertainty or provenance were not reviewed",
        ),
        (x.cure_heat_clock_temperature_and_environment_reviewed, "cure/heat history was not reviewed"),
        (
            x.caller_profile_authority_identity_and_rules_reviewed,
            "caller profile authority, identity or rules were not reviewed",
        ),
    ):
        if not reviewed:
            insufficient.append(reason)
    identities = (
        (x.substrate_condition_id, p.permitted_substrate_condition_ids, "substrate"),
        (x.surface_preparation_id, p.permitted_surface_preparation_ids, "surface_preparation"),
        (x.coating_system_id, p.permitted_coating_system_ids, "coating_system"),
        (x.process_condition_id, p.permitted_process_condition_ids, "process_condition"),
        (x.application_environment_id, p.permitted_environment_ids, "application_environment"),
    )
    for observed, allowed, name in identities:
        outcome = "pass" if observed in allowed else "review"
        if outcome == "review":
            reviews.append(f"{name} outside caller profile")
        findings.append(
            CoatingCampaignFinding(
                rule_id=name,
                target_id=x.campaign_id,
                outcome=outcome,
                observed_value=observed,
                unit_token="identity",
                basis="caller permitted-identity list",
            )
        )
    for interval in x.cure_heat_history:
        duration = interval.end_time_s - interval.start_time_s
        within = (
            interval.environment_id in p.permitted_environment_ids
            and p.minimum_cure_temperature_k <= interval.minimum_temperature_k
            and interval.maximum_temperature_k <= p.maximum_cure_temperature_k
            and duration <= p.maximum_cure_interval_s
        )
        findings.append(
            CoatingCampaignFinding(
                rule_id="cure_heat_history",
                target_id=interval.interval_id,
                outcome="pass" if within else "fail",
                observed_value=interval.maximum_temperature_k,
                unit_token="K",
                basis="caller cure/heat environment, temperature and duration envelope",
            )
        )
    for rule in p.metric_rules:
        rows = [
            row
            for row in x.measurements
            if row.metric_kind == rule.metric_kind
            and row.metric_id == rule.metric_id
            and row.unit_token == rule.unit_token
        ]
        groups: dict[str, list[CoatingQualityMeasurement]] = {}
        for row in rows:
            groups.setdefault(row.replicate_group_id, []).append(row)
        if not groups:
            outcome = rule.missing_disposition
            (reviews if outcome == "review" else insufficient).append(
                f"{rule.rule_id} lacks exact metric/unit evidence"
            )
            continue
        for group_id, group in sorted(groups.items()):
            available = [row for row in group if row.status == "available"]
            if len(available) < rule.minimum_replicates_per_group:
                outcome = rule.missing_disposition
                (reviews if outcome == "review" else insufficient).append(
                    f"{rule.rule_id}:{group_id} has insufficient valid replicates"
                )
                findings.append(
                    CoatingCampaignFinding(
                        rule_id=rule.rule_id,
                        target_id=group_id,
                        outcome=outcome,
                        observed_value=None,
                        unit_token=rule.unit_token,
                        basis="caller minimum replicate count not met",
                    )
                )
                continue
            values = [row.value for row in available]
            if rule.aggregation == "individual":
                selected = [(row.measurement_id, row.value, row.standard_uncertainty) for row in available]
            else:
                aggregate = {
                    "replicate_mean": fmean(values),
                    "replicate_minimum": min(values),
                    "replicate_maximum": max(values),
                }[rule.aggregation]
                repeatability = pstdev(values) / math.sqrt(len(values)) if len(values) > 1 else 0.0
                measurement_u = math.sqrt(sum(row.standard_uncertainty**2 for row in available)) / len(
                    available
                )
                selected = [(group_id, aggregate, math.sqrt(repeatability**2 + measurement_u**2))]
            for target, value, uncertainty in selected:
                span = (
                    rule.uncertainty_coverage_factor * uncertainty
                    if rule.uncertainty_policy == "interval_must_fit"
                    else 0.0
                )
                low, high = value - span, value + span
                within = (rule.minimum_inclusive is None or low >= rule.minimum_inclusive) and (
                    rule.maximum_inclusive is None or high <= rule.maximum_inclusive
                )
                findings.append(
                    CoatingCampaignFinding(
                        rule_id=rule.rule_id,
                        target_id=target,
                        outcome="pass" if within else "fail",
                        observed_value=value,
                        unit_token=rule.unit_token,
                        evaluated_lower=low,
                        evaluated_upper=high,
                        basis=f"caller {rule.aggregation} rule with {rule.uncertainty_policy}",
                    )
                )
    if insufficient:
        disposition: Disposition = "insufficient_evidence"
    elif any(row.outcome == "fail" for row in findings):
        disposition = "reject"
    elif reviews or any(row.outcome == "review" for row in findings):
        disposition = "review"
    else:
        disposition = "accept"
    values = {
        "assessment_id": x.assessment_id,
        "campaign_id": x.campaign_id,
        "coating_lot_id": x.coating_lot_id,
        "profile_id": p.profile_id,
        "disposition": disposition,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
        "findings": tuple(findings),
        "review_reasons": tuple(dict.fromkeys(reviews)),
        "insufficient_evidence_reasons": tuple(dict.fromkeys(insufficient)),
        "notes": (
            "Campaign aggregation consumes caller/provider measurements; it does not repeat adhesion, segmentation, thickness or porosity algorithms.",
            "Only caller-owned identity, cure-history and metric rules are applied; no standard limit or lot-release table is embedded.",
            "The disposition is not code qualification, physical validation, coating life or failure probability.",
        ),
    }
    unsigned = CoatingCampaignAssessmentResult.model_validate(
        {**values, "result_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return CoatingCampaignAssessmentResult.model_validate(
        {**values, "result_digest": canonical_digest(unsigned.digest_payload())}
    )

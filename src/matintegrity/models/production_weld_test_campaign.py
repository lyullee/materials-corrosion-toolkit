"""Caller-profile production weld test campaign evidence."""

from __future__ import annotations

import math
from statistics import fmean, pstdev
from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

Disposition = Literal["accept", "reject", "review", "insufficient_evidence"]
MODEL_ID = "welding.production_weld_test_campaign_evidence"
SOURCE_ID = "authored_production_weld_test_campaign_profile"


class ProductionWeldIdentity(Contract):
    weld_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    wps_id: str = Field(min_length=1)
    wps_revision: str = Field(min_length=1)
    welder_ids: tuple[str, ...] = Field(min_length=1)
    consumable_lot_ids: tuple[str, ...] = Field(min_length=1)
    base_material_heat_ids: tuple[str, ...] = Field(min_length=1)
    identity_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class WeldCouponSpecimen(Contract):
    specimen_id: str = Field(min_length=1)
    coupon_id: str = Field(min_length=1)
    weld_id: str = Field(min_length=1)
    extraction_location_id: str = Field(min_length=1)
    extraction_orientation: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    extraction_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class WeldTestMeasurement(Contract):
    measurement_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    replicate_group_id: str = Field(min_length=1)
    test_kind: Literal["bend", "tensile", "impact", "hardness", "macro", "nde", "chemistry", "user_defined"]
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
                raise ValueError("available weld-test measurements require value, uncertainty and digest")
        elif (
            self.value is not None
            or self.standard_uncertainty is not None
            or self.result_digest is not None
            or not self.missing_or_invalid_basis
        ):
            raise ValueError("missing or invalid weld-test measurements require a basis and no value")
        return self


class CallerWeldTestCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    test_kind: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    aggregation: Literal["individual", "replicate_mean", "replicate_minimum", "replicate_maximum"]
    minimum_inclusive: float | None = None
    maximum_inclusive: float | None = None
    uncertainty_policy: Literal["point_value", "interval_must_fit"]
    uncertainty_coverage_factor: Positive = 1.0
    minimum_replicates: int = Field(ge=1)
    minimum_independent_source_groups: int = Field(ge=1)
    missing_disposition: Literal["review", "insufficient_evidence"]
    description: str = Field(min_length=1)

    @model_validator(mode="after")
    def bounds(self):
        if self.minimum_inclusive is None and self.maximum_inclusive is None:
            raise ValueError("weld-test criteria require at least one caller bound")
        if (
            self.minimum_inclusive is not None
            and self.maximum_inclusive is not None
            and self.maximum_inclusive < self.minimum_inclusive
        ):
            raise ValueError("weld-test criterion bounds must be ordered")
        return self


class CallerProductionWeldTestProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    permitted_wps_ids: tuple[str, ...] = Field(min_length=1)
    permitted_consumable_lot_ids: tuple[str, ...] = Field(min_length=1)
    permitted_base_material_heat_ids: tuple[str, ...] = Field(min_length=1)
    criteria: tuple[CallerWeldTestCriterion, ...] = Field(min_length=1)
    profile_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique(self):
        ids = [row.criterion_id for row in self.criteria]
        if len(ids) != len(set(ids)):
            raise ValueError("weld-test criterion IDs must be unique")
        return self


class ProductionWeldTestCampaign(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    welds: tuple[ProductionWeldIdentity, ...] = Field(min_length=1)
    specimens: tuple[WeldCouponSpecimen, ...] = Field(min_length=1)
    measurements: tuple[WeldTestMeasurement, ...] = Field(min_length=1)
    profile: CallerProductionWeldTestProfile
    weld_joint_wps_welder_consumable_and_heat_identity_reviewed: bool
    coupon_specimen_extraction_location_and_orientation_reviewed: bool
    test_metric_units_uncertainty_status_and_provenance_reviewed: bool
    replicate_source_and_independence_groups_reviewed: bool
    caller_profile_authority_and_criteria_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked(self):
        weld_ids = [row.weld_id for row in self.welds]
        specimen_ids = [row.specimen_id for row in self.specimens]
        measurement_ids = [row.measurement_id for row in self.measurements]
        for ids, label in ((weld_ids, "weld"), (specimen_ids, "specimen"), (measurement_ids, "measurement")):
            if len(ids) != len(set(ids)):
                raise ValueError(f"production {label} IDs must be unique")
        if any(row.weld_id not in weld_ids for row in self.specimens):
            raise ValueError("specimens must reference declared production welds")
        if any(row.specimen_id not in specimen_ids for row in self.measurements):
            raise ValueError("measurements must reference declared specimens")
        group_partitions: dict[str, set[str]] = {}
        specimen_by_id = {row.specimen_id: row for row in self.specimens}
        for row in self.measurements:
            specimen = specimen_by_id[row.specimen_id]
            group_partitions.setdefault(row.replicate_group_id, set()).add(specimen.independence_group_id)
        if any(len(values) < 1 for values in group_partitions.values()):
            raise ValueError("replicate groups require independence-group lineage")
        return self


class WeldTestFinding(Contract):
    criterion_id: str
    target_id: str
    outcome: Literal["pass", "fail", "review", "insufficient_evidence"]
    observed_value: float | str | None
    unit_token: str
    evaluated_lower: float | None = None
    evaluated_upper: float | None = None
    basis: str


class ProductionWeldTestCampaignResult(Contract):
    schema_version: Literal["matintegrity.production_weld_test_campaign.v1"] = (
        "matintegrity.production_weld_test_campaign.v1"
    )
    model_id: Literal["welding.production_weld_test_campaign_evidence"] = MODEL_ID
    assessment_id: str
    campaign_id: str
    profile_id: str
    disposition: Disposition
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    findings: tuple[WeldTestFinding, ...]
    review_reasons: tuple[str, ...]
    insufficient_evidence_reasons: tuple[str, ...]
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    wps_or_code_qualification_claim: Literal[False] = False
    strength_conversion_or_standard_acceptance_claim: Literal[False] = False
    notes: tuple[str, ...] = Field(min_length=1)

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"result_digest"})

    @model_validator(mode="after")
    def digest(self, info: ValidationInfo):
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.result_digest
        ):
            raise ValueError("production weld-test result digest does not match its content")
        return self


def assess_production_weld_tests(x: ProductionWeldTestCampaign) -> ProductionWeldTestCampaignResult:
    p = x.profile
    reviews, insufficient, findings = [], [], []
    for reviewed, reason in (
        (p.profile_reviewed, "caller profile was not reviewed"),
        (x.weld_joint_wps_welder_consumable_and_heat_identity_reviewed, "weld identity was not reviewed"),
        (
            x.coupon_specimen_extraction_location_and_orientation_reviewed,
            "specimen extraction was not reviewed",
        ),
        (x.test_metric_units_uncertainty_status_and_provenance_reviewed, "test evidence was not reviewed"),
        (
            x.replicate_source_and_independence_groups_reviewed,
            "replicate/source independence was not reviewed",
        ),
        (x.caller_profile_authority_and_criteria_reviewed, "caller criteria authority was not reviewed"),
        (all(r.identity_reviewed for r in x.welds), "one or more weld identities were not reviewed"),
        (
            all(r.extraction_reviewed for r in x.specimens),
            "one or more specimen extractions were not reviewed",
        ),
    ):
        if not reviewed:
            insufficient.append(reason)
    for weld in x.welds:
        if (
            weld.wps_id not in p.permitted_wps_ids
            or not set(weld.consumable_lot_ids).issubset(p.permitted_consumable_lot_ids)
            or not set(weld.base_material_heat_ids).issubset(p.permitted_base_material_heat_ids)
        ):
            reviews.append(f"weld {weld.weld_id} identity outside caller profile")
    specimen_by_id = {r.specimen_id: r for r in x.specimens}
    for c in p.criteria:
        rows = [
            r
            for r in x.measurements
            if r.test_kind == c.test_kind and r.metric_id == c.metric_id and r.unit_token == c.unit_token
        ]
        groups: dict[str, list[WeldTestMeasurement]] = {}
        for r in rows:
            groups.setdefault(r.replicate_group_id, []).append(r)
        if not groups:
            outcome = c.missing_disposition
            (reviews if outcome == "review" else insufficient).append(
                f"{c.criterion_id} lacks exact metric/unit evidence"
            )
            continue
        for gid, group in sorted(groups.items()):
            avail = [r for r in group if r.status == "available"]
            sources = {specimen_by_id[r.specimen_id].source_group_id for r in avail}
            independence = {specimen_by_id[r.specimen_id].independence_group_id for r in avail}
            if (
                len(avail) < c.minimum_replicates
                or len(sources) < c.minimum_independent_source_groups
                or len(independence) < c.minimum_independent_source_groups
            ):
                outcome = c.missing_disposition
                (reviews if outcome == "review" else insufficient).append(
                    f"{c.criterion_id}:{gid} lacks replicate/source support"
                )
                findings.append(
                    WeldTestFinding(
                        criterion_id=c.criterion_id,
                        target_id=gid,
                        outcome=outcome,
                        observed_value=None,
                        unit_token=c.unit_token,
                        basis="caller replicate and independent-source minimum not met",
                    )
                )
                continue
            vals = [r.value for r in avail]
            coverage = c.uncertainty_coverage_factor if c.uncertainty_policy == "interval_must_fit" else 0.0
            if c.aggregation == "individual":
                selected = [
                    (
                        r.measurement_id,
                        r.value,
                        r.value - coverage * r.standard_uncertainty,
                        r.value + coverage * r.standard_uncertainty,
                    )
                    for r in avail
                ]
            elif c.aggregation == "replicate_mean":
                value = fmean(vals)
                rep = pstdev(vals) / math.sqrt(len(vals)) if len(vals) > 1 else 0.0
                mu = math.sqrt(sum(r.standard_uncertainty**2 for r in avail)) / len(avail)
                span = coverage * math.sqrt(rep**2 + mu**2)
                selected = [(gid, value, value - span, value + span)]
            else:
                extreme = min if c.aggregation == "replicate_minimum" else max
                # Extrema propagate input intervals, not a standard error of a mean.
                low = extreme(r.value - coverage * r.standard_uncertainty for r in avail)
                high = extreme(r.value + coverage * r.standard_uncertainty for r in avail)
                selected = [(gid, extreme(vals), low, high)]
            for target, value, low, high in selected:
                within = (c.minimum_inclusive is None or low >= c.minimum_inclusive) and (
                    c.maximum_inclusive is None or high <= c.maximum_inclusive
                )
                findings.append(
                    WeldTestFinding(
                        criterion_id=c.criterion_id,
                        target_id=target,
                        outcome="pass" if within else "fail",
                        observed_value=value,
                        unit_token=c.unit_token,
                        evaluated_lower=low,
                        evaluated_upper=high,
                        basis=f"caller {c.aggregation} criterion with {c.uncertainty_policy}",
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
            "Only caller-owned production-test criteria are applied; no code or WPS qualification is inferred.",
            "Weld identity, specimen extraction, test units, invalid/missing states, uncertainty and source independence remain traceable.",
            "No strength conversion, standard acceptance, life or failure probability is calculated.",
        ),
    )
    unsigned = ProductionWeldTestCampaignResult.model_validate(
        {**values, "result_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return ProductionWeldTestCampaignResult.model_validate(
        {**values, "result_digest": canonical_digest(unsigned.digest_payload())}
    )


def _calculation(x):
    r = assess_production_weld_tests(x)
    return Calculation(values=r.model_dump(mode="json"), notes=r.notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("production weld-test campaign asset and location must match run context")

    return [
        ModelSpec(
            MODEL_ID,
            ProductionWeldTestCampaign,
            _calculation,
            {"disposition": "1", "findings": "mixed", "result_digest": "1"},
            ("Caller criteria only; no WPS or code qualification claim.",),
            (SOURCE_ID,),
            context_validator=same_identity,
            version="1.0.2",
        )
    ]

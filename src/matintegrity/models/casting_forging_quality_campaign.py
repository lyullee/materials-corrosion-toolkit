"""Caller-profile campaign audit for casting and forging quality evidence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

ProductKind = Literal["casting", "forging"]
ObservationCategory = Literal[
    "dimensional",
    "surface",
    "internal",
    "nde",
    "macro",
    "micro",
    "chemistry",
    "mechanical",
]
CampaignMetric = Literal[
    "product_count",
    "sample_count",
    "replicate_group_count",
    "independent_source_group_count",
    "valid_observation_fraction",
]


class ManufacturingHeatTreatment(Contract):
    treatment_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    treatment_type: str = Field(min_length=1)
    furnace_or_provider_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_recorded_temperature_K: Positive
    maximum_recorded_temperature_K: Positive
    temperature_uncertainty_K: Nonnegative
    cooling_route_definition: str = Field(min_length=1)
    controller_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    treatment_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_treatment(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("heat treatment must have positive duration")
        if self.maximum_recorded_temperature_K < self.minimum_recorded_temperature_K:
            raise ValueError("heat-treatment temperature bounds must be ordered")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid heat-treatment records require a basis")
        return self


class ManufacturedProductEvidence(Contract):
    product_id: str = Field(min_length=1)
    product_kind: ProductKind
    heat_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    product_form_descriptor: str = Field(min_length=1)
    manufacturing_route_id: str = Field(min_length=1)
    manufacturing_route_revision: str = Field(min_length=1)
    route_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    forging_ratio: Positive | None = None
    forging_ratio_definition: str | None = Field(default=None, min_length=1)
    forging_ratio_unit_token: str | None = Field(default=None, min_length=1)
    casting_process_id: str | None = Field(default=None, min_length=1)
    casting_process_definition: str | None = Field(default=None, min_length=1)
    heat_treatments: tuple[ManufacturingHeatTreatment, ...] = Field(min_length=1)
    product_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def route_specific_and_ordered(self):
        forging_fields = (self.forging_ratio, self.forging_ratio_definition, self.forging_ratio_unit_token)
        casting_fields = (self.casting_process_id, self.casting_process_definition)
        if self.product_kind == "forging":
            if any(value is None for value in forging_fields) or any(
                value is not None for value in casting_fields
            ):
                raise ValueError("forging products require only complete caller forging-ratio identity")
        elif any(value is not None for value in forging_fields) or any(
            value is None for value in casting_fields
        ):
            raise ValueError("casting products require only complete casting-process identity")
        treatment_ids = [row.treatment_id for row in self.heat_treatments]
        sequence = [row.sequence_index for row in self.heat_treatments]
        if len(set(treatment_ids)) != len(treatment_ids) or len(set(sequence)) != len(sequence):
            raise ValueError("heat-treatment identities and sequence indices must be unique")
        if tuple(sorted(self.heat_treatments, key=lambda row: row.sequence_index)) != self.heat_treatments:
            raise ValueError("heat treatments must be supplied in sequence order")
        return self


class ProductSampleEvidence(Contract):
    sample_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    sampling_plan_id: str = Field(min_length=1)
    physical_location_definition: str = Field(min_length=1)
    orientation_id: str = Field(min_length=1)
    thickness_or_depth_coordinate: float
    coordinate_unit_token: str = Field(min_length=1)
    replicate_group_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    sampling_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class ProductQualityObservation(Contract):
    observation_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    observation_category: ObservationCategory
    examination_or_test_method_id: str = Field(min_length=1)
    method_revision: str = Field(min_length=1)
    metric_id: str | None = Field(default=None, min_length=1)
    metric_definition: str | None = Field(default=None, min_length=1)
    value: float | None = None
    unit_token: str | None = Field(default=None, min_length=1)
    expanded_uncertainty: Nonnegative | None = None
    uncertainty_basis: str | None = Field(default=None, min_length=1)
    reported_finding: str = Field(min_length=1)
    caller_disposition_id: str | None = Field(default=None, min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    raw_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observation_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_observation(self):
        quantitative = (
            self.metric_id,
            self.metric_definition,
            self.value,
            self.unit_token,
            self.expanded_uncertainty,
            self.uncertainty_basis,
        )
        if any(value is not None for value in quantitative) and any(value is None for value in quantitative):
            raise ValueError("quantitative product observations require metric, unit, uncertainty, and basis")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid product quality observations require a basis")
        return self


class CastingForgingQualityCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    criterion_source: Literal["campaign", "observation"]
    campaign_metric: CampaignMetric | None = None
    observation_category: ObservationCategory | None = None
    observation_metric_id: str | None = Field(default=None, min_length=1)
    aggregation: Literal["minimum", "maximum"]
    direction: Literal["minimum", "maximum"]
    accept_limit: float
    reject_limit: float
    unit_token: str = Field(min_length=1)
    criterion_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_criterion(self):
        if self.criterion_source == "campaign":
            if (
                self.campaign_metric is None
                or self.observation_category is not None
                or self.observation_metric_id is not None
            ):
                raise ValueError("campaign criteria require only a campaign metric")
        elif (
            self.campaign_metric is not None
            or self.observation_category is None
            or self.observation_metric_id is None
        ):
            raise ValueError("observation criteria require category and metric identity")
        if self.direction == "minimum" and self.reject_limit > self.accept_limit:
            raise ValueError("minimum quality criteria require reject <= accept")
        if self.direction == "maximum" and self.reject_limit < self.accept_limit:
            raise ValueError("maximum quality criteria require accept <= reject")
        return self


class CastingForgingCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    required_product_kinds: tuple[ProductKind, ...] = Field(min_length=1)
    required_observation_categories: tuple[ObservationCategory, ...] = Field(min_length=1)
    criteria: tuple[CastingForgingQualityCriterion, ...] = Field(min_length=1)
    profile_provider_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_authority: str = Field(min_length=1)
    built_in_specification_table_used: Literal[False] = False
    minimum_forging_ratio_embedded: Literal[False] = False
    allowable_defect_rule_embedded: Literal[False] = False
    material_qualification_claimed: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_profile(self):
        if len(set(self.required_product_kinds)) != len(self.required_product_kinds):
            raise ValueError("required product kinds must be unique")
        if len(set(self.required_observation_categories)) != len(self.required_observation_categories):
            raise ValueError("required observation categories must be unique")
        ids = [row.criterion_id for row in self.criteria]
        keys = [
            (row.criterion_source, row.campaign_metric, row.observation_category, row.observation_metric_id)
            for row in self.criteria
        ]
        if len(set(ids)) != len(ids) or len(set(keys)) != len(keys):
            raise ValueError("quality criteria must have unique identities and metric sources")
        return self


class CastingForgingQualityCampaignAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    products: tuple[ManufacturedProductEvidence, ...] = Field(min_length=1)
    samples: tuple[ProductSampleEvidence, ...] = Field(min_length=1)
    observations: tuple[ProductQualityObservation, ...] = Field(min_length=1)
    caller_profile: CastingForgingCallerProfile
    product_heat_route_and_process_identity_reviewed: bool
    forging_ratio_or_casting_process_basis_reviewed: bool
    heat_treatment_sequence_and_digests_reviewed: bool
    sampling_location_orientation_and_groups_reviewed: bool
    observation_method_units_uncertainty_and_findings_reviewed: bool
    replicate_source_and_independence_claims_reviewed: bool
    provider_provenance_and_digests_reviewed: bool
    caller_profile_reviewed: bool
    invalid_and_missing_records_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        identities = {
            "product": [row.product_id for row in self.products],
            "heat": [row.heat_id for row in self.products],
            "sample": [row.sample_id for row in self.samples],
            "observation": [row.observation_id for row in self.observations],
            "raw-data digest": [row.raw_data_digest for row in self.observations],
            "observation digest": [row.observation_record_digest for row in self.observations],
        }
        for label, values in identities.items():
            if len(set(values)) != len(values):
                raise ValueError(f"casting/forging campaign {label} identities must be unique")
        product_ids = {row.product_id for row in self.products}
        sample_by_id = {row.sample_id: row for row in self.samples}
        if {row.product_id for row in self.samples} - product_ids:
            raise ValueError("samples must reference declared campaign products")
        for row in self.observations:
            sample = sample_by_id.get(row.sample_id)
            if sample is None or row.product_id != sample.product_id:
                raise ValueError("observations must match their declared sample and product")
        return self


class CastingForgingQualityCampaignReport(Contract):
    report_schema_version: Literal["matintegrity.casting_forging_quality_campaign_report.v1"] = (
        "matintegrity.casting_forging_quality_campaign_report.v1"
    )
    assessment_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    campaign_outcome: Literal["accept", "review", "reject", "insufficient_evidence"]
    caller_profile_id: str = Field(min_length=1)
    metric_values: dict[str, float]
    criterion_findings: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_profile_only: Literal[True] = True
    specification_or_forging_ratio_limit_embedded: Literal[False] = False
    automatic_defect_acceptance: Literal[False] = False
    material_qualification: Literal[False] = False
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"report_digest"})

    @model_validator(mode="after")
    def digest_is_bound(self, info: ValidationInfo):
        if not (
            isinstance(info.context, dict) and info.context.get("allow_unbound_digest")
        ) and self.report_digest != canonical_digest(self.digest_payload()):
            raise ValueError("casting/forging campaign report digest does not match content")
        return self


def _bound_report(**payload: Any) -> CastingForgingQualityCampaignReport:
    unsigned = CastingForgingQualityCampaignReport.model_validate(
        {**payload, "report_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return CastingForgingQualityCampaignReport.model_validate(
        {**payload, "report_digest": canonical_digest(unsigned.digest_payload())}
    )


def _criterion_outcome(value: float, row: CastingForgingQualityCriterion) -> str:
    if row.direction == "minimum":
        return "accept" if value >= row.accept_limit else "reject" if value <= row.reject_limit else "review"
    return "accept" if value <= row.accept_limit else "reject" if value >= row.reject_limit else "review"


def casting_forging_quality_campaign(x: CastingForgingQualityCampaignAssessment) -> Calculation:
    review_fields = (
        "product_heat_route_and_process_identity_reviewed",
        "forging_ratio_or_casting_process_basis_reviewed",
        "heat_treatment_sequence_and_digests_reviewed",
        "sampling_location_orientation_and_groups_reviewed",
        "observation_method_units_uncertainty_and_findings_reviewed",
        "replicate_source_and_independence_claims_reviewed",
        "provider_provenance_and_digests_reviewed",
        "caller_profile_reviewed",
        "invalid_and_missing_records_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    invalid_treatments = [
        row.treatment_id for product in x.products for row in product.heat_treatments if not row.record_valid
    ]
    invalid_observations = [row.observation_id for row in x.observations if not row.record_valid]
    profile = x.caller_profile
    missing_product_kinds = sorted(
        set(profile.required_product_kinds) - {row.product_kind for row in x.products}
    )
    missing_categories = sorted(
        set(profile.required_observation_categories) - {row.observation_category for row in x.observations}
    )
    input_digest = canonical_digest(x.model_dump(mode="json"))
    diagnostics: dict[str, Any] = {
        "missing_reviews": missing_reviews,
        "invalid_heat_treatment_ids": invalid_treatments,
        "invalid_observation_ids": invalid_observations,
        "missing_required_product_kinds": missing_product_kinds,
        "missing_required_observation_categories": missing_categories,
        "product_ids": [row.product_id for row in x.products],
        "heat_ids": [row.heat_id for row in x.products],
        "sample_ids": [row.sample_id for row in x.samples],
        "raw_data_digests": [row.raw_data_digest for row in x.observations],
        "observation_record_digests": [row.observation_record_digest for row in x.observations],
    }
    if (
        missing_reviews
        or invalid_treatments
        or invalid_observations
        or missing_product_kinds
        or missing_categories
    ):
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            campaign_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            metric_values={},
            criterion_findings=(),
            diagnostics=diagnostics,
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Complete reviewed campaign evidence is required.",),
        )

    campaign_values = {
        "product_count": float(len(x.products)),
        "sample_count": float(len(x.samples)),
        "replicate_group_count": float(len({row.replicate_group_id for row in x.samples})),
        "independent_source_group_count": float(
            len({(row.source_group_id, row.independence_group_id) for row in x.samples})
        ),
        "valid_observation_fraction": sum(row.record_valid for row in x.observations) / len(x.observations),
    }
    campaign_units = {key: "1" if key == "valid_observation_fraction" else "count" for key in campaign_values}
    metric_values: dict[str, float] = {}
    metric_units: dict[str, str] = {}
    missing_criteria: list[str] = []
    unit_conflicts: list[str] = []
    for criterion in profile.criteria:
        if criterion.criterion_source == "campaign":
            key = f"campaign:{criterion.campaign_metric}"
            value = campaign_values[criterion.campaign_metric]
            unit = campaign_units[criterion.campaign_metric]
        else:
            key = f"observation:{criterion.observation_category}:{criterion.observation_metric_id}"
            matching = [
                row
                for row in x.observations
                if row.observation_category == criterion.observation_category
                and row.metric_id == criterion.observation_metric_id
            ]
            if not matching:
                missing_criteria.append(criterion.criterion_id)
                continue
            units = {row.unit_token for row in matching}
            if units != {criterion.unit_token}:
                unit_conflicts.append(criterion.criterion_id)
                continue
            values = [row.value for row in matching]
            value = min(values) if criterion.aggregation == "minimum" else max(values)
            unit = criterion.unit_token
        if unit != criterion.unit_token:
            unit_conflicts.append(criterion.criterion_id)
            continue
        metric_values[key] = value
        metric_units[key] = unit
    if missing_criteria or unit_conflicts:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            campaign_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            metric_values=metric_values,
            criterion_findings=(),
            diagnostics={
                **diagnostics,
                "missing_criterion_evidence_ids": missing_criteria,
                "criterion_unit_conflict_ids": unit_conflicts,
            },
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Every caller criterion requires exact-unit evidence.",),
        )

    def criterion_key(row: CastingForgingQualityCriterion) -> str:
        if row.criterion_source == "campaign":
            return f"campaign:{row.campaign_metric}"
        return f"observation:{row.observation_category}:{row.observation_metric_id}"

    findings = tuple(
        {
            "criterion_id": row.criterion_id,
            "metric_key": criterion_key(row),
            "aggregation": row.aggregation,
            "value": metric_values[criterion_key(row)],
            "unit": metric_units[criterion_key(row)],
            "direction": row.direction,
            "accept_limit": row.accept_limit,
            "reject_limit": row.reject_limit,
            "outcome": _criterion_outcome(metric_values[criterion_key(row)], row),
            "criterion_basis": row.criterion_basis,
        }
        for row in profile.criteria
    )
    outcomes = {row["outcome"] for row in findings}
    campaign_outcome = "reject" if "reject" in outcomes else "review" if "review" in outcomes else "accept"
    report = _bound_report(
        assessment_id=x.assessment_id,
        campaign_id=x.campaign_id,
        campaign_outcome=campaign_outcome,
        caller_profile_id=profile.profile_id,
        metric_values=metric_values,
        criterion_findings=findings,
        diagnostics=diagnostics,
        input_digest=input_digest,
    )
    return Calculation(
        status="computed",
        values=report.model_dump(),
        notes=(
            "Accept, review and reject reflect caller-authored campaign criteria only.",
            "Forging ratio, casting process, observations, findings and uncertainty remain caller evidence.",
            "No specification table, minimum forging ratio, allowable defect rule, material qualification, life, or failure probability is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("casting/forging campaign asset and location must match run context")

    return [
        ModelSpec(
            "materials.casting_forging_quality",
            CastingForgingQualityCampaignAssessment,
            casting_forging_quality_campaign,
            {
                "report_schema_version": "1",
                "assessment_id": "1",
                "campaign_id": "1",
                "campaign_outcome": "1",
                "caller_profile_id": "1",
                "metric_values": "mixed",
                "criterion_findings": "mixed",
                "diagnostics": "mixed",
                "input_digest": "1",
                "caller_profile_only": "1",
                "specification_or_forging_ratio_limit_embedded": "1",
                "automatic_defect_acceptance": "1",
                "material_qualification": "1",
                "report_digest": "1",
            },
            (
                "Product, heat, route, process, heat treatment, sampling and observation evidence remains caller supplied.",
                "No embedded specification, forging ratio minimum, defect acceptance, or material qualification is produced.",
            ),
            ("authored_casting_forging_quality_campaign_audit",),
            context_validator=same_identity,
        )
    ]

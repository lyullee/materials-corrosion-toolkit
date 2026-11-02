"""Caller-profile evidence campaign audit for corrosion under insulation inspections."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

EventKind = Literal["access", "inspection", "repair", "reinstatement", "other"]
ObservationCategory = Literal["moisture", "visual", "thickness", "nde"]
CampaignMetric = Literal[
    "access_region_count",
    "coverage_fraction",
    "observation_count",
    "independent_source_group_count",
]


class CUIScopeIdentity(Contract):
    zone_id: str = Field(min_length=1)
    component_or_circuit_id: str = Field(min_length=1)
    physical_scope_definition: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    substrate_material_id: str = Field(min_length=1)
    substrate_material_condition_id: str = Field(min_length=1)
    service_id: str = Field(min_length=1)
    service_medium_definition: str = Field(min_length=1)
    minimum_service_temperature_K: Positive
    maximum_service_temperature_K: Positive
    insulation_system_id: str = Field(min_length=1)
    insulation_material_id: str = Field(min_length=1)
    insulation_condition_id: str = Field(min_length=1)
    jacketing_system_id: str = Field(min_length=1)
    jacketing_condition_id: str = Field(min_length=1)
    coating_system_id: str = Field(min_length=1)
    coating_condition_id: str = Field(min_length=1)
    external_environment_id: str = Field(min_length=1)
    external_environment_definition: str = Field(min_length=1)
    scope_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_service_temperature(self):
        if self.maximum_service_temperature_K < self.minimum_service_temperature_K:
            raise ValueError("CUI service temperature bounds must be ordered")
        return self


class CUIAccessInspectionRepairEvent(Contract):
    event_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    event_kind: EventKind
    start_time_s: Nonnegative
    end_time_s: Positive
    contractor_or_provider_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    activity_definition: str = Field(min_length=1)
    resulting_insulation_condition_id: str | None = Field(default=None, min_length=1)
    resulting_jacketing_condition_id: str | None = Field(default=None, min_length=1)
    resulting_coating_condition_id: str | None = Field(default=None, min_length=1)
    event_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    event_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_event(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("CUI campaign events require positive duration")
        condition_fields = (
            self.resulting_insulation_condition_id,
            self.resulting_jacketing_condition_id,
            self.resulting_coating_condition_id,
        )
        if self.event_kind in ("repair", "reinstatement") and any(
            value is None for value in condition_fields
        ):
            raise ValueError("repair and reinstatement events require resulting system conditions")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid CUI campaign events require a basis")
        return self


class CUIAccessCoverageRegion(Contract):
    access_region_id: str = Field(min_length=1)
    access_event_id: str = Field(min_length=1)
    physical_location_definition: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    target_extent: Positive
    accessed_extent: Nonnegative
    extent_unit_token: str = Field(min_length=1)
    coverage_uncertainty: Nonnegative
    overlap_group_id: str = Field(min_length=1)
    unaccessed_basis: str | None = Field(default=None, min_length=1)
    coverage_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_coverage(self):
        if self.accessed_extent > self.target_extent:
            raise ValueError("accessed CUI extent cannot exceed target extent")
        if self.accessed_extent < self.target_extent and not self.unaccessed_basis:
            raise ValueError("partial CUI access requires an unaccessed-area basis")
        return self


class CUIObservation(Contract):
    observation_id: str = Field(min_length=1)
    inspection_event_id: str = Field(min_length=1)
    access_region_id: str = Field(min_length=1)
    observation_category: ObservationCategory
    physical_location_definition: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    orientation_definition: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    method_revision: str = Field(min_length=1)
    metric_id: str | None = Field(default=None, min_length=1)
    metric_definition: str | None = Field(default=None, min_length=1)
    value: float | None = None
    unit_token: str | None = Field(default=None, min_length=1)
    expanded_uncertainty: Nonnegative | None = None
    uncertainty_basis: str | None = Field(default=None, min_length=1)
    reported_finding: str = Field(min_length=1)
    caller_disposition_id: str | None = Field(default=None, min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
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
            raise ValueError("quantitative CUI observations require complete metric evidence")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid CUI observations require a basis")
        return self


class CUICampaignCriterion(Contract):
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
                raise ValueError("campaign CUI criteria require only a campaign metric")
        elif (
            self.campaign_metric is not None
            or self.observation_category is None
            or self.observation_metric_id is None
        ):
            raise ValueError("observation CUI criteria require category and metric identity")
        if self.direction == "minimum" and self.reject_limit > self.accept_limit:
            raise ValueError("minimum CUI criteria require reject <= accept")
        if self.direction == "maximum" and self.reject_limit < self.accept_limit:
            raise ValueError("maximum CUI criteria require accept <= reject")
        return self


class CUICallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    required_event_kinds: tuple[EventKind, ...] = Field(min_length=1)
    required_observation_categories: tuple[ObservationCategory, ...] = Field(min_length=1)
    criteria: tuple[CUICampaignCriterion, ...] = Field(min_length=1)
    profile_provider_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_authority: str = Field(min_length=1)
    corrosion_rate_inference_claimed: Literal[False] = False
    remaining_life_claimed: Literal[False] = False
    hidden_area_extrapolation_claimed: Literal[False] = False
    risk_or_pod_claimed: Literal[False] = False
    built_in_code_or_standard_acceptance_used: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_profile(self):
        if len(set(self.required_event_kinds)) != len(self.required_event_kinds):
            raise ValueError("required CUI event kinds must be unique")
        if len(set(self.required_observation_categories)) != len(self.required_observation_categories):
            raise ValueError("required CUI observation categories must be unique")
        ids = [row.criterion_id for row in self.criteria]
        keys = [
            (row.criterion_source, row.campaign_metric, row.observation_category, row.observation_metric_id)
            for row in self.criteria
        ]
        if len(set(ids)) != len(ids) or len(set(keys)) != len(keys):
            raise ValueError("CUI criteria must have unique identities and metric sources")
        return self


class UnderInsulationCampaignAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    scope: CUIScopeIdentity
    events: tuple[CUIAccessInspectionRepairEvent, ...] = Field(min_length=1)
    coverage_regions: tuple[CUIAccessCoverageRegion, ...] = Field(min_length=1)
    observations: tuple[CUIObservation, ...] = Field(min_length=1)
    caller_profile: CUICallerProfile
    zone_insulation_jacketing_coating_material_service_environment_reviewed: bool
    ordered_access_inspection_repair_events_reviewed: bool
    access_coverage_regions_overlap_and_units_reviewed: bool
    moisture_visual_thickness_nde_observations_reviewed: bool
    locations_methods_units_uncertainty_and_findings_reviewed: bool
    source_independence_provenance_and_digests_reviewed: bool
    caller_profile_reviewed: bool
    invalid_and_missing_records_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        event_ids = [row.event_id for row in self.events]
        sequence = [row.sequence_index for row in self.events]
        region_ids = [row.access_region_id for row in self.coverage_regions]
        observation_ids = [row.observation_id for row in self.observations]
        raw_digests = [row.raw_data_digest for row in self.observations]
        result_digests = [row.observation_record_digest for row in self.observations]
        for values, label in (
            (event_ids, "event"),
            (sequence, "event sequence"),
            (region_ids, "coverage region"),
            (observation_ids, "observation"),
            (raw_digests, "raw-data digest"),
            (result_digests, "observation-record digest"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"CUI campaign {label} identities must be unique")
        if tuple(sorted(self.events, key=lambda row: row.sequence_index)) != self.events:
            raise ValueError("CUI events must be supplied in sequence order")
        event_by_id = {row.event_id: row for row in self.events}
        region_by_id = {row.access_region_id: row for row in self.coverage_regions}
        for region in self.coverage_regions:
            event = event_by_id.get(region.access_event_id)
            if event is None or event.event_kind != "access":
                raise ValueError("CUI coverage regions must reference access events")
            if region.coordinate_frame_id != self.scope.coordinate_frame_id:
                raise ValueError("CUI coverage regions must use the scope coordinate frame")
        for row in self.observations:
            event = event_by_id.get(row.inspection_event_id)
            region = region_by_id.get(row.access_region_id)
            if event is None or event.event_kind != "inspection" or region is None:
                raise ValueError("CUI observations must reference inspection events and access regions")
            if row.coordinate_frame_id != self.scope.coordinate_frame_id:
                raise ValueError("CUI observations must use the scope coordinate frame")
        return self


class UnderInsulationCampaignReport(Contract):
    report_schema_version: Literal["matintegrity.under_insulation_campaign_report.v1"] = (
        "matintegrity.under_insulation_campaign_report.v1"
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
    corrosion_rate_or_remaining_life: Literal[False] = False
    hidden_area_extrapolated: Literal[False] = False
    risk_pod_or_standard_acceptance: Literal[False] = False
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    downstream_receipt: dict[str, Any] | None = None

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"report_digest", "downstream_receipt"})

    @model_validator(mode="after")
    def digest_is_bound(self, info: ValidationInfo):
        if not (
            isinstance(info.context, dict) and info.context.get("allow_unbound_digest")
        ) and self.report_digest != canonical_digest(self.digest_payload()):
            raise ValueError("CUI campaign report digest does not match content")
        if self.downstream_receipt is not None:
            receipt = CUIEvidenceReceipt.model_validate(self.downstream_receipt)
            if (
                receipt.assessment_id != self.assessment_id
                or receipt.campaign_id != self.campaign_id
                or receipt.input_digest != self.input_digest
                or receipt.report_digest != self.report_digest
                or receipt.caller_profile_id != self.caller_profile_id
                or receipt.campaign_outcome != self.campaign_outcome
            ):
                raise ValueError("CUI downstream receipt is not bound to this report")
        return self


class CUIEvidenceReceipt(Contract):
    """Minimal digest-bound handoff for downstream risk and asset systems."""

    schema_version: Literal["matintegrity.cui_evidence_receipt.v1"] = "matintegrity.cui_evidence_receipt.v1"
    assessment_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    zone_id: str = Field(min_length=1)
    component_or_circuit_id: str = Field(min_length=1)
    scope_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_profile_id: str = Field(min_length=1)
    caller_profile_revision: str = Field(min_length=1)
    campaign_outcome: Literal["accept", "review", "reject", "insufficient_evidence"]
    coverage_fraction: Nonnegative
    observation_count: int = Field(ge=0)
    finding_outcomes: list[Literal["accept", "review", "reject"]]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    receipt_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    corrosion_rate_inferred: Literal[False] = False
    hidden_area_extrapolated: Literal[False] = False
    risk_or_failure_probability_generated: Literal[False] = False

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"receipt_digest"})

    @model_validator(mode="after")
    def digest_is_bound(self, info: ValidationInfo):
        if not (
            isinstance(info.context, dict) and info.context.get("allow_unbound_digest")
        ) and self.receipt_digest != canonical_digest(self.digest_payload()):
            raise ValueError("CUI evidence receipt digest does not match content")
        return self


def _bound_report(**payload: Any) -> UnderInsulationCampaignReport:
    unsigned = UnderInsulationCampaignReport.model_validate(
        {**payload, "report_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return UnderInsulationCampaignReport.model_validate(
        {**payload, "report_digest": canonical_digest(unsigned.digest_payload())}
    )


def _criterion_outcome(value: float, row: CUICampaignCriterion) -> str:
    if row.direction == "minimum":
        return "accept" if value >= row.accept_limit else "reject" if value <= row.reject_limit else "review"
    return "accept" if value <= row.accept_limit else "reject" if value >= row.reject_limit else "review"


def cui_evidence_receipt(
    assessment: UnderInsulationCampaignAssessment,
    report: UnderInsulationCampaignReport,
) -> CUIEvidenceReceipt:
    """Create a narrow downstream handoff after verifying the report is bound to this input."""
    expected_input_digest = canonical_digest(assessment.model_dump(mode="json"))
    if report.assessment_id != assessment.assessment_id:
        raise ValueError("CUI report assessment identity does not match input")
    if report.campaign_id != assessment.campaign_id:
        raise ValueError("CUI report campaign identity does not match input")
    if report.input_digest != expected_input_digest:
        raise ValueError("CUI report input digest does not match input")
    payload = {
        "assessment_id": assessment.assessment_id,
        "campaign_id": assessment.campaign_id,
        "asset_id": assessment.asset_id,
        "location_id": assessment.location_id,
        "zone_id": assessment.scope.zone_id,
        "component_or_circuit_id": assessment.scope.component_or_circuit_id,
        "scope_configuration_digest": assessment.scope.scope_configuration_digest,
        "caller_profile_id": report.caller_profile_id,
        "caller_profile_revision": assessment.caller_profile.profile_revision,
        "campaign_outcome": report.campaign_outcome,
        "coverage_fraction": report.metric_values.get("campaign:coverage_fraction", 0.0),
        "observation_count": len(assessment.observations),
        "finding_outcomes": [row["outcome"] for row in report.criterion_findings],
        "input_digest": report.input_digest,
        "report_digest": report.report_digest,
    }
    unsigned = CUIEvidenceReceipt.model_validate(
        {**payload, "receipt_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return CUIEvidenceReceipt.model_validate(
        {**payload, "receipt_digest": canonical_digest(unsigned.digest_payload())}
    )


def under_insulation_campaign(x: UnderInsulationCampaignAssessment) -> Calculation:
    review_fields = (
        "zone_insulation_jacketing_coating_material_service_environment_reviewed",
        "ordered_access_inspection_repair_events_reviewed",
        "access_coverage_regions_overlap_and_units_reviewed",
        "moisture_visual_thickness_nde_observations_reviewed",
        "locations_methods_units_uncertainty_and_findings_reviewed",
        "source_independence_provenance_and_digests_reviewed",
        "caller_profile_reviewed",
        "invalid_and_missing_records_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    invalid_events = [row.event_id for row in x.events if not row.record_valid]
    invalid_observations = [row.observation_id for row in x.observations if not row.record_valid]
    profile = x.caller_profile
    missing_event_kinds = sorted(set(profile.required_event_kinds) - {row.event_kind for row in x.events})
    missing_categories = sorted(
        set(profile.required_observation_categories) - {row.observation_category for row in x.observations}
    )
    extent_units = {row.extent_unit_token for row in x.coverage_regions}
    coverage_unit_conflict = len(extent_units) != 1
    input_digest = canonical_digest(x.model_dump(mode="json"))
    diagnostics: dict[str, Any] = {
        "missing_reviews": missing_reviews,
        "invalid_event_ids": invalid_events,
        "invalid_observation_ids": invalid_observations,
        "missing_required_event_kinds": missing_event_kinds,
        "missing_required_observation_categories": missing_categories,
        "coverage_extent_unit_conflict": coverage_unit_conflict,
        "access_region_ids": [row.access_region_id for row in x.coverage_regions],
        "unaccessed_region_ids": [
            row.access_region_id for row in x.coverage_regions if row.accessed_extent < row.target_extent
        ],
        "raw_data_digests": [row.raw_data_digest for row in x.observations],
        "observation_record_digests": [row.observation_record_digest for row in x.observations],
    }
    if (
        missing_reviews
        or invalid_events
        or invalid_observations
        or missing_event_kinds
        or missing_categories
        or coverage_unit_conflict
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
            values=report.model_dump()
            | {"downstream_receipt": cui_evidence_receipt(x, report).model_dump(mode="json")},
            notes=("Complete reviewed access, event, coverage, and observation evidence is required.",),
        )

    campaign_values = {
        "access_region_count": float(len(x.coverage_regions)),
        "coverage_fraction": sum(row.accessed_extent for row in x.coverage_regions)
        / sum(row.target_extent for row in x.coverage_regions),
        "observation_count": float(len(x.observations)),
        "independent_source_group_count": float(
            len({(row.source_group_id, row.independence_group_id) for row in x.observations})
        ),
    }
    campaign_units = {
        "access_region_count": "count",
        "coverage_fraction": "1",
        "observation_count": "count",
        "independent_source_group_count": "count",
    }
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
            values=report.model_dump()
            | {"downstream_receipt": cui_evidence_receipt(x, report).model_dump(mode="json")},
            notes=("Every caller criterion requires matching exact-unit evidence.",),
        )

    def criterion_key(row: CUICampaignCriterion) -> str:
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
        values=report.model_dump()
        | {"downstream_receipt": cui_evidence_receipt(x, report).model_dump(mode="json")},
        notes=(
            "Accept, review and reject reflect caller-authored campaign criteria only.",
            "Coverage and observations apply only to declared accessed regions; hidden areas are not extrapolated.",
            "No corrosion rate, remaining life, risk, POD, standard acceptance, or failure probability is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("CUI campaign asset and location must match run context")

    return [
        ModelSpec(
            "degradation.under_insulation",
            UnderInsulationCampaignAssessment,
            under_insulation_campaign,
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
                "corrosion_rate_or_remaining_life": "1",
                "hidden_area_extrapolated": "1",
                "risk_pod_or_standard_acceptance": "1",
                "report_digest": "1",
                "downstream_receipt": "mixed",
            },
            (
                "CUI scope, ordered access/inspection/repair events, explicit coverage and observations remain caller evidence.",
                "No hidden-area extrapolation, corrosion rate, life, risk, POD, or standard acceptance is produced.",
            ),
            (
                "authored_cui_inspection_evidence_campaign_audit",
                "authored_cui_digest_bound_downstream_evidence_receipt",
            ),
            context_validator=same_identity,
        )
    ]

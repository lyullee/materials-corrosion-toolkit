"""Caller-reviewed specimen and campaign audit for fracture-toughness testing.

Reported results and validity statements are retained rather than recalculated.
No published test-standard validity rule or design allowable is implemented.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

ToughnessKind = Literal["K", "J", "CTOD", "arrest", "user_defined"]
MetricId = Literal[
    "specimen_count",
    "replicate_group_count",
    "independent_source_group_count",
    "caller_valid_fraction",
    "minimum_reported_toughness",
    "maximum_expanded_uncertainty",
]


class FractureSpecimenGeometry(Contract):
    geometry_id: str = Field(min_length=1)
    specimen_type_descriptor: str = Field(min_length=1)
    width: Positive
    thickness: Positive
    net_thickness: Positive
    initial_notch_length: Nonnegative
    final_crack_length: Positive
    dimension_unit_token: str = Field(min_length=1)
    geometry_measurement_uncertainty: Nonnegative
    geometry_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent_geometry(self):
        if self.net_thickness > self.thickness:
            raise ValueError("net specimen thickness cannot exceed gross thickness")
        if self.final_crack_length <= self.initial_notch_length:
            raise ValueError("final crack length must exceed the initial notch length")
        return self


class FatiguePrecrackEvidence(Contract):
    precrack_method_id: str = Field(min_length=1)
    cycle_count: int = Field(ge=1)
    maximum_load_value: Positive
    load_unit_token: str = Field(min_length=1)
    load_ratio: float
    frequency_hz: Positive
    precrack_extension: Positive
    extension_unit_token: str = Field(min_length=1)
    precrack_front_definition: str = Field(min_length=1)
    precrack_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class CallerValidityFlag(Contract):
    flag_id: str = Field(min_length=1)
    flag_result: Literal["satisfied", "not_satisfied", "not_evaluated"]
    flag_definition: str = Field(min_length=1)
    review_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class FractureToughnessSpecimenRecord(Contract):
    record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    replicate_group_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    product_form_id: str = Field(min_length=1)
    extraction_location_definition: str = Field(min_length=1)
    notch_orientation_id: str = Field(min_length=1)
    crack_plane_orientation_id: str = Field(min_length=1)
    crack_growth_direction_id: str = Field(min_length=1)
    geometry: FractureSpecimenGeometry
    test_temperature_K: Positive
    expanded_temperature_uncertainty_K: Nonnegative
    environment_id: str = Field(min_length=1)
    loading_mode: str = Field(min_length=1)
    loading_control_definition: str = Field(min_length=1)
    loading_rate_value: Positive
    loading_rate_unit_token: str = Field(min_length=1)
    expanded_loading_rate_uncertainty: Nonnegative
    fatigue_precrack: FatiguePrecrackEvidence
    toughness_kind: ToughnessKind
    user_defined_toughness_description: str | None = None
    test_method_id: str = Field(min_length=1)
    test_method_revision: str = Field(min_length=1)
    reported_toughness: Nonnegative
    toughness_unit_token: str = Field(min_length=1)
    expanded_toughness_uncertainty: Nonnegative
    uncertainty_coverage_definition: str = Field(min_length=1)
    caller_validity_flags: tuple[CallerValidityFlag, ...] = Field(min_length=1)
    caller_overall_valid: bool
    caller_validity_record_id: str = Field(min_length=1)
    invalid_or_limiting_basis: str | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    raw_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_result(self):
        if self.toughness_kind == "user_defined" and not self.user_defined_toughness_description:
            raise ValueError("user-defined toughness requires a metric description")
        if self.toughness_kind != "user_defined" and self.user_defined_toughness_description is not None:
            raise ValueError("only user-defined toughness may carry a custom metric description")
        flag_ids = [row.flag_id for row in self.caller_validity_flags]
        if len(set(flag_ids)) != len(flag_ids):
            raise ValueError("caller validity flag identities must be unique within a specimen")
        flags_satisfied = all(row.flag_result == "satisfied" for row in self.caller_validity_flags)
        if self.caller_overall_valid != flags_satisfied:
            raise ValueError("caller overall validity must agree with all supplied validity flags")
        if not self.caller_overall_valid and not self.invalid_or_limiting_basis:
            raise ValueError("caller-invalid toughness records require a limiting basis")
        return self


class FractureToughnessCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    metric_id: MetricId
    direction: Literal["minimum", "maximum"]
    accept_limit: Nonnegative
    reject_limit: Nonnegative
    unit_token: str = Field(min_length=1)
    criterion_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_limits(self):
        if self.direction == "minimum" and self.reject_limit > self.accept_limit:
            raise ValueError("minimum toughness criteria require reject <= accept")
        if self.direction == "maximum" and self.reject_limit < self.accept_limit:
            raise ValueError("maximum toughness criteria require accept <= reject")
        return self


class FractureToughnessCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    toughness_kind: ToughnessKind
    test_method_id: str = Field(min_length=1)
    test_method_revision: str = Field(min_length=1)
    toughness_unit_token: str = Field(min_length=1)
    loading_rate_unit_token: str = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_loading_rate: Positive
    maximum_loading_rate: Positive
    criteria: tuple[FractureToughnessCriterion, ...] = Field(min_length=6)
    profile_provider_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_authority: str = Field(min_length=1)
    official_standard_validity_rules_embedded: Literal[False] = False
    toughness_conversion_or_recalculation_claimed: Literal[False] = False
    design_allowable_claimed: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_profile(self):
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("caller temperature support must be ordered")
        if self.maximum_loading_rate < self.minimum_loading_rate:
            raise ValueError("caller loading-rate support must be ordered")
        metric_ids = [row.metric_id for row in self.criteria]
        criterion_ids = [row.criterion_id for row in self.criteria]
        if len(set(metric_ids)) != len(metric_ids) or len(set(criterion_ids)) != len(criterion_ids):
            raise ValueError("toughness profile criterion and metric identities must be unique")
        if set(metric_ids) != {
            "specimen_count",
            "replicate_group_count",
            "independent_source_group_count",
            "caller_valid_fraction",
            "minimum_reported_toughness",
            "maximum_expanded_uncertainty",
        }:
            raise ValueError("toughness caller profile requires the complete metric set")
        return self


class FractureToughnessCampaignAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    records: tuple[FractureToughnessSpecimenRecord, ...] = Field(min_length=1)
    caller_profile: FractureToughnessCallerProfile
    specimen_geometry_orientation_and_extraction_reviewed: bool
    temperature_loading_rate_and_environment_reviewed: bool
    notch_crack_and_fatigue_precrack_reviewed: bool
    method_result_unit_and_uncertainty_reviewed: bool
    caller_validity_flags_and_basis_reviewed: bool
    replicate_source_and_independence_groups_reviewed: bool
    provider_provenance_and_digests_reviewed: bool
    caller_profile_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_campaign_records(self):
        identities = {
            "record": [row.record_id for row in self.records],
            "specimen": [row.physical_specimen_id for row in self.records],
            "validity record": [row.caller_validity_record_id for row in self.records],
            "raw-data digest": [row.raw_data_digest for row in self.records],
            "result digest": [row.result_record_digest for row in self.records],
        }
        for label, values in identities.items():
            if len(set(values)) != len(values):
                raise ValueError(f"fracture-toughness campaign {label} identities must be unique")
        specimen_groups: dict[str, set[str]] = {}
        for row in self.records:
            specimen_groups.setdefault(row.physical_specimen_id, set()).add(row.independence_group_id)
        if any(len(groups) > 1 for groups in specimen_groups.values()):
            raise ValueError("one physical specimen cannot claim multiple independence groups")
        return self


class FractureToughnessCampaignReport(Contract):
    report_schema_version: Literal["matintegrity.fracture_toughness_testing_report.v1"] = (
        "matintegrity.fracture_toughness_testing_report.v1"
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
    official_validity_rules_applied: Literal[False] = False
    toughness_converted_or_recalculated: Literal[False] = False
    design_allowable_produced: Literal[False] = False
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"report_digest"})

    @model_validator(mode="after")
    def digest_is_bound(self, info: ValidationInfo):
        if not (
            isinstance(info.context, dict) and info.context.get("allow_unbound_digest")
        ) and self.report_digest != canonical_digest(self.digest_payload()):
            raise ValueError("fracture-toughness campaign report digest does not match report content")
        return self


def _bound_report(**payload: Any) -> FractureToughnessCampaignReport:
    unsigned = FractureToughnessCampaignReport.model_validate(
        {**payload, "report_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return FractureToughnessCampaignReport.model_validate(
        {**payload, "report_digest": canonical_digest(unsigned.digest_payload())}
    )


def _criterion_outcome(value: float, criterion: FractureToughnessCriterion) -> str:
    if criterion.direction == "minimum":
        return (
            "accept"
            if value >= criterion.accept_limit
            else "reject"
            if value <= criterion.reject_limit
            else "review"
        )
    return (
        "accept"
        if value <= criterion.accept_limit
        else "reject"
        if value >= criterion.reject_limit
        else "review"
    )


def fracture_toughness_testing(x: FractureToughnessCampaignAssessment) -> Calculation:
    review_fields = (
        "specimen_geometry_orientation_and_extraction_reviewed",
        "temperature_loading_rate_and_environment_reviewed",
        "notch_crack_and_fatigue_precrack_reviewed",
        "method_result_unit_and_uncertainty_reviewed",
        "caller_validity_flags_and_basis_reviewed",
        "replicate_source_and_independence_groups_reviewed",
        "provider_provenance_and_digests_reviewed",
        "caller_profile_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    profile = x.caller_profile
    invalid_records = [row.record_id for row in x.records if not row.caller_overall_valid]
    method_mismatch = [
        row.record_id
        for row in x.records
        if (row.toughness_kind, row.test_method_id, row.test_method_revision)
        != (profile.toughness_kind, profile.test_method_id, profile.test_method_revision)
    ]
    unit_mismatch = [
        row.record_id
        for row in x.records
        if row.toughness_unit_token != profile.toughness_unit_token
        or row.loading_rate_unit_token != profile.loading_rate_unit_token
    ]
    out_of_support = [
        row.record_id
        for row in x.records
        if not profile.minimum_temperature_K <= row.test_temperature_K <= profile.maximum_temperature_K
        or not profile.minimum_loading_rate <= row.loading_rate_value <= profile.maximum_loading_rate
    ]
    input_digest = canonical_digest(x.model_dump(mode="json"))
    diagnostics: dict[str, Any] = {
        "missing_reviews": missing_reviews,
        "caller_invalid_record_ids": invalid_records,
        "method_identity_mismatch_record_ids": method_mismatch,
        "unit_mismatch_record_ids": unit_mismatch,
        "outside_caller_support_record_ids": out_of_support,
        "physical_specimen_ids": [row.physical_specimen_id for row in x.records],
        "raw_data_digests": [row.raw_data_digest for row in x.records],
        "result_record_digests": [row.result_record_digest for row in x.records],
    }
    if missing_reviews or invalid_records or method_mismatch or unit_mismatch or out_of_support:
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
            notes=("Reviewed, caller-valid, method-matched records inside caller support are required.",),
        )

    metric_values = {
        "specimen_count": float(len(x.records)),
        "replicate_group_count": float(len({row.replicate_group_id for row in x.records})),
        "independent_source_group_count": float(
            len({(row.source_group_id, row.independence_group_id) for row in x.records})
        ),
        "caller_valid_fraction": sum(row.caller_overall_valid for row in x.records) / len(x.records),
        "minimum_reported_toughness": min(row.reported_toughness for row in x.records),
        "maximum_expanded_uncertainty": max(row.expanded_toughness_uncertainty for row in x.records),
    }
    metric_units = {
        "specimen_count": "count",
        "replicate_group_count": "count",
        "independent_source_group_count": "count",
        "caller_valid_fraction": "1",
        "minimum_reported_toughness": profile.toughness_unit_token,
        "maximum_expanded_uncertainty": profile.toughness_unit_token,
    }
    criteria = {row.metric_id: row for row in profile.criteria}
    criterion_unit_mismatch = [
        row.criterion_id for row in profile.criteria if row.unit_token != metric_units[row.metric_id]
    ]
    if criterion_unit_mismatch:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            campaign_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            metric_values=metric_values,
            criterion_findings=(),
            diagnostics={**diagnostics, "criterion_unit_mismatch_ids": criterion_unit_mismatch},
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Caller criterion units must exactly match reported campaign metrics.",),
        )

    findings = tuple(
        {
            "criterion_id": criteria[metric].criterion_id,
            "metric_id": metric,
            "value": metric_values[metric],
            "unit": metric_units[metric],
            "direction": criteria[metric].direction,
            "accept_limit": criteria[metric].accept_limit,
            "reject_limit": criteria[metric].reject_limit,
            "outcome": _criterion_outcome(metric_values[metric], criteria[metric]),
            "criterion_basis": criteria[metric].criterion_basis,
        }
        for metric in sorted(criteria)
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
            "Accept, review and reject reflect only caller-authored campaign criteria.",
            "Reported toughness and validity are not converted, recalculated, or checked against an embedded standard rule.",
            "The result is not a design allowable, structural acceptance, life, or failure probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("fracture-toughness testing asset and location must match run context")

    return [
        ModelSpec(
            "inspection.fracture_toughness_testing",
            FractureToughnessCampaignAssessment,
            fracture_toughness_testing,
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
                "official_validity_rules_applied": "1",
                "toughness_converted_or_recalculated": "1",
                "design_allowable_produced": "1",
                "report_digest": "1",
            },
            (
                "Specimen, geometry, orientation, precrack, loading, result, uncertainty and provenance remain caller evidence.",
                "Only caller profile limits are applied; no official validity rule, conversion, recalculation or design allowable is embedded.",
            ),
            ("authored_fracture_toughness_testing_campaign_audit",),
            context_validator=same_identity,
        )
    ]

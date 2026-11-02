"""Campaign receipts for caller-qualified external-pressure provider evidence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, canonical_digest
from ..registry import ModelSpec
from .external_pressure_provider import (
    ExternalPressureProviderEvidenceAssessment,
    ResultKind,
    external_pressure_provider_evidence,
)

ReceiptMetric = Literal[
    "supported_receipt_count",
    "out_of_support_receipt_count",
    "maximum_convergence_metric",
    "maximum_holdout_absolute_relative_error",
]


class ExternalPressureConvergenceEvidence(Contract):
    convergence_record_id: str = Field(min_length=1)
    provider_assessment_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    result_kind: ResultKind
    mesh_family_id: str = Field(min_length=1)
    model_family_id: str = Field(min_length=1)
    pressure_basis: str = Field(min_length=1)
    convergence_metric_definition: str = Field(min_length=1)
    convergence_metric_value: Nonnegative
    convergence_metric_unit_token: str = Field(min_length=1)
    comparison_result_ids: tuple[str, ...] = Field(min_length=2)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    comparison_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    comparison_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_record(self):
        if len(set(self.comparison_result_ids)) != len(self.comparison_result_ids):
            raise ValueError("convergence comparison result identities must be unique")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid convergence evidence requires a basis")
        return self


class ExternalPressureReceiptCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    metric_id: ReceiptMetric
    direction: Literal["minimum", "maximum"]
    accept_limit: Nonnegative
    reject_limit: Nonnegative
    unit_token: str = Field(min_length=1)
    criterion_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_limits(self):
        if self.direction == "minimum" and self.reject_limit > self.accept_limit:
            raise ValueError("minimum receipt criteria require reject <= accept")
        if self.direction == "maximum" and self.reject_limit < self.accept_limit:
            raise ValueError("maximum receipt criteria require accept <= reject")
        return self


class ExternalPressureCampaignCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    required_result_kinds: tuple[ResultKind, ...] = Field(min_length=1)
    convergence_metric_definition: str = Field(min_length=1)
    convergence_metric_unit_token: str = Field(min_length=1)
    criteria: tuple[ExternalPressureReceiptCriterion, ...] = Field(min_length=4)
    profile_provider_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_review_authority: str = Field(min_length=1)
    buckling_analysis_executed: Literal[False] = False
    code_curve_or_safety_factor_used: Literal[False] = False
    automatic_acceptance_claimed: Literal[False] = False
    field_qualification_claimed: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_profile(self):
        if len(set(self.required_result_kinds)) != len(self.required_result_kinds):
            raise ValueError("required external-pressure result kinds must be unique")
        metric_ids = [row.metric_id for row in self.criteria]
        criterion_ids = [row.criterion_id for row in self.criteria]
        if len(set(metric_ids)) != len(metric_ids) or len(set(criterion_ids)) != len(criterion_ids):
            raise ValueError("external-pressure receipt criteria and metrics must be unique")
        if set(metric_ids) != {
            "supported_receipt_count",
            "out_of_support_receipt_count",
            "maximum_convergence_metric",
            "maximum_holdout_absolute_relative_error",
        }:
            raise ValueError("external-pressure campaign requires the complete receipt metric set")
        return self


class ExternalPressureCampaignAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    provider_assessments: tuple[ExternalPressureProviderEvidenceAssessment, ...] = Field(min_length=1)
    convergence_evidence: tuple[ExternalPressureConvergenceEvidence, ...] = Field(min_length=1)
    caller_profile: ExternalPressureCampaignCallerProfile
    component_geometry_material_imperfection_identity_reviewed: bool
    boundary_load_pressure_basis_and_support_reviewed: bool
    provider_solver_revision_configuration_and_digests_reviewed: bool
    mesh_and_model_identity_reviewed: bool
    applicability_and_envelope_support_reviewed: bool
    convergence_definition_units_and_records_reviewed: bool
    calibration_holdout_validation_evidence_reviewed: bool
    caller_profile_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        assessment_ids = [row.assessment_id for row in self.provider_assessments]
        result_digests = [row.provider_result.result_digest for row in self.provider_assessments]
        convergence_ids = [row.convergence_record_id for row in self.convergence_evidence]
        for values, label in (
            (assessment_ids, "provider assessment"),
            (result_digests, "provider result digest"),
            (convergence_ids, "convergence record"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"external-pressure campaign {label} identities must be unique")
        if any(
            (row.asset_id, row.location_id, row.component_id)
            != (self.asset_id, self.location_id, self.component_id)
            for row in self.provider_assessments
        ):
            raise ValueError("provider assessments must match campaign asset, location, and component")
        by_id = {row.assessment_id: row for row in self.provider_assessments}
        convergence_assessments = [row.provider_assessment_id for row in self.convergence_evidence]
        if set(convergence_assessments) != set(assessment_ids):
            raise ValueError("each provider assessment requires exactly one convergence record")
        if len(set(convergence_assessments)) != len(convergence_assessments):
            raise ValueError("provider assessments cannot share multiple convergence records")
        for row in self.convergence_evidence:
            assessment = by_id[row.provider_assessment_id]
            result = assessment.provider_result
            if (
                row.analysis_id != result.analysis_id
                or row.result_kind != result.result_kind
                or row.pressure_basis != result.pressure_basis
                or row.provider_id != result.provider_id
                or row.provider_revision != result.provider_revision
                or row.provider_configuration_digest != result.provider_configuration_digest
            ):
                raise ValueError("convergence evidence must preserve provider result identity")
        return self


class ExternalPressureCampaignReport(Contract):
    report_schema_version: Literal["matintegrity.external_pressure_campaign_report.v1"] = (
        "matintegrity.external_pressure_campaign_report.v1"
    )
    assessment_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    evidence_outcome: Literal["supported", "review", "not_supported", "insufficient_evidence"]
    caller_profile_id: str = Field(min_length=1)
    metric_values: dict[str, float]
    criterion_findings: tuple[dict[str, Any], ...]
    receipt_summaries: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_profile_only: Literal[True] = True
    buckling_analysis_executed: Literal[False] = False
    allowable_pressure_or_safety_factor_produced: Literal[False] = False
    automatic_acceptance_or_field_qualification: Literal[False] = False
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"report_digest"})

    @model_validator(mode="after")
    def digest_is_bound(self, info: ValidationInfo):
        if not (
            isinstance(info.context, dict) and info.context.get("allow_unbound_digest")
        ) and self.report_digest != canonical_digest(self.digest_payload()):
            raise ValueError("external-pressure campaign report digest does not match content")
        return self


def _bound_report(**payload: Any) -> ExternalPressureCampaignReport:
    unsigned = ExternalPressureCampaignReport.model_validate(
        {**payload, "report_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return ExternalPressureCampaignReport.model_validate(
        {**payload, "report_digest": canonical_digest(unsigned.digest_payload())}
    )


def _criterion_outcome(value: float, row: ExternalPressureReceiptCriterion) -> str:
    if row.direction == "minimum":
        return (
            "supported"
            if value >= row.accept_limit
            else "not_supported"
            if value <= row.reject_limit
            else "review"
        )
    return (
        "supported"
        if value <= row.accept_limit
        else "not_supported"
        if value >= row.reject_limit
        else "review"
    )


def external_pressure_campaign(x: ExternalPressureCampaignAssessment) -> Calculation:
    review_fields = (
        "component_geometry_material_imperfection_identity_reviewed",
        "boundary_load_pressure_basis_and_support_reviewed",
        "provider_solver_revision_configuration_and_digests_reviewed",
        "mesh_and_model_identity_reviewed",
        "applicability_and_envelope_support_reviewed",
        "convergence_definition_units_and_records_reviewed",
        "calibration_holdout_validation_evidence_reviewed",
        "caller_profile_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    profile = x.caller_profile
    invalid_convergence_ids = [
        row.convergence_record_id for row in x.convergence_evidence if not row.record_valid
    ]
    convergence_identity_conflicts = [
        row.convergence_record_id
        for row in x.convergence_evidence
        if row.convergence_metric_definition != profile.convergence_metric_definition
        or row.convergence_metric_unit_token != profile.convergence_metric_unit_token
    ]
    lower_results = [external_pressure_provider_evidence(row) for row in x.provider_assessments]
    incomplete_receipt_ids = [
        assessment.assessment_id
        for assessment, result in zip(x.provider_assessments, lower_results, strict=True)
        if result.status == "needs_data"
    ]
    represented_result_kinds = {row.provider_result.result_kind for row in x.provider_assessments}
    missing_result_kinds = sorted(set(profile.required_result_kinds) - represented_result_kinds)
    input_digest = canonical_digest(x.model_dump(mode="json"))
    receipt_summaries = tuple(
        {
            "provider_assessment_id": assessment.assessment_id,
            "provider_result_record_id": assessment.provider_result.result_record_id,
            "result_kind": assessment.provider_result.result_kind,
            "pressure_basis": assessment.provider_result.pressure_basis,
            "mesh_id": assessment.provider_result.mesh_id,
            "result_digest": assessment.provider_result.result_digest,
            "receipt_status": result.status,
            "outside_support_reasons": result.values.get("outside_support_reasons", []),
            "qualification_envelope_id": result.values.get("qualification_envelope_id"),
        }
        for assessment, result in zip(x.provider_assessments, lower_results, strict=True)
    )
    diagnostics: dict[str, Any] = {
        "missing_reviews": missing_reviews,
        "invalid_convergence_record_ids": invalid_convergence_ids,
        "convergence_identity_conflict_ids": convergence_identity_conflicts,
        "incomplete_provider_receipt_ids": incomplete_receipt_ids,
        "missing_required_result_kinds": missing_result_kinds,
    }
    if (
        missing_reviews
        or invalid_convergence_ids
        or convergence_identity_conflicts
        or incomplete_receipt_ids
        or missing_result_kinds
    ):
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            evidence_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            metric_values={},
            criterion_findings=(),
            receipt_summaries=receipt_summaries,
            diagnostics=diagnostics,
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=(
                "Complete reviewed provider receipts, convergence records, and validation evidence are required.",
            ),
        )

    supported_count = sum(result.status == "computed" for result in lower_results)
    outside_count = sum(result.status == "out_of_scope" for result in lower_results)
    holdout_errors = []
    for assessment, lower in zip(x.provider_assessments, lower_results, strict=True):
        envelope_id = lower.values.get("qualification_envelope_id")
        if envelope_id is None:
            matching = [
                row
                for row in assessment.candidate_envelopes
                if (
                    row.shell_type_id,
                    row.material_condition_id,
                    row.boundary_support_id,
                    row.load_case_id,
                    row.pressure_basis,
                )
                == (
                    assessment.shell_type_id,
                    assessment.material_condition_id,
                    assessment.boundary_support_id,
                    assessment.load_case_id,
                    assessment.pressure_basis,
                )
            ]
            if not matching:
                continue
            envelope = matching[0]
        else:
            envelope = next(row for row in assessment.candidate_envelopes if row.envelope_id == envelope_id)
        holdout_errors.extend(
            abs(row.predicted_value - row.observed_value) / row.observed_value
            for row in envelope.qualification_evidence
            if row.partition == "holdout"
        )
    if not holdout_errors:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            evidence_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            metric_values={},
            criterion_findings=(),
            receipt_summaries=receipt_summaries,
            diagnostics={**diagnostics, "missing_holdout_validation_metric": True},
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("At least one caller-qualified holdout comparison is required.",),
        )

    metric_values = {
        "supported_receipt_count": float(supported_count),
        "out_of_support_receipt_count": float(outside_count),
        "maximum_convergence_metric": max(row.convergence_metric_value for row in x.convergence_evidence),
        "maximum_holdout_absolute_relative_error": max(holdout_errors),
    }
    metric_units = {
        "supported_receipt_count": "count",
        "out_of_support_receipt_count": "count",
        "maximum_convergence_metric": profile.convergence_metric_unit_token,
        "maximum_holdout_absolute_relative_error": "1",
    }
    criteria = {row.metric_id: row for row in profile.criteria}
    unit_conflicts = [
        row.criterion_id for row in profile.criteria if row.unit_token != metric_units[row.metric_id]
    ]
    if unit_conflicts:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            evidence_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            metric_values=metric_values,
            criterion_findings=(),
            receipt_summaries=receipt_summaries,
            diagnostics={**diagnostics, "criterion_unit_conflict_ids": unit_conflicts},
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Caller receipt criterion units must match evidence metrics exactly.",),
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
    evidence_outcome = (
        "not_supported" if "not_supported" in outcomes else "review" if "review" in outcomes else "supported"
    )
    report = _bound_report(
        assessment_id=x.assessment_id,
        campaign_id=x.campaign_id,
        evidence_outcome=evidence_outcome,
        caller_profile_id=profile.profile_id,
        metric_values=metric_values,
        criterion_findings=findings,
        receipt_summaries=receipt_summaries,
        diagnostics=diagnostics,
        input_digest=input_digest,
    )
    return Calculation(
        status="computed",
        values=report.model_dump(),
        notes=(
            "Supported, review, and not-supported are caller evidence-receipt outcomes, not component acceptance.",
            "Provider result values are not converted into allowable pressure, safety factor, or collapse probability.",
            "No buckling solve, code curve, automatic acceptance, field qualification, or remaining life is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("external-pressure campaign asset and location must match run context")

    return [
        ModelSpec(
            "structural.external_pressure",
            ExternalPressureCampaignAssessment,
            external_pressure_campaign,
            {
                "report_schema_version": "1",
                "assessment_id": "1",
                "campaign_id": "1",
                "evidence_outcome": "1",
                "caller_profile_id": "1",
                "metric_values": "mixed",
                "criterion_findings": "mixed",
                "receipt_summaries": "mixed",
                "diagnostics": "mixed",
                "input_digest": "1",
                "caller_profile_only": "1",
                "buckling_analysis_executed": "1",
                "allowable_pressure_or_safety_factor_produced": "1",
                "automatic_acceptance_or_field_qualification": "1",
                "report_digest": "1",
            },
            (
                "Existing provider assessments retain exact geometry, material, imperfection, boundary, load, mesh, model, pressure and digest identities.",
                "Campaign metrics audit applicability, convergence and holdout evidence without executing buckling analysis or component acceptance.",
            ),
            ("authored_external_pressure_provider_receipt_campaign_audit",),
            context_validator=same_identity,
        )
    ]

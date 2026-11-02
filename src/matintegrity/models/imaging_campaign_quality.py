"""Campaign quality audit for radiography and encoded phased-array evidence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

ImagingFamily = Literal["radiography", "phased_array"]
QualityOutcome = Literal["pass", "review", "fail", "insufficient_evidence"]
MetricId = Literal[
    "acquisition_count",
    "coverage_fraction",
    "reference_feature_check_coverage_fraction",
    "required_stage_coverage_fraction",
    "response_present_fraction",
    "minimum_sensitivity_metric",
    "maximum_resolution_metric",
]


class ImagingReferenceFeature(Contract):
    feature_id: str = Field(min_length=1)
    feature_type_descriptor: str = Field(min_length=1)
    physical_location_definition: str = Field(min_length=1)
    nominal_dimension: Positive
    dimension_unit_token: str = Field(min_length=1)
    expanded_dimension_uncertainty: Nonnegative
    physical_feature_identity_reviewed: bool
    feature_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class ImagingReferenceStandard(Contract):
    reference_standard_id: str = Field(min_length=1)
    material_and_product_form_id: str = Field(min_length=1)
    standard_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    features: tuple[ImagingReferenceFeature, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_features(self):
        identifiers = [row.feature_id for row in self.features]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("imaging reference feature identifiers must be unique")
        return self


class ImagingReferenceVerification(Contract):
    verification_id: str = Field(min_length=1)
    reference_feature_id: str = Field(min_length=1)
    check_stage: str = Field(min_length=1)
    reported_response_present: bool
    sensitivity_metric: float
    sensitivity_unit_token: str = Field(min_length=1)
    expanded_sensitivity_uncertainty: Nonnegative
    resolution_metric: Nonnegative
    resolution_unit_token: str = Field(min_length=1)
    expanded_resolution_uncertainty: Nonnegative
    verification_method_definition: str = Field(min_length=1)
    verification_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_record_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid imaging reference verifications require a basis")
        return self


class ImagingAcquisitionEvidence(Contract):
    acquisition_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    acquisition_configuration_id: str = Field(min_length=1)
    acquisition_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    acquisition_device_id: str = Field(min_length=1)
    reference_standard_id: str = Field(min_length=1)
    target_extent: Positive
    examined_extent: Nonnegative
    extent_unit_token: str = Field(min_length=1)
    encoded_data_id: str = Field(min_length=1)
    encoded_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    encoded_data_format: str = Field(min_length=1)
    verifications: tuple[ImagingReferenceVerification, ...] = Field(min_length=1)
    acquisition_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def extent_and_verifications(self):
        if self.examined_extent > self.target_extent:
            raise ValueError("imaging examined extent cannot exceed target extent")
        identifiers = [row.verification_id for row in self.verifications]
        keys = [(row.reference_feature_id, row.check_stage) for row in self.verifications]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("imaging verification identifiers must be unique within an acquisition")
        if len(set(keys)) != len(keys):
            raise ValueError("reference feature and stage checks must be unique within an acquisition")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid imaging acquisitions require a basis")
        return self


class ImagingQualityCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    metric_id: MetricId
    direction: Literal["minimum", "maximum"]
    pass_limit: Nonnegative
    fail_limit: Nonnegative
    unit_token: str = Field(min_length=1)
    criterion_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_limits(self):
        if self.direction == "maximum" and self.fail_limit < self.pass_limit:
            raise ValueError("maximum imaging criteria require fail limit at or above pass limit")
        if self.direction == "minimum" and self.fail_limit > self.pass_limit:
            raise ValueError("minimum imaging criteria require fail limit at or below pass limit")
        return self


class ImagingCampaignAcceptanceProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    imaging_family: ImagingFamily
    required_check_stages: tuple[str, ...] = Field(min_length=1)
    sensitivity_metric_definition: str = Field(min_length=1)
    sensitivity_unit_token: str = Field(min_length=1)
    resolution_metric_definition: str = Field(min_length=1)
    resolution_unit_token: str = Field(min_length=1)
    criteria: tuple[ImagingQualityCriterion, ...] = Field(min_length=7)
    profile_provider_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_authority: str = Field(min_length=1)
    built_in_code_or_standard_limits_used: Literal[False] = False
    flaw_acceptance_claimed: Literal[False] = False
    pod_claimed: Literal[False] = False
    physical_qualification_claimed: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_profile(self):
        if len(set(self.required_check_stages)) != len(self.required_check_stages):
            raise ValueError("required imaging check stages must be unique")
        criterion_ids = [row.criterion_id for row in self.criteria]
        metric_ids = [row.metric_id for row in self.criteria]
        if len(set(criterion_ids)) != len(criterion_ids):
            raise ValueError("imaging quality criterion identifiers must be unique")
        if len(set(metric_ids)) != len(metric_ids):
            raise ValueError("imaging quality metrics must have exactly one criterion")
        required = {
            "acquisition_count",
            "coverage_fraction",
            "reference_feature_check_coverage_fraction",
            "required_stage_coverage_fraction",
            "response_present_fraction",
            "minimum_sensitivity_metric",
            "maximum_resolution_metric",
        }
        if set(metric_ids) != required:
            raise ValueError("imaging acceptance profile requires the complete quality metric set")
        return self


class ImagingCampaignQualityAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    imaging_family: ImagingFamily
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    extent_unit_token: str = Field(min_length=1)
    reference_standard: ImagingReferenceStandard
    acquisitions: tuple[ImagingAcquisitionEvidence, ...] = Field(min_length=1)
    acceptance_profile: ImagingCampaignAcceptanceProfile
    procedure_and_acquisition_identities_reviewed: bool
    reference_standard_features_and_uncertainty_reviewed: bool
    calibration_and_verification_checks_reviewed: bool
    coverage_and_extent_units_reviewed: bool
    encoded_data_identity_and_digests_reviewed: bool
    sensitivity_resolution_metrics_units_and_uncertainty_reviewed: bool
    caller_acceptance_profile_reviewed: bool
    record_validity_and_missingness_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        if self.acceptance_profile.imaging_family != self.imaging_family:
            raise ValueError("imaging campaign and acceptance profile families must match")
        acquisition_ids = [row.acquisition_id for row in self.acquisitions]
        encoded_ids = [row.encoded_data_id for row in self.acquisitions]
        encoded_digests = [row.encoded_data_digest for row in self.acquisitions]
        for values, label in (
            (acquisition_ids, "acquisition"),
            (encoded_ids, "encoded data"),
            (encoded_digests, "encoded data digest"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"imaging campaign {label} identities must be unique")
        feature_ids = {row.feature_id for row in self.reference_standard.features}
        for acquisition in self.acquisitions:
            if (acquisition.procedure_id, acquisition.procedure_revision) != (
                self.procedure_id,
                self.procedure_revision,
            ):
                raise ValueError("all acquisitions must match campaign procedure identity and revision")
            if acquisition.reference_standard_id != self.reference_standard.reference_standard_id:
                raise ValueError("all acquisitions must reference the campaign reference standard")
            if acquisition.extent_unit_token != self.extent_unit_token:
                raise ValueError("all acquisition coverage extents must use the campaign unit")
            if {row.reference_feature_id for row in acquisition.verifications} - feature_ids:
                raise ValueError("verification checks must reference declared standard features")
        return self


class ImagingCampaignQualityReport(Contract):
    report_schema_version: Literal["matintegrity.imaging_campaign_quality_report.v1"] = (
        "matintegrity.imaging_campaign_quality_report.v1"
    )
    assessment_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    imaging_family: ImagingFamily
    quality_outcome: QualityOutcome
    acceptance_profile_id: str = Field(min_length=1)
    metric_values: dict[str, float]
    criterion_findings: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_profile_only: Literal[True] = True
    automatic_flaw_acceptance: Literal[False] = False
    pod_claimed: Literal[False] = False
    physical_qualification: Literal[False] = False
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"report_digest"})

    @model_validator(mode="after")
    def digest_is_bound(self, info: ValidationInfo):
        if not (
            isinstance(info.context, dict) and info.context.get("allow_unbound_digest")
        ) and self.report_digest != canonical_digest(self.digest_payload()):
            raise ValueError("imaging campaign report digest does not match report content")
        return self


def _bound_report(**payload: Any) -> ImagingCampaignQualityReport:
    unsigned = ImagingCampaignQualityReport.model_validate(
        {**payload, "report_digest": "0" * 64},
        context={"allow_unbound_digest": True},
    )
    return ImagingCampaignQualityReport.model_validate(
        {**payload, "report_digest": canonical_digest(unsigned.digest_payload())}
    )


def _criterion_outcome(value: float, criterion: ImagingQualityCriterion) -> str:
    if criterion.direction == "maximum":
        if value <= criterion.pass_limit:
            return "pass"
        if value >= criterion.fail_limit:
            return "fail"
        return "review"
    if value >= criterion.pass_limit:
        return "pass"
    if value <= criterion.fail_limit:
        return "fail"
    return "review"


def imaging_campaign_quality(x: ImagingCampaignQualityAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "procedure_and_acquisition_identities_reviewed",
            "reference_standard_features_and_uncertainty_reviewed",
            "calibration_and_verification_checks_reviewed",
            "coverage_and_extent_units_reviewed",
            "encoded_data_identity_and_digests_reviewed",
            "sensitivity_resolution_metrics_units_and_uncertainty_reviewed",
            "caller_acceptance_profile_reviewed",
            "record_validity_and_missingness_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_feature_ids = [
        row.feature_id for row in x.reference_standard.features if not row.physical_feature_identity_reviewed
    ]
    invalid_acquisition_ids = [row.acquisition_id for row in x.acquisitions if not row.record_valid]
    invalid_verification_ids = [
        row.verification_id
        for acquisition in x.acquisitions
        for row in acquisition.verifications
        if not row.record_valid
    ]
    input_digest = canonical_digest(x.model_dump(mode="json"))
    base_diagnostics = {
        "missing_reviews": missing_reviews,
        "invalid_reference_feature_ids": invalid_feature_ids,
        "invalid_acquisition_ids": invalid_acquisition_ids,
        "invalid_verification_ids": invalid_verification_ids,
        "encoded_data_ids": [row.encoded_data_id for row in x.acquisitions],
        "encoded_data_digests": [row.encoded_data_digest for row in x.acquisitions],
    }
    if missing_reviews or invalid_feature_ids or invalid_acquisition_ids or invalid_verification_ids:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            imaging_family=x.imaging_family,
            quality_outcome="insufficient_evidence",
            acceptance_profile_id=x.acceptance_profile.profile_id,
            metric_values={},
            criterion_findings=(),
            diagnostics=base_diagnostics,
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=(
                "Campaign quality requires reviewed, valid reference, acquisition and verification evidence.",
            ),
        )

    profile = x.acceptance_profile
    verifications = [row for acquisition in x.acquisitions for row in acquisition.verifications]
    sensitivity_unit_mismatch_ids = [
        row.verification_id
        for row in verifications
        if row.sensitivity_unit_token != profile.sensitivity_unit_token
    ]
    resolution_unit_mismatch_ids = [
        row.verification_id
        for row in verifications
        if row.resolution_unit_token != profile.resolution_unit_token
    ]
    if sensitivity_unit_mismatch_ids or resolution_unit_mismatch_ids:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            imaging_family=x.imaging_family,
            quality_outcome="insufficient_evidence",
            acceptance_profile_id=profile.profile_id,
            metric_values={},
            criterion_findings=(),
            diagnostics={
                **base_diagnostics,
                "sensitivity_unit_mismatch_verification_ids": sensitivity_unit_mismatch_ids,
                "resolution_unit_mismatch_verification_ids": resolution_unit_mismatch_ids,
            },
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Sensitivity and resolution units are exact; no hidden conversion is performed.",),
        )

    feature_ids = {row.feature_id for row in x.reference_standard.features}
    required_stages = set(profile.required_check_stages)
    expected_feature_stage_checks = len(x.acquisitions) * len(feature_ids) * len(required_stages)
    present_feature_stage_checks = sum(
        row.reference_feature_id in feature_ids and row.check_stage in required_stages
        for row in verifications
    )
    expected_acquisition_stages = len(x.acquisitions) * len(required_stages)
    present_acquisition_stages = sum(
        stage in {row.check_stage for row in acquisition.verifications}
        for acquisition in x.acquisitions
        for stage in required_stages
    )
    total_target = sum(row.target_extent for row in x.acquisitions)
    total_examined = sum(row.examined_extent for row in x.acquisitions)
    metric_values = {
        "acquisition_count": float(len(x.acquisitions)),
        "coverage_fraction": total_examined / total_target,
        "reference_feature_check_coverage_fraction": (
            present_feature_stage_checks / expected_feature_stage_checks
        ),
        "required_stage_coverage_fraction": present_acquisition_stages / expected_acquisition_stages,
        "response_present_fraction": sum(row.reported_response_present for row in verifications)
        / len(verifications),
        "minimum_sensitivity_metric": min(row.sensitivity_metric for row in verifications),
        "maximum_resolution_metric": max(row.resolution_metric for row in verifications),
    }
    metric_units = {
        "acquisition_count": "count",
        "coverage_fraction": "1",
        "reference_feature_check_coverage_fraction": "1",
        "required_stage_coverage_fraction": "1",
        "response_present_fraction": "1",
        "minimum_sensitivity_metric": profile.sensitivity_unit_token,
        "maximum_resolution_metric": profile.resolution_unit_token,
    }
    criteria = {row.metric_id: row for row in profile.criteria}
    criterion_unit_mismatch_ids = [
        row.criterion_id for row in profile.criteria if row.unit_token != metric_units[row.metric_id]
    ]
    if criterion_unit_mismatch_ids:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            imaging_family=x.imaging_family,
            quality_outcome="insufficient_evidence",
            acceptance_profile_id=profile.profile_id,
            metric_values=metric_values,
            criterion_findings=(),
            diagnostics={
                **base_diagnostics,
                "criterion_unit_mismatch_ids": criterion_unit_mismatch_ids,
            },
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Caller criteria and calculated quality metrics require exact unit identity.",),
        )

    findings = tuple(
        {
            "criterion_id": criteria[metric_id].criterion_id,
            "metric_id": metric_id,
            "value": metric_values[metric_id],
            "unit": metric_units[metric_id],
            "direction": criteria[metric_id].direction,
            "pass_limit": criteria[metric_id].pass_limit,
            "fail_limit": criteria[metric_id].fail_limit,
            "outcome": _criterion_outcome(metric_values[metric_id], criteria[metric_id]),
            "criterion_basis": criteria[metric_id].criterion_basis,
        }
        for metric_id in sorted(criteria)
    )
    outcomes = {row["outcome"] for row in findings}
    quality_outcome = "fail" if "fail" in outcomes else "review" if "review" in outcomes else "pass"
    report = _bound_report(
        assessment_id=x.assessment_id,
        campaign_id=x.campaign_id,
        imaging_family=x.imaging_family,
        quality_outcome=quality_outcome,
        acceptance_profile_id=profile.profile_id,
        metric_values=metric_values,
        criterion_findings=findings,
        diagnostics={
            **base_diagnostics,
            "procedure_id": x.procedure_id,
            "procedure_revision": x.procedure_revision,
            "reference_standard_id": x.reference_standard.reference_standard_id,
            "reference_feature_ids": sorted(feature_ids),
            "required_check_stages": list(profile.required_check_stages),
            "acquisition_configuration_digests": [
                row.acquisition_configuration_digest for row in x.acquisitions
            ],
        },
        input_digest=input_digest,
    )
    return Calculation(
        status="computed",
        values=report.model_dump(),
        notes=(
            "Pass, review and fail use only caller profile limits; no code or standard acceptance value is bundled.",
            "Reference-feature response is campaign quality evidence, not automatic flaw acceptance, POD or physical qualification.",
            "No flaw classification, sizing acceptance, remaining life or failure probability is inferred.",
        ),
    )


def specifications():
    output_units = {
        "report_schema_version": "1",
        "assessment_id": "1",
        "campaign_id": "1",
        "imaging_family": "1",
        "quality_outcome": "1",
        "acceptance_profile_id": "1",
        "metric_values": "mixed",
        "criterion_findings": "mixed",
        "diagnostics": "mixed",
        "input_digest": "1",
        "caller_acceptance_profile_only": "1",
        "automatic_flaw_acceptance": "1",
        "pod_claimed": "1",
        "physical_qualification": "1",
        "report_digest": "1",
    }

    def spec(family: ImagingFamily):
        def same_identity(x, context):
            if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
                raise ValueError("imaging campaign asset and location must match run context")
            if x.imaging_family != family:
                raise ValueError(f"{family} model requires its matching imaging family")

        model_id = (
            "inspection.radiography_campaign_quality"
            if family == "radiography"
            else "inspection.phased_array_campaign_quality"
        )
        return ModelSpec(
            model_id,
            ImagingCampaignQualityAssessment,
            imaging_campaign_quality,
            output_units,
            (
                "Procedure, acquisition, reference standard, coverage and encoded-data identities are caller supplied.",
                "Sensitivity, resolution and reference response are quality metrics under caller limits only.",
                "Campaign audit does not establish flaw acceptance, POD or physical qualification.",
            ),
            ("authored_imaging_reference_campaign_quality_audit",),
            context_validator=same_identity,
        )

    return [spec("radiography"), spec("phased_array")]

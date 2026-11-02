"""Caller-profile campaign audits for acoustic-emission and guided-wave evidence.

This module audits acquisition provenance and reference/baseline consistency.  It
does not interpret signals as damage, size indications, estimate POD, or qualify
an inspection method.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

WaveFamily = Literal["acoustic_emission", "guided_waves"]
MetricId = Literal[
    "record_count",
    "baseline_count",
    "observation_count",
    "coverage_fraction",
    "channel_coverage_fraction",
    "reference_stage_coverage_fraction",
    "maximum_absolute_timing_error_s",
    "minimum_amplitude_metric",
    "maximum_noise_metric",
    "maximum_localization_error_m",
    "maximum_reference_consistency_error",
]


class WaveArrayElement(Contract):
    element_id: str = Field(min_length=1)
    channel_id: str = Field(min_length=1)
    element_kind: Literal["sensor", "transducer"]
    physical_position_definition: str = Field(min_length=1)
    calibration_id: str = Field(min_length=1)
    calibration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class WaveAcquisitionConfiguration(Contract):
    configuration_id: str = Field(min_length=1)
    family: WaveFamily
    array_id: str = Field(min_length=1)
    elements: tuple[WaveArrayElement, ...] = Field(min_length=1)
    coupling_method: str = Field(min_length=1)
    coupling_state_id: str = Field(min_length=1)
    coupling_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    clock_id: str = Field(min_length=1)
    sampling_rate_hz: Positive
    acquisition_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_array_members(self):
        element_ids = [row.element_id for row in self.elements]
        channel_ids = [row.channel_id for row in self.elements]
        if len(set(element_ids)) != len(element_ids) or len(set(channel_ids)) != len(channel_ids):
            raise ValueError("wave array element and channel identities must be unique")
        expected_kind = "sensor" if self.family == "acoustic_emission" else "transducer"
        if any(row.element_kind != expected_kind for row in self.elements):
            raise ValueError(f"{self.family} array elements must use {expected_kind} identity")
        return self


class WaveReferenceSourceCheck(Contract):
    check_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    elapsed_time_s: Nonnegative
    check_stage: str = Field(min_length=1)
    reference_source_id: str = Field(min_length=1)
    reference_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    channel_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    timing_error_s: float
    expanded_timing_uncertainty_s: Nonnegative
    amplitude_metric: Nonnegative
    amplitude_unit_token: str = Field(min_length=1)
    expanded_amplitude_uncertainty: Nonnegative
    noise_metric: Nonnegative
    noise_unit_token: str = Field(min_length=1)
    expanded_noise_uncertainty: Nonnegative
    localization_error_m: Nonnegative
    expanded_localization_uncertainty_m: Nonnegative
    reference_consistency_error: Nonnegative
    expanded_consistency_uncertainty: Nonnegative
    check_method_definition: str = Field(min_length=1)
    check_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid wave reference checks require a basis")
        return self


class WaveAcquisitionRecord(Contract):
    record_id: str = Field(min_length=1)
    record_role: Literal["baseline", "observation"]
    configuration_id: str = Field(min_length=1)
    coupling_state_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    active_channel_ids: tuple[str, ...] = Field(min_length=1)
    target_extent: Positive
    examined_extent: Nonnegative
    extent_unit_token: str = Field(min_length=1)
    encoded_data_id: str = Field(min_length=1)
    encoded_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    encoded_data_format: str = Field(min_length=1)
    reference_checks: tuple[WaveReferenceSourceCheck, ...] = Field(min_length=1)
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_record(self):
        if self.examined_extent > self.target_extent:
            raise ValueError("wave examined extent cannot exceed target extent")
        if len(set(self.active_channel_ids)) != len(self.active_channel_ids):
            raise ValueError("active wave channel identities must be unique")
        check_ids = [row.check_id for row in self.reference_checks]
        if len(set(check_ids)) != len(check_ids):
            raise ValueError("wave reference check identities must be unique within a record")
        if {row.channel_id for row in self.reference_checks} - set(self.active_channel_ids):
            raise ValueError("wave reference checks must use active record channels")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid wave acquisition records require a basis")
        return self


class WaveQualityCriterion(Contract):
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
            raise ValueError("maximum wave criteria require ordered pass and fail limits")
        if self.direction == "minimum" and self.fail_limit > self.pass_limit:
            raise ValueError("minimum wave criteria require ordered pass and fail limits")
        return self


class WaveCampaignAcceptanceProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    family: WaveFamily
    required_check_stages: tuple[str, ...] = Field(min_length=1)
    amplitude_metric_definition: str = Field(min_length=1)
    amplitude_unit_token: str = Field(min_length=1)
    noise_metric_definition: str = Field(min_length=1)
    noise_unit_token: str = Field(min_length=1)
    reference_consistency_metric_definition: str = Field(min_length=1)
    criteria: tuple[WaveQualityCriterion, ...] = Field(min_length=11)
    profile_provider_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_authority: str = Field(min_length=1)
    built_in_code_or_standard_limits_used: Literal[False] = False
    automatic_damage_detection_or_sizing_claimed: Literal[False] = False
    pod_claimed: Literal[False] = False
    physical_qualification_claimed: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_profile(self):
        if len(set(self.required_check_stages)) != len(self.required_check_stages):
            raise ValueError("required wave check stages must be unique")
        metric_ids = [row.metric_id for row in self.criteria]
        criterion_ids = [row.criterion_id for row in self.criteria]
        if len(set(metric_ids)) != len(metric_ids) or len(set(criterion_ids)) != len(criterion_ids):
            raise ValueError("wave profile criteria and metrics must be unique")
        if set(metric_ids) != {
            "record_count",
            "baseline_count",
            "observation_count",
            "coverage_fraction",
            "channel_coverage_fraction",
            "reference_stage_coverage_fraction",
            "maximum_absolute_timing_error_s",
            "minimum_amplitude_metric",
            "maximum_noise_metric",
            "maximum_localization_error_m",
            "maximum_reference_consistency_error",
        }:
            raise ValueError("wave profile requires the complete campaign metric set")
        return self


class WaveCampaignQualityAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    family: WaveFamily
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    extent_unit_token: str = Field(min_length=1)
    acquisition_configuration: WaveAcquisitionConfiguration
    records: tuple[WaveAcquisitionRecord, ...] = Field(min_length=1)
    acceptance_profile: WaveCampaignAcceptanceProfile
    procedure_array_and_acquisition_identity_reviewed: bool
    coupling_and_clock_identity_reviewed: bool
    calibration_and_reference_source_checks_reviewed: bool
    baseline_observation_identity_and_digests_reviewed: bool
    channel_mapping_and_coverage_reviewed: bool
    timing_amplitude_noise_localization_units_and_uncertainty_reviewed: bool
    source_and_independence_groups_reviewed: bool
    caller_acceptance_profile_reviewed: bool
    record_validity_and_missingness_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        if (
            self.acquisition_configuration.family != self.family
            or self.acceptance_profile.family != self.family
        ):
            raise ValueError("wave campaign, configuration and profile families must match")
        record_ids = [row.record_id for row in self.records]
        data_ids = [row.encoded_data_id for row in self.records]
        data_digests = [row.encoded_data_digest for row in self.records]
        for values, label in (
            (record_ids, "record"),
            (data_ids, "encoded data"),
            (data_digests, "encoded digest"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"wave campaign {label} identities must be unique")
        declared_channels = {row.channel_id for row in self.acquisition_configuration.elements}
        sequence_indices: list[int] = []
        for row in self.records:
            if row.configuration_id != self.acquisition_configuration.configuration_id:
                raise ValueError("wave records must reference the campaign configuration")
            if row.coupling_state_id != self.acquisition_configuration.coupling_state_id:
                raise ValueError("wave records must preserve the reviewed coupling state identity")
            if row.clock_id != self.acquisition_configuration.clock_id:
                raise ValueError("wave records must preserve the reviewed clock identity")
            if row.extent_unit_token != self.extent_unit_token:
                raise ValueError("wave record extents must use the campaign unit")
            if set(row.active_channel_ids) - declared_channels:
                raise ValueError("wave record channels must belong to the declared array")
            sequence_indices.extend(check.sequence_index for check in row.reference_checks)
        if len(set(sequence_indices)) != len(sequence_indices):
            raise ValueError("wave reference check sequence indices must be unique across the campaign")
        return self


class WaveCampaignQualityReport(Contract):
    report_schema_version: Literal["matintegrity.wave_campaign_quality_report.v1"] = (
        "matintegrity.wave_campaign_quality_report.v1"
    )
    assessment_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    family: WaveFamily
    quality_outcome: Literal["pass", "review", "fail", "insufficient_evidence"]
    acceptance_profile_id: str = Field(min_length=1)
    metric_values: dict[str, float]
    criterion_findings: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_profile_only: Literal[True] = True
    automatic_damage_detection_or_sizing: Literal[False] = False
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
            raise ValueError("wave campaign report digest does not match report content")
        return self


def _bound_report(**payload: Any) -> WaveCampaignQualityReport:
    unsigned = WaveCampaignQualityReport.model_validate(
        {**payload, "report_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return WaveCampaignQualityReport.model_validate(
        {**payload, "report_digest": canonical_digest(unsigned.digest_payload())}
    )


def _criterion_outcome(value: float, criterion: WaveQualityCriterion) -> str:
    if criterion.direction == "maximum":
        return (
            "pass" if value <= criterion.pass_limit else "fail" if value >= criterion.fail_limit else "review"
        )
    return "pass" if value >= criterion.pass_limit else "fail" if value <= criterion.fail_limit else "review"


def wave_campaign_quality(x: WaveCampaignQualityAssessment) -> Calculation:
    review_fields = (
        "procedure_array_and_acquisition_identity_reviewed",
        "coupling_and_clock_identity_reviewed",
        "calibration_and_reference_source_checks_reviewed",
        "baseline_observation_identity_and_digests_reviewed",
        "channel_mapping_and_coverage_reviewed",
        "timing_amplitude_noise_localization_units_and_uncertainty_reviewed",
        "source_and_independence_groups_reviewed",
        "caller_acceptance_profile_reviewed",
        "record_validity_and_missingness_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    invalid_records = [row.record_id for row in x.records if not row.record_valid]
    checks = [check for row in x.records for check in row.reference_checks]
    invalid_checks = [row.check_id for row in checks if not row.record_valid]
    baseline_ids = [row.record_id for row in x.records if row.record_role == "baseline"]
    observation_ids = [row.record_id for row in x.records if row.record_role == "observation"]
    input_digest = canonical_digest(x.model_dump(mode="json"))
    diagnostics: dict[str, Any] = {
        "missing_reviews": missing_reviews,
        "invalid_record_ids": invalid_records,
        "invalid_check_ids": invalid_checks,
        "baseline_record_ids": baseline_ids,
        "observation_record_ids": observation_ids,
        "encoded_data_ids": [row.encoded_data_id for row in x.records],
        "encoded_data_digests": [row.encoded_data_digest for row in x.records],
    }
    unavailable = []
    if not baseline_ids:
        unavailable.append("baseline_record_required")
    if not observation_ids:
        unavailable.append("observation_record_required")
    if missing_reviews or invalid_records or invalid_checks or unavailable:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            family=x.family,
            quality_outcome="insufficient_evidence",
            acceptance_profile_id=x.acceptance_profile.profile_id,
            metric_values={},
            criterion_findings=(),
            diagnostics={**diagnostics, "unavailable_evidence": unavailable},
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Reviewed valid baseline, observation and reference evidence is required.",),
        )

    profile = x.acceptance_profile
    unit_mismatches = {
        "amplitude": [
            row.check_id for row in checks if row.amplitude_unit_token != profile.amplitude_unit_token
        ],
        "noise": [row.check_id for row in checks if row.noise_unit_token != profile.noise_unit_token],
    }
    if any(unit_mismatches.values()):
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            family=x.family,
            quality_outcome="insufficient_evidence",
            acceptance_profile_id=profile.profile_id,
            metric_values={},
            criterion_findings=(),
            diagnostics={**diagnostics, "metric_unit_mismatch_check_ids": unit_mismatches},
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Wave metric units are exact; no conversion is performed.",),
        )

    declared_channels = {row.channel_id for row in x.acquisition_configuration.elements}
    active_channels = {channel for row in x.records for channel in row.active_channel_ids}
    required_stages = set(profile.required_check_stages)
    present_stage = {
        (record.record_id, check.check_stage)
        for record in x.records
        for check in record.reference_checks
        if check.check_stage in required_stages
    }
    total_target = sum(row.target_extent for row in x.records)
    metric_values = {
        "record_count": float(len(x.records)),
        "baseline_count": float(len(baseline_ids)),
        "observation_count": float(len(observation_ids)),
        "coverage_fraction": sum(row.examined_extent for row in x.records) / total_target,
        "channel_coverage_fraction": len(active_channels) / len(declared_channels),
        "reference_stage_coverage_fraction": len(present_stage) / (len(x.records) * len(required_stages)),
        "maximum_absolute_timing_error_s": max(abs(row.timing_error_s) for row in checks),
        "minimum_amplitude_metric": min(row.amplitude_metric for row in checks),
        "maximum_noise_metric": max(row.noise_metric for row in checks),
        "maximum_localization_error_m": max(row.localization_error_m for row in checks),
        "maximum_reference_consistency_error": max(row.reference_consistency_error for row in checks),
    }
    metric_units = {
        "record_count": "count",
        "baseline_count": "count",
        "observation_count": "count",
        "coverage_fraction": "1",
        "channel_coverage_fraction": "1",
        "reference_stage_coverage_fraction": "1",
        "maximum_absolute_timing_error_s": "s",
        "minimum_amplitude_metric": profile.amplitude_unit_token,
        "maximum_noise_metric": profile.noise_unit_token,
        "maximum_localization_error_m": "m",
        "maximum_reference_consistency_error": "1",
    }
    criteria = {row.metric_id: row for row in profile.criteria}
    criterion_unit_mismatches = [
        row.criterion_id for row in profile.criteria if row.unit_token != metric_units[row.metric_id]
    ]
    if criterion_unit_mismatches:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            family=x.family,
            quality_outcome="insufficient_evidence",
            acceptance_profile_id=profile.profile_id,
            metric_values=metric_values,
            criterion_findings=(),
            diagnostics={**diagnostics, "criterion_unit_mismatch_ids": criterion_unit_mismatches},
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Caller criterion units must match metrics exactly.",),
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
    outcome = "fail" if "fail" in outcomes else "review" if "review" in outcomes else "pass"
    report = _bound_report(
        assessment_id=x.assessment_id,
        campaign_id=x.campaign_id,
        family=x.family,
        quality_outcome=outcome,
        acceptance_profile_id=profile.profile_id,
        metric_values=metric_values,
        criterion_findings=findings,
        diagnostics={
            **diagnostics,
            "procedure_id": x.procedure_id,
            "procedure_revision": x.procedure_revision,
            "array_id": x.acquisition_configuration.array_id,
            "coupling_state_id": x.acquisition_configuration.coupling_state_id,
            "clock_id": x.acquisition_configuration.clock_id,
            "required_check_stages": list(profile.required_check_stages),
        },
        input_digest=input_digest,
    )
    return Calculation(
        status="computed",
        values=report.model_dump(),
        notes=(
            "Pass, review and fail use only caller-authored profile limits.",
            "Metrics audit campaign evidence and do not detect or size damage, establish POD, accept an indication, or qualify a method.",
        ),
    )


def specifications():
    output_units = {
        "report_schema_version": "1",
        "assessment_id": "1",
        "campaign_id": "1",
        "family": "1",
        "quality_outcome": "1",
        "acceptance_profile_id": "1",
        "metric_values": "mixed",
        "criterion_findings": "mixed",
        "diagnostics": "mixed",
        "input_digest": "1",
        "caller_acceptance_profile_only": "1",
        "automatic_damage_detection_or_sizing": "1",
        "pod_claimed": "1",
        "physical_qualification": "1",
        "report_digest": "1",
    }

    def spec(family: WaveFamily):
        def same_identity(x, context):
            if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
                raise ValueError("wave campaign asset and location must match run context")
            if x.family != family:
                raise ValueError(f"{family} model requires its matching campaign family")

        return ModelSpec(
            f"inspection.{family}_campaign_quality",
            WaveCampaignQualityAssessment,
            wave_campaign_quality,
            output_units,
            (
                "Array, coupling, acquisition, baseline, observation and reference identities are caller supplied.",
                "No automatic damage detection, sizing, POD, acceptance or physical qualification is produced.",
            ),
            ("authored_wave_reference_baseline_campaign_quality_audit",),
            context_validator=same_identity,
        )

    return [spec("acoustic_emission"), spec("guided_waves")]

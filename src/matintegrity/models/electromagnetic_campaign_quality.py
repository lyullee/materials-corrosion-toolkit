"""Campaign quality audit for eddy-current and magnetic-flux-leakage evidence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

ElectromagneticFamily = Literal["eddy_current", "flux_leakage"]
MetricId = Literal[
    "scan_count",
    "coverage_fraction",
    "channel_coverage_fraction",
    "reference_feature_stage_coverage_fraction",
    "response_present_fraction",
    "minimum_sensitivity_metric",
    "maximum_noise_metric",
    "maximum_resolution_metric",
    "maximum_drift_relative_change",
]


class ElectromagneticReferenceFeature(Contract):
    feature_id: str = Field(min_length=1)
    feature_type_descriptor: str = Field(min_length=1)
    physical_location_definition: str = Field(min_length=1)
    nominal_dimension: Positive
    dimension_unit_token: str = Field(min_length=1)
    expanded_dimension_uncertainty: Nonnegative
    physical_feature_identity_reviewed: bool
    feature_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class ElectromagneticReferenceStandard(Contract):
    reference_standard_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    standard_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    features: tuple[ElectromagneticReferenceFeature, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_features(self):
        identifiers = [row.feature_id for row in self.features]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("electromagnetic reference feature identifiers must be unique")
        return self


class ElectromagneticAcquisitionConfiguration(Contract):
    configuration_id: str = Field(min_length=1)
    family: ElectromagneticFamily
    probe_or_sensor_array_id: str = Field(min_length=1)
    magnetizer_id: str | None = Field(default=None, min_length=1)
    excitation_id: str = Field(min_length=1)
    excitation_value: Nonnegative
    excitation_unit_token: str = Field(min_length=1)
    nominal_lift_off_m: Nonnegative
    expanded_lift_off_uncertainty_m: Nonnegative
    lift_off_control_basis: str = Field(min_length=1)
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def family_specific_identity(self):
        if self.family == "flux_leakage" and self.magnetizer_id is None:
            raise ValueError("flux-leakage campaign configurations require magnetizer identity")
        if self.family == "eddy_current" and self.magnetizer_id is not None:
            raise ValueError("eddy-current campaign configurations cannot declare an MFL magnetizer")
        return self


class ElectromagneticReferenceCheck(Contract):
    check_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    elapsed_time_s: Nonnegative
    check_stage: str = Field(min_length=1)
    reference_feature_id: str = Field(min_length=1)
    channel_id: str = Field(min_length=1)
    drift_group_id: str = Field(min_length=1)
    reported_response_present: bool
    sensitivity_metric: Nonnegative
    sensitivity_unit_token: str = Field(min_length=1)
    expanded_sensitivity_uncertainty: Nonnegative
    noise_metric: Nonnegative
    noise_unit_token: str = Field(min_length=1)
    expanded_noise_uncertainty: Nonnegative
    resolution_metric: Nonnegative
    resolution_unit_token: str = Field(min_length=1)
    expanded_resolution_uncertainty: Nonnegative
    check_method_definition: str = Field(min_length=1)
    check_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_check_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid electromagnetic reference checks require a basis")
        return self


class EncodedElectromagneticScanEvidence(Contract):
    scan_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    configuration_id: str = Field(min_length=1)
    reference_standard_id: str = Field(min_length=1)
    active_channel_ids: tuple[str, ...] = Field(min_length=1)
    scan_speed_m_s: Nonnegative
    expanded_scan_speed_uncertainty_m_s: Nonnegative
    speed_control_basis: str = Field(min_length=1)
    target_extent: Positive
    examined_extent: Nonnegative
    extent_unit_token: str = Field(min_length=1)
    encoded_data_id: str = Field(min_length=1)
    encoded_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    encoded_data_format: str = Field(min_length=1)
    checks: tuple[ElectromagneticReferenceCheck, ...] = Field(min_length=1)
    scan_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_scan(self):
        if self.examined_extent > self.target_extent:
            raise ValueError("electromagnetic examined extent cannot exceed target extent")
        if len(set(self.active_channel_ids)) != len(self.active_channel_ids):
            raise ValueError("active electromagnetic channel identifiers must be unique")
        check_ids = [row.check_id for row in self.checks]
        if len(set(check_ids)) != len(check_ids):
            raise ValueError("electromagnetic check identifiers must be unique within a scan")
        if {row.channel_id for row in self.checks} - set(self.active_channel_ids):
            raise ValueError("reference checks must use active scan channels")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid electromagnetic scans require a basis")
        return self


class ElectromagneticQualityCriterion(Contract):
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
            raise ValueError("maximum electromagnetic criteria require ordered pass and fail limits")
        if self.direction == "minimum" and self.fail_limit > self.pass_limit:
            raise ValueError("minimum electromagnetic criteria require ordered pass and fail limits")
        return self


class ElectromagneticCampaignAcceptanceProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    family: ElectromagneticFamily
    required_check_stages: tuple[str, ...] = Field(min_length=1)
    sensitivity_metric_definition: str = Field(min_length=1)
    sensitivity_unit_token: str = Field(min_length=1)
    noise_metric_definition: str = Field(min_length=1)
    noise_unit_token: str = Field(min_length=1)
    resolution_metric_definition: str = Field(min_length=1)
    resolution_unit_token: str = Field(min_length=1)
    criteria: tuple[ElectromagneticQualityCriterion, ...] = Field(min_length=9)
    profile_provider_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_authority: str = Field(min_length=1)
    built_in_code_or_standard_limits_used: Literal[False] = False
    automatic_sizing_or_acceptance_claimed: Literal[False] = False
    pod_claimed: Literal[False] = False
    physical_qualification_claimed: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_profile(self):
        if len(set(self.required_check_stages)) != len(self.required_check_stages):
            raise ValueError("required electromagnetic check stages must be unique")
        metric_ids = [row.metric_id for row in self.criteria]
        criterion_ids = [row.criterion_id for row in self.criteria]
        if len(set(metric_ids)) != len(metric_ids) or len(set(criterion_ids)) != len(criterion_ids):
            raise ValueError("electromagnetic profile criteria and metrics must be unique")
        required = {
            "scan_count",
            "coverage_fraction",
            "channel_coverage_fraction",
            "reference_feature_stage_coverage_fraction",
            "response_present_fraction",
            "minimum_sensitivity_metric",
            "maximum_noise_metric",
            "maximum_resolution_metric",
            "maximum_drift_relative_change",
        }
        if set(metric_ids) != required:
            raise ValueError("electromagnetic profile requires the complete campaign metric set")
        return self


class ElectromagneticCampaignQualityAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    family: ElectromagneticFamily
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    extent_unit_token: str = Field(min_length=1)
    declared_channel_ids: tuple[str, ...] = Field(min_length=1)
    acquisition_configuration: ElectromagneticAcquisitionConfiguration
    reference_standard: ElectromagneticReferenceStandard
    scans: tuple[EncodedElectromagneticScanEvidence, ...] = Field(min_length=1)
    acceptance_profile: ElectromagneticCampaignAcceptanceProfile
    procedure_probe_sensor_magnetizer_and_excitation_reviewed: bool
    lift_off_speed_and_uncertainty_reviewed: bool
    reference_standard_features_reviewed: bool
    encoded_scan_identity_and_digests_reviewed: bool
    channel_mapping_and_coverage_reviewed: bool
    pre_in_post_checks_and_drift_groups_reviewed: bool
    sensitivity_noise_resolution_units_and_uncertainty_reviewed: bool
    caller_acceptance_profile_reviewed: bool
    record_validity_and_missingness_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        if (
            self.acquisition_configuration.family != self.family
            or self.acceptance_profile.family != self.family
        ):
            raise ValueError("electromagnetic campaign, configuration and profile families must match")
        if len(set(self.declared_channel_ids)) != len(self.declared_channel_ids):
            raise ValueError("declared electromagnetic channels must be unique")
        scan_ids = [row.scan_id for row in self.scans]
        encoded_ids = [row.encoded_data_id for row in self.scans]
        encoded_digests = [row.encoded_data_digest for row in self.scans]
        for values, label in (
            (scan_ids, "scan"),
            (encoded_ids, "encoded data"),
            (encoded_digests, "encoded digest"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"electromagnetic campaign {label} identities must be unique")
        feature_ids = {row.feature_id for row in self.reference_standard.features}
        sequence_indices = []
        for scan in self.scans:
            if (scan.procedure_id, scan.procedure_revision) != (
                self.procedure_id,
                self.procedure_revision,
            ):
                raise ValueError("all electromagnetic scans must match campaign procedure identity")
            if scan.configuration_id != self.acquisition_configuration.configuration_id:
                raise ValueError("all scans must reference the campaign acquisition configuration")
            if scan.reference_standard_id != self.reference_standard.reference_standard_id:
                raise ValueError("all scans must reference the campaign reference standard")
            if scan.extent_unit_token != self.extent_unit_token:
                raise ValueError("all scan extents must use the campaign unit")
            if set(scan.active_channel_ids) - set(self.declared_channel_ids):
                raise ValueError("scan channels must be declared by the campaign")
            if {row.reference_feature_id for row in scan.checks} - feature_ids:
                raise ValueError("checks must reference declared standard features")
            sequence_indices.extend(row.sequence_index for row in scan.checks)
        if len(set(sequence_indices)) != len(sequence_indices):
            raise ValueError("electromagnetic check sequence indices must be unique across the campaign")
        return self


class ElectromagneticCampaignQualityReport(Contract):
    report_schema_version: Literal["matintegrity.electromagnetic_campaign_quality_report.v1"] = (
        "matintegrity.electromagnetic_campaign_quality_report.v1"
    )
    assessment_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    family: ElectromagneticFamily
    quality_outcome: Literal["pass", "review", "fail", "insufficient_evidence"]
    acceptance_profile_id: str = Field(min_length=1)
    metric_values: dict[str, float]
    criterion_findings: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_profile_only: Literal[True] = True
    automatic_sizing_or_acceptance: Literal[False] = False
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
            raise ValueError("electromagnetic campaign report digest does not match report content")
        return self


def _bound_report(**payload: Any) -> ElectromagneticCampaignQualityReport:
    unsigned = ElectromagneticCampaignQualityReport.model_validate(
        {**payload, "report_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return ElectromagneticCampaignQualityReport.model_validate(
        {**payload, "report_digest": canonical_digest(unsigned.digest_payload())}
    )


def _criterion_outcome(value: float, criterion: ElectromagneticQualityCriterion) -> str:
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


def electromagnetic_campaign_quality(x: ElectromagneticCampaignQualityAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "procedure_probe_sensor_magnetizer_and_excitation_reviewed",
            "lift_off_speed_and_uncertainty_reviewed",
            "reference_standard_features_reviewed",
            "encoded_scan_identity_and_digests_reviewed",
            "channel_mapping_and_coverage_reviewed",
            "pre_in_post_checks_and_drift_groups_reviewed",
            "sensitivity_noise_resolution_units_and_uncertainty_reviewed",
            "caller_acceptance_profile_reviewed",
            "record_validity_and_missingness_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_feature_ids = [
        row.feature_id for row in x.reference_standard.features if not row.physical_feature_identity_reviewed
    ]
    invalid_scan_ids = [row.scan_id for row in x.scans if not row.record_valid]
    checks = [row for scan in x.scans for row in scan.checks]
    invalid_check_ids = [row.check_id for row in checks if not row.record_valid]
    input_digest = canonical_digest(x.model_dump(mode="json"))
    diagnostics = {
        "missing_reviews": missing_reviews,
        "invalid_reference_feature_ids": invalid_feature_ids,
        "invalid_scan_ids": invalid_scan_ids,
        "invalid_check_ids": invalid_check_ids,
        "encoded_data_ids": [row.encoded_data_id for row in x.scans],
        "encoded_data_digests": [row.encoded_data_digest for row in x.scans],
    }
    if missing_reviews or invalid_feature_ids or invalid_scan_ids or invalid_check_ids:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            family=x.family,
            quality_outcome="insufficient_evidence",
            acceptance_profile_id=x.acceptance_profile.profile_id,
            metric_values={},
            criterion_findings=(),
            diagnostics=diagnostics,
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Reviewed valid campaign evidence is required.",),
        )

    profile = x.acceptance_profile
    unit_mismatches = {
        "sensitivity": [
            row.check_id for row in checks if row.sensitivity_unit_token != profile.sensitivity_unit_token
        ],
        "noise": [row.check_id for row in checks if row.noise_unit_token != profile.noise_unit_token],
        "resolution": [
            row.check_id for row in checks if row.resolution_unit_token != profile.resolution_unit_token
        ],
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
            notes=("Sensitivity, noise and resolution units are exact; no conversion is performed.",),
        )

    drift_values = []
    unavailable_drift_groups = []
    drift_groups: dict[str, list[ElectromagneticReferenceCheck]] = {}
    for row in checks:
        drift_groups.setdefault(row.drift_group_id, []).append(row)
    for group_id, rows in drift_groups.items():
        if len(rows) < 2:
            continue
        ordered = sorted(rows, key=lambda row: (row.elapsed_time_s, row.sequence_index))
        first, last = ordered[0], ordered[-1]
        if first.reference_feature_id != last.reference_feature_id or first.channel_id != last.channel_id:
            unavailable_drift_groups.append(f"{group_id}:identity_mismatch")
        elif first.sensitivity_metric == 0.0:
            unavailable_drift_groups.append(f"{group_id}:zero_baseline")
        else:
            drift_values.append(
                abs(last.sensitivity_metric - first.sensitivity_metric) / first.sensitivity_metric
            )
    if not drift_values:
        unavailable_drift_groups.append("no_usable_drift_group")
    if unavailable_drift_groups:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            family=x.family,
            quality_outcome="insufficient_evidence",
            acceptance_profile_id=profile.profile_id,
            metric_values={},
            criterion_findings=(),
            diagnostics={**diagnostics, "unavailable_drift_groups": unavailable_drift_groups},
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Drift requires a repeated feature and channel with a nonzero baseline.",),
        )

    feature_ids = {row.feature_id for row in x.reference_standard.features}
    required_stages = set(profile.required_check_stages)
    present_feature_stage = {
        (scan.scan_id, row.reference_feature_id, row.check_stage)
        for scan in x.scans
        for row in scan.checks
        if row.check_stage in required_stages
    }
    expected_feature_stage_count = len(x.scans) * len(feature_ids) * len(required_stages)
    total_target = sum(row.target_extent for row in x.scans)
    total_examined = sum(row.examined_extent for row in x.scans)
    active_channels = {channel for scan in x.scans for channel in scan.active_channel_ids}
    metric_values = {
        "scan_count": float(len(x.scans)),
        "coverage_fraction": total_examined / total_target,
        "channel_coverage_fraction": len(active_channels) / len(x.declared_channel_ids),
        "reference_feature_stage_coverage_fraction": len(present_feature_stage)
        / expected_feature_stage_count,
        "response_present_fraction": sum(row.reported_response_present for row in checks) / len(checks),
        "minimum_sensitivity_metric": min(row.sensitivity_metric for row in checks),
        "maximum_noise_metric": max(row.noise_metric for row in checks),
        "maximum_resolution_metric": max(row.resolution_metric for row in checks),
        "maximum_drift_relative_change": max(drift_values),
    }
    metric_units = {
        "scan_count": "count",
        "coverage_fraction": "1",
        "channel_coverage_fraction": "1",
        "reference_feature_stage_coverage_fraction": "1",
        "response_present_fraction": "1",
        "minimum_sensitivity_metric": profile.sensitivity_unit_token,
        "maximum_noise_metric": profile.noise_unit_token,
        "maximum_resolution_metric": profile.resolution_unit_token,
        "maximum_drift_relative_change": "1",
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
    quality_outcome = "fail" if "fail" in outcomes else "review" if "review" in outcomes else "pass"
    report = _bound_report(
        assessment_id=x.assessment_id,
        campaign_id=x.campaign_id,
        family=x.family,
        quality_outcome=quality_outcome,
        acceptance_profile_id=profile.profile_id,
        metric_values=metric_values,
        criterion_findings=findings,
        diagnostics={
            **diagnostics,
            "procedure_id": x.procedure_id,
            "procedure_revision": x.procedure_revision,
            "probe_or_sensor_array_id": x.acquisition_configuration.probe_or_sensor_array_id,
            "magnetizer_id": x.acquisition_configuration.magnetizer_id,
            "excitation_id": x.acquisition_configuration.excitation_id,
            "configuration_digest": x.acquisition_configuration.configuration_digest,
            "reference_standard_id": x.reference_standard.reference_standard_id,
            "reference_feature_ids": sorted(feature_ids),
            "required_check_stages": list(profile.required_check_stages),
        },
        input_digest=input_digest,
    )
    return Calculation(
        status="computed",
        values=report.model_dump(),
        notes=(
            "Pass, review and fail use only caller limits; no code or standard value is bundled.",
            "Reference response, noise, resolution and drift are campaign metrics, not sizing, flaw acceptance, POD or qualification.",
            "No compensation, signal fusion, defect classification, life or failure probability is inferred.",
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
        "automatic_sizing_or_acceptance": "1",
        "pod_claimed": "1",
        "physical_qualification": "1",
        "report_digest": "1",
    }

    def spec(family: ElectromagneticFamily):
        def same_identity(x, context):
            if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
                raise ValueError("electromagnetic campaign asset and location must match run context")
            if x.family != family:
                raise ValueError(f"{family} model requires its matching campaign family")

        return ModelSpec(
            f"inspection.{family}_campaign_quality",
            ElectromagneticCampaignQualityAssessment,
            electromagnetic_campaign_quality,
            output_units,
            (
                "Probe/sensor, magnetizer, excitation, lift-off, speed, channel and scan identities are caller supplied.",
                "Reference checks and campaign metrics are evaluated only against caller profile limits.",
                "No automatic sizing, flaw acceptance, POD or physical qualification is produced.",
            ),
            ("authored_electromagnetic_reference_campaign_quality_audit",),
            context_validator=same_identity,
        )

    return [spec("eddy_current"), spec("flux_leakage")]

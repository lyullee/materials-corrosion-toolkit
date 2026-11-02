"""Campaign-level quality audit for caller-supplied leak-test evidence."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

CampaignFamily = Literal["leak_rate", "vacuum_testing", "cryogenic_leak_testing"]
MetricId = Literal[
    "reference_point_count",
    "distinct_reference_level_count",
    "blank_background_count",
    "mean_absolute_blank_background_response",
    "maximum_repeatability_relative_standard_deviation",
    "maximum_drift_relative_change",
    "maximum_relative_response_uncertainty",
    "detection_threshold_response",
]


class LeakCampaignStateIdentity(Contract):
    state_id: str = Field(min_length=1)
    temperature_K: Positive
    expanded_temperature_uncertainty_K: Nonnegative
    internal_pressure_Pa: Nonnegative
    external_pressure_Pa: Nonnegative
    expanded_pressure_uncertainty_Pa: Nonnegative
    pressure_basis: str = Field(min_length=1)
    thermal_and_phase_state_descriptor: str = Field(min_length=1)
    state_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_state_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid leak-test state identities require a basis")
        return self


class ReferenceLeakCampaignPoint(Contract):
    point_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    elapsed_time_s: Nonnegative
    state_id: str = Field(min_length=1)
    physical_reference_id: str = Field(min_length=1)
    reference_level_id: str = Field(min_length=1)
    reference_leak_rate_mol_s: Positive
    expanded_reference_leak_uncertainty_mol_s: Nonnegative
    response_value: float
    expanded_response_uncertainty: Nonnegative
    response_unit_token: str = Field(min_length=1)
    repeatability_group_id: str = Field(min_length=1)
    drift_group_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    observation_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_point_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid reference-leak campaign points require a basis")
        return self


class BlankBackgroundObservation(Contract):
    observation_id: str = Field(min_length=1)
    observation_kind: Literal["blank", "background"]
    sequence_index: int = Field(ge=0)
    elapsed_time_s: Nonnegative
    state_id: str = Field(min_length=1)
    response_value: float
    expanded_response_uncertainty: Nonnegative
    response_unit_token: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    observation_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_observation_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid blank or background observations require a basis")
        return self


class DetectionCapabilityEvidence(Contract):
    evidence_id: str = Field(min_length=1)
    mode: Literal["detection_threshold", "response_uncertainty_profile"]
    detection_threshold_response: Nonnegative | None = None
    response_unit_token: str | None = None
    uncertainty_profile_id: str | None = None
    uncertainty_profile_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    capability_definition: str = Field(min_length=1)
    capability_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def mode_specific_fields(self):
        if self.mode == "detection_threshold":
            if self.detection_threshold_response is None or not self.response_unit_token:
                raise ValueError("detection-threshold evidence requires a response value and unit")
            if self.uncertainty_profile_id is not None or self.uncertainty_profile_digest is not None:
                raise ValueError("detection-threshold evidence cannot contain an uncertainty profile")
        else:
            if not self.uncertainty_profile_id or self.uncertainty_profile_digest is None:
                raise ValueError("response-uncertainty evidence requires profile identity and digest")
            if self.detection_threshold_response is not None or self.response_unit_token is not None:
                raise ValueError("response-uncertainty evidence cannot contain a detection threshold")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid detection-capability evidence requires a basis")
        return self


class LeakCampaignQualityCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    metric_id: MetricId
    direction: Literal["minimum", "maximum"]
    pass_limit: Nonnegative
    fail_limit: Nonnegative
    unit_token: str = Field(min_length=1)
    criterion_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_decision_limits(self):
        if self.direction == "maximum" and self.fail_limit < self.pass_limit:
            raise ValueError("maximum criteria require fail limit at or above pass limit")
        if self.direction == "minimum" and self.fail_limit > self.pass_limit:
            raise ValueError("minimum criteria require fail limit at or below pass limit")
        return self


class LeakCampaignAcceptanceProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    campaign_family: CampaignFamily
    criteria: tuple[LeakCampaignQualityCriterion, ...] = Field(min_length=7)
    profile_provider_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_authority: str = Field(min_length=1)
    built_in_standard_criteria_used: Literal[False] = False
    physical_qualification_claimed: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_unique_metrics(self):
        criterion_ids = [row.criterion_id for row in self.criteria]
        metric_ids = [row.metric_id for row in self.criteria]
        if len(set(criterion_ids)) != len(criterion_ids):
            raise ValueError("leak campaign criterion identifiers must be unique")
        if len(set(metric_ids)) != len(metric_ids):
            raise ValueError("leak campaign quality metrics must have one criterion each")
        core = {
            "reference_point_count",
            "distinct_reference_level_count",
            "blank_background_count",
            "mean_absolute_blank_background_response",
            "maximum_repeatability_relative_standard_deviation",
            "maximum_drift_relative_change",
        }
        if not core <= set(metric_ids):
            raise ValueError("leak campaign profile is missing a core quality criterion")
        detection_metrics = {
            "detection_threshold_response",
            "maximum_relative_response_uncertainty",
        } & set(metric_ids)
        if len(detection_metrics) != 1:
            raise ValueError("leak campaign profile requires exactly one detection-capability criterion")
        return self


class LeakTestCampaignQualityAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    campaign_family: CampaignFamily
    method_id: str = Field(min_length=1)
    instrument_id: str = Field(min_length=1)
    instrument_configuration_id: str = Field(min_length=1)
    instrument_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    test_gas_id: str = Field(min_length=1)
    response_definition: str = Field(min_length=1)
    response_unit_token: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    states: tuple[LeakCampaignStateIdentity, ...] = Field(min_length=1)
    reference_points: tuple[ReferenceLeakCampaignPoint, ...] = Field(min_length=1)
    blank_background_observations: tuple[BlankBackgroundObservation, ...] = Field(min_length=1)
    detection_capability: DetectionCapabilityEvidence
    acceptance_profile: LeakCampaignAcceptanceProfile
    campaign_method_instrument_and_gas_reviewed: bool
    temperature_pressure_and_state_identity_reviewed: bool
    reference_leak_traceability_and_uncertainty_reviewed: bool
    blank_and_background_records_reviewed: bool
    repeatability_and_drift_groups_reviewed: bool
    detection_threshold_or_uncertainty_profile_reviewed: bool
    caller_acceptance_profile_reviewed: bool
    record_digests_and_missingness_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign_records(self):
        if self.acceptance_profile.campaign_family != self.campaign_family:
            raise ValueError("leak campaign and acceptance profile families must match")
        identifiers = [row.state_id for row in self.states]
        point_ids = [row.point_id for row in self.reference_points]
        observation_ids = [row.observation_id for row in self.blank_background_observations]
        for values, label in (
            (identifiers, "state"),
            (point_ids, "reference point"),
            (observation_ids, "blank/background observation"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"leak campaign {label} identifiers must be unique")
        known_states = set(identifiers)
        for row in (*self.reference_points, *self.blank_background_observations):
            if row.state_id not in known_states:
                raise ValueError("every leak campaign observation must reference a declared state")
            if row.response_unit_token != self.response_unit_token:
                raise ValueError("all leak campaign responses must use the exact campaign unit token")
        if (
            self.detection_capability.mode == "detection_threshold"
            and self.detection_capability.response_unit_token != self.response_unit_token
        ):
            raise ValueError("detection threshold and campaign response units must match exactly")
        sequence = [row.sequence_index for row in self.reference_points]
        sequence.extend(row.sequence_index for row in self.blank_background_observations)
        if len(set(sequence)) != len(sequence):
            raise ValueError("leak campaign sequence indices must be unique across observations")
        if self.detection_capability.mode == "detection_threshold":
            required_metric = "detection_threshold_response"
        else:
            required_metric = "maximum_relative_response_uncertainty"
        if required_metric not in {row.metric_id for row in self.acceptance_profile.criteria}:
            raise ValueError("detection evidence mode and acceptance-profile metric must match")
        return self


def _criterion_outcome(value: float, criterion: LeakCampaignQualityCriterion) -> str:
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


def leak_test_campaign_quality(x: LeakTestCampaignQualityAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "campaign_method_instrument_and_gas_reviewed",
            "temperature_pressure_and_state_identity_reviewed",
            "reference_leak_traceability_and_uncertainty_reviewed",
            "blank_and_background_records_reviewed",
            "repeatability_and_drift_groups_reviewed",
            "detection_threshold_or_uncertainty_profile_reviewed",
            "caller_acceptance_profile_reviewed",
            "record_digests_and_missingness_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_state_ids = [row.state_id for row in x.states if not row.record_valid]
    invalid_reference_point_ids = [row.point_id for row in x.reference_points if not row.record_valid]
    invalid_blank_background_ids = [
        row.observation_id for row in x.blank_background_observations if not row.record_valid
    ]
    if (
        missing_reviews
        or invalid_state_ids
        or invalid_reference_point_ids
        or invalid_blank_background_ids
        or not x.detection_capability.record_valid
    ):
        body = {
            "assessment_id": x.assessment_id,
            "campaign_id": x.campaign_id,
            "campaign_family": x.campaign_family,
            "quality_outcome": "insufficient_evidence",
            "missing_reviews": missing_reviews,
            "invalid_state_ids": invalid_state_ids,
            "invalid_reference_point_ids": invalid_reference_point_ids,
            "invalid_blank_background_observation_ids": invalid_blank_background_ids,
            "detection_capability_record_valid": x.detection_capability.record_valid,
            "physical_qualification": False,
        }
        body["report_digest"] = canonical_digest(body)
        return Calculation(
            status="needs_data",
            values=body,
            notes=("Campaign quality is withheld until all reviewed evidence records are valid.",),
        )

    unavailable_metrics = []
    metric_values: dict[str, float] = {
        "reference_point_count": float(len(x.reference_points)),
        "distinct_reference_level_count": float(len({row.reference_level_id for row in x.reference_points})),
        "blank_background_count": float(len(x.blank_background_observations)),
        "mean_absolute_blank_background_response": math.fsum(
            abs(row.response_value) for row in x.blank_background_observations
        )
        / len(x.blank_background_observations),
    }
    repeatability_values = []
    repeatability_groups: dict[str, list[ReferenceLeakCampaignPoint]] = {}
    drift_groups: dict[str, list[ReferenceLeakCampaignPoint]] = {}
    for row in x.reference_points:
        repeatability_groups.setdefault(row.repeatability_group_id, []).append(row)
        drift_groups.setdefault(row.drift_group_id, []).append(row)
    for group_id, rows in repeatability_groups.items():
        if len(rows) < 2:
            continue
        mean = math.fsum(row.response_value for row in rows) / len(rows)
        if mean == 0.0:
            unavailable_metrics.append(f"repeatability:{group_id}:zero_mean")
            continue
        variance = math.fsum((row.response_value - mean) ** 2 for row in rows) / (len(rows) - 1)
        repeatability_values.append(math.sqrt(variance) / abs(mean))
    if repeatability_values:
        metric_values["maximum_repeatability_relative_standard_deviation"] = max(repeatability_values)
    else:
        unavailable_metrics.append("maximum_repeatability_relative_standard_deviation")

    drift_values = []
    for group_id, rows in drift_groups.items():
        if len(rows) < 2:
            continue
        ordered = sorted(rows, key=lambda row: (row.elapsed_time_s, row.sequence_index))
        first, last = ordered[0], ordered[-1]
        same_basis = (
            first.reference_level_id == last.reference_level_id
            and first.physical_reference_id == last.physical_reference_id
            and first.state_id == last.state_id
        )
        if not same_basis:
            unavailable_metrics.append(f"drift:{group_id}:identity_mismatch")
            continue
        if first.response_value == 0.0:
            unavailable_metrics.append(f"drift:{group_id}:zero_baseline")
            continue
        drift_values.append(abs(last.response_value - first.response_value) / abs(first.response_value))
    if drift_values:
        metric_values["maximum_drift_relative_change"] = max(drift_values)
    else:
        unavailable_metrics.append("maximum_drift_relative_change")

    if x.detection_capability.mode == "detection_threshold":
        metric_values["detection_threshold_response"] = x.detection_capability.detection_threshold_response
    else:
        relative_uncertainties = []
        for row in (*x.reference_points, *x.blank_background_observations):
            if row.response_value == 0.0:
                unavailable_metrics.append(
                    f"response_uncertainty:{getattr(row, 'point_id', None) or row.observation_id}:zero_response"
                )
            else:
                relative_uncertainties.append(row.expanded_response_uncertainty / abs(row.response_value))
        if relative_uncertainties:
            metric_values["maximum_relative_response_uncertainty"] = max(relative_uncertainties)
        else:
            unavailable_metrics.append("maximum_relative_response_uncertainty")

    criteria = {row.metric_id: row for row in x.acceptance_profile.criteria}
    metric_units = {
        "reference_point_count": "count",
        "distinct_reference_level_count": "count",
        "blank_background_count": "count",
        "mean_absolute_blank_background_response": x.response_unit_token,
        "maximum_repeatability_relative_standard_deviation": "1",
        "maximum_drift_relative_change": "1",
        "maximum_relative_response_uncertainty": "1",
        "detection_threshold_response": x.response_unit_token,
    }
    unit_mismatch_metrics = [
        metric_id
        for metric_id, criterion in criteria.items()
        if criterion.unit_token != metric_units[metric_id]
    ]
    missing_metric_ids = sorted(set(criteria) - set(metric_values))
    if unavailable_metrics or unit_mismatch_metrics or missing_metric_ids:
        body = {
            "assessment_id": x.assessment_id,
            "campaign_id": x.campaign_id,
            "campaign_family": x.campaign_family,
            "quality_outcome": "insufficient_evidence",
            "metric_values": metric_values,
            "unavailable_metric_bases": unavailable_metrics,
            "criterion_unit_mismatch_metric_ids": unit_mismatch_metrics,
            "missing_metric_ids": missing_metric_ids,
            "physical_qualification": False,
        }
        body["report_digest"] = canonical_digest(body)
        return Calculation(
            status="needs_data",
            values=body,
            notes=("Unavailable or unit-incompatible campaign metrics cannot be silently replaced.",),
        )

    findings = []
    for metric_id in sorted(criteria):
        criterion = criteria[metric_id]
        value = metric_values[metric_id]
        findings.append(
            {
                "criterion_id": criterion.criterion_id,
                "metric_id": metric_id,
                "value": value,
                "unit": metric_units[metric_id],
                "direction": criterion.direction,
                "pass_limit": criterion.pass_limit,
                "fail_limit": criterion.fail_limit,
                "outcome": _criterion_outcome(value, criterion),
                "criterion_basis": criterion.criterion_basis,
            }
        )
    finding_outcomes = {row["outcome"] for row in findings}
    quality_outcome = (
        "fail" if "fail" in finding_outcomes else "review" if "review" in finding_outcomes else "pass"
    )
    body = {
        "assessment_id": x.assessment_id,
        "campaign_id": x.campaign_id,
        "campaign_family": x.campaign_family,
        "quality_outcome": quality_outcome,
        "acceptance_profile_id": x.acceptance_profile.profile_id,
        "acceptance_profile_version": x.acceptance_profile.profile_version,
        "metric_values": metric_values,
        "criterion_findings": findings,
        "reference_point_ids": [row.point_id for row in x.reference_points],
        "blank_background_observation_ids": [row.observation_id for row in x.blank_background_observations],
        "state_ids": [row.state_id for row in x.states],
        "detection_capability_evidence_id": x.detection_capability.evidence_id,
        "caller_acceptance_profile_only": True,
        "physical_qualification": False,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
    }
    body["report_digest"] = canonical_digest(body)
    return Calculation(
        status="computed",
        values=body,
        notes=(
            "Pass, review and fail outcomes use only caller-provided acceptance criteria; no standard limit is bundled.",
            "This campaign audit does not calibrate an instrument, invert an unknown leak or establish physical qualification.",
            "No detection probability, leak-path physics, FTA probability, acceptance-code conclusion or life is inferred.",
        ),
    )


def specifications():
    output_units = {
        "assessment_id": "1",
        "campaign_id": "1",
        "campaign_family": "1",
        "quality_outcome": "1",
        "acceptance_profile_id": "1",
        "acceptance_profile_version": "1",
        "metric_values": "mixed",
        "criterion_findings": "mixed",
        "reference_point_ids": "1",
        "blank_background_observation_ids": "1",
        "state_ids": "1",
        "detection_capability_evidence_id": "1",
        "caller_acceptance_profile_only": "1",
        "physical_qualification": "1",
        "input_digest": "1",
        "report_digest": "1",
    }

    def spec(family: CampaignFamily):
        def same_identity(x, context):
            if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
                raise ValueError("leak campaign asset and location must match run context")
            if x.campaign_family != family:
                raise ValueError(f"{family} model requires its matching campaign family")

        return ModelSpec(
            f"inspection.{family}_campaign_quality",
            LeakTestCampaignQualityAssessment,
            leak_test_campaign_quality,
            output_units,
            (
                "Reference, blank/background, state, repeatability, drift and capability evidence is caller supplied.",
                "Criteria and pass/review/fail boundaries are caller owned and unit exact.",
                "Campaign quality is separate from calibration, physical qualification and field acceptance.",
            ),
            ("authored_caller_leak_campaign_quality_audit",),
            context_validator=same_identity,
        )

    return [spec(family) for family in ("leak_rate", "vacuum_testing", "cryogenic_leak_testing")]

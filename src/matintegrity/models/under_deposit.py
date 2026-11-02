"""Caller-calibrated under-deposit exposure and local-loss accounting."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Nonnegative, Positive
from ..local_environment_history import (
    LocalEnvironmentHistoryAssessment,
    assess_local_environment_history,
)
from ..registry import ModelSpec


class UnderDepositLossInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    temperature_K: Positive | None = None
    deposit_coverage_fraction: Fraction | None = None
    stagnation_descriptor: str | None = None
    differential_aeration_descriptor: str | None = None
    calibrated_local_loss_rate_m_s: Nonnegative | None = None
    rate_provider_id: str | None = None
    rate_provider_state_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("under-deposit intervals must have positive duration")
        required = (
            self.temperature_K,
            self.deposit_coverage_fraction,
            self.stagnation_descriptor,
            self.differential_aeration_descriptor,
            self.calibrated_local_loss_rate_m_s,
            self.rate_provider_id,
            self.rate_provider_state_digest,
        )
        if self.record_valid and any(value is None for value in required):
            raise ValueError("a valid under-deposit interval requires state and rate-provider fields")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid under-deposit interval requires a basis")
        return self


class UnderDepositRateSupport(Contract):
    support_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    rate_provider_id: str = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_deposit_coverage_fraction: Fraction
    maximum_deposit_coverage_fraction: Fraction
    supported_stagnation_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_differential_aeration_descriptors: tuple[str, ...] = Field(min_length=1)
    support_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("under-deposit temperature support must be ordered")
        if self.maximum_deposit_coverage_fraction < self.minimum_deposit_coverage_fraction:
            raise ValueError("under-deposit coverage support must be ordered")
        return self


class UnderDepositExposureHistory(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    assessed_surface_area_m2: Positive
    intervals: tuple[UnderDepositLossInterval, ...] = Field(min_length=1)
    rate_support: UnderDepositRateSupport
    material_and_environment_reviewed: bool
    clock_and_interval_completeness_reviewed: bool
    deposit_coverage_reviewed: bool
    stagnation_and_aeration_mapping_reviewed: bool
    calibrated_rate_provider_reviewed: bool

    @model_validator(mode="after")
    def ordered_intervals(self):
        identifiers = [row.interval_id for row in self.intervals]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("under-deposit interval identifiers must be unique")
        for first, second in zip(self.intervals, self.intervals[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("under-deposit intervals must be ordered and cannot overlap")
        return self


def under_deposit_exposure_history(x: UnderDepositExposureHistory) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_and_environment_reviewed",
            "clock_and_interval_completeness_reviewed",
            "deposit_coverage_reviewed",
            "stagnation_and_aeration_mapping_reviewed",
            "calibrated_rate_provider_reviewed",
        )
        if not getattr(x, name)
    ]
    support = x.rate_support
    identity_match = (
        x.material_condition_id == support.material_condition_id
        and x.environment_id == support.environment_id
    )

    invalid = [row.interval_id for row in x.intervals if not row.record_valid]
    provider_mismatch = [
        row.interval_id
        for row in x.intervals
        if row.record_valid and row.rate_provider_id != support.rate_provider_id
    ]
    if missing_reviews or not identity_match or invalid or provider_mismatch:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "material_and_environment_identity_match": identity_match,
                "invalid_interval_ids": invalid,
                "provider_mismatch_interval_ids": provider_mismatch,
                "missing_reviews": missing_reviews,
            },
            notes=("Complete reviewed intervals and one matching calibrated rate provider are required.",),
        )

    unsupported = []
    for row in x.intervals:
        if not (
            support.minimum_temperature_K <= row.temperature_K <= support.maximum_temperature_K
            and support.minimum_deposit_coverage_fraction
            <= row.deposit_coverage_fraction
            <= support.maximum_deposit_coverage_fraction
            and row.stagnation_descriptor in support.supported_stagnation_descriptors
            and row.differential_aeration_descriptor in support.supported_differential_aeration_descriptors
        ):
            unsupported.append(row.interval_id)
    if unsupported:
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "outside_rate_support_interval_ids": unsupported,
                "missing_reviews": [],
            },
            notes=("At least one reviewed state is outside the calibrated rate-provider support.",),
        )

    elapsed = 0.0
    covered_area_time = 0.0
    local_loss = 0.0
    rows = []
    for row in x.intervals:
        duration = row.end_time_s - row.start_time_s
        contribution = row.calibrated_local_loss_rate_m_s * duration
        elapsed += duration
        covered_area_time += x.assessed_surface_area_m2 * row.deposit_coverage_fraction * duration
        local_loss += contribution
        rows.append(
            {
                "interval_id": row.interval_id,
                "duration_s": duration,
                "deposit_coverage_fraction": row.deposit_coverage_fraction,
                "covered_area_m2": x.assessed_surface_area_m2 * row.deposit_coverage_fraction,
                "local_loss_contribution_m": contribution,
                "rate_provider_state_digest": row.rate_provider_state_digest,
            }
        )
    return Calculation(
        values={
            "assessment_id": x.assessment_id,
            "support_id": support.support_id,
            "elapsed_exposure_s": elapsed,
            "deposit_covered_area_time_m2_s": covered_area_time,
            "cumulative_calibrated_local_loss_m": local_loss,
            "maximum_deposit_coverage_fraction": max(row.deposit_coverage_fraction for row in x.intervals),
            "interval_contributions": rows,
        },
        notes=(
            "Local-loss rates are external calibrated inputs; the model performs exact interval accounting only.",
            "Deposit coverage and cumulative local loss do not identify mechanism synergy, geometry evolution, remaining life, failure probability or acceptance.",
        ),
    )


def under_deposit_local_environment_review(
    x: UnderDepositLocalEnvironmentInput,
) -> Calculation:
    """Evaluate caller-defined deposit-environment criteria without inferring a loss rate."""
    assessment = x.history
    if assessment.domain != "under_deposit":
        return Calculation(
            status="needs_data",
            values={"assessment_id": assessment.assessment_id, "provided_domain": assessment.domain},
            notes=("Under-deposit review requires a local-environment history declared for that domain.",),
        )
    report = assess_local_environment_history(assessment)
    return Calculation(
        status="computed" if report.decision in {"accept", "reject"} else "needs_data",
        values={
            "assessment_id": report.assessment_id,
            "decision": report.decision,
            "findings": [row.model_dump(mode="json") for row in report.findings],
            "total_exposure_time_s": report.total_exposure_time_s,
            "complete_evidence_time_s": report.complete_evidence_time_s,
            "complete_evidence_fraction": report.complete_evidence_fraction,
            "input_digest": report.input_digest,
            "report_digest": report.report_digest,
            "calibrated_loss_integrated": False,
            "corrosion_rate_inferred": False,
            "failure_probability_inferred": False,
        },
        notes=(
            "The result compares measured local-environment facts with caller-defined bounds only.",
            "A caller-rule outcome is not a corrosion mechanism diagnosis, loss rate, lifetime, risk or acceptance decision.",
        ),
    )


class UnderDepositLocalEnvironmentInput(Contract):
    history: LocalEnvironmentHistoryAssessment

    @property
    def asset_id(self):
        return self.history.asset_id

    @property
    def location_id(self):
        return self.history.location_id


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("under-deposit asset and location must match the run context")

    return [
        ModelSpec(
            "degradation.under_deposit_local_environment_review",
            UnderDepositLocalEnvironmentInput,
            under_deposit_local_environment_review,
            {
                "assessment_id": "1",
                "decision": "1",
                "findings": "mixed",
                "total_exposure_time_s": "s",
                "complete_evidence_time_s": "s",
                "complete_evidence_fraction": "1",
                "input_digest": "1",
                "report_digest": "1",
                "calibrated_loss_integrated": "1",
                "corrosion_rate_inferred": "1",
                "failure_probability_inferred": "1",
            },
            (
                "Local-environment observations and caller criteria are reviewed and identity-linked.",
                "This model delegates to the shared local-environment evaluator and produces no damage-rate calculation.",
            ),
            ("caller_under_deposit_environment_criteria_comparison",),
        ),
        ModelSpec(
            "degradation.under_deposit_calibrated_loss",
            UnderDepositExposureHistory,
            under_deposit_exposure_history,
            {
                "assessment_id": "1",
                "support_id": "1",
                "elapsed_exposure_s": "s",
                "deposit_covered_area_time_m2_s": "m^2*s",
                "cumulative_calibrated_local_loss_m": "m",
                "maximum_deposit_coverage_fraction": "1",
                "interval_contributions": "mixed",
            },
            (
                "Each interval has a reviewed deposit state and an external calibrated local-loss rate within one provider support.",
                "Rates are constant over their explicit intervals and are not generated from deposit observations.",
            ),
            ("external_under_deposit_local_loss_accounting",),
            context_validator=same_identity,
        ),
    ]

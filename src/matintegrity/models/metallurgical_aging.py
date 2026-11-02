"""Caller-calibrated equivalent thermal-aging exposure accounting."""

from __future__ import annotations

import math
from fractions import Fraction as Rational

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class AgingExposureInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    temperature_K: Positive | None = None
    equivalent_time_rate_multiplier: Nonnegative | None = None
    multiplier_provider_id: str | None = None
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("aging intervals must have positive duration")
        values = (
            self.temperature_K,
            self.equivalent_time_rate_multiplier,
            self.multiplier_provider_id,
        )
        if self.record_valid and any(value is None for value in values):
            raise ValueError("a valid aging interval requires temperature, multiplier and provider")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid aging interval requires a basis")
        return self


class DeclaredAgingExposureEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    aging_mechanism_id: str = Field(min_length=1)
    reference_temperature_K: Positive
    multiplier_provider_id: str = Field(min_length=1)
    minimum_supported_temperature_K: Positive
    maximum_supported_temperature_K: Positive
    maximum_equivalent_exposure_s: Positive
    applicability_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_temperature(self):
        if self.maximum_supported_temperature_K < self.minimum_supported_temperature_K:
            raise ValueError("aging temperature support must be ordered")
        if not (
            self.minimum_supported_temperature_K
            <= self.reference_temperature_K
            <= self.maximum_supported_temperature_K
        ):
            raise ValueError("reference temperature must lie inside the declared support")
        return self


class MetallurgicalAgingExposure(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    aging_mechanism_id: str = Field(min_length=1)
    intervals: tuple[AgingExposureInterval, ...] = Field(min_length=1)
    exposure_envelope: DeclaredAgingExposureEnvelope
    material_and_mechanism_reviewed: bool
    clock_and_temperature_history_reviewed: bool
    multiplier_provider_reviewed: bool
    interval_completeness_reviewed: bool
    envelope_authority_reviewed: bool

    @model_validator(mode="after")
    def ordered_intervals(self):
        identifiers = [row.interval_id for row in self.intervals]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("aging interval identifiers must be unique")
        for first, second in zip(self.intervals, self.intervals[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("aging intervals must be ordered and cannot overlap")
        return self


def metallurgical_aging_exposure(x: MetallurgicalAgingExposure) -> Calculation:
    identity = dict(
        assessment_id=x.assessment_id,
        clock_id=x.clock_id,
        material_condition_id=x.material_condition_id,
        aging_mechanism_id=x.aging_mechanism_id,
    )
    gaps = [
        [left.end_time_s, right.start_time_s]
        for left, right in zip(x.intervals, x.intervals[1:], strict=False)
        if right.start_time_s > left.end_time_s
    ]
    coverage = dict(
        history_span_s=x.intervals[-1].end_time_s - x.intervals[0].start_time_s,
        uncovered_duration_s=sum(end - start for start, end in gaps),
        uncovered_intervals_s=gaps,
    )
    missing_reviews = [
        name
        for name in (
            "material_and_mechanism_reviewed",
            "clock_and_temperature_history_reviewed",
            "multiplier_provider_reviewed",
            "interval_completeness_reviewed",
            "envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    envelope = x.exposure_envelope
    identity_matches = (
        x.material_condition_id == envelope.material_condition_id
        and x.aging_mechanism_id == envelope.aging_mechanism_id
    )
    invalid = [row.interval_id for row in x.intervals if not row.record_valid]
    provider_mismatch = [
        row.interval_id
        for row in x.intervals
        if row.record_valid and row.multiplier_provider_id != envelope.multiplier_provider_id
    ]
    if missing_reviews or not identity_matches or invalid or provider_mismatch or gaps:
        return Calculation(
            status="needs_data",
            values={
                **identity,
                **coverage,
                "invalid_interval_ids": invalid,
                "provider_mismatch_interval_ids": provider_mismatch,
                "material_and_mechanism_identity_match": identity_matches,
                "missing_reviews": missing_reviews,
            },
            notes=(
                "Reviewed identity, complete intervals and one qualified multiplier provider are required. Unobserved internal spans are not assigned zero exposure.",
            ),
        )

    outside_support = [
        row.interval_id
        for row in x.intervals
        if not (
            envelope.minimum_supported_temperature_K
            <= row.temperature_K
            <= envelope.maximum_supported_temperature_K
        )
    ]
    if outside_support:
        return Calculation(
            status="out_of_scope",
            values={
                **identity,
                **coverage,
                "outside_temperature_support_interval_ids": outside_support,
                "missing_reviews": [],
            },
            notes=("At least one reviewed temperature is outside the multiplier provider support.",),
        )

    def represent(exact):
        value = float(exact)
        if not math.isfinite(value) or (exact and value == 0):
            raise ArithmeticError("nonzero equivalent exposure is not representable")
        return value

    rows = []
    equivalent_exact = Rational(0)
    elapsed_exact = Rational(0)
    try:
        for row in x.intervals:
            duration_exact = Rational(row.end_time_s) - Rational(row.start_time_s)
            contribution_exact = duration_exact * Rational(row.equivalent_time_rate_multiplier)
            elapsed_exact += duration_exact
            equivalent_exact += contribution_exact
            rows.append(
                {
                    "interval_id": row.interval_id,
                    "duration_s": represent(duration_exact),
                    "temperature_K": row.temperature_K,
                    "equivalent_time_rate_multiplier": row.equivalent_time_rate_multiplier,
                    "equivalent_exposure_contribution_s": represent(contribution_exact),
                }
            )
        remaining_exact = Rational(envelope.maximum_equivalent_exposure_s) - equivalent_exact
        elapsed_exposure = represent(elapsed_exact)
        equivalent_exposure = represent(equivalent_exact)
        remaining = represent(remaining_exact)
    except ArithmeticError:
        return Calculation(
            status="out_of_scope",
            values={
                **identity,
                **coverage,
                "reason": "equivalent exposure exceeds finite arithmetic support",
            },
        )
    return Calculation(
        values={
            **identity,
            **coverage,
            "envelope_id": envelope.envelope_id,
            "reference_temperature_K": envelope.reference_temperature_K,
            "elapsed_exposure_s": elapsed_exposure,
            "equivalent_exposure_s": equivalent_exposure,
            "maximum_equivalent_exposure_s": envelope.maximum_equivalent_exposure_s,
            "remaining_equivalent_exposure_s": remaining,
            "within_declared_equivalent_exposure": remaining_exact >= 0,
            "interval_contributions": rows,
        },
        notes=(
            "Equivalent-time multipliers and the exposure limit are caller-owned calibrated inputs, not a bundled aging law.",
            "Equivalent exposure does not predict phase fraction, embrittlement, strength, toughness, remaining life or acceptance.",
            "The assessed history spans the first supplied start through the last supplied end; no earlier or later asset history is inferred.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("aging-exposure asset and location must match the run context")

    return [
        ModelSpec(
            "degradation.metallurgical_aging_exposure",
            MetallurgicalAgingExposure,
            metallurgical_aging_exposure,
            {
                "assessment_id": "1",
                "clock_id": "1",
                "material_condition_id": "1",
                "aging_mechanism_id": "1",
                "history_span_s": "s",
                "uncovered_duration_s": "s",
                "uncovered_intervals_s": "s",
                "envelope_id": "1",
                "reference_temperature_K": "K",
                "elapsed_exposure_s": "s",
                "equivalent_exposure_s": "s",
                "maximum_equivalent_exposure_s": "s",
                "remaining_equivalent_exposure_s": "s",
                "within_declared_equivalent_exposure": "1",
                "interval_contributions": "mixed",
            },
            (
                "Each interval uses a caller-calibrated equivalent-time rate multiplier at a reviewed temperature.",
                "One exact material condition, aging mechanism and multiplier provider apply to the full history.",
            ),
            ("declared_metallurgical_aging_equivalent_exposure",),
            version="1.0.2",
            context_validator=same_identity,
        )
    ]

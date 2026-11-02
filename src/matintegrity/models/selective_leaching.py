"""Selective-leaching observations and caller-qualified applicability support."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class SelectiveLeachingTestEvidence(Contract):
    test_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    test_method_id: str = Field(min_length=1)
    reported_endpoint: str = Field(min_length=1)
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_record(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("invalid selective-leaching test evidence requires a basis")
        return self


class SelectiveLeachingQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    alloy_ids: list[str] = Field(min_length=1)
    composition_condition_ids: list[str] = Field(min_length=1)
    phase_condition_ids: list[str] = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_pH: float
    maximum_pH: float
    redox_or_potential_descriptor_id: str = Field(min_length=1)
    potential_basis: str | None = None
    potential_unit: str | None = None
    minimum_potential: float | None = None
    maximum_potential: float | None = None
    maximum_exposure_duration_s: Positive
    test_evidence_ids: list[str] = Field(min_length=1)
    applicability_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        for lower, upper, name in (
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (self.minimum_pH, self.maximum_pH, "pH"),
        ):
            if upper < lower:
                raise ValueError(f"{name} support must be ordered")
        potential_fields = (
            self.potential_basis,
            self.potential_unit,
            self.minimum_potential,
            self.maximum_potential,
        )
        if any(value is not None for value in potential_fields) and any(
            value is None for value in potential_fields
        ):
            raise ValueError("quantitative potential support requires basis, unit and both bounds")
        if self.minimum_potential is not None and self.maximum_potential < self.minimum_potential:
            raise ValueError("potential support must be ordered")
        for values, name in (
            (self.alloy_ids, "alloy"),
            (self.composition_condition_ids, "composition condition"),
            (self.phase_condition_ids, "phase condition"),
            (self.test_evidence_ids, "test evidence"),
        ):
            if len(set(values)) != len(values) or any(not value.strip() for value in values):
                raise ValueError(f"{name} IDs must be unique and nonblank")
        return self


class SelectiveLeachingExposure(Contract):
    interval_id: str = Field(min_length=1)
    envelope_id: str | None = None
    start_time_s: Nonnegative
    end_time_s: Positive
    environment_id: str = Field(min_length=1)
    temperature_K: Positive | None = None
    pH: float | None = None
    redox_or_potential_descriptor_id: str = Field(min_length=1)
    potential_basis: str | None = None
    potential_unit: str | None = None
    potential_value: float | None = None
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("selective-leaching exposure interval must have positive duration")
        if self.record_valid and (self.temperature_K is None or self.pH is None):
            raise ValueError("a valid exposure requires temperature and pH")
        potential_fields = (self.potential_basis, self.potential_unit, self.potential_value)
        if any(value is not None for value in potential_fields) and any(
            value is None for value in potential_fields
        ):
            raise ValueError("quantitative exposure potential requires basis, unit and value")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid selective-leaching exposure requires a basis")
        return self


class SelectiveLeachingObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_region_id: str = Field(min_length=1)
    observation_kind: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    reported_value: float | None = None
    expanded_uncertainty: Nonnegative | None = None
    unit: str = Field(min_length=1)
    caller_range_id: str | None = None
    reported_description: str = Field(min_length=1)
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_observation(self):
        if self.record_valid and (self.reported_value is None or self.expanded_uncertainty is None):
            raise ValueError("a valid selective-leaching observation requires value and uncertainty")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid selective-leaching observation requires a basis")
        return self


class CallerObservationRange(Contract):
    range_id: str = Field(min_length=1)
    observation_kind: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    minimum_value: float | None = None
    maximum_value: float | None = None
    range_basis: str = Field(min_length=1)
    caller_disposition_id_if_outside: str = Field(min_length=1)

    @model_validator(mode="after")
    def bounded_range(self):
        if self.minimum_value is None and self.maximum_value is None:
            raise ValueError("a caller observation range requires at least one bound")
        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.maximum_value < self.minimum_value
        ):
            raise ValueError("caller observation range bounds must be ordered")
        return self


class SelectiveLeachingApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    alloy_id: str = Field(min_length=1)
    composition_condition_id: str = Field(min_length=1)
    phase_condition_id: str = Field(min_length=1)
    qualification_tests: list[SelectiveLeachingTestEvidence] = Field(min_length=1)
    qualification_envelopes: list[SelectiveLeachingQualificationEnvelope] = Field(min_length=1)
    exposure_intervals: list[SelectiveLeachingExposure] = Field(min_length=1)
    observations: list[SelectiveLeachingObservation] = Field(default_factory=list)
    caller_observation_ranges: list[CallerObservationRange] = Field(default_factory=list)
    alloy_composition_and_phase_reviewed: bool
    environment_temperature_and_pH_reviewed: bool
    redox_or_potential_basis_reviewed: bool
    exposure_clock_reviewed: bool
    microscopy_and_composition_observations_reviewed: bool
    measurement_units_and_uncertainty_reviewed: bool
    qualification_tests_envelopes_and_ranges_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_records(self):
        collections = (
            ([row.test_id for row in self.qualification_tests], "test"),
            ([row.envelope_id for row in self.qualification_envelopes], "envelope"),
            ([row.interval_id for row in self.exposure_intervals], "exposure interval"),
            ([row.observation_id for row in self.observations], "observation"),
            ([row.range_id for row in self.caller_observation_ranges], "observation range"),
        )
        for values, name in collections:
            if len(set(values)) != len(values):
                raise ValueError(f"selective-leaching {name} IDs must be unique")
        known_tests = {row.test_id for row in self.qualification_tests}
        for envelope in self.qualification_envelopes:
            if set(envelope.test_evidence_ids) - known_tests:
                raise ValueError("qualification envelopes must reference declared tests")
        previous_end = None
        for interval in self.exposure_intervals:
            if previous_end is not None and interval.start_time_s < previous_end:
                raise ValueError("exposure intervals must be ordered and cannot overlap")
            previous_end = interval.end_time_s
        return self


def selective_leaching_applicability(x: SelectiveLeachingApplicability) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "alloy_composition_and_phase_reviewed",
            "environment_temperature_and_pH_reviewed",
            "redox_or_potential_basis_reviewed",
            "exposure_clock_reviewed",
            "microscopy_and_composition_observations_reviewed",
            "measurement_units_and_uncertainty_reviewed",
            "qualification_tests_envelopes_and_ranges_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_tests = [row.test_id for row in x.qualification_tests if not row.record_valid]
    invalid_exposures = [row.interval_id for row in x.exposure_intervals if not row.record_valid]
    invalid_observations = [row.observation_id for row in x.observations if not row.record_valid]
    envelopes = {row.envelope_id: row for row in x.qualification_envelopes}
    unmatched_exposures = []
    potential_basis_mismatch = []
    potential_unit_mismatch = []
    missing_potential = []
    outside_exposures = []
    exposure_comparisons = []

    for interval in x.exposure_intervals:
        if not interval.record_valid:
            continue
        envelope = envelopes.get(interval.envelope_id)
        if envelope is None:
            unmatched_exposures.append(interval.interval_id)
            continue
        if envelope.minimum_potential is not None:
            if interval.potential_value is None:
                missing_potential.append(interval.interval_id)
                continue
            if interval.potential_basis != envelope.potential_basis:
                potential_basis_mismatch.append(interval.interval_id)
                continue
            if interval.potential_unit != envelope.potential_unit:
                potential_unit_mismatch.append(interval.interval_id)
                continue

        reasons = []
        if x.alloy_id not in envelope.alloy_ids:
            reasons.append("alloy")
        if x.composition_condition_id not in envelope.composition_condition_ids:
            reasons.append("composition_condition")
        if x.phase_condition_id not in envelope.phase_condition_ids:
            reasons.append("phase_condition")
        if interval.environment_id != envelope.environment_id:
            reasons.append("environment")
        if not envelope.minimum_temperature_K <= interval.temperature_K <= envelope.maximum_temperature_K:
            reasons.append("temperature")
        if not envelope.minimum_pH <= interval.pH <= envelope.maximum_pH:
            reasons.append("pH")
        if interval.redox_or_potential_descriptor_id != envelope.redox_or_potential_descriptor_id:
            reasons.append("redox_or_potential_descriptor")
        if envelope.minimum_potential is not None and not (
            envelope.minimum_potential <= interval.potential_value <= envelope.maximum_potential
        ):
            reasons.append("potential")
        duration = interval.end_time_s - interval.start_time_s
        if duration > envelope.maximum_exposure_duration_s:
            reasons.append("exposure_duration")
        if reasons:
            outside_exposures.append(interval.interval_id)
        exposure_comparisons.append(
            {
                "interval_id": interval.interval_id,
                "envelope_id": envelope.envelope_id,
                "exposure_duration_s": duration,
                "inside_declared_qualification_support": not reasons,
                "outside_support_reasons": reasons,
                "test_evidence_ids": envelope.test_evidence_ids,
            }
        )

    ranges = {row.range_id: row for row in x.caller_observation_ranges}
    unmatched_observations = []
    observation_definition_mismatch = []
    observation_unit_mismatch = []
    observation_comparisons = []
    for observation in x.observations:
        if not observation.record_valid:
            continue
        candidate = ranges.get(observation.caller_range_id)
        if candidate is None:
            unmatched_observations.append(observation.observation_id)
            continue
        if (
            observation.observation_kind,
            observation.method_id,
            observation.metric_definition,
        ) != (candidate.observation_kind, candidate.method_id, candidate.metric_definition):
            observation_definition_mismatch.append(observation.observation_id)
            continue
        if observation.unit != candidate.unit:
            observation_unit_mismatch.append(observation.observation_id)
            continue
        low = observation.reported_value - observation.expanded_uncertainty
        high = observation.reported_value + observation.expanded_uncertainty
        observation_comparisons.append(
            {
                "observation_id": observation.observation_id,
                "range_id": candidate.range_id,
                "reported_value": observation.reported_value,
                "expanded_uncertainty": observation.expanded_uncertainty,
                "uncertainty_interval_minimum": low,
                "uncertainty_interval_maximum": high,
                "unit": observation.unit,
                "nominal_below_declared_minimum": candidate.minimum_value is not None
                and observation.reported_value < candidate.minimum_value,
                "nominal_above_declared_maximum": candidate.maximum_value is not None
                and observation.reported_value > candidate.maximum_value,
                "uncertainty_interval_extends_below_declared_minimum": candidate.minimum_value is not None
                and low < candidate.minimum_value,
                "uncertainty_interval_extends_above_declared_maximum": candidate.maximum_value is not None
                and high > candidate.maximum_value,
                "caller_disposition_id_if_outside": candidate.caller_disposition_id_if_outside,
            }
        )

    incomplete = (
        missing_reviews
        or invalid_tests
        or invalid_exposures
        or invalid_observations
        or unmatched_exposures
        or potential_basis_mismatch
        or potential_unit_mismatch
        or missing_potential
        or unmatched_observations
        or observation_definition_mismatch
        or observation_unit_mismatch
    )
    status = "needs_data" if incomplete else "out_of_scope" if outside_exposures else "computed"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "alloy_id": x.alloy_id,
            "composition_condition_id": x.composition_condition_id,
            "phase_condition_id": x.phase_condition_id,
            "invalid_qualification_test_ids": invalid_tests,
            "invalid_exposure_interval_ids": invalid_exposures,
            "unmatched_envelope_interval_ids": unmatched_exposures,
            "potential_basis_mismatch_interval_ids": potential_basis_mismatch,
            "potential_unit_mismatch_interval_ids": potential_unit_mismatch,
            "missing_quantitative_potential_interval_ids": missing_potential,
            "outside_qualification_support_interval_ids": outside_exposures,
            "qualification_support_comparisons": exposure_comparisons,
            "observation_count": len(x.observations),
            "invalid_observation_ids": invalid_observations,
            "unmatched_observation_range_ids": unmatched_observations,
            "observation_definition_mismatch_ids": observation_definition_mismatch,
            "observation_unit_mismatch_ids": observation_unit_mismatch,
            "caller_observation_range_comparisons": observation_comparisons,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Qualification envelopes, observation ranges and disposition IDs are caller-owned evidence declarations, not bundled acceptance criteria.",
            "Microscopy and composition uncertainty intervals are retained without conversion to dealloyed-depth growth or residual strength.",
            "Inside-support and range-comparison results do not predict fracture, remaining life, failure probability or acceptability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("selective-leaching asset and location must match the assessment context")

    return [
        ModelSpec(
            "degradation.selective_leaching_applicability",
            SelectiveLeachingApplicability,
            selective_leaching_applicability,
            {"observation_count": "count"},
            (
                "Alloy, composition, phase, environment, temperature, pH, electrochemical descriptor and exposure duration are compared only with caller-qualified support.",
                "Microscopy and composition observations compare only with exactly matching caller ranges while retaining supplied uncertainty.",
            ),
            ("selective_leaching_observation_envelope_accounting",),
            context_validator=same_identity,
        )
    ]

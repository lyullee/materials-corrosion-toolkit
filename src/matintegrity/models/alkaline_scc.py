"""Caller-qualified alkaline-SCC applicability without initiation or growth prediction."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class AlkalineSCCTestEvidence(Contract):
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
            raise ValueError("invalid alkaline-SCC test evidence requires an invalid-record basis")
        return self


class AlkalineSCCQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_ids: list[str] = Field(min_length=1)
    heat_treatment_condition_ids: list[str] = Field(min_length=1)
    alkaline_species_id: str = Field(min_length=1)
    concentration_unit: str = Field(min_length=1)
    minimum_concentration: Nonnegative
    maximum_concentration: Nonnegative
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    electrochemical_descriptor_id: str = Field(min_length=1)
    potential_reference_id: str | None = None
    minimum_potential_V: float | None = None
    maximum_potential_V: float | None = None
    applied_stress_definition: str = Field(min_length=1)
    minimum_applied_stress_Pa: float
    maximum_applied_stress_Pa: float
    residual_stress_definition: str = Field(min_length=1)
    minimum_residual_stress_Pa: float
    maximum_residual_stress_Pa: float
    maximum_exposure_duration_s: Positive
    test_evidence_ids: list[str] = Field(min_length=1)
    applicability_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        ranges = (
            (self.minimum_concentration, self.maximum_concentration, "concentration"),
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (self.minimum_applied_stress_Pa, self.maximum_applied_stress_Pa, "applied stress"),
            (self.minimum_residual_stress_Pa, self.maximum_residual_stress_Pa, "residual stress"),
        )
        for lower, upper, name in ranges:
            if upper < lower:
                raise ValueError(f"{name} support must be ordered")
        if (self.minimum_potential_V is None) != (self.maximum_potential_V is None):
            raise ValueError("potential support requires both minimum and maximum or neither")
        if self.minimum_potential_V is not None and self.maximum_potential_V < self.minimum_potential_V:
            raise ValueError("potential support must be ordered")
        for values, name in (
            (self.material_condition_ids, "material condition"),
            (self.heat_treatment_condition_ids, "heat-treatment condition"),
            (self.test_evidence_ids, "test evidence"),
        ):
            if len(set(values)) != len(values) or any(not value.strip() for value in values):
                raise ValueError(f"{name} IDs must be unique and nonblank")
        if self.minimum_potential_V is not None and not self.potential_reference_id:
            raise ValueError("numeric potential support requires a potential reference")
        return self


class AlkalineExposureInterval(Contract):
    interval_id: str = Field(min_length=1)
    envelope_id: str | None = None
    start_time_s: Nonnegative
    end_time_s: Positive
    alkaline_species_id: str = Field(min_length=1)
    concentration: Nonnegative | None = None
    concentration_unit: str = Field(min_length=1)
    temperature_K: Positive | None = None
    electrochemical_descriptor_id: str = Field(min_length=1)
    potential_reference_id: str | None = None
    potential_V: float | None = None
    applied_stress_definition: str = Field(min_length=1)
    applied_stress_Pa: float | None = None
    residual_stress_definition: str = Field(min_length=1)
    residual_stress_Pa: float | None = None
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("alkaline exposure interval must have positive duration")
        required = (
            self.concentration,
            self.temperature_K,
            self.applied_stress_Pa,
            self.residual_stress_Pa,
        )
        if self.record_valid and any(value is None for value in required):
            raise ValueError("a valid alkaline exposure requires chemistry, temperature and stresses")
        if self.potential_V is not None and not self.potential_reference_id:
            raise ValueError("a numeric exposure potential requires a potential reference")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid alkaline exposure requires an invalid-record basis")
        return self


class AlkalineSCCApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    heat_treatment_condition_id: str = Field(min_length=1)
    qualification_tests: list[AlkalineSCCTestEvidence] = Field(min_length=1)
    qualification_envelopes: list[AlkalineSCCQualificationEnvelope] = Field(min_length=1)
    exposure_intervals: list[AlkalineExposureInterval] = Field(min_length=1)
    material_and_heat_treatment_reviewed: bool
    alkaline_chemistry_and_units_reviewed: bool
    temperature_history_reviewed: bool
    electrochemical_descriptor_reviewed: bool
    applied_and_residual_stress_reviewed: bool
    exposure_clock_reviewed: bool
    qualification_tests_and_envelopes_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_records(self):
        test_ids = [row.test_id for row in self.qualification_tests]
        envelope_ids = [row.envelope_id for row in self.qualification_envelopes]
        interval_ids = [row.interval_id for row in self.exposure_intervals]
        for values, name in (
            (test_ids, "qualification test"),
            (envelope_ids, "qualification envelope"),
            (interval_ids, "exposure interval"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"{name} IDs must be unique")
        known_tests = set(test_ids)
        for envelope in self.qualification_envelopes:
            if set(envelope.test_evidence_ids) - known_tests:
                raise ValueError("qualification envelopes must reference declared test evidence")
        previous_end = None
        for interval in self.exposure_intervals:
            if previous_end is not None and interval.start_time_s < previous_end:
                raise ValueError("alkaline exposure intervals must be ordered and cannot overlap")
            previous_end = interval.end_time_s
        return self


def alkaline_scc_applicability(x: AlkalineSCCApplicability) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_and_heat_treatment_reviewed",
            "alkaline_chemistry_and_units_reviewed",
            "temperature_history_reviewed",
            "electrochemical_descriptor_reviewed",
            "applied_and_residual_stress_reviewed",
            "exposure_clock_reviewed",
            "qualification_tests_and_envelopes_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_tests = [row.test_id for row in x.qualification_tests if not row.record_valid]
    invalid_intervals = [row.interval_id for row in x.exposure_intervals if not row.record_valid]
    envelopes = {row.envelope_id: row for row in x.qualification_envelopes}
    unmatched_intervals = []
    unit_mismatch_intervals = []
    missing_potential_intervals = []
    comparisons = []
    outside_interval_ids = []

    for interval in x.exposure_intervals:
        if not interval.record_valid:
            continue
        envelope = envelopes.get(interval.envelope_id)
        if envelope is None:
            unmatched_intervals.append(interval.interval_id)
            continue
        if interval.concentration_unit != envelope.concentration_unit:
            unit_mismatch_intervals.append(interval.interval_id)
            continue
        if envelope.minimum_potential_V is not None and interval.potential_V is None:
            missing_potential_intervals.append(interval.interval_id)
            continue

        outside_reasons = []
        if x.material_condition_id not in envelope.material_condition_ids:
            outside_reasons.append("material_condition")
        if x.heat_treatment_condition_id not in envelope.heat_treatment_condition_ids:
            outside_reasons.append("heat_treatment_condition")
        if interval.alkaline_species_id != envelope.alkaline_species_id:
            outside_reasons.append("alkaline_species")
        if not envelope.minimum_concentration <= interval.concentration <= envelope.maximum_concentration:
            outside_reasons.append("concentration")
        if not envelope.minimum_temperature_K <= interval.temperature_K <= envelope.maximum_temperature_K:
            outside_reasons.append("temperature")
        if interval.electrochemical_descriptor_id != envelope.electrochemical_descriptor_id:
            outside_reasons.append("electrochemical_descriptor")
        if envelope.minimum_potential_V is not None:
            if interval.potential_reference_id != envelope.potential_reference_id:
                outside_reasons.append("potential_reference")
            elif not envelope.minimum_potential_V <= interval.potential_V <= envelope.maximum_potential_V:
                outside_reasons.append("potential")
        if interval.applied_stress_definition != envelope.applied_stress_definition:
            outside_reasons.append("applied_stress_definition")
        elif not (
            envelope.minimum_applied_stress_Pa
            <= interval.applied_stress_Pa
            <= envelope.maximum_applied_stress_Pa
        ):
            outside_reasons.append("applied_stress")
        if interval.residual_stress_definition != envelope.residual_stress_definition:
            outside_reasons.append("residual_stress_definition")
        elif not (
            envelope.minimum_residual_stress_Pa
            <= interval.residual_stress_Pa
            <= envelope.maximum_residual_stress_Pa
        ):
            outside_reasons.append("residual_stress")
        duration = interval.end_time_s - interval.start_time_s
        if duration > envelope.maximum_exposure_duration_s:
            outside_reasons.append("exposure_duration")
        if outside_reasons:
            outside_interval_ids.append(interval.interval_id)
        comparisons.append(
            {
                "interval_id": interval.interval_id,
                "envelope_id": envelope.envelope_id,
                "exposure_duration_s": duration,
                "inside_declared_qualification_support": not outside_reasons,
                "outside_support_reasons": outside_reasons,
                "test_evidence_ids": envelope.test_evidence_ids,
            }
        )

    incomplete = (
        missing_reviews
        or invalid_tests
        or invalid_intervals
        or unmatched_intervals
        or unit_mismatch_intervals
        or missing_potential_intervals
    )
    status = "needs_data" if incomplete else "out_of_scope" if outside_interval_ids else "computed"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "material_condition_id": x.material_condition_id,
            "heat_treatment_condition_id": x.heat_treatment_condition_id,
            "qualification_test_count": len(x.qualification_tests),
            "invalid_qualification_test_ids": invalid_tests,
            "qualification_envelope_count": len(x.qualification_envelopes),
            "exposure_interval_count": len(x.exposure_intervals),
            "invalid_exposure_interval_ids": invalid_intervals,
            "unmatched_envelope_interval_ids": unmatched_intervals,
            "concentration_unit_mismatch_interval_ids": unit_mismatch_intervals,
            "missing_numeric_potential_interval_ids": missing_potential_intervals,
            "outside_qualification_support_interval_ids": outside_interval_ids,
            "qualification_support_comparisons": comparisons,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Qualification envelopes and test links are caller-owned support declarations, not bundled alkaline-SCC limits or acceptance criteria.",
            "Inside-support status does not predict crack initiation, threshold, growth rate, life or failure probability.",
            "Concentration units and electrochemical references are compared exactly; no hidden conversion or reference-electrode correction is applied.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("alkaline-SCC asset and location must match the assessment context")

    return [
        ModelSpec(
            "degradation.alkaline_scc_applicability",
            AlkalineSCCApplicability,
            alkaline_scc_applicability,
            {
                "qualification_test_count": "count",
                "qualification_envelope_count": "count",
                "exposure_interval_count": "count",
            },
            (
                "Material, heat treatment, alkaline chemistry, temperature, electrochemical descriptor, stresses and duration are checked only against caller-qualified evidence envelopes.",
                "Invalid or unmatched evidence needs data; valid exposure outside an otherwise complete declared envelope remains outside model scope.",
            ),
            ("alkaline_scc_qualification_envelope_accounting",),
            context_validator=same_identity,
        )
    ]

"""Nitriding exposure applicability without profile, kinetics or property prediction."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class NitridingTestEvidence(Contract):
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
            raise ValueError("invalid nitriding test evidence requires an invalid-record basis")
        return self


class NitridingQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_ids: list[str] = Field(min_length=1)
    material_condition_ids: list[str] = Field(min_length=1)
    nitrogen_species_id: str = Field(min_length=1)
    nitrogen_driving_force_basis: str = Field(min_length=1)
    nitrogen_driving_force_unit: str = Field(min_length=1)
    minimum_nitrogen_driving_force: Nonnegative
    maximum_nitrogen_driving_force: Nonnegative
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_pressure_Pa_abs: Positive
    maximum_pressure_Pa_abs: Positive
    gas_environment_descriptor_id: str = Field(min_length=1)
    maximum_exposure_duration_s: Positive
    test_evidence_ids: list[str] = Field(min_length=1)
    applicability_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        for lower, upper, name in (
            (
                self.minimum_nitrogen_driving_force,
                self.maximum_nitrogen_driving_force,
                "nitrogen driving force",
            ),
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (self.minimum_pressure_Pa_abs, self.maximum_pressure_Pa_abs, "absolute pressure"),
        ):
            if upper < lower:
                raise ValueError(f"{name} support must be ordered")
        for values, name in (
            (self.material_ids, "material"),
            (self.material_condition_ids, "material condition"),
            (self.test_evidence_ids, "test evidence"),
        ):
            if len(set(values)) != len(values) or any(not value.strip() for value in values):
                raise ValueError(f"{name} IDs must be unique and nonblank")
        return self


class NitridingExposureInterval(Contract):
    interval_id: str = Field(min_length=1)
    envelope_id: str | None = None
    start_time_s: Nonnegative
    end_time_s: Positive
    nitrogen_species_id: str = Field(min_length=1)
    nitrogen_driving_force_basis: str = Field(min_length=1)
    nitrogen_driving_force_unit: str = Field(min_length=1)
    nitrogen_driving_force: Nonnegative | None = None
    temperature_K: Positive | None = None
    pressure_Pa_abs: Positive | None = None
    gas_environment_descriptor_id: str = Field(min_length=1)
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("nitriding exposure interval must have positive duration")
        if self.record_valid and any(
            value is None
            for value in (
                self.nitrogen_driving_force,
                self.temperature_K,
                self.pressure_Pa_abs,
            )
        ):
            raise ValueError("a valid nitriding exposure requires driving force, temperature and pressure")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid nitriding exposure requires an invalid-record basis")
        return self


class NitridingApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    qualification_tests: list[NitridingTestEvidence] = Field(min_length=1)
    qualification_envelopes: list[NitridingQualificationEnvelope] = Field(min_length=1)
    exposure_intervals: list[NitridingExposureInterval] = Field(min_length=1)
    material_and_condition_reviewed: bool
    nitrogen_species_basis_and_unit_reviewed: bool
    temperature_history_reviewed: bool
    absolute_pressure_reviewed: bool
    gas_environment_descriptor_reviewed: bool
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
                raise ValueError("nitriding envelopes must reference declared test evidence")
        previous_end = None
        for interval in self.exposure_intervals:
            if previous_end is not None and interval.start_time_s < previous_end:
                raise ValueError("nitriding exposure intervals must be ordered and cannot overlap")
            previous_end = interval.end_time_s
        return self


def nitriding_applicability(x: NitridingApplicability) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_and_condition_reviewed",
            "nitrogen_species_basis_and_unit_reviewed",
            "temperature_history_reviewed",
            "absolute_pressure_reviewed",
            "gas_environment_descriptor_reviewed",
            "exposure_clock_reviewed",
            "qualification_tests_and_envelopes_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_tests = [row.test_id for row in x.qualification_tests if not row.record_valid]
    invalid_intervals = [row.interval_id for row in x.exposure_intervals if not row.record_valid]
    envelopes = {row.envelope_id: row for row in x.qualification_envelopes}
    unmatched_intervals = []
    basis_mismatch_intervals = []
    unit_mismatch_intervals = []
    outside_interval_ids = []
    comparisons = []

    for interval in x.exposure_intervals:
        if not interval.record_valid:
            continue
        envelope = envelopes.get(interval.envelope_id)
        if envelope is None:
            unmatched_intervals.append(interval.interval_id)
            continue
        if interval.nitrogen_driving_force_basis != envelope.nitrogen_driving_force_basis:
            basis_mismatch_intervals.append(interval.interval_id)
            continue
        if interval.nitrogen_driving_force_unit != envelope.nitrogen_driving_force_unit:
            unit_mismatch_intervals.append(interval.interval_id)
            continue

        outside_reasons = []
        if x.material_id not in envelope.material_ids:
            outside_reasons.append("material")
        if x.material_condition_id not in envelope.material_condition_ids:
            outside_reasons.append("material_condition")
        if interval.nitrogen_species_id != envelope.nitrogen_species_id:
            outside_reasons.append("nitrogen_species")
        if not (
            envelope.minimum_nitrogen_driving_force
            <= interval.nitrogen_driving_force
            <= envelope.maximum_nitrogen_driving_force
        ):
            outside_reasons.append("nitrogen_driving_force")
        if not envelope.minimum_temperature_K <= interval.temperature_K <= envelope.maximum_temperature_K:
            outside_reasons.append("temperature")
        if (
            not envelope.minimum_pressure_Pa_abs
            <= interval.pressure_Pa_abs
            <= envelope.maximum_pressure_Pa_abs
        ):
            outside_reasons.append("absolute_pressure")
        if interval.gas_environment_descriptor_id != envelope.gas_environment_descriptor_id:
            outside_reasons.append("gas_environment_descriptor")
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
        or basis_mismatch_intervals
        or unit_mismatch_intervals
    )
    status = "needs_data" if incomplete else "out_of_scope" if outside_interval_ids else "computed"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "material_id": x.material_id,
            "material_condition_id": x.material_condition_id,
            "qualification_test_count": len(x.qualification_tests),
            "invalid_qualification_test_ids": invalid_tests,
            "qualification_envelope_count": len(x.qualification_envelopes),
            "exposure_interval_count": len(x.exposure_intervals),
            "invalid_exposure_interval_ids": invalid_intervals,
            "unmatched_envelope_interval_ids": unmatched_intervals,
            "nitrogen_driving_force_basis_mismatch_interval_ids": basis_mismatch_intervals,
            "nitrogen_driving_force_unit_mismatch_interval_ids": unit_mismatch_intervals,
            "outside_qualification_support_interval_ids": outside_interval_ids,
            "qualification_support_comparisons": comparisons,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Qualification envelopes and linked tests are caller-owned evidence support, not bundled nitriding limits or acceptance criteria.",
            "Nitrogen driving-force basis and unit are matched exactly; activity, potential, concentration and partial pressure are not interconverted.",
            "Inside-support status does not predict a nitrogen profile, diffusion or reaction kinetics, nitride phase, property change, life or failure probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("nitriding assessment asset and location must match the assessment context")

    return [
        ModelSpec(
            "degradation.nitriding_applicability",
            NitridingApplicability,
            nitriding_applicability,
            {
                "qualification_test_count": "count",
                "qualification_envelope_count": "count",
                "exposure_interval_count": "count",
            },
            (
                "Material, condition, nitrogen species and driving-force basis, temperature, absolute pressure, gas environment and duration are compared only with caller-qualified evidence envelopes.",
                "Invalid or unmatched evidence needs data; valid exposure outside an otherwise complete declared envelope remains outside model scope.",
            ),
            ("nitriding_qualification_envelope_accounting",),
            context_validator=same_identity,
        )
    ]

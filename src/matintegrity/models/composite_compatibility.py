"""Composite service exposure against a caller-owned qualification envelope."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Nonnegative, Positive
from ..registry import ModelSpec


class CompositeExposure(Contract):
    exposure_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    temperature_K: Positive
    moisture_mass_fraction: Fraction
    pressure_Pa_abs: Positive
    record_valid: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def positive_duration(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("composite exposure interval must have positive duration")
        return self


class CompositeQualificationRecord(Contract):
    record_id: str = Field(min_length=1)
    coupon_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    laminate_system_id: str = Field(min_length=1)
    resin_system_id: str = Field(min_length=1)
    fiber_system_id: str = Field(min_length=1)
    manufacturing_condition_id: str = Field(min_length=1)
    layup_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    record_valid: bool
    supports_declared_envelope: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class CompositeQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    laminate_system_id: str = Field(min_length=1)
    resin_system_id: str = Field(min_length=1)
    fiber_system_id: str = Field(min_length=1)
    manufacturing_condition_id: str = Field(min_length=1)
    layup_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_moisture_mass_fraction: Fraction
    maximum_moisture_mass_fraction: Fraction
    minimum_pressure_Pa_abs: Positive
    maximum_pressure_Pa_abs: Positive
    maximum_cumulative_exposure_s: Positive
    qualification_records: tuple[CompositeQualificationRecord, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_ranges_and_unique_records(self):
        for lower, upper, name in (
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (
                self.minimum_moisture_mass_fraction,
                self.maximum_moisture_mass_fraction,
                "moisture",
            ),
            (self.minimum_pressure_Pa_abs, self.maximum_pressure_Pa_abs, "pressure"),
        ):
            if upper < lower:
                raise ValueError(f"{name} envelope bounds must be ordered")
        identifiers = [record.record_id for record in self.qualification_records]
        coupons = [record.coupon_id for record in self.qualification_records]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("qualification record identifiers must be unique")
        if len(coupons) != len(set(coupons)):
            raise ValueError("qualification coupon identifiers must be unique")
        return self


class CompositeCompatibility(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    laminate_system_id: str = Field(min_length=1)
    resin_system_id: str = Field(min_length=1)
    fiber_system_id: str = Field(min_length=1)
    manufacturing_condition_id: str = Field(min_length=1)
    layup_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    exposures: tuple[CompositeExposure, ...] = Field(min_length=1)
    qualification_envelope: CompositeQualificationEnvelope
    material_and_layup_identity_reviewed: bool
    manufacturing_condition_reviewed: bool
    environment_and_clock_reviewed: bool
    exposure_records_reviewed: bool
    qualification_evidence_reviewed: bool
    calibration_holdout_partition_reviewed: bool

    @model_validator(mode="after")
    def exposure_identity_and_clock(self):
        identifiers = [exposure.exposure_id for exposure in self.exposures]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("composite exposure identifiers must be unique")
        for first, second in zip(self.exposures, self.exposures[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("composite exposure intervals must be ordered and cannot overlap")
        return self


def composite_compatibility(x: CompositeCompatibility) -> Calculation:
    missing_reviews = [
        name
        for name, reviewed in (
            ("material_and_layup_identity", x.material_and_layup_identity_reviewed),
            ("manufacturing_condition", x.manufacturing_condition_reviewed),
            ("environment_and_clock", x.environment_and_clock_reviewed),
            ("exposure_records", x.exposure_records_reviewed),
            ("qualification_evidence", x.qualification_evidence_reviewed),
            ("calibration_holdout_partition", x.calibration_holdout_partition_reviewed),
        )
        if not reviewed
    ]
    envelope = x.qualification_envelope
    identity_fields = (
        "laminate_system_id",
        "resin_system_id",
        "fiber_system_id",
        "manufacturing_condition_id",
        "layup_id",
        "environment_id",
    )
    envelope_identity_mismatches = [
        field for field in identity_fields if getattr(x, field) != getattr(envelope, field)
    ]
    invalid_exposure_ids = [exposure.exposure_id for exposure in x.exposures if not exposure.record_valid]

    invalid_qualification_ids = []
    qualification_identity_mismatches = []
    source_partitions: dict[str, set[str]] = {}
    for record in envelope.qualification_records:
        if not record.record_valid or not record.supports_declared_envelope:
            invalid_qualification_ids.append(record.record_id)
        mismatches = [
            field for field in identity_fields if getattr(record, field) != getattr(envelope, field)
        ]
        if mismatches:
            qualification_identity_mismatches.append({"record_id": record.record_id, "fields": mismatches})
        source_partitions.setdefault(record.source_group_id, set()).add(record.partition)
    leaking_source_groups = sorted(
        group for group, partitions in source_partitions.items() if len(partitions) > 1
    )
    partitions = {record.partition for record in envelope.qualification_records}
    missing_partitions = sorted({"calibration", "holdout"} - partitions)

    if (
        missing_reviews
        or envelope_identity_mismatches
        or invalid_exposure_ids
        or invalid_qualification_ids
        or qualification_identity_mismatches
        or leaking_source_groups
        or missing_partitions
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "envelope_identity_mismatch_fields": envelope_identity_mismatches,
                "invalid_exposure_ids": invalid_exposure_ids,
                "invalid_qualification_record_ids": invalid_qualification_ids,
                "qualification_identity_mismatches": qualification_identity_mismatches,
                "source_groups_crossing_partitions": leaking_source_groups,
                "missing_evidence_partitions": missing_partitions,
            },
            notes=(
                "Compatibility comparison is withheld until identities, records and separated qualification evidence are complete.",
            ),
        )

    cumulative_exposure = 0.0
    comparisons = []
    violating_exposure_ids = []
    for exposure in x.exposures:
        duration = exposure.end_time_s - exposure.start_time_s
        cumulative_exposure += duration
        violations = []
        if not envelope.minimum_temperature_K <= exposure.temperature_K <= envelope.maximum_temperature_K:
            violations.append("temperature")
        if not (
            envelope.minimum_moisture_mass_fraction
            <= exposure.moisture_mass_fraction
            <= envelope.maximum_moisture_mass_fraction
        ):
            violations.append("moisture")
        if (
            not envelope.minimum_pressure_Pa_abs
            <= exposure.pressure_Pa_abs
            <= envelope.maximum_pressure_Pa_abs
        ):
            violations.append("pressure")
        if violations:
            violating_exposure_ids.append(exposure.exposure_id)
        comparisons.append(
            {
                "exposure_id": exposure.exposure_id,
                "duration_s": duration,
                "violations": violations,
                "within_declared_state_envelope": not violations,
            }
        )
    cumulative_within = cumulative_exposure <= envelope.maximum_cumulative_exposure_s
    evidence_summary = {
        partition: {
            "record_count": sum(record.partition == partition for record in envelope.qualification_records),
            "coupon_ids": [
                record.coupon_id for record in envelope.qualification_records if record.partition == partition
            ],
            "source_group_ids": sorted(
                {
                    record.source_group_id
                    for record in envelope.qualification_records
                    if record.partition == partition
                }
            ),
        }
        for partition in ("calibration", "holdout")
    }
    within = not violating_exposure_ids and cumulative_within
    return Calculation(
        values={
            "assessment_id": x.assessment_id,
            "exposure_comparisons": comparisons,
            "cumulative_exposure_s": cumulative_exposure,
            "remaining_declared_exposure_s": envelope.maximum_cumulative_exposure_s - cumulative_exposure,
            "cumulative_exposure_within_envelope": cumulative_within,
            "violating_exposure_ids": violating_exposure_ids,
            "qualification_evidence_summary": evidence_summary,
            "declared_compatibility_outcome": "within" if within else "outside",
        },
        notes=(
            "The outcome is an applicability comparison with a caller-owned qualification envelope, not material acceptance.",
            "Micromechanics, strength reduction, delamination growth, damage accumulation and service life are not calculated.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "materials.composite_compatibility_assessment",
            CompositeCompatibility,
            composite_compatibility,
            {
                "assessment_id": "1",
                "exposure_comparisons": "1",
                "cumulative_exposure_s": "s",
                "remaining_declared_exposure_s": "s",
                "cumulative_exposure_within_envelope": "1",
                "violating_exposure_ids": "1",
                "qualification_evidence_summary": "1",
                "declared_compatibility_outcome": "1",
            },
            (
                "Laminate, resin, fiber, manufacturing, layup and environment identities must match exactly.",
                "Service states are recorded as constant values within nonoverlapping intervals on one reviewed clock.",
                "Calibration and holdout source groups remain separated and only support a caller-declared envelope.",
            ),
            ("declared_composite_qualification_envelope",),
        )
    ]

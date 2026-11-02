"""Carburization exposure applicability against caller-owned evidence support."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class CarburizationExposure(Contract):
    exposure_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    carbon_basis: Literal["carbon_activity", "carburizing_potential"]
    carbon_value: Nonnegative
    carbon_unit: str = Field(min_length=1)
    temperature_K: Positive
    pressure_Pa_abs: Positive
    gas_composition_descriptor: str = Field(min_length=1)
    record_valid: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def positive_duration(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("carburization exposure interval must have positive duration")
        return self


class CarburizationTestEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    test_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    alloy_condition_id: str = Field(min_length=1)
    record_valid: bool
    supports_declared_envelope: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class CarburizationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    alloy_condition_id: str = Field(min_length=1)
    carbon_basis: Literal["carbon_activity", "carburizing_potential"]
    carbon_unit: str = Field(min_length=1)
    minimum_carbon_value: Nonnegative
    maximum_carbon_value: Nonnegative
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_pressure_Pa_abs: Positive
    maximum_pressure_Pa_abs: Positive
    supported_gas_composition_descriptors: tuple[str, ...] = Field(min_length=1)
    maximum_cumulative_exposure_s: Positive
    test_evidence: tuple[CarburizationTestEvidence, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ranges_and_identities(self):
        for lower, upper, name in (
            (self.minimum_carbon_value, self.maximum_carbon_value, "carbon"),
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (self.minimum_pressure_Pa_abs, self.maximum_pressure_Pa_abs, "pressure"),
        ):
            if upper < lower:
                raise ValueError(f"{name} envelope bounds must be ordered")
        descriptors = self.supported_gas_composition_descriptors
        if len(descriptors) != len(set(descriptors)) or any(not value.strip() for value in descriptors):
            raise ValueError("gas composition descriptors must be unique and nonblank")
        record_ids = [record.evidence_record_id for record in self.test_evidence]
        specimen_ids = [record.specimen_id for record in self.test_evidence]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("carburization evidence record identifiers must be unique")
        if len(specimen_ids) != len(set(specimen_ids)):
            raise ValueError("carburization specimen identifiers must be unique")
        return self


class CarburizationApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    alloy_condition_id: str = Field(min_length=1)
    exposures: tuple[CarburizationExposure, ...] = Field(min_length=1)
    qualification_envelope: CarburizationEnvelope
    material_and_alloy_condition_reviewed: bool
    carbon_basis_and_units_reviewed: bool
    temperature_pressure_and_gas_reviewed: bool
    clock_and_duration_reviewed: bool
    qualification_evidence_reviewed: bool

    @model_validator(mode="after")
    def exposure_clock(self):
        identifiers = [exposure.exposure_id for exposure in self.exposures]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("carburization exposure identifiers must be unique")
        for first, second in zip(self.exposures, self.exposures[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("carburization exposure intervals must be ordered and cannot overlap")
        return self


def carburization_applicability(x: CarburizationApplicability) -> Calculation:
    envelope = x.qualification_envelope
    missing_reviews = [
        name
        for name, reviewed in (
            ("material_and_alloy_condition", x.material_and_alloy_condition_reviewed),
            ("carbon_basis_and_units", x.carbon_basis_and_units_reviewed),
            ("temperature_pressure_and_gas", x.temperature_pressure_and_gas_reviewed),
            ("clock_and_duration", x.clock_and_duration_reviewed),
            ("qualification_evidence", x.qualification_evidence_reviewed),
        )
        if not reviewed
    ]
    identity_mismatches = []
    for field in ("material_condition_id", "alloy_condition_id"):
        if getattr(x, field) != getattr(envelope, field):
            identity_mismatches.append(field)
    invalid_exposure_ids = [exposure.exposure_id for exposure in x.exposures if not exposure.record_valid]
    basis_or_unit_mismatches = [
        {
            "exposure_id": exposure.exposure_id,
            "fields": [
                field
                for field in ("carbon_basis", "carbon_unit")
                if getattr(exposure, field) != getattr(envelope, field)
            ],
        }
        for exposure in x.exposures
        if exposure.carbon_basis != envelope.carbon_basis or exposure.carbon_unit != envelope.carbon_unit
    ]
    invalid_evidence_ids = []
    evidence_identity_mismatches = []
    for record in envelope.test_evidence:
        if not record.record_valid or not record.supports_declared_envelope:
            invalid_evidence_ids.append(record.evidence_record_id)
        fields = [
            field
            for field in ("material_condition_id", "alloy_condition_id")
            if getattr(record, field) != getattr(envelope, field)
        ]
        if fields:
            evidence_identity_mismatches.append(
                {"evidence_record_id": record.evidence_record_id, "fields": fields}
            )
    if (
        missing_reviews
        or identity_mismatches
        or invalid_exposure_ids
        or basis_or_unit_mismatches
        or invalid_evidence_ids
        or evidence_identity_mismatches
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "identity_mismatch_fields": identity_mismatches,
                "invalid_exposure_ids": invalid_exposure_ids,
                "carbon_basis_or_unit_mismatches": basis_or_unit_mismatches,
                "invalid_test_evidence_ids": invalid_evidence_ids,
                "test_evidence_identity_mismatches": evidence_identity_mismatches,
            },
            notes=(
                "Applicability is withheld until identities, carbon basis, exact units and test evidence are complete.",
            ),
        )

    cumulative_exposure = 0.0
    outside_ids = []
    comparisons = []
    for exposure in x.exposures:
        duration = exposure.end_time_s - exposure.start_time_s
        cumulative_exposure += duration
        unsupported = []
        if not envelope.minimum_carbon_value <= exposure.carbon_value <= envelope.maximum_carbon_value:
            unsupported.append("carbon_value")
        if not envelope.minimum_temperature_K <= exposure.temperature_K <= envelope.maximum_temperature_K:
            unsupported.append("temperature")
        if (
            not envelope.minimum_pressure_Pa_abs
            <= exposure.pressure_Pa_abs
            <= envelope.maximum_pressure_Pa_abs
        ):
            unsupported.append("pressure")
        if exposure.gas_composition_descriptor not in envelope.supported_gas_composition_descriptors:
            unsupported.append("gas_composition_descriptor")
        if unsupported:
            outside_ids.append(exposure.exposure_id)
        comparisons.append(
            {
                "exposure_id": exposure.exposure_id,
                "duration_s": duration,
                "unsupported_fields": unsupported,
                "within_declared_support": not unsupported,
            }
        )
    cumulative_supported = cumulative_exposure <= envelope.maximum_cumulative_exposure_s
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "exposure_comparisons": comparisons,
        "cumulative_exposure_s": cumulative_exposure,
        "remaining_supported_exposure_s": envelope.maximum_cumulative_exposure_s - cumulative_exposure,
        "cumulative_exposure_within_support": cumulative_supported,
        "outside_support_exposure_ids": outside_ids,
        "test_evidence_summary": {
            "record_ids": [record.evidence_record_id for record in envelope.test_evidence],
            "test_ids": sorted({record.test_id for record in envelope.test_evidence}),
            "specimen_ids": [record.specimen_id for record in envelope.test_evidence],
            "source_group_ids": sorted({record.source_group_id for record in envelope.test_evidence}),
        },
    }
    notes = (
        "Applicability compares reviewed exposure records only with a caller-owned qualification envelope.",
        "No carbon profile, kinetic rate, phase or property change, lifetime or acceptance result is produced.",
    )
    if outside_ids or not cumulative_supported:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_applicability_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    return [
        ModelSpec(
            "degradation.carburization_applicability",
            CarburizationApplicability,
            carburization_applicability,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "exposure_comparisons": "1",
                "cumulative_exposure_s": "s",
                "remaining_supported_exposure_s": "s",
                "cumulative_exposure_within_support": "1",
                "outside_support_exposure_ids": "1",
                "test_evidence_summary": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Material and alloy-condition identities match the caller-owned qualification evidence exactly.",
                "Carbon activity or carburizing potential is compared only under an exact basis and unit token.",
                "Gas composition is a caller-defined descriptor; carbon transfer and material response are not inferred.",
            ),
            ("declared_carburization_qualification_envelope",),
        )
    ]

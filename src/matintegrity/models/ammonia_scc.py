"""Ammonia-SCC applicability against caller-controlled qualification evidence."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class AmmoniaSCCExposure(Contract):
    exposure_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    ammonia_phase: str = Field(min_length=1)
    ammonia_concentration: Nonnegative
    ammonia_concentration_unit: str = Field(min_length=1)
    water_state_descriptor: str = Field(min_length=1)
    oxygen_state_descriptor: str = Field(min_length=1)
    impurity_state_descriptor: str = Field(min_length=1)
    temperature_K: Positive
    applied_stress_descriptor: str = Field(min_length=1)
    residual_stress_descriptor: str = Field(min_length=1)
    record_valid: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def positive_duration(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("ammonia-SCC exposure interval must have positive duration")
        return self


class AmmoniaSCCTestEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    test_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    metallurgy_id: str = Field(min_length=1)
    heat_treatment_id: str = Field(min_length=1)
    record_valid: bool
    supports_declared_envelope: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class AmmoniaSCCEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    metallurgy_id: str = Field(min_length=1)
    heat_treatment_id: str = Field(min_length=1)
    supported_ammonia_phases: tuple[str, ...] = Field(min_length=1)
    ammonia_concentration_unit: str = Field(min_length=1)
    minimum_ammonia_concentration: Nonnegative
    maximum_ammonia_concentration: Nonnegative
    supported_water_state_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_oxygen_state_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_impurity_state_descriptors: tuple[str, ...] = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    supported_applied_stress_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_residual_stress_descriptors: tuple[str, ...] = Field(min_length=1)
    maximum_cumulative_exposure_s: Positive
    test_evidence: tuple[AmmoniaSCCTestEvidence, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ranges_and_identities(self):
        if self.maximum_ammonia_concentration < self.minimum_ammonia_concentration:
            raise ValueError("ammonia concentration envelope bounds must be ordered")
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("temperature envelope bounds must be ordered")
        for values, name in (
            (self.supported_ammonia_phases, "ammonia phase"),
            (self.supported_water_state_descriptors, "water state"),
            (self.supported_oxygen_state_descriptors, "oxygen state"),
            (self.supported_impurity_state_descriptors, "impurity state"),
            (self.supported_applied_stress_descriptors, "applied stress"),
            (self.supported_residual_stress_descriptors, "residual stress"),
        ):
            if len(values) != len(set(values)) or any(not value.strip() for value in values):
                raise ValueError(f"supported {name} descriptors must be unique and nonblank")
        record_ids = [record.evidence_record_id for record in self.test_evidence]
        specimen_ids = [record.specimen_id for record in self.test_evidence]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("ammonia-SCC evidence record identifiers must be unique")
        if len(specimen_ids) != len(set(specimen_ids)):
            raise ValueError("ammonia-SCC specimen identifiers must be unique")
        return self


class AmmoniaSCCApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    metallurgy_id: str = Field(min_length=1)
    heat_treatment_id: str = Field(min_length=1)
    exposures: tuple[AmmoniaSCCExposure, ...] = Field(min_length=1)
    qualification_envelope: AmmoniaSCCEnvelope
    material_metallurgy_and_heat_treatment_reviewed: bool
    ammonia_phase_concentration_and_units_reviewed: bool
    water_oxygen_and_impurity_states_reviewed: bool
    stress_descriptors_reviewed: bool
    clock_and_duration_reviewed: bool
    qualification_evidence_reviewed: bool

    @model_validator(mode="after")
    def exposure_clock(self):
        identifiers = [exposure.exposure_id for exposure in self.exposures]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("ammonia-SCC exposure identifiers must be unique")
        for first, second in zip(self.exposures, self.exposures[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("ammonia-SCC exposure intervals must be ordered and cannot overlap")
        return self


def ammonia_scc_applicability(x: AmmoniaSCCApplicability) -> Calculation:
    envelope = x.qualification_envelope
    missing_reviews = [
        name
        for name, reviewed in (
            (
                "material_metallurgy_and_heat_treatment",
                x.material_metallurgy_and_heat_treatment_reviewed,
            ),
            (
                "ammonia_phase_concentration_and_units",
                x.ammonia_phase_concentration_and_units_reviewed,
            ),
            ("water_oxygen_and_impurity_states", x.water_oxygen_and_impurity_states_reviewed),
            ("stress_descriptors", x.stress_descriptors_reviewed),
            ("clock_and_duration", x.clock_and_duration_reviewed),
            ("qualification_evidence", x.qualification_evidence_reviewed),
        )
        if not reviewed
    ]
    identity_fields = ("material_condition_id", "metallurgy_id", "heat_treatment_id")
    identity_mismatches = [
        field for field in identity_fields if getattr(x, field) != getattr(envelope, field)
    ]
    invalid_exposure_ids = [exposure.exposure_id for exposure in x.exposures if not exposure.record_valid]
    unit_mismatch_ids = [
        exposure.exposure_id
        for exposure in x.exposures
        if exposure.ammonia_concentration_unit != envelope.ammonia_concentration_unit
    ]
    invalid_evidence_ids = []
    evidence_identity_mismatches = []
    for record in envelope.test_evidence:
        if not record.record_valid or not record.supports_declared_envelope:
            invalid_evidence_ids.append(record.evidence_record_id)
        fields = [field for field in identity_fields if getattr(record, field) != getattr(envelope, field)]
        if fields:
            evidence_identity_mismatches.append(
                {"evidence_record_id": record.evidence_record_id, "fields": fields}
            )
    if (
        missing_reviews
        or identity_mismatches
        or invalid_exposure_ids
        or unit_mismatch_ids
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
                "ammonia_concentration_unit_mismatch_ids": unit_mismatch_ids,
                "invalid_test_evidence_ids": invalid_evidence_ids,
                "test_evidence_identity_mismatches": evidence_identity_mismatches,
            },
            notes=(
                "Applicability is withheld until exact identities, units, records and test evidence are complete.",
            ),
        )

    cumulative_exposure = 0.0
    outside_ids = []
    comparisons = []
    for exposure in x.exposures:
        duration = exposure.end_time_s - exposure.start_time_s
        cumulative_exposure += duration
        unsupported = []
        if exposure.ammonia_phase not in envelope.supported_ammonia_phases:
            unsupported.append("ammonia_phase")
        if not (
            envelope.minimum_ammonia_concentration
            <= exposure.ammonia_concentration
            <= envelope.maximum_ammonia_concentration
        ):
            unsupported.append("ammonia_concentration")
        for value, supported, name in (
            (
                exposure.water_state_descriptor,
                envelope.supported_water_state_descriptors,
                "water_state_descriptor",
            ),
            (
                exposure.oxygen_state_descriptor,
                envelope.supported_oxygen_state_descriptors,
                "oxygen_state_descriptor",
            ),
            (
                exposure.impurity_state_descriptor,
                envelope.supported_impurity_state_descriptors,
                "impurity_state_descriptor",
            ),
            (
                exposure.applied_stress_descriptor,
                envelope.supported_applied_stress_descriptors,
                "applied_stress_descriptor",
            ),
            (
                exposure.residual_stress_descriptor,
                envelope.supported_residual_stress_descriptors,
                "residual_stress_descriptor",
            ),
        ):
            if value not in supported:
                unsupported.append(name)
        if not envelope.minimum_temperature_K <= exposure.temperature_K <= envelope.maximum_temperature_K:
            unsupported.append("temperature")
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
        "Applicability compares reviewed inputs only with a caller-owned qualification envelope.",
        "No SCC threshold, initiation, crack growth, lifetime, probability or acceptance result is produced.",
    )
    if outside_ids or not cumulative_supported:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_applicability_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    return [
        ModelSpec(
            "degradation.ammonia_scc_applicability",
            AmmoniaSCCApplicability,
            ammonia_scc_applicability,
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
                "Material, metallurgy and heat-treatment identities match the qualification evidence exactly.",
                "Ammonia concentration is compared only under an exact caller-declared unit token; no conversion is hidden.",
                "Water, oxygen, impurity and stress conditions are caller-defined descriptors, not inferred quantities or thresholds.",
            ),
            ("declared_ammonia_scc_qualification_envelope",),
        )
    ]

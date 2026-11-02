"""Liquid-metal exposure applicability against caller-qualified evidence support."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class LMEQualificationObservation(Contract):
    observation_id: str = Field(min_length=1)
    observation_kind: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    physical_region_id: str = Field(min_length=1)
    reported_endpoint: str = Field(min_length=1)
    record_valid: bool
    invalid_or_limiting_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_observation(self):
        if not self.record_valid and not self.invalid_or_limiting_basis:
            raise ValueError("invalid liquid-metal test observations require a basis")
        return self


class LMEQualificationTestEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    test_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    structural_material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    liquid_metal_species_id: str = Field(min_length=1)
    liquid_metal_composition_id: str = Field(min_length=1)
    impurity_profile_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observations: tuple[LMEQualificationObservation, ...] = Field(min_length=1)
    record_valid: bool
    supports_declared_envelope: bool
    invalid_or_limiting_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_observations_and_validity(self):
        identifiers = [row.observation_id for row in self.observations]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("liquid-metal qualification observation identifiers must be unique per test")
        if (
            not self.record_valid or not self.supports_declared_envelope
        ) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or limiting liquid-metal test evidence requires a basis")
        return self


class LiquidMetalExposureInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    liquid_metal_species_id: str = Field(min_length=1)
    liquid_metal_composition_id: str = Field(min_length=1)
    impurity_profile_id: str = Field(min_length=1)
    contact_state_descriptor: str = Field(min_length=1)
    wetting_descriptor: str = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_stress_value: Nonnegative
    maximum_stress_value: Nonnegative
    stress_unit_token: str = Field(min_length=1)
    minimum_strain_rate_value: Nonnegative
    maximum_strain_rate_value: Nonnegative
    strain_rate_unit_token: str = Field(min_length=1)
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_ranges_and_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("liquid-metal exposure intervals must have positive duration")
        for lower, upper, name in (
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (self.minimum_stress_value, self.maximum_stress_value, "stress"),
            (self.minimum_strain_rate_value, self.maximum_strain_rate_value, "strain-rate"),
        ):
            if upper < lower:
                raise ValueError(f"liquid-metal exposure {name} ranges must be ordered")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid liquid-metal exposure requires a basis")
        return self


class LMEQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    structural_material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    liquid_metal_species_id: str = Field(min_length=1)
    liquid_metal_composition_id: str = Field(min_length=1)
    impurity_profile_id: str = Field(min_length=1)
    supported_contact_state_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_wetting_descriptors: tuple[str, ...] = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_stress_value: Nonnegative
    maximum_stress_value: Nonnegative
    stress_unit_token: str = Field(min_length=1)
    minimum_strain_rate_value: Nonnegative
    maximum_strain_rate_value: Nonnegative
    strain_rate_unit_token: str = Field(min_length=1)
    maximum_single_exposure_s: Positive
    maximum_cumulative_exposure_s: Positive
    test_evidence: tuple[LMEQualificationTestEvidence, ...] = Field(min_length=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support_and_unique_evidence(self):
        for lower, upper, name in (
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (self.minimum_stress_value, self.maximum_stress_value, "stress"),
            (self.minimum_strain_rate_value, self.maximum_strain_rate_value, "strain-rate"),
        ):
            if upper < lower:
                raise ValueError(f"liquid-metal qualification {name} bounds must be ordered")
        if self.maximum_cumulative_exposure_s < self.maximum_single_exposure_s:
            raise ValueError(
                "cumulative liquid-metal exposure support cannot be below single exposure support"
            )
        for values, name in (
            (self.supported_contact_state_descriptors, "contact-state"),
            (self.supported_wetting_descriptors, "wetting"),
        ):
            if len(set(values)) != len(values) or any(not value.strip() for value in values):
                raise ValueError(f"supported {name} descriptors must be unique and nonblank")
        evidence_ids = [row.evidence_record_id for row in self.test_evidence]
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("liquid-metal test evidence record identifiers must be unique")
        observation_ids = [
            observation.observation_id for record in self.test_evidence for observation in record.observations
        ]
        if len(set(observation_ids)) != len(observation_ids):
            raise ValueError("liquid-metal observation identifiers must be unique across tests")
        return self


class LiquidMetalEmbrittlementApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    structural_material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    exposures: tuple[LiquidMetalExposureInterval, ...] = Field(min_length=1)
    qualification_envelope: LMEQualificationEnvelope
    structural_material_and_condition_reviewed: bool
    liquid_metal_composition_and_impurities_reviewed: bool
    contact_state_and_wetting_reviewed: bool
    temperature_stress_and_strain_rate_reviewed: bool
    exposure_clock_and_duration_reviewed: bool
    observation_and_test_evidence_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_envelope_authority_reviewed: bool

    @model_validator(mode="after")
    def unique_ordered_exposures(self):
        identifiers = [row.interval_id for row in self.exposures]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("liquid-metal exposure interval identifiers must be unique")
        for first, second in zip(self.exposures, self.exposures[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("liquid-metal exposure intervals must be ordered and cannot overlap")
        return self


def liquid_metal_embrittlement_applicability(
    x: LiquidMetalEmbrittlementApplicability,
) -> Calculation:
    envelope = x.qualification_envelope
    missing_reviews = [
        name
        for name in (
            "structural_material_and_condition_reviewed",
            "liquid_metal_composition_and_impurities_reviewed",
            "contact_state_and_wetting_reviewed",
            "temperature_stress_and_strain_rate_reviewed",
            "exposure_clock_and_duration_reviewed",
            "observation_and_test_evidence_reviewed",
            "provider_lineage_and_digests_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    identity_fields = ("structural_material_id", "material_condition_id")
    identity_mismatches = [
        field for field in identity_fields if getattr(x, field) != getattr(envelope, field)
    ]
    invalid_exposure_ids = [row.interval_id for row in x.exposures if not row.record_valid]
    unit_mismatch_ids = [
        row.interval_id
        for row in x.exposures
        if row.stress_unit_token != envelope.stress_unit_token
        or row.strain_rate_unit_token != envelope.strain_rate_unit_token
    ]
    invalid_evidence_ids = []
    invalid_observation_ids = []
    evidence_identity_mismatches = []
    evidence_identity_fields = (
        "structural_material_id",
        "material_condition_id",
        "liquid_metal_species_id",
        "liquid_metal_composition_id",
        "impurity_profile_id",
    )
    for record in envelope.test_evidence:
        if not record.record_valid or not record.supports_declared_envelope:
            invalid_evidence_ids.append(record.evidence_record_id)
        fields = [
            field for field in evidence_identity_fields if getattr(record, field) != getattr(envelope, field)
        ]
        if fields:
            evidence_identity_mismatches.append(
                {"evidence_record_id": record.evidence_record_id, "fields": fields}
            )
        invalid_observation_ids.extend(
            row.observation_id for row in record.observations if not row.record_valid
        )
    incomplete = bool(
        missing_reviews
        or identity_mismatches
        or invalid_exposure_ids
        or unit_mismatch_ids
        or invalid_evidence_ids
        or invalid_observation_ids
        or evidence_identity_mismatches
    )
    if incomplete:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "identity_mismatch_fields": identity_mismatches,
                "invalid_exposure_interval_ids": invalid_exposure_ids,
                "stress_or_strain_rate_unit_mismatch_interval_ids": unit_mismatch_ids,
                "invalid_test_evidence_ids": invalid_evidence_ids,
                "invalid_test_observation_ids": invalid_observation_ids,
                "test_evidence_identity_mismatches": evidence_identity_mismatches,
            },
            notes=(
                "Applicability is withheld until identities, units and qualification evidence are complete.",
            ),
        )

    cumulative_exposure = 0.0
    comparisons = []
    outside_ids = []
    for exposure in x.exposures:
        duration = exposure.end_time_s - exposure.start_time_s
        cumulative_exposure += duration
        reasons = []
        for field in (
            "liquid_metal_species_id",
            "liquid_metal_composition_id",
            "impurity_profile_id",
        ):
            if getattr(exposure, field) != getattr(envelope, field):
                reasons.append(field)
        if exposure.contact_state_descriptor not in envelope.supported_contact_state_descriptors:
            reasons.append("contact_state_descriptor")
        if exposure.wetting_descriptor not in envelope.supported_wetting_descriptors:
            reasons.append("wetting_descriptor")
        for observed_min, observed_max, supported_min, supported_max, name in (
            (
                exposure.minimum_temperature_K,
                exposure.maximum_temperature_K,
                envelope.minimum_temperature_K,
                envelope.maximum_temperature_K,
                "temperature_range",
            ),
            (
                exposure.minimum_stress_value,
                exposure.maximum_stress_value,
                envelope.minimum_stress_value,
                envelope.maximum_stress_value,
                "stress_range",
            ),
            (
                exposure.minimum_strain_rate_value,
                exposure.maximum_strain_rate_value,
                envelope.minimum_strain_rate_value,
                envelope.maximum_strain_rate_value,
                "strain_rate_range",
            ),
        ):
            if observed_min < supported_min or observed_max > supported_max:
                reasons.append(name)
        if duration > envelope.maximum_single_exposure_s:
            reasons.append("single_exposure_duration")
        if reasons:
            outside_ids.append(exposure.interval_id)
        comparisons.append(
            {
                "interval_id": exposure.interval_id,
                "duration_s": duration,
                "outside_support_reasons": reasons,
                "within_declared_qualification_support": not reasons,
            }
        )
    cumulative_supported = cumulative_exposure <= envelope.maximum_cumulative_exposure_s
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "qualification_envelope_id": envelope.envelope_id,
        "exposure_comparisons": comparisons,
        "cumulative_exposure_s": cumulative_exposure,
        "remaining_supported_exposure_s": envelope.maximum_cumulative_exposure_s - cumulative_exposure,
        "cumulative_exposure_within_support": cumulative_supported,
        "outside_support_exposure_interval_ids": outside_ids,
        "test_evidence_summary": {
            "evidence_record_ids": [row.evidence_record_id for row in envelope.test_evidence],
            "test_ids": sorted({row.test_id for row in envelope.test_evidence}),
            "physical_specimen_ids": sorted({row.physical_specimen_id for row in envelope.test_evidence}),
            "source_group_ids": sorted({row.source_group_id for row in envelope.test_evidence}),
            "observation_ids": [
                observation.observation_id
                for row in envelope.test_evidence
                for observation in row.observations
            ],
        },
    }
    notes = (
        "Applicability compares reviewed inputs only with a caller-owned qualification envelope; no material/liquid-metal susceptibility table is bundled.",
        "Observation records and provider digests preserve evidence lineage but do not establish transferability or independent specimen populations.",
        "No crack initiation or growth, property loss, remaining life, failure probability or acceptance result is produced.",
    )
    if outside_ids or not cumulative_supported:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_applicability_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("liquid-metal assessment asset and location must match the run context")

    return [
        ModelSpec(
            "degradation.liquid_metal_embrittlement_applicability",
            LiquidMetalEmbrittlementApplicability,
            liquid_metal_embrittlement_applicability,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "qualification_envelope_id": "1",
                "exposure_comparisons": "mixed",
                "cumulative_exposure_s": "s",
                "remaining_supported_exposure_s": "s",
                "cumulative_exposure_within_support": "1",
                "outside_support_exposure_interval_ids": "1",
                "test_evidence_summary": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Structural material, condition, liquid-metal species, composition and impurity identities match qualification evidence exactly.",
                "Stress and strain-rate ranges are compared only under exact caller-declared unit tokens; no conversion is inferred.",
                "Contact, wetting and evidence support are caller declarations, not susceptibility classification or acceptance criteria.",
            ),
            ("declared_liquid_metal_embrittlement_qualification_envelope",),
            context_validator=same_identity,
        )
    ]

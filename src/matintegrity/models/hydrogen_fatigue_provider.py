"""Hydrogen-fatigue growth-provider results bound to caller qualification evidence."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

ExposureQuantityKind = Literal["absolute_partial_pressure", "fugacity"]
ResultKind = Literal["tabulated_growth_curve", "predicted_growth_rate"]
Partition = Literal["calibration", "holdout"]


class HydrogenFatigueGrowthPoint(Contract):
    point_id: str = Field(min_length=1)
    delta_k_value: Positive
    growth_rate_value: Positive
    expanded_growth_rate_uncertainty: Nonnegative
    uncertainty_coverage_factor: Positive
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class HydrogenFatigueProviderResult(Contract):
    result_record_id: str = Field(min_length=1)
    curve_or_result_id: str = Field(min_length=1)
    result_kind: ResultKind
    material_condition_id: str = Field(min_length=1)
    hydrogen_species: str = Field(min_length=1)
    exposure_quantity_kind: ExposureQuantityKind
    exposure_quantity_value: Positive
    exposure_quantity_unit_token: str = Field(min_length=1)
    temperature_K: Positive
    load_ratio: float = Field(lt=1.0)
    frequency_Hz: Positive
    waveform_descriptor: str = Field(min_length=1)
    delta_k_definition: str = Field(min_length=1)
    delta_k_unit_token: str = Field(min_length=1)
    growth_rate_definition: str = Field(min_length=1)
    growth_rate_unit_token: str = Field(min_length=1)
    points: tuple[HydrogenFatigueGrowthPoint, ...] = Field(min_length=1)
    solver_or_method_id: str = Field(min_length=1)
    solver_or_method_revision: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_points(self):
        identifiers = [row.point_id for row in self.points]
        delta_k = [row.delta_k_value for row in self.points]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("hydrogen-fatigue point identifiers must be unique")
        if any(second <= first for first, second in zip(delta_k, delta_k[1:], strict=False)):
            raise ValueError("hydrogen-fatigue delta-K points must be strictly increasing")
        if self.result_kind == "predicted_growth_rate" and len(self.points) != 1:
            raise ValueError("a predicted growth-rate result requires exactly one point")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid hydrogen-fatigue provider result requires a basis")
        return self


class HydrogenFatigueQualificationEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    partition: Partition
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    hydrogen_species: str = Field(min_length=1)
    exposure_quantity_kind: ExposureQuantityKind
    exposure_quantity_unit_token: str = Field(min_length=1)
    delta_k_definition: str = Field(min_length=1)
    delta_k_unit_token: str = Field(min_length=1)
    growth_rate_definition: str = Field(min_length=1)
    growth_rate_unit_token: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    supports_declared_envelope: bool
    invalid_or_limiting_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity_has_basis(self):
        if (
            not self.record_valid or not self.supports_declared_envelope
        ) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or limiting hydrogen-fatigue evidence requires a basis")
        return self


class HydrogenFatigueQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    hydrogen_species: str = Field(min_length=1)
    exposure_quantity_kind: ExposureQuantityKind
    exposure_quantity_unit_token: str = Field(min_length=1)
    minimum_exposure_quantity_value: Positive
    maximum_exposure_quantity_value: Positive
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_load_ratio: float = Field(lt=1.0)
    maximum_load_ratio: float = Field(lt=1.0)
    minimum_frequency_Hz: Positive
    maximum_frequency_Hz: Positive
    supported_waveform_descriptors: tuple[str, ...] = Field(min_length=1)
    delta_k_definition: str = Field(min_length=1)
    delta_k_unit_token: str = Field(min_length=1)
    minimum_delta_k_value: Positive
    maximum_delta_k_value: Positive
    growth_rate_definition: str = Field(min_length=1)
    growth_rate_unit_token: str = Field(min_length=1)
    supported_result_kinds: tuple[ResultKind, ...] = Field(min_length=1)
    solver_or_method_id: str = Field(min_length=1)
    solver_or_method_revision: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    qualification_evidence: tuple[HydrogenFatigueQualificationEvidence, ...] = Field(min_length=1)
    minimum_calibration_source_group_count: int = Field(ge=1)
    minimum_holdout_source_group_count: int = Field(ge=1)
    minimum_holdout_independence_group_count: int = Field(ge=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        for lower, upper, name in (
            (self.minimum_exposure_quantity_value, self.maximum_exposure_quantity_value, "exposure"),
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (self.minimum_load_ratio, self.maximum_load_ratio, "load-ratio"),
            (self.minimum_frequency_Hz, self.maximum_frequency_Hz, "frequency"),
            (self.minimum_delta_k_value, self.maximum_delta_k_value, "delta-K"),
        ):
            if upper < lower:
                raise ValueError(f"hydrogen-fatigue {name} support must be ordered")
        if len(set(self.supported_waveform_descriptors)) != len(self.supported_waveform_descriptors):
            raise ValueError("hydrogen-fatigue waveform descriptors must be unique")
        if len(set(self.supported_result_kinds)) != len(self.supported_result_kinds):
            raise ValueError("hydrogen-fatigue result kinds must be unique")
        evidence_ids = [row.evidence_record_id for row in self.qualification_evidence]
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("hydrogen-fatigue qualification evidence identifiers must be unique")
        return self


class HydrogenFatigueProviderEvidenceAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    hydrogen_species: str = Field(min_length=1)
    exposure_quantity_kind: ExposureQuantityKind
    exposure_quantity_value: Positive
    exposure_quantity_unit_token: str = Field(min_length=1)
    temperature_K: Positive
    load_ratio: float = Field(lt=1.0)
    frequency_Hz: Positive
    waveform_descriptor: str = Field(min_length=1)
    provider_result: HydrogenFatigueProviderResult
    candidate_envelopes: tuple[HydrogenFatigueQualificationEnvelope, ...] = Field(min_length=1)
    material_and_condition_reviewed: bool
    hydrogen_species_quantity_basis_and_units_reviewed: bool
    temperature_load_ratio_frequency_and_waveform_reviewed: bool
    crack_growth_definitions_units_and_uncertainty_reviewed: bool
    specimen_source_and_independence_partitions_reviewed: bool
    solver_provider_revision_and_digests_reviewed: bool
    calibration_holdout_qualification_reviewed: bool
    qualification_envelope_authority_reviewed: bool

    @model_validator(mode="after")
    def unique_envelopes(self):
        identifiers = [row.envelope_id for row in self.candidate_envelopes]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("hydrogen-fatigue envelope identifiers must be unique")
        return self


def _identity(value) -> tuple[object, ...]:
    return (
        value.material_id,
        value.material_condition_id,
        value.hydrogen_species,
        value.exposure_quantity_kind,
        value.exposure_quantity_unit_token,
    )


def hydrogen_fatigue_provider_evidence(
    x: HydrogenFatigueProviderEvidenceAssessment,
) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_and_condition_reviewed",
            "hydrogen_species_quantity_basis_and_units_reviewed",
            "temperature_load_ratio_frequency_and_waveform_reviewed",
            "crack_growth_definitions_units_and_uncertainty_reviewed",
            "specimen_source_and_independence_partitions_reviewed",
            "solver_provider_revision_and_digests_reviewed",
            "calibration_holdout_qualification_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    matches = [row for row in x.candidate_envelopes if _identity(row) == _identity(x)]
    if missing_reviews or not x.provider_result.record_valid:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
                "missing_reviews": missing_reviews,
                "provider_result_record_valid": x.provider_result.record_valid,
            },
            notes=("Invalid or unreviewed hydrogen-fatigue provider results are not qualified.",),
        )
    if not matches:
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "identity_matching_envelope_ids": []},
            notes=("No envelope has the exact material, hydrogen quantity basis and unit identity.",),
        )

    envelope = matches[0]
    result = x.provider_result
    result_condition_matches = (
        result.material_condition_id == x.material_condition_id
        and result.hydrogen_species == x.hydrogen_species
        and result.exposure_quantity_kind == x.exposure_quantity_kind
        and result.exposure_quantity_unit_token == x.exposure_quantity_unit_token
        and result.exposure_quantity_value == x.exposure_quantity_value
        and result.temperature_K == x.temperature_K
        and result.load_ratio == x.load_ratio
        and result.frequency_Hz == x.frequency_Hz
        and result.waveform_descriptor == x.waveform_descriptor
    )
    result_definition_and_unit_matches = (
        result.delta_k_definition == envelope.delta_k_definition
        and result.delta_k_unit_token == envelope.delta_k_unit_token
        and result.growth_rate_definition == envelope.growth_rate_definition
        and result.growth_rate_unit_token == envelope.growth_rate_unit_token
    )
    provider_identity_matches = (
        result.solver_or_method_id == envelope.solver_or_method_id
        and result.solver_or_method_revision == envelope.solver_or_method_revision
        and result.provider_id == envelope.provider_id
        and result.provider_revision == envelope.provider_revision
        and result.provider_configuration_digest == envelope.provider_configuration_digest
    )
    invalid_evidence_ids = [
        row.evidence_record_id
        for row in envelope.qualification_evidence
        if not row.record_valid or not row.supports_declared_envelope
    ]
    mismatched_evidence_ids = []
    for row in envelope.qualification_evidence:
        if (
            row.material_condition_id != envelope.material_condition_id
            or row.hydrogen_species != envelope.hydrogen_species
            or row.exposure_quantity_kind != envelope.exposure_quantity_kind
            or row.exposure_quantity_unit_token != envelope.exposure_quantity_unit_token
            or row.delta_k_definition != envelope.delta_k_definition
            or row.delta_k_unit_token != envelope.delta_k_unit_token
            or row.growth_rate_definition != envelope.growth_rate_definition
            or row.growth_rate_unit_token != envelope.growth_rate_unit_token
            or row.provider_id != envelope.provider_id
            or row.provider_revision != envelope.provider_revision
            or row.provider_configuration_digest != envelope.provider_configuration_digest
        ):
            mismatched_evidence_ids.append(row.evidence_record_id)
    calibration_groups = {
        row.source_group_id for row in envelope.qualification_evidence if row.partition == "calibration"
    }
    holdout_groups = {
        row.source_group_id for row in envelope.qualification_evidence if row.partition == "holdout"
    }
    holdout_independence_groups = {
        row.independence_group_id for row in envelope.qualification_evidence if row.partition == "holdout"
    }
    partition_counts_sufficient = (
        len(calibration_groups) >= envelope.minimum_calibration_source_group_count
        and len(holdout_groups) >= envelope.minimum_holdout_source_group_count
        and len(holdout_independence_groups) >= envelope.minimum_holdout_independence_group_count
    )
    if (
        not result_condition_matches
        or not result_definition_and_unit_matches
        or not provider_identity_matches
        or invalid_evidence_ids
        or mismatched_evidence_ids
        or not partition_counts_sufficient
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "qualification_envelope_id": envelope.envelope_id,
                "provider_result_condition_matches": result_condition_matches,
                "provider_result_definition_and_units_match": result_definition_and_unit_matches,
                "provider_identity_matches": provider_identity_matches,
                "invalid_qualification_evidence_ids": invalid_evidence_ids,
                "qualification_evidence_identity_or_unit_mismatch_ids": mismatched_evidence_ids,
                "qualification_partition_counts_sufficient": partition_counts_sufficient,
            },
            notes=("Exact result conditions, definitions, provider lineage and partitions are required.",),
        )

    outside_reasons = []
    for value, lower, upper, name in (
        (
            x.exposure_quantity_value,
            envelope.minimum_exposure_quantity_value,
            envelope.maximum_exposure_quantity_value,
            "exposure_quantity_value",
        ),
        (x.temperature_K, envelope.minimum_temperature_K, envelope.maximum_temperature_K, "temperature_K"),
        (x.load_ratio, envelope.minimum_load_ratio, envelope.maximum_load_ratio, "load_ratio"),
        (x.frequency_Hz, envelope.minimum_frequency_Hz, envelope.maximum_frequency_Hz, "frequency_Hz"),
    ):
        if not lower <= value <= upper:
            outside_reasons.append(name)
    if x.waveform_descriptor not in envelope.supported_waveform_descriptors:
        outside_reasons.append("waveform_descriptor")
    if result.result_kind not in envelope.supported_result_kinds:
        outside_reasons.append("result_kind")
    outside_point_ids = [
        row.point_id
        for row in result.points
        if not envelope.minimum_delta_k_value <= row.delta_k_value <= envelope.maximum_delta_k_value
    ]
    if outside_point_ids:
        outside_reasons.append("delta_k_support")
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "qualification_envelope_id": envelope.envelope_id,
        "provider_result_record_id": result.result_record_id,
        "curve_or_result_id": result.curve_or_result_id,
        "result_kind": result.result_kind,
        "outside_support_reasons": outside_reasons,
        "outside_delta_k_point_ids": outside_point_ids,
        "provider_growth_points": [row.model_dump(mode="json") for row in result.points],
        "calibration_source_group_ids": sorted(calibration_groups),
        "holdout_source_group_ids": sorted(holdout_groups),
        "holdout_independence_group_ids": sorted(holdout_independence_groups),
    }
    notes = (
        "Pressure and fugacity are distinct quantity bases and are never converted automatically.",
        "Provider curve points are preserved without interpolation, extrapolation or crack-growth integration.",
        "No bundled curve, remaining life, failure probability or acceptance result is produced.",
    )
    if outside_reasons:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_applicability_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("hydrogen-fatigue assessment asset and location must match run context")

    return [
        ModelSpec(
            "degradation.hydrogen_fatigue_provider_evidence",
            HydrogenFatigueProviderEvidenceAssessment,
            hydrogen_fatigue_provider_evidence,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "qualification_envelope_id": "1",
                "provider_result_record_id": "1",
                "curve_or_result_id": "1",
                "result_kind": "1",
                "outside_support_reasons": "1",
                "outside_delta_k_point_ids": "1",
                "provider_growth_points": "mixed",
                "calibration_source_group_ids": "1",
                "holdout_source_group_ids": "1",
                "holdout_independence_group_ids": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Material condition, hydrogen species, quantity basis and units match exactly.",
                "Pressure and fugacity are not converted; load and waveform conditions are explicit.",
                "Provider growth evidence is not integrated into life, probability or acceptance.",
            ),
            ("reviewed_hydrogen_fatigue_provider_qualification_envelope",),
            context_validator=same_identity,
        )
    ]

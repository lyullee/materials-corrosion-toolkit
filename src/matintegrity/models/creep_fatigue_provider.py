"""Creep-fatigue interaction-provider results bound to caller qualification evidence."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

Partition = Literal["calibration", "holdout"]


class CreepFatigueExposureBlock(Contract):
    block_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    stress_history_descriptor: str = Field(min_length=1)
    strain_history_descriptor: str = Field(min_length=1)
    cycle_or_block_descriptor: str = Field(min_length=1)
    history_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    creep_exposure_definition: str = Field(min_length=1)
    creep_exposure_value: Nonnegative
    creep_exposure_unit_token: str = Field(min_length=1)
    fatigue_exposure_definition: str = Field(min_length=1)
    fatigue_exposure_value: Nonnegative
    fatigue_exposure_unit_token: str = Field(min_length=1)
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_valid_block(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("creep-fatigue exposure blocks require positive duration")
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("creep-fatigue block temperatures must be ordered")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid creep-fatigue exposure block requires a basis")
        return self


class CreepFatigueProviderResult(Contract):
    result_record_id: str = Field(min_length=1)
    interaction_basis_id: str = Field(min_length=1)
    block_history_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_model_id: str = Field(min_length=1)
    provider_model_revision: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_metric_definition: str = Field(min_length=1)
    result_value: float
    result_unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    uncertainty_coverage_factor: Positive
    solution_state: str = Field(min_length=1)
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid creep-fatigue provider result requires a basis")
        return self


class CreepFatigueQualificationEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    partition: Partition
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    interaction_basis_id: str = Field(min_length=1)
    creep_exposure_definition: str = Field(min_length=1)
    creep_exposure_unit_token: str = Field(min_length=1)
    fatigue_exposure_definition: str = Field(min_length=1)
    fatigue_exposure_unit_token: str = Field(min_length=1)
    result_metric_definition: str = Field(min_length=1)
    result_unit_token: str = Field(min_length=1)
    observed_value: float
    predicted_value: float
    expanded_observation_uncertainty: Nonnegative
    uncertainty_coverage_factor: Positive
    provider_model_id: str = Field(min_length=1)
    provider_model_revision: str = Field(min_length=1)
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
            raise ValueError("invalid or limiting creep-fatigue evidence requires a basis")
        return self


class CreepFatigueInteractionEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    interaction_basis_id: str = Field(min_length=1)
    creep_exposure_definition: str = Field(min_length=1)
    creep_exposure_unit_token: str = Field(min_length=1)
    fatigue_exposure_definition: str = Field(min_length=1)
    fatigue_exposure_unit_token: str = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    supported_stress_history_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_strain_history_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_cycle_or_block_descriptors: tuple[str, ...] = Field(min_length=1)
    maximum_single_block_duration_s: Positive
    maximum_cumulative_duration_s: Positive
    provider_model_id: str = Field(min_length=1)
    provider_model_revision: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_metric_definition: str = Field(min_length=1)
    result_unit_token: str = Field(min_length=1)
    minimum_supported_result_value: float | None = None
    maximum_supported_result_value: float | None = None
    qualification_evidence: tuple[CreepFatigueQualificationEvidence, ...] = Field(min_length=1)
    minimum_calibration_source_group_count: int = Field(ge=1)
    minimum_holdout_source_group_count: int = Field(ge=1)
    minimum_holdout_independence_group_count: int = Field(ge=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("creep-fatigue temperature support must be ordered")
        if self.maximum_cumulative_duration_s < self.maximum_single_block_duration_s:
            raise ValueError("creep-fatigue cumulative duration cannot be below single-block duration")
        if (
            self.minimum_supported_result_value is not None
            and self.maximum_supported_result_value is not None
            and self.maximum_supported_result_value < self.minimum_supported_result_value
        ):
            raise ValueError("creep-fatigue provider-result support must be ordered")
        for values, name in (
            (self.supported_stress_history_descriptors, "stress-history"),
            (self.supported_strain_history_descriptors, "strain-history"),
            (self.supported_cycle_or_block_descriptors, "cycle/block"),
        ):
            if len(set(values)) != len(values) or any(not value.strip() for value in values):
                raise ValueError(f"creep-fatigue {name} descriptors must be unique and nonblank")
        evidence_ids = [row.evidence_record_id for row in self.qualification_evidence]
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("creep-fatigue qualification evidence identifiers must be unique")
        return self


class CreepFatigueInteractionProviderAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    interaction_basis_id: str = Field(min_length=1)
    creep_exposure_definition: str = Field(min_length=1)
    creep_exposure_unit_token: str = Field(min_length=1)
    fatigue_exposure_definition: str = Field(min_length=1)
    fatigue_exposure_unit_token: str = Field(min_length=1)
    exposure_blocks: tuple[CreepFatigueExposureBlock, ...] = Field(min_length=1)
    provider_result: CreepFatigueProviderResult
    candidate_envelopes: tuple[CreepFatigueInteractionEnvelope, ...] = Field(min_length=1)
    material_condition_and_physical_scope_reviewed: bool
    clock_block_order_and_history_digests_reviewed: bool
    temperature_stress_strain_and_cycle_descriptors_reviewed: bool
    separate_creep_and_fatigue_quantity_definitions_reviewed: bool
    interaction_basis_and_provider_model_reviewed: bool
    result_metric_units_and_uncertainty_reviewed: bool
    specimen_source_independence_and_partitions_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_envelope_authority_reviewed: bool

    @model_validator(mode="after")
    def unique_ordered_blocks(self):
        block_ids = [row.block_id for row in self.exposure_blocks]
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        if len(set(block_ids)) != len(block_ids):
            raise ValueError("creep-fatigue block identifiers must be unique")
        if len(set(envelope_ids)) != len(envelope_ids):
            raise ValueError("creep-fatigue envelope identifiers must be unique")
        for first, second in zip(self.exposure_blocks, self.exposure_blocks[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("creep-fatigue blocks must be ordered and cannot overlap")
        return self


def _identity(value) -> tuple[str, ...]:
    return (
        value.material_id,
        value.material_condition_id,
        value.interaction_basis_id,
        value.creep_exposure_definition,
        value.creep_exposure_unit_token,
        value.fatigue_exposure_definition,
        value.fatigue_exposure_unit_token,
    )


def creep_fatigue_interaction_provider_evidence(
    x: CreepFatigueInteractionProviderAssessment,
) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_condition_and_physical_scope_reviewed",
            "clock_block_order_and_history_digests_reviewed",
            "temperature_stress_strain_and_cycle_descriptors_reviewed",
            "separate_creep_and_fatigue_quantity_definitions_reviewed",
            "interaction_basis_and_provider_model_reviewed",
            "result_metric_units_and_uncertainty_reviewed",
            "specimen_source_independence_and_partitions_reviewed",
            "provider_lineage_and_digests_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_block_ids = [row.block_id for row in x.exposure_blocks if not row.record_valid]
    matches = [row for row in x.candidate_envelopes if _identity(row) == _identity(x)]
    if missing_reviews or invalid_block_ids or not x.provider_result.record_valid:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
                "missing_reviews": missing_reviews,
                "invalid_exposure_block_ids": invalid_block_ids,
                "provider_result_record_valid": x.provider_result.record_valid,
            },
            notes=("Invalid or unreviewed exposure and provider records are not qualified.",),
        )
    if not matches:
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "identity_matching_envelope_ids": []},
            notes=("No envelope has the exact material, interaction basis and exposure definitions.",),
        )

    envelope = matches[0]
    result = x.provider_result
    provider_identity_matches = (
        result.interaction_basis_id == envelope.interaction_basis_id
        and result.provider_model_id == envelope.provider_model_id
        and result.provider_model_revision == envelope.provider_model_revision
        and result.provider_id == envelope.provider_id
        and result.provider_revision == envelope.provider_revision
        and result.provider_configuration_digest == envelope.provider_configuration_digest
    )
    result_definition_and_unit_match = (
        result.result_metric_definition == envelope.result_metric_definition
        and result.result_unit_token == envelope.result_unit_token
    )
    block_quantity_mismatch_ids = [
        row.block_id
        for row in x.exposure_blocks
        if row.creep_exposure_definition != envelope.creep_exposure_definition
        or row.creep_exposure_unit_token != envelope.creep_exposure_unit_token
        or row.fatigue_exposure_definition != envelope.fatigue_exposure_definition
        or row.fatigue_exposure_unit_token != envelope.fatigue_exposure_unit_token
    ]
    invalid_evidence_ids = [
        row.evidence_record_id
        for row in envelope.qualification_evidence
        if not row.record_valid or not row.supports_declared_envelope
    ]
    mismatched_evidence_ids = []
    for row in envelope.qualification_evidence:
        if (
            row.material_condition_id != envelope.material_condition_id
            or row.interaction_basis_id != envelope.interaction_basis_id
            or row.creep_exposure_definition != envelope.creep_exposure_definition
            or row.creep_exposure_unit_token != envelope.creep_exposure_unit_token
            or row.fatigue_exposure_definition != envelope.fatigue_exposure_definition
            or row.fatigue_exposure_unit_token != envelope.fatigue_exposure_unit_token
            or row.result_metric_definition != envelope.result_metric_definition
            or row.result_unit_token != envelope.result_unit_token
            or row.provider_model_id != envelope.provider_model_id
            or row.provider_model_revision != envelope.provider_model_revision
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
        not provider_identity_matches
        or not result_definition_and_unit_match
        or block_quantity_mismatch_ids
        or invalid_evidence_ids
        or mismatched_evidence_ids
        or not partition_counts_sufficient
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "qualification_envelope_id": envelope.envelope_id,
                "provider_identity_matches": provider_identity_matches,
                "result_definition_and_unit_match": result_definition_and_unit_match,
                "block_quantity_definition_or_unit_mismatch_ids": block_quantity_mismatch_ids,
                "invalid_qualification_evidence_ids": invalid_evidence_ids,
                "qualification_evidence_identity_or_unit_mismatch_ids": mismatched_evidence_ids,
                "qualification_partition_counts_sufficient": partition_counts_sufficient,
            },
            notes=(
                "Exact interaction basis, quantity definitions, provider lineage and partitions are required.",
            ),
        )

    outside_block_ids = []
    cumulative_duration_s = 0.0
    block_comparisons = []
    for row in x.exposure_blocks:
        duration = row.end_time_s - row.start_time_s
        cumulative_duration_s += duration
        reasons = []
        if (
            row.minimum_temperature_K < envelope.minimum_temperature_K
            or row.maximum_temperature_K > envelope.maximum_temperature_K
        ):
            reasons.append("temperature_range")
        if row.stress_history_descriptor not in envelope.supported_stress_history_descriptors:
            reasons.append("stress_history_descriptor")
        if row.strain_history_descriptor not in envelope.supported_strain_history_descriptors:
            reasons.append("strain_history_descriptor")
        if row.cycle_or_block_descriptor not in envelope.supported_cycle_or_block_descriptors:
            reasons.append("cycle_or_block_descriptor")
        if duration > envelope.maximum_single_block_duration_s:
            reasons.append("block_duration")
        if reasons:
            outside_block_ids.append(row.block_id)
        block_comparisons.append(
            {"block_id": row.block_id, "duration_s": duration, "outside_support_reasons": reasons}
        )
    cumulative_duration_supported = cumulative_duration_s <= envelope.maximum_cumulative_duration_s
    result_within_support = not (
        envelope.minimum_supported_result_value is not None
        and result.result_value < envelope.minimum_supported_result_value
        or envelope.maximum_supported_result_value is not None
        and result.result_value > envelope.maximum_supported_result_value
    )
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "clock_id": x.clock_id,
        "qualification_envelope_id": envelope.envelope_id,
        "provider_result_record_id": result.result_record_id,
        "interaction_basis_id": result.interaction_basis_id,
        "provider_reported_result_value": result.result_value,
        "provider_reported_result_unit_token": result.result_unit_token,
        "block_comparisons": block_comparisons,
        "outside_support_block_ids": outside_block_ids,
        "cumulative_block_duration_s": cumulative_duration_s,
        "cumulative_duration_within_support": cumulative_duration_supported,
        "provider_result_within_support": result_within_support,
        "calibration_source_group_ids": sorted(calibration_groups),
        "holdout_source_group_ids": sorted(holdout_groups),
        "holdout_independence_group_ids": sorted(holdout_independence_groups),
    }
    notes = (
        "Creep and fatigue exposure quantities remain separate caller-defined inputs.",
        "The provider result is preserved without independent damage summation or a bundled interaction diagram.",
        "No remaining life, failure probability, acceptance or code compliance is produced.",
    )
    if outside_block_ids or not cumulative_duration_supported or not result_within_support:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_applicability_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("creep-fatigue assessment asset and location must match run context")

    return [
        ModelSpec(
            "structural.creep_fatigue_interaction_provider_evidence",
            CreepFatigueInteractionProviderAssessment,
            creep_fatigue_interaction_provider_evidence,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "clock_id": "1",
                "qualification_envelope_id": "1",
                "provider_result_record_id": "1",
                "interaction_basis_id": "1",
                "provider_reported_result_value": "provider unit",
                "provider_reported_result_unit_token": "1",
                "block_comparisons": "mixed",
                "outside_support_block_ids": "1",
                "cumulative_block_duration_s": "s",
                "cumulative_duration_within_support": "1",
                "provider_result_within_support": "1",
                "calibration_source_group_ids": "1",
                "holdout_source_group_ids": "1",
                "holdout_independence_group_ids": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Material, interaction basis and separate creep/fatigue quantity definitions match exactly.",
                "Ordered blocks preserve temperature, stress, strain, cycle descriptors and data digests.",
                "Provider evidence is not an independent damage sum, life, probability or acceptance result.",
            ),
            ("reviewed_creep_fatigue_interaction_provider_envelope",),
            context_validator=same_identity,
        )
    ]

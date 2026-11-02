"""Solidification-cracking applicability against caller-owned weld evidence."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class SolidificationCrackingTestEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    qualification_test_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    weld_metal_condition_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    consumable_classification_id: str = Field(min_length=1)
    chemistry_profile_id: str = Field(min_length=1)
    test_method_id: str = Field(min_length=1)
    result_definition: str = Field(min_length=1)
    result_value: float
    result_unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    uncertainty_coverage_factor: Positive
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
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
            raise ValueError("invalid or limiting solidification-cracking evidence requires a basis")
        return self


class SolidificationCrackingQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    weld_metal_condition_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    consumable_classification_id: str = Field(min_length=1)
    chemistry_basis_id: str = Field(min_length=1)
    supported_chemistry_profile_ids: tuple[str, ...] = Field(min_length=1)
    supported_thermal_history_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_strain_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_restraint_descriptors: tuple[str, ...] = Field(min_length=1)
    result_definition: str = Field(min_length=1)
    result_unit_token: str = Field(min_length=1)
    minimum_physical_specimen_count: int = Field(ge=1)
    minimum_source_group_count: int = Field(ge=1)
    test_evidence: tuple[SolidificationCrackingTestEvidence, ...] = Field(min_length=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_support_and_evidence(self):
        for values, name in (
            (self.supported_chemistry_profile_ids, "chemistry profile"),
            (self.supported_thermal_history_descriptors, "thermal-history descriptor"),
            (self.supported_strain_descriptors, "strain descriptor"),
            (self.supported_restraint_descriptors, "restraint descriptor"),
        ):
            if len(set(values)) != len(values) or any(not value.strip() for value in values):
                raise ValueError(f"supported {name} values must be unique and nonblank")
        identifiers = [row.evidence_record_id for row in self.test_evidence]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("solidification-cracking evidence identifiers must be unique")
        return self


class SolidificationCrackingApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    production_weld_id: str = Field(min_length=1)
    weld_metal_condition_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    consumable_classification_id: str = Field(min_length=1)
    consumable_lot_id: str = Field(min_length=1)
    chemistry_basis_id: str = Field(min_length=1)
    chemistry_profile_id: str = Field(min_length=1)
    thermal_history_descriptor: str = Field(min_length=1)
    strain_descriptor: str = Field(min_length=1)
    restraint_descriptor: str = Field(min_length=1)
    candidate_envelopes: tuple[SolidificationCrackingQualificationEnvelope, ...] = Field(min_length=1)
    weld_metal_process_and_consumable_reviewed: bool
    chemistry_identity_and_basis_reviewed: bool
    thermal_history_reviewed: bool
    strain_and_restraint_reviewed: bool
    specimen_and_source_group_partitions_reviewed: bool
    test_method_units_and_uncertainty_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_envelopes(self):
        identifiers = [row.envelope_id for row in self.candidate_envelopes]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("solidification-cracking envelope identifiers must be unique")
        identities = [_identity(row) for row in self.candidate_envelopes]
        if len(set(identities)) != len(identities):
            raise ValueError("solidification-cracking envelope identities must be unique")
        return self


def _identity(value) -> tuple[str, ...]:
    return (
        value.weld_metal_condition_id,
        value.welding_process_id,
        value.consumable_classification_id,
        value.chemistry_basis_id,
    )


def solidification_cracking_applicability(x: SolidificationCrackingApplicability) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "weld_metal_process_and_consumable_reviewed",
            "chemistry_identity_and_basis_reviewed",
            "thermal_history_reviewed",
            "strain_and_restraint_reviewed",
            "specimen_and_source_group_partitions_reviewed",
            "test_method_units_and_uncertainty_reviewed",
            "provider_lineage_and_digests_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    matches = [row for row in x.candidate_envelopes if _identity(row) == _identity(x)]
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
            },
            notes=("Applicability is withheld until production and evidence reviews are complete.",),
        )
    if not matches:
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": [],
                "identity_matching_envelope_ids": [],
            },
            notes=("No caller-owned envelope has the exact weld, process, consumable and chemistry basis.",),
        )

    envelope = matches[0]
    invalid_ids = [
        row.evidence_record_id
        for row in envelope.test_evidence
        if not row.record_valid or not row.supports_declared_envelope
    ]
    evidence_mismatches = []
    for row in envelope.test_evidence:
        fields = [
            field
            for field in (
                "weld_metal_condition_id",
                "welding_process_id",
                "consumable_classification_id",
            )
            if getattr(row, field) != getattr(envelope, field)
        ]
        if row.chemistry_profile_id not in envelope.supported_chemistry_profile_ids:
            fields.append("chemistry_profile_id")
        if row.result_definition != envelope.result_definition:
            fields.append("result_definition")
        if row.result_unit_token != envelope.result_unit_token:
            fields.append("result_unit_token")
        if fields:
            evidence_mismatches.append({"evidence_record_id": row.evidence_record_id, "fields": fields})
    specimen_ids = sorted({row.physical_specimen_id for row in envelope.test_evidence})
    source_group_ids = sorted({row.source_group_id for row in envelope.test_evidence})
    insufficient_partition_counts = (
        len(specimen_ids) < envelope.minimum_physical_specimen_count
        or len(source_group_ids) < envelope.minimum_source_group_count
    )
    if invalid_ids or evidence_mismatches or insufficient_partition_counts:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "qualification_envelope_id": envelope.envelope_id,
                "invalid_test_evidence_ids": invalid_ids,
                "test_evidence_identity_or_unit_mismatches": evidence_mismatches,
                "physical_specimen_ids": specimen_ids,
                "source_group_ids": source_group_ids,
                "evidence_partition_counts_sufficient": not insufficient_partition_counts,
            },
            notes=("Qualification evidence is incomplete, invalid or inconsistent with its envelope.",),
        )

    outside_reasons = []
    for value, supported, name in (
        (x.chemistry_profile_id, envelope.supported_chemistry_profile_ids, "chemistry_profile_id"),
        (
            x.thermal_history_descriptor,
            envelope.supported_thermal_history_descriptors,
            "thermal_history_descriptor",
        ),
        (x.strain_descriptor, envelope.supported_strain_descriptors, "strain_descriptor"),
        (x.restraint_descriptor, envelope.supported_restraint_descriptors, "restraint_descriptor"),
    ):
        if value not in supported:
            outside_reasons.append(name)
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "production_weld_id": x.production_weld_id,
        "consumable_lot_id": x.consumable_lot_id,
        "qualification_envelope_id": envelope.envelope_id,
        "outside_support_reasons": outside_reasons,
        "physical_specimen_ids": specimen_ids,
        "source_group_ids": source_group_ids,
        "test_evidence_record_ids": [row.evidence_record_id for row in envelope.test_evidence],
    }
    notes = (
        "The result compares caller-reviewed identities and descriptors with a caller-owned qualification envelope.",
        "No proprietary composition limit, cracking index, acceptance rule or design table is bundled.",
        "No crack initiation, extent, probability, remaining life or welding acceptance is inferred.",
    )
    if outside_reasons:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_applicability_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("solidification-cracking assessment asset and location must match run context")

    return [
        ModelSpec(
            "welding.solidification_cracking_applicability",
            SolidificationCrackingApplicability,
            solidification_cracking_applicability,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "production_weld_id": "1",
                "consumable_lot_id": "1",
                "qualification_envelope_id": "1",
                "outside_support_reasons": "1",
                "physical_specimen_ids": "1",
                "source_group_ids": "1",
                "test_evidence_record_ids": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Weld-metal condition, process, consumable classification and chemistry basis match exactly.",
                "Thermal, strain and restraint descriptors are caller-defined tokens and are not inferred.",
                "Test records demonstrate only declared envelope support, not cracking probability or acceptance.",
            ),
            ("reviewed_solidification_cracking_qualification_envelope",),
            context_validator=same_identity,
        )
    ]

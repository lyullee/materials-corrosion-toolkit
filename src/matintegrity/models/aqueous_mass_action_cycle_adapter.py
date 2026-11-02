"""Bind the mass-action system contract to the standalone reaction-cycle audit."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Positive, canonical_digest
from ..registry import ModelSpec
from .aqueous_mass_action import AqueousMassActionSystem
from .aqueous_thermodynamic_cycle_audit import (
    AqueousCycleReaction,
    AqueousCycleSpecies,
    AqueousThermodynamicCycleAudit,
    aqueous_thermodynamic_cycle_audit,
)


class AqueousReactionEvidenceBinding(Contract):
    reaction_id: str = Field(min_length=1)
    evidence_source_id: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class AqueousMassActionCycleAuditBinding(Contract):
    adapter_id: str = Field(min_length=1)
    system: AqueousMassActionSystem
    reaction_evidence_bindings: tuple[AqueousReactionEvidenceBinding, ...] = Field(min_length=1, max_length=100)
    stoichiometric_balance_tolerance: Positive = Field(default=1e-10, le=1e-4)
    rank_relative_tolerance: Positive = Field(default=1e-12, le=1e-3)
    cycle_closure_tolerance_log10: Positive = Field(default=1e-8, le=1.0)
    numerical_rank_and_cycle_tolerance_reviewed: bool
    evidence_and_usage_rights_reviewed: bool

    @model_validator(mode="after")
    def exact_reaction_binding_coverage(self):
        expected = [row.reaction_id for row in self.system.reactions]
        supplied = [row.reaction_id for row in self.reaction_evidence_bindings]
        if len(supplied) != len(set(supplied)) or set(supplied) != set(expected):
            raise ValueError("reaction evidence bindings must cover the system reactions exactly once")
        return self


def aqueous_mass_action_cycle_audit_adapter(x: AqueousMassActionCycleAuditBinding) -> Calculation:
    """Reuse one caller mass-action network without duplicating its chemistry inputs."""
    system = x.system
    system_digest = canonical_digest(system.model_dump(mode="json"))
    base = {
        "adapter_id": x.adapter_id,
        "mass_action_system_input_sha256": system_digest,
        "mass_action_system_id": system.assessment_id,
        "solution_id": system.solution_id,
        "temperature_K": system.temperature_K,
        "equilibrium_provider_id": system.equilibrium_provider_id,
        "equilibrium_provider_revision": system.equilibrium_provider_revision,
        "equilibrium_configuration_digest": system.equilibrium_configuration_digest,
        "equilibrium_record_digest": system.equilibrium_record_digest,
    }
    missing_reviews = [
        name
        for name, reviewed in (
            ("complete_aqueous_species_inventory_reviewed", system.complete_aqueous_species_inventory_reviewed),
            ("reaction_stoichiometry_and_constant_reviewed", system.reaction_stoichiometry_and_constant_reviewed),
            ("elemental_formula_and_reaction_balance_reviewed", system.elemental_formula_and_reaction_balance_reviewed),
            ("temperature_and_provider_lineage_reviewed", system.temperature_and_provider_lineage_reviewed),
            ("numerical_rank_and_cycle_tolerance_reviewed", x.numerical_rank_and_cycle_tolerance_reviewed),
            ("evidence_and_usage_rights_reviewed", x.evidence_and_usage_rights_reviewed),
        )
        if not reviewed
    ]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing_reviews})
    if any(not row.elemental_composition for row in system.species):
        return Calculation(status="needs_data", values=base | {
            "reason": "mass_action_system_lacks_complete_elemental_formulas",
        })
    evidence_by_id = {row.source_id: row for row in system.evidence}
    if len(evidence_by_id) != len(system.evidence):
        return Calculation(status="needs_data", values=base | {
            "reason": "mass_action_system_evidence_source_ids_are_ambiguous",
        })
    binding_by_reaction = {row.reaction_id: row for row in x.reaction_evidence_bindings}
    mismatches = []
    for reaction in system.reactions:
        binding = binding_by_reaction[reaction.reaction_id]
        evidence = evidence_by_id.get(binding.evidence_source_id)
        if evidence is None or evidence.sha256 != binding.evidence_sha256:
            mismatches.append(reaction.reaction_id)
    if mismatches:
        return Calculation(status="needs_data", values=base | {
            "reaction_evidence_mismatch_ids": mismatches,
        })
    missing_licenses = [
        row.source_id
        for row in system.evidence
        if row.origin == "open_dataset" and not (row.license_id and row.license_id.strip())
    ]
    if missing_licenses:
        return Calculation(status="needs_data", values=base | {
            "open_dataset_evidence_missing_license_ids": missing_licenses,
        })
    cycle_input = AqueousThermodynamicCycleAudit(
        schema_version="matintegrity.aqueous_thermodynamic_cycle_audit.v1",
        audit_id=x.adapter_id,
        temperature_K=system.temperature_K,
        activity_standard_state=system.activity_standard_state,
        parameter_provider_id=system.equilibrium_provider_id,
        parameter_provider_revision=system.equilibrium_provider_revision,
        species=tuple(
            AqueousCycleSpecies(
                species_id=row.species_id,
                charge_number=row.charge_number,
                elemental_composition=row.elemental_composition,
            )
            for row in system.species
        ),
        reactions=tuple(
            AqueousCycleReaction(
                reaction_id=row.reaction_id,
                log10_equilibrium_constant=row.log10_equilibrium_constant,
                terms=row.terms,
                evidence_source_id=binding_by_reaction[row.reaction_id].evidence_source_id,
                source_record_id=binding_by_reaction[row.reaction_id].source_record_id,
                evidence_sha256=binding_by_reaction[row.reaction_id].evidence_sha256,
            )
            for row in system.reactions
        ),
        evidence=system.evidence,
        stoichiometric_balance_tolerance=x.stoichiometric_balance_tolerance,
        rank_relative_tolerance=x.rank_relative_tolerance,
        cycle_closure_tolerance_log10=x.cycle_closure_tolerance_log10,
        complete_species_inventory_reviewed=system.complete_aqueous_species_inventory_reviewed,
        elemental_formula_and_stoichiometry_reviewed=system.elemental_formula_and_reaction_balance_reviewed,
        equilibrium_constant_conditions_reviewed=(
            system.reaction_stoichiometry_and_constant_reviewed
            and system.temperature_and_provider_lineage_reviewed
        ),
        numerical_rank_and_cycle_tolerance_reviewed=x.numerical_rank_and_cycle_tolerance_reviewed,
        evidence_and_usage_rights_reviewed=x.evidence_and_usage_rights_reviewed,
    )
    calculation = aqueous_thermodynamic_cycle_audit(cycle_input)
    return Calculation(
        status=calculation.status,
        values=base | {
            "cycle_audit_input_sha256": canonical_digest(cycle_input.model_dump(mode="json")),
            "cycle_audit": calculation.values,
        },
        notes=(
            "The adapter reuses the exact caller AqueousMassActionSystem chemistry and verifies complete reaction-specific source bindings before cycle analysis.",
            *calculation.notes,
        ),
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.aqueous_mass_action_cycle_audit",
        AqueousMassActionCycleAuditBinding,
        aqueous_mass_action_cycle_audit_adapter,
        {
            "temperature_K": "K",
            "cycle_audit.reaction_balance[].charge_balance_residual": "1",
            "cycle_audit.cycle_closure_residual_l2_log10": "1",
            "cycle_audit.reaction_cycle_basis[].log10_equilibrium_cycle_residual": "1",
        },
        (
            "The existing mass-action species, formulas, charges, reaction direction, log10(K), temperature and standard state are reused without chemical reinterpretation.",
            "Each reaction receives exactly one source record binding, and its declared Evidence source ID and file hash must match.",
            "Cycle rank and closure are diagnostics only; no reaction/phase discovery, speciation solve, parameter correction or corrosion qualification is performed.",
        ),
        ("aqueous_mass_action_reaction_cycle_audit_adapter", "aqueous_reaction_cycle_nullspace_consistency"),
        qualification="user_model",
    )]

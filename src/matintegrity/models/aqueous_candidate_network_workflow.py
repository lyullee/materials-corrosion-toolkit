"""Lineage-preserving composition of explicit aqueous candidate-network steps."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, canonical_digest
from ..registry import ModelSpec
from .aqueous_mass_action import (
    AqueousCandidateReactionBindingRequest,
    AqueousMassActionSystemAssemblyRequest,
    AqueousReactionCandidateEnumeration,
    assemble_aqueous_mass_action_system,
    bind_aqueous_candidate_reactions,
    enumerate_aqueous_reaction_candidates,
)


class AqueousCandidateNetworkWorkflow(Contract):
    """Explicit three-step workflow, retaining human thermodynamic selection."""

    workflow_id: str = Field(min_length=1)
    enumeration: AqueousReactionCandidateEnumeration
    binding: AqueousCandidateReactionBindingRequest
    assembly: AqueousMassActionSystemAssemblyRequest

    @model_validator(mode="after")
    def exact_species_temperature_and_standard_state(self):
        enum_species = {row.species_id: row for row in self.enumeration.species}
        assembly_species = {row.species_id: row for row in self.assembly.species}
        if set(enum_species) != set(assembly_species):
            raise ValueError("candidate enumeration and mass-action assembly must use the identical species set")
        for species_id, candidate in enum_species.items():
            assembly_row = assembly_species[species_id]
            if (candidate.charge_number != assembly_row.charge_number
                    or candidate.elemental_composition != assembly_row.elemental_composition):
                raise ValueError(f"candidate formula/charge differs from assembled species {species_id}")
        expected_enumeration_digest = canonical_digest(self.enumeration.model_dump(mode="json"))
        if self.binding.candidate_enumeration_input_sha256 != expected_enumeration_digest:
            raise ValueError("binding request must pin this exact candidate enumeration input")
        if abs(self.binding.target_mass_action_temperature_K - self.assembly.temperature_K) > self.binding.temperature_match_tolerance_K:
            raise ValueError("candidate equilibrium data temperature does not match assembly temperature support")
        if self.binding.target_activity_standard_state != self.assembly.activity_standard_state:
            raise ValueError("candidate binding and assembly activity standard states differ")
        return self


def assemble_aqueous_candidate_network_workflow(x: AqueousCandidateNetworkWorkflow) -> Calculation:
    """Run enumeration, evidence-backed manual binding and strict system assembly."""
    workflow_digest = canonical_digest(x.model_dump(mode="json"))
    enumeration = enumerate_aqueous_reaction_candidates(x.enumeration)
    if enumeration.status != "computed":
        return _stopped_workflow(x, workflow_digest, "enumeration", enumeration)
    binding = bind_aqueous_candidate_reactions(enumeration, x.binding)
    if binding.status != "computed":
        return _stopped_workflow(x, workflow_digest, "binding", binding, enumeration)
    assembly = assemble_aqueous_mass_action_system(binding, x.assembly)
    values = {
        "workflow_id": x.workflow_id,
        "workflow_sha256": workflow_digest,
        "stopped_stage": None if assembly.status == "computed" else "assembly",
        "completed_stages": ["enumeration", "binding", "assembly"] if assembly.status == "computed" else ["enumeration", "binding"],
        "unexecuted_stages": [],
        "failed_stage_result_sha256": None if assembly.status == "computed" else canonical_digest(assembly.model_dump(mode="json")),
        "enumeration_input_sha256": canonical_digest(x.enumeration.model_dump(mode="json")),
        "enumeration_result_sha256": canonical_digest(enumeration.model_dump(mode="json")),
        "binding_input_sha256": canonical_digest(x.binding.model_dump(mode="json")),
        "binding_result_sha256": canonical_digest(binding.model_dump(mode="json")),
        "assembly_input_sha256": canonical_digest(x.assembly.model_dump(mode="json")),
        "assembly_result_sha256": canonical_digest(assembly.model_dump(mode="json")),
        "enumeration": enumeration.model_dump(mode="json"),
        "binding": binding.model_dump(mode="json"),
        "assembly": assembly.model_dump(mode="json"),
        "workflow_scope": (
            "bounded stoichiometric candidate enumeration followed by caller-selected, evidence-backed equilibrium "
            "constants and strict single-phase mass-action system assembly; no reaction or phase is automatically selected"
        ),
    }
    return Calculation(status=assembly.status, values=values, notes=(
        "This adapter composes existing bounded contracts and preserves every stage digest; it does not infer chemical feasibility, missing species, phase stability, equilibrium constants or kinetics.",
        "The returned system is an assembly artifact. A separate explicitly parameterized speciation calculation is required to solve for activities.",
    ))


def _stopped_workflow(
    x: AqueousCandidateNetworkWorkflow,
    workflow_digest: str,
    stage: str,
    failure: Calculation,
    enumeration: Calculation | None = None,
) -> Calculation:
    """Preserve the originating failure without executing dependent stages."""
    values = {
        "workflow_id": x.workflow_id,
        "workflow_sha256": workflow_digest,
        "stopped_stage": stage,
        "completed_stages": [] if stage == "enumeration" else ["enumeration"],
        "enumeration_input_sha256": canonical_digest(x.enumeration.model_dump(mode="json")),
        "enumeration_result_sha256": canonical_digest((enumeration if enumeration is not None else failure).model_dump(mode="json")),
        "binding_input_sha256": canonical_digest(x.binding.model_dump(mode="json")),
        "binding_result_sha256": canonical_digest(failure.model_dump(mode="json")) if stage == "binding" else None,
        "assembly_input_sha256": canonical_digest(x.assembly.model_dump(mode="json")),
        "assembly_result_sha256": None,
        "enumeration": (enumeration or failure).model_dump(mode="json"),
        "binding": failure.model_dump(mode="json") if stage == "binding" else None,
        "assembly": None,
        "failed_stage_result_sha256": canonical_digest(failure.model_dump(mode="json")),
        "unexecuted_stages": ["binding", "assembly"] if stage == "enumeration" else ["assembly"],
    }
    return Calculation(status=failure.status, values=values, notes=(
        "The workflow stopped at the first incomplete stage; dependent binding or assembly was not executed and no assembled system is available.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.aqueous_candidate_network_workflow",
        AqueousCandidateNetworkWorkflow,
        assemble_aqueous_candidate_network_workflow,
        {"candidate_reaction_count": "1", "reaction_count": "1"},
        (
            "A caller-defined closed candidate species inventory and formula/charge set is screened with explicit search budgets.",
            "Reaction selections, direction, equilibrium records, temperature match, constraints, activity coefficients and phase scope remain caller supplied and evidence bound.",
            "The workflow assembles but does not solve, discover phases, infer kinetics, or qualify wet-CO2 corrosion.",
        ),
        ("caller_composed_aqueous_candidate_network_workflow",),
        qualification="user_model",
    )]

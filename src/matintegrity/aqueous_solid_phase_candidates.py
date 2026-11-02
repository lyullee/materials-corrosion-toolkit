"""Bounded stoichiometric screening for caller-proposed aqueous solid phases.

This module can enumerate balanced reaction proposals only after the caller
supplies and reviews phase formulas and a closed species inventory. It does
not discover minerals, assign stability, select phases, or estimate Ksp.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .models.aqueous_mass_action import (
    AqueousReactionCandidateEnumeration,
    AqueousReactionCandidateSpecies,
    enumerate_aqueous_reaction_candidates,
)


class AqueousSolidPhaseCandidateEnumeration(Contract):
    """Enumerate charge/element-balanced proposals for caller-listed solids."""

    schema_version: Literal["matintegrity.aqueous_solid_phase_candidates.v1"] = (
        "matintegrity.aqueous_solid_phase_candidates.v1"
    )
    enumeration_id: str = Field(min_length=1)
    aqueous_species: tuple[AqueousReactionCandidateSpecies, ...] = Field(min_length=2, max_length=11)
    proposed_solid_phases: tuple[AqueousReactionCandidateSpecies, ...] = Field(min_length=1, max_length=11)
    maximum_total_stoichiometric_order: int = Field(default=4, ge=2, le=8)
    maximum_side_multisets: int = Field(default=250_000, ge=1, le=2_000_000)
    maximum_candidate_pair_checks: int = Field(default=250_000, ge=1, le=2_000_000)
    maximum_candidate_reactions: int = Field(default=50_000, ge=1, le=100_000)
    species_formula_and_charge_reviewed: bool
    closed_aqueous_and_solid_inventory_reviewed: bool
    candidate_use_and_manual_phase_selection_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_inventory(self):
        all_species = (*self.aqueous_species, *self.proposed_solid_phases)
        if len(all_species) > 12:
            raise ValueError("the combined candidate inventory is limited to twelve species")
        ids = [row.species_id for row in all_species]
        if len(ids) != len(set(ids)):
            raise ValueError("aqueous and proposed solid species IDs must be globally unique")
        for phase in self.proposed_solid_phases:
            if phase.charge_number != 0:
                raise ValueError("proposed bulk solid phases must have declared zero net charge")
        AqueousReactionCandidateEnumeration(
            enumeration_id=self.enumeration_id,
            species=all_species,
            maximum_total_stoichiometric_order=self.maximum_total_stoichiometric_order,
            maximum_side_multisets=self.maximum_side_multisets,
            maximum_candidate_pair_checks=self.maximum_candidate_pair_checks,
            maximum_candidate_reactions=self.maximum_candidate_reactions,
            species_formula_and_charge_reviewed=self.species_formula_and_charge_reviewed,
            closed_candidate_species_inventory_reviewed=self.closed_aqueous_and_solid_inventory_reviewed,
            candidate_use_and_manual_selection_reviewed=self.candidate_use_and_manual_phase_selection_reviewed,
            evidence=self.evidence,
        )
        return self


def enumerate_aqueous_solid_phase_candidates(
    request: AqueousSolidPhaseCandidateEnumeration,
) -> Calculation:
    """Return balanced solid-dissolution proposals for manual thermodynamic review.

    The caller provides every aqueous species and proposed solid formula. The
    underlying bounded integer enumerator is reused, then reactions are kept
    only when one proposed solid appears alone on one side and aqueous species
    appear on the other. No phase is selected or declared stable by this scan.
    """
    input_sha256 = canonical_digest(request.model_dump(mode="json"))
    missing = [
        name for name, checked in (
            ("species_formula_and_charge_reviewed", request.species_formula_and_charge_reviewed),
            ("closed_aqueous_and_solid_inventory_reviewed", request.closed_aqueous_and_solid_inventory_reviewed),
            ("candidate_use_and_manual_phase_selection_reviewed", request.candidate_use_and_manual_phase_selection_reviewed),
        ) if not checked
    ]
    base = {
        "enumeration_id": request.enumeration_id,
        "input_sha256": input_sha256,
        "aqueous_species_ids": [row.species_id for row in request.aqueous_species],
        "caller_proposed_solid_phase_ids": [row.species_id for row in request.proposed_solid_phases],
        "phase_formulae_inferred": False,
        "phase_stability_assessed": False,
        "equilibrium_constants_assigned": False,
        "manual_phase_selection_required": True,
    }
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    combined = (*request.aqueous_species, *request.proposed_solid_phases)
    scan = enumerate_aqueous_reaction_candidates(AqueousReactionCandidateEnumeration(
        enumeration_id=request.enumeration_id,
        species=combined,
        maximum_total_stoichiometric_order=request.maximum_total_stoichiometric_order,
        maximum_side_multisets=request.maximum_side_multisets,
        maximum_candidate_pair_checks=request.maximum_candidate_pair_checks,
        maximum_candidate_reactions=request.maximum_candidate_reactions,
        species_formula_and_charge_reviewed=True,
        closed_candidate_species_inventory_reviewed=True,
        candidate_use_and_manual_selection_reviewed=True,
        evidence=request.evidence,
    ))
    if scan.status != "computed":
        return Calculation(status=scan.status, values=base | {
            "stoichiometric_scan_status": scan.status,
            "stoichiometric_scan": scan.values,
            "phase_candidates": [],
            "partial_catalog_returned": False,
        }, notes=scan.notes)

    aqueous_ids = {row.species_id for row in request.aqueous_species}
    solid_ids = {row.species_id for row in request.proposed_solid_phases}
    phase_candidates = []
    for reaction in scan.values["candidate_reactions"]:
        left_solids = [term for term in reaction["reactants"] if term["species_id"] in solid_ids]
        right_solids = [term for term in reaction["products"] if term["species_id"] in solid_ids]
        if (len(left_solids) + len(right_solids)) != 1:
            continue
        solid_term = (left_solids or right_solids)[0]
        if solid_term["coefficient"] != 1:
            continue
        other_side = reaction["products"] if left_solids else reaction["reactants"]
        if not other_side or any(term["species_id"] not in aqueous_ids for term in other_side):
            continue
        # Normalize the proposal as solid -> aqueous dissolution, regardless
        # of the direction-neutral base enumerator's lexical side ordering.
        dissolution = {
            "solid": {"species_id": solid_term["species_id"], "coefficient": 1},
            "aqueous_products": sorted(other_side, key=lambda term: term["species_id"]),
            "balanced_elements": reaction["balanced_elements"],
            "charge_stoichiometric_residual": 0,
        }
        digest = canonical_digest(dissolution)
        phase_candidates.append(dissolution | {
            "candidate_id": f"solid-dissolution:{digest[:24]}",
            "candidate_sha256": digest,
            "base_stoichiometric_candidate_sha256": reaction["candidate_sha256"],
        })
    phase_candidates.sort(key=lambda row: (row["solid"]["species_id"], row["candidate_sha256"]))
    return Calculation(status="computed", values=base | {
        "stoichiometric_scan_input_sha256": scan.values["input_sha256"],
        "stoichiometric_candidate_count": scan.values["candidate_reaction_count"],
        "phase_candidate_count": len(phase_candidates),
        "phase_candidates": phase_candidates,
        "enumeration_complete_within_declared_species_and_order": True,
    }, notes=(
        "This is a bounded stoichiometric screen over caller-proposed neutral solids and a caller-closed aqueous inventory. It neither generates phase formulas nor determines whether a balanced dissolution is chemically plausible or stable.",
        "Each result needs manual phase/reaction selection and an independently sourced, temperature- and standard-state-compatible equilibrium record before mass-action use.",
    ))

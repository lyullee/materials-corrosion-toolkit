"""Synthetic wiring example for caller-proposed solid phase proposals."""

from matintegrity.aqueous_solid_phase_candidates import (
    AqueousSolidPhaseCandidateEnumeration,
    enumerate_aqueous_solid_phase_candidates,
)
from matintegrity.models.aqueous_mass_action import AqueousReactionCandidateSpecies
from matintegrity.contracts import Evidence

request = AqueousSolidPhaseCandidateEnumeration(
    enumeration_id="synthetic-calcium-carbonate-proposals",
    aqueous_species=(
        AqueousReactionCandidateSpecies(
            species_id="calcium_ion", charge_number=2, elemental_composition={"Ca": 1}
        ),
        AqueousReactionCandidateSpecies(
            species_id="carbonate_ion", charge_number=-2, elemental_composition={"C": 1, "O": 3}
        ),
        AqueousReactionCandidateSpecies(
            species_id="bicarbonate_ion", charge_number=-1,
            elemental_composition={"H": 1, "C": 1, "O": 3},
        ),
    ),
    proposed_solid_phases=(
        AqueousReactionCandidateSpecies(
            species_id="caller_proposed_CaCO3_solid", charge_number=0,
            elemental_composition={"Ca": 1, "C": 1, "O": 3},
        ),
    ),
    maximum_total_stoichiometric_order=4,
    maximum_side_multisets=250_000,
    maximum_candidate_pair_checks=250_000,
    maximum_candidate_reactions=50_000,
    species_formula_and_charge_reviewed=True,
    closed_aqueous_and_solid_inventory_reviewed=True,
    candidate_use_and_manual_phase_selection_reviewed=True,
    evidence=(Evidence(
        source_id="synthetic-phase-candidate-example",
        origin="synthetic",
        citation="Invented stoichiometric input used only to illustrate API wiring",
    ),),
)

result = enumerate_aqueous_solid_phase_candidates(request)
print(result.model_dump(mode="json"))

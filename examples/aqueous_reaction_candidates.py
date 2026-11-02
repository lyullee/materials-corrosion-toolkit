"""Synthetic wiring example for bounded atom/charge-balanced reaction candidates."""

from matintegrity.models.aqueous_mass_action import (
    AqueousReactionCandidateEnumeration,
    enumerate_aqueous_reaction_candidates,
)

request = AqueousReactionCandidateEnumeration.model_validate({
    "enumeration_id": "synthetic-water-ionization-candidates",
    "species": [
        {"species_id": "water", "charge_number": 0, "elemental_composition": {"H": 2, "O": 1}},
        {"species_id": "proton", "charge_number": 1, "elemental_composition": {"H": 1}},
        {"species_id": "hydroxide", "charge_number": -1, "elemental_composition": {"H": 1, "O": 1}},
        {"species_id": "hydronium", "charge_number": 1, "elemental_composition": {"H": 3, "O": 1}},
    ],
    "maximum_total_stoichiometric_order": 4,
    "maximum_side_multisets": 250_000,
    "maximum_candidate_pair_checks": 250_000,
    "maximum_candidate_reactions": 50_000,
    "species_formula_and_charge_reviewed": True,
    "closed_candidate_species_inventory_reviewed": True,
    "candidate_use_and_manual_selection_reviewed": True,
    "evidence": [{
        "source_id": "synthetic_reaction_candidate_example",
        "origin": "synthetic",
        "citation": "Invented species used only to demonstrate API wiring",
    }],
})
result = enumerate_aqueous_reaction_candidates(request)
print(result.model_dump(mode="json"))

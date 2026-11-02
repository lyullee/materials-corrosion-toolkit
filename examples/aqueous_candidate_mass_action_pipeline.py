"""Synthetic wiring example: balance candidates -> reviewed binding -> strict solver input.

This example defines arbitrary inputs only to illustrate API composition. It has
not been numerically executed or qualified as a chemical system.
"""

from matintegrity.contracts import Evidence
from matintegrity.models.aqueous_mass_action import (
    AqueousActivitySpecies,
    AqueousCandidateReactionBindingRequest,
    AqueousCandidateReactionSelection,
    AqueousLinearConstraint,
    AqueousMassActionSystemAssemblyRequest,
    AqueousReactionCandidateEnumeration,
    AqueousReactionCandidateSpecies,
    AqueousStoichiometricTerm,
    assemble_aqueous_mass_action_system,
    bind_aqueous_candidate_reactions,
    enumerate_aqueous_reaction_candidates,
)


candidate_request = AqueousReactionCandidateEnumeration(
    enumeration_id="synthetic-hydration-reaction-candidates",
    species=(
        AqueousReactionCandidateSpecies(
            species_id="water", charge_number=0, elemental_composition={"H": 2, "O": 1}
        ),
        AqueousReactionCandidateSpecies(
            species_id="proton", charge_number=1, elemental_composition={"H": 1}
        ),
        AqueousReactionCandidateSpecies(
            species_id="hydronium", charge_number=1, elemental_composition={"H": 3, "O": 1}
        ),
        AqueousReactionCandidateSpecies(
            species_id="chloride", charge_number=-1, elemental_composition={"Cl": 1}
        ),
    ),
    maximum_total_stoichiometric_order=3,
    species_formula_and_charge_reviewed=True,
    closed_candidate_species_inventory_reviewed=True,
    candidate_use_and_manual_selection_reviewed=True,
    evidence=(Evidence(
        source_id="synthetic-stoichiometry-example",
        origin="synthetic",
        citation="API wiring fixture only; no chemical recommendation",
    ),),
)
candidate_result = enumerate_aqueous_reaction_candidates(candidate_request)

expected_reactants = {"water": 1, "proton": 1}
expected_products = {"hydronium": 1}
candidate = next(
    row for row in candidate_result.values["candidate_reactions"]
    if (
        {term["species_id"]: term["coefficient"] for term in row["reactants"]} == expected_reactants
        and {term["species_id"]: term["coefficient"] for term in row["products"]} == expected_products
    ) or (
        {term["species_id"]: term["coefficient"] for term in row["reactants"]} == expected_products
        and {term["species_id"]: term["coefficient"] for term in row["products"]} == expected_reactants
    )
)
direction = (
    "candidate_forward"
    if {term["species_id"]: term["coefficient"] for term in candidate["reactants"]} == expected_reactants
    else "candidate_reverse"
)
equilibrium_sha = "a" * 64
binding_request = AqueousCandidateReactionBindingRequest(
    binding_id="synthetic-equilibrium-binding",
    candidate_enumeration_input_sha256=candidate_result.values["input_sha256"],
    target_mass_action_temperature_K=298.15,
    target_activity_standard_state="molarity_1_mol_L",
    selections=(AqueousCandidateReactionSelection(
        candidate_id=candidate["candidate_id"],
        candidate_sha256=candidate["candidate_sha256"],
        reaction_id="caller-selected-hydration-reaction",
        direction=direction,
        log10_equilibrium_constant=-2.0,
        temperature_K=298.15,
        equilibrium_parameter_set_id="synthetic-K-record",
        equilibrium_record_id="synthetic-record-1",
        equilibrium_record_sha256=equilibrium_sha,
    ),),
    reaction_selection_and_constant_reviewed=True,
    evidence=(Evidence(
        source_id="synthetic-K-record",
        origin="synthetic",
        citation="Invented record identifier for input wiring only",
        sha256=equilibrium_sha,
    ),),
)
binding_result = bind_aqueous_candidate_reactions(candidate_result, binding_request)

species = (
    AqueousActivitySpecies(
        species_id="water", charge_number=0, activity_coefficient=1.0,
        initial_activity=0.5, elemental_composition={"H": 2, "O": 1},
    ),
    AqueousActivitySpecies(
        species_id="proton", charge_number=1, activity_coefficient=1.0,
        initial_activity=0.2, elemental_composition={"H": 1},
    ),
    AqueousActivitySpecies(
        species_id="hydronium", charge_number=1, activity_coefficient=1.0,
        initial_activity=0.1, elemental_composition={"H": 3, "O": 1},
    ),
    AqueousActivitySpecies(
        species_id="chloride", charge_number=-1, activity_coefficient=1.0,
        initial_activity=0.3, elemental_composition={"Cl": 1},
    ),
)
assembly_request = AqueousMassActionSystemAssemblyRequest(
    assessment_id="synthetic-aqueous-assembly",
    solution_id="synthetic-solution",
    temperature_K=298.15,
    activity_standard_state="molarity_1_mol_L",
    species=species,
    constraints=(
        AqueousLinearConstraint(
            constraint_id="total-hydrogen",
            target_mol_L=1.5,
            residual_scale_mol_L=1.0,
            terms=(
                AqueousStoichiometricTerm(species_id="water", coefficient=2.0),
                AqueousStoichiometricTerm(species_id="proton", coefficient=1.0),
                AqueousStoichiometricTerm(species_id="hydronium", coefficient=3.0),
            ),
        ),
        AqueousLinearConstraint(
            constraint_id="total-chloride",
            target_mol_L=0.3,
            residual_scale_mol_L=1.0,
            terms=(AqueousStoichiometricTerm(species_id="chloride", coefficient=1.0),),
        ),
        AqueousLinearConstraint(
            constraint_id="charge-balance",
            target_mol_L=0.0,
            residual_scale_mol_L=1.0,
            terms=(
                AqueousStoichiometricTerm(species_id="proton", coefficient=1.0),
                AqueousStoichiometricTerm(species_id="hydronium", coefficient=1.0),
                AqueousStoichiometricTerm(species_id="chloride", coefficient=-1.0),
            ),
        ),
    ),
    activity_provider_id="synthetic-ideal-activity",
    activity_provider_revision="1",
    activity_configuration_digest="b" * 64,
    activity_record_digest="c" * 64,
    equilibrium_provider_id="synthetic-equilibrium-provider",
    equilibrium_provider_revision="1",
    equilibrium_configuration_digest="d" * 64,
    complete_aqueous_species_inventory_reviewed=True,
    reaction_stoichiometry_and_constant_reviewed=True,
    balance_constraints_and_charge_scope_reviewed=True,
    fixed_activity_coefficients_and_standard_state_reviewed=True,
    temperature_and_provider_lineage_reviewed=True,
    initial_activity_guess_and_solver_tolerance_reviewed=True,
    single_liquid_phase_and_no_precipitation_reviewed=True,
    elemental_formula_and_reaction_balance_reviewed=True,
    evidence=(
        Evidence(
            source_id="synthetic-activity-record",
            origin="synthetic",
            citation="Invented activity record for input wiring only",
            sha256="c" * 64,
        ),
        *binding_request.evidence,
    ),
)
assembly_result = assemble_aqueous_mass_action_system(binding_result, assembly_request)
print(assembly_result.model_dump(mode="json"))

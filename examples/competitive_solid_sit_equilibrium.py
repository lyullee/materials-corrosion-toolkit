"""Synthetic wiring example for caller-parameterized SIT/solid equilibrium."""

from matintegrity.models.competitive_solid_sit_iteration import (
    CompetitiveSolidSITIteration,
    competitive_solid_sit_self_consistent_equilibrium,
)

SIT_EVIDENCE_SHA256 = "a" * 64

request = CompetitiveSolidSITIteration.model_validate({
    "equilibrium": {
        "equilibrium_id": "synthetic-calcite-gypsum-SIT",
        "aqueous_species": [
            {"species_id": "Ca2+", "initial_concentration_mol_m3": 20.0, "activity_reference_concentration_mol_m3": 1000.0, "activity_coefficient": 1.0, "charge_number": 2, "elemental_composition": {"Ca": 1}},
            {"species_id": "CO3--", "initial_concentration_mol_m3": 10.0, "activity_reference_concentration_mol_m3": 1000.0, "activity_coefficient": 1.0, "charge_number": -2, "elemental_composition": {"C": 1, "O": 3}},
            {"species_id": "SO4--", "initial_concentration_mol_m3": 5.0, "activity_reference_concentration_mol_m3": 1000.0, "activity_coefficient": 1.0, "charge_number": -2, "elemental_composition": {"S": 1, "O": 4}},
            {"species_id": "Cl-", "initial_concentration_mol_m3": 10.0, "activity_reference_concentration_mol_m3": 1000.0, "activity_coefficient": 1.0, "charge_number": -1, "elemental_composition": {"Cl": 1}},
        ],
        "candidate_solid_phases": [
            {"solid_species_id": "CaCO3(s)", "precipitation_stoichiometry": {"Ca2+": 1.0, "CO3--": 1.0}, "solid_elemental_composition": {"Ca": 1, "C": 1, "O": 3}, "initial_solid_moles_per_solution_volume_mol_m3": 0.0, "dimensionless_solubility_product": 1e-8, "equilibrium_constant_source_sha256": "1" * 64},
            {"solid_species_id": "CaSO4(s)", "precipitation_stoichiometry": {"Ca2+": 1.0, "SO4--": 1.0}, "solid_elemental_composition": {"Ca": 1, "S": 1, "O": 4}, "initial_solid_moles_per_solution_volume_mol_m3": 0.0, "dimensionless_solubility_product": 1e-5, "equilibrium_constant_source_sha256": "2" * 64},
        ],
        "temperature_K": 298.15,
        "standard_state_id": "synthetic-1-mol-per-liter",
        "candidate_phase_set_completeness_reviewed": True,
        "fixed_activity_coefficients_and_standard_states_reviewed": True,
        "equilibrium_constant_temperature_and_computational_use_reviewed": True,
        "single_liquid_fixed_volume_and_neutral_solid_assumptions_reviewed": True,
    },
    "water_mass_per_solution_volume_kg_L": 0.997,
    "debye_huckel_A_at_temperature": 0.5092,
    "A_evidence_source_id": "synthetic-SIT-parameters",
    "provider_id": "synthetic-provider",
    "provider_revision": "1",
    "configuration_sha256": "3" * 64,
    "record_sha256": "4" * 64,
    "interactions": [
        {"target_species_id": "Ca2+", "counter_species_id": "Cl-", "epsilon_kg_mol": 0.12, "evidence_source_id": "synthetic-SIT-parameters", "source_record_id": "eps-Ca-Cl", "evidence_sha256": SIT_EVIDENCE_SHA256},
        {"target_species_id": "Cl-", "counter_species_id": "Ca2+", "epsilon_kg_mol": 0.10, "evidence_source_id": "synthetic-SIT-parameters", "source_record_id": "eps-Cl-Ca", "evidence_sha256": SIT_EVIDENCE_SHA256},
        {"target_species_id": "CO3--", "counter_species_id": "Cl-", "epsilon_kg_mol": 0.05, "evidence_source_id": "synthetic-SIT-parameters", "source_record_id": "eps-carbonate-Cl", "evidence_sha256": SIT_EVIDENCE_SHA256},
        {"target_species_id": "Cl-", "counter_species_id": "CO3--", "epsilon_kg_mol": 0.04, "evidence_source_id": "synthetic-SIT-parameters", "source_record_id": "eps-Cl-carbonate", "evidence_sha256": SIT_EVIDENCE_SHA256},
    ],
    "evidence": [{"source_id": "synthetic-SIT-parameters", "origin": "synthetic", "citation": "Synthetic wiring values only; not a chemical parameter source.", "sha256": SIT_EVIDENCE_SHA256}],
    "ionic_strength_limit_mol_kg": 1.0,
    "charge_balance_tolerance_mol_kg": 1e-8,
    "maximum_outer_iterations": 100,
    "log_gamma_tolerance": 1e-8,
    "damping_fraction": 0.5,
    "water_mass_conversion_reviewed": True,
    "temperature_solvent_A_and_standard_state_reviewed": True,
    "molarity_standard_state_mapping_reviewed": True,
    "complete_interaction_set_and_applicability_reviewed": True,
    "competing_solid_sit_applicability_reviewed": True,
    "charge_scope_and_solver_settings_reviewed": True,
})

if __name__ == "__main__":
    print(competitive_solid_sit_self_consistent_equilibrium(request).model_dump(mode="json"))

"""Synthetic shape example for a fixed-gamma competitive solid equilibrium."""

from matintegrity.registry import default_registry


inputs = {
    "equilibrium_id": "synthetic-calcite-gypsum-competition",
    "aqueous_species": [
        {
            "species_id": "Ca2+", "initial_concentration_mol_m3": 20.0,
            "activity_reference_concentration_mol_m3": 1000.0,
            "activity_coefficient": 1.0, "charge_number": 2,
            "elemental_composition": {"Ca": 1},
        },
        {
            "species_id": "CO3--", "initial_concentration_mol_m3": 10.0,
            "activity_reference_concentration_mol_m3": 1000.0,
            "activity_coefficient": 1.0, "charge_number": -2,
            "elemental_composition": {"C": 1, "O": 3},
        },
        {
            "species_id": "SO4--", "initial_concentration_mol_m3": 5.0,
            "activity_reference_concentration_mol_m3": 1000.0,
            "activity_coefficient": 1.0, "charge_number": -2,
            "elemental_composition": {"S": 1, "O": 4},
        },
    ],
    "candidate_solid_phases": [
        {
            "solid_species_id": "CaCO3(s)", "precipitation_stoichiometry": {"Ca2+": 1.0, "CO3--": 1.0},
            "solid_elemental_composition": {"Ca": 1, "C": 1, "O": 3},
            "initial_solid_moles_per_solution_volume_mol_m3": 0.0,
            "dimensionless_solubility_product": 1e-8,
            "equilibrium_constant_source_sha256": "1" * 64,
        },
        {
            "solid_species_id": "CaSO4(s)", "precipitation_stoichiometry": {"Ca2+": 1.0, "SO4--": 1.0},
            "solid_elemental_composition": {"Ca": 1, "S": 1, "O": 4},
            "initial_solid_moles_per_solution_volume_mol_m3": 0.0,
            "dimensionless_solubility_product": 1e-5,
            "equilibrium_constant_source_sha256": "2" * 64,
        },
    ],
    "temperature_K": 298.15,
    "standard_state_id": "synthetic-1-mol-per-liter",
    "candidate_phase_set_completeness_reviewed": True,
    "fixed_activity_coefficients_and_standard_states_reviewed": True,
    "equilibrium_constant_temperature_and_computational_use_reviewed": True,
    "single_liquid_fixed_volume_and_neutral_solid_assumptions_reviewed": True,
}

if __name__ == "__main__":
    result = default_registry().run("chemistry.competitive_solid_equilibrium", inputs)
    print(result.model_dump(mode="json"))

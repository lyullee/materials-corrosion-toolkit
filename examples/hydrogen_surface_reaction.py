"""Compose a synthetic reviewed gas driver with the planar hydrogen solver."""

import json

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "authored-synthetic",
    "origin": "synthetic",
    "citation": "Authored reduced surface-reaction demonstration",
    "license_id": "MIT",
}
SURFACE_INPUTS = {
    "boundary_id": "synthetic-gas-face",
    "material_condition_id": "synthetic-state",
    "reference_lattice_id": "synthetic-sites",
    "surface_condition_id": "synthetic-clean-face",
    "hydrogen_species_id": "H2",
    "gas_state_provider_id": "synthetic-reviewed-fugacity",
    "elapsed_time_origin_id": "synthetic-exposure-start",
    "elapsed_time_s": [0.0, 5.0, 10.0],
    "temperature_K": [300.0, 400.0, 500.0],
    "hydrogen_gas_driver_Pa": [100000.0, 225000.0, 400000.0],
    "gas_driver_kind": "fugacity",
    "reference_fugacity_Pa": 100000.0,
    "supported_temperature_K": [280.0, 520.0],
    "supported_hydrogen_gas_driver_Pa": [0.0, 500000.0],
    "absorption": {
        "rate_id": "synthetic-absorption",
        "pre_exponential_capacity_flux_mol_m2_s": 0.001,
        "activation_energy_J_mol": 5000.0,
        "evidence": [EVIDENCE],
    },
    "desorption": {
        "rate_id": "synthetic-desorption",
        "pre_exponential_capacity_flux_mol_m2_s": 0.0002,
        "activation_energy_J_mol": 7000.0,
        "evidence": [EVIDENCE],
    },
    "temperature_history_reviewed": True,
    "gas_driver_history_reviewed": True,
    "surface_parameterizations_reviewed": True,
    "lattice_surface_state_mapping_reviewed": True,
}

if __name__ == "__main__":
    registry = default_registry()
    context = RunContext(
        asset_id="synthetic-specimen",
        location_id="synthetic-gas-face",
        time_basis="elapsed from synthetic exposure start",
    )
    surface = registry.run_json(
        "transport.hydrogen_dissociative_surface_rates",
        json.dumps(SURFACE_INPUTS),
        context,
    )
    slab_inputs = {
        "material_condition_id": "synthetic-state",
        "reference_lattice_id": "synthetic-sites",
        "elapsed_time_origin_id": "synthetic-exposure-start",
        "thickness_m": 0.001,
        "cell_count": 8,
        "lattice_site_density_mol_m3": 1000.0,
        "initial_lattice_hydrogen_atoms_mol_m3": [0.0] * 8,
        "elapsed_time_s": SURFACE_INPUTS["elapsed_time_s"],
        "uniform_temperature_K": SURFACE_INPUTS["temperature_K"],
        "lattice_diffusivity_m2_s": [1e-9, 1e-9, 1e-9],
        "left_boundary": {
            "boundary_id": "synthetic-gas-face",
            **surface.values["boundary_contract_fields"],
        },
        "right_boundary": {
            "boundary_id": "synthetic-sealed-face",
            "kind": "no_flux",
            "evidence": [EVIDENCE],
        },
        "traps": [],
        "maximum_supported_lattice_occupancy": 0.99,
        "maximum_supported_total_trap_to_lattice_site_ratio": 0.05,
        "planar_geometry_reviewed": True,
        "fixed_populations_and_uniform_temperature_reviewed": True,
        "independent_single_occupancy_and_dilute_trap_regime_reviewed": True,
        "negligible_stress_gradient_reviewed": True,
        "detailed_balance_rate_ratio_reviewed": True,
    }
    slab = registry.run_json("transport.hydrogen_slab_kinetic", json.dumps(slab_inputs), context)
    print(
        json.dumps(
            {
                "surface_status": surface.status,
                "slab_status": slab.status,
                "surface_zero_net_occupancy": surface.values.get("zero_net_surface_occupancy"),
                "left_inward_flux_mol_m2_s": slab.values.get("left_inward_flux_mol_m2_s"),
                "relative_mass_balance_error": slab.values.get("relative_mass_balance_error"),
            },
            indent=2,
        )
    )

"""Synthetic local atomic-hydrogen balance, independent of a gas-pressure model."""

import json

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


def inputs():
    evidence = [
        dict(
            source_id="synthetic-traps",
            origin="synthetic",
            citation="Declared synthetic independent single-occupancy populations",
            license_id="MIT",
        )
    ]
    return dict(
        material_condition_id="synthetic-material",
        reference_lattice_id="synthetic-reference-lattice",
        total_hydrogen_atoms_mol_m3=1.0,
        lattice_site_density_mol_m3=1e5,
        lattice_diffusivity_m2_s=1e-8,
        temperature_K=300.0,
        maximum_supported_lattice_occupancy=0.01,
        traps=[
            dict(
                trap_id="population-a",
                material_condition_id="synthetic-material",
                reference_lattice_id="synthetic-reference-lattice",
                site_density_mol_m3=100.0,
                binding_energy_J_mol=25000.0,
                maximum_supported_occupancy=1.0,
                evidence=evidence,
            ),
            dict(
                trap_id="population-b",
                material_condition_id="synthetic-material",
                reference_lattice_id="synthetic-reference-lattice",
                site_density_mol_m3=300.0,
                binding_energy_J_mol=45000.0,
                maximum_supported_occupancy=1.0,
                evidence=evidence,
            ),
        ],
        local_equilibrium_confirmed=True,
        independent_single_occupancy_sites_confirmed=True,
        fixed_trap_population_and_uniform_temperature_confirmed=True,
    )


def main():
    result = default_registry().run_json(
        "transport.hydrogen_trap_equilibrium",
        json.dumps(inputs()),
        RunContext(
            asset_id="synthetic",
            location_id="one-material-point",
            time_basis="instantaneous local equilibrium",
        ),
    )
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()

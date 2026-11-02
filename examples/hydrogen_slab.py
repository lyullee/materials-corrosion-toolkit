"""Synthetic planar charging with user-supplied kinetics; no experimental calibration."""

import json

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "authored-synthetic",
    "origin": "synthetic",
    "citation": "Authored parameter demonstration",
}
INPUTS = dict(
    material_condition_id="synthetic-state",
    reference_lattice_id="synthetic-sites",
    elapsed_time_origin_id="synthetic-charging-start",
    thickness_m=0.001,
    cell_count=12,
    lattice_site_density_mol_m3=1000.0,
    initial_lattice_hydrogen_atoms_mol_m3=[0.01] * 12,
    elapsed_time_s=[0.0, 1.0, 5.0, 10.0],
    uniform_temperature_K=[300.0, 300.0, 320.0, 330.0],
    lattice_diffusivity_m2_s=[1e-9, 1e-9, 2e-9, 3e-9],
    left_boundary=dict(
        boundary_id="entry",
        kind="prescribed_lattice_concentration",
        lattice_hydrogen_atoms_mol_m3=[0.02] * 4,
        evidence=[EVIDENCE],
    ),
    right_boundary=dict(
        boundary_id="exit",
        kind="prescribed_lattice_concentration",
        lattice_hydrogen_atoms_mol_m3=[0.005] * 4,
        evidence=[EVIDENCE],
    ),
    traps=[
        dict(
            population=dict(
                trap_id="population-one",
                material_condition_id="synthetic-state",
                reference_lattice_id="synthetic-sites",
                site_density_mol_m3=10.0,
                binding_energy_J_mol=5000.0,
                maximum_supported_occupancy=0.8,
                evidence=[EVIDENCE],
            ),
            capture_frequency_per_s=[0.2, 0.2, 0.3, 0.4],
            initial_occupancy=[0.0] * 12,
            rate_evidence=[EVIDENCE],
        )
    ],
    maximum_supported_lattice_occupancy=0.01,
    maximum_supported_total_trap_to_lattice_site_ratio=0.05,
    planar_geometry_reviewed=True,
    fixed_populations_and_uniform_temperature_reviewed=True,
    independent_single_occupancy_and_dilute_trap_regime_reviewed=True,
    negligible_stress_gradient_reviewed=True,
    detailed_balance_rate_ratio_reviewed=True,
)


if __name__ == "__main__":
    result = default_registry().run_json(
        "transport.hydrogen_slab_kinetic",
        json.dumps(INPUTS),
        RunContext(
            asset_id="synthetic-slab", location_id="wall", time_basis="elapsed from synthetic charging start"
        ),
    )
    print(
        json.dumps(
            dict(
                status=result.status,
                mass_error=result.values.get("relative_mass_balance_error"),
                solver=result.values.get("solver"),
            ),
            indent=2,
        )
    )

"""Verify the reduced hydrogen surface law and planar/cylindrical composition."""

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.hydrogen import R_J_mol_K
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
SURFACE_MODEL = "transport.hydrogen_dissociative_surface_rates"
SLAB_MODEL = "transport.hydrogen_slab_kinetic"
CYLINDER_MODEL = "transport.hydrogen_finite_cylinder_kinetic"
EVIDENCE = {
    "source_id": "authored-validation",
    "origin": "synthetic",
    "citation": "Authored reduced surface-reaction benchmark",
}


def law(identifier, capacity, energy):
    return {
        "rate_id": identifier,
        "pre_exponential_capacity_flux_mol_m2_s": capacity,
        "activation_energy_J_mol": energy,
        "evidence": [EVIDENCE],
    }


def surface_request():
    return {
        "boundary_id": "gas-face",
        "material_condition_id": "authored-state",
        "reference_lattice_id": "authored-lattice",
        "surface_condition_id": "authored-surface",
        "hydrogen_species_id": "H2",
        "gas_state_provider_id": "authored-fugacity",
        "elapsed_time_origin_id": "authored-exposure-start",
        "elapsed_time_s": [0.0, 0.001],
        "temperature_K": [300.0, 600.0],
        "hydrogen_gas_driver_Pa": [1e5, 4e5],
        "gas_driver_kind": "fugacity",
        "reference_fugacity_Pa": 1e5,
        "supported_temperature_K": [250.0, 650.0],
        "supported_hydrogen_gas_driver_Pa": [0.0, 5e5],
        "absorption": law("absorption", 8.0, 2000.0),
        "desorption": law("desorption", 3.0, 3000.0),
        "temperature_history_reviewed": True,
        "gas_driver_history_reviewed": True,
        "surface_parameterizations_reviewed": True,
        "lattice_surface_state_mapping_reviewed": True,
    }


def no_flux(identifier):
    return {"boundary_id": identifier, "kind": "no_flux", "evidence": [EVIDENCE]}


def common_transport(surface_fields):
    return {
        "material_condition_id": "authored-state",
        "reference_lattice_id": "authored-lattice",
        "elapsed_time_origin_id": "authored-exposure-start",
        "lattice_site_density_mol_m3": 10.0,
        "elapsed_time_s": [0.0, 0.001],
        "uniform_temperature_K": [300.0, 600.0],
        "lattice_diffusivity_m2_s": [2.0, 2.0],
        "traps": [],
        "maximum_supported_lattice_occupancy": 0.9,
        "maximum_supported_total_trap_to_lattice_site_ratio": 0.05,
        "fixed_populations_and_uniform_temperature_reviewed": True,
        "independent_single_occupancy_and_dilute_trap_regime_reviewed": True,
        "negligible_stress_gradient_reviewed": True,
        "detailed_balance_rate_ratio_reviewed": True,
        "surface_fields": surface_fields,
    }


def main():
    registry = default_registry()
    context = RunContext(
        asset_id="authored-specimen",
        location_id="gas-face",
        time_basis="elapsed seconds",
    )
    request = surface_request()
    surface = registry.run_json(SURFACE_MODEL, json.dumps(request), context)
    if surface.status != "computed":
        raise ValueError(surface.notes)
    temperatures = np.asarray(request["temperature_K"])
    drivers = np.asarray(request["hydrogen_gas_driver_Pa"])
    expected_absorption = (
        8.0
        * np.exp(-2000.0 / (R_J_mol_K * temperatures))
        * np.sqrt(drivers / request["reference_fugacity_Pa"])
    )
    expected_desorption = 3.0 * np.exp(-3000.0 / (R_J_mol_K * temperatures))
    capacity_relative_error = max(
        float(
            np.max(
                np.abs(
                    np.asarray(surface.values["absorption_capacity_flux_mol_m2_s"]) / expected_absorption - 1
                )
            )
        ),
        float(
            np.max(
                np.abs(
                    np.asarray(surface.values["desorption_capacity_flux_mol_m2_s"]) / expected_desorption - 1
                )
            )
        ),
    )
    fragment = surface.values["boundary_contract_fields"]
    common = common_transport(fragment)
    slab_input = {key: value for key, value in common.items() if key != "surface_fields"} | {
        "thickness_m": 1.0,
        "cell_count": 2,
        "initial_lattice_hydrogen_atoms_mol_m3": [2.0, 2.0],
        "left_boundary": {"boundary_id": "gas-face", **fragment},
        "right_boundary": no_flux("sealed-face"),
        "planar_geometry_reviewed": True,
    }
    slab = registry.run_json(SLAB_MODEL, json.dumps(slab_input), context)
    if slab.status != "computed":
        raise ValueError(slab.notes)
    absorption = surface.values["absorption_capacity_flux_mol_m2_s"][0]
    desorption = surface.values["desorption_capacity_flux_mol_m2_s"][0]
    target = absorption / (absorption + desorption)
    half_cell = 0.25
    surface_conductance = absorption + desorption
    diffusion_conductance = 10.0 * 2.0 / half_cell
    combined = 1 / (1 / surface_conductance + 1 / diffusion_conductance)
    expected_slab_flux = combined * (target - 0.2)
    slab_flux_error = abs(slab.values["left_inward_flux_mol_m2_s"][0] - expected_slab_flux)

    cylinder_input = {key: value for key, value in common.items() if key != "surface_fields"} | {
        "radius_m": 1.0,
        "length_m": 2.0,
        "radial_cell_count": 2,
        "axial_cell_count": 2,
        "initial_lattice_hydrogen_atoms_mol_m3": [2.0] * 4,
        "curved_surface_boundary": {"boundary_id": "gas-face", **fragment},
        "lower_end_boundary": no_flux("lower"),
        "upper_end_boundary": no_flux("upper"),
        "finite_axisymmetric_geometry_reviewed": True,
        "azimuthally_uniform_state_reviewed": True,
    }
    cylinder = registry.run_json(CYLINDER_MODEL, json.dumps(cylinder_input), context)
    if cylinder.status != "computed":
        raise ValueError(cylinder.notes)
    expected_flow = expected_slab_flux * 2 * math.pi * 1.0 * 2.0
    cylinder_flow_error = abs(
        cylinder.values["inward_surface_flow_mol_s"]["curved_surface"][0] - expected_flow
    )
    mass_error = max(
        slab.values["relative_mass_balance_error"],
        cylinder.values["relative_mass_balance_error"],
    )
    if (
        capacity_relative_error > 2e-15
        or slab_flux_error > 1e-13
        or cylinder_flow_error > 1e-12
        or mass_error > 1e-9
    ):
        raise ValueError("surface-reaction verification exceeds its declared numerical checks")
    record = {
        "schema_version": "matintegrity.hydrogen_surface_reaction_verification.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_ids": [SURFACE_MODEL, SLAB_MODEL, CYLINDER_MODEL],
        "source_sha256": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in (
                "src/matintegrity/models/hydrogen_surface.py",
                "src/matintegrity/models/hydrogen_kinetics.py",
                "src/matintegrity/models/hydrogen_cylinder.py",
            )
        },
        "status": "passed",
        "surface_input_digest": surface.input_digest,
        "boundary_fragment_digest": canonical_digest(fragment),
        "maximum_capacity_relative_error": capacity_relative_error,
        "planar_initial_flux_absolute_error_mol_m2_s": slab_flux_error,
        "cylinder_initial_flow_absolute_error_mol_s": cylinder_flow_error,
        "maximum_composed_relative_mass_balance_error": mass_error,
        "qualification": (
            "Authored algebraic, geometry-composition and discrete mass-balance checks only. Synthetic "
            "parameters do not calibrate a material, surface state, gas equation of state or experiment."
        ),
    }
    target_file = ROOT / "validation/hydrogen_surface_reaction_math.json"
    target_file.write_text(json.dumps(record, indent=2, allow_nan=False), encoding="utf-8")
    print(target_file)


if __name__ == "__main__":
    main()

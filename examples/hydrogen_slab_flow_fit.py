"""Fit one synthetic planar hydrogen-transport history multiplier."""

import json

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "authored-synthetic",
    "origin": "synthetic",
    "citation": "Authored planar hydrogen-flow inverse demonstration",
    "license_id": "MIT",
}
TIMES = [0.0, 0.05, 0.1, 0.2, 0.4, 0.8]
BASE_SLAB = {
    "material_condition_id": "synthetic-state",
    "reference_lattice_id": "synthetic-lattice",
    "elapsed_time_origin_id": "synthetic-charging-start",
    "thickness_m": 1.0,
    "cell_count": 2,
    "lattice_site_density_mol_m3": 1.0,
    "initial_lattice_hydrogen_atoms_mol_m3": [0.0, 0.0],
    "elapsed_time_s": TIMES,
    "uniform_temperature_K": [300.0] * 6,
    "lattice_diffusivity_m2_s": [0.1] * 6,
    "left_boundary": {
        "boundary_id": "synthetic-entry",
        "kind": "prescribed_lattice_concentration",
        "lattice_hydrogen_atoms_mol_m3": [1.0] * 6,
        "evidence": [EVIDENCE],
    },
    "right_boundary": {
        "boundary_id": "synthetic-exit",
        "kind": "prescribed_lattice_concentration",
        "lattice_hydrogen_atoms_mol_m3": [0.0] * 6,
        "evidence": [EVIDENCE],
    },
    "traps": [],
    "maximum_supported_lattice_occupancy": 1.0,
    "maximum_supported_total_trap_to_lattice_site_ratio": 0.05,
    "planar_geometry_reviewed": True,
    "fixed_populations_and_uniform_temperature_reviewed": True,
    "independent_single_occupancy_and_dilute_trap_regime_reviewed": True,
    "negligible_stress_gradient_reviewed": True,
    "detailed_balance_rate_ratio_reviewed": True,
    "relative_tolerance": 0.0001,
    "absolute_occupancy_tolerance": 1e-11,
    "maximum_step_s": 0.05,
}
INPUTS = {
    "fit_id": "synthetic-diffusivity-multiplier-fit",
    "observation_series_id": "synthetic-exit-flow",
    "specimen_id": "synthetic-slab",
    "detector_calibration_id": "synthetic-ideal-flow",
    "observed_surface": "right",
    "observed_surface_id": "synthetic-exit",
    "base_slab": BASE_SLAB,
    "physical_surface_area_m2": 1.0,
    "observation_id": [f"synthetic-point-{index}" for index in range(6)],
    "source_group_id": [
        "synthetic-holdout",
        "synthetic-calibration",
        "synthetic-calibration",
        "synthetic-holdout",
        "synthetic-calibration",
        "synthetic-calibration",
    ],
    "partition": [
        "holdout",
        "calibration",
        "calibration",
        "holdout",
        "calibration",
        "calibration",
    ],
    "elapsed_time_s": TIMES,
    "outward_hydrogen_atoms_mol_s": [
        0.0,
        0.0011851797849124796,
        0.00438192242415886,
        0.015022994623681306,
        0.044701638924310554,
        0.1040459450438412,
    ],
    "residual_scale_mol_s": 0.001,
    "parameter_target": "lattice_diffusivity",
    "parameter_target_id": "synthetic-lattice",
    "initial_multiplier": 1.0,
    "multiplier_bounds": [0.25, 4.0],
    "minimum_calibration_jacobian_norm": 1e-6,
    "maximum_function_evaluations": 60,
    "observation_conversion_reviewed": True,
    "physical_surface_area_reviewed": True,
    "fixed_inputs_independent_of_holdout_reviewed": True,
    "one_parameter_scope_reviewed": True,
    "holdout_partition_predeclared": True,
    "evidence": [EVIDENCE],
}

if __name__ == "__main__":
    result = default_registry().run_json(
        "transport.hydrogen_slab_flow_multiplier_fit",
        json.dumps(INPUTS),
        RunContext(
            asset_id="synthetic-slab",
            location_id="synthetic-exit",
            time_basis="elapsed from synthetic charging start",
        ),
    )
    print(
        json.dumps(
            {
                "status": result.status,
                "fitted_multiplier": result.values.get("fitted_multiplier"),
                "calibration_flow_rmse_mol_s": result.values.get("calibration_flow_rmse_mol_s"),
                "holdout_flow_rmse_mol_s": result.values.get("holdout_flow_rmse_mol_s"),
                "fitted_slab_digest": result.values.get("fitted_slab_digest"),
            },
            indent=2,
        )
    )

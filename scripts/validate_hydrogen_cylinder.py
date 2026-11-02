"""Reproduce authored finite-cylinder diffusion checks without experimental observations."""

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.special import jn_zeros

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "transport.hydrogen_finite_cylinder_kinetic"
EVIDENCE = {
    "source_id": "authored-validation",
    "origin": "synthetic",
    "citation": "Authored finite-cylinder mathematical benchmark",
}


def boundary(name, concentration=None):
    result = {"boundary_id": name, "kind": "no_flux", "evidence": [EVIDENCE]}
    if concentration is not None:
        result.update(
            kind="prescribed_lattice_concentration",
            lattice_hydrogen_atoms_mol_m3=[concentration, concentration],
        )
    return result


def case(nr, nz, final_time):
    return dict(
        material_condition_id="authored-state",
        reference_lattice_id="authored-lattice",
        elapsed_time_origin_id="authored-zero",
        radius_m=1.0,
        length_m=2.0,
        radial_cell_count=nr,
        axial_cell_count=nz,
        lattice_site_density_mol_m3=1.0,
        initial_lattice_hydrogen_atoms_mol_m3=[0.0] * (nr * nz),
        elapsed_time_s=[0.0, final_time],
        uniform_temperature_K=[300.0, 300.0],
        lattice_diffusivity_m2_s=[1.0, 1.0],
        curved_surface_boundary=boundary("curved", 0.1),
        lower_end_boundary=boundary("lower"),
        upper_end_boundary=boundary("upper"),
        traps=[],
        maximum_supported_lattice_occupancy=0.9,
        maximum_supported_total_trap_to_lattice_site_ratio=0.05,
        finite_axisymmetric_geometry_reviewed=True,
        azimuthally_uniform_state_reviewed=True,
        fixed_populations_and_uniform_temperature_reviewed=True,
        independent_single_occupancy_and_dilute_trap_regime_reviewed=True,
        negligible_stress_gradient_reviewed=True,
        detailed_balance_rate_ratio_reviewed=True,
        relative_tolerance=0.005,
        maximum_step_s=0.0002,
    )


def main():
    registry = default_registry()
    context = RunContext(
        asset_id="authored-cylinder", location_id="synthetic-grid", time_basis="elapsed seconds"
    )
    final_time = 0.05
    roots = jn_zeros(0, 160)
    exact_mean = float(0.1 * (1 - 4 * np.sum(np.exp(-(roots**2) * final_time) / roots**2)))
    radial = []
    for cells in (10, 20):
        payload = case(cells, 2, final_time)
        result = registry.run_json(MODEL_ID, json.dumps(payload), context)
        if result.status != "computed":
            raise ValueError(result.notes)
        observed = result.values["lattice_volume_mean_hydrogen_atoms_mol_m3"][-1]
        radial.append(
            {
                "radial_cells": cells,
                "axial_cells": 2,
                "input_digest": result.input_digest,
                "absolute_volume_mean_error_mol_m3": abs(observed - exact_mean),
                "relative_mass_balance_error": result.values["relative_mass_balance_error"],
            }
        )
    reduction = (
        radial[0]["absolute_volume_mean_error_mol_m3"] / radial[1]["absolute_volume_mean_error_mol_m3"]
    )
    axial = case(3, 8, 1.0)
    dz = axial["length_m"] / axial["axial_cell_count"]
    line = [0.3 - 0.2 * (index + 0.5) * dz / axial["length_m"] for index in range(8)]
    axial["initial_lattice_hydrogen_atoms_mol_m3"] = line * 3
    axial["curved_surface_boundary"] = boundary("curved")
    axial["lower_end_boundary"] = boundary("lower", 0.3)
    axial["upper_end_boundary"] = boundary("upper", 0.1)
    axial["lattice_diffusivity_m2_s"] = [0.2, 0.2]
    result = registry.run_json(MODEL_ID, json.dumps(axial), context)
    if result.status != "computed":
        raise ValueError(result.notes)
    expected_flow = 0.2 * (0.3 - 0.1) / 2 * math.pi
    axial_errors = {
        "maximum_profile_error_mol_m3": float(
            np.max(
                np.abs(
                    np.asarray(result.values["final_lattice_hydrogen_atoms_mol_m3"])
                    - np.asarray(axial["initial_lattice_hydrogen_atoms_mol_m3"])
                )
            )
        ),
        "lower_end_flow_error_mol_s": abs(
            result.values["inward_surface_flow_mol_s"]["lower_end"][-1] - expected_flow
        ),
        "upper_end_flow_error_mol_s": abs(
            result.values["inward_surface_flow_mol_s"]["upper_end"][-1] + expected_flow
        ),
        "relative_mass_balance_error": result.values["relative_mass_balance_error"],
    }
    if reduction <= 2.5 or max(axial_errors.values()) > 1e-9:
        raise ValueError("finite-cylinder verification no longer satisfies declared checks")
    record = {
        "schema_version": "matintegrity.hydrogen_finite_cylinder_verification.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_id": MODEL_ID,
        "model_source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/hydrogen_cylinder.py").read_bytes()
        ).hexdigest(),
        "status": "passed",
        "radial_bessel_volume_mean": radial,
        "radial_error_reduction": reduction,
        "axial_linear_steady_state": axial_errors,
        "qualification": (
            "Authored mathematical verification of axisymmetric diffusion, finite-volume geometry and "
            "surface inventory only; not detector calibration, trap-parameter fitting, experimental "
            "validation or a global discretization-error guarantee."
        ),
    }
    target = ROOT / "validation/hydrogen_finite_cylinder_math.json"
    target.write_text(json.dumps(record, indent=2, allow_nan=False), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

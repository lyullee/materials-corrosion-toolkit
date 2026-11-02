"""Check authored linear surface-transfer resistance and inventory identities."""

import copy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def main():
    examples = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"]
    registry = default_registry()
    context = RunContext(
        asset_id="authored-surface-transfer",
        location_id="synthetic-boundary",
        time_basis="elapsed seconds",
    )
    coefficient = 0.05
    initial = 0.2
    diffusivity = 0.1

    slab = copy.deepcopy(examples["transport.hydrogen_slab_kinetic"])
    cells = 4
    slab.update(
        thickness_m=1.0,
        cell_count=cells,
        lattice_site_density_mol_m3=1.0,
        initial_lattice_hydrogen_atoms_mol_m3=[initial] * cells,
        elapsed_time_s=[0.0, 0.1],
        uniform_temperature_K=[300.0, 300.0],
        lattice_diffusivity_m2_s=[diffusivity, diffusivity],
        traps=[],
        maximum_supported_lattice_occupancy=0.9,
    )
    slab["left_boundary"] = {
        "boundary_id": "linear-left",
        "kind": "linear_surface_transfer",
        "equilibrium_lattice_hydrogen_atoms_mol_m3": [0.0, 0.0],
        "transfer_coefficient_m_s": [coefficient, coefficient],
        "evidence": slab["left_boundary"]["evidence"],
    }
    slab["right_boundary"] = {
        "boundary_id": "sealed-right",
        "kind": "no_flux",
        "evidence": slab["right_boundary"]["evidence"],
    }
    slab_result = registry.run_json("transport.hydrogen_slab_kinetic", json.dumps(slab), context)
    if slab_result.status != "computed":
        raise ValueError(slab_result.notes)
    slab_half_cell = slab["thickness_m"] / cells / 2
    slab_effective = 1 / (1 / coefficient + slab_half_cell / diffusivity)
    slab_expected = -slab_effective * initial

    cylinder = copy.deepcopy(examples["transport.hydrogen_finite_cylinder_kinetic"])
    nr, nz = 4, 3
    cylinder.update(
        radius_m=1.0,
        length_m=2.0,
        radial_cell_count=nr,
        axial_cell_count=nz,
        lattice_site_density_mol_m3=1.0,
        initial_lattice_hydrogen_atoms_mol_m3=[initial] * (nr * nz),
        elapsed_time_s=[0.0, 0.1],
        uniform_temperature_K=[300.0, 300.0],
        lattice_diffusivity_m2_s=[diffusivity, diffusivity],
        traps=[],
        maximum_supported_lattice_occupancy=0.9,
    )
    cylinder["curved_surface_boundary"] = {
        "boundary_id": "linear-curved",
        "kind": "linear_surface_transfer",
        "equilibrium_lattice_hydrogen_atoms_mol_m3": [0.0, 0.0],
        "transfer_coefficient_m_s": [coefficient, coefficient],
        "evidence": cylinder["curved_surface_boundary"]["evidence"],
    }
    for name in ("lower_end_boundary", "upper_end_boundary"):
        cylinder[name] = {
            "boundary_id": name,
            "kind": "no_flux",
            "evidence": cylinder[name]["evidence"],
        }
    cylinder_result = registry.run_json(
        "transport.hydrogen_finite_cylinder_kinetic", json.dumps(cylinder), context
    )
    if cylinder_result.status != "computed":
        raise ValueError(cylinder_result.notes)
    cylinder_half_cell = cylinder["radius_m"] / nr / 2
    cylinder_effective = 1 / (1 / coefficient + cylinder_half_cell / diffusivity)
    curved_area = 2 * math.pi * cylinder["radius_m"] * cylinder["length_m"]
    cylinder_expected = -cylinder_effective * initial * curved_area

    errors = {
        "slab_initial_flux_mol_m2_s": abs(slab_result.values["left_inward_flux_mol_m2_s"][0] - slab_expected),
        "cylinder_initial_flow_mol_s": abs(
            cylinder_result.values["inward_surface_flow_mol_s"]["curved_surface"][0] - cylinder_expected
        ),
        "slab_relative_mass_balance": slab_result.values["relative_mass_balance_error"],
        "cylinder_relative_mass_balance": cylinder_result.values["relative_mass_balance_error"],
    }
    if max(errors.values()) > 1e-9:
        raise ValueError(f"surface-transfer identity mismatch: {errors}")
    sources = (
        ROOT / "src/matintegrity/models/hydrogen_kinetics.py",
        ROOT / "src/matintegrity/models/hydrogen_cylinder.py",
    )
    record = {
        "schema_version": "matintegrity.hydrogen_surface_transfer_verification.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "series_resistance_identity": "v_eff = 1 / (1/k_surface + half_cell_distance/D)",
        "absolute_errors": errors,
        "slab_input_digest": slab_result.input_digest,
        "cylinder_input_digest": cylinder_result.input_digest,
        "model_source_sha256": {
            source.name: hashlib.sha256(source.read_bytes()).hexdigest() for source in sources
        },
        "qualification": (
            "Authored finite-volume boundary identity and numerical mass-balance check only; the "
            "surface coefficient, equilibrium concentration and experimental applicability require "
            "independent evidence."
        ),
    }
    target = ROOT / "validation/hydrogen_surface_transfer_math.json"
    target.write_text(json.dumps(record, indent=2, allow_nan=False), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

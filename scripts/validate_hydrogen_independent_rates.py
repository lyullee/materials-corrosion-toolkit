"""Verify independently supplied hydrogen trap frequencies with authored closed systems."""

import copy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = {
    "source_id": "authored-validation",
    "origin": "synthetic",
    "citation": "Authored independent-rate mathematical benchmark",
}


def sealed(boundary):
    boundary.update(kind="no_flux")
    for key in (
        "lattice_hydrogen_atoms_mol_m3",
        "equilibrium_lattice_hydrogen_atoms_mol_m3",
        "transfer_coefficient_m_s",
    ):
        boundary.pop(key, None)


def explicit_trap(cells, capture=0.7, release=0.7):
    return {
        "population": {
            "trap_id": "independent-rate-trap",
            "material_condition_id": "authored-state",
            "reference_lattice_id": "authored-lattice",
            "site_density_mol_m3": 0.01,
            "binding_energy_J_mol": 1e9,
            "maximum_supported_occupancy": 1.0,
            "evidence": [EVIDENCE],
        },
        "rate_model": "independent_frequencies",
        "capture_frequency_per_s": [capture, capture],
        "release_frequency_per_s": [release, release],
        "initial_occupancy": [0.8] * cells,
        "independent_rate_histories_reviewed": True,
        "rate_evidence": [EVIDENCE],
    }


def main():
    examples = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"]
    registry = default_registry()
    context = RunContext(
        asset_id="authored-closed-system",
        location_id="synthetic-domain",
        time_basis="elapsed seconds",
    )
    exact = 0.208 / 1.01 + (0.8 - 0.208 / 1.01) * math.exp(-0.7 * 1.01)
    cases = []
    for model_id in (
        "transport.hydrogen_slab_kinetic",
        "transport.hydrogen_finite_cylinder_kinetic",
    ):
        payload = copy.deepcopy(examples[model_id])
        payload.update(
            material_condition_id="authored-state",
            reference_lattice_id="authored-lattice",
            elapsed_time_s=[0.0, 1.0],
            uniform_temperature_K=[300.0, 900.0],
            lattice_diffusivity_m2_s=[0.1, 0.1],
            lattice_site_density_mol_m3=1.0,
            maximum_supported_lattice_occupancy=0.9,
            maximum_supported_total_trap_to_lattice_site_ratio=0.05,
            detailed_balance_rate_ratio_reviewed=False,
            maximum_step_s=0.005,
            relative_tolerance=0.005,
        )
        if model_id.endswith("slab_kinetic"):
            payload.update(thickness_m=1.0, cell_count=2)
            cells = 2
            boundaries = (payload["left_boundary"], payload["right_boundary"])
        else:
            payload.update(radius_m=1.0, length_m=2.0, radial_cell_count=2, axial_cell_count=2)
            cells = 4
            boundaries = (
                payload["curved_surface_boundary"],
                payload["lower_end_boundary"],
                payload["upper_end_boundary"],
            )
        for boundary in boundaries:
            sealed(boundary)
        payload["initial_lattice_hydrogen_atoms_mol_m3"] = [0.2] * cells
        payload["traps"] = [explicit_trap(cells)]
        result = registry.run_json(model_id, json.dumps(payload), context)
        if result.status != "computed":
            raise ValueError(result.notes)
        observed = result.values["traps"][0]["final_occupancy"][0]
        cases.append(
            {
                "model_id": model_id,
                "input_digest": result.input_digest,
                "rate_model": result.values["traps"][0]["rate_model"],
                "rate_history_digest": result.values["traps"][0]["rate_history_digest"],
                "absolute_occupancy_error": abs(observed - exact),
                "relative_mass_balance_error": result.values["relative_mass_balance_error"],
            }
        )
    maximum_error = max(case["absolute_occupancy_error"] for case in cases)
    maximum_balance_error = max(case["relative_mass_balance_error"] for case in cases)
    if maximum_error > 0.001 or maximum_balance_error > 1e-9:
        raise ValueError("independent-frequency verification exceeds its declared checks")
    record = {
        "schema_version": "matintegrity.hydrogen_independent_rates_verification.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_source_sha256": {
            name: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for name, path in {
                "slab": "src/matintegrity/models/hydrogen_kinetics.py",
                "finite_cylinder": "src/matintegrity/models/hydrogen_cylinder.py",
            }.items()
        },
        "status": "passed",
        "closed_equal_rate_cases": cases,
        "maximum_absolute_occupancy_error": maximum_error,
        "maximum_relative_mass_balance_error": maximum_balance_error,
        "qualification": (
            "Authored closed-system verification only. Explicit capture/release histories are not "
            "material parameters, an experimental calibration, or evidence for extrapolation."
        ),
    }
    target = ROOT / "validation/hydrogen_independent_rates_math.json"
    target.write_text(json.dumps(record, indent=2, allow_nan=False), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

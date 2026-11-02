"""Reproduce authored analytical hydrogen benchmarks without external observations."""

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "transport.hydrogen_slab_kinetic"


def main():
    template = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"][
        MODEL_ID
    ]
    registry = default_registry()
    context = RunContext(
        asset_id="authored-benchmark", location_id="synthetic-slab", time_basis="elapsed seconds"
    )

    def base(cells):
        x = copy.deepcopy(template)
        x.update(
            cell_count=cells,
            thickness_m=1.0,
            lattice_site_density_mol_m3=1.0,
            initial_lattice_hydrogen_atoms_mol_m3=[0.2] * cells,
            elapsed_time_s=[0.0, 1.0],
            uniform_temperature_K=[300.0, 300.0],
            lattice_diffusivity_m2_s=[0.1, 0.1],
            maximum_supported_lattice_occupancy=0.9,
            traps=[],
        )
        for boundary in (x["left_boundary"], x["right_boundary"]):
            boundary.update(kind="no_flux", lattice_hydrogen_atoms_mol_m3=None)
        return x

    def calculate(x):
        result = registry.run_json(MODEL_ID, json.dumps(x), context)
        if result.status != "computed":
            raise ValueError(result.notes)
        return result

    temporal = []
    exact_reaction = 0.208 / 1.01 + (0.8 - 0.208 / 1.01) * np.exp(-0.7 * 1.01)
    for step in (0.04, 0.02, 0.01):
        x = base(4)
        population = copy.deepcopy(template["traps"][0])
        population["population"].update(
            site_density_mol_m3=0.01, binding_energy_J_mol=0.0, maximum_supported_occupancy=1.0
        )
        population.update(capture_frequency_per_s=[0.7, 0.7], initial_occupancy=[0.8] * 4)
        x.update(traps=[population], maximum_step_s=step, relative_tolerance=0.01)
        result = calculate(x)
        temporal.append(
            dict(
                maximum_step_s=step,
                input_digest=result.input_digest,
                absolute_trap_occupancy_error=abs(
                    result.values["traps"][0]["final_occupancy"][0] - float(exact_reaction)
                ),
                relative_mass_balance_error=result.values["relative_mass_balance_error"],
            )
        )
    spatial = []
    for cells in (12, 24):
        x = base(cells)
        x.update(
            initial_lattice_hydrogen_atoms_mol_m3=[0.0] * cells,
            elapsed_time_s=[0.0, 0.1],
            lattice_diffusivity_m2_s=[1.0, 1.0],
            maximum_step_s=1e-4,
            relative_tolerance=0.01,
        )
        x["left_boundary"].update(
            kind="prescribed_lattice_concentration", lattice_hydrogen_atoms_mol_m3=[0.1, 0.1]
        )
        x["right_boundary"].update(
            kind="prescribed_lattice_concentration", lattice_hydrogen_atoms_mol_m3=[0.0, 0.0]
        )
        modes = np.arange(1, 161)[:, None]
        center = (np.arange(cells) + 0.5) / cells
        average_sine = np.sin(np.pi * modes * center) * np.sinc(modes / (2 * cells))
        expected = 0.1 * (
            1
            - center
            - np.sum(2 / (np.pi * modes) * average_sine * np.exp(-(np.pi**2) * modes**2 * 0.1), axis=0)
        )
        result = calculate(x)
        spatial.append(
            dict(
                cells=cells,
                maximum_step_s=1e-4,
                input_digest=result.input_digest,
                maximum_cell_average_error_mol_m3=float(
                    np.max(np.abs(result.values["final_lattice_hydrogen_atoms_mol_m3"] - expected))
                ),
                relative_mass_balance_error=result.values["relative_mass_balance_error"],
            )
        )
    time_ratios = [
        temporal[i]["absolute_trap_occupancy_error"] / temporal[i + 1]["absolute_trap_occupancy_error"]
        for i in range(2)
    ]
    mesh_ratio = (
        spatial[0]["maximum_cell_average_error_mol_m3"] / spatial[1]["maximum_cell_average_error_mol_m3"]
    )
    if min(time_ratios) <= 1.8 or mesh_ratio <= 2.5:
        raise ValueError("analytical convergence evidence no longer satisfies the declared checks")
    record = dict(
        schema_version="matintegrity.hydrogen_slab_verification.v1",
        checked_at_utc=datetime.now(timezone.utc).isoformat(),
        model_id=MODEL_ID,
        model_source_sha256=hashlib.sha256(
            (ROOT / "src/matintegrity/models/hydrogen_kinetics.py").read_bytes()
        ).hexdigest(),
        status="passed",
        temporal_reaction=temporal,
        temporal_error_reduction=time_ratios,
        fourier_cell_averages=spatial,
        spatial_error_reduction=mesh_ratio,
        qualification="Authored mathematical benchmarks only. Fixed temporal error contributes to the mesh comparison; this is not a fitted experimental curve, global error guarantee or physical validation.",
    )
    (ROOT / "validation/hydrogen_slab_math.json").write_text(
        json.dumps(record, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()

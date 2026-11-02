"""Validate the finite-slab hydrogen bakeout screening model."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import Evidence
from matintegrity.models import welding
from matintegrity.models.hydrogen_kinetics import HydrogenSlab, LatticeBoundary, slab_kinetic
from matintegrity.models.welding import HydrogenBakeoutSlab, hydrogen_bakeout_slab

ROOT = Path(__file__).resolve().parents[1]


def request(times, diffusivities):
    return HydrogenBakeoutSlab(
        procedure_id="authored-bakeout-validation",
        material_condition_id="authored-steel",
        diffusivity_source_id="authored-validation-diffusivity",
        thickness_source_id="authored-validation-thickness",
        elapsed_time_s=times,
        temperature_K=[473.15] * len(times),
        effective_diffusivity_m2_s=diffusivities,
        slab_thickness_m=0.01,
        initial_diffusible_hydrogen_atoms_mol_m3=100.0,
        both_faces_exposed_reviewed=True,
        uniform_initial_concentration_reviewed=True,
        diffusion_limited_surface_reviewed=True,
        diffusivity_history_reviewed=True,
        temperature_history_reviewed=True,
    )


def main():
    thickness, diffusivity = 0.01, 1e-8
    characteristic_time = thickness**2 / (math.pi**2 * diffusivity)
    characteristic = hydrogen_bakeout_slab(request([0.0, characteristic_time], [diffusivity, diffusivity]))
    reference = sum(8 / math.pi**2 * math.exp(-((2 * n + 1) ** 2)) / (2 * n + 1) ** 2 for n in range(50))
    series_error = abs(characteristic.values["remaining_diffusible_fraction"][-1] - reference)

    analytical = hydrogen_bakeout_slab(request([0.0, 1000.0], [diffusivity, diffusivity]))
    evidence = Evidence(source_id="authored", origin="synthetic", citation="authored cross-check")
    concentration = 100.0
    numerical = slab_kinetic(
        HydrogenSlab(
            material_condition_id="authored-steel",
            reference_lattice_id="authored-lattice",
            elapsed_time_origin_id="authored-clock",
            thickness_m=thickness,
            cell_count=80,
            lattice_site_density_mol_m3=1e6,
            initial_lattice_hydrogen_atoms_mol_m3=[concentration] * 80,
            elapsed_time_s=[0.0, 1000.0],
            uniform_temperature_K=[473.15, 473.15],
            lattice_diffusivity_m2_s=[diffusivity, diffusivity],
            left_boundary=LatticeBoundary(
                boundary_id="left",
                kind="prescribed_lattice_concentration",
                lattice_hydrogen_atoms_mol_m3=[0.0, 0.0],
                evidence=(evidence,),
            ),
            right_boundary=LatticeBoundary(
                boundary_id="right",
                kind="prescribed_lattice_concentration",
                lattice_hydrogen_atoms_mol_m3=[0.0, 0.0],
                evidence=(evidence,),
            ),
            maximum_supported_lattice_occupancy=0.01,
            maximum_supported_total_trap_to_lattice_site_ratio=0.1,
            planar_geometry_reviewed=True,
            fixed_populations_and_uniform_temperature_reviewed=True,
            independent_single_occupancy_and_dilute_trap_regime_reviewed=True,
            negligible_stress_gradient_reviewed=True,
            detailed_balance_rate_ratio_reviewed=True,
            relative_tolerance=1e-5,
            maximum_relative_mass_balance_error=1e-6,
        )
    )
    if numerical.status != "computed":
        raise AssertionError("finite-volume no-trap cross-check did not compute")
    analytical_fraction = analytical.values["remaining_diffusible_fraction"][-1]
    numerical_fraction = numerical.values["lattice_mean_hydrogen_atoms_mol_m3"][-1] / concentration
    fvm_relative_error = abs(numerical_fraction / analytical_fraction - 1.0)
    if series_error > 1e-10 or fvm_relative_error > 0.003:
        raise AssertionError("hydrogen bakeout validation tolerance exceeded")

    first = hydrogen_bakeout_slab(request([0.0, 500.0, 1000.0], [0.5e-8, 1.5e-8, 0.5e-8]))
    transformed_time_error = abs(first.values["remaining_diffusible_fraction"][-1] - analytical_fraction)
    if transformed_time_error > 1e-13:
        raise AssertionError("equal integrated diffusivity changed the bakeout solution")

    result = {
        "schema_version": "matintegrity.hydrogen_bakeout_validation.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_source_sha256": hashlib.sha256(Path(welding.__file__).read_bytes()).hexdigest(),
        "validation_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "characteristic_time_s": characteristic_time,
        "characteristic_time_remaining_fraction": reference,
        "series_absolute_error": series_error,
        "finite_volume_cell_count": 80,
        "finite_volume_relative_error": fvm_relative_error,
        "equal_integrated_diffusivity_absolute_error": transformed_time_error,
        "qualification": (
            "Authored analytical-series, time-transformation and independent finite-volume no-trap "
            "cross-checks. This is not weld-procedure, diffusivity, trap, microstructure, hydrogen-cracking, "
            "field, design-code or acceptance validation."
        ),
    }
    target = ROOT / "validation/hydrogen_bakeout_math.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

"""Verify thermal trap frequencies and their composition with the planar transport model."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

from matintegrity.contracts import RunContext
from matintegrity.models.hydrogen_rates import BOLTZMANN_J_K, PLANCK_J_S, R_J_mol_K
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
RATE_MODEL = "transport.hydrogen_trap_thermal_rates"
SLAB_MODEL = "transport.hydrogen_slab_kinetic"
EVIDENCE = {
    "source_id": "authored-validation",
    "origin": "synthetic",
    "citation": "Authored thermal-rate benchmark",
}


def arrhenius(identifier, prefactor, energy):
    return {
        "frequency_id": identifier,
        "kind": "arrhenius",
        "pre_exponential_frequency_per_s": prefactor,
        "activation_energy_J_mol": energy,
        "evidence": [EVIDENCE],
    }


def request():
    return {
        "trap_id": "authored-trap",
        "material_condition_id": "authored-state",
        "reference_lattice_id": "authored-lattice",
        "energy_reference_id": "authored-lattice-site-zero",
        "elapsed_time_origin_id": "authored-heating-start",
        "elapsed_time_s": [0.0, 0.5, 1.0],
        "temperature_K": [300.0, 450.0, 600.0],
        "supported_temperature_K": [250.0, 650.0],
        "capture": arrhenius("capture", 5.0, 2000.0),
        "release": arrhenius("release", 2.0, 3000.0),
        "temperature_history_reviewed": True,
        "frequency_parameterizations_reviewed": True,
        "common_energy_reference_reviewed": True,
    }


def main():
    registry = default_registry()
    context = RunContext(
        asset_id="authored-closed-system",
        location_id="synthetic-trap",
        time_basis="elapsed seconds",
    )
    payload = request()
    rate_result = registry.run_json(RATE_MODEL, json.dumps(payload), context)
    if rate_result.status != "computed":
        raise ValueError(rate_result.notes)
    temperatures = np.asarray(payload["temperature_K"])
    expected_capture = 5.0 * np.exp(-2000.0 / (R_J_mol_K * temperatures))
    expected_release = 2.0 * np.exp(-3000.0 / (R_J_mol_K * temperatures))
    arrhenius_error = max(
        float(np.max(np.abs(rate_result.values["capture_frequency_per_s"] - expected_capture))),
        float(np.max(np.abs(rate_result.values["release_frequency_per_s"] - expected_release))),
    )

    transition = request()
    transition["capture"] = {
        "frequency_id": "capture-transition-state",
        "kind": "transition_state",
        "activation_enthalpy_J_mol": 45000.0,
        "activation_entropy_J_mol_K": -30.0,
        "transmission_coefficient": 0.7,
        "evidence": [EVIDENCE],
    }
    transition_result = registry.run_json(RATE_MODEL, json.dumps(transition), context)
    if transition_result.status != "computed":
        raise ValueError(transition_result.notes)
    expected_transition = (
        0.7
        * BOLTZMANN_J_K
        * temperatures
        / PLANCK_J_S
        * np.exp(-30.0 / R_J_mol_K)
        * np.exp(-45000.0 / (R_J_mol_K * temperatures))
    )
    transition_error = float(
        np.max(
            np.abs(np.asarray(transition_result.values["capture_frequency_per_s"]) / expected_transition - 1)
        )
    )

    times = payload["elapsed_time_s"]
    capture = rate_result.values["capture_frequency_per_s"]
    release = rate_result.values["release_frequency_per_s"]
    slab = {
        "material_condition_id": "authored-state",
        "reference_lattice_id": "authored-lattice",
        "elapsed_time_origin_id": "authored-heating-start",
        "thickness_m": 1.0,
        "cell_count": 4,
        "lattice_site_density_mol_m3": 1.0,
        "initial_lattice_hydrogen_atoms_mol_m3": [0.2] * 4,
        "elapsed_time_s": times,
        "uniform_temperature_K": payload["temperature_K"],
        "lattice_diffusivity_m2_s": [0.1] * 3,
        "left_boundary": {"boundary_id": "left", "kind": "no_flux", "evidence": [EVIDENCE]},
        "right_boundary": {"boundary_id": "right", "kind": "no_flux", "evidence": [EVIDENCE]},
        "traps": [
            {
                "population": {
                    "trap_id": "authored-trap",
                    "material_condition_id": "authored-state",
                    "reference_lattice_id": "authored-lattice",
                    "site_density_mol_m3": 0.01,
                    "binding_energy_J_mol": 1000.0,
                    "maximum_supported_occupancy": 1.0,
                    "evidence": [EVIDENCE],
                },
                "initial_occupancy": [0.8] * 4,
                **rate_result.values["independent_rate_contract_fields"],
            }
        ],
        "maximum_supported_lattice_occupancy": 0.9,
        "maximum_supported_total_trap_to_lattice_site_ratio": 0.05,
        "planar_geometry_reviewed": True,
        "fixed_populations_and_uniform_temperature_reviewed": True,
        "independent_single_occupancy_and_dilute_trap_regime_reviewed": True,
        "negligible_stress_gradient_reviewed": True,
        "detailed_balance_rate_ratio_reviewed": False,
        "relative_tolerance": 1e-6,
        "absolute_occupancy_tolerance": 1e-11,
        "maximum_step_s": 0.002,
    }
    slab_result = registry.run_json(SLAB_MODEL, json.dumps(slab), context)
    if slab_result.status != "computed":
        raise ValueError(slab_result.notes)
    total = 0.2 + 0.01 * 0.8

    def reaction(time, state):
        occupancy = state[0]
        lattice = total - 0.01 * occupancy
        capture_now = np.interp(time, times, capture)
        release_now = np.interp(time, times, release)
        return [capture_now * lattice * (1 - occupancy) - release_now * occupancy * (1 - lattice)]

    reference = solve_ivp(
        reaction,
        [times[0], times[-1]],
        [0.8],
        t_eval=times,
        method="DOP853",
        atol=1e-13,
        rtol=1e-11,
    )
    if not reference.success:
        raise ValueError(reference.message)
    observed = np.asarray(slab_result.values["traps"][0]["mean_hydrogen_atoms_mol_m3"]) / 0.01
    composition_error = float(np.max(np.abs(observed - reference.y[0])))
    mass_error = slab_result.values["relative_mass_balance_error"]
    if arrhenius_error > 1e-14 or transition_error > 1e-14 or composition_error > 0.0002:
        raise ValueError("thermal-rate verification exceeds its declared numerical checks")
    record = {
        "schema_version": "matintegrity.hydrogen_thermal_rates_verification.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_ids": [RATE_MODEL, SLAB_MODEL],
        "source_sha256": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in (
                "src/matintegrity/models/hydrogen_rates.py",
                "src/matintegrity/models/hydrogen_kinetics.py",
            )
        },
        "status": "passed",
        "rate_input_digest": rate_result.input_digest,
        "arrhenius_maximum_absolute_frequency_error_per_s": arrhenius_error,
        "transition_state_maximum_relative_frequency_error": transition_error,
        "composed_slab_maximum_occupancy_error": composition_error,
        "composed_slab_relative_mass_balance_error": mass_error,
        "composition_interpolation": "piecewise_linear_frequency_histories_on_shared_time_knots",
        "qualification": (
            "Authored mathematical and composition checks only. The parameters are synthetic and do not "
            "calibrate a material, identify a mechanism, quantify uncertainty or validate an experiment."
        ),
    }
    target = ROOT / "validation/hydrogen_thermal_rates_math.json"
    target.write_text(json.dumps(record, indent=2, allow_nan=False), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

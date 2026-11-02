"""Verify thermal-rate fitting against independent weighted closed forms."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from matintegrity.models.hydrogen import R_J_mol_K
from matintegrity.models.hydrogen_calibration import HydrogenThermalRateFit, fit_thermal_rate
from matintegrity.models.hydrogen_rates import (
    BOLTZMANN_J_K,
    PLANCK_J_S,
    HydrogenTrapThermalRates,
    ThermallyActivatedFrequency,
    thermal_trap_rates,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ({"source_id": "authored", "origin": "synthetic", "citation": "Authored identity"},)


def manual_weighted_line(inverse_temperature, response, sigma):
    weights = 1 / sigma**2
    mean_x = float(np.dot(weights, inverse_temperature) / weights.sum())
    mean_y = float(np.dot(weights, response) / weights.sum())
    slope = float(
        np.dot(weights, (inverse_temperature - mean_x) * (response - mean_y))
        / np.dot(weights, (inverse_temperature - mean_x) ** 2)
    )
    return mean_y - slope * mean_x, slope


def main():
    temperatures = np.array([300.0, 340.0, 390.0, 450.0, 520.0, 365.0, 420.0])
    partition = ["calibration"] * 5 + ["holdout"] * 2
    sigma = np.array([0.03, 0.04, 0.05, 0.04, 0.03, 0.06, 0.06])
    log_noise = np.array([0.01, -0.02, 0.015, -0.005, 0.0, 0.02, -0.01])
    prefactor, activation = 4e8, 38000.0
    frequency = prefactor * np.exp(-activation / (R_J_mol_K * temperatures) + log_noise)
    common = dict(
        fit_id="authored-fit",
        frequency_id="authored-capture",
        frequency_role="capture",
        kind="arrhenius",
        trap_id="authored-trap",
        material_condition_id="authored-state",
        reference_lattice_id="authored-lattice",
        energy_reference_id="authored-zero",
        observation_id=[f"rate-{index}" for index in range(len(temperatures))],
        source_group_id=["calibration-source"] * 5 + ["holdout-source"] * 2,
        partition=partition,
        temperature_K=temperatures.tolist(),
        frequency_per_s=frequency.tolist(),
        log_frequency_standard_uncertainty=sigma.tolist(),
        minimum_calibration_temperature_span_K=100.0,
        calibration_observations_independent_reviewed=True,
        rate_observation_mapping_reviewed=True,
        common_energy_reference_reviewed=True,
        holdout_partition_predeclared=True,
        evidence=EVIDENCE,
    )
    result = fit_thermal_rate(HydrogenThermalRateFit(**common))
    calibration = np.arange(len(temperatures)) < 5
    intercept, slope = manual_weighted_line(
        1 / temperatures[calibration], np.log(frequency[calibration]), sigma[calibration]
    )
    law = result.values["frequency_law"]
    errors = {
        "arrhenius_log_prefactor": abs(math.log(law["pre_exponential_frequency_per_s"]) - intercept),
        "arrhenius_activation_energy_J_mol": abs(law["activation_energy_J_mol"] + R_J_mol_K * slope),
    }
    changed = dict(common)
    changed["frequency_per_s"] = list(common["frequency_per_s"])
    changed["frequency_per_s"][-2:] = [value * 7 for value in changed["frequency_per_s"][-2:]]
    changed_result = fit_thermal_rate(HydrogenThermalRateFit(**changed))
    errors["holdout_exclusion_parameter_digest_changed"] = float(
        changed_result.values["frequency_law_digest"] != result.values["frequency_law_digest"]
    )

    enthalpy, entropy, transmission = 62000.0, -22.0, 0.7
    tst_frequency = (
        transmission
        * BOLTZMANN_J_K
        * temperatures
        / PLANCK_J_S
        * np.exp(entropy / R_J_mol_K)
        * np.exp(-enthalpy / (R_J_mol_K * temperatures))
    )
    tst = dict(common)
    tst.update(
        fit_id="authored-tst-fit",
        frequency_id="authored-release",
        frequency_role="release",
        kind="transition_state",
        transmission_coefficient=transmission,
        frequency_per_s=tst_frequency.tolist(),
    )
    tst_result = fit_thermal_rate(HydrogenThermalRateFit(**tst))
    tst_law = tst_result.values["frequency_law"]
    errors.update(
        transition_state_enthalpy_J_mol=abs(tst_law["activation_enthalpy_J_mol"] - enthalpy),
        transition_state_entropy_J_mol_K=abs(tst_law["activation_entropy_J_mol_K"] - entropy),
    )
    rates = thermal_trap_rates(
        HydrogenTrapThermalRates(
            trap_id="authored-trap",
            material_condition_id="authored-state",
            reference_lattice_id="authored-lattice",
            energy_reference_id="authored-zero",
            elapsed_time_origin_id="authored-clock",
            elapsed_time_s=[0.0, 1.0],
            temperature_K=[340.0, 450.0],
            supported_temperature_K=(300.0, 520.0),
            capture=ThermallyActivatedFrequency.model_validate_json(json.dumps(law)),
            release=ThermallyActivatedFrequency.model_validate_json(json.dumps(tst_law)),
            temperature_history_reviewed=True,
            frequency_parameterizations_reviewed=True,
            common_energy_reference_reviewed=True,
        )
    )
    if rates.status != "computed":
        raise AssertionError("fitted laws did not compose with the thermal-rate provider")
    errors["composed_rate_contract_failure"] = 0.0
    tolerances = {
        "arrhenius_log_prefactor": 1e-11,
        "arrhenius_activation_energy_J_mol": 1e-8,
        "holdout_exclusion_parameter_digest_changed": 0.0,
        "transition_state_enthalpy_J_mol": 1e-8,
        "transition_state_entropy_J_mol_K": 1e-10,
        "composed_rate_contract_failure": 0.0,
    }
    if any(errors[key] > tolerance for key, tolerance in tolerances.items()):
        raise AssertionError(errors)
    record = {
        "schema_version": "matintegrity.validation.hydrogen_thermal_rate_fit.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": (
            "Authored weighted-regression, holdout-exclusion and contract-composition verification; "
            "not experimental parameter calibration or independent validation."
        ),
        "absolute_errors": errors,
        "tolerances": tolerances,
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/hydrogen_calibration.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/hydrogen_thermal_rate_fit_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

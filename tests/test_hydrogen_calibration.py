import json
import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.hydrogen import R_J_mol_K
from matintegrity.models.hydrogen_calibration import HydrogenThermalRateFit, fit_thermal_rate
from matintegrity.models.hydrogen_rates import BOLTZMANN_J_K, PLANCK_J_S
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "authored-test",
    "origin": "synthetic",
    "citation": "Authored rate-fit observations",
}


def arrhenius_inputs():
    temperatures = [300.0, 350.0, 400.0, 450.0, 500.0, 375.0, 425.0]
    prefactor = 2.5e9
    activation = 42000.0
    frequencies = [prefactor * math.exp(-activation / (R_J_mol_K * t)) for t in temperatures]
    return {
        "fit_id": "fit-a",
        "frequency_id": "capture-a",
        "frequency_role": "capture",
        "kind": "arrhenius",
        "trap_id": "trap-a",
        "material_condition_id": "state-a",
        "reference_lattice_id": "lattice-a",
        "energy_reference_id": "lattice-zero-a",
        "observation_id": [f"obs-{i}" for i in range(len(temperatures))],
        "source_group_id": ["cal-source"] * 5 + ["holdout-source"] * 2,
        "partition": ["calibration"] * 5 + ["holdout"] * 2,
        "temperature_K": temperatures,
        "frequency_per_s": frequencies,
        "log_frequency_standard_uncertainty": [0.05] * len(temperatures),
        "minimum_calibration_temperature_span_K": 100.0,
        "calibration_observations_independent_reviewed": True,
        "rate_observation_mapping_reviewed": True,
        "common_energy_reference_reviewed": True,
        "holdout_partition_predeclared": True,
        "evidence": [EVIDENCE],
    }


def calculate(payload):
    return fit_thermal_rate(HydrogenThermalRateFit.model_validate_json(json.dumps(payload)))


def test_arrhenius_fit_recovers_parameters_and_known_uncertainty_covariance():
    result = calculate(arrhenius_inputs())
    law = result.values["frequency_law"]
    assert result.status == "computed"
    assert law["pre_exponential_frequency_per_s"] == pytest.approx(2.5e9, rel=1e-12)
    assert law["activation_energy_J_mol"] == pytest.approx(42000.0, rel=1e-12)
    assert result.values["holdout_log_frequency_rmse"] == pytest.approx(0.0, abs=1e-13)
    assert result.values["uncertainty_basis"] == "caller_supplied_log_frequency_standard_uncertainty"
    assert all(value > 0 for value in result.values["parameter_standard_uncertainty"])
    assert result.values["holdout_source_groups_disjoint"] is True


def test_transition_state_fit_recovers_enthalpy_entropy_with_fixed_transmission():
    payload = arrhenius_inputs()
    temperatures = payload["temperature_K"]
    enthalpy, entropy, transmission = 61000.0, -18.0, 0.65
    payload.update(
        kind="transition_state",
        transmission_coefficient=transmission,
        frequency_id="release-a",
        frequency_role="release",
        frequency_per_s=[
            transmission
            * BOLTZMANN_J_K
            * temperature
            / PLANCK_J_S
            * math.exp(entropy / R_J_mol_K)
            * math.exp(-enthalpy / (R_J_mol_K * temperature))
            for temperature in temperatures
        ],
    )
    result = calculate(payload)
    law = result.values["frequency_law"]
    assert law["activation_enthalpy_J_mol"] == pytest.approx(enthalpy, rel=1e-12)
    assert law["activation_entropy_J_mol_K"] == pytest.approx(entropy, rel=1e-12)
    assert law["transmission_coefficient"] == transmission


def test_holdout_values_never_change_fitted_parameters():
    baseline = calculate(arrhenius_inputs()).values["frequency_law"]
    changed = arrhenius_inputs()
    changed["frequency_per_s"][-2:] = [value * 3 for value in changed["frequency_per_s"][-2:]]
    result = calculate(changed)
    assert result.values["frequency_law"] == baseline
    assert result.values["holdout_log_frequency_rmse"] == pytest.approx(math.log(3.0))


@pytest.mark.parametrize(
    "flag",
    [
        "calibration_observations_independent_reviewed",
        "rate_observation_mapping_reviewed",
        "common_energy_reference_reviewed",
    ],
)
def test_unreviewed_calibration_basis_returns_needs_data(flag):
    payload = arrhenius_inputs()
    payload[flag] = False
    result = calculate(payload)
    assert result.status == "needs_data" and result.values == {}


def test_too_few_distinct_temperatures_and_small_span_are_not_identifiable():
    payload = arrhenius_inputs()
    payload["temperature_K"][:5] = [300.0, 300.0, 350.0, 350.0, 300.0]
    assert calculate(payload).status == "needs_data"
    payload = arrhenius_inputs()
    payload["minimum_calibration_temperature_span_K"] = 250.0
    result = calculate(payload)
    assert result.status == "needs_data"
    assert result.values["calibration_temperature_span_K"] == 200.0


def test_holdout_extrapolation_is_not_reported_as_validation():
    payload = arrhenius_inputs()
    payload["temperature_K"][-1] = 600.0
    assert calculate(payload).status == "out_of_scope"


def test_arrhenius_negative_activation_fit_is_out_of_scope():
    payload = arrhenius_inputs()
    payload["frequency_per_s"] = [1 / value for value in payload["frequency_per_s"]]
    result = calculate(payload)
    assert result.status == "out_of_scope"
    assert result.values["fitted_activation_energy_J_mol"] < 0


@pytest.mark.parametrize(
    "change,message",
    [
        ({"transmission_coefficient": 0.5}, "Arrhenius fitting"),
        ({"observation_id": ["same"] * 7}, "unique"),
        ({"source_group_id": ["group"]}, "aligned"),
        ({"log_frequency_standard_uncertainty": [0.1]}, "align"),
    ],
)
def test_contract_rejects_mixed_parameterizations_and_identity_misalignment(change, message):
    payload = arrhenius_inputs()
    payload.update(change)
    with pytest.raises(ValueError, match=message):
        HydrogenThermalRateFit.model_validate_json(json.dumps(payload))


def test_transition_state_requires_fixed_transmission_coefficient():
    payload = arrhenius_inputs()
    payload["kind"] = "transition_state"
    with pytest.raises(ValueError, match="fixed transmission"):
        HydrogenThermalRateFit.model_validate_json(json.dumps(payload))


def test_unweighted_fit_reports_residual_scatter_not_measurement_uncertainty():
    payload = arrhenius_inputs()
    payload["log_frequency_standard_uncertainty"] = None
    payload["frequency_per_s"][1] *= 1.02
    result = calculate(payload)
    assert result.status == "computed"
    assert result.values["uncertainty_basis"] == "residual_scatter_unweighted"
    assert result.values["residual_log_frequency_variance"] > 0


def test_registry_exposes_strict_json_rate_fit():
    registry = default_registry()
    assert "transport.hydrogen_thermal_rate_fit" in registry.list_models()
    result = registry.run_json(
        "transport.hydrogen_thermal_rate_fit",
        json.dumps(arrhenius_inputs()),
        RunContext(asset_id="asset-a", location_id="trap-a", time_basis="rate observations"),
    )
    assert result.status == "computed"

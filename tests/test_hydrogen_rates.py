import json
import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.hydrogen_kinetics import HydrogenKineticTrap
from matintegrity.models.hydrogen_rates import (
    BOLTZMANN_J_K,
    PLANCK_J_S,
    HydrogenTrapThermalRates,
    thermal_trap_rates,
)
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "authored-test",
    "origin": "synthetic",
    "citation": "Authored thermal-frequency test",
}


def law(name, *, kind="arrhenius", energy=40000.0, entropy=-20.0):
    if kind == "arrhenius":
        return {
            "frequency_id": name,
            "kind": kind,
            "pre_exponential_frequency_per_s": 1e8,
            "activation_energy_J_mol": energy,
            "evidence": [EVIDENCE],
        }
    return {
        "frequency_id": name,
        "kind": kind,
        "activation_enthalpy_J_mol": energy,
        "activation_entropy_J_mol_K": entropy,
        "transmission_coefficient": 0.7,
        "evidence": [EVIDENCE],
    }


def inputs():
    return {
        "trap_id": "trap-a",
        "material_condition_id": "state-a",
        "reference_lattice_id": "lattice-a",
        "energy_reference_id": "lattice-site-zero-a",
        "elapsed_time_origin_id": "heating-start",
        "elapsed_time_s": [0.0, 10.0],
        "temperature_K": [300.0, 600.0],
        "supported_temperature_K": [250.0, 700.0],
        "capture": law("capture"),
        "release": law("release", energy=70000.0),
        "temperature_history_reviewed": True,
        "frequency_parameterizations_reviewed": True,
        "common_energy_reference_reviewed": True,
    }


def calculate(payload):
    return thermal_trap_rates(HydrogenTrapThermalRates.model_validate_json(json.dumps(payload)))


def test_arrhenius_histories_and_rate_ratio_energy_match_independent_equations():
    x = inputs()
    result = calculate(x)
    assert result.status == "computed"
    expected_capture = [1e8 * math.exp(-40000 / (8.31446261815324 * t)) for t in (300, 600)]
    expected_release = [1e8 * math.exp(-70000 / (8.31446261815324 * t)) for t in (300, 600)]
    assert result.values["capture_frequency_per_s"] == pytest.approx(expected_capture)
    assert result.values["release_frequency_per_s"] == pytest.approx(expected_release)
    assert result.values["effective_rate_ratio_energy_J_mol"] == pytest.approx([30000.0] * 2)
    assert len(result.values["independent_rate_history_digest"]) == 64


def test_transition_state_histories_use_exact_si_constants_and_declared_entropy():
    x = inputs()
    x["capture"] = law("capture-tst", kind="transition_state", energy=45000.0, entropy=-30.0)
    x["release"] = law("release-tst", kind="transition_state", energy=65000.0, entropy=-10.0)
    result = calculate(x)
    assert result.status == "computed"
    expected = [
        0.7
        * BOLTZMANN_J_K
        * temperature
        / PLANCK_J_S
        * math.exp(-30 / 8.31446261815324)
        * math.exp(-45000 / (8.31446261815324 * temperature))
        for temperature in (300, 600)
    ]
    assert result.values["capture_frequency_per_s"] == pytest.approx(expected)
    assert result.values["constant_basis"]["si_constants_exact"] is True


def test_returned_rate_fragment_validates_as_an_independent_kinetic_trap():
    result = calculate(inputs())
    trap = HydrogenKineticTrap.model_validate_json(
        json.dumps(
            {
                "population": {
                    "trap_id": "trap-a",
                    "material_condition_id": "state-a",
                    "reference_lattice_id": "lattice-a",
                    "site_density_mol_m3": 1.0,
                    "binding_energy_J_mol": 30000.0,
                    "maximum_supported_occupancy": 1.0,
                    "evidence": [EVIDENCE],
                },
                "initial_occupancy": [0.0, 0.0],
                **result.values["independent_rate_contract_fields"],
            }
        )
    )
    assert trap.rate_model == "independent_frequencies"
    assert trap.release_frequency_per_s == result.values["release_frequency_per_s"]


@pytest.mark.parametrize(
    "flag",
    [
        "temperature_history_reviewed",
        "frequency_parameterizations_reviewed",
        "common_energy_reference_reviewed",
    ],
)
def test_unreviewed_rate_inputs_do_not_produce_frequencies(flag):
    x = inputs()
    x[flag] = False
    result = calculate(x)
    assert result.status == "needs_data" and result.values == {}


def test_temperature_support_and_floating_point_limits_are_not_extrapolated_or_clipped():
    outside = inputs()
    outside["temperature_K"][-1] = 701.0
    result = calculate(outside)
    assert result.status == "out_of_scope" and result.values == {}

    underflow = inputs()
    underflow["capture"]["activation_energy_J_mol"] = 1e9
    result = calculate(underflow)
    assert result.status == "out_of_scope"
    assert result.values["log_capture_frequency_per_s"][0] < -1000


@pytest.mark.parametrize("mutation", ["mixed", "missing", "clock", "support", "identity"])
def test_thermal_rate_contract_rejects_ambiguous_or_misaligned_inputs(mutation):
    x = inputs()
    if mutation == "mixed":
        x["capture"]["activation_enthalpy_J_mol"] = 1.0
    if mutation == "missing":
        x["release"].pop("activation_energy_J_mol")
    if mutation == "clock":
        x["temperature_K"].pop()
    if mutation == "support":
        x["supported_temperature_K"] = [700.0, 250.0]
    if mutation == "identity":
        x["release"]["frequency_id"] = x["capture"]["frequency_id"]
    with pytest.raises(ValueError):
        HydrogenTrapThermalRates.model_validate_json(json.dumps(x))


def test_registry_exposes_units_sources_and_strict_json_execution():
    registry = default_registry()
    model_id = "transport.hydrogen_trap_thermal_rates"
    description = registry.describe(model_id)
    assert description["output_units"]["capture_frequency_per_s"] == "1/s"
    assert "eyring_transition_state" in description["source_ids"]
    result = registry.run_json(
        model_id,
        json.dumps(inputs()),
        RunContext(asset_id="synthetic", location_id="trap", time_basis="elapsed seconds"),
    )
    assert result.status == "computed"
    assert result.values["trap_id"] == "trap-a"

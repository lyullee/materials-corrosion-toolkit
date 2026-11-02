import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.fabrication import WinterizationInventory, winterization_inventory
from matintegrity.registry import default_registry
from matintegrity.thermo import winterization_inputs_from_coolprop


def inputs(**updates):
    payload = {
        "case_id": "authored-winterization-case",
        "fluid_id": "Water",
        "pressure_Pa_abs": 101325.0,
        "inventory_mass_kg": 100.0,
        "initial_bulk_temperature_K": 300.0,
        "minimum_allowable_temperature_K": 280.0,
        "time_s": [0.0, 10000.0],
        "interval_ambient_temperature_K": [260.0],
        "interval_heat_loss_conductance_W_K": [50.0],
        "interval_heat_tracing_power_W": [0.0],
        "interval_effective_isobaric_heat_capacity_J_kg_K": [4180.0],
        "property_evaluation_temperature_K": [290.0],
        "property_phase": ["liquid"],
        "property_provider_id": "authored-constant-cp",
        "property_provider_version": "1",
        "property_history_digest": "0" * 64,
        "inventory_and_mixing_reviewed": True,
        "conductance_history_reviewed": True,
        "heat_tracing_history_reviewed": True,
        "property_states_reviewed": True,
        "minimum_temperature_reviewed": True,
    }
    payload.update(updates)
    return WinterizationInventory(**payload)


def test_constant_interval_matches_closed_form_and_crossing_time():
    result = winterization_inventory(inputs())
    expected = 260.0 + 40.0 * math.exp(-50.0 * 10000.0 / (100.0 * 4180.0))
    crossing = -100.0 * 4180.0 / 50.0 * math.log(0.5)
    assert result.values["bulk_temperature_K"][-1] == pytest.approx(expected)
    assert result.values["first_minimum_temperature_crossing_s"] == pytest.approx(crossing)
    assert result.values["minimum_temperature_margin_K"] == pytest.approx(expected - 280.0)


def test_interval_energy_balance_and_zero_conductance_heating():
    request = inputs(
        time_s=[0.0, 100.0, 200.0],
        interval_ambient_temperature_K=[290.0, 290.0],
        interval_heat_loss_conductance_W_K=[10.0, 0.0],
        interval_heat_tracing_power_W=[500.0, 500.0],
        interval_effective_isobaric_heat_capacity_J_kg_K=[4000.0, 4000.0],
        property_evaluation_temperature_K=[300.0, 300.0],
        property_phase=["liquid", "liquid"],
    )
    result = winterization_inventory(request)
    stored = 100.0 * 4000.0 * (result.values["bulk_temperature_K"][-1] - 300.0)
    supplied = result.values["cumulative_heat_tracing_energy_J"]
    lost = result.values["cumulative_environment_heat_loss_J"]
    assert supplied - lost == pytest.approx(stored)
    assert result.values["bulk_temperature_K"][-1] > result.values["bulk_temperature_K"][-2]


def test_missing_review_withholds_heat_balance():
    result = winterization_inventory(inputs(property_states_reviewed=False))
    assert result.status == "needs_data"
    assert "bulk_temperature_K" not in result.values


@pytest.mark.parametrize(
    "updates",
    [
        {"inventory_mass_kg": 1e308},
        {"inventory_mass_kg": 1e-300, "interval_effective_isobaric_heat_capacity_J_kg_K": [1e-300]},
        {"interval_heat_loss_conductance_W_K": [1e-308], "interval_heat_tracing_power_W": [1e308]},
        {"interval_heat_loss_conductance_W_K": [0.0], "interval_heat_tracing_power_W": [1e308]},
    ],
)
def test_unsupported_numeric_ranges_withhold_results(updates):
    result = winterization_inventory(inputs(**updates))
    assert result.status == "out_of_scope"
    assert result.values == {}


def test_small_heating_increment_is_retained():
    result = winterization_inventory(
        inputs(
            inventory_mass_kg=1.0,
            interval_effective_isobaric_heat_capacity_J_kg_K=[1.0],
            interval_heat_loss_conductance_W_K=[1e-20],
            interval_heat_tracing_power_W=[1e-8],
            time_s=[0.0, 1.0],
        )
    )
    assert result.status == "computed"
    assert result.values["bulk_temperature_K"][-1] - 300.0 == pytest.approx(1e-8, rel=1e-5)


def test_alignment_is_strict():
    with pytest.raises(ValueError, match="one ambient"):
        inputs(interval_ambient_temperature_K=[260.0, 260.0])


def test_cold_start_heating_preserves_initial_excursion():
    result = winterization_inventory(
        inputs(
            initial_bulk_temperature_K=270.0,
            time_s=[100.0, 10100.0],
            interval_heat_loss_conductance_W_K=[0.0],
            interval_heat_tracing_power_W=[1000.0],
        )
    )
    assert result.status == "computed"
    assert result.values["bulk_temperature_K"][-1] == pytest.approx(270.0 + 1e7 / 418000.0)
    assert result.values["minimum_temperature_margin_K"] == -10.0
    assert result.values["first_minimum_temperature_crossing_s"] == 100.0


def test_coolprop_builder_runs_registered_model_and_records_provider():
    payload = winterization_inputs_from_coolprop(
        case_id="coolprop-water",
        fluid="Water",
        pressure_Pa_abs=101325.0,
        inventory_mass_kg=100.0,
        initial_bulk_temperature_K=300.0,
        minimum_allowable_temperature_K=280.0,
        time_s=[0.0, 1000.0],
        interval_ambient_temperature_K=[270.0],
        interval_heat_loss_conductance_W_K=[20.0],
        interval_heat_tracing_power_W=[100.0],
        property_evaluation_temperature_K=[290.0],
    )
    assert payload["property_provider_id"] == "CoolProp:HEOS"
    assert 4000.0 < payload["interval_effective_isobaric_heat_capacity_J_kg_K"][0] < 4300.0
    result = default_registry().run(
        "fabrication.winterization_inventory",
        payload,
        RunContext(asset_id="synthetic", location_id="inventory", time_basis="authored interval clock"),
    )
    assert result.status == "computed"
    assert result.values["bulk_temperature_K"][-1] < 300.0

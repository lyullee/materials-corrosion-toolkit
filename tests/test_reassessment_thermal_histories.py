import math

import pytest

from matintegrity.models.thermohistory import (
    CoolingInterval,
    CylindricalLayers,
    HeatTreatmentHistory,
    LumpedTemperature,
    cooling_interval,
    cylindrical_layers,
    heat_treatment_history,
    lumped_temperature,
)


def test_radial_heat_balance_against_three_equal_series_resistances():
    x = CylindricalLayers(
        radii_m=[0.1, 0.2],
        conductivity_W_m_K=[math.log(2) / (2 * math.pi)],
        length_m=1.0,
        inner_fluid_temperature_K=400.0,
        ambient_temperature_K=300.0,
        radiative_environment_temperature_K=300.0,
        inner_convection_W_m2_K=1 / (2 * math.pi * 0.1),
        outer_convection_W_m2_K=1 / (2 * math.pi * 0.2),
        outer_emissivity=0.0,
    )
    result = cylindrical_layers(x)
    assert result.values["heat_rate_outward_W"] == pytest.approx(100 / 3)
    assert result.values["interface_temperatures_K"] == pytest.approx([400 - 100 / 3, 300 + 100 / 3])
    assert result.values["outer_balance_residual_W"] == pytest.approx(0.0, abs=1e-7)
    cold = cylindrical_layers(x.model_copy(update={"inner_fluid_temperature_K": 200.0}))
    assert cold.values["heat_rate_outward_W"] == pytest.approx(-100 / 3)


def test_uniform_solid_time_constant_initial_state_and_biot_gate():
    x = LumpedTemperature(
        initial_temperature_K=400.0,
        ambient_temperature_K=300.0,
        heat_capacity_J_K=100.0,
        surface_area_m2=1.0,
        convection_W_m2_K=10.0,
        solid_conductivity_W_m_K=100.0,
        characteristic_length_m=0.01,
        maximum_declared_biot=0.1,
        exposure_s=10.0,
    )
    assert lumped_temperature(x).values["temperature_K"] == pytest.approx(300 + 100 / math.e)
    assert lumped_temperature(x.model_copy(update={"exposure_s": 0.0})).values["temperature_K"] == 400.0
    assert lumped_temperature(x.model_copy(update={"maximum_declared_biot": 0.0001})).status == "out_of_scope"


def test_multi_sensor_hold_intersection_and_clock_translation():
    x = HeatTreatmentHistory(
        time_s=[0.0, 10.0, 20.0, 30.0],
        sensor_temperature_K=[[300.0, 500.0, 500.0, 300.0], [300.0, 400.0, 500.0, 300.0]],
        minimum_hold_temperature_K=400.0,
        maximum_hold_temperature_K=500.0,
    )
    result = heat_treatment_history(x)
    assert result.values["simultaneous_hold_intervals_s"] == [[10.0, 25.0]]
    assert result.values["total_simultaneous_hold_s"] == 15.0
    shifted = heat_treatment_history(x.model_copy(update={"time_s": [1000 + t for t in x.time_s]}))
    assert shifted.values["simultaneous_hold_intervals_s"] == [[1010.0, 1025.0]]
    assert shifted.values["total_simultaneous_hold_s"] == 15.0


def test_interrupted_hold_does_not_become_one_continuous_hold():
    result = heat_treatment_history(
        HeatTreatmentHistory(
            time_s=[0.0, 1.0, 2.0, 3.0, 4.0],
            sensor_temperature_K=[[450.0, 450.0, 350.0, 450.0, 450.0]],
            minimum_hold_temperature_K=400.0,
            maximum_hold_temperature_K=500.0,
        )
    )
    assert result.values["simultaneous_hold_intervals_s"] == [[0.0, 1.5], [2.5, 4.0]]
    assert result.values["total_simultaneous_hold_s"] == 3.0
    assert result.values["longest_continuous_hold_s"] == 1.5


@pytest.mark.parametrize("scale", [1e-10, 1e10])
def test_hold_segmentation_is_invariant_to_elapsed_time_scale(scale):
    result = heat_treatment_history(
        HeatTreatmentHistory(
            time_s=[scale * t for t in (0.0, 1.0, 2.0, 3.0, 4.0)],
            sensor_temperature_K=[[450.0, 450.0, 350.0, 450.0, 450.0]],
            minimum_hold_temperature_K=400.0,
            maximum_hold_temperature_K=500.0,
        )
    )
    assert len(result.values["simultaneous_hold_intervals_s"]) == 2
    assert result.values["total_simultaneous_hold_s"] / scale == pytest.approx(3.0)
    assert result.values["longest_continuous_hold_s"] / scale == pytest.approx(1.5)


def test_cooling_plateau_keeps_explicit_branch_and_first_entry():
    x = CoolingInterval(
        time_s=[0.0, 1.0, 2.0, 3.0, 4.0],
        temperature_K=[800.0, 700.0, 700.0, 500.0, 400.0],
        upper_temperature_K=700.0,
        lower_temperature_K=500.0,
    )
    full = cooling_interval(x)
    selected = cooling_interval(x.model_copy(update={"cooling_branch_start_index": 2}))
    assert full.values["cooling_interval_s"] == 2.0
    assert selected.values["cooling_interval_s"] == 1.0
    assert selected.values["selected_branch_sha256"] != full.values["selected_branch_sha256"]

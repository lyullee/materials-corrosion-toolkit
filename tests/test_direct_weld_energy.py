"""Independent energy accounting and compatibility for direct power/energy APIs."""
import pytest
from pydantic import ValidationError

from matintegrity.models.fabrication import (
    ArcEnergy,
    MeasuredWeldEnergy,
    WaveformEnergy,
    WeldPowerTravel,
    arc_energy,
    measured_weld_energy,
    waveform_energy,
    weld_power_travel,
)


def test_one_kilojoule_over_one_centimetre_has_declared_si_heat_input():
    result = measured_weld_energy(MeasuredWeldEnergy(
        source_energy_J=1000.0, weld_length_m=0.01, efficiency=0.8,
    ))
    assert result.values["source_energy_per_length_J_m"] == pytest.approx(100_000.0)
    assert result.values["net_heat_input_J_m"] == pytest.approx(80_000.0)


def test_same_constant_process_agrees_across_four_measurement_representations():
    # 20 V * 200 A for 2 s deposits 0.2 m: 8 kJ and 40 kJ/m source energy.
    measured = measured_weld_energy(MeasuredWeldEnergy(
        source_energy_J=8000.0, weld_length_m=0.2, efficiency=0.75,
    ))
    power = weld_power_travel(WeldPowerTravel(
        source_power_W=4000.0, travel_speed_m_s=0.1, efficiency=0.75,
    ))
    arc = arc_energy(ArcEnergy(
        voltage_V=20.0, current_A=200.0, travel_speed_m_s=0.1, efficiency=0.75,
    ))
    waveform = waveform_energy(WaveformEnergy(
        time_s=[0.0, 1.0, 2.0], voltage_V=[20.0] * 3, current_A=[200.0] * 3,
        travel_distance_m=0.2, efficiency=0.75,
    ))
    for result in (measured, power, arc, waveform):
        assert result.values["net_heat_input_J_m"] == pytest.approx(30_000.0)


def test_energy_per_length_is_invariant_under_equal_observation_partition():
    for fraction in (0.1, 0.25, 1.0, 4.0):
        result = measured_weld_energy(MeasuredWeldEnergy(
            source_energy_J=8000.0 * fraction,
            weld_length_m=0.2 * fraction, efficiency=0.75,
        ))
        assert result.values["net_heat_input_J_m"] == pytest.approx(30_000.0)


def test_direct_energy_models_are_callable_through_public_registry():
    from matintegrity.contracts import RunContext
    from matintegrity.registry import default_registry

    registry = default_registry()
    context = RunContext(asset_id="synthetic-weld", location_id="joint-1", time_basis="test interval")
    for model_id, inputs in (
        ("welding.measured_energy_per_length", {
            "source_energy_J": 8000.0, "weld_length_m": 0.2, "efficiency": 0.75,
        }),
        ("welding.power_travel_energy", {
            "source_power_W": 4000.0, "travel_speed_m_s": 0.1, "efficiency": 0.75,
        }),
    ):
        result = registry.run(model_id, inputs, context)
        assert result.status == "computed"
        assert result.values["net_heat_input_J_m"] == pytest.approx(30_000.0)


@pytest.mark.parametrize("contract,inputs", [
    (MeasuredWeldEnergy, {"source_energy_J": -1.0, "weld_length_m": 0.1, "efficiency": 0.8}),
    (MeasuredWeldEnergy, {"source_energy_J": 1.0, "weld_length_m": 0.0, "efficiency": 0.8}),
    (WeldPowerTravel, {"source_power_W": 1.0, "travel_speed_m_s": 0.0, "efficiency": 0.8}),
    (WeldPowerTravel, {"source_power_W": 1.0, "travel_speed_m_s": 0.1, "efficiency": 1.1}),
])
def test_invalid_measurement_or_efficiency_is_rejected(contract, inputs):
    with pytest.raises(ValidationError):
        contract(**inputs)

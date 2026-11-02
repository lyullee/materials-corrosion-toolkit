import pytest

from matintegrity.models.testmethods import GasPressureDecay, gas_pressure_decay
from matintegrity.thermo import gas_pressure_decay_inputs_from_coolprop


def test_coolprop_real_gas_adapter_preserves_states_and_runs():
    pytest.importorskip("CoolProp")
    values = gas_pressure_decay_inputs_from_coolprop(
        fluid="Nitrogen",
        rigid_volume_m3=0.1,
        initial_absolute_pressure_Pa=200000.0,
        final_absolute_pressure_Pa=180000.0,
        initial_temperature_K=300.0,
        final_temperature_K=300.0,
        duration_s=100.0,
        reference_pressure_Pa=101325.0,
        reference_temperature_K=293.15,
    )
    model = GasPressureDecay.model_validate(values)
    result = gas_pressure_decay(model)
    assert result.values["net_molar_outflow_mol_s"] > 0
    assert result.values["property_provider_id"] == "CoolProp:HEOS"
    assert len(result.values["property_state_digest"]) == 64


def test_adapter_rejects_nonpositive_absolute_state():
    pytest.importorskip("CoolProp")
    with pytest.raises(ValueError, match="must be positive"):
        gas_pressure_decay_inputs_from_coolprop(
            fluid="Nitrogen",
            rigid_volume_m3=0.1,
            initial_absolute_pressure_Pa=0.0,
            final_absolute_pressure_Pa=180000.0,
            initial_temperature_K=300.0,
            final_temperature_K=300.0,
            duration_s=100.0,
            reference_pressure_Pa=101325.0,
            reference_temperature_K=293.15,
        )


def test_partial_provider_provenance_is_rejected():
    with pytest.raises(ValueError, match="complete and reviewed"):
        GasPressureDecay(
            rigid_volume_m3=0.1,
            initial_absolute_pressure_Pa=200000.0,
            final_absolute_pressure_Pa=180000.0,
            initial_temperature_K=300.0,
            final_temperature_K=300.0,
            initial_compressibility_factor=1.0,
            final_compressibility_factor=1.0,
            duration_s=100.0,
            reference_pressure_Pa=101325.0,
            reference_temperature_K=293.15,
            reference_compressibility_factor=1.0,
            fluid_id="Nitrogen",
        )

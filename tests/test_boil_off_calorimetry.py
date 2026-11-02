import pytest

from matintegrity.contracts import Evidence, RunContext, canonical_digest
from matintegrity.models.testmethods import (
    BoilOffCalorimetry,
    SaturationCalorimetryState,
    boil_off_calorimetry,
    specifications,
)
from matintegrity.registry import ModelRegistry


def state(**changes):
    values = (
        dict(
            fluid_id="synthetic",
            pressure_Pa=100000.0,
            temperature_K=80.0,
            liquid_density_kg_m3=100.0,
            vapor_density_kg_m3=10.0,
            liquid_enthalpy_J_kg=-10000.0,
            vapor_enthalpy_J_kg=190000.0,
            provider_id="synthetic-properties",
            provider_version="1",
            provider_revision="1",
        )
        | changes
    )
    return SaturationCalorimetryState(
        **values,
        provider_state_digest=canonical_digest(values),
        evidence=(Evidence(source_id="synthetic", origin="synthetic", citation="authored balance test"),),
    )


def inputs(**changes):
    return BoilOffCalorimetry(
        **(
            dict(
                saturation_state=state(),
                escaping_vapor_mass_flow_kg_s=0.009,
                inventory_mode="falling_liquid_level_rigid_vessel",
                isobaric_saturated_bath_reviewed=True,
                flow_is_escaping_vapor_mass_at_bath_outlet_reviewed=True,
                inventory_mode_and_no_other_mass_exchange_reviewed=True,
                sensible_transient_and_other_energy_terms_negligible_reviewed=True,
                property_state_and_measurement_applicability_reviewed=True,
            )
            | changes
        )
    )


def test_falling_level_mass_and_energy_closure():
    result = boil_off_calorimetry(inputs())
    assert result.values["liquid_to_vapor_mass_rate_kg_s"] == pytest.approx(0.01)
    assert result.values["vapor_accumulation_mass_rate_kg_s"] == pytest.approx(0.001)
    assert result.values["total_bath_heat_input_W"] == pytest.approx(2000.0)
    # Accumulated vapor fills the vacated liquid volume at fixed vessel volume.
    assert result.values["vapor_accumulation_mass_rate_kg_s"] / 10 == pytest.approx(0.01 / 100)


def test_constant_level_and_signed_residual():
    result = boil_off_calorimetry(
        inputs(
            inventory_mode="constant_level_saturated_liquid_makeup", separately_accounted_heat_input_W=2000.0
        )
    )
    assert result.values["escaping_flow_correction_factor"] == 1.0
    assert result.values["vapor_accumulation_mass_rate_kg_s"] == 0.0
    assert result.values["residual_heat_input_W"] == pytest.approx(-200.0)


def test_enthalpy_reference_invariance_and_zero_flow():
    shifted = boil_off_calorimetry(
        inputs(saturation_state=state(liquid_enthalpy_J_kg=990000.0, vapor_enthalpy_J_kg=1190000.0))
    )
    assert shifted.values["total_bath_heat_input_W"] == pytest.approx(2000.0)
    assert (
        boil_off_calorimetry(inputs(escaping_vapor_mass_flow_kg_s=0.0)).values["total_bath_heat_input_W"]
        == 0.0
    )


def test_property_identity_and_phase_rejection():
    with pytest.raises(ValueError, match="digest mismatch"):
        SaturationCalorimetryState.model_validate(state().model_dump() | {"temperature_K": 81.0})
    with pytest.raises(ValueError, match="distinct saturated phases"):
        state(vapor_density_kg_m3=100.0)
    with pytest.raises(ValueError, match="positive vaporization"):
        state(vapor_enthalpy_J_kg=-10000.0)


def test_review_gate_and_public_exchange():
    assert boil_off_calorimetry(inputs(isobaric_saturated_bath_reviewed=False)).status == "needs_data"
    registry = ModelRegistry()
    registry.register(next(s for s in specifications() if s.model_id == "inspection.boil_off_calorimetry"))
    context = RunContext(asset_id="synthetic", location_id="bath", time_basis="test")
    python = registry.run("inspection.boil_off_calorimetry", inputs(), context)
    serialized = registry.run_json("inspection.boil_off_calorimetry", inputs().model_dump_json(), context)
    assert python.model_dump() == serialized.model_dump()


def test_optional_coolprop_saturation_pair():
    pytest.importorskip("CoolProp")
    from matintegrity.thermo import boil_off_saturation_state_from_coolprop

    value = boil_off_saturation_state_from_coolprop(fluid="Nitrogen", pressure_Pa=101325.0)
    assert value.liquid_density_kg_m3 > value.vapor_density_kg_m3
    assert value.vapor_enthalpy_J_kg > value.liquid_enthalpy_J_kg
    assert 70 < value.temperature_K < 90
    assert value.provider_id == "CoolProp:HEOS"
    with pytest.raises(ValueError, match="single pure-fluid"):
        boil_off_saturation_state_from_coolprop(fluid="Nitrogen&Oxygen", pressure_Pa=101325.0)

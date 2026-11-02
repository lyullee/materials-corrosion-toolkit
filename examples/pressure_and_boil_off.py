"""Synthetic pressure-rule and calorimetry examples, not engineering limits."""
from matintegrity.contracts import Evidence, RunContext, canonical_digest
from matintegrity.models.engineering_correlations import ReliefPressureEnvelope
from matintegrity.models.testmethods import BoilOffCalorimetry, SaturationCalorimetryState
from matintegrity.registry import default_registry


def sample_requests():
    properties = dict(fluid_id="synthetic", pressure_Pa=100000.0, temperature_K=80.0,
        liquid_density_kg_m3=100.0, vapor_density_kg_m3=10.0,
        liquid_enthalpy_J_kg=0.0, vapor_enthalpy_J_kg=200000.0,
        provider_id="synthetic", provider_version="1", provider_revision="1")
    state = SaturationCalorimetryState(**properties, provider_state_digest=canonical_digest(properties),
        evidence=(Evidence(source_id="synthetic", origin="synthetic", citation="authored API example"),))
    boil_off = BoilOffCalorimetry(saturation_state=state, escaping_vapor_mass_flow_kg_s=0.009,
        inventory_mode="falling_liquid_level_rigid_vessel", isobaric_saturated_bath_reviewed=True,
        flow_is_escaping_vapor_mass_at_bath_outlet_reviewed=True,
        inventory_mode_and_no_other_mass_exchange_reviewed=True,
        sensible_transient_and_other_energy_terms_negligible_reviewed=True,
        property_state_and_measurement_applicability_reviewed=True)
    pressure = dict(equipment_allowable_gauge_pressure_Pa=1000.0, device_set_gauge_pressure_Pa=1000.0,
        peak_equipment_gauge_pressure_Pa=1125.0, gauge_reference_id="declared-ambient",
        maximum_set_pressure_multiplier=1.0, fractional_accumulation_allowance=0.125,
        absolute_accumulation_allowance_Pa=150.0, allowance_combination="larger_of", scenario_id="synthetic")
    digest = canonical_digest(pressure)
    envelope = ReliefPressureEnvelope(**pressure, basis=dict(source_id="synthetic-rule", revision="1",
        license_id="authored-example", record_sha256=digest, applicability_and_units_reviewed=True,
        computational_use_authorized=True, evidence=(dict(source_id="synthetic-rule", origin="synthetic",
            citation="Authored parameters, not standard limits", license_id="authored-example", sha256=digest),)))
    return (("inspection.boil_off_calorimetry", boil_off), ("design.relief_pressure_envelope", envelope))


if __name__ == "__main__":
    registry = default_registry()
    context = RunContext(asset_id="synthetic", location_id="bath-and-device", time_basis="example")
    for model_id, inputs in sample_requests():
        print(registry.run(model_id, inputs, context).model_dump_json(indent=2))

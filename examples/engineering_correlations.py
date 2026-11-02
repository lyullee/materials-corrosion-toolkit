"""Synthetic inputs for direct energy and caller-owned engineering correlations."""
from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    CarbonEquivalentRecipe,
    CouplingPressure,
    FluxMoistureHydrogen,
    PipingDisplacementAllowance,
    ThreadConnectionPressure,
    WeldCoolingCorrelation,
)
from matintegrity.models.fabrication import MeasuredPipeOvality, MeasuredWeldEnergy, WeldPowerTravel
from matintegrity.models.inspection import PipeMembraneTestPressure, ReferenceEnergyMass


def bind(contract, payload):
    """Pin explicit coefficients and inputs; synthetic values are not material data."""
    complete = {key: field.default for key, field in contract.model_fields.items()
                if key != "basis" and not field.is_required()}
    complete.update(payload)
    digest = canonical_digest(complete)
    return contract(**complete, basis={
        "source_id": "synthetic-example", "revision": "1", "license_id": "synthetic-example",
        "record_sha256": digest, "applicability_and_units_reviewed": True,
        "computational_use_authorized": True,
        "evidence": ({"source_id": "synthetic-example", "origin": "synthetic",
                      "citation": "Toy coefficients for API wiring, not physical qualification.",
                      "license_id": "synthetic-example", "sha256": digest},),
    })


def sample_requests():
    return [
        ("fabrication.measured_pipe_ovality", MeasuredPipeOvality(
            maximum_diameter_m=0.11, minimum_diameter_m=0.09, reference_basis="nominal",
            nominal_diameter_m=0.1)),
        ("welding.carbon_equivalent_recipe", bind(CarbonEquivalentRecipe, {
            "method_id": "synthetic-linear-index", "chemistry_mass_percent": {"C": 0.1, "Mn": 1.0},
            "base_carbon_multiplier": 1.0,
            "terms": ({"term_id": "Mn", "coefficient": 0.5, "numerator_element": "Mn",
                       "denominator_element": None},),
        })),
        ("welding.measured_energy_per_length", MeasuredWeldEnergy(
            source_energy_J=8000.0, weld_length_m=0.2, efficiency=0.75)),
        ("welding.power_travel_energy", WeldPowerTravel(
            source_power_W=4000.0, travel_speed_m_s=0.1, efficiency=0.75)),
        ("inspection.pipe_membrane_test_pressure", PipeMembraneTestPressure(
            outside_diameter_m=0.2, wall_thickness_m=0.01, yield_strength_Pa=400e6,
            declared_yield_fraction=0.8, factor_basis="Synthetic factor, not a grade rule.",
            geometry_material_and_factor_applicability_reviewed=True)),
        ("inspection.reference_energy_mass", ReferenceEnergyMass(
            energy_J=2e6, reference_specific_energy_J_kg=4e6,
            reference_id="synthetic-reference", energy_basis="declared work")),
        ("piping.displacement_stress_allowance", bind(PipingDisplacementAllowance, {
            "variant": "base", "cold_allowable_Pa": 100e6, "hot_allowable_Pa": 80e6,
            "cycle_reduction_factor": 0.5, "cold_multiplier": 1.0, "hot_multiplier": 1.0,
        })),
        ("welding.cooling_time_correlation", bind(WeldCoolingCorrelation, {
            "heat_flow_dimension": 2, "preheat_temperature_K": 300.0,
            "lower_temperature_K": 500.0, "upper_temperature_K": 800.0,
            "net_heat_input_J_m": 1000.0, "plate_thickness_m": 0.01, "shape_factor": 1.0,
            "coefficient_reference_temperature_K": 300.0, "coefficient_at_reference": 0.001,
            "coefficient_temperature_slope_per_K": 0.0, "coefficient_unit": "s*m^4*K^2/J^2",
            "minimum_valid_preheat_K": 290.0, "maximum_valid_preheat_K": 400.0,
        })),
        ("welding.flux_moisture_hydrogen", bind(FluxMoistureHydrogen, {
            "combined_water_mass_fraction": 0.02, "absorbed_water_mass_fraction": 0.01,
            "water_vapor_partial_pressure_Pa": 1000.0, "intercept_m3_H2_kg_deposit": 0.0,
            "combined_water_coefficient_m3_H2_kg_deposit": 0.01,
            "absorbed_water_coefficient_m3_H2_kg_deposit": 0.02,
            "vapor_coefficient_m3_H2_kg_deposit_Pa": 1e-8,
            "maximum_valid_combined_water_fraction": 0.1,
            "maximum_valid_absorbed_water_fraction": 0.1, "maximum_valid_vapor_pressure_Pa": 2000.0,
            "gas_volume_reference_temperature_K": 300.0, "gas_volume_reference_pressure_Pa": 100000.0,
        })),
        ("inspection.coupling_pressure", bind(CouplingPressure, {
            "outside_diameter_m": 0.2, "thread_root_diameter_m": 0.1,
            "yield_strength_Pa": 400e6, "declared_strength_factor": 0.8,
        })),
        ("inspection.thread_connection_pressure", bind(ThreadConnectionPressure, {
            "outside_diameter_m": 0.2, "seal_pitch_diameter_m": 0.1, "elastic_modulus_Pa": 200e9,
            "diametral_taper_m_m": 0.1, "power_turn_count": 2.0, "thread_pitch_m_per_turn": 0.001,
        })),
    ]


if __name__ == "__main__":
    from matintegrity.registry import default_registry

    registry = default_registry()
    context = RunContext(asset_id="synthetic-asset", location_id="synthetic-location", time_basis="demo")
    for model_id, request in sample_requests():
        print(registry.run(model_id, request, context).model_dump_json(indent=2))

"""Synthetic inputs for existing mechanics, materials and thermal APIs."""

from matintegrity.contracts import RunContext
from matintegrity.models.materials import DissolutionCharge, DuctilityComparison, TensilePoint
from matintegrity.models.mechanics import (
    Cylinder,
    PlaneStress,
    PressureTemperatureEnvelope,
    StressIntensity,
    ThermalRestraint,
)
from matintegrity.models.thermohistory import (
    CoolingInterval,
    CylindricalLayers,
    HeatTreatmentHistory,
    LumpedTemperature,
)
from matintegrity.registry import default_registry


def sample_requests():
    return (
        (
            "mechanics.lame_cylinder",
            Cylinder(
                inner_radius_m=0.1,
                outer_radius_m=0.2,
                internal_pressure_Pa=1e6,
                external_pressure_Pa=0.0,
                evaluation_radius_m=0.1,
                closed_ends=True,
            ),
        ),
        ("mechanics.plane_stress", PlaneStress(stress_x_Pa=1e6, stress_y_Pa=-0.5e6, shear_xy_Pa=0.2e6)),
        (
            "mechanics.thermal_restraint",
            ThermalRestraint(
                young_modulus_Pa=200e9,
                expansion_coefficient_per_K=1e-5,
                temperature_change_K=100.0,
                restraint_fraction=0.25,
            ),
        ),
        (
            "fracture.stress_intensity",
            StressIntensity(
                crack_depth_m=0.001,
                tensile_stress_Pa=100e6,
                geometry_factor=1.2,
                fracture_toughness_Pa_sqrt_m=50e6,
            ),
        ),
        (
            "materials.tensile_point",
            TensilePoint(
                force_N=1000.0,
                initial_area_m2=1e-4,
                extension_m=0.01,
                gauge_length_m=0.1,
                uniform_deformation_declared=True,
            ),
        ),
        (
            "materials.ductility_retention",
            DuctilityComparison(baseline_elongation_fraction=0.2, exposed_elongation_fraction=0.3),
        ),
        (
            "corrosion.charge_to_loss",
            DissolutionCharge(
                anodic_charge_C=100.0,
                equivalent_weight_kg_mol_electron=0.02,
                density_kg_m3=8000.0,
                current_efficiency=0.5,
            ),
        ),
        (
            "thermal.cylindrical_layers",
            CylindricalLayers(
                radii_m=[0.1, 0.2],
                conductivity_W_m_K=[1.0],
                length_m=1.0,
                inner_fluid_temperature_K=400.0,
                ambient_temperature_K=300.0,
                radiative_environment_temperature_K=300.0,
                inner_convection_W_m2_K=10.0,
                outer_convection_W_m2_K=10.0,
                outer_emissivity=0.0,
            ),
        ),
        (
            "thermal.lumped_temperature",
            LumpedTemperature(
                initial_temperature_K=400.0,
                ambient_temperature_K=300.0,
                heat_capacity_J_K=100.0,
                surface_area_m2=1.0,
                convection_W_m2_K=10.0,
                solid_conductivity_W_m_K=100.0,
                characteristic_length_m=0.01,
                maximum_declared_biot=0.1,
                exposure_s=10.0,
            ),
        ),
        (
            "welding.heat_treatment_history",
            HeatTreatmentHistory(
                time_s=[0.0, 10.0, 20.0, 30.0],
                sensor_temperature_K=[[300.0, 500.0, 500.0, 300.0], [300.0, 400.0, 500.0, 300.0]],
                minimum_hold_temperature_K=400.0,
                maximum_hold_temperature_K=500.0,
            ),
        ),
        (
            "welding.cooling_interval",
            CoolingInterval(
                time_s=[0.0, 1.0, 2.0, 3.0],
                temperature_K=[800.0, 700.0, 500.0, 400.0],
                upper_temperature_K=700.0,
                lower_temperature_K=500.0,
            ),
        ),
        (
            "structural.pressure_temperature_envelope",
            PressureTemperatureEnvelope(
                envelope_id="synthetic-curve",
                applicability_basis="authored curve for numerical demonstration",
                source_sha256="0" * 64,
                knots=[
                    dict(temperature_K=300.0, allowable_pressure_Pa=1000.0),
                    dict(temperature_K=400.0, allowable_pressure_Pa=800.0),
                ],
                operating_points=[dict(point_id="synthetic-design", temperature_K=350.0, pressure_Pa=850.0)],
                applicability_reviewed=True,
                operating_points_reviewed=True,
            ),
        ),
    )


if __name__ == "__main__":
    registry = default_registry()
    context = RunContext(asset_id="synthetic", location_id="specimen", time_basis="example")
    for model_id, inputs in sample_requests():
        print(registry.run(model_id, inputs, context).model_dump_json(indent=2))

"""Small synthetic examples for two caller-parameterized models.

All values in this file are invented for API illustration; they are not
engineering data, fitted material properties, or a design recommendation.
"""

from hashlib import sha256

from matintegrity.contracts import Evidence
from matintegrity.models.gasket_leakage_map_fit import (
    GasketLeakageFitObservation,
    GasketLeakageMapFit,
    fit_gasket_leakage_map,
)
from matintegrity.models.scale_moving_boundary import (
    PlanarScaleDiffusionReactionHistory,
    ScaleDiffusionReactionInterval,
    planar_scale_diffusion_reaction_history,
)


SYNTHETIC_FIXTURE_SHA256 = sha256(b"project-authored synthetic API fixture v1").hexdigest()

synthetic_evidence = Evidence(
    source_id="example-synthetic-inputs",
    origin="synthetic",
    citation="Project-authored synthetic API fixture; not measured data",
    sha256=SYNTHETIC_FIXTURE_SHA256,
)

scale_input = PlanarScaleDiffusionReactionHistory(
    assessment_id="example-scale-run",
    physical_scope_id="example-coupon",
    clock_id="example-clock",
    scale_phase_id="caller-defined-scale",
    transported_species_id="caller-defined-species",
    provider_id="example-synthetic-inputs",
    provider_revision="1",
    configuration_sha256="b" * 64,
    initial_thickness_m=1e-6,
    scale_molar_volume_m3_mol=2e-5,
    temperature_support_min_K=273.15,
    temperature_support_max_K=373.15,
    intervals=(ScaleDiffusionReactionInterval(
        interval_id="step-1",
        start_time_s=0.0,
        end_time_s=3600.0,
        effective_diffusivity_m2_s=1e-14,
        interface_transfer_coefficient_m_s=1e-8,
        signed_reservoir_driving_concentration_mol_m3=100.0,
        temperature_K=298.15,
    ),),
    fixed_planar_area_dense_single_phase_reviewed=True,
    quasi_steady_series_resistance_and_reservoir_reviewed=True,
    signed_driving_force_and_one_to_one_molar_balance_reviewed=True,
    interval_properties_and_temperature_support_reviewed=True,
    computational_use_authorized=True,
    evidence=(synthetic_evidence,),
)
scale_result = planar_scale_diffusion_reaction_history(scale_input)

observations = tuple(
    GasketLeakageFitObservation(
        observation_id=f"synthetic-{index}",
        physical_specimen_id=f"specimen-{index}",
        source_group_id="one-synthetic-source-group",
        source_sha256=SYNTHETIC_FIXTURE_SHA256,
        role="calibration",
        contact_pressure_Pa=pressure,
        differential_pressure_Pa=delta_pressure,
        molar_leak_flux_mol_s_m2=flux,
        residual_scale_mol_s_m2=1e-9,
    )
    for index, (pressure, delta_pressure, flux) in enumerate((
        (0.0, 0.0, 0.0),
        (1e6, 0.0, 0.0),
        (0.0, 1e5, 2e-8),
        (1e6, 1e5, 1e-8),
    ))
)
gasket_input = GasketLeakageMapFit(
    assessment_id="example-gasket-fit",
    joint_scope_id="example-joint",
    calibration_id="synthetic-map-v1",
    contact_pressure_knots_Pa=(0.0, 1e6),
    differential_pressure_knots_Pa=(0.0, 1e5),
    observations=observations,
    observation_units_and_scope_reviewed=True,
    predeclared_partition_and_source_independence_reviewed=True,
    bilinear_nonnegative_surface_and_residual_scale_reviewed=True,
    pointwise_computational_use_authorized=True,
    evidence=(synthetic_evidence,),
)
gasket_result = fit_gasket_leakage_map(gasket_input)

if __name__ == "__main__":
    print("scale:", scale_result.model_dump(mode="json"))
    print("gasket:", gasket_result.model_dump(mode="json"))

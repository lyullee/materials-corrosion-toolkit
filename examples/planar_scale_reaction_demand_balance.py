"""Construct synthetic inputs only; no model calculation is executed."""

from matintegrity.contracts import Evidence
from matintegrity.models.scale_reaction_demand_balance import (
    PlanarScaleReactionDemandBalance,
    ScaleReactionDemandInterval,
)

request = PlanarScaleReactionDemandBalance(
    assessment_id="synthetic-scale-demand",
    physical_scope_id="synthetic-planar-surface",
    clock_id="synthetic-seconds",
    scale_phase_id="synthetic-solid",
    transported_reactant_id="synthetic-reactant",
    demand_reaction_id="synthetic-consumption",
    provider_id="synthetic-provider",
    provider_revision="fixture-1",
    parameter_record_sha256="a" * 64,
    initial_scale_thickness_m=1e-6,
    scale_molar_volume_m3_mol=3e-5,
    transported_reactant_moles_per_scale_mole=1.0,
    electrons_per_reaction_extent=2.0,
    consumed_scale_moles_per_reaction_extent=1.0,
    consuming_partial_current_sign="negative",
    temperature_support_min_K=290.0,
    temperature_support_max_K=310.0,
    intervals=(ScaleReactionDemandInterval(
        interval_id="synthetic-current-interval",
        start_time_s=0.0,
        end_time_s=100.0,
        temperature_K=298.15,
        effective_diffusivity_m2_s=1e-10,
        interface_transfer_coefficient_m_s=1e-5,
        reservoir_driving_concentration_mol_m3=1.0,
        signed_partial_current_density_A_m2=-0.01,
    ),),
    fixed_planar_dense_single_phase_and_area_reviewed=True,
    quasi_steady_series_resistance_and_reservoir_reviewed=True,
    stoichiometry_and_surface_consumption_balance_reviewed=True,
    signed_partial_current_mapping_reviewed=True,
    interval_parameter_temperature_support_reviewed=True,
    computational_use_authorized=True,
    evidence=(Evidence(source_id="synthetic-provider", origin="synthetic",
                       citation="Fabricated API fixture; no physical parameter recommendation.",
                       license_id="synthetic-fixture-MIT", sha256="a" * 64),),
)

if __name__ == "__main__":
    print(request.model_dump_json(indent=2))

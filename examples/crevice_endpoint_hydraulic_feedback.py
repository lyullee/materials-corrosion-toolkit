"""Synthetic wiring example for reviewed within-segment crevice hydraulics.

All values and callbacks below are illustrative. Replace them with source-bound,
reviewed inputs for the material, geometry, fluid, boundary history and wall law.
Running this file performs a model calculation; it is not a validation case.
"""

import numpy as np

from matintegrity.crevice_campaign import (
    CreviceTransportRecessionFeedback,
    solve_crevice_transport_recession_feedback,
)
from matintegrity.crevice_geometry import PlanarSlitGeometry
from matintegrity.restricted_transport import RestrictedTransportRequest


geometry = PlanarSlitGeometry(
    geometry_id="synthetic-two-cell-slit",
    source_sha256="a" * 64,
    cell_widths_m=(0.02, 0.02),
    aperture_m=100e-6,
    transverse_width_m=0.01,
    reactive_broad_face_count=1,
    constant_aperture_cross_section_and_transverse_uniformity_reviewed=True,
)
area = geometry.aperture_m * geometry.transverse_width_m
cell_areas = (area, area)
face_areas = (area, area, area)

transport = RestrictedTransportRequest(
    simulation_id="synthetic-crevice-transport",
    species_ids=("Fe2+",),
    length_m=0.04,
    cell_count=2,
    cell_widths_m=geometry.cell_widths_m,
    cell_cross_section_m2=cell_areas,
    face_cross_section_m2=face_areas,
    reference_cross_section_m2=area,
    variable_area_one_dimensional_reduction_reviewed=True,
    diffusivity_m2_s=(1e-9,),
    initial_concentration_mol_m3=((1.0, 1.0),),
    mouth_concentration_mol_m3=(1.0,),
    output_times_s=(0.0, 10.0),
    reaction_provider_id="synthetic-zero-reaction",
    reaction_configuration_sha256="b" * 64,
    geometry_diffusion_reaction_basis_reviewed=True,
    axial_advection_and_flow_continuity_reviewed=True,
    wall_area_per_volume_m2_m3=(1.0 / geometry.aperture_m,) * 2,
    wall_surface_provider_id="synthetic-constant-fe-dissolution",
    wall_surface_configuration_sha256="c" * 64,
    wall_surface_flux_basis_reviewed=True,
)

feedback = CreviceTransportRecessionFeedback(
    metal_species_id="Fe2+",
    metal_molar_mass_kg_mol=0.055845,
    metal_density_kg_m3=7874.0,
    one_metal_atom_per_species_mole_reviewed=True,
    all_selected_wall_flux_is_metal_dissolution_or_redeposition_reviewed=True,
    supported_minimum_aperture_m=20e-6,
    supported_maximum_aperture_m=200e-6,
    aperture_feedback_mapping_reviewed=True,
    maximum_geometry_update_step_s=5.0,
    geometry_update_step_sampling_reviewed=True,
    maximum_relative_aperture_change_per_segment=0.05,
    adaptive_aperture_update_reviewed=True,
    callback_re_evaluation_deterministic_reviewed=True,
    within_segment_geometry_feedback_enabled=True,
    within_segment_geometry_feedback_reviewed=True,
    within_segment_feedback_convergence_reviewed=True,
    within_segment_hydraulic_feedback_enabled=True,
    within_segment_hydraulic_velocity_path_reviewed=True,
    steady_hydraulic_recalculation_enabled=True,
    pressure_drop_history_Pa=(1000.0, 1200.0),
    pressure_history_interpolation="piecewise_linear",
    pressure_interpolation_reviewed=True,
    pressure_history_source_sha256="d" * 64,
    fluid_property_source_sha256="e" * 64,
    dynamic_viscosity_Pa_s=1e-3,
    density_kg_m3=1000.0,
    steady_hydraulics_and_pressure_alignment_reviewed=True,
    incompressible_newtonian_fluid_properties_reviewed=True,
    laminar_fully_developed_slit_assumption_reviewed=True,
)


def reaction(_time_s: float, concentrations_mol_m3: np.ndarray) -> np.ndarray:
    """Synthetic no-reaction source, shaped as species by cell."""
    return np.zeros_like(concentrations_mol_m3)


def wall_flux(
    _time_s: float,
    concentrations_mol_m3: np.ndarray,
    _potential_V: np.ndarray | None,
) -> np.ndarray:
    """Synthetic inward Fe2+ molar flux per reactive wall area and cell."""
    return np.full_like(concentrations_mol_m3, 1e-8)


if __name__ == "__main__":
    result = solve_crevice_transport_recession_feedback(
        campaign_id="synthetic-crevice-campaign",
        geometry=geometry,
        base_transport_request=transport,
        feedback=feedback,
        output_times_s=transport.output_times_s,
        exact_time_geometry_remap_reviewed=False,
        fixed_geometry_within_interval_reviewed=False,
        cell_inventory_remap_reviewed=False,
        callback_global_time_mapping_reviewed=True,
        reaction=reaction,
        wall_surface_flux=wall_flux,
    )
    print(result)

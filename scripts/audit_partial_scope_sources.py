"""Refresh path-level evidence for the bounded 101-item implementation audit.

This records source presence and hashes only. It does not establish that a file
implements the full capability, that an algorithm is correct, or that it has
been run or physically qualified.
"""

import ast
import hashlib
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data/catalogs/implementation_scope_audit.json"
CAPABILITIES = ROOT / "src/matintegrity/catalog_data/capabilities.json"
COMPONENT_SOURCE_PATHS = {
    "transport.crevice_variable_area_activity_corrected_reactive_nernst_planck_1d": "src/matintegrity/crevice_variable_area_activity_transport.py",
    "integration.wet_co2_cylindrical_geometry_fixed_point_controller": "src/matintegrity/wet_co2_geometry_fixed_point.py",
    "data.mendeley_mdea_co2_eis_typed_rows": "src/matintegrity/mendeley_mdea_co2_eis_rows.py",
    "electrochemistry.mendeley_mdea_eis_complex_channel_conversion": "src/matintegrity/mendeley_mdea_eis_complex.py",
    "integration.crevice_activity_transport_sequential_aperture_campaign": "src/matintegrity/crevice_activity_transport_sequential_aperture.py",
    "integration.crevice_activity_transport_spatial_phase_aperture_handoff": "src/matintegrity/crevice_activity_transport_phase_aperture.py",
    "integration.wet_co2_cylindrical_bv_wall_recession": "src/matintegrity/wet_co2_cylindrical_bv_wall_recession.py",
    "chemistry.wet_co2_neutral_solid_formula_proposals": "src/matintegrity/wet_co2_neutral_solid_formula_proposals.py",
    "fatigue.multiaxial_deviatoric_stress_path_variation": "src/matintegrity/multiaxial_deviatoric_path_variation.py",
    "integration.wet_co2_scale_corrosion_moving_geometry_history": "src/matintegrity/wet_co2_scale_corrosion_coupled_history.py",
    "fabrication.gasket_contact_distribution_statistics": "src/matintegrity/models/gasket_contact_distribution_statistics.py",
    "fabrication.gasket_contact_subthreshold_exposure": "src/matintegrity/models/gasket_contact_subthreshold_exposure.py",
    "fabrication.gasket_prony_temperature_shift_history": "src/matintegrity/models/gasket_temperature_shifted_prony_history.py",
    "fabrication.gasket_prony_relaxation_spectrum_fit": "src/matintegrity/gasket_prony_relaxation_fit.py",
    "fatigue.crossland_proportional_miner_campaign": "src/matintegrity/crossland_proportional_miner_campaign.py",
    "integration.wet_co2_transient_gas_carbonate_alkalinity_equilibrium": "src/matintegrity/wet_co2_transient_carbonate_gas_equilibrium.py",
    "integration.wet_co2_gas_film_condensation_transfer_history": "src/matintegrity/wet_co2_condensation_transfer_history.py",
    "transport.crevice_electroneutral_multispecies_diffusion_1d": "src/matintegrity/crevice_electroneutral_diffusion.py",
    "integration.crevice_activity_gradient_nernst_planck_flux_1d": "src/matintegrity/crevice_activity_gradient_flux.py",
    "transport.crevice_activity_corrected_nernst_planck_1d": "src/matintegrity/crevice_activity_corrected_transport.py",
    "chemistry.crevice_activity_based_reaction_rates": "src/matintegrity/crevice_activity_reaction_rates.py",
    "transport.crevice_activity_corrected_reactive_nernst_planck_1d": "src/matintegrity/crevice_activity_corrected_transport.py",
    "validation.crevice_repassivation_margin_history": "src/matintegrity/crevice_repassivation_margin.py",
    "integration.wet_co2_cylindrical_steady_hydraulics": "src/matintegrity/wet_co2_cylindrical_steady_hydraulics.py",
    "integration.wet_co2_cylindrical_hydraulics_to_scale_removal": "src/matintegrity/wet_co2_cylindrical_hydraulics_to_scale_removal.py",
    "integration.wet_co2_cylindrical_liquid_transfer_capacity_history": "src/matintegrity/wet_co2_cylindrical_liquid_transfer_capacity.py",
    "integration.wet_co2_cylindrical_finite_liquid_transfer_inventory": "src/matintegrity/wet_co2_cylindrical_finite_liquid_transfer_inventory.py",
    "integration.wet_co2_finite_inventory_saturation_scale_geometry": "src/matintegrity/wet_co2_finite_inventory_saturation_scale_geometry.py",
    "integration.wet_co2_finite_inventory_electrode_mixed_potential": "src/matintegrity/wet_co2_finite_inventory_electrode_mixed_potential.py",
    "integration.wet_co2_cylindrical_shear_limited_scale_removal": "src/matintegrity/wet_co2_cylindrical_shear_limited_scale_removal.py",
    "integration.crevice_neutral_reactive_transport_1d": "src/matintegrity/crevice_reactive_transport_1d.py",
    "fatigue.multiaxial_sines_parameter_life": "src/matintegrity/multiaxial_sines_parameter_life.py",
    "fatigue.multiaxial_sines_life_fit": "src/matintegrity/multiaxial_sines_life_fit.py",
    "fatigue.j2_armstrong_frederick_strain_history": "src/matintegrity/j2_armstrong_frederick_history.py",
    "integration.wet_co2_lumped_wall_thermal_condensation_history": "src/matintegrity/wet_co2_wall_thermal_condensation.py",
    "integration.crevice_spatial_ohmic_mixed_potential": "src/matintegrity/crevice_spatial_ohmic_mixed_potential.py",
    "integration.crevice_current_carrying_np_faradaic": "src/matintegrity/crevice_current_carrying_np_faradaic.py",
    "integration.crevice_current_carrying_aperture_feedback": "src/matintegrity/crevice_current_carrying_aperture_feedback.py",
    "integration.crevice_current_carrying_extent_to_metal_loss": "src/matintegrity/crevice_current_carrying_metal_loss.py",
    "integration.crevice_spatial_ohmic_partial_current_metal_loss": "src/matintegrity/crevice_spatial_metal_loss.py",
    "integration.crevice_transport_to_local_mass_action": "src/matintegrity/crevice_transport_local_mass_action.py",
    "integration.crevice_ionic_reactive_transport_1d": "src/matintegrity/crevice_ionic_reactive_transport.py",
    "fabrication.gasket_bolt_nominal_strength_screen": "src/matintegrity/models/gasket_bolt_strength_margin.py",
    "integration.wet_co2_scale_diffusion_electrode_mixed_potential": "src/matintegrity/wet_co2_scale_diffusion_electrode.py",
    "integration.gasket_leakage_pressure_inventory_decay": "src/matintegrity/models/gasket_pressure_inventory_decay.py",
    "fatigue.multiaxial_mcdiarmid_finite_plane_limit_screen": "src/matintegrity/models/multiaxial_mcdiarmid_limit_screen.py",
    "fatigue.mcdiarmid_calibrated_miner_campaign": "src/matintegrity/models/mcdiarmid_miner_campaign.py",
    "fabrication.gasket_radial_open_path_screen": "src/matintegrity/models/gasket_radial_open_path.py",
    "fabrication.gasket_compression_hysteresis_energy": "src/matintegrity/models/gasket_compression_hysteresis_energy.py",
    "fabrication.gasket_temperature_compression_curve_transfer": "src/matintegrity/models/gasket_temperature_compression_curve.py",
    "integration.gasket_temperature_compression_joint_history": "src/matintegrity/models/gasket_temperature_compression_joint_history.py",
    "integration.gasket_thermoelastic_expansion_joint_history": "src/matintegrity/models/gasket_thermoelastic_expansion_joint_history.py",
    "integration.gasket_joint_equilibrium_local_covariance": "src/matintegrity/models/gasket_joint_equilibrium_covariance.py",
    "fatigue.multiaxial_calibration_transfer_audit": "src/matintegrity/multiaxial_calibration_transfer_audit.py",
    "fabrication.gasket_bolt_preload_sequence_redistribution": "src/matintegrity/models/gasket_bolt_preload_sequence_redistribution.py",
    "degradation.wet_co2_cylindrical_scale_geometry_history": "src/matintegrity/wet_co2_cylindrical_scale_geometry.py",
    "fabrication.gasket_compression_curve_monotone_fit": "src/matintegrity/models/gasket_compression_curve_monotone_fit.py",
    "integration.external_gasket_fe_field_import": "src/matintegrity/models/external_gasket_fe_field_import.py",
    "integration.gasket_fe_von_mises_caller_limit_screen": "src/matintegrity/models/gasket_fe_von_mises_caller_limit_screen.py",
    "integration.wet_co2_cylindrical_transport_mixed_potential": "src/matintegrity/wet_co2_cylindrical_transport_mixed_potential.py",
    "integration.wet_co2_cylindrical_geometry_coupled_history": "src/matintegrity/wet_co2_cylindrical_geometry_coupled_history.py",
    "integration.wet_co2_cylindrical_scale_recession_feedback": "src/matintegrity/wet_co2_cylindrical_scale_recession_feedback.py",
    "integration.wet_co2_cylindrical_stage_speciation_scale_feedback": "src/matintegrity/wet_co2_cylindrical_stage_speciation_scale_feedback.py",
    "integration.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback": "src/matintegrity/wet_co2_cylindrical_finite_gas_stage_speciation_feedback.py",
    "integration.wet_co2_cylindrical_finite_gas_stage_geometry_feedback": "src/matintegrity/wet_co2_cylindrical_finite_gas_stage_geometry_feedback.py",
    "chemistry.crevice_spatial_activity_solid_fixed_point": "src/matintegrity/crevice_spatial_activity_solid_fixed_point.py",
    "chemistry.crevice_component_solid_partition": "src/matintegrity/crevice_component_solid_partition.py",
    "integration.crevice_component_state_segment_handoff": "src/matintegrity/crevice_component_state_segment_handoff.py",
    "integration.crevice_component_state_segment_transition": "src/matintegrity/crevice_component_state_segment_transition.py",
    "chemistry.crevice_nucleation_kinetic_history": "src/matintegrity/crevice_nucleation_kinetic_history.py",
    "calibration.crevice_slit_hydraulic_law_parameters": "src/matintegrity/crevice_hydraulic_parameter_fit.py",
    "corrosion.crevice_hydraulic_stage_rhs": "src/matintegrity/crevice_hydraulic_stage_rhs.py",
    "integration.crevice_double_layer_to_component_bdf_binding": "src/matintegrity/crevice_double_layer_bdf_binding.py",
    "integration.crevice_cellwise_nucleation_kinetic_history": "src/matintegrity/crevice_cellwise_nucleation_kinetic_history.py",
    "integration.crevice_bdf_nucleation_operator_split": "src/matintegrity/crevice_bdf_nucleation_operator_split.py",
    "integration.crevice_dynamic_double_layer_faradaic_history": "src/matintegrity/crevice_dynamic_double_layer_faradaic_history.py",
    "integration.crevice_dynamic_double_layer_to_component_bdf_binding": "src/matintegrity/crevice_dynamic_double_layer_bdf_binding.py",
    "integration.crevice_hydraulic_component_advection": "src/matintegrity/crevice_hydraulic_component_advection.py",
    "integration.crevice_moving_volume_liquid_continuity": "src/matintegrity/crevice_moving_volume_continuity.py",
    "corrosion.crevice_moving_volume_hydraulic_history": "src/matintegrity/crevice_moving_volume_hydraulic_history.py",
    "integration.wet_co2_cylindrical_transient_transport": "src/matintegrity/wet_co2_cylindrical_transient_transport.py",
    "integration.wet_co2_cylindrical_wall_saturation_scale_kinetics": "src/matintegrity/wet_co2_cylindrical_wall_saturation_scale_kinetics.py",
    "integration.wet_co2_cylindrical_scale_kinetics_to_geometry": "src/matintegrity/wet_co2_cylindrical_scale_kinetics_geometry.py",
    "fatigue.multiaxial_power_law_life_transfer": "src/matintegrity/multiaxial_power_law_life_transfer.py",
    "integration.wet_co2_cylindrical_multilayer_transport_resistance": "src/matintegrity/wet_co2_cylindrical_multilayer_transport.py",
    "integration.wet_co2_cylindrical_diffusion_limited_scale_growth": "src/matintegrity/wet_co2_cylindrical_diffusion_limited_scale_growth.py",
    "integration.wet_co2_cylindrical_coupled_scale_geometry_replay": "src/matintegrity/wet_co2_cylindrical_coupled_scale_geometry_replay.py",
    "integration.wet_co2_scale_corrosion_simultaneous_history": "src/matintegrity/wet_co2_scale_corrosion_simultaneous.py",
    "integration.wet_co2_finite_gas_water_condensation_history": "src/matintegrity/wet_co2_finite_gas_water_condensation.py",
    "fatigue.multiaxial_crossland_proportional_limit_screen": "src/matintegrity/multiaxial_crossland_proportional_screen.py",
    "integration.wet_co2_finite_gas_multispecies_wall_flux_history": "src/matintegrity/wet_co2_multispecies_finite_inventory_history.py",
    "fabrication.gasket_circumferential_contact_continuity": "src/matintegrity/models/gasket_circumferential_contact_continuity.py",
    "integration.wet_co2_film_transport_limited_mixed_potential": "src/matintegrity/wet_co2_transport_limited_mixed_potential.py",
    "transport.crevice_component_diffusion_1d": "src/matintegrity/models/crevice_component_diffusion.py",
    "fabrication.gasket_bolt_cyclic_damage": "src/matintegrity/models/gasket_bolt_cyclic_damage.py",
    "fatigue.wang_brown_parameter_life_fit": "src/matintegrity/wang_brown_parameter_life_fit.py",
    "integration.wet_co2_finite_gas_wall_reaction_inventory_history": "src/matintegrity/wet_co2_wall_reaction_coupled_history.py",
    "integration.gasket_joint_spatial_resultant_balance": "src/matintegrity/models/gasket_joint_spatial_resultants.py",
    "integration.wet_co2_carbonate_transport_boundary_history": "src/matintegrity/wet_co2_carbonate_transport_history.py",
    "fatigue.dang_van_finite_parameter_life": "src/matintegrity/dang_van_finite_life_curve.py",
    "integration.multi_bolt_joint_to_flange_contact_request": "src/matintegrity/models/multi_bolt_flange_contact_influence.py",
    "integration.extended_debye_huckel_transport_activity_callback": "src/matintegrity/models/aqueous_extended_debye_huckel_iteration.py",
    "integration.co2_henry_temperature_to_fixed_fugacity_carbonate_history": "src/matintegrity/models/co2_henry_carbonate_history_adapter.py",
    "fatigue.itoh_nonproportional_miner_blocks": "src/matintegrity/itoh_nonproportional_miner_blocks.py",
    "fabrication.gasket_evidence_bound_prony_history": "src/matintegrity/models/gasket_evidence_bound_prony_history.py",
    "integration.co2_henry_temperature_to_fixed_fugacity_carbonate": "src/matintegrity/models/co2_henry_carbonate_adapter.py",
    "chemistry.co2_henry_vant_hoff_temperature_correction": "src/matintegrity/models/co2_henry_vant_hoff.py",
    "fatigue.itoh_nonproportional_strain_parameter": "src/matintegrity/itoh_nonproportional_strain_parameter.py",
    "fatigue.itoh_nonproportional_strain_life": "src/matintegrity/itoh_nonproportional_strain_life.py",
    "fabrication.gasket_multi_bolt_sector_equilibrium": "src/matintegrity/models/gasket_multi_bolt_sector_equilibrium.py",
    "chemistry.aqueous_extended_debye_huckel_self_consistent_speciation": "src/matintegrity/models/aqueous_extended_debye_huckel_iteration.py",
    "data.bam_cmsx6_creep_lis_typed_rows": "src/matintegrity/cmsx6_creep_lis_typed_rows.py",
    "chemistry.aqueous_extended_debye_huckel_activity": "src/matintegrity/models/extended_debye_huckel_activity.py",
    "integration.lh2dt_dynamic_network_node_state_history": "src/matintegrity/lh2dt_adapter.py",
    "fatigue.wang_brown_reviewed_excursion_parameter": "src/matintegrity/wang_brown_excursion_parameter.py",
    "fabrication.chemical_cleaning_bath_component_inventory": "src/matintegrity/models/chemical_cleaning_bath_inventory.py",
    "mechanics.gasket_nominal_contact_pressure": "src/matintegrity/models/gasket_nominal_contact_pressure.py",
    "integration.crevice_geometry_aware_solid_deposition_provider": "src/matintegrity/crevice_geometry_aware_solid_deposition.py",
    "integration.wet_co2_finite_gas_variable_liquid_history": "src/matintegrity/wet_co2_finite_gas_variable_liquid_history.py",
    "thermo.coolprop_pure_water_saturated_vapor_fugacity": "src/matintegrity/wet_co2_coolprop_water.py",
    "integration.wet_co2_condensate_film_history": "src/matintegrity/wet_co2_condensate_film_history.py",
    "integration.wet_co2_variable_condensate_transfer_history": "src/matintegrity/wet_co2_variable_condensate_transfer_history.py",
    "integration.crevice_geometry_aware_aqueous_chemistry_provider": "src/matintegrity/crevice_geometry_aware_chemistry.py",
    "chemistry.crevice_transient_wall_sink": "src/matintegrity/crevice_transient_wall_sink.py",
    "fatigue.sampled_tensor_stress_strain_work_cycle": "src/matintegrity/multiaxial_tensor_work_cycle.py",
    "fabrication.gasket_contact_transition_refinement": "src/matintegrity/models/gasket_contact_transition_refinement.py",
    "chemistry.pitzer_salt_saturation_index": "src/matintegrity/pitzer_salt_saturation_index.py",
    "chemistry.pitzer_salt_finite_scenario_envelope": "src/matintegrity/pitzer_salt_finite_scenario_envelope.py",
    "fabrication.gasket_contact_transition_brackets": "src/matintegrity/models/gasket_contact_transition_brackets.py",
    "fatigue.sampled_stress_invariant_history": "src/matintegrity/multiaxial_stress_invariant_history.py",
    "chemistry.crevice_steady_wall_sink": "src/matintegrity/crevice_steady_wall_sink.py",
    "integration.findley_miner_ordered_block_history": "src/matintegrity/fatigue_miner_block_history.py",
    "fatigue.ince_glinka_gsa_life_from_curve": "src/matintegrity/ince_glinka_gsa_curve_life.py",
    "integration.crevice_transport_volume_weighted_composition": "src/matintegrity/crevice_transport_composition_bridge.py",
    "integration.crevice_calibrated_wall_sink_rate_history": "src/matintegrity/crevice_calibrated_wall_sink_history.py",
    "integration.crevice_calibrated_wall_flux_callback": "src/matintegrity/crevice_calibrated_wall_flux_callback.py",
    "integration.crevice_multispecies_wall_flux_callback": "src/matintegrity/crevice_multispecies_wall_flux_callback.py",
    "validation.crevice_wall_sink_source_group_stability": "src/matintegrity/crevice_wall_sink_group_cv.py",
    "integration.crevice_kinetic_solid_volume_history": "src/matintegrity/crevice_kinetic_solid_volume_history.py",
    "integration.crevice_saturation_interval_average_rates": "src/matintegrity/crevice_saturation_interval_rate.py",
    "integration.crevice_solid_inventory_geometry_boundary_remap": "src/matintegrity/crevice_solid_inventory_geometry_remap.py",
    "integration.crevice_wall_flux_inventory_history": "src/matintegrity/crevice_wall_flux_inventory_history.py",
    "chemistry.crevice_closed_batch_aqueous_equilibrium": "src/matintegrity/crevice_closed_batch_aqueous_equilibrium.py",
    "integration.crevice_component_state_bdf": "src/matintegrity/crevice_component_state_bdf.py",
    "integration.crevice_component_state_faradaic_schedule_binding": "src/matintegrity/crevice_component_state_faradaic_binding.py",
    "integration.crevice_local_speciation_volume_ledger": "src/matintegrity/crevice_local_speciation_ledger.py",
    "integration.crevice_local_mass_action_projection": "src/matintegrity/crevice_local_speciation_ledger.py",
    "integration.crevice_local_external_activity_projection": "src/matintegrity/crevice_local_speciation_ledger.py",
    "integration.crevice_external_activity_local_solid_saturation": "src/matintegrity/crevice_external_activity_solid_saturation.py",
    "integration.wet_co2_simulation_wall_loss_envelope": "src/matintegrity/wet_co2_simulation_wall_loss_envelope.py",
    "chemistry.layered_scale_history_series_transport": "src/matintegrity/scale_layer_stack_series_transport.py",
    "chemistry.scale_precipitation_inventory_budget": "src/matintegrity/scale_precipitation_inventory_budget.py",
    "corrosion.scale_diffusion_metal_loss_bound": "src/matintegrity/scale_diffusion_metal_loss_bound.py",
    "chemistry.aqueous_mass_action_scenario_envelope": "src/matintegrity/aqueous_mass_action_scenario_envelope.py",
    "chemistry.aqueous_mass_action_topology_envelope": "src/matintegrity/aqueous_mass_action_topology_envelope.py",
    "integration.fixed_fugacity_carbonate_to_scale_kinetics": "src/matintegrity/fixed_fugacity_carbonate_scale_kinetics.py",
    "integration.wet_co2_finite_liquid_transfer_history": "src/matintegrity/wet_co2_finite_liquid_transfer_history.py",
    "integration.wet_co2_carbonate_alkalinity_speciation": "src/matintegrity/wet_co2_carbonate_alkalinity_speciation.py",
    "integration.wet_co2_finite_gas_liquid_exchange_history": "src/matintegrity/wet_co2_finite_gas_liquid_exchange_history.py",
    "degradation.wet_co2_gas_side_mass_transfer": "src/matintegrity/wet_co2_gas_side_mass_transfer.py",
    "integration.wet_co2_parallel_zone_transfer": "src/matintegrity/wet_co2_parallel_zone_transfer.py",
    "integration.wet_co2_reactive_film_transfer": "src/matintegrity/wet_co2_reactive_film_transfer.py",
    "integration.wet_co2_condensate_state": "src/matintegrity/wet_co2_condensate_state.py",
    "integration.crevice_spatial_mass_action_workflow": "src/matintegrity/crevice_spatial_mass_action_workflow.py",
    "fatigue.ince_glinka_gsa_miner_campaign": "src/matintegrity/ince_glinka_gsa_miner_campaign.py",
    "fatigue.papadopoulos_p1_finite_integral_screen": "src/matintegrity/papadopoulos_p1_finite_integral_screen.py",
    "fatigue.papadopoulos_p1_calibration": "src/matintegrity/papadopoulos_p1_calibration.py",
    "fatigue.papadopoulos_p1_calibrated_life": "src/matintegrity/papadopoulos_p1_calibrated_life.py",
    "fatigue.papadopoulos_p1_miner_blocks": "src/matintegrity/papadopoulos_p1_miner_blocks.py",
    "fatigue.carpinteri_spagnoli_finite_limit_screen": "src/matintegrity/carpinteri_spagnoli_finite_screen.py",
    "fatigue.carpinteri_spagnoli_life_dependent_curve": "src/matintegrity/carpinteri_spagnoli_life.py",
    "fatigue.periodic_tensor_fourier_reconstruction": "src/matintegrity/multiaxial_periodic_fourier_reconstruction.py",
    "fatigue.periodic_fourier_tensor_work": "src/matintegrity/multiaxial_fourier_tensor_work.py",
    "fatigue.periodic_fourier_tensor_work_life": "src/matintegrity/multiaxial_fourier_work_life.py",
    "fatigue.periodic_tensor_fourier_rates": "src/matintegrity/multiaxial_periodic_fourier_rates.py",
    "integration.elastic_joint_to_flange_contact_history": "src/matintegrity/elastic_joint_to_flange_contact_history.py",
    "integration.elastic_joint_load_ordered_history": "src/matintegrity/gasket_joint_load_history.py",
    "integration.gasket_leakage_rate_threshold_events": "src/matintegrity/models/gasket_leakage_rate_threshold_events.py",
    "corrosion.piecewise_linear_rate_thickness_history": "src/matintegrity/corrosion_rate_history.py",
    "adapter.corrosion_rate_history_to_fault_tree_basic_event": "src/matintegrity/corrosion_fta_binding.py",
    "integration.adaptive_cycle_block_damage": "src/matintegrity/adaptive_cycle_block_damage.py",
    "chemistry.crevice_aqueous_kinetic_network": "src/matintegrity/models/crevice_kinetic_network.py",
    "fatigue.ince_glinka_generalized_strain_amplitude": "src/matintegrity/models/ince_glinka_gsa.py",
    "chemistry.planar_scale_diffusion_reaction_history": "src/matintegrity/models/scale_moving_boundary.py",
    "chemistry.planar_scale_reaction_demand_balance": "src/matintegrity/models/scale_reaction_demand_balance.py",
    "fabrication.gasket_leakage_map_fit": "src/matintegrity/models/gasket_leakage_map_fit.py",
    "fabrication.gasket_finite_scenario_dependence": "src/matintegrity/models/gasket_finite_scenario_dependence.py",
    "fabrication.gasket_calibrated_leakage_history": "src/matintegrity/models/gasket_leakage_calibration.py",
    "integration.gasket_contact_to_leakage": "src/matintegrity/models/gasket_leakage_calibration.py",
    "chemistry.caller_scale_coverage_kinetics": "src/matintegrity/models/scale_coverage_kinetics.py",
    "integration.scale_limited_electrochemical_boundary": "src/matintegrity/scale_limited_electrochemistry.py",
    "integration.caller_multiaxial_path_damage": "src/matintegrity/multiaxial_damage_provider.py",
    "fatigue.caller_stateful_multiaxial_damage": "src/matintegrity/multiaxial_damage_provider.py",
    "chemistry.aqueous_mass_action_speciation": "src/matintegrity/models/aqueous_mass_action.py",
    "chemistry.pitzer_single_salt_activity": "src/matintegrity/models/pitzer_single_salt.py",
    "integration.sit_activity_transport_callback": "src/matintegrity/models/aqueous_activity_iteration.py",
    "integration.aqueous_external_activity_provider": "src/matintegrity/models/aqueous_external_activity.py",
    "integration.aqueous_external_activity_speciation_history": "src/matintegrity/models/aqueous_external_activity_history.py",
    "integration.sit_competing_solid_kinetics": "src/matintegrity/models/aqueous_activity_iteration.py",
    "chemistry.aqueous_reaction_candidate_enumeration": "src/matintegrity/models/aqueous_mass_action.py",
    "integration.aqueous_solid_phase_candidate_enumeration": "src/matintegrity/aqueous_solid_phase_candidates.py",
    "integration.tangent_thermal_expansion": "src/matintegrity/thermal_expansion.py",
    "chemistry.single_solid_precipitation_equilibrium": "src/matintegrity/single_solid_equilibrium.py",
    "chemistry.competitive_solid_equilibrium": "src/matintegrity/competing_solid_equilibrium.py",
    "chemistry.competitive_solid_sit_equilibrium": "src/matintegrity/models/competitive_solid_sit_iteration.py",
    "chemistry.competitive_solid_bdot_equilibrium": "src/matintegrity/models/competitive_solid_bdot_iteration.py",
    "chemistry.competitive_solid_kinetic_ledger": "src/matintegrity/multiphase_kinetic_ledger.py",
    "chemistry.competitive_solid_saturation_kinetics": "src/matintegrity/multiphase_kinetic_ledger.py",
    "integration.competitive_solid_kinetic_transport": "src/matintegrity/multiphase_kinetic_transport.py",
    "integration.competitive_solid_equilibrium_transport": "src/matintegrity/multiphase_equilibrium_transport.py",
    "corrosion.planar_slit_hydraulic_flow": "src/matintegrity/crevice_geometry.py",
    "corrosion.planar_slit_hydraulic_history": "src/matintegrity/crevice_geometry.py",
    "corrosion.planar_slit_transient_hydraulic_history": "src/matintegrity/models/planar_slit_transient_hydraulic.py",
    "corrosion.crevice_wall_shear_exposure": "src/matintegrity/models/crevice_wall_shear_exposure.py",
    "integration.planar_slit_transient_hydraulic_transport_binding": "src/matintegrity/restricted_transport.py",
    "integration.planar_slit_transient_hydraulic_transport_series_binding": "src/matintegrity/restricted_transport.py",
    "chemistry.fixed_fugacity_carbonate_history": "src/matintegrity/models/co2_fixed_fugacity_equilibrium.py",
    "thermo.co2_pure_fugacity_history": "src/matintegrity/models/co2_fugacity.py",
    "fabrication.flange_contact_compliance_reduction": "src/matintegrity/models/flange_compliance_reduction.py",
    "fabrication.flange_contact_compliance_reduction_history": "src/matintegrity/models/flange_compliance_reduction.py",
    "integration.equilibrium_reactive_transport": "src/matintegrity/equilibrium_reactive_transport.py",
    "integration.co2_corrosion_campaign": "src/matintegrity/co2_corrosion_campaign.py",
    "integration.restricted_transport": "src/matintegrity/restricted_transport.py",
    "degradation.calibrated_damage_history": "src/matintegrity/calibrated_damage_history.py",
    "degradation.calibrated_condition_loss_rate": "src/matintegrity/calibrated_condition_loss.py",
    "degradation.calibrated_condition_loss_history": "src/matintegrity/calibrated_condition_loss.py",
    "integration.sequence_crack_growth": "src/matintegrity/sequence_crack_growth.py",
    "integration.insulation_surface": "src/matintegrity/insulation_surface.py",
    "integration.fire_thermal_response": "src/matintegrity/fire_thermal_response.py",
    "integration.subset_replicates": "src/matintegrity/subset_replicates.py",
    "integration.subset_replicate_tasks": "examples/subset_replicate_tasks.py",
    "data.phase_label_map_area_fractions": "src/matintegrity/phase_map_data.py",
    "data.phase_map_topology_summary": "src/matintegrity/phase_map_topology.py",
    "integration.electrochemical_partial_current_metal_loss": "src/matintegrity/models/electrochemical_metal_loss.py",
    "integration.electrochemical_metal_loss_wall_thickness_history": "src/matintegrity/models/electrochemical_wall_thickness.py",
    "integration.electrochemical_wall_thickness_scenario_envelope": "src/matintegrity/models/electrochemical_wall_thickness_scenario_envelope.py",
    "integration.electrochemical_metal_loss_to_crevice_geometry": "src/matintegrity/models/electrochemical_crevice_geometry.py",
    "integration.external_crevice_solver_receipt": "src/matintegrity/models/external_crevice_solver.py",
    "integration.caller_multiaxial_law_applicability_binding": "src/matintegrity/multiaxial_damage_provider.py",
    "integration.electrochemical_chemistry_boundary_audit": "src/matintegrity/models/wco2_chemistry_boundary.py",
    "integration.stateful_multiaxial_cycle_block_binding": "src/matintegrity/multiaxial_cycle_exchange.py",
    "integration.external_flange_compliance_receipt": "src/matintegrity/models/external_flange_compliance.py",
    "integration.crevice_aperture_history_refinement": "src/matintegrity/models/crevice_aperture_refinement.py",
    "integration.wet_co2_elemental_phase_handoff": "src/matintegrity/models/wet_co2_elemental_phase_handoff.py",
    "fatigue.multiaxial_life_scenario_envelope": "src/matintegrity/models/multiaxial_life_scenario_envelope.py",
    "fatigue.multiaxial_weighted_life_scenario_moments": "src/matintegrity/models/multiaxial_weighted_life_scenarios.py",
    "integration.gasket_leakage_scenario_exposure": "src/matintegrity/models/gasket_leakage_scenario_exposure.py",
    "integration.gasket_leakage_scenario_rate_interval": "src/matintegrity/models/gasket_transient_exposure.py",
    "integration.aqueous_candidate_network_workflow": "src/matintegrity/models/aqueous_candidate_network_workflow.py",
    "integration.aqueous_candidate_network_speciation": "src/matintegrity/models/aqueous_candidate_speciation.py",
    "integration.aqueous_vant_hoff_saturation_history": "src/matintegrity/models/aqueous_vant_hoff_saturation.py",
    "fabrication.gasket_correlated_scenario_envelope": "src/matintegrity/gasket_correlated_uncertainty.py",
}
# Cross-cutting adapters are standalone catalog capabilities, so they do not
# appear in the parent capability's ``implemented_components`` field. Keep the
# explicit scope lineage here to make the audit traceable without claiming the
# broader parent model is complete.
SCOPE_EXTENSION_COMPONENTS = {
    "structural.creep_rupture_fit": [
        "data.bam_cmsx6_creep_lis_typed_rows",
    ],
    "degradation.crevice_chemistry": [
        "integration.crevice_external_activity_local_solid_saturation",
        "integration.crevice_local_external_activity_projection",
        "integration.crevice_transport_to_local_mass_action",
        "integration.crevice_spatial_ohmic_partial_current_metal_loss",
        "integration.crevice_spatial_ohmic_mixed_potential",
        "integration.crevice_neutral_reactive_transport_1d",
        "transport.crevice_electroneutral_multispecies_diffusion_1d",
        "transport.crevice_component_diffusion_1d",
        "integration.extended_debye_huckel_transport_activity_callback",
        "chemistry.aqueous_extended_debye_huckel_self_consistent_speciation",
        "chemistry.aqueous_extended_debye_huckel_activity",
        "integration.crevice_geometry_aware_solid_deposition_provider",
        "integration.crevice_geometry_aware_aqueous_chemistry_provider",
        "integration.crevice_transport_volume_weighted_composition",
        "integration.crevice_local_speciation_volume_ledger",
        "integration.crevice_local_mass_action_projection",
        "chemistry.crevice_aqueous_kinetic_network",
        "integration.crevice_spatial_mass_action_workflow",
        "integration.crevice_deposition_aperture_history",
        "integration.crevice_local_solid_saturation",
        "integration.crevice_saturation_exposure_history",
        "integration.crevice_deposition_transport_geometry",
        "degradation.crevice_wall_sink_arrhenius_calibration",
        "integration.crevice_calibrated_wall_sink_rate_history",
        "integration.crevice_calibrated_wall_flux_callback",
        "integration.crevice_multispecies_wall_flux_callback",
        "validation.crevice_wall_sink_source_group_stability",
        "integration.crevice_kinetic_solid_volume_history",
        "integration.crevice_saturation_interval_average_rates",
        "integration.crevice_solid_inventory_geometry_boundary_remap",
        "chemistry.crevice_spatial_activity_solid_fixed_point",
        "integration.crevice_wall_flux_inventory_history",
        "chemistry.crevice_closed_batch_aqueous_equilibrium",
        "integration.crevice_component_state_bdf",
        "integration.crevice_double_layer_to_component_bdf_binding",
        "corrosion.crevice_hydraulic_stage_rhs",
        "integration.crevice_cellwise_nucleation_kinetic_history",
        "integration.crevice_bdf_nucleation_operator_split",
        "integration.crevice_dynamic_double_layer_faradaic_history",
        "integration.crevice_dynamic_double_layer_to_component_bdf_binding",
        "integration.crevice_moving_volume_liquid_continuity",
        "corrosion.crevice_moving_volume_hydraulic_history",
        "chemistry.crevice_component_solid_partition",
        "integration.crevice_component_state_segment_handoff",
        "integration.crevice_component_state_segment_transition",
        "chemistry.crevice_nucleation_kinetic_history",
        "integration.crevice_component_state_faradaic_schedule_binding",
    ],
    "degradation.wet_co2": [
        "integration.wet_co2_cylindrical_scale_recession_feedback",
        "integration.wet_co2_cylindrical_stage_speciation_scale_feedback",
        "integration.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback",
        "integration.wet_co2_cylindrical_finite_gas_stage_geometry_feedback",
        "integration.wet_co2_scale_corrosion_simultaneous_history",
        "integration.wet_co2_lumped_wall_thermal_condensation_history",
        "integration.wet_co2_finite_gas_water_condensation_history",
        "integration.wet_co2_gas_film_condensation_transfer_history",
        "integration.wet_co2_transient_gas_carbonate_alkalinity_equilibrium",
        "integration.wet_co2_scale_corrosion_moving_geometry_history",
        "integration.wet_co2_finite_gas_multispecies_wall_flux_history",
        "integration.wet_co2_film_transport_limited_mixed_potential",
        "integration.wet_co2_finite_gas_wall_reaction_inventory_history",
        "integration.wet_co2_carbonate_transport_boundary_history",
        "integration.extended_debye_huckel_transport_activity_callback",
        "chemistry.co2_henry_vant_hoff_temperature_correction",
        "integration.co2_henry_temperature_to_fixed_fugacity_carbonate",
        "integration.co2_henry_temperature_to_fixed_fugacity_carbonate_history",
        "chemistry.aqueous_extended_debye_huckel_self_consistent_speciation",
        "integration.wet_co2_finite_gas_variable_liquid_history",
        "thermo.coolprop_pure_water_saturated_vapor_fugacity",
        "integration.wet_co2_condensate_film_history",
        "integration.wet_co2_variable_condensate_transfer_history",
        "integration.wet_co2_simulation_wall_loss_envelope",
        "chemistry.layered_scale_history_series_transport",
        "chemistry.planar_scale_diffusion_reaction_history",
        "chemistry.planar_scale_reaction_demand_balance",
        "chemistry.scale_precipitation_inventory_budget",
        "corrosion.scale_diffusion_metal_loss_bound",
        "chemistry.aqueous_mass_action_scenario_envelope",
        "chemistry.aqueous_mass_action_topology_envelope",
        "integration.fixed_fugacity_carbonate_to_scale_kinetics",
        "data.plos_ct110_wet_co2_typed_rows",
        "degradation.wet_co2_liquid_side_mass_transfer",
        "integration.wet_co2_finite_liquid_transfer_history",
        "integration.wet_co2_carbonate_alkalinity_speciation",
        "integration.wet_co2_finite_gas_liquid_exchange_history",
        "integration.wet_co2_reactive_film_transfer",
        "integration.wet_co2_parallel_zone_transfer",
        "degradation.wet_co2_gas_side_mass_transfer",
        "integration.wet_co2_cylindrical_geometry_coupled_history",
    ],
    "structural.multiaxial_fatigue": [
        "fatigue.j2_armstrong_frederick_strain_history",
        "fatigue.multiaxial_sines_life_fit",
        "fatigue.multiaxial_sines_parameter_life",
        "fatigue.crossland_proportional_miner_campaign",
        "fatigue.multiaxial_deviatoric_stress_path_variation",
        "fatigue.multiaxial_crossland_proportional_limit_screen",
        "fatigue.wang_brown_parameter_life_fit",
        "fatigue.dang_van_finite_parameter_life",
        "fatigue.itoh_nonproportional_strain_parameter",
        "fatigue.itoh_nonproportional_strain_life",
        "fatigue.itoh_nonproportional_miner_blocks",
        "fatigue.wang_brown_reviewed_excursion_parameter",
        "integration.findley_miner_ordered_block_history",
        "integration.adaptive_cycle_block_damage",
        "fatigue.ince_glinka_generalized_strain_amplitude",
        "fatigue.ince_glinka_gsa_life_from_curve",
        "fatigue.ince_glinka_gsa_miner_campaign",
        "fatigue.multiaxial_sampled_shear_path_area",
        "fatigue.multiaxial_principal_stress_axis_rotation",
        "fatigue.crossland_proportional_miner_campaign",
        "fatigue.j2_prager_strain_history",
        "fatigue.papadopoulos_p1_finite_integral_screen",
        "fatigue.papadopoulos_p1_calibration",
        "fatigue.papadopoulos_p1_calibrated_life",
        "fatigue.papadopoulos_p1_miner_blocks",
        "fatigue.carpinteri_spagnoli_finite_limit_screen",
        "fatigue.carpinteri_spagnoli_life_dependent_curve",
        "fatigue.periodic_tensor_fourier_reconstruction",
        "fatigue.periodic_fourier_tensor_work",
        "fatigue.periodic_fourier_tensor_work_life",
        "fatigue.periodic_tensor_fourier_rates",
    ],
    "fabrication.gasket_joint": [
        "fabrication.gasket_prony_relaxation_spectrum_fit",
        "fabrication.gasket_prony_temperature_shift_history",
        "fabrication.gasket_contact_subthreshold_exposure",
        "fabrication.gasket_contact_distribution_statistics",
        "fabrication.gasket_circumferential_contact_continuity",
        "fabrication.gasket_bolt_cyclic_damage",
        "integration.gasket_joint_spatial_resultant_balance",
        "integration.multi_bolt_joint_to_flange_contact_request",
        "fabrication.gasket_multi_bolt_sector_equilibrium",
        "fabrication.gasket_evidence_bound_prony_history",
        "integration.elastic_joint_load_ordered_history",
        "integration.gasket_leakage_rate_threshold_events",
        "fabrication.gasket_contact_root_localization",
        "fabrication.gasket_calibrated_leakage_history",
        "integration.gasket_contact_to_leakage",
        "fabrication.gasket_contact_subthreshold_exposure",
        "integration.elastic_joint_to_flange_contact_history",
    ],
    "reliability.risk_inspection": [
        "adapter.corrosion_rate_history_to_fault_tree_basic_event",
    ],
}


def main() -> None:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    catalog_rows = json.loads(CAPABILITIES.read_text(encoding="utf-8"))["capabilities"]
    catalog = {row["id"]: row for row in catalog_rows}
    component_owners: dict[str, list[dict[str, str]]] = defaultdict(list)
    for capability in catalog_rows:
        # A catalog row is itself a concrete implemented component as well as a
        # possible parent of nested components. Keep both ownership forms visible.
        component_owners[capability["id"]].append(
            {"capability_id": capability["id"], "capability_status": capability["status"]}
        )
        for component_id in capability.get("implemented_components", []):
            component_owners[component_id].append(
                {"capability_id": capability["id"], "capability_status": capability["status"]}
            )
    component_drift: list[str] = []
    missing_paths: list[str] = []

    for row in audit["items"]:
        # Repeated audit runs must not duplicate a component that is present
        # both in the generated capability row and this explicit scope map.
        row["implemented_components"] = list(dict.fromkeys(row.get("implemented_components", [])))
        row["source_paths"] = list(dict.fromkeys(row.get("source_paths", [])))
        row["evidence_paths"] = list(dict.fromkeys(row.get("evidence_paths", [])))
        catalog_scope = catalog.get(row["capability_id"], {})
        catalog_components = catalog_scope.get("implemented_components", [])
        known_components = set(row.get("implemented_components", []))
        catalog_components = list(dict.fromkeys([
            *catalog_components,
            *SCOPE_EXTENSION_COMPONENTS.get(row["capability_id"], []),
        ]))
        added_components = [component for component in catalog_components if component not in known_components]
        if added_components:
            row["implemented_components"] = [*row.get("implemented_components", []), *added_components]
            component_drift.extend(f"{row['capability_id']}: {component}" for component in added_components)
        for component in catalog_components:
            source_path = COMPONENT_SOURCE_PATHS.get(component)
            if source_path:
                if source_path not in row.setdefault("source_paths", []):
                    row["source_paths"].append(source_path)
                if source_path not in row.setdefault("evidence_paths", []):
                    row["evidence_paths"].append(source_path)
        for item in row.get("current_code_evidence", []):
            source_path = item.get("path")
            if source_path and source_path not in row.setdefault("source_paths", []):
                row["source_paths"].append(source_path)

        # Give every scoped row a navigable evidence path. If a row already
        # declares implementation source paths but its separate evidence map
        # is empty, reuse those paths and record the basis explicitly.
        if not row.get("evidence_paths") and row.get("source_paths"):
            row["evidence_paths"] = list(row["source_paths"])
            row["evidence_path_basis"] = "declared_source_path_map"

        evidence = []
        symbols_by_path: dict[str, set[str]] = {}
        for relative in row.get("source_paths", []):
            path = ROOT / relative
            if not path.is_file():
                missing_paths.append(f"{row['capability_id']}: {relative}")
                evidence.append({"path": relative, "presence": "missing"})
                symbols_by_path[relative] = set()
                continue
            source = path.read_bytes()
            digest = hashlib.sha256(source).hexdigest()
            symbols = []
            try:
                tree = ast.parse(source.decode("utf-8"), filename=relative)
            except (SyntaxError, UnicodeDecodeError) as exc:
                evidence.append(
                    {
                        "path": relative,
                        "presence": "present",
                        "sha256": digest,
                        "ast_status": "unavailable",
                        "ast_error": type(exc).__name__,
                    }
                )
                symbols_by_path[relative] = set()
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    symbols.append({"name": node.name, "line": node.lineno, "kind": type(node).__name__})
            symbols_by_path[relative] = {item["name"] for item in symbols}
            evidence.append(
                {
                    "path": relative,
                    "presence": "present",
                    "sha256": digest,
                    "ast_status": "parsed",
                    "declared_symbols": sorted(symbols, key=lambda item: (item["line"], item["name"])),
                }
            )
        row["source_path_audit"] = evidence
        audited_by_path = {entry["path"]: entry for entry in evidence}
        for item in row.get("current_code_evidence", []):
            relative = item.get("path")
            if not relative or item.get("symbol") not in symbols_by_path.get(relative, set()):
                continue
            path_evidence = audited_by_path.get(relative, {})
            item["line"] = next(
                symbol["line"]
                for symbol in path_evidence.get("declared_symbols", [])
                if symbol["name"] == item["symbol"]
            )
            if path_evidence.get("sha256"):
                item["source_sha256"] = path_evidence["sha256"]
        row["code_symbol_evidence_audit"] = [
            {
                "path": item["path"],
                "symbol": item["symbol"],
                "status": (
                    "present"
                    if item["symbol"] in symbols_by_path.get(item["path"], set())
                    else "missing_or_unmapped"
                ),
            }
            for item in row.get("current_code_evidence", [])
        ]

        component_statuses = []
        for component_id in row.get("implemented_components", []):
            component = catalog.get(component_id)
            owners = component_owners.get(component_id, [])
            component_statuses.append(
                {
                    "id": component_id,
                    "catalog_status": (
                        component.get("status")
                        if component
                        else "declared_component"
                        if owners
                        else "unmapped"
                    ),
                    "declared_by": owners,
                }
            )
        row["component_catalog_audit"] = component_statuses

    audit["source_audit_as_of"] = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    audit["source_audit_meaning"] = (
        "File existence and SHA-256 only. Presence is not proof of symbol-level behavior, "
        "full-domain implementation, execution, correctness, or qualification."
    )
    audit["ast_audit_meaning"] = (
        "AST parsing and declared class/function names provide navigation evidence only. "
        "They do not link a declared symbol to a capability's full behavior or validate execution."
    )
    classification_keys = ("provider_dependent", "data_validation_pending", "code_incomplete")
    audit["counts"] = {
        key: sum(row.get("classification") == key for row in audit["items"])
        for key in classification_keys
    }
    ast_unavailable = sum(
        entry.get("ast_status") != "parsed"
        for row in audit["items"]
        for entry in row.get("source_path_audit", [])
        if entry.get("presence") == "present"
    )
    stale_symbols = [
        f"{row['capability_id']}: {entry['path']}::{entry['symbol']}"
        for row in audit["items"]
        for entry in row.get("code_symbol_evidence_audit", [])
        if entry["status"] != "present"
    ]
    unmapped_components = [
        f"{row['capability_id']}: {component['id']}"
        for row in audit["items"]
        for component in row.get("component_catalog_audit", [])
        if component["catalog_status"] == "unmapped"
    ]
    total_rows = len(audit["items"])
    rows_with_source_map = sum(bool(row.get("source_paths")) for row in audit["items"])
    rows_with_evidence_map = sum(bool(row.get("evidence_paths")) for row in audit["items"])
    rows_with_complete_path_trace = sum(
        bool(row.get("source_paths"))
        and bool(row.get("evidence_paths"))
        and len(row.get("source_path_audit", [])) == len(row.get("source_paths", []))
        and all(
            entry.get("presence") == "present" and entry.get("ast_status") == "parsed"
            for entry in row.get("source_path_audit", [])
        )
        for row in audit["items"]
    )
    total_component_count = sum(len(row.get("component_catalog_audit", [])) for row in audit["items"])
    audit["trace_coverage"] = {
        "scope_rows": total_rows,
        "rows_with_source_map": rows_with_source_map,
        "rows_with_evidence_map": rows_with_evidence_map,
        "rows_with_complete_path_trace": rows_with_complete_path_trace,
        "complete_path_trace_fraction": (
            rows_with_complete_path_trace / total_rows if total_rows else 1.0
        ),
        "source_paths_declared": sum(len(row.get("source_paths", [])) for row in audit["items"]),
        "source_paths_audited": sum(len(row.get("source_path_audit", [])) for row in audit["items"]),
        "source_paths_missing": len(missing_paths),
        "source_paths_ast_unavailable": ast_unavailable,
        "explicit_code_symbols": sum(
            len(row.get("code_symbol_evidence_audit", [])) for row in audit["items"]
        ),
        "explicit_code_symbols_missing_or_unmapped": len(stale_symbols),
        "components_declared": total_component_count,
        "components_mapped": total_component_count - len(unmapped_components),
        "components_unmapped": len(unmapped_components),
        "meaning": (
            "Traceability measures source/evidence navigation and static presence only; "
            "it does not measure implementation completeness, execution, correctness, or qualification."
        ),
    }
    print(f"rows={total_rows}")
    print(f"source_paths={sum(len(row.get('source_path_audit', [])) for row in audit['items'])}")
    print(f"missing_paths={len(missing_paths)}")
    print(f"components={total_component_count}")
    print(f"ast_unavailable={ast_unavailable}")
    print(f"stale_or_unmapped_code_symbols={len(stale_symbols)}")
    print(f"unmapped_components={len(unmapped_components)}")
    print(f"catalog_component_drift_reconciled={len(component_drift)}")
    print(
        "complete_path_trace="
        f"{rows_with_complete_path_trace}/{total_rows} "
        f"({100.0 * rows_with_complete_path_trace / total_rows if total_rows else 100.0:.1f}%)"
    )
    for value in missing_paths:
        print(f"MISSING {value}")
    for value in component_drift:
        print(f"RECONCILED {value}")
    for value in unmapped_components:
        print(f"UNMAPPED {value}")
    for value in stale_symbols:
        print(f"STALE_SYMBOL {value}")
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

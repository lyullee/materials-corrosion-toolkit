"""Record mathematical bases and public implementation references without reproducing source prose."""

import json
from pathlib import Path

from matintegrity.registry import default_registry
from matintegrity.sensitivity import SENSITIVITY_SOURCE_IDS

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_INTERFACE_SOURCE_IDS = {
    "dryad_formate_packer_corrosion_workbook_rows",
    "declared_crevice_transport_provider",
    "caller_reviewed_carbonate_transport_boundary_history",
    "caller_reviewed_co2star_partition_and_water_concentration",
    "caller_dang_van_finite_parameter_life_curve",
    "caller_multi_bolt_to_spatial_flange_contact_influence",
    "caller_gasket_joint_spatial_resultant_balance",
    "caller_wet_co2_electrochemical_co2star_sink_mapping",
    "caller_wang_brown_parameter_constant_amplitude_life_data",
    "caller_gasket_bolt_sn_calibration",
    "caller_basquin_goodman_miner",
    "caller_gasket_circumferential_contact_threshold",
    "caller_periodic_voronoi_contact_partition",
    "caller_wet_co2_species_film_transport_parameters",
    "caller_calibrated_butler_volmer_reaction_set",
    "caller_wet_co2_electrochemical_species_flux_interval_schedule",
    "caller_finite_gas_two_film_and_variable_liquid_transfer",
    "caller_finite_tensor_stress_path_variation",
    "caller_wet_co2_scale_growth_per_metal_dissolution_mapping",
    "caller_wet_co2_scale_phase_molar_volume_and_external_flux",
    "caller_gasket_contact_distribution_statistics",
    "caller_gasket_contact_subthreshold_exposure_threshold",
    "caller_crossland_parameter_constant_amplitude_life_curve",
    "caller_wet_co2_conditional_carbonate_equilibrium_parameters",
    "caller_wet_co2_wall_carbon_and_alkalinity_flux_schedule",
    "caller_finite_gas_carbonate_transfer_and_variable_liquid",
    "caller_wet_co2_gas_film_water_transfer_parameters",
    "caller_wet_co2_wall_water_saturation_fugacity",
    "scipy_integrate_bdf",
    "caller_crevice_nernst_planck_species_transport",
    "caller_crevice_electroneutral_boundary_history",
    "caller_crevice_activity_gradient_species_face_state",
    "activity_corrected_zero_current_nernst_planck_face_flux",
    "caller_cylindrical_diffusion_limited_scale_growth_ledger",
    "caller_wall_shear_history",
    "caller_calibrated_shear_scale_detachment_law",
    "caller_crevice_activity_corrected_transport_species",
    "caller_crevice_activity_coefficient_cell_time_fields",
    "caller_crevice_activity_corrected_mouth_boundary_history",
    "finite_volume_activity_corrected_zero_current_nernst_planck_transport",
    "caller_wet_co2_cylindrical_geometry_result",
    "caller_cylindrical_geometry_result",
    "caller_single_phase_density_viscosity_roughness_flow_record",
    "darcy_weisbach_laminar_colebrook_pipe_flow",
    "caller_crevice_activity_rate_state_and_gamma",
    "caller_crevice_activity_rate_reaction_records",
    "reversible_mass_action_rates_on_dimensionless_activities",
    "caller_activity_based_crevice_reaction_network",
    "finite_volume_activity_nernst_planck_with_local_mass_action",
    "caller_cylindrical_steady_hydraulics_result",
    "caller_calibrated_cylindrical_scale_shear_removal_request",
    "caller_liquid_species_diffusivity_record",
    "caller_cylindrical_segment_wetted_area_geometry",
    "registered_liquid_side_mass_transfer_correlation",
    "caller_cylindrical_liquid_transfer_capacity_history",
    "caller_cylindrical_geometry_history",
    "caller_cylindrical_hydraulics_history",
    "caller_bulk_wall_liquid_concentration_records",
    "caller_bulk_wall_external_inventory_exchange_records",
    "finite_two_compartment_liquid_transfer_balance",
    "caller_cylindrical_finite_liquid_inventory_results",
    "caller_finite_inventory_wall_activity_and_ksp_records",
    "caller_surface_scale_kinetics_configuration",
    "caller_cylindrical_scale_geometry_seed",
    "finite_liquid_to_solid_reaction_stoichiometric_closure",
    "caller_calibrated_butler_volmer_branch_set",
    "caller_finite_bulk_wall_liquid_inventories",
    "caller_interval_external_liquid_sources_sinks",
    "finite_reservoir_species_limited_mixed_potential_ledger",
    "caller_crevice_repassivation_threshold_history",
    "caller_measured_crevice_operating_potential_history",
    "exact_knot_uncertainty_aware_potential_margin_screen",
    "caller_competing_solid_aqueous_state",
    "caller_competing_solid_equilibrium_constants",
    "caller_sines_parameter_constant_amplitude_life_curve",
    "caller_multiaxial_sines_life_calibration_tests",
    "caller_single_backstress_armstrong_frederick_parameters",
    "caller_finite_gas_water_fugacity_transfer_parameters",
    "caller_wall_water_saturation_fugacity_history",
    "caller_temperature_tabulated_wall_water_saturation_fugacity",
    "caller_lumped_wall_heat_capacity_and_boundary_flux",
    "caller_finite_gas_water_film_transfer_parameters",
    "caller_crevice_spatial_butler_volmer_branch_profiles",
    "caller_crevice_spatial_electrolyte_conductivity",
    "finite_volume_current_carrying_activity_nernst_planck_with_faradaic_wall_balance",
    "mixed_potential_face_current_to_ionic_nernst_planck_flux_closure",
    "caller_wet_co2_simultaneous_scale_molar_volume",
    "caller_gasket_prony_time_temperature_shift_parameters",
    "caller_crevice_spatial_dissolution_branch_mapping",
    "caller_crevice_current_branch_metal_mapping",
    "caller_crevice_current_branch_disposition",
    "caller_gasket_prony_step_strain_relaxation_tests",
    "caller_crevice_transport_to_mass_action_constraint_mapping",
    "caller_crevice_transport_cell_volume_mapping",
    "caller_crevice_ionic_reactive_transport_species",
    "caller_crevice_ionic_reaction_network",
    "caller_crevice_ionic_transport_boundary_history",
    "caller_crevice_axial_velocity_face_history",
    "finite_volume_advection_nernst_planck_and_mass_action",
    "mendeley_316l_metastable_pitting_rows",
    "mendeley_az31b_corrosion_fatigue_lab_rows",
    "mendeley_explosive_weld_multilayer_fatigue_rows",
    "mendeley_aisi1018_aerobic_corrosion_file_inventory",
    "caller_aisi1018_corrosion_file_mapping",
    "zenodo_cocr_wear_corrosion_rows",
    "caller_scale_reaction_diffusion_transport_parameters",
    "caller_scale_anodic_butler_volmer_branches",
    "caller_scale_cathodic_butler_volmer_branches",
    "caller_scale_reactant_and_metal_stoichiometry",
    "finite_volume_scale_first_order_sink_with_butler_volmer_mixed_potential",
    "butler_erdey_gruz_volmer_electrode_kinetics",
    "nist_codata_faraday_constant_2022",
    "caller_gasket_leak_calibration_map",
    "caller_gasket_contact_pressure_history",
    "caller_gasket_gas_inventory_volume_temperature_pressure",
    "ideal_gas_inventory_balance_with_calibrated_leakage",
    "mcdiarmid_shear_stress_critical_plane_1994",
    "caller_multiaxial_stress_tensor_history",
    "caller_mcdiarmid_case_torsion_and_tensile_strengths",
    "finite_sampled_shear_traction_diameter_and_normal_stress_screen",
    "caller_mcdiarmid_index_life_curve",
    "caller_ordered_multiaxial_cycle_block_counts",
    "linear_miner_damage_rule_for_mcdiarmid_campaign",
    "caller_gasket_annular_contact_pressure_map",
    "caller_radial_seal_threshold_and_mesh_connectivity",
    "annular_cell_area_and_four_neighbor_radial_path_graph",
    "gasket_contact_open_path_topology_screen",
    "mendeley_ahss1300_hydrogen_permeation_rows",
    "caller_gasket_compression_force_displacement_loops",
    "caller_gasket_specimen_area_thickness_and_condition",
    "piecewise_linear_force_displacement_loop_work_integral",
    "closed_loop_work_as_measured_hysteresis_energy_summary",
    "caller_gasket_temperature_bracket_loading_curves",
    "caller_gasket_specimen_geometry_and_condition",
    "linear_temperature_interpolation_at_fixed_compression_strain",
    "quasi_static_gasket_force_compression_curve_transfer",
    "caller_bolt_preload_stiffness_and_thermal_free_length",
    "caller_gasket_sector_area_compression_and_thermal_free_thickness",
    "quasi_static_parallel_bolt_gasket_force_equilibrium_with_temperature_curve_transfer",
    "ccps_release_history_schema_bridge",
    "caller_bolt_and_gasket_sector_cte_temperature_tables",
    "caller_component_effective_free_dimensions_and_reference_temperature",
    "piecewise_linear_cte_thermal_strain_integral",
    "temperature_dependent_bolt_gasket_joint_equilibrium",
    "caller_covariance_for_ordered_joint_load_coordinates",
    "central_finite_difference_local_sensitivity_of_quasistatic_gasket_equilibrium",
    "first_order_covariance_pushforward_joint_contact_outputs",
    "caller_paired_reference_target_multiaxial_life_observations",
    "independent_weighted_log_life_ratio_summary",
    "caller_joint_specific_elastic_interaction_matrix",
    "caller_ordered_bolt_tightening_operations_and_preload_increments",
    "sequential_linear_superposition_of_elastic_bolt_load_transfer",
    "caller_wet_co2_initial_cylindrical_pipe_geometry",
    "caller_wet_co2_wall_recession_and_scale_phase_inventory_history",
    "caller_wet_co2_scale_phase_molar_volume",
    "caller_gasket_compression_force_observations_and_uncertainties",
    "weighted_non_decreasing_isotonic_regression_pool_adjacent_violators",
    "caller_material_condition_temperature_rate_and_loading_branch",
    "caller_finite_element_gasket_field_receipt_and_normalized_arrays",
    "caller_mesh_contact_location_area_and_coordinate_mapping",
    "caller_solver_step_time_and_support_boundary_records",
    "imported_gasket_fe_stress_tensor_components_and_frame",
    "three_dimensional_j2_von_mises_equivalent_stress_invariant",
    "caller_material_condition_temperature_and_equivalent_stress_limit",
    "independent_cylindrical_radial_finite_volume_species_balance",
    "caller_signed_cylindrical_wall_reaction_extent_schedule",
    "independent_moving_cylinder_finite_volume_inventory_balance",
    "caller_cylindrical_wall_activity_product_to_scale_kinetics",
    "caller_cylindrical_transient_species_history_for_wall_saturation",
    "caller_surface_scale_kinetics",
    "caller_cylindrical_scale_geometry_record",
    "caller_scale_thickness_kinetics_history",
    "cylindrical_annular_layer_inventory_geometry_handoff",
    "computed_digest_pinned_multiaxial_paired_life_audit",
    "caller_reference_condition_multiaxial_parameter_life_curve",
    "weighted_log_linear_paired_life_transfer",
    "caller_cylindrical_phase_solution_diffusivity_records",
    "cylindrical_multilayer_radial_diffusion_resistance",
    "caller_wet_co2_wall_saturation_scale_kinetics_result",
    "caller_wet_co2_cylindrical_multilayer_transport_result",
    "caller_balanced_solid_precipitation_consumption_stoichiometry",
    "caller_cylindrical_geometry_iteration_seed",
    "bounded_picard_replay_of_caller_transport_saturation_and_scale_growth",
    "caller_bolt_proof_strength_temperature_curve",
    "piecewise_linear_bolt_nominal_strength_margin",
    "zenodo_316l_polarization_typed_rows",
    "caller_crevice_neutral_reaction_diffusion_network",
    "caller_crevice_reactive_transport_mouth_history",
    "caller_finite_area_weighted_empirical_statistics",
    "caller_crevice_geometry_aware_solid_deposition_extent",
    "lyullee_lh2dt_dynamic_network_public_result_contract",
    "caller_extended_debye_huckel_activity_parameters",
    "bam_cmsx6_creep_lis_typed_rows",
    "caller_co2_henry_vant_hoff_thermochemistry",
    "caller_reviewed_co2_henry_carbonate_handoff",
    "caller_ordered_co2_henry_carbonate_history",
    "caller_itoh_nonproportional_hardening_calibration",
    "caller_itoh_nonproportional_strain_life_curve",
    "caller_itoh_nonproportional_miner_block_decomposition",
    "caller_multi_bolt_parallel_sector_joint_equilibrium",
    "caller_evidence_bound_gasket_prony_parameter_lineage",
    "wang_brown_1993_path_independent_multiaxial_strain_parameter",
    "caller_declared_well_mixed_solution_component_inventory_balance",
    "caller_reviewed_gasket_mean_contact_pressure",
    "dryad_downhole_tool_co2_corrosion_dataset_candidate",
    "fault_tree_inspection_risk_campaign_execution",
    "fault_tree_inspection_expected_loss_adapter",
    "fault_tree_action_event_probability_adapter",
    "independent_basic_event_minimal_cut_sets",
    "explicit_co2_corrosion_campaign",
    "ideal_single_solid_split_transport",
    "digest_pinned_activity_single_solid_split_transport",
    "single_solid_stoichiometric_equilibrium",
    "calibrated_condition_loss_response",
    "reversible_gasket_contact_equilibrium",
    "caller_nonlinear_bolt_gasket_equilibrium",
    "multiaxial_cycle_life_composition",
    "caller_multiaxial_path_damage_integration",
    "caller_multiaxial_law_applicability_binding",
    "ordered_multiaxial_cycle_block_state_exchange",
    "external_flange_fe_compliance_receipt",
    "external_flange_fe_compliance_receipt_history",
    "caller_correlated_gasket_leakage_joint_scenario_envelope",
    "caller_joint_gasket_leakage_covariance_delta_method",
    "caller_gasket_leakage_independent_box_envelope",
    "caller_weighted_gasket_leakage_joint_scenario_moments",
    "caller_findley_parameter_life_curve",
    "layered_scale_history_stack_assembly",
    "caller_gasket_contact_pressure_screen_window",
    "caller_lumped_crevice_exchange_first_order_reaction",
    "caller_lumped_slit_inertance_resistance",
    "caller_crevice_laminar_wall_shear_exposure",
    "caller_crevice_deposition_aperture_geometry_mapping",
    "caller_finite_shear_path_polygon_area_nonproportional_loading_descriptor",
    "caller_crevice_cell_local_candidate_saturation_screen",
    "caller_crevice_cell_saturation_exposure_reconstruction",
    "caller_crevice_wall_sink_velocity_arrhenius_calibration",
    "small_strain_j2_associative_return_mapping_with_linear_prager_kinematic_and_isotropic_hardening",
    "caller_deposition_aperture_to_transport_geometry_mapping",
    "caller_gasket_contact_response_root_localization",
    "caller_finite_sample_principal_stress_axis_rotation_descriptor_nonproportional_loading",
    "caller_weighted_finite_multiaxial_life_scenario_moments",
    "caller_correlated_finite_multiaxial_life_scenario_envelope",
    "caller_constant_state_gasket_leakage_scenario_exposure",
    "caller_finite_gasket_joint_scenario_dependence",
    "caller_piecewise_linear_gasket_leakage_scenario_rate_interval",
    "caller_stateful_multiaxial_damage_sequence_integration",
    "caller_adaptive_cycle_block_state_damage_ode",
    "caller_rate_multiphase_transport_operator_split",
    "critical_plane_piecewise_linear_time_extrema",
    "explicit_critical_plane_cycle_pair_damage",
    "caller_declared_weld_dilution_uncertainty",
    "planar_slit_geometry_reduction",
    "planar_slit_aperture_evolution",
    "explicit_electrolyte_species_extension",
    "explicit_carbonate_transport_boundary",
    "explicit_water_carbonate_network",
    "caller_general_aqueous_mass_action_speciation",
    "caller_element_charge_balanced_aqueous_reaction_candidate_enumeration",
    "caller_aqueous_candidate_reaction_binding",
    "caller_aqueous_solid_phase_candidate_enumeration",
    "caller_aqueous_mass_action_system_assembly",
    "caller_external_aqueous_activity_provider",
    "caller_external_aqueous_activity_speciation_history",
    "pytzer_optional_gpl_provider_metadata",
    "aqueous_mass_action_activities_to_crevice_nernst_potential_history",
    "caller_single_salt_pitzer_mean_activity",
    "zenodo_ti6al4v_cathodic_polarization_csv_import",
    "caller_aqueous_candidate_saturation_screen",
    "caller_tabulated_aqueous_activity_coefficients",
    "self_consistent_davies_aqueous_speciation",
    "molality_to_molarity_activity_standard_state_bridge",
    "caller_surface_scale_kinetic_balance",
    "caller_aqueous_saturation_to_surface_scale_kinetics",
    "caller_gasket_leakage_pressure_envelope",
    "caller_competing_solid_saturation_rate_law",
    "caller_layered_scale_diffusion_limit",
    "caller_planar_scale_diffusion_reaction_balance",
    "caller_planar_scale_reaction_demand_balance",
    "caller_gasket_leakage_surface_fit",
    "caller_crevice_aqueous_kinetic_network",
    "ince_glinka_generalized_strain_amplitude",
    "zenodo_mg_deis_archive_structure",
    "zenodo-ti12mo5hf-oxygen-corrosion",
    "zenodo-ti12mo5zr-aqueous-corrosion",
    "caller_zenodo_ti12mo5hf_aesec_row_reader",
    "layered_scale_history_transport_binding",
    "scale_limited_electrochemical_surface_boundary",
    "sequential_crevice_geometry_transport_campaign",
    "sequential_transport_derived_crevice_recession_feedback",
    "caller_coupled_crevice_diffusive_recession_fixed_point",
    "crevice_nernst_activity_potential",
    "nernst_driven_butler_volmer_history",
    "crevice_multireaction_nernst_butler_volmer_balance",
    "crevice_mixed_potential_species_flux_interval_inventory_transfer",
    "electrochemical_partial_current_to_metal_loss",
    "electrochemical_metal_loss_to_wall_thickness_history",
    "electrochemical_metal_loss_wall_thickness_finite_scenario_envelope",
    "electrochemical_metal_loss_to_crevice_geometry",
    "external_crevice_solver_pressure_velocity_receipt",
    "caller_reviewed_crevice_aperture_history_refinement",
    "caller_declared_wet_co2_elemental_phase_history_handoff",
    "paolinelli_nesic_2021_chilton_colburn_liquid_transfer",
    "caller_composed_aqueous_candidate_network_workflow",
    "caller_composed_aqueous_candidate_network_speciation",
    "caller_competitive_solid_equilibrium_transport_split",
    "psa_dyna_public_mean_stream_contract",
    "electrochemical_chemistry_state_boundary_audit",
    "crevice_electrochemical_transfer_to_well_mixed_composition_history",
    "crevice_composition_to_caller_aqueous_mass_action_knot_history",
    "calibrated_fs_factor_life",
    "caller_shear_normal_strain_curve_life",
    "kandil_brown_miller_curve_life",
    "continuous_plane_fs_life_bound_mapping",
    "explicit_coupled_dissolution_selection",
    "explicit_coupled_wall_metal_loss",
    "caller_gasket_prony_constitutive_response",
    "caller_coupled_prony_bolt_gasket_history",
    "caller_nonlinear_gasket_prony_joint_history",
    "caller_unilateral_nonlinear_gasket_prony_joint_history",
    "caller_spatial_flange_contact_compliance",
    "caller_spatial_nonlinear_flange_contact_compliance",
    "caller_spatial_linear_prony_flange_contact_history",
    "caller_nonlinear_maxwell_spatial_gasket_contact",
    "sequence_zone_memory_and_partial_dissolution",
    "electrochemical_transport_composition",
    "explicit_mass_action_transport_source",
    "caller_butler_volmer_stoichiometry",
    "fire_flux_conduction_composition",
    "restricted_fick_reaction_transport",
    "caller_prescribed_moving_geometry_transport",
    "calibrated_damage_and_plane_life_composition",
    "cylindrical_surface_energy_balance",
    "caller_fad_and_assembly_geometry",
    "caller_gasket_relaxation_curve",
    "subset_replicate_dispersion",
    "tangent_thermal_expansion_integration",
    "declared_creep_fatigue_campaign_composition",
    "declared_secondary_creep_history",
    "declared_strain_life_block_accumulation",
    "caller_creep_fatigue_interaction_curve",
    "aa7050_local_pitting_reader",
    "seccm_316l_pitting_reader",
    "ceit_uniform_corrosion_field_reader",
    "ceit_pulse_echo_method",
    "coqtel_dataset_reader",
    "fabest_lcf_v2_reader",
    "sandia_helpr_v2_1_0",
    "hymatbase_4130x_hydrogen_fatigue_reader",
    "wet_co2_egua_publisher_preview",
    "wet_co2_hainan_secondary_evidence",
    "wet_co2_simulation_source_crosswalk",
    "nist_corr_data_archive_structure_audit",
    "mendeley_304l_chloride_scc_archive_audit",
    "wet_co2_literature_crosswalk",
    "ct110_weld_corrosion_supplement",
    "plos_ct110_wet_co2_typed_rows",
    "aquasoldb_gas_solubility_v2_1_audit",
    "phase_label_map_area_counting",
    "oxford_ebsd_defdap_reader",
    "phase_map_topology_summary",
    "reliability_subset_simulation_pcn",
}
REFERENCES = {
    "length_weighted_profile_roughness_integrals": (
        "NIST surface roughness and step-height calibration methods and height-parameter definitions; this implementation uses explicit piecewise-linear numerical interpretation, not a calibration claim.",
        "https://www.nist.gov/publications/nist-surface-roughness-and-step-height-calibrations-measurement-conditions-and-sources",
    ),
    "screw_thread_and_bearing_friction_equilibrium": (
        "NASA RP-1228 Fastener Design Manual, alternative torque formula and friction coefficient definitions; effective bearing diameter is an explicit caller input here.",
        "https://ntrs.nasa.gov/citations/19900009424",
    ),
    "crossland_1956_hydrostatic_pressure_torsional_fatigue_criterion": (
        "Crossland, B. Effect of large hydrostatic pressures on the torsional fatigue strength of an alloy steel (1956); bibliographic citation verified in a peer-reviewed multiaxial fatigue validation article.",
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC7795696/",
    ),
    "itoh_1995_nonproportional_low_cycle_fatigue_criterion": (
        "T. Itoh et al., Nonproportional Low Cycle Fatigue Criterion for Type 304 Stainless Steel (1995)",
        "https://doi.org/10.1115/1.2804541",
    ),
    "usgs_phreeqc_extended_debye_huckel_method": (
        "USGS PHREEQC Version 3 documentation: extended Debye-Hückel activity model",
        "https://water.usgs.gov/water-resources/software/PHREEQC/Phreeqc_3_2013_manual.pdf",
    ),
    "cmsx6-creep": (
        "BAM Reference Data: Creep of Single-Crystal Ni-Based Superalloy CMSX-6 (Zenodo record 14750432)",
        "https://zenodo.org/records/14750432",
    ),
    "scipy_integrate_solve_ivp": (
        "SciPy scipy.integrate.solve_ivp API",
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html",
    ),
    "scipy_integrate_dop853": (
        "SciPy DOP853 solver documentation",
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.DOP853.html",
    ),
    "idaes_van_t_hoff_equilibrium_constant": (
        "IDAES: Equilibrium Constant Forms — van 't Hoff equation",
        "https://idaes-pse.readthedocs.io/en/2.13.0/explanations/components/property_package/general_reactions/equil_constant.html",
    ),
    "nist_molar_gas_constant": (
        "NIST CODATA 2022: molar gas constant",
        "https://physics.nist.gov/cgi-bin/cuu/Value?r%7Csearch_for=R",
    ),
    "iupac_standard_equilibrium_constant": (
        "IUPAC Gold Book: standard equilibrium constant",
        "https://goldbook.iupac.org/terms/view/S05915",
    ),
    "oecd_nea_reaction_heat_capacity_temperature_correction": (
        "OECD NEA Thermochemical Database: temperature corrections to thermodynamic data and enthalpy calculations",
        "https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/tdb4new_2020-09-02_11-54-56_843.pdf",
    ),
    "erosion_corrosion_1996_electrochemical_measurements": (
        "S. Zhou, M. M. Stack and R. C. Newman, Characterization of synergistic effects between erosion and corrosion in an aqueous environment using electrochemical techniques (1996)",
        "https://doi.org/10.5006/1.3292087",
    ),
    "findley_1959_mean_stress_critical_plane": (
        "W. N. Findley, A Theory for the Effect of Mean Stress on Fatigue of Metals Under Combined Torsion and Axial Load or Bending (1959)",
        "https://doi.org/10.1115/1.4008327",
    ),
    "nea_thermochemical_database_sit_method": (
        "OECD Nuclear Energy Agency Thermochemical Database Project: SIT method",
        "https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/tdb2_2020-09-02_11-51-54_735.pdf",
    ),
    "usgs_phreeqc_llnl_bdot_activity": (
        "USGS PHREEQC 3 documentation: LLNL extended Debye-Huckel B-dot activity model",
        "https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-26.htm",
    ),
    "usgs_phreeqc_sit_model_documentation": (
        "USGS PHREEQC 3 documentation: SIT aqueous model data block",
        "https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-46.htm",
    ),
    "pytzer_optional_gpl_provider_metadata": (
        "Pytzer documentation: Pitzer activities, provider libraries and GPLv3 license",
        "https://pytzer.readthedocs.io/en/develop/",
    ),
    "usgs_davies_ionic_strength_approximation": (
        "USGS WSP 2254: Davies approximation for aqueous activity coefficients",
        "https://pubs.usgs.gov/wsp/wsp2254/pdf/wsp2254a.pdf",
    ),
    "usgs_phreeqc_davies_activity_coefficients": (
        "USGS PHREEQC 3 documentation: Davies activity-coefficient model",
        "https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-50.htm",
    ),
    "usgs_advanced_carbonate_speciation": (
        "USGS advanced carbonate and bicarbonate speciation method",
        "https://water.usgs.gov/water-resources/memos/memo.php?id=2098",
    ),
    "usgs_phreeqc_gas_liquid_equilibrium": (
        "USGS PHREEQC 3 documentation: gas-phase Henry solubility and fixed-pressure/fixed-volume boundaries",
        "https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-17.htm",
    ),
    "aquasoldb_gas_solubility_v2_1_audit": (
        "AquaSolDB v2.1: versioned gas solubility measurements in water and brine",
        "https://doi.org/10.5281/zenodo.23470595",
    ),
    "oxford_ebsd_defdap_reader": (
        "DefDAP Python library: Oxford EBSD .cpr/.crc reader API",
        "https://defdap.readthedocs.io/en/latest/_modules/defdap/file_readers.html",
    ),
    "coolprop_high_level": (
        "CoolProp high-level thermodynamic property API",
        "https://coolprop.org/coolprop/HighLevelAPI.html",
    ),
    "coolprop_low_level_fugacity": (
        "CoolProp AbstractState low-level API, mixture mole fractions and component fugacity coefficient",
        "https://coolprop.org/coolprop/LowLevelAPI.html",
    ),
    "coolprop_abstract_state_single_phase_properties": (
        "CoolProp AbstractState thermodynamic state and single-phase transport-property API",
        "https://coolprop.org/coolprop/LowLevelAPI.html",
    ),
    "aa7050_local_pitting_reader": (
        "Raw data for AA7050 Specimen 01 - Relationships between microstructure and micromechanical stresses on local pitting",
        "https://doi.org/10.17632/hhf5sfk5bj.1",
    ),
    "seccm_316l_pitting_reader": (
        "Correlative SECCM–SEM/EBSD dataset for 316L pitting: CA traces, descriptors, and imaging tables",
        "https://doi.org/10.5281/zenodo.18668632",
    ),
    "ceit_uniform_corrosion_field_reader": (
        "CEIT near-shore ultrasound monitoring of one uncoated steel sample",
        "https://doi.org/10.5281/zenodo.13897090",
    ),
    "ceit_pulse_echo_method": (
        "Ultrasound-Based Smart Corrosion Monitoring System for Offshore Wind Turbines",
        "https://doi.org/10.3390/app12020808",
    ),
    "coqtel_dataset_reader": (
        "COQTEL project dataset: Corrosion Quantification Through Extended use of Lamb waves",
        "https://doi.org/10.1016/j.dib.2025.111393",
    ),
    "fabest_lcf_v2_reader": (
        "FABEST LCF Benchmark Dataset v2",
        "https://doi.org/10.5281/zenodo.21420213",
    ),
    "sandia_helpr_v2_1_0": (
        "Sandia Hydrogen Extremely Low Probability of Rupture release v2.1.0",
        "https://github.com/sandialabs/helpr/tree/v2.1.0",
    ),
    "hymatbase_4130x_hydrogen_fatigue_reader": (
        "HyMatBase RECORD-SAND2012-7321 4130X vessel Q&T",
        "https://hymatbase.stfc.ac.uk/records/j1e8n-2bz97",
    ),
    "ct110_weld_corrosion_supplement": (
        "CT110 coiled-tubing weld and base-metal weight-loss corrosion rates, supplementary files S1 and S2",
        "https://doi.org/10.1371/journal.pone.0244237",
    ),
    "plos_ct110_wet_co2_typed_rows": (
        "CT110 coiled-tubing weld and base-metal wet-CO2 corrosion-rate supporting workbook",
        "https://doi.org/10.1371/journal.pone.0244237.s017",
    ),
    "wet_co2_simulation_source_crosswalk": (
        "Simulation data for CO2 corrosion rate of oil pipeline",
        "https://doi.org/10.17632/4nydhxjymw.1",
    ),
    "nist_corr_data_archive_structure_audit": (
        "NIST CORR-DATA corrosion observation archive",
        "https://catalog.data.gov/dataset/corr-data",
    ),
    "mendeley_304l_chloride_scc_archive_audit": (
        "Data for: The effect of salt loading on chloride-induced stress corrosion cracking of 304L austenitic stainless steel under atmospheric conditions",
        "https://doi.org/10.17632/mrwrphjvjr.1",
    ),
    "wet_co2_literature_crosswalk": (
        "Neural network modelling of high pressure CO2 corrosion in pipeline steels",
        "https://doi.org/10.1016/j.psep.2018.07.006",
    ),
    "paolinelli_nesic_2021_chilton_colburn_liquid_transfer": (
        "Paolinelli and Nesic (2021), Calculation of mass transfer coefficients for corrosion prediction in two-phase gas-liquid pipe flow",
        "https://doi.org/10.1016/j.ijheatmasstransfer.2020.120689",
    ),
    "paolinelli_nesic_2021_chilton_colburn_gas_film": (
        "Paolinelli and Nesic (2021), Calculation of mass transfer coefficients for corrosion prediction in two-phase gas-liquid pipe flow",
        "https://doi.org/10.1016/j.ijheatmasstransfer.2020.120689",
    ),
    "papadopoulos_1995_high_cycle_integral_multiaxial_criterion": (
        "Papadopoulos (1995), A high-cycle fatigue criterion applied in biaxial and triaxial out-of-phase stress conditions",
        "https://doi.org/10.1111/j.1460-2695.1995.tb00143.x",
    ),
    "papadopoulos_1995_p1_endurance_limit_parameter_relation": (
        "Papadopoulos (1994), A new criterion of fatigue strength for out-of-phase bending and torsion of hard metals",
        "https://doi.org/10.1016/0142-1123(94)90449-9",
    ),
    "papadopoulos_long_life_multiaxial_2001": (
        "Papadopoulos (2001), Long life fatigue under multiaxial loading",
        "https://doi.org/10.1016/S0142-1123(01)00059-7",
    ),
    "carpinteri_spagnoli_2001_hard_metal_high_cycle_fatigue_criterion": (
        "Carpinteri and Spagnoli (2001), Multiaxial high-cycle fatigue criterion for hard metals",
        "https://doi.org/10.1016/S0142-1123(00)00075-X",
    ),
    "carpinteri_spagnoli_life_dependent_material_parameter_sn_curve_method": (
        "Carpinteri and Spagnoli, life-dependent critical plane parameter based on axial and torsional S-N curves",
        "https://doi.org/10.3390/ma13071587",
    ),
    "trefethen_spectral_methods_fourier_interpolation": (
        "Trefethen, Spectral Methods in MATLAB (Fourier interpolation and trigonometric polynomials)",
        "https://doi.org/10.1137/1.9780898719598",
    ),
    "trefethen_spectral_methods_in_matlab_fourier_differentiation": (
        "Trefethen, Spectral Methods in MATLAB (Fourier differentiation)",
        "https://doi.org/10.1137/1.9780898719598",
    ),
    "rsc_fast_gas_liquid_reaction_kinetics": (
        "Determination of fast gas-liquid reaction kinetics in flow",
        "https://doi.org/10.1039/C9RE00390H",
    ),
    "seiersten_top_of_line_corrosion_condensation": (
        "Seiersten et al., Top of line corrosion in gas-condensate pipelines",
        "https://doi.org/10.1088/1757-899X/1201/1/012082",
    ),
    "small_strain_j2_associative_return_mapping_with_linear_prager_kinematic_and_isotropic_hardening": (
        "Prager (1949) general plasticity framework; Chiumenti et al. (2004) J2-plastic constitutive formulation",
        "https://doi.org/10.1016/j.ijplas.2003.11.009",
    ),
    "wet_co2_hainan_secondary_evidence": (
        "A KPCA-IHPO-KELM model for predicting internal corrosion rates in gas gathering pipelines",
        "https://doi.org/10.6047/j.issn.1000-8241.2025.10.006",
    ),
    "wet_co2_egua_publisher_preview": (
        "Corrosion Rate Prediction in Oil and Gas Pipelines Based on Multiphase Flow Modelling",
        "https://doi.org/10.4028/p-brqaI1",
    ),
    "iupac_faradays_laws_of_electrolysis": (
        "IUPAC Gold Book: Faraday’s laws of electrolysis",
        "https://goldbook.iupac.org/terms/view/09075",
    ),
    "numpy_lstsq": (
        "NumPy least-squares solver documentation",
        "https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html",
    ),
    "si_defining_constants": (
        "BIPM SI defining constants for elementary charge and the Avogadro constant",
        "https://www.bipm.org/en/measurement-units/",
    ),
    "cumulative_loading_segments": (
        "Independent segmented-cycle accounting and endpoint classification contract",
        "project://docs/PRESSURIZED_FATIGUE_KO.md",
    ),
    "fabest_hcf_protocol_v2_1_2": (
        "FABEST HCF Competition participant package version 2.1.2",
        "https://doi.org/10.5281/zenodo.23532147",
    ),
    "fabest_lcf_rules_2026": (
        "FABEST in LCF official rules and task description",
        "https://faber-cost.eu/wp-content/uploads/2026/05/Assignment_FABEST_LCF_FINAL.pdf",
    ),
    "iupac_mixed_potential": (
        "IUPAC mixed-potential definition and signed partial-current balance",
        "https://goldbook.iupac.org/terms/view/M03944",
    ),
    "iupac_fugacity_definition": (
        "IUPAC Gold Book definition of fugacity",
        "https://doi.org/10.1351/goldbook.F02543",
    ),
    "gamry_net_polarization": (
        "Gamry explanation of measured net current, partial reactions and polarization limitations",
        "https://www.gamry.com/application-notes/corrosion-coatings/basics-of-electrochemical-corrosion-measurements/",
    ),
    "scipy_sobol": (
        "SciPy first and total Sobol sensitivity estimators and array conventions",
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.sobol_indices.html",
    ),
    "scipy_qmc_sobol": (
        "SciPy scrambled Sobol sequence and balanced power-of-two sample sizes",
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.Sobol.html",
    ),
    "scipy_rqmc_error": (
        "SciPy randomized quasi-Monte Carlo replication and approximate integration intervals",
        "https://docs.scipy.org/doc/scipy/reference/stats.qmc.html",
    ),
    "sobol_variance_indices": (
        "Sobol, global variance sensitivity indices and their Monte Carlo estimates",
        "https://doi.org/10.1016/S0378-4754(00)00270-6",
    ),
    "diaz_kinetic_transport": (
        "Diaz, Alegre, Cuesta and Martinez-Paneda, coupled hydrogen transport and frequency-based trapping kinetics",
        "https://doi.org/10.1016/j.engfracmech.2025.111007",
    ),
    "eyring_transition_state": (
        "Eyring, The Activated Complex in Chemical Reactions, Journal of Chemical Physics 3 (1935) 107-115",
        "https://doi.org/10.1063/1.1749604",
    ),
    "scipy_banded": (
        "SciPy banded linear solver",
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_banded.html",
    ),
    "scipy_sparse": (
        "SciPy sparse direct linear solver",
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.spsolve.html",
    ),
    "oriani_equilibrium": (
        "Oriani, local equilibrium diffusion and trapping of hydrogen",
        "https://doi.org/10.1016/0001-6160(70)90078-7",
    ),
    "nist_lognormal": (
        "NIST lognormal lifetime distribution",
        "https://www.itl.nist.gov/div898/handbook/apr/section1/apr164.htm",
    ),
    "nist_hydrogen_outgassing": (
        "NIST finite-slab diffusion-limited hydrogen outgassing model and characteristic time",
        "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=924339",
    ),
    "nist_accelerated_mle": (
        "NIST accelerated lifetime likelihood estimation",
        "https://www.itl.nist.gov/div898/handbook/apr/section4/apr422.htm",
    ),
    "scipy_minimize": (
        "SciPy constrained minimization API",
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html",
    ),
    "bsee_area_reduction": (
        "Original DNV joint-industry research report hosted by BSEE, area-reduction equation 3.1",
        "https://www.bsee.gov/sites/bsee.gov/files/tap-technical-assessment-program/265ac.pdf",
    ),
    "nist_gumbel": (
        "NIST extreme-value maximum distribution and estimation",
        "https://www.itl.nist.gov/div898/handbook/eda/section3/eda366g.htm",
    ),
    "scipy_genextreme": (
        "SciPy generalized extreme-value distribution, shape convention, CDF and survival-function methods",
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.genextreme.html",
    ),
    "scipy_goodness_of_fit": (
        "SciPy refitted parametric goodness-of-fit inference",
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.goodness_of_fit.html",
    ),
    "scipy_least_squares": (
        "SciPy nonlinear least-squares and robust residual losses",
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html",
    ),
    "evident_pmi_limits": (
        "Instrument manufacturer discussion of elemental and surface PMI limitations",
        "https://ims.evidentscientific.com/en/insights/considerations-using-xrf-pmi",
    ),
    "twi_dilution": (
        "TWI weld-overlay dilution investigation",
        "https://www.twi-global.com/technical-knowledge/published-papers/cra-weld-overlay-influence-of-welding-process-and-parameters-on-dilution-and-corrosion-resistance",
    ),
    "dod_cathodic_current": (
        "DoD electrical technical paper on cathodic current and anodes",
        "https://www.wbdg.org/FFC/DOD/STC/tsewg_tp16.pdf",
    ),
    "nist_instrument_confidence": (
        "NIST instrument performance confidence analysis",
        "https://www.nist.gov/publications/estimating-instrument-performance-confidence-intervals-and-confidence-bounds",
    ),
    "nist_tn1297_uncertainty_propagation": (
        "NIST Technical Note 1297: Law of Propagation of Uncertainty",
        "https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-appendix-law-propagation-uncertainty",
    ),
    "profile_likelihood_inference": (
        "POD method author discussion of likelihood confidence inference",
        "https://statistical-engineering.com/mh1823-workshop/",
    ),
    "osti_polarization": (
        "DOE electrochemical corrosion monitoring report",
        "https://www.osti.gov/servlets/purl/895690",
    ),
    "cambridge_diffusion": (
        "Cambridge materials research diffusion derivation",
        "https://www.phase-trans.msm.cam.ac.uk/2026/boltzmann.html",
    ),
    "inl_cylindrical_heat": (
        "Idaho National Laboratory TMAP8 heat transfer theory",
        "https://tmap8.inl.gov/source/utils/HeatTransferModels.html",
    ),
    "twi_tofd": (
        "TWI discussion of diffraction inspection geometry and limitations",
        "https://www.twi-global.com/technical-knowledge/published-papers/structural-integrity-with-time-of-flight-diffraction-tofd-ultrasonic-inspection-july-2005",
    ),
    "comsol_strain_life": (
        "COMSOL documented strain-life relations",
        "https://doc.comsol.com/6.4/doc/com.comsol.help.fatigue/fatigue_ug_sme.4.21.html",
    ),
    "morrow_mean_stress_strain_life": (
        "Dowling, Mean stress effects in strain-life fatigue",
        "https://doi.org/10.1111/j.1460-2695.2009.01404.x",
    ),
    "fatemi_socie_1988": (
        "Fatemi and Socie, critical-plane fatigue approach including out-of-phase loading",
        "https://doi.org/10.1111/j.1460-2695.1988.tb01169.x",
    ),
    "smith_watson_topper_1970": (
        "Smith, Watson and Topper, stress-strain fatigue function with mean-stress effect",
        "https://www.researchgate.net/publication/309476268_A_stress-strain_function_for_the_fatigue_of_metals_stress-strain_function_for_metal_fatigue_including_mean_stress_effect",
    ),
    "cyclic_ramberg_osgood": (
        "Siemens strain-life and cyclic stress-strain discussion",
        "https://community.sw.siemens.com/articles/en_US/Knowledge/The-Strain-Life-Approach",
    ),
    "cambridge_lame": (
        "Cambridge engineering notes on thick cylinders",
        "https://www-mdp.eng.cam.ac.uk/web/library/enginfo/textbooks_dvd_only/DAN/cylinders/thick/thick.html",
    ),
    "nasa_paris": (
        "NASA preferred reliability practice on fracture control",
        "https://extapps.ksc.nasa.gov/Reliability/Documents/Preferred_Practices/2304.pdf",
    ),
    "nasa_fracture_control": (
        "NASA fracture control implementation handbook",
        "https://standards.nasa.gov/sites/default/files/standards/NASA/Baseline/0/NASA-HDBK-5026-Final-8-12-2024.pdf",
    ),
    "astm_e647_scope": (
        "ASTM E647-24 fatigue crack growth rate test-method scope",
        "https://store.astm.org/standards/e647",
    ),
    "scipy_theilslopes": (
        "SciPy Theil-Sen API",
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html",
    ),
    "twi_arc_measurement": (
        "TWI arc measurement guidance",
        "https://www.twi-global.com/technical-knowledge/job-knowledge/measurement-of-arc-welding-parameters-139",
    ),
    "rosenthal_welding_heat_source": (
        "Tsai and Eagar, Changes of Weld Pool Shape by Variations in the Distribution of Heat Source in Arc Welding",
        "https://eagar.mit.edu/publications/Eagar032.pdf",
    ),
    "twi_carbon_equivalent": (
        "TWI carbon-equivalent formulation discussion",
        "https://www.twi-global.com/technical-knowledge/faqs/faq-what-is-the-difference-between-the-various-carbon-equivalent-formulae-used-in-relation-to-hydrogen-cracking",
    ),
    "rainflow_library": ("rainflow upstream Python package", "https://github.com/iamlikeme/rainflow"),
    "ince_glinka_gsa_2017": (
        "Yu et al., Multiaxial Fatigue Damage Parameter and Life Prediction without Any Additional Material Constants",
        "https://doi.org/10.3390/ma10080923",
    ),
    "nde_pod": (
        "FHWA report on inspection probability of detection",
        "https://rosap.ntl.bts.gov/view/dot/53616/dot_53616_DS1.pdf",
    ),
}
DERIVATIONS = {
    "caller_evidenced_crevice_phase_molar_volume_gap_occupancy_map": "Consume a caller-evidenced ordered cell/phase map of solid molar volumes and explicit gap-occupancy flags. This map supplies geometric conversion factors only; phase identity, thermodynamic stability and property qualification remain caller responsibilities.",
    "caller_evidenced_crevice_cell_phase_molar_rate_stage": "Consume signed caller-evidenced solid molar rates at one exact physical-scope clock stage, preserving ordered cell and phase identities. Positive values denote formation and negative values dissolution; the adapter does not calibrate or qualify a kinetic law.",
    "composed_crevice_stage_geometry_and_phase_volume_rate": "Bind a caller-authorized composite license record to the exact digest of a hydraulic stage geometry and phase-derived liquid-volume rates. The record authorizes only the declared composition and makes no claim that source licenses transfer automatically.",
    "hydrostatic_pressure_balance": "Compute hydrostatic head as caller-supplied density times gravitational acceleration times vertical head and combine it with the caller-provided test multiplier and allowable ratio. Preserve the caller's units and reference elevation; this is a parameterized pressure balance, not a code-mandated test pressure or acceptance rule.",
    "caller_declared_pressure_thickness_relation": "Solve and invert the caller-authorized algebraic relation P=k*S*E*t/(L+c*t) under the supplied dimensional conventions, coefficient identities, applicability declaration and positive-denominator/bound checks. The relation is configurable input and is not presented as a code-prescribed vessel formula or acceptance rule.",
    "ordered_layer_deposition_removal_balance": "Authored one-dimensional layer bookkeeping: add explicitly identified deposited layers at the top and remove supplied thickness from the exposed top downward, retaining removed layer identities, input origins and the ordered event digest. Conservation is initial thickness plus deposited thickness minus removed thickness; no metallurgical mixing, substrate erosion, heat response or procedure acceptance is inferred.",
    "length_weighted_profile_roughness_integrals": "Authored exact segment integration of a caller-preprocessed one-dimensional profile after removing its length-weighted mean. Integrate absolute linear height with explicit internal zero crossings and integrate squared linear height analytically. Report full-evaluation extrema separately; do not infer standard-specific filtering, sampling-length averages, Rz or fixed Ra/Rq conversion factors.",
    "coating_damage_patch_area_geometry": "Authored geometric inventory of caller-measured nonoverlapping damage patches within a reviewed inspected extent. Sum patch area, preserve separate area/length extrema identities and distinguish known damage relative to original area from inspected-area fractions. No repair route, galvanizing standard threshold or extrapolation over uninspected area is supplied.",
    "screw_thread_and_bearing_friction_equilibrium": "Authored quasistatic raising-torque calculation with independent caller thread and effective bearing friction terms. Resolve the helix ratio from lead per revolution and pitch diameter, and use the explicit thread profile half-angle. No tabulated torque, geometry proportions or friction coefficients are distributed. The bearing term uses the caller effective mean diameter rather than a nominal-diameter proportional approximation.",
    "caller_lot_inspection_coverage_escalation": "Authored deterministic population accounting with explicit unit membership and caller sample fractions/counts. Round fraction-times-population upward using the float's round-trip decimal value. Retain failures, trigger caller expansion by unique failed units, and distinguish incomplete/inconclusive observations from definitive inspected outcomes. No statistical acceptance plan or proprietary sampling constants are supplied.",
    "equipment_mass_weighted_centroid": "Authored rigid inventory arithmetic: sum declared component masses and compute the mass-fraction-weighted position in one explicitly reviewed frame. Accessory inclusion, component identity and source evidence remain caller supplied.",
    "planar_two_support_static_equilibrium": "Authored planar force and moment balance for two parallel vertical reactions. Rotate relative body-frame lever arms by the caller angle and distribute the caller-factored weight by projected horizontal lever ratios. Reject unsupported singular spans, numeric range and negative-reaction configurations; no lifting standard factors or structural capacity are bundled.",
    "caller_forming_process_sequence_and_waiver_conditions": "Authored declarative process accounting: ordered nonoverlapping operation ranges are compared with caller count, duration and temperature bounds; exact-clock observations can witness intermediate cooling; caller alternatives combine final finish-temperature and area-reduction conditions. No code constants or treatment waiver authority are supplied.",
    "signed_surface_normal_projection": "Authored Euclidean geometry: project the measured-minus-reference vector onto an explicit unit normal. Normalize by the caller reference length and compare expanded intervals with caller bounds. No coordinate registration, proprietary tolerances or structural acceptance factors are supplied.",
    "observed_impact_metric_linear_crossings": "Independent adjacent-segment target interpolation for separately declared impact energy, shear fraction or lateral expansion, preserving exact target points, nonmonotonic multiple crossings and plateau intervals without extrapolation. Metric context: NIST impact characterization (https://www.nist.gov/publications/impact-characterization-4340-and-t200-steels-means-standard-sub-size-and-miniaturized). No copied criteria, conversion tables or standard qualification rules.",
    "caller_named_steel_composition_indices": "Independent J product-of-sums and X/RCS/K weighted-sum structure evaluations with caller-declared mass basis, coefficients, divisor and offset. No empirical coefficients or acceptance thresholds bundled. Context: Materials 10 (2017) 671 (https://doi.org/10.3390/ma10060671), and TWI's original technical guidance on reheat cracking (https://www.twi-global.com/technical-knowledge/job-knowledge/defects-imperfections-in-welds-reheat-cracking-048). Descriptor calculation is not physical embrittlement or crack prediction.",
    "caller_composition_index_polynomial": "Independent finite sums of coefficient-weighted products of explicitly assayed mass composition, with declared mass-fraction/percent/ppm conversion. Caller supplies the entire licensed recipe; no J/X/reheat susceptibility coefficients or acceptance tables bundled. Context: Materials 10 (2017) 671, https://doi.org/10.3390/ma10060671. Descriptor arithmetic does not predict embrittlement or cracking.",
    "caller_piping_class_component_envelope_composition": "Compose an existing caller-supported piecewise-linear pressure-temperature envelope with exact service/material/component labels, caller-declared corrosion allowances and attribute comparisons. Require explicit rule authority and complete-input digest; never infer nominal rating pressure, designation equivalence, compatibility, required standard tables or regulatory acceptance.",
    "saturated_bath_boil_off_energy_balance": "Independent saturated-bath mass and latent-heat balance. Falling liquid level in a rigid vessel corrects escaping mass flow by 1/(1-rho_v/rho_l); constant-level saturated makeup uses no accumulation correction. See P. Lebrun, CERN/AT 2007-1, section 2.2 (https://www.cryogenicsociety.org/assets/docs/lebrun_intro_to_cryogenics.pdf). No numerical property or acceptance tables bundled.",
    "declared_reference_normalized_diameter_range": "Independently divide the difference between measured maximum and minimum cross-section diameters by an explicit caller-selected nominal or measured-mean diameter. Preserve the denominator basis and report fraction/percent without bundled forming tolerances, sampling rules or acceptance decisions.",
    "caller_declared_carbon_index_recipe": "Independently evaluate caller-specified weighted elemental assays, element ratios, reciprocal assays and an optional carbon-dependent hyperbolic-tangent response. Require explicit mass-percent composition, every referenced assay, nonzero denominators, supported carbon range and digest-pinned licensed input/coefficient records. No empirical coefficient catalogue, normative chemistry limits, weldability or preheat rule is bundled.",
    "caller_parameterized_engineering_correlation_arithmetic": "Independently evaluate explicit caller-parameterized displacement-stress variants, dimensionally declared 2D/3D cooling correlations, affine moisture/hydrogen estimation and coupling/thread pressure arithmetic. Require full input/coefficient record hashes, licensed Evidence and applicability review. All empirical and standard-dependent coefficients are caller inputs; no proprietary parameter/grade/shape-factor tables, automatic method eligibility, rounding or qualification is bundled. Cooling dimensional structure is cross-checked against Bjork et al. 2023, https://doi.org/10.1007/s40194-023-01483-w; no prose or figures copied.",
    "energy_divided_by_declared_reference_specific_energy": "Independently normalize caller energy in joules by caller reference specific energy in joules per kilogram. Preserve reference identity and energy basis without bundled reference constants, blast efficiency, pressure prediction or exclusion-distance rules.",
    "declared_yield_fraction_pipe_membrane_equilibrium": "Independently evaluate outside-diameter membrane pressure from twice the caller stress fraction times yield strength times wall thickness divided by outside diameter. Require positive bore and caller-reviewed geometry/material/factor applicability. No grade-dependent factors, proprietary standard tables, rounding rules, threaded-connection equations or approval criteria are bundled.",
    "declared_energy_or_power_per_weld_length": "Independently compute source energy divided by deposited length, or constant source power divided by travel speed, in SI units. Apply only caller-supplied efficiency to report absorbed heat per length. No empirical efficiency table, standard acceptance limit, source prose or procedure qualification is bundled.",
    "corrosion.crevice_moving_volume_hydraulic_history": "Integrate the pressure-driven common inlet-flow state for a series of caller-evidenced slit cells while linearly interpolated apertures impose piecewise-constant liquid-volume rates. Use cellwise incompressible continuity to derive face-flow offsets, sum caller-reviewed planar-slit resistance and lumped fluid inertance in the momentum balance, and reconstruct cell pressure drops from the same interval midpoint state. Preserve digest-pinned geometry/pressure records and reject work, aspect-ratio, Reynolds or pressure-closure failures. This is a reduced model, not Navier-Stokes, moving-mesh species transport or qualification.",
    "caller_evidenced_pressure_driven_moving_slit_volume_history": "Use caller-supplied exact-knot cell apertures, ordered dimensions, fluid density/viscosity, signed total pressure-drop intervals and initial inlet flow. Treat aperture as linear and pressure as constant inside each declared interval; apply incompressible continuity to recover cell face-flow differences and independently integrate the resulting reduced series momentum ODE. No pressure, geometry, fluid property, deposit morphology or applicability parameter is inferred.",
    "integration.crevice_moving_volume_liquid_continuity": "For each exact-knot interval, calculate caller-mapped slit-cell liquid-volume change from linearly varying aperture, then reconstruct signed interval-mean face flows recursively from dV/dt = Q_left - Q_right. Require the implied terminal face flow to match the independently supplied right boundary flow within declared closure tolerances; preserve geometry and boundary digests. This kinematic balance does not solve momentum, pressure, reactive transport or deposition.",
    "caller_evidenced_slit_volume_and_boundary_flow_continuity": "Use caller-supplied ordered cell lengths, slit width, aperture history and both signed boundary-flow histories to close interval-mean incompressible liquid continuity on a fixed mesh. Linear aperture interpolation is an explicit interval assumption; the operator does not infer a pressure-flow relation or physical qualification.",
    "integration.crevice_dynamic_double_layer_faradaic_history": "Integrate independent lumped electrode-cell potentials from exact-knot total-current histories, caller-supplied signed polarization tables and differential-capacitance curves using total current equal to Faradaic plus capacitive current. Interpolate only within declared supports, preserve Evidence digests and enforce solver/work bounds. Electrolyte ohmic coupling, ionic transport, active-area evolution and qualification are outside this model.",
    "integration.crevice_dynamic_double_layer_to_component_bdf_binding": "Recompute the digest-pinned lumped potential/Faradaic history, map reviewed branches to aqueous reaction extents by declared electron numbers, convert capacitive current to the aqueous sign convention, and reconstruct exact-knot ionic face currents. Require charge-map and insulated-boundary closure before creating the typed component BDF request. This is a sequential handoff without feedback from the BDF chemistry into potential history.",
    "caller_cellwise_aqueous_and_solid_equilibrium_by_knot": "At each exact transport knot and mapped cell, consume caller-declared aqueous species/reactions/linear inventory constraints, temperature-specific activity inputs, finite solid candidates and equilibrium records. Preserve input/result digests and record the provider's species order, cell identity and geometry knot. No automatic species or phase discovery is performed.",
    "sequential_variable_volume_nernst_planck_and_local_chemistry_operator_split": "For each adjacent exact time-knot pair, run the existing BDF variable-volume finite-volume Nernst-Planck transport with caller face areas, flow, diffusivity, mouth boundary and balanced kinetic reaction rates. Hold each cell activity coefficient at its left-knot equilibrium value within that interval; at the right knot, re-solve caller Davies/mass-action speciation and finite competing-solid equilibrium, then carry aqueous concentrations and phase inventories into the next interval. Check per-interval species inventory, local charge and zero-current residuals, per-knot aqueous-plus-solid elemental inventory against integrated mouth/reaction sources, bounded solver evaluations, and full interval/knot digests. This is sequential operator splitting, not a monolithic within-step chemistry/transport solve; no kinetic precipitation, electrochemical source, aperture feedback or integrity qualification is inferred.",
    "caller_activity_driven_stage_scale_kinetics": "BDF-stage evaluation of caller activity/log-solubility-product scale kinetics from current wall-cell concentrations, with finite caller precipitation/dissolution power-law caps.",
    "multireactant_cylindrical_supply_and_inventory_limiter_at_bdf_stages": "Shared cylindrical reactant-supply and live-solid-inventory limiter reevaluated at each BDF stage.",
    "caller_faradaic_branch_species_and_reservoir_stoichiometry": "Caller branch mapping for local species/current stoichiometry and external elemental reservoirs, tied to electron count and face area for extent conversion.",
    "caller_spatial_nernst_standard_potential_and_activity_quotient": "Caller-pinned spatial standard potential and dimensionless activity quotient coefficients for each Faradaic branch.",
    "caller_species_molar_conductivity_mapping": "Caller-pinned ionic molar-conductivity mapping evaluated from the local species state.",
    "knotwise_spatial_mixed_potential_faradaic_inventory_split": "Endpoint split combining variable-area transport, exact-knot Faradaic extents, chemistry re-solve and local mixed-potential iteration; nonzero face current is rejected by the reused kernel contract.",
    "finite_volume_current_carrying_activity_nernst_planck_with_faradaic_wall_balance": "Integrate variable-volume species inventories with activity-gradient, advection, diffusion and migration fluxes. Interior migration uses the caller mixed-potential voltage gradient; boundary electrical currents are insulated. Faradaic wall reaction is a distinct endpoint-trapezoid species source. Iteration commits only when face-current, potential, branch-current, chemistry, charge and element ledgers close within declared tolerances; this does not include double-layer storage or within-step equilibrium.",
    "mixed_potential_face_current_to_ionic_nernst_planck_flux_closure": "Compare the ionic current reconstructed from signed species face fluxes and caller face areas against the spatial mixed-potential current at each internal face. Reject constitutively incompatible conductivity and mobility mappings instead of adjusting transport fluxes to force agreement.",
    "caller_solid_volume_to_aperture_response": "Caller-evidenced mapping from finite solid inventory to a spatial aperture change; this parameterized mapping does not infer deposits, porosity or roughness.",
    "caller_aperture_to_hydraulic_velocity_response": "Caller-provided aperture-to-face-velocity sensitivity with pinned units, geometry, evidence and record digest; not a hydraulic constitutive law.",
    "bounded_geometry_hydraulic_chemistry_picard_iteration": "Bounded outer iteration over registered spatial crevice chemistry-transport, caller solid-volume/aperture mapping and caller aperture/velocity sensitivity, requiring both residual classes and inherited mass-balance gates before commit.",
    "bounded_picard_feedback_of_current_carrying_crevice_transport_geometry": "Repeat the complete current-carrying Nernst–Planck/Faradaic and exact-knot chemistry trajectory using caller-provided solid-volume/aperture and aperture/face-velocity sensitivity mappings. Rebuild digest-pinned area histories on every trial and commit only after both geometry and hydraulic residuals satisfy caller tolerances. This knotwise outer iteration is not a continuous within-step geometry integration and has no general uniqueness or physical-qualification guarantee.",
    "mendeley_mg_fsp_scc_lab_rows": "Version-1 Mendeley ZE41/AZ91D base and friction-stir-processed SCC workbook row reader. Raw assets remain local-only under the provider CC BY 4.0 declaration, with third-party permission risk retained; row interpretation and qualification are not inferred.",
    "mendeley_explosive_weld_multilayer_fatigue_rows": "Mendeley Data v1 workbook reader for fatigue experiments on corrosion-resistant explosively welded multilayer plates. The workbook is checksum-pinned and local-only; the provider declares CC BY 4.0 but embedded third-party content may need separate permission. The reader preserves cell structure and makes no fatigue or service qualification.",
    "mendeley_aisi1018_aerobic_corrosion_file_inventory": "Mendeley Data v1 local-only inventory for 22 AISI 1018 aerobic-consortium corrosion files; verifies provider IDs, sizes and SHA-256 values without parsing any text or OPJ content. Provider-declared CC BY 4.0 is subject to a third-party-content permission caveat; data values are not redistributed or interpreted.",
    "caller_aisi1018_corrosion_file_mapping": "Caller-provided file labels retained with explicit user-declared Evidence; does not establish treatment, replicate, specimen or test semantics.",
    "bounded_picard_replay_of_spatial_bv_transport_and_cylindrical_recession": "Iterate an independently implemented, exact-knot radial finite-volume aqueous transport and caller-calibrated Butler-Volmer response against cylindrical steel-surface recession. Reconstruct the bore from the caller-fixed scale inventory, require per-element wall inventory and radius residual closure, then rerun the ordinary strict geometry balance. The bounded Picard method does not update scale chemistry or kinetics and has no independent physical qualification.",
    "bounded_bv_transport_with_caller_scale_reaction_interval_sources": "Independent same-RHS assembly of caller precipitation/dissolution source/sink terms and spatial Butler-Volmer transport, with exact-knot finite phase inventory and cylindrical geometry iterations.",
    "cylindrical_radial_supply_cap_for_scale_reactants": "Cylindrical radial diffusion supply bound for aggregate simultaneous caller scale-phase consumption of shared aqueous reactants.",
    "caller_cell_aqueous_mass_action_and_solids": "Use the caller's per-cell Davies activity/speciation system, aqueous elemental formulae, charge states, linear conservation targets and finite candidate solid records as explicit nested inputs. No solution chemistry, reaction network, phase list or equilibrium parameter is discovered from process conditions.",
    "aqueous_solid_inventory_feedback_fixed_point": "Alternate a computed aqueous activity/speciation state with the finite competing-solid inventory transfer, update the declared linear aqueous conservation targets by the stoichiometric concentration change, and damp/re-solve until aqueous, solid-inventory and constraint residuals meet caller tolerances. Cell calculations are independent at one fixed geometry knot; convergence is numerical and does not establish global thermodynamic stability or physical qualification.",
    "caller_ion_pair_charge_balanced_solid_formula_proposals": "Enumerate reduced integer charge-neutral stoichiometry for every caller-declared positive-cation/negative-anion pair, merge identical elemental formulae, and retain all generating pairs. This is finite proposal enumeration, not phase identity, stability, chemistry or precipitation evidence.",
    "caller_declared_aqueous_ion_formula_and_charge": "Caller supplies source-record and Evidence-digest-pinned elemental formula and signed integer charge for each aqueous ion; the proposal API performs no speciation, oxidation-state selection or formula inference.",
    "independent_transient_cylindrical_finite_volume_electrochemical_inventory": "Independently assemble a radial finite-volume transient species inventory over exact caller geometry knots, couple reviewed caller Butler–Volmer branches through a shared zero-current potential, and remap inventories across moving cylindrical geometry with explicit species, aqueous element/charge, wall-element and circuit closure ledgers. No reaction kinetics, thermodynamic property table, calibration or corrosion qualification is bundled.",
    "caller_finite_tensor_stress_path_variation": "Sum Euclidean increments in deviatoric five-dimensional stress space using sqrt(J2) distance, and separately sum absolute hydrostatic-stress increments over an ordered closed finite tensor record. Preserve each segment descriptor; do not infer interpolated extrema, cycles, damage or life.",
    "caller_wet_co2_scale_growth_per_metal_dissolution_mapping": "Map digest-pinned anodic metal loss to product-scale generation using caller metal stoichiometry, molar masses, density and product yield; all physical conversion inputs and reviews remain caller supplied.",
    "caller_wet_co2_scale_phase_molar_volume_and_external_flux": "Update areal scale inventory from caller-evidenced molar volume and externally declared interval phase fluxes, retaining signs and source lineage. No phase equilibrium, adhesion, morphology or protective effectiveness is inferred.",
    "caller_gasket_contact_distribution_statistics": "Summarize caller-area-weighted finite gasket contact nodes after verifying each nodal pressure-area force agrees with the upstream contact-force result. Report moments, quantiles and optional threshold area fraction only.",
    "caller_finite_area_weighted_empirical_statistics": "Calculate finite-sample left-continuous area-weighted empirical quantiles and area fractions over ordered caller nodal partitions without interpolation between nodes or a continuous probability model.",
    "caller_gasket_contact_subthreshold_exposure_threshold": "Compare a digest-pinned computed gasket contact history against a caller-owned, evidence- and license-linked pressure threshold; integrate finite-node area-time below that level and positive pressure-deficit dose under explicit piecewise-linear interpolation between exact solver knots. This does not model leakage or establish sealing acceptance.",
    "piecewise_linear_threshold_area_time_integral": "For each finite contact node, integrate the area-time portion below a fixed threshold over a segment whose endpoint pressures are linearly interpolated, resolving a single crossing exactly. Integrate the positive threshold deficit over the same segment without inferring between-knot solver events or leakage.",
    "caller_crossland_parameter_constant_amplitude_life_curve": "Map finite proportional Crossland parameters to caller-supplied same-condition cycle-life data using bounded log-log interpolation, then sum explicitly caller-counted blocks with the linear Miner rule. Do not count cycles, extrapolate, infer sequence effects, probability, or qualified service life.",
    "caller_wet_co2_conditional_carbonate_equilibrium_parameters": "Resolve ideal carbonate-only species fractions at each transient integration evaluation from caller-provided, temperature-matched conditional equilibrium constants and current DIC and alkalinity. Preserve reviewed source and solvent lineage; do not imply nonideal activity or complete electrolyte speciation.",
    "caller_wet_co2_gas_film_water_transfer_parameters": "Use a caller-declared gas-film coefficient with exact interval gas and wall water fugacities to calculate signed condensation or evaporation flux for a fixed wall patch. No hydrodynamic coefficient model is embedded.",
    "caller_wet_co2_wall_water_saturation_fugacity": "Accept caller-evidenced wall saturation fugacity as an input to a gas-film mass-transfer balance; no brine or MEG activity is inferred.",
    "finite_gas_film_fugacity_driven_condensation_inventory": "Integrate gas-film-driven signed water transfer into a finite areal wall inventory, limiting evaporation by available inventory and reporting unmet dryout request and equivalent uniform film thickness. Gas depletion, heat transfer, drainage and corrosion are outside the balance.",
    "caller_crevice_nernst_planck_species_transport": "Require caller-defined ion charges, diffusivities, initial profiles, fixed geometry and reviewed transport scope for a dilute one-dimensional Nernst-Planck component model. No reaction, activity correction, flow or phase law is inferred.",
    "caller_crevice_electroneutral_boundary_history": "Bind caller-provided ordered species concentration boundary conditions to fixed-geometry crevice transport with explicit electroneutrality and zero-current closure assumptions.",
    "caller_crevice_activity_gradient_species_face_state": "Caller supplies species charge, diffusivity, left/right concentration and single-ion activity-coefficient values at one face, with provider and rights evidence; no chemical property data are bundled.",
    "activity_corrected_zero_current_nernst_planck_face_flux": "Evaluate one face's Nernst–Planck flux using caller concentration and log-activity-coefficient gradients, arithmetic face concentration and upwind advection; solve the local dimensionless potential gradient algebraically so total ionic current is zero. This software relation is not a qualified electrolyte model or a source of activity coefficients.",
    "caller_cylindrical_diffusion_limited_scale_growth_ledger": "Require the exact caller-generated cylindrical geometry and diffusion-limited scale-growth results as inputs; this interface derives neither transport nor precipitation data.",
    "caller_wall_shear_history": "Caller supplies licensed, digest-pinned wall-shear stress values at exact cylindrical geometry time knots.",
    "caller_calibrated_shear_scale_detachment_law": "Caller supplies a digest-pinned threshold power law for scale detachment velocity; the implementation does not infer adhesion or detachment parameters.",
    "caller_crevice_activity_corrected_transport_species": "Caller declares ionic species charge, constant diffusivity and initial cell concentration for a reaction-free transport interval; no property table is bundled.",
    "caller_crevice_activity_coefficient_cell_time_fields": "Caller provides species-specific positive activity coefficients at every declared cell and time knot, plus a mouth coefficient history. Provider, standard state, single-ion convention and applicability are caller reviewed; no activity law or coefficient data are included.",
    "caller_crevice_activity_corrected_mouth_boundary_history": "Caller supplies an electroneutral mouth concentration history and signed axial face-velocity schedule aligned to exact output time knots, with a no-flow blind tip.",
    "finite_volume_activity_corrected_zero_current_nernst_planck_transport": "Independently discretize caller activity-corrected Nernst–Planck species fluxes over fixed finite volumes; linearly interpolate concentrations and log activity coefficients in time, use upwind advection, solve each face potential gradient for local zero current and integrate cell inventories with a stiff BDF solver. The implementation does not solve speciation, phases, reaction kinetics or corrosion.",
    "caller_single_phase_density_viscosity_roughness_flow_record": "Caller supplies digest-pinned single-phase flow rate, density, viscosity and absolute roughness at exact geometry knots; no fluid property table is bundled.",
    "darcy_weisbach_laminar_colebrook_pipe_flow": "Use the Darcy–Weisbach pressure-loss relation with laminar friction and an iterated Colebrook turbulent friction factor; fail closed in the transitional Reynolds interval and outside declared roughness support. This calculation is a straight-pipe single-phase screen, not a wet-gas corrosion model.",
    "caller_crevice_activity_rate_state_and_gamma": "Caller supplies a single electroneutral liquid state, concentrations and positive single-ion activity coefficients with a declared concentration standard state; no species/property table is bundled.",
    "caller_crevice_activity_rate_reaction_records": "Caller supplies element/charge-balanced reversible reaction stoichiometry, positive forward/reverse volumetric rate constants, dimensionless equilibrium constants, record IDs/digests and licensed Evidence. The implementation does not fit or temperature-transfer kinetic parameters.",
    "reversible_mass_action_rates_on_dimensionless_activities": "Compute forward and reverse extent rates from caller dimensionless activities and balanced stoichiometry, derive net species source terms and log10(Q/K), and require kf/kr to match caller K within a declared tolerance. This is a single-state activity-based rate snapshot, not speciation, equilibrium, phase selection, or a qualified kinetic law.",
    "caller_activity_based_crevice_reaction_network": "Caller supplies exact-knot forward/reverse rate and dimensionless equilibrium-constant schedules on an activity basis, balanced reaction stoichiometry, per-record digests and a digest-pinned network manifest. No kinetic calibration or chemical mechanism is bundled.",
    "finite_volume_activity_nernst_planck_with_local_mass_action": "Co-integrate activity-corrected Nernst–Planck finite-volume transport with caller reversible mass-action sources in one stiff BDF system. Couple per-cell gamma fields to both the chemical-potential transport gradient and dimensionless reaction activities, retain mouth/no-flux-tip boundaries and track cumulative reaction inventory to close species balances. This is not full speciation, phase equilibrium, wall reaction or a qualified corrosion model.",
    "caller_cylindrical_steady_hydraulics_result": "Consume a caller-evidenced computed cylindrical single-phase hydraulics result with exact geometry, scope and time-knot lineage.",
    "caller_calibrated_cylindrical_scale_shear_removal_request": "Preserve the caller's existing scale-removal threshold, rate coefficient and exponent while mapping hydraulic wall-shear magnitude to exact corresponding geometry knots; no detachment law is calibrated by the adapter.",
    "caller_liquid_species_diffusivity_record": "Caller supplies licensed, digest-pinned species diffusivity at each exact geometry knot; no liquid property table is bundled.",
    "caller_cylindrical_segment_wetted_area_geometry": "Use caller-defined axial segment lengths and exact geometry-derived wetted perimeter to construct the per-segment cylindrical wall area; no area basis is inferred from a corrosion rate.",
    "registered_liquid_side_mass_transfer_correlation": "Call the existing pointwise liquid-side transfer correlation with caller transport properties, local cylindrical hydraulics and selected friction exponent; this adapter does not claim the correlation is qualified outside its stated regime.",
    "caller_cylindrical_liquid_transfer_capacity_history": "Require the exact digest-pinned cylindrical wall-to-bulk transfer-capacity result and preserve its species, interval, geometry and hydraulics lineage.",
    "caller_cylindrical_geometry_history": "Use the exact caller-provided cylindrical geometry knots as the time and wetted-area basis; no corrosion or deposition geometry is inferred.",
    "caller_cylindrical_hydraulics_history": "Require the exact digest-pinned single-phase hydraulic knots used by the upstream transfer-capacity result.",
    "caller_bulk_wall_liquid_concentration_records": "Caller supplies digest-pinned bulk and wall compartment concentrations and finite liquid volumes at every aligned knot, with licensed evidence.",
    "caller_bulk_wall_external_inventory_exchange_records": "Caller supplies signed licensed external species inventory changes per interval for each liquid compartment; no gas/liquid reaction source is inferred.",
    "finite_two_compartment_liquid_transfer_balance": "Convert an upstream per-segment transfer conductance and caller bulk-wall concentration difference into left-held signed molar exchange between finite liquid compartments, add explicit external inventory increments, and fail closed when either compartment inventory becomes negative or the closure residual exceeds tolerance. This is bookkeeping, not a mass-transfer or reaction model.",
    "caller_cylindrical_finite_liquid_inventory_results": "Require exact, computed finite-compartment liquid concentration/inventory histories for the selected transported aqueous species; no liquid states are reconstructed from gas data.",
    "caller_finite_inventory_wall_activity_and_ksp_records": "Caller supplies digest-pinned wall activity coefficients, activity-product species terms and temperature-supported solubility-product records for one explicitly selected solid phase.",
    "caller_surface_scale_kinetics_configuration": "Use the caller's existing surface-scale kinetic parameterization only after exact saturation ratio and wall state mapping; no kinetic coefficient is inferred or fitted.",
    "caller_cylindrical_scale_geometry_seed": "Start from a caller-pinned cylindrical geometry state and preserve layer order, selected phase identity and axial segment basis through the scale update.",
    "finite_liquid_to_solid_reaction_stoichiometric_closure": "Bridge a single selected solid's caller saturation and kinetic increments to finite aqueous wall-species inventory changes using balanced stoichiometry, then update cylindrical layer inventory and geometry; fail closed on concentration/solid balance residuals or depletion. This is a bounded operator-split bridge, not full multiphase equilibrium, nucleation or a qualified corrosion model.",
    "caller_calibrated_butler_volmer_branch_set": "Caller supplies digest-pinned anodic/cathodic Butler–Volmer branches and stoichiometric extents for a bounded electrode calculation; no reaction mechanism or calibration is bundled.",
    "caller_finite_bulk_wall_liquid_inventories": "Caller supplies licensed, digest-pinned finite inventories for selected aqueous species in bulk and wall liquid compartments, plus exact compartment volumes over time.",
    "caller_interval_external_liquid_sources_sinks": "Caller supplies signed bulk/wall aqueous inventory exchange records for each exact interval; no gas absorption or external feed is inferred.",
    "finite_reservoir_species_limited_mixed_potential_ledger": "At each left-held interval, solve a caller branch current balance for mixed potential while limiting electrode extent by available finite wall-side species inventory and closing bulk/wall compartment ledgers with explicit caller external exchanges. This is a lumped two-reservoir model, not a spatial PDE, speciation engine or qualified corrosion prediction.",
    "caller_crevice_repassivation_threshold_history": "Caller supplies licensed, digest-pinned measured repassivation potential records with exact material/environment/temperature/reference metadata and a stated standard uncertainty; the tool does not source or generalize threshold values.",
    "caller_measured_crevice_operating_potential_history": "Caller supplies licensed, digest-pinned operating-potential observations and matched electrolyte/material/reference metadata at exact knots.",
    "exact_knot_uncertainty_aware_potential_margin_screen": "At exact matching knots, compute the signed operating-minus-repassivation potential margin and combine two reported standard uncertainties by root-sum-square; classify only relative position versus a caller-selected uncertainty band. This is a deterministic comparison, not a probability, corrosion prediction or acceptance rule.",
    "exact_knot_sample_supported_threshold_excursion_duration": "Classify duration only over adjacent exact measured potential-margin knots: an interval is definite above threshold only when both endpoint uncertainty bands are above it, possible when either endpoint may be above, and otherwise unresolved. No within-interval crossing time, interpolation, probability or corrosion forecast is inferred.",
    "caller_competing_solid_aqueous_state": "Caller supplies the initial shared aqueous state, explicit charge/element composition, activity reference concentration and fixed activity coefficients, with a digest-bound record for each species; no speciation or electrolyte properties are inferred.",
    "caller_competing_solid_equilibrium_constants": "Caller supplies a finite candidate set of neutral pure solids, balanced aqueous reactant stoichiometries, initial solid inventories and digest-bound dimensionless solubility products at the declared temperature and standard state; no phase is selected or parameterized automatically.",
    "bounded_sequential_active_set_multi_solid_equilibrium": "Apply an ordered bounded scalar equilibrium update over a finite caller phase list, iterate the shared liquid inventory until state convergence, and enforce present/absent saturation complementarity plus charge and extent closure. This software composition is not a global Gibbs-energy minimization or empirical validation.",
    "finite_volume_zero_current_nernst_planck_transport": "Discretize dilute multispecies Nernst-Planck transport by finite volumes and solve local potential gradients from zero-current closure while preserving declared electroneutrality. This is not a concentrated electrolyte law and excludes convection, chemistry, precipitation and corrosion.",
    "caller_crevice_neutral_reaction_diffusion_network": "Require a caller-defined finite neutral-species reaction network with atom-balanced reversible mass-action terms, species diffusivities, fixed geometry and explicit kinetic parameter lineage. No ionic activity, wall reaction, phase equilibrium or corrosion mechanism is implied.",
    "caller_crevice_reactive_transport_mouth_history": "Apply caller-provided ordered mouth concentration and reaction-rate schedules at explicit time knots to a fixed-geometry, blind-tip crevice transport calculation. Input interpolation and boundary meaning remain caller reviewed.",
    "finite_volume_diffusion_with_local_reversible_mass_action": "Co-integrate one-dimensional fixed-geometry Fick diffusion and caller-defined local reversible mass-action kinetics using finite volumes and a stiff initial-value solver. Track boundary transfer, reaction transfer and species inventory residuals; no convection, electromigration, wall kinetics or corrosion is inferred.",
    "caller_sines_parameter_constant_amplitude_life_curve": "Map a caller-calibrated finite Sines-style mean-stress fatigue parameter to same-condition constant-amplitude life data with evidence and digest binding, using log-log interpolation only within observed support. Do not extrapolate or infer cycle counting, damage accumulation or qualification.",
    "scipy_integrate_bdf": "Integrate the declared stiff initial-value transport system with SciPy's variable-order backward differentiation formula implementation using caller-selected tolerances and ordered output times; numerical solver choice does not establish physical validation.",
    "caller_multiaxial_sines_life_calibration_tests": "Use caller-reviewed, uncensored, same-condition specimen-level Sines parameter and cycles-to-failure records with explicit source group, Evidence, rights and independence review. These data do not themselves provide independent validation or runout treatment.",
    "finite_sines_parameter_loglog_ordinary_least_squares": "Fit an ordinary least-squares line to log cycles versus log Sines parameter using a finite caller dataset after validating distinct specimens and common material/calibration conditions. Reject non-decreasing life fits; report fitted-data limitations and do not extrapolate or infer probability.",
    "caller_single_backstress_armstrong_frederick_parameters": "Require caller-provided, evidence- and digest-bound single-backstress Armstrong-Frederick C and gamma parameters for a declared material condition. The parameter record is not a multi-backstress calibration or independent constitutive validation.",
    "backward_euler_j2_armstrong_frederick_radial_return": "Integrate small-strain J2 elastoplastic response with one nonlinear Armstrong-Frederick backstress using backward-Euler radial return and a bracketed scalar consistency solve per supplied strain interval. It is not a general multi-backstress model and does not infer fatigue life or qualify a material.",
    "caller_finite_gas_water_fugacity_transfer_parameters": "Specify a finite, well-mixed water-vapor gas inventory, gas volume, temperature and gas-film coefficient for interval-constant gas-to-wall transfer. No transfer coefficient or state is inferred.",
    "caller_wall_water_saturation_fugacity_history": "Supply evidence-linked exact-interval wall saturation fugacity and reviewed wall state for finite gas water-vapor exchange; does not supply water activity or phase behavior for saline or mixed solvents.",
    "finite_well_mixed_gas_water_wall_film_exchange": "Integrate a finite ideal well-mixed gas water-vapor inventory against a fixed wall saturation fugacity for interval-constant temperature, volume and gas-film transfer coefficient using the exact exponential solution. Couple signed gas transfer to finite liquid-film inventory with dryout limiting and mass-balance reporting; exclude heat balance, brine activity, gas nonideality and corrosion.",
    "caller_temperature_tabulated_wall_water_saturation_fugacity": "Supply an evidence-linked finite wall-temperature/saturation-fugacity table and an explicit interpolation review. Requests outside tabulated support are rejected; no water activity, extrapolation or thermodynamic property is inferred.",
    "caller_lumped_wall_heat_capacity_and_boundary_flux": "Specify caller wall-patch areal heat capacity and interval-constant external heat flux, gas-side heat-transfer coefficient and boundary orientation. These inputs do not constitute a validated conjugate heat-transfer model.",
    "caller_finite_gas_water_film_transfer_parameters": "Specify caller gas-film transfer coefficient, finite-gas state and patch area for a coupled wall-energy and vapor-inventory balance. No hydrodynamic correlation is selected automatically.",
    "lumped_wall_energy_and_finite_gas_water_mass_balance": "Co-integrate wall temperature, finite ideal-gas water inventory, condensate areal inventory and external/sensible/latent energy terms using the caller tabulated saturation fugacity and SciPy DOP853. Stop outside saturation-table support and preserve mass/energy residuals; no saline activity or corrosion law is inferred.",
    "caller_crevice_spatial_butler_volmer_branch_profiles": "Require caller profiles of equilibrium potential, exchange-current density and branch direction for each finite crevice cell and exact output knot; reactions remain externally parameterized and evidence-bound.",
    "caller_crevice_spatial_electrolyte_conductivity": "Supply caller-identified electrolyte conductivity over the finite crevice cells and exact calculation knots. No composition/property law or mass-transport correction is inferred.",
    "finite_volume_electrolyte_resistance_with_local_butler_volmer_balance": "Solve one connected equipotential metal with distributed local Butler-Volmer branches and finite-volume electrolyte ohmic drops under insulated electrolyte end conditions. Report cell potentials, branch and face currents and closure residuals; exclude speciation, concentration polarization, charging and metal resistance.",
    "caller_wet_co2_simultaneous_scale_molar_volume": "Provide an evidence-bound scale molar volume for continuous conversion between dissolved-metal stoichiometric extent and evolving film thickness. No material property is inferred or transferred across conditions.",
    "continuous_within_interval_scale_transport_electrochemical_feedback": "Within each interval's ODE right-hand side, update film thickness from scale inventory, re-evaluate the registered steady film-limited mixed potential, and integrate metal loss, scale inventory and recession with stiff BDF. Caller reaction, transport, yield and external scale-flux mappings remain explicit; this is not a spatial PDE, validated hydrodynamics, or independent corrosion qualification.",
    "caller_gasket_prony_time_temperature_shift_parameters": "Use caller-evidenced Arrhenius or WLF parameters to compute a time-temperature shift factor for an existing generalized-Maxwell Prony response within explicit review and temperature support. No parameters are inferred or transferred between formulations.",
    "arrhenius_reduced_time_prony_shift": "Scale elapsed Prony time by an Arrhenius shift factor from caller activation energy and reference temperature, then pass reduced-time increments to the existing linear viscoelastic generalized-Maxwell solver. This does not shift modulus, solve heat transfer, or imply contact or leakage performance.",
    "wlf_reduced_time_prony_shift": "Scale elapsed Prony time by a caller WLF shift factor using caller constants and reference temperature, then reuse the existing generalized-Maxwell solver. The implementation enforces supplied support and does not establish a universal shift law or material qualification.",
    "nonlinear_weighted_generalized_maxwell_relaxation_fit": "Fit a finite generalized-Maxwell relaxation spectrum to caller-observed step-strain stress records with weighted nonlinear least squares, caller bounds, specimen/source-group identities and explicit data-use lineage. Report optimizer and rank diagnostics; a fitted spectrum is not unique, independently validated, temperature transferable or a sealing qualification.",
    "caller_gasket_prony_step_strain_relaxation_tests": "Use caller-provided finite step-strain relaxation tests with explicit specimen/source-group identity, time and temperature support, data rights, and uncertainty basis to fit a generalized-Maxwell Prony spectrum. The observations remain caller-owned and are not bundled.",
    "caller_crevice_transport_to_mass_action_constraint_mapping": "Declare an explicit one-to-one mapping from caller-named transport species and exact output knots/cells to caller-supplied aqueous mass-action linear constraints. The mapping fixes concentration scaling and preserves input Evidence/digest; it does not infer chemistry.",
    "caller_crevice_transport_cell_volume_mapping": "Supply evidence- and digest-bound finite cell volumes to convert caller-aligned transported concentrations to cell species inventories. No geometry or cell volume is inferred from the transport field.",
    "exact_cell_transport_field_mass_action_constraint_binding": "At each exact cell and time knot, convert mapped transport concentration from mol/m3 to the caller-declared mol/L constraint target, solve the caller's existing aqueous mass-action template independently, and compute cell inventory with explicit volume mapping. Preserve first-failure prefixes; do not infer reaction networks, feedback, phase selection or corrosion.",
    "zenodo_316l_polarization_typed_rows": "Stream and structurally audit the provider's version-pinned CC BY 4.0 raw polarization curve archive under caller attribution and local-use authorization. Preserve exact curve order and measured time/potential/current units; exclude derived descriptors, current density, corrosion metrics and bundled raw archive from the software distribution.",
    "caller_crevice_spatial_dissolution_branch_mapping": "Map explicitly identified anodic spatial mixed-potential branches to dissolved metal using caller electron count, stoichiometry, current efficiency, molar mass, density and reactive cell area with evidence/digest lineage. No cathodic redeposition or localized geometry correction is inferred.",
    "faradaic_extent_to_cellwise_metal_volume_and_recession": "Convert already time-integrated, committed reaction extents into caller-mapped metal moles, mass, volume and uniform per-cell recession. No second current integration or Faraday conversion is applied; net sign reversals inside an interval remain unresolved.",
    "piecewise_linear_positive_spatial_current_faraday_recession": "Integrate only the positive anodic portion of a digest-verified finite spatial branch-current history using piecewise-linear exact-knot segments, then apply Faraday stoichiometry and fixed cell area to obtain gross equivalent uniform recession. It is not a pitting model, full corrosion model or probability/qualification result.",
    "finite_sines_parameter_loglog_life_interpolation": "Apply bounded two-point log-log interpolation on a strictly monotone finite Sines-parameter cycle-life curve; reject requests outside support and preserve the computed parameter and source lineage.",
    "caller_wet_co2_wall_carbon_and_alkalinity_flux_schedule": "Apply signed caller-declared carbon and alkalinity-equivalent flux schedules over exact transient intervals, with explicit physical basis and evidence lineage. Fluxes are exogenous and do not imply corrosion kinetics or electrochemical coupling.",
    "caller_finite_gas_carbonate_transfer_and_variable_liquid": "Integrate finite gas CO2 inventory, dissolved inorganic carbon, total alkalinity, and variable well-mixed liquid volume using caller-supplied transfer, gas-volume, Henry, initial-state and inflow/outflow parameters. Couple to ideal carbonate-only conditional equilibrium; no external chemistry, activity model, or corrosion law is inferred.",
    "integration.wet_co2_film_transport_limited_mixed_potential": "Consume the registered steady planar-film-limited mixed-potential calculation as one sequential interval endpoint. Re-evaluate it with current caller-mapped scale thickness, then update metal recession and scale inventory; do not imply within-interval simultaneous feedback.",
    "caller_crossland_finite_proportional_limit_calibration": "Evaluate the caller-provided Crossland beta and alpha against the maximum sampled hydrostatic stress and proportional deviatoric stress-path amplitude only after a finite tensor path passes the declared proportionality tolerance. Require same-material calibration Evidence and support; do not infer calibration parameters, unsampled extrema, fatigue life or qualification.",
    "caller_wet_co2_electrochemical_species_flux_interval_schedule": "Apply caller-declared exact-interval species molar wall-flux schedules to liquid inventory states, preserving signed source/sink identity, provider configuration, input digest and physical scope. Flux values are exogenous to the transport solve.",
    "caller_finite_gas_two_film_and_variable_liquid_transfer": "Couple a finite gas CO2 inventory with a well-mixed changing liquid volume through caller-supplied Henry and effective two-film transfer parameters, while independently integrating non-CO2* liquid species amounts and interval wall fluxes. No chemistry or kinetics is implied.",
    "caller_gasket_circumferential_contact_threshold": "Classify caller pressure nodes against an evidence-pinned threshold and ring geometry; the threshold is a descriptive screening level, not universal sealing criteria. No measured leakage calibration or acceptance rule is embedded.",
    "caller_periodic_voronoi_contact_partition": "Partition a caller-defined periodic ring into angular Voronoi cells around explicit node locations and join contiguous below-threshold cells, including the wrap-around component. This finite mesh descriptor does not reconstruct pressure between nodes.",
    "caller_wet_co2_species_film_transport_parameters": "Limit consumption of explicitly listed dissolved carbonate-bound species by a caller-defined steady planar Fick-film capacity D/delta times the boundary-to-minimum-surface concentration difference. Require provider Evidence and parameter review; do not infer diffusivity, boundary concentration, wetting, film thickness or transport-model validity.",
    "caller_calibrated_butler_volmer_reaction_set": "Evaluate caller-calibrated anodic and cathodic Butler-Volmer branches at exact boundary temperature, with caller-defined reaction direction, electron count, species stoichiometry and calibration support. Calibration and reaction applicability remain caller responsibility.",
    "finite_volume_fick_component_diffusion": "Solve caller-defined one-dimensional constant-area component diffusion with a cell-centered finite-volume spatial balance and backward-Euler time steps, fixed mouth concentration, no-flux blind tip and explicit cellwise source. Subdivide each interval within declared provider support and report discrete inventory/boundary/source closure; do not infer electromigration, species speciation, chemistry, electrochemistry or moving geometry.",
    "declared_crevice_transport_provider": "Require digest-pinned caller transport geometry, diffusivity, source, mouth concentration and declared parameter support for one explicitly named transported component. The provider declaration does not imply a universal property model or calibration.",
    "caller_gasket_bolt_sn_calibration": "Map bolt nominal stress ranges to same-condition caller Basquin calibration and apply caller ultimate-strength Goodman mean-stress correction to each rainflow cycle before linear Miner accumulation. Require explicit repeated-service history and rights review; no local notch, corrosion, fretting, hydrogen or joint qualification is inferred.",
    "caller_basquin_goodman_miner": "Use a caller-declared constant-amplitude Basquin curve, linear tensile-mean Goodman correction and linear Miner rule on rainflow-counted bolt stress cycles. The calculation is a conditional screening model, not a general bolt fatigue law or acceptance criterion.",
    "caller_reviewed_carbonate_transport_boundary_history": "Map each computed carbonate-equilibrium time knot into a typed transport boundary only after an evidence-pinned caller partition supplies the CO2*/H2CO3 split and water concentration. Preserve exact-knot order and digests; perform no temporal interpolation or full aqueous speciation.",
    "caller_reviewed_co2star_partition_and_water_concentration": "Treat hydrate partition and water concentration as externally supplied, reviewed boundary composition inputs with source digest and license lineage. The adapter converts declared mol/L carbonate species into mol/m3 without inferring equilibrium constants or unreported ions.",
    "caller_dang_van_finite_parameter_life_curve": "Interpolate a caller-owned same-condition finite Dang Van parameter versus cycles-to-failure curve in log-log coordinates only inside strictly monotone observed support. No universal life equation, extrapolation, cycle counting or variable-amplitude damage is asserted.",
    "caller_multi_bolt_to_spatial_flange_contact_influence": "Apply a caller-provided, digest-pinned linear bolt-force-to-contact-node closure operator to the selected exact multi-bolt equilibrium knot, then compose it once with reviewed non-bolt free closure. No FE response, local stress or leakage is generated.",
    "caller_gasket_joint_spatial_resultant_balance": "Reconcile digest-pinned per-bolt tensile forces and a computed unilateral contact field at a caller-reviewed exact common time. Compute discrete axial force and planar moment residuals, center of pressure and finite-node area/pressure descriptors from caller geometry; do not infer continuous fields or acceptance.",
    "caller_wet_co2_electrochemical_co2star_sink_mapping": "Couple externally supplied CO2* consumption per anodically removed-metal mole with a computed digest-pinned partial-current metal-loss history. Keep reaction mapping, review, alloy density and molar mass as caller inputs; do not infer electrochemical kinetics or local penetration.",
    "caller_wang_brown_parameter_constant_amplitude_life_data": "Fit a log-log power law by ordinary least squares from at least three distinct caller constant-amplitude tests of the same finite Wang-Brown-style parameter and material condition. Restrict predictions to observed parameter support; no variable-amplitude accumulation or universal life law is inferred.",
    "caller_co2_henry_vant_hoff_thermochemistry": (
        "Apply the integrated van't Hoff temperature correction to a caller-supplied CO2* Henry solubility coefficient using caller dissolution enthalpy and optional constant heat-capacity difference. Preserve solvent identity, reference/target temperature support, parameter record digest and Evidence. No Henry coefficient, thermochemical table, fugacity, speciation, corrosion rate or acceptance value is embedded or inferred."
    ),
    "caller_reviewed_co2_henry_carbonate_handoff": (
        "Adapt a digest-verified CO2* Henry temperature-correction result to the existing carbonate-only fixed-fugacity equilibrium calculation. Require exact agreement of upstream result/model/input and output digests, coefficient convention and unit, target temperature, solvent digest, provider revision/configuration and reference-record digest. The downstream solver covers a carbonate subsystem only; no other aqueous species, complete solution charge balance, multiphase network, reaction kinetics or corrosion rate is inferred."
    ),
    "caller_ordered_co2_henry_carbonate_history": (
        "Apply the digest-verified Henry-to-carbonate adapter once at each exact, strictly ordered caller time knot. Require a matching computed Henry-correction AssessmentResult, point input, target temperature, solvent identity and RunContext at each knot. Stop at the first failed point and retain only its successful prefix; do not interpolate or extrapolate temperature, solvent composition or Henry coefficients, and do not represent the carbonate subsystem as full aqueous speciation."
    ),
    "caller_itoh_nonproportional_hardening_calibration": (
        "Combine a caller-supplied principal-strain range and same-condition nonproportional hardening coefficient with a finite sampled strain-path factor for one reviewed closed cycle. Retain sample order, clock, tensor convention, calibration Evidence and digest. This parameter does not count cycles, map life, accumulate damage or qualify material response."
    ),
    "caller_itoh_nonproportional_strain_life_curve": (
        "Map a digest-bound Itoh adjusted strain parameter to cycle life using a caller-supplied same-condition, licensed, monotonically decreasing strain-life curve. Preserve exact material/strain-definition and curve Evidence; interpolate log-log only within support and fail closed outside it. No cycle counting, damage accumulation, material transfer or qualification is inferred."
    ),
    "caller_itoh_nonproportional_miner_block_decomposition": (
        "Use caller-declared ordered finite cycle blocks and nonnegative integer repetition counts. Recompute each block's Itoh parameter and bounded same-condition strain-life mapping, then accumulate only through the existing linear Miner rule after every block maps successfully. Require identical material condition, strain definition, shear convention, alpha calibration and licensed curve digests across blocks. No cycle extraction, sequence interaction, probability, acceptance or remaining-life qualification is inferred."
    ),
    "caller_multi_bolt_parallel_sector_joint_equilibrium": (
        "Solve a one-degree-of-freedom axial force balance at caller-declared load knots for independent tension-only linear bolts and compression-only gasket sectors with caller-supplied piecewise-linear force/compression curves. Preserve preloads, tensile areas, sector areas, source digests and Evidence. No flange bending, leakage, relaxation, code limit or qualification is inferred."
    ),
    "caller_evidence_bound_gasket_prony_parameter_lineage": (
        "Wrap the existing caller-parameterized generalized-Maxwell gasket history with exact source/material-condition Evidence and declared use-license identity, and require the requested temperature to remain inside caller-reviewed material support. Delegate the constitutive calculation unchanged; do not fit or transfer Prony parameters, add flange mechanics, predict leakage or establish qualification."
    ),
    "caller_extended_debye_huckel_activity_parameters": (
        "Compute ion activity coefficients from the extended Debye-Hückel equation using caller-supplied, evidence-pinned solvent constants, ion-size parameters, charges and temperature support. No database parameters are embedded; outside declared ionic-strength/temperature support the evaluator fails closed. This activity provider is not a complete aqueous speciation or corrosion model."
    ),
    "bam_cmsx6_creep_lis_typed_rows": (
        "Read the checksum-pinned Vh5205_C-97.LIS asset from the CMSX-6 dataset (10.5281/zenodo.14750432) as ordered typed lexical rows while retaining source line and token identity. The dataset catalog records its CC BY 4.0 declaration; embedded third-party rights remain separately bounded. The reader does not interpret measurements, fit creep laws, redistribute the raw asset, or reproduce third-party standards."
    ),
    "lyullee_lh2dt_dynamic_network_public_result_contract": (
        "Transfer only the selected node's caller-mapped public dynamic-network thermodynamic states from a revision-pinned lh2dt_models result. Preserve run/configuration/result digests and require upstream solver and junction-conservation success plus explicit node-to-asset and fluid/material review. No wall state, fluid chemistry, corrosion, hydrogen ingress, damage, life or acceptance is inferred."
    ),
    "wang_brown_1993_path_independent_multiaxial_strain_parameter": (
        "For caller-selected finite shear-direction planes and one reviewed closed-cycle reversal arc, combine engineering-shear half-range with a caller-calibrated normal-strain excursion parameter and report the largest sampled candidate. This does not detect/count cycles, interpolate unsampled extrema, search a continuous plane, map to life, transfer calibration, or qualify a material."
    ),
    "caller_declared_well_mixed_solution_component_inventory_balance": (
        "Advance caller-declared component mass and liquid volume through ordered additions, perfectly mixed liquid withdrawals, and separately supplied component consumption. Preserve the caller's component identity, evidence and event order. This is inventory bookkeeping only; it does not infer chemical reactions, dissolution, cleaning performance, compatibility or acceptance."
    ),
    "caller_reviewed_gasket_mean_contact_pressure": (
        "Calculate mean gasket contact pressure from a caller-reviewed compressive reaction and either reviewed effective area or circular-annulus dimensions. Preserve force and geometry evidence and require a shared physical scope plus uniform-mean interpretation review. This is F/A bookkeeping; it does not predict local contact fields, leakage, seal performance or acceptance."
    ),
    "caller_crevice_geometry_aware_solid_deposition_extent": (
        "Apply caller-supplied, signed endpoint reaction extents to a closed aqueous/neutral-solid inventory inside the existing segmentwise crevice recession fixed point. Bind the trial aperture path, endpoint aqueous states, phase inventory, molar volume, extent limits, provider/configuration digests and repeated-evaluation determinism. Enforce element/charge balance, nonnegative aqueous/solid inventories and phase-volume-to-gap closure before committing the trial. This is an endpoint operator split; it does not infer phase selection, Ksp, kinetics, morphology, solid mechanics, continuous precipitation feedback or physical qualification."
    ),
    "caller_finite_gas_variable_liquid_two_film_balance": (
        "Integrate caller-specified finite gas CO2 fugacity inventory, variable well-mixed liquid volume and CO2star concentration with piecewise-constant two-film transfer, signed condensate volume flux, and caller-specified inflow CO2star composition. Use a caller-pinned numerical IVP solver and record the per-area gas/liquid inventory ledger and closure residual. No EOS, gas capacity, correlations, water chemistry, reaction, spatial gradient or corrosion law is inferred."
    ),
    "caller_variable_condensate_two_film_mass_balance": (
        "Advance a caller-declared finite, well-mixed aqueous patch inventory using piecewise-constant gas-film transfer, liquid-film transfer, incoming condensate volume/composition and well-mixed liquid outflow. Preserve finite-volume and dissolved CO2* ledgers with exact interval clocks. No mass-transfer correlation, condensate generation, selective evaporation, reaction, speciation, spatial gradient or corrosion law is inferred."
    ),
    "caller_crevice_geometry_aware_aqueous_chemistry_provider": (
        "Adapt a caller-owned aqueous reaction provider to each trial aperture in the existing bounded crevice transport-recession fixed-point solver. Require an exact ordered aqueous species set, provider and configuration identity, declared concentration/aperture/time support, finite nonnegative outputs, Evidence and digest lineage, and charge/element-balanced reaction stoichiometry. The provider supplies reaction behavior; this interface does not select phases, calculate activities, precipitation/deposition, hydrodynamics beyond the existing optional endpoint path, or establish physical validity."
    ),
    "caller_net_retained_condensate_flux_history": (
        "Integrate caller-supplied net retained liquid-water mass flux over a fixed patch to obtain nonnegative areal inventory, equivalent uniform film thickness, wet duration, dryout timing, and separately recorded sink demand beyond depletion. This bookkeeping does not predict condensation, retention, drainage, evaporation, film morphology, gas-liquid transport or corrosion."
    ),
    "coolprop_pure_water_saturated_vapor_state": (
        "Call the optional, lazily imported CoolProp AbstractState provider to obtain pure-water saturated-vapor pressure and fugacity coefficient at the caller wall temperature. Bind the backend, software version/revision, input state, caller-declared absolute bound and output digest. This property adapter does not calculate actual gas-mixture water fugacity, solution activity, condensation quantity or corrosion."
    ),
    "coolprop_pure_water_single_phase_state": (
        "Call the optional, lazily imported CoolProp AbstractState provider at a caller-declared pure-water pressure/temperature state and require the computed phase to match the reviewed liquid, gas or supercritical declaration. Return density, enthalpy, heat capacity, viscosity, thermal conductivity, speed of sound and compressibility with backend/version/revision and request/result digests. Reject two-phase states; do not infer mixture properties, transport correlations, corrosion or qualification."
    ),
    "wang_brown_1993_normal_strain_excursion_on_maximum_shear_reversal": "Associate a caller-counted finite shear rainflow cycle with the paired normal-strain samples over the cycle's inclusive source-index interval and return the sampled minimum, maximum and range. Require a pinned projected-cycle result, matching ordered sample IDs, source Evidence and caller clock-alignment review. This is a sampled temporal feature consistent with the literature concept, not a complete Wang-Brown damage/life criterion; it does not recount cycles, infer between-sample extrema or qualify material response.",
    "caller_crevice_solid_molar_volume_inventory": "Convert each caller-supplied, digest-bound solid-phase inventory per reference area into a volume contribution using its Evidence-backed caller molar volume. Preserve exact chemistry/result identity, cell and phase order, and review gates. This is volume bookkeeping only; it does not determine deposition location, porosity, morphology, aperture closure, transport, kinetics, corrosion or qualification.",
    "caller_crevice_deposition_aperture_geometry_mapping": "Map caller-reviewed solid-volume snapshots to mean-equivalent and covered-patch gap measures using explicit cell geometry, reference area, deposition faces, and coverage. Preserve exact result digests and physical/time/cell alignment. Equal face partition and uniform within-cell coverage are declared assumptions; this geometry mapping does not resolve deposit morphology, porosity, adhesion, transport feedback, corrosion or acceptance.",
    "caller_finite_shear_path_polygon_area_nonproportional_loading_descriptor": "Compute the signed finite polygon area from caller-ordered samples of two engineering shear-strain coordinates on a selected plane. Require explicit axis, path-closure and convention reviews, retain source digest and Evidence, and report an unnormalized geometric descriptor only; no interpolation, fatigue damage, life or qualification is inferred.",
    "caller_crevice_cell_local_candidate_saturation_screen": "Screen caller-specified candidate-solid saturation independently for each local cell in one exact transport knot, preserving the composition ledger, local mass-action result, cell transport context and solubility-source digests. A common candidate solubility set requires common temperature and standard state. This does not select phases, calculate precipitation amount or kinetics, mix cells, update geometry or qualify corrosion behavior.",
    "caller_crevice_cell_saturation_exposure_reconstruction": "Integrate only the positive part of caller-reviewed, piecewise-linear sampled log10 saturation ratio over exact crevice-cell history knots, preserving cell and candidate identities and source-result lineage. The finite-sample diagnostic is an exposure descriptor, not precipitation amount, phase selection, nucleation, kinetics, corrosion rate or acceptance.",
    "caller_crevice_wall_sink_velocity_arrhenius_calibration": "Estimate a linear Arrhenius temperature response for positive measured effective crevice wall-transfer velocities using only the declared calibration observations and reciprocal-temperature regression around an explicit reference temperature. Keep holdout source groups entirely outside fitting, preserve observation/Evidence digests, reject extrapolation and unsupported negative activation energy. The result concerns an effective transfer velocity, not a metal-loss rate, corrosion law or qualification.",
    "caller_crevice_wall_sink_calibration_application": "Recompute the supplied digest-bound effective wall-transfer Arrhenius calibration, verify its complete result identity, and apply only at exact caller temperature knots contained within the fit's observed support through the existing wall-sink rate-history evaluator. Preserve calibration, request and result lineage. This adapter supplies an effective wall-transfer velocity history only; it does not model chemistry, metal loss or corrosion rate.",
    "caller_finite_liquid_two_film_co2star_mass_balance": "Advance a fixed-volume, well-mixed liquid's neutral dissolved CO2 inventory over caller-declared contiguous intervals with fixed gas fugacity and piecewise-constant two-film transfer resistances. Preserve fugacity, Henry-law and transfer-provider identities, exact interval mass balance and parameter Evidence. This analytical transfer history excludes gas depletion, aqueous speciation, reaction, flow, corrosion rate and risk.",
    "papadopoulos_1995_high_cycle_integral_multiaxial_criterion": "Evaluate a finite caller-supplied orientation quadrature approximation to a Papadopoulos P1 high-cycle fatigue-limit form using sampled closed-cycle resolved-shear half-ranges and a caller-calibrated hydrostatic term. Require matching material condition, source Evidence and explicit quadrature/calibration reviews. No continuous orientation error bound, fatigue-life prediction, damage accumulation or qualification is inferred.",
    "caller_papadopoulos_p1_parameter_life_curve_loglog_mapping": "Compose the finite-quadrature P1 parameter calculation with a caller-supplied same-condition parameter/life curve and interpolate only within its strictly ordered support in log-log coordinates. Preserve calibration, history, curve and Evidence digests. No extrapolation, cycle counting, scatter, sequence effect or qualification is inferred.",
    "caller_papadopoulos_p1_cycle_block_life_and_linear_miner_accumulation": "Apply the finite-quadrature P1 parameter and bounded caller-curve life mapping to each caller-declared cycle block, then sum cycle-count/life fractions under an explicit linear Miner review. Preserve block order and source digests. Caller owns cycle decomposition and repetition counts; sequence effects, scatter, probability and qualification are excluded.",
    "caller_conditional_carbonate_constants_and_alkalinity": "Solve a carbonate-only alkalinity balance at a caller-fixed dissolved CO2-star state with caller-supplied conditional concentration constants using a bounded scalar root procedure. Preserve thermodynamic-convention Evidence and explicit review. Other buffers, nonideal activities, kinetics, corrosion and risk are outside this calculation.",
    "caller_papadopoulos_p1_endurance_limit_coefficient_calibration": "Derive the nonnegative hydrostatic coefficient in the caller-selected P1 limit relation from paired same-condition fully reversed smooth-specimen axial and torsional endurance limits. Require source Evidence and matched test-basis review; the coefficient does not itself predict life, damage or qualification.",
    "caller_crevice_calibrated_wall_flux_boundary": "Build a bounded, evidence-linked callable wall-flux boundary from a digest-verified calibrated effective wall-transfer history and caller surface-concentration history. Require exact shared time/cell geometry, species and condition identity, and explicit sign/interpolation reviews. Flux is inward-positive and supplied to the transport solver, which owns area weighting; the adapter neither runs transport nor models surface chemistry or corrosion.",
    "caller_crevice_multispecies_calibrated_wall_flux_boundary": "Build an independently calibrated wall-flux callback for an ordered set of transported species from digest-bound wall-transfer histories and caller equilibrium-concentration profiles on common geometry/time knots. Preserve species order, Evidence, bounded interpolation and inward-positive flux. No competitive site chemistry, coupled reaction or transport solve is implied.",
    "caller_crevice_wall_sink_leave_one_group_out_diagnostic": "Recompute a digest-bound crevice wall-sink Arrhenius fit across leave-one-calibration-source-group-out folds, never using the separately declared external holdout. Report fold parameter spread and out-of-fold residual diagnostics with source-group lineage. This measures within-source calibration sensitivity, not independent validation, confidence limits, transfer or qualification.",
    "caller_crevice_kinetic_solid_inventory_to_solid_volume": "Convert exact digest-bound competing-solid kinetic-transport output knots from fixed-geometry volumetric solid concentration to per-reference-area inventory using the campaign cell geometry, then compose with the existing solid molar-volume inventory evaluator. Preserve phase/cell/clock order and require closed upstream aqueous inventory. No moving-geometry feedback, deposit morphology, coverage, aperture change or qualification is inferred.",
    "caller_crevice_saturation_path_average_rate": "Integrate the existing caller precipitation/dissolution power law over each caller-reviewed piecewise-linear saturation path, split the interval at saturation ratio one, and provide finite quadrature interval-average rates to the existing inventory-limited kinetic ledger. Preserve exact local cell/phase/time lineage. Saturation is not updated inside an interval; finite quadrature has no claimed error bound and no simultaneous chemistry/geometry solution is implied.",
    "caller_crevice_solid_inventory_immobile_geometry_remap": "Remap immobile per-phase solid inventory across one exact caller-reviewed fixed-geometry state boundary by conserving per-reference-area moles and dividing by target cell liquid-volume basis. Bind source kinetic campaign/result, target geometry result, grid, phase order and exact time. No within-interval motion, inter-cell transport, reaction, precipitation, dissolution or coupled geometry feedback is inferred.",
    "caller_crevice_wall_flux_to_species_inventory_history": "Integrate the existing multispecies wall callback against caller bulk concentration and exact geometry wall-area density into per-species transferred amount per cell and interval. For the declared linear paths, use the fixed three-point Gauss-Legendre rule and preserve signed boundary flux, order, clock and source digests. This records boundary transfer only; it does not infer reaction extent, metal loss or solid formation.",
    "caller_wet_gas_wall_condensate_thermo_state": "Compare caller water-vapor fugacity with wall-temperature condensate equilibrium fugacity using deterministic input bounds, and estimate the neutral CO2star concentration in incipient liquid from caller CO2 fugacity and a compatible Henry coefficient. This marks thermodynamic possibility only and does not infer condensate amount, pH, corrosion or risk.",
    "trefethen_full_bandwidth_periodic_tensor_interpolant": "Construct the real full-bandwidth trigonometric interpolant of caller uniformly spaced exactly closed tensor-cycle samples, treating even-grid Nyquist content explicitly, and evaluate only requested phases. Sampling periodicity and bandwidth are caller reviewed; no filter, anti-aliasing, reconstruction error bound or fatigue criterion is inferred.",
    "caller_uniform_periodic_real_trigonometric_tensor_interpolation": "Construct the full-bandwidth real trigonometric interpolant of uniformly sampled, exactly closed caller tensor cycles, including the even-grid Nyquist term, and evaluate requested phases. Preserve tensor components and phase lineage. Uniform periodic sampling and suitability are caller-reviewed; no filtering, anti-aliasing, interpolation error bound or fatigue law is inferred.",
    "caller_periodic_tensor_fourier_rates": "Analytically differentiate the full-bandwidth real Fourier interpolants of caller uniformly spaced, exactly closed stress and strain tensor cycles at requested phase points, then scale by caller cycle period to physical time derivatives. Preserve component convention and units; no derivative error bound, constitutive law, fatigue damage or life is inferred.",
    "caller_periodic_fourier_tensor_work": "Compute the signed closed-loop tensor stress-strain work of the caller full-bandwidth periodic Fourier interpolant from its real Fourier coefficients with tensor shear contraction weights. This is exact only for the declared interpolant and represents signed net work, not plastic dissipation, fatigue damage, life or qualification.",
    "caller_exact_closed_tensor_work_fourier_orthogonality_integral": "Compute exact signed closed-cycle stress-strain work for the caller's finite-bandwidth real Fourier tensor interpolant using coefficient orthogonality and the declared tensor/engineering shear convention. The result is exact for that interpolant only and is not automatically plastic dissipation or a fatigue metric.",
    "caller_periodic_fourier_work_life_curve": "Compose the caller periodic Fourier tensor-work calculation with an absolute signed-work-to-life calibration curve, bounded log-log interpolation, and caller-declared block counts under an explicitly reviewed linear Miner sum. The curve and interpretation are user-supplied; no extrapolation, plastic dissipation, sequence interaction, probability or qualification is inferred.",
    "caller_periodic_fourier_tensor_work_life_curve_and_miner_bridge": "Compose finite-bandwidth periodic Fourier stress-strain work with a caller same-condition absolute-work/cycles-to-failure curve, bounded log-log interpolation and caller block repetitions under an explicit linear Miner rule. Preserve inputs and curve digests; signed net work is not assumed to be plastic dissipation, and no extrapolation or qualification is inferred.",
    "caller_finite_gas_finite_liquid_two_film_balance": "Advance finite gas and well-mixed liquid neutral CO2 inventories together over caller-declared contiguous intervals using a closed-form two-film transfer balance and caller-provided constant gas inventory capacity. Preserve Henry/film/capacity provider evidence and exact signed conservation ledger. No equation of state, changing capacity, carbonate chemistry, reaction, corrosion or risk is inferred.",
    "caller_disjoint_wet_co2_transfer_zones": "Aggregate signed instantaneous gas-to-liquid transfer over caller-declared disjoint interface zones, each with its own local Henry and two-film state, while requiring exact zone-area partition and preserving per-zone gradients and transfer ledger. This does not model cross-zone mixing, reservoir depletion, time evolution, corrosion or localized attack.",
    "caller_pseudofirst_order_co2_film_kinetics": "Solve a steady one-dimensional stagnant-film diffusion/reaction balance using a caller apparent irreversible first-order CO2star sink coupled algebraically with gas-film resistance. Report gas uptake, liquid-film reaction consumption and bulk CO2star delivery separately with mass-balance residual. No kinetic fit, carbonate equilibrium, flow renewal, corrosion or risk is inferred.",
    "small_strain_j2_associative_return_mapping_with_linear_prager_kinematic_and_isotropic_hardening": "Advance a caller-supplied small-strain symmetric tensor path with an isotropic elastic predictor and backward-Euler radial return on a von Mises surface with linear isotropic and Prager kinematic hardening. Preserve the declared tensor-shear convention, initial state, material Evidence and interval order. One update is performed per supplied interval; no adaptive substepping, cyclic fatigue law, material fit or qualification is included.",
    "paolinelli_nesic_2021_chilton_colburn_liquid_transfer": "Estimate an integral liquid-side mass-transfer coefficient from caller-supplied local liquid mean velocity, reviewed wall shear, molecular diffusivity and physical properties using the independently implemented Chilton-Colburn analogy with an explicit friction exponent. Preserve provider/property digests and applicability gates. This does not determine two-phase hydrodynamics, wall wetting, gas-film resistance, corrosion rate or life.",
    "paolinelli_nesic_2021_chilton_colburn_gas_film": "Estimate a gas-side film coefficient from caller-supplied turbulent gas properties, flow inputs and equation-of-state concentration sensitivity using an independently implemented Chilton-Colburn analogy with caller exponent. Preserve provider/configuration digests and applicability limits. This is not the paper's full multiphase near-wall model and does not compute hydrodynamics, wetting, corrosion rate or life.",
    "caller_deposition_aperture_to_transport_geometry_mapping": "Convert an exact digest-pinned deposition-aperture history into the existing crevice transport geometry-history contract using caller-reviewed cross-section geometry and cell mapping. Preserve source, scope, time and cell order. The result supports operator-split sequential transport only and does not solve simultaneous chemistry, deposition, flow or geometry feedback.",
    "caller_gasket_contact_response_root_localization": "Narrow one caller-reviewed scalar contact-response sign-change bracket with digest-bound external FE/contact evaluations and provider receipts at bisection times. Require a reviewed single continuous monotone root and stop at the first invalid receipt; do not search for hidden or multiple roots or assert an exact physical event time, leak rate, acceptance or probability.",
    "plos_ct110_wet_co2_typed_rows": "Read only the pinned single-sheet CT110 wet-CO2 workbook after caller attribution and computational-use authorization. Preserve the original three provider rows, workbook/sheet/row/cell identities, stored values and cell types, and Evidence digests. The source supports one narrow study's three temperature summaries for weld metal and base metal; replicate counts, a factorial operating map, corrosion kinetics, extrapolation and qualified validation are not inferred.",
    "caller_finite_sample_principal_stress_axis_rotation_descriptor_nonproportional_loading": "Compute adjacent-sample angular travel of the largest algebraic principal-stress axis for symmetric tensors in the declared component order, treating eigenvector sign as equivalent. Require exact cycle closure and a caller threshold separating the largest eigenvalue from the second. The finite sampled kinematic descriptor does not reconstruct paths or predict fatigue damage, life, acceptance or qualification.",
    "caller_finite_shear_hydrostatic_dang_van_limit_screen": "Apply a caller-calibrated Dang Van-style high-cycle limit screen on an explicit finite set of oriented material shear systems and time samples. Center each resolved shear history by its caller-clock trapezoidal mean, combine its maximum absolute centered value with instantaneous hydrostatic stress through the caller coefficient, and compare with the same-condition caller limit. Preserve sample timing, system population, Evidence and calibration digest; do not infer continuous plane/time extrema, fatigue life, probability, acceptance or qualification.",
    "caller_finite_quadrature_papadopoulos_p2_limit_screen": "Evaluate a finite-quadrature Papadopoulos P2-style deterministic fatigue-limit screen from caller-provided orthonormal material planes and normalized in-plane shear directions. At each requested direction compute the signed resolved-shear half-range and a weighted quadratic generalized amplitude, combine its governing plane value with the maximum sampled hydrostatic stress using a caller coefficient, then compare with a same-condition caller limit. Preserve the finite quadrature and calibration lineage; do not claim continuous angular optimization, fatigue life, probability or qualification.",
    "caller_crevice_aperture_displacement_flow_continuity": "From a digest-pinned complete blind-slit aperture/volume history, compute interval-mean one-dimensional incompressible mouth displacement flow by summing downstream cell-volume change rates, with zero flow beyond the blind tip. Preserve exact source/result lineage and caller cell order. This is kinematic bookkeeping only; no pressure, momentum, face-velocity profile, transport, reaction or corrosion is solved.",
    "caller_finite_sample_sines_mean_hydrostatic_limit_screen": "Evaluate a finite-sample invariant fatigue-limit descriptor from caller-reviewed closed tensor stress samples: combine the existing maximum-pairwise deviatoric sqrt(J2) half-distance with a trapezoidal time average of hydrostatic stress using explicit caller coefficients, then compare with a same-condition caller limit. Preserve calibration Evidence and scope review. This discretized screen does not establish a continuous-path criterion, life, probability, acceptance or qualification.",
    "caller_wet_co2_two_film_transfer_history": "At each caller-ordered exact time knot, independently evaluate the existing steady two-film CO2 transfer point model with matching timestamp and asset/location identity. Preserve strict chronology, each point's source/result digests, successful prefix and first noncomputed knot. No inter-knot interpolation, transient interface dynamics, carbonate speciation, reaction, corrosion or qualification is inferred.",
    "caller_wet_co2_two_film_transfer_inputs": "Compute steady gas/liquid CO2-star transfer from caller-provided gas fugacity, Henry convention, bulk liquid concentration and two film coefficients using an algebraic interfacial balance. Preserve exact condition, provider, coefficient-source Evidence and input digest. The calculation does not solve aqueous carbonate speciation, gas/liquid dynamics, surface reaction, scale growth, corrosion rate or qualification.",
    "caller_crevice_arrhenius_wall_sink_rate_history": "Apply the existing Arrhenius rate calculation to caller-provided reference wall-transfer velocity and activation energy at each exact reviewed crevice-temperature knot. Enforce declared temperature support, preserve chronology and fail the history at its first invalid numerical state. Do not infer activation parameters, interpolate time, solve concentration/transport, or claim corrosion kinetics or qualification.",
    "caller_gasket_leakage_fit_residual_diagnostics": "Summarize raw and residual-scale-normalized signed error, absolute error, root-mean-square error and maximum absolute error from a digest-pinned completed caller-calibrated gasket leakage map. Verify output row identities and preserve separate calibration, holdout, source-group and caller specimen-label partitions. This is a descriptive assessment of a precomputed surface; it does not refit, claim independence, infer uncertainty or establish physical qualification, sealing acceptance or failure probability.",
    "caller_finite_sample_multiaxial_invariant_limit_screen": "Evaluate a caller-calibrated linear combination of finite-sample maximum hydrostatic stress and half maximum pairwise deviatoric sqrt(J2) distance, then compare it with a caller-supplied same-condition limit. Preserve calibration Evidence/digest and require explicit coefficient, material-scope and use review. This deterministic descriptor-to-limit screen does not interpolate unsampled paths or establish fatigue life, probability, code acceptance or qualification.",
    "caller_crevice_transient_wall_sink": "Evaluate a finite caller-requested eigenfunction expansion for one dissolved species in a fixed blind slit with constant diffusivity, fixed mouth concentration, zero-flux blind tip, uniform matching initial concentration and irreversible first-order wall sink. Preserve exact input order, digest, Evidence, requested grid and declared truncation. Do not report an error/convergence bound or infer multi-species chemistry, phase equilibrium, corrosion, wall loss or qualification.",
    "caller_multiaxial_tensor_work_cycle": "Compute the signed finite-sample stress:strain path integral over caller-ordered, exactly closed symmetric tensor samples with separate pinned stress and strain sources, an explicit tensor/engineering shear convention, reviewed conjugacy and canonical input digest. The result is not necessarily dissipative energy and must not be converted to fatigue damage, life, probability, acceptance or qualification.",
    "caller_external_flange_contact_state_provider": "Refine one digest-bound observed flange contact-state transition bracket only through a caller-supplied external contact-state provider with matching identity, revision, configuration, source context, midpoint time, Evidence and response digest. Require a caller-reviewed monotonic single transition, time tolerance and bounded evaluation budget. Return a narrower bracket only; do not provide an FE solver or claim exact event time, hidden transition discovery, sealing acceptance, leakage, stress, probability or qualification.",
    "caller_pitzer_salt_saturation_index": "Compute log10(Q/Ksp) from one caller-reviewed Pitzer pure-salt mean ionic activity and a temperature-matched, Evidence/hash-bound caller solubility product using the declared stoichiometric product exponent and shared standard state. Withhold the index unless both data and authorization reviews pass and the Pitzer activity call computes. Report only an equilibrium saturation screen; do not infer phase amount, nucleation, kinetics, mixed electrolyte behavior, corrosion, probability, acceptance or qualification.",
    "caller_pitzer_salt_finite_scenario_envelope": "Evaluate 2–200 caller-ordered single-pure-salt Pitzer requests sharing the reviewed salt formula and temperature. Preserve each request/result digest and report extrema only after every case computes; otherwise retain the completed prefix and first failure without a partial envelope. This is a finite-list descriptor, not a continuous/global uncertainty bound, mixed-electrolyte model, probability, corrosion prediction or qualification.",
    "caller_computed_flange_contact_history": "Inspect the exact digest-bound output of an existing computed viscoelastic flange contact history. Preserve caller scope/time review, ordered solver knots and stable node identity; report only open/closed state changes observed between adjacent knots as brackets. Do not interpolate event time, infer hidden transitions, generate FE response, leakage, seal acceptance, stress or failure probability.",
    "caller_sampled_stress_invariant_history": "For one caller-reviewed exactly closed symmetric stress tensor cycle in explicit [xx, yy, zz, xy, yz, zx] order, report maximum sampled hydrostatic stress and the maximum pairwise sqrt(J2) distance among the finite supplied deviatoric samples, with witness sample identities. Preserve the source pin, canonical input digest, order and review flags. Half the finite diameter has a conventional amplitude interpretation only for collinear paths. Do not interpolate, count cycles, infer a fatigue law, life, probability, acceptance or qualification.",
    "caller_crevice_steady_wall_sink": "Evaluate the exact steady one-dimensional solution for one caller-supplied dissolved species in a fixed blind slit with constant effective diffusivity, a constant mouth concentration, zero-flux tip and irreversible first-order wall sink. Report the finite profile and inlet-versus-integrated-sink balance. Require caller Evidence and explicit review of assumptions; do not infer speciation, phase equilibrium, corrosion rate, wall loss, transient behavior or qualification.",
    "caller_elastic_joint_to_flange_contact_history_transfer": "Evaluate the existing caller-reviewed exact-knot elastic joint load history, then apply only a caller-evidenced, scope/revision/reference-state reviewed nodal incremental closure-per-clamp-force map to the difference from an explicit reference clamp force. Reuse the existing unilateral flange contact field solver at each exact knot and preserve complete source/result digests, location, material, time and prefix failure. Do not infer FE compliance, transfer coefficients, bolt/gasket constitutive law, seal pressure/acceptance, leakage, probability or qualification.",
    "mendeley_atmospheric_corrosion_typed_rows": "Read only the exact-pinned Mendeley atmospheric-corrosion compilation through its existing bounded parser and caller authorization. Preserve source order, reported units/meanings, archive/member/row Evidence and authorization digests. The record declares CC BY 4.0 for the compilation, but rights for underlying field/program/paper observations remain unresolved; keep rows local-only and do not redistribute them. Do not recalibrate rates, infer site validity, fit climate response, or claim independent validation.",
    "zenodo_zr_nb_sn_electrochemical_typed_rows": "Read only the eight SHA-256-pinned version-2 Zenodo XLSX workbooks after caller attribution and local-only authorization. Preserve workbook, worksheet, row, cell order, cell types, formula text and digest-bound Evidence. The provider declares CC BY 4.0; retain required attribution and keep the acquired workbooks outside public release artifacts. Do not infer specimen identity, corrosion rates, localized penetration, life, acceptance, or probability from the raw spreadsheet representation.",
    "mendeley_x80_srb_scc_lab_rows": "Use only the three SHA-256-pinned version-1 Mendeley X80/SRB legacy XLS assets after caller attribution and local-only computational-use authorization. Preserve workbook, worksheet, row and cell order, cell storage types, exact dataset DOI and Evidence lineage. Keep raw rows local; do not infer electrochemical units, specimen grouping, conditions, SCC susceptibility, corrosion rate or qualification. Third-party content rights require separate review.",
    "caller_ince_glinka_gsa_miner_campaign": "For each complete caller-defined representative closed tensor cycle and caller-allocated cycle count, reuse the existing finite-plane Ince-Glinka GSA-to-life mapping on one exact shared calibration/material/scope curve. Sum only the completed finite group lives with the existing linear Miner calculator after every group succeeds. Do not extract cycles, infer sequence effects, fit curves, derive counts, probability, acceptance, remaining life or qualification.",
    "mendeley_fracture_toughness_temperature_typed_rows": "Read only the catalogued pinned Mendeley Table A2/A3 workbook after caller attribution and local-only authorization. Preserve exact split/table and row identity, parser values, workbook/member/row Evidence and authorization digests. The CC BY 4.0 record covers the compilation; underlying observation rights remain unresolved, so do not redistribute rows or make broader rights claims. Do not fit master curves, convert toughness, establish ASTM compliance, acceptance or qualification.",
    "caller_crevice_spatial_mass_action_workflow": "For each exact transport-knot cell, require a complete caller-authored mass-action system with unique request identity, empty result slots, explicit local-solver authorization and cell-chemistry mapping review. Reuse the existing aqueous mass-action solver independently per cell, stop at the first failure, and assemble the existing volume ledger only when every required cell result is computed. Do not generate chemistry, constraints, phases, kinetics, corrosion, transport feedback or bulk mixing.",
    "figshare_corrosion_alloy_metrics_typed_rows": "Read only the catalogued exact-pinned Figshare corrosion-alloy compilation after caller attribution and local-only computational-use authorization. Reuse the existing bounded parser and preserve workbook row order, reported fields, censoring, units, file/row digest and Evidence/auth lineage. CC BY 4.0 applies to the compilation; rights to underlying publication observations remain unresolved, so do not redistribute source rows or make dataset-wide rights claims. Do not infer missing metrics, corrosion rates, uncertainty, acceptance or qualification.",
    "zenodo_mg_deis_typed_rows": "Read only the checksum-pinned CC0 AZ31/WE43 DEIS archive after caller attribution/local-only authorization. Reuse the existing bounded member parser, preserving matrix row/column order, native numeric values, source/member/archive digest, Evidence and authorization lineage. Keep axis, time, frequency, signal units, corrosion interpretation and specimen comparability unresolved; do not infer rates, protection, acceptance or qualification.",
    "zenodo_ceit_uniform_corrosion_field_typed_rows": "Read only the catalogued CEIT uniform-corrosion JSON after matching its filename, byte count, MD5 and local acquisition SHA-256 before reusing the existing parser. Preserve observation order, caller-selected units/clock choices, source/Evidence/authorization and row digest lineage. Keep raw signals local and do not infer thickness, corrosion rate, uncertainty, acceptance, life or probability from unresolved ToF and voltage fields.",
    "caller_fixed_fugacity_carbonate_to_scale_kinetics": "Bind every exact knot of a computed fixed-fugacity carbonate history to caller-evidenced activity coefficients, activities for other selected-solid species, and temperature-supported Ksp records. Screen only the caller-selected phase, then pass the complete finite saturation-ratio history to the existing caller surface-scale kinetic law under explicit interpolation/applicability review. Do not infer activities, Ksp, phase selection, kinetic parameters, corrosion, protection, life, probability or qualification.",
    "zenodo_pressure_decay_leak_sample_row_adapter": "Read only the SHA-256-pinned CC BY 4.0 pressure-decay workbook after caller computational/local-use authorization and attribution. Preserve sheet, series, row index, time, temperature and pressure values with provider-described basis and lineage. The source has no blank/reference configuration for calibration; do not infer a leak rate, defect size or acceptance.",
    "uci_metropt3_process_history_reader": "Read only the exact UCI MetroPT-3 CC BY 4.0 archive and CSV member under caller attribution/local-use authorization. Verify archive and member byte counts and SHA-256 before lazy streaming; preserve source row/index/timestamp/raw cells and provider-native numeric signals. Do not normalize units, infer pressure reference, corrosion/degradation, failure cause or maintenance decisions.",
    "mendeley_thermal_rod_typed_rows": "Read only the catalogued SHA-256-pinned Mendeley thermal-rod transient archive after caller attribution and local computational-use authorization. Preserve run identity, source CSV order and row number, archive/member digests, reported time, six ambient-excess thermocouple channels, and controller counts with their declared units and Evidence. Do not convert controller setting to power/heat flux, infer thermal properties from the measurements, or treat the experiment as corrosion or structural-integrity qualification.",
    "mendeley_crack_arrest_typed_rows": "Read only the catalogued SHA-256-pinned CC BY 4.0 Mendeley C1/C2 crack-arrest archive after caller attribution and local computational-use authorization. Preserve exact specimen/CSV row order, raw signs and zeros, parser-reported units and transforms, and archive/member/row Evidence digests. Do not infer fracture toughness, validate a test method, pool C1/C2 specimens, fit a resistance curve, or establish an acceptance/qualification value.",
    "mendeley_guided_wave_typed_sample_rows": "Read only the catalogued SHA-256-pinned CC BY 4.0 guided-wave archive after caller attribution and local computational-use authorization. Preserve the selected acquisition/frequency sample order, repeated distances, native voltage fields, archive/nested/member/row digests and Evidence. Do not infer corrosion, wall loss, defects, temperature, timestamps, POD or qualification from signal amplitudes.",
    "zenodo_18735817_cathodic_protection_typed_rows": "Read only the five locally held, SHA-256-pinned CC BY 4.0 cathodic-protection CSV exports after caller attribution and local computational-use authorization. Preserve DPlot curve/sample identity, native axes, potential and authorization digest. The pins protect the held copies and are not represented as publisher checksums. Keep samples local; do not infer a protection criterion, corrosion rate, reference-electrode subtype, or calibration applicability.",
    "caller_findley_life_to_ordered_miner_block_history": "For each caller-ordered cycle block, require a computed canonical-input-digest-consistent calibrated Findley life result with matching asset, location, time basis and material-condition identity. Under explicit caller review of linear damage, exact block order and absence of sequence interaction, sum cycles divided by the corresponding life over only the finite supplied sequence and bracket the first integer cycle crossing of the caller threshold. Preserve each result digest and return no probability, extrapolated remaining life, acceptance or qualification.",
    "caller_crevice_transport_volume_weighted_composition_handoff": "Bind computed cellwise transport outputs to the exact crevice campaign input, geometry history and result digest. At each exact solver knot calculate cell inventory as cell volume times concentration and a volume-weighted bulk summary, while retaining all spatial cell fields and explicit pre/post-remap states at geometry discontinuities. This is bookkeeping only; do not infer equilibrium, reactions, kinetics, phase changes, corrosion, acceptance or risk.",
    "caller_wet_co2_simulation_rows_to_wall_loss_scenarios": "Bind each exact CC BY NORSOK M506 simulation-grid row and archive Evidence digest to one finite scenario. Require measured baseline-thickness Evidence and caller-declared or open-dataset Evidence for the required-thickness limit. Under explicit caller review of mapping, constant-rate duration, baseline scope and finite-set interpretation, calculate uniform area-average wall loss, remaining-thickness margins and threshold crossings over the specified exposure, rejecting scenarios whose loss exceeds the measured baseline. These are generated model scenarios only; do not infer weights, probability, field prediction, acceptance or qualification.",
    "caller_ordered_elastic_joint_load_history": "Evaluate each exact caller-supplied ordered time snapshot with the registered linear elastic two-spring joint-load partition. Preserve per-knot input digests and common asset/location/time identity; report only the first supplied snapshot below a caller clamp-force threshold. Do not reconstruct between knots or infer gasket constitutive response, contact transitions, leakage, seal acceptance or qualification.",
    "caller_piecewise_linear_corrosion_rate_thickness_history": "Require caller-evidenced, nonnegative corrosion-rate knots starting at elapsed exposure time zero, measured baseline-thickness Evidence, caller-declared or open-dataset required-thickness Evidence, and reviewed asset/location/material/time scope. Reconstruct rate linearly only between adjacent knots and integrate each segment by the exact trapezoid, retaining knot/input digests and all interval evidence. Report a required-thickness crossing bracket conditional on that reconstruction; do not commit an interval that consumes more than the measured baseline. No extrapolation, probability, field transfer, acceptance or qualification is inferred.",
    "caller_ince_glinka_gsa_life_curve": "Map the existing finite-plane Ince-Glinka GSA result through a caller-supplied strictly monotone calibration curve whose material-condition identity matches the calculation and whose points each retain source Evidence. Use log-log interpolation only within positive finite supplied support and preserve the calculation and request digests. Do not fit the curve, extrapolate, count cycles, transfer calibration between conditions, infer probability or establish material qualification.",
    "caller_crevice_local_speciation_volume_ledger": "Bind separately computed, digest-pinned aqueous mass-action results to every cell at exact knots of one digest-pinned crevice transport-composition campaign. Require explicit review of state-to-constraint mapping, species/result lineage, spatial separation, volume basis and no bulk/phase inference. Convert declared mol/L species concentrations to conditional per-cell inventories from the supplied m3 volumes; report charge and available elemental totals as diagnostics and retain only complete exact-knot prefixes. Do not solve equilibrium, mix compartments, infer charge closure, kinetics, corrosion or acceptance.",
    "caller_component_constraint_basis_for_crevice_local_speciation": "For each cell and exact knot of a digest-pinned crevice transport-composition campaign, replace only the caller-selected linear mass-action constraint targets with the corresponding caller-declared component sums of that cell concentration converted from mol/m3 to mol/L, preserve every unselected target, and execute the supplied fixed-activity single-liquid mass-action solver. Keep the activity coefficients, reaction network, equilibrium constants, temperature and phase scope caller supplied. Preserve complete-knot prefixes and cell/result lineage. This is an independent local operator-split equilibrium projection; it does not feed results back to transport, interpolate time, discover phases, or infer corrosion or qualification.",
    "caller_crevice_local_external_activity_projection": "For each exact digest-bound transport cell, derive only the explicitly selected mass-action constraint targets from the caller-declared component basis, then solve that cell's liquid mass-action state with a caller-injected, evidence-bound molality activity provider using the existing damped activity fixed-point solver. Bind provider identity, revision, configuration and parameter digests; preserve the exact converged inner mass-action input digest, provider transcript and complete-knot prefix. Reaction topology, equilibrium constants, temperature support, solvent conversion and single-ion convention remain caller declared. The independent cell solves do not create phase transitions, inter-knot kinetics, transport feedback, a qualified aqueous activity model or corrosion rate.",
    "caller_external_activity_crevice_cell_saturation_handoff": "Bind one exact knot from a computed external-activity crevice projection to caller-selected candidate-solid saturation screens. Recompute and verify each cell context digest, require the exact provider/configuration/parameter lineage, and form dimensionless molarity-standard-state activities from the projected gamma coefficient and concentration before invoking the existing saturation calculation. Require caller Evidence and temperature/standard-state/candidate reviews. Preserve successful cell prefix and upstream result digests. Do not select phases, predict precipitation, mix spatial cells, infer kinetics, corrosion, or qualification.",
    "caller_gasket_leakage_rate_threshold": "Compare a computed digest-pinned caller-calibrated gasket leakage history with caller-provided lower and optional upper rate thresholds, preserving threshold provenance, Evidence, computational-use rights, units, context and reconstruction review. Locate threshold excursions only for the supplied piecewise-linear rate path and report finite time intervals/censoring; this is a conditional event summary, not seal acceptance, failure probability or qualification.",
    "caller_corrosion_fta_event_probability_binding": "Bind a computed finite caller-reviewed corrosion thickness history and its required-thickness condition to an existing fault-tree basic-event contract only when the caller separately supplies the event probability, semantics, conditioning, common scope, Evidence and rights boundary. Preserve both request/result digests and asset/location/clock/horizon identity; never derive or infer probability from deterministic metal loss or crossing, evaluate the fault tree, or establish event validity.",
    "caller_crevice_faradaic_fta_probability_binding": "Bind only an exact-digest computed Crevice Faradaic Calculation with every adjacent requested clock interval committed. Carry the caller request's asset, location, physical scope, clock and horizon; require caller-supplied probability semantics, conditioning, probability scope, probability Evidence, calculation Evidence pinned to the whole result, and rights boundary. Never infer probability from current or reaction extents, evaluate the tree, or qualify the event.",
    "caller_explosive_weld_workbook_column_mapping": "Require a caller-reviewed worksheet, exact raw header values, selected row span, and explicit field IDs, meanings, unit tokens, roles and mapping Evidence before extracting selected source cells. Preserve raw values, formula text, cell types, coordinates and both source/mapping digests. Do not infer units or column meanings, evaluate formulas, fit fatigue relations, compute allowables or claim qualification.",
    "caller_layered_scale_history_series_transport": "Bind one distinct digest-pinned caller-calibrated single-phase scale-thickness history to each explicitly named diffusion layer, require identical exact time knots and common physical scope, and evaluate the existing steady layered diffusion bound independently at those knots. Preserve mapping reviews, history digests and failure prefix. Do not interpolate time, solve transient transport or scale reaction, infer corrosion/wall loss, or establish qualification.",
    "caller_scale_diffusion_metal_loss_bound": "Translate one computed digest-pinned layered-scale steady molar-flux ceiling through a caller-reviewed complete set of productive reaction stoichiometries to dissolved-metal atom flux, then use one Evidence-pinned molar mass and density to report conditional uniform penetration-rate and finite-duration loss ceilings. Require exact physical scope, surface-area basis, source identity, branch completeness, sustained-bound applicability and no other metal-loss path. This is not an actual current or corrosion-rate prediction, and it does not infer localization, life, acceptance or qualification.",
    "caller_aqueous_mass_action_finite_scenario_envelope": "Solve each complete caller-supplied fixed-topology aqueous mass-action system independently and report unweighted extrema over exactly the finite declared cases. Require exact species/reaction/constraint topology, solution and standard-state identity, and comparable provider-family revisions; preserve every successful case in order and withhold a complete envelope when any case fails. No sampling, weighting, interpolation, probability, confidence, global bound, phase selection, kinetics, corrosion or qualification is inferred.",
    "caller_aqueous_mass_action_topology_envelope": "Solve each of 2 to 64 complete caller-supplied alternative aqueous reaction networks at fixed solution identity, temperature, species inventory, fixed activities, standard state, balance constraints and comparable provider revisions. Report unweighted activity/concentration extrema over exactly those distinct alternatives; preserve successful prefix and first failure, withholding a complete envelope if any case does not compute. Do not generate or select networks, assign probability, or infer phase behavior, kinetics, corrosion or qualification.",
    "caller_scale_precipitation_inventory_budget": "Reconcile gross precipitated scale-formula moles from one computed, digest-pinned caller scale-thickness history against caller-supplied initial and ordered interval additions for each limiting aqueous species. Require Evidence, matching interval IDs, exposed area, explicit formula stoichiometry and accessibility reviews; stop before the first interval whose gross demand exceeds the declared stock. Do not credit dissolution as reactant supply, infer speciation/equilibrium/transport, alter the upstream history, or claim corrosion rate, wall loss or qualification.",
    "zenodo_galvanized_polarization_typed_rows": "Read only the three catalogued CC BY 4.0 galvanized-steel polarization workbooks with their declared byte counts and Zenodo MD5s; calculate local SHA-256 pins and preserve parser source row, sample order, specimen/electrolyte, caller attribution and authorization digest. Retain signed current in provider A/cm2 and the existing parser's A/m2 view, while the potential reference remains unresolved. Do not choose Tafel regions, compensate resistance, infer corrosion current/rate, rank specimens, or decide acceptance.",
    "caller_electrochemical_metal_loss_wall_flux_schedule": "Translate a complete digest-pinned electrochemical metal-loss assessment into contiguous interval anodic-metal flux densities using the common reviewed exposure area, elapsed-time origin and caller-reviewed uniform cell mapping. Preserve reaction/species identity and exact support. The upstream global ledger need not be conserved under moving geometry; no electrochemical feedback, local distribution or wall-loss law is inferred.",
    "caller_wco2_species_transfer_audit": "Audit caller-declared mappings from one WCO2 workflow stage to the next, checking exact species coverage, reviewed upstream exclusions, and element/formal-charge closure for each identity, renamed or stoichiometric transfer rule. Preserve rule and composition digests plus Evidence. This bookkeeping does not infer a reaction mechanism, thermodynamic conversion, kinetics, transport or corrosion.",
    "caller_multiaxial_cycle_block_result_summary": "Join an exact digest-pinned ordered cycle exchange receipt, bound stateful damage request and computed or accepted-prefix result. Verify provider, result, request, receipt and block order lineage before grouping existing cycle-ledger entries by source block. Preserve incomplete prefixes; do not recalculate or physically validate the fatigue model.",
    "caller_ti12mo5zr_eis_phase_convention": "Apply only the caller-selected sign mapping between provider-reported phase degrees and the imaginary impedance component, bound by evidence and a canonical phase-convention record. Preserve measured magnitude, frequency, scan time, source ordering and row digests. Do not infer instrument convention, exposure clock, area normalization, circuit parameters, corrosion resistance or material ranking.",
    "caller_multiaxial_cycle_block_feature_handoff": "Resolve caller-provided closed tensor cycles on explicitly oriented finite planes, extract declared stress and strain descriptors, and digest-bind selected unit-bearing features to adaptive integer-cycle parameter blocks. No fatigue law, damage, life or material-state law is inferred.",
    "caller_external_flange_diagnostic_screen": "Compare digest-pinned provider-reported FE diagnostics with caller-defined, evidence-backed limits after exact metric/category/definition/unit matching and review of uncertainty comparability. A result is a diagnostic screen only; it is not structural solver qualification, physical acceptance or seal qualification.",
    "caller_gasket_contact_pressure_time_window_event_audit": "For one selected node, extract mean pressure from exact computed gasket-contact history knots and locate caller-window crossings by reviewed piecewise-linear interpolation. Preserve upstream digests and context, with criterion and rights evidence. Do not infer sealing acceptance, leakage, failure cause or probability.",
    "caller_wet_co2_simulation_matched_contrast": "Compare two digest-pinned provider simulation rows that share exact dataset/source identity and differ only in one declared input. After caller pairing and output-scope review, calculate a finite difference, positive-response ratio and log-log secant elasticity where defined. These are contrasts between simulated outputs, not experimental sensitivities, causal effects, corrosion forecasts or failure probabilities.",
    "caller_aqueous_saturation_history_event_audit": "Audit caller-provided exact time and temperature knots for threshold crossings and positive-duration events using the declared interpolation policy. Preserve source and parameter digests, distinguish left/right censoring, and report only deterministic history features. The adapter does not solve aqueous chemistry or infer equilibrium constants, kinetics, corrosion, risk or acceptance.",
    "caller-baseline-thickness-evidence": "Use a traceable caller-provided baseline thickness measurement for the declared asset, location, material condition, method, date and uncertainty. No baseline value or acceptance criterion is bundled or inferred.",
    "caller-density-evidence": "Use only caller-supplied traceable density evidence applicable to the exact material/product condition and temperature range. No density value or empirical table is bundled.",
    "caller_ti12mo5zr_ocp_window_summary": "Summarize caller-selected finite windows from one exact digest-pinned Ti-12Mo-5Zr open-circuit-potential monitor member. Preserve source rows, ordering, potential-reference evidence and interpolation review; calculate signed change, time average, integral and extrema only within provider support. No extrapolation, corrosion rate, polarization resistance, alloy ranking or acceptance is inferred.",
    "caller_spatial_piecewise_mass_action": "Construct a spatial transport source callback from a caller-calibrated finite mass-action network with fixed stoichiometry and contiguous piecewise-constant rate tables. Check units, charge and optional elemental closure, calibration/rights evidence, provider pins and exact time support. Do not infer kinetics, equilibrium, activities, corrosion or surface laws.",
    "caller_crevice_aqueous_kinetic_network": "Integrate a caller-declared finite reversible mass-action network in a constant-volume, well-mixed liquid with piecewise-constant bulk exchange and rate coefficients. Validate element and charge conservation before solving; evolve concentrations, exchange inventory and reaction extents in one stiff implicit BDF or Radau integration per interval. Commit only completed intervals and retain conservation residuals. Rate-law units and parameter meaning remain caller responsibilities; no activity/speciation equilibrium, phase change, transport, wall loss or qualification is supplied.",
    "ince_glinka_generalized_strain_amplitude": "For each caller-listed material plane, resolve the supplied closed-cycle symmetric stress and elastic/plastic strain tensors into normal and engineering shear histories. Combine the maximum resolved normal and absolute shear stresses with elastic and plastic strain amplitudes using caller fatigue-strength coefficients, then select the maximum over the finite plane list. This evaluates one supplied cycle and finite plane set only; cycle counting, life conversion, unsampled-path reconstruction, continuous plane optimization and material qualification are not inferred.",
    "zenodo_mg_deis_archive_structure": "Pin the caller-local archive to the versioned Zenodo CC0 record by archive SHA-256 and byte count; verify the exact member inventory, CRC, two tabular matrix member hashes, dimensions and finite numeric cell coverage. Preserve row order while leaving axes, units, spectrum partitioning and material interpretation unresolved. The importer exposes rows only from the ignored local cache and publishes no point values or provider files.",
    "zenodo-ti12mo5hf-oxygen-corrosion": "Bind a read-only local archive audit to the Zenodo CC0 dataset record by its publisher-declared byte count and MD5 plus a caller-supplied SHA-256. Return only a bounded ZIP member inventory and provider-described alloy/environment/program metadata; do not extract assets, interpret workbook columns, reconstruct corrosion histories, or infer qualification.",
    "zenodo-ti12mo5zr-aqueous-corrosion": "Read only explicitly allowlisted, SHA-256-pinned OCP, EIS and AESEC workbook members from the provider-declared CC0 archive after explicit local-use authorization. Preserve source headers, row order, missing cells, member/archive digests and provider units without coordinate alignment, unit conversion, segment inference, fitting or corrosion-rate recalculation. Other archive assets remain outside this reader.",
    "caller_external_aqueous_activity_provider": "Accept caller-computed composition-dependent molality-standard-state activity coefficients from an external Python callback and couple them to the existing molarity-standard-state mass-action solver with bounded damped fixed-point iteration. Bind each provider request to the exact temperature, ordered species/charges, molality vector, ionic strength and water-mass basis; require provider identity/revision, configuration and parameter digests, exact species coverage/order, echoed request digest, declared single-ion convention, ionic-strength agreement, evidence and explicit applicability reviews. Convert gamma_m to gamma_c=gamma_m/w for the 1 mol/L mass-action basis. The same provider boundary can supply molality gamma values to a restricted-transport callback at each mouth/cell state using the caller-declared fixed solvent-mass basis. The project imports and bundles no thermodynamic provider, parameter table or license-restricted implementation; the adapter does not qualify provider equations, parameter coverage, local equilibrium or solution chemistry.",
    "caller_external_aqueous_activity_speciation_history": "At every explicitly supplied increasing time knot, solve one independently parameterized mass-action system with the same caller-owned composition-dependent activity provider identity, revision, configuration and single-ion convention. Require a fixed species/formula/reaction/constraint topology, exact time-temperature mapping, explicit knot-specific parameter records, complete provider convergence and caller reviews. Retain per-knot request/result digest and only report computed when all knots succeed; otherwise return a failed knot and prior prefix. No interpolation, kinetic model, provider implementation, phase selection or corrosion qualification is inferred.",
    "molality_to_molarity_activity_standard_state_bridge": "Map a molality-standard-state coefficient to a molarity-standard-state coefficient by equating the same dimensionless activity: gamma_c*c/(1 mol/L) = gamma_m*m/(1 mol/kg-water), with m=c/w and caller-supplied w in kg-water/L-solution, giving gamma_c=gamma_m/w. Require review of the water-mass conversion and standard-state mapping, preserve both coefficients, and fail closed outside finite numeric range. This algebraic basis does not infer solution water content or validate an activity model.",
    "caller_vant_hoff_aqueous_mass_action_history": "For each caller-declared temperature knot, integrate the van't Hoff relation using caller-supplied reference log10(K) and reaction enthalpy, optionally with constant or linearly temperature-dependent caller-supplied reaction heat-capacity change over an explicit validity interval. Re-solve the existing single-phase aqueous mass-action system independently at every knot, preserving reaction stoichiometry and balance constraints. Require exact reaction-record coverage, Evidence/source-record lineage, thermochemistry-model and time/temperature reviews, and bounded log10(K). Either consume complete caller-supplied per-knot activity coefficients in exact species order with consistent provider ID/revision/configuration digest and their own evidence/review, or retain reference coefficients only after an explicit fixed-gamma applicability review. Do not infer enthalpy, heat capacity or activity data, extrapolate, discover phases, calculate precipitation or infer corrosion kinetics.",
    "aqueous_mass_action_reaction_cycle_audit_adapter": "Reuse the exact caller-defined aqueous mass-action species, formulas, charges, reaction terms, log10(K), temperature and activity standard state. Require reaction-by-reaction source-record IDs and file hashes that resolve to the system Evidence bundle, then pass the bound network to the independent stoichiometric cycle-consistency audit. Do not transform reaction direction, infer missing formulae or discover phases.",
    "aqueous_reaction_cycle_nullspace_consistency": "Construct the caller-declared species-by-reaction stoichiometric matrix after checking elemental and charge balance. An orthonormal right-null-space basis identifies linear reaction cycles; equilibrium constants are algebraically consistent on that declared cycle space when the L2 norm of the basis projection of log10(K) is within a caller-reviewed tolerance. Numerical rank tolerance and the supplied species, reactions and conditions remain caller responsibilities. No reaction or phase discovery, speciation solve, or parameter qualification is performed.",
    "erosion_corrosion_wall_limit_state_link": "At each complete contiguous erosion-corrosion interval, subtract cumulative caller-supplied combined thickness loss from a digest-linked measured wall thickness and then compare with the caller-required minimum thickness. When complete deterministic loss endpoints exist, propagate the margin by reversing the cumulative loss bounds and report the earliest possible/definite crossing only as an observed interval bracket. Require asset/location/physical-scope/material/geometry identity and exact baseline-clock continuity. Report a deterministic threshold relation only; do not interpolate a crossing root or infer failure probability, inspection reliability, code acceptance or remaining life.",
    "caller_erosion_corrosion_component_accounting": "For strictly matched caller-supplied thickness-loss rates, define signed residual synergy as the combined erosion-corrosion rate minus the independently supplied pure erosion and pure corrosion rates. When a corrosion rate measured during erosion is also supplied, derive the concurrent erosion contribution by subtraction from the total and retain both signed changes relative to the pure baselines. Optional caller-reviewed lower/upper rate endpoints propagate by interval arithmetic without a statistical interpretation. Integrate each piecewise-constant rate only over its explicitly recorded interval. Do not infer an interaction mechanism, clamp negative values, extrapolate, or qualify the material.",
    "caller_gamma_corrected_effective_concentration_kinetics": "For a caller-calibrated concentration-basis homogeneous mass-action network, optionally multiply each local species concentration by the matching caller-supplied activity coefficient before evaluating the unchanged forward and reverse concentration-rate expressions. Require an explicit review gate and the exact pinned transport activity provider identity/configuration. Preserve the original rate-constant units and calibration. This effective-concentration correction is not a standard-state transformation, equilibrium solver, automatic kinetic law, or validation of the activity model or rate coefficients.",
    "caller_findley_reference_strength_calibration": "Evaluate the finite-sample critical-plane parameter as the sampled shear-traction amplitude plus a caller-calibrated coefficient times the maximum sampled normal stress. The amplitude is explicitly one half of the maximum pairwise chord among supplied two-component in-plane shear tractions. Evaluate only caller-supplied plane orientations and compare against a caller-supplied parameter strength at one stated reference life. This deterministic screening calculation does not infer fatigue life, acceptance criteria, probability, material qualification, unsampled times or unsupplied plane orientations.",
    "caller_findley_parameter_life_curve": "Evaluate the existing finite-sample critical-plane Findley parameter for the caller-supplied stress history and interpolate cycles to failure only within a caller-provided, digest-bound, strictly monotone parameter/life curve. The method is piecewise linear in logarithmic parameter and logarithmic life, rejects extrapolation, and records material-condition, load-basis, curve-support, rights and authorization reviews. It does not infer a curve, transfer calibration, fatigue acceptance, probability, unsampled orientations or material qualification.",
    "caller_correlated_finite_multiaxial_life_scenario_envelope": "Evaluate only a finite caller-provided set of complete computed multiaxial critical-plane life campaign results. Require result/input-context digests, unique scenario IDs, matching registered campaign revision, calibration digest, material condition, valid cycle support and asset/location/time identity; preserve scenario source, calibration and plane-factor digests. Report extrema and witnesses over the supplied scenarios only. Do not assign probabilities, confidence levels, continuous bounds, parameter-wise recombinations or extrapolated life.",
    "psa_dyna_public_mean_stream_contract": "Provide a versioned typed row/batch contract and explicit converter boundary for caller-exported PSA Dyna mean-stream composition records. Preserve column identity, unit basis and source row lineage; do not import or reproduce the external simulator, infer missing mixture inputs, or claim fugacity validation.",
    "caller_constant_state_gasket_leakage_scenario_exposure": "Multiply every rate in a digest-pinned computed finite correlated gasket leakage scenario envelope by an explicitly caller-reviewed constant-state duration. Preserve source assessment/input/context/scenario digests, snapshot time and run-context asset/location/time basis; report finite-scenario molar exposure extrema and witnesses only. Do not infer pressure/contact/calibration evolution, scenario probability, continuous bounds or seal acceptance.",
    "caller_finite_gasket_joint_scenario_dependence": "Compute weighted centered cross-covariances and correlations from the same complete digest-bound finite gasket scenarios and caller-declared normalized weights. Include common differential pressure, total contact area and total leakage, plus selected node pressure, area and leakage contribution with explicit per-variable units. Preserve scenario and weight lineage; constant-column correlation is undefined. These are descriptive moments of the declared finite set, not a population estimator, distribution, confidence interval, causal effect, continuous bound or seal acceptance.",
    "caller_piecewise_linear_gasket_leakage_scenario_rate_interval": "Integrate matched scenario-specific nonnegative gasket leakage rates between two digest-pinned computed endpoint envelopes using the exact trapezoid integral for an explicitly caller-reviewed piecewise-linear-in-time rate reconstruction. Require identical joint/scope, scenario provider identity and IDs, calibration provider/revision/record/map, license, node order and asset/location/clock context; require matching per-scenario calibration-flux realization digests. Preserve endpoint result/input/scenario-row digests and scenario witnesses. Do not infer pressure, contact, relaxation, calibration evolution, event probability or unsampled transient extrema.",
    "caller_composed_aqueous_candidate_network_workflow": "Compose a bounded candidate stoichiometry enumeration, manual evidence-backed selection/direction/equilibrium-constant binding and strict aqueous mass-action system assembly. Pin every stage digest and require identical species formula/charge, temperature and activity standard state across the workflow. This assembles but does not solve chemistry, discover species or phases, infer feasibility/kinetics, or qualify corrosion.",
    "caller_composed_aqueous_candidate_network_speciation": "Consume only the mass-action system emitted by a computed digest-pinned caller candidate-network workflow. Verify workflow AssessmentResult input/context/result digest, assembly and system digests, temperature and activity standard state, then call the existing fixed-gamma aqueous mass-action speciation solver. Preserve workflow, enumeration, binding, assembly and solve lineage. Do not discover reactions/phases, infer constants/activity data, precipitation, kinetics, corrosion or qualification.",
    "caller_reviewed_crevice_aperture_history_refinement": "Bounded recursive subdivision of a digest-pinned positive aperture history using caller-reviewed piecewise-linear interpolation only; preserve the source digest, limits and successful prefix, and do not recompute physical processes.",
    "caller_declared_wet_co2_elemental_phase_history_handoff": "Apply caller-declared elemental formula counts and cell solution volumes to already-computed aqueous and solid concentration histories; preserve source lineage and do not infer reaction extents, omitted pools, flux closure, kinetics or chemistry.",
    "electrochemical_partial_current_to_metal_loss": "Require a computed digest-pinned mixed-potential history and caller-reviewed metal-dissolution mapping for each selected reaction. Integrate each upstream reference-area current-density branch with the exact trapezoid integral under a declared piecewise-linear between-knot reconstruction. Divide charge by the upstream reaction electron number and Faraday constant, apply the caller metal-atom stoichiometric factor and evidence-linked molar mass, then divide signed mass change by caller density and actual mapped branch area for a uniform area-average recession. Report anodic and cathodic equivalents separately from signed net transfer. This implements Faraday charge-to-reaction accounting only; it does not validate current kinetics, alloy selectivity, completeness of selected dissolution reactions, local attack, evolving geometry or corrosion qualification.",
    "electrochemical_metal_loss_to_wall_thickness_history": "Require the computed digest-pinned electrochemical metal-loss AssessmentResult and a digest-linked measured wall-thickness baseline at the first interval start, matching asset, location, physical scope and material condition. Require complete reaction-set review and every selected branch area to agree with the caller's common assessed wall area within an explicit tolerance. Sum gross anodic mass across the selected reactions, divide by evidence-linked caller effective density and reviewed wall area, and subtract each interval increment from the baseline thickness. Cathodic equivalents and signed net mass do not offset wall loss. Report deterministic thickness margins over supplied intervals and a first-crossing interval bracket only; do not interpolate within-interval time, extrapolate corrosion, predict life, decide acceptance or assign probability.",
    "electrochemical_metal_loss_wall_thickness_finite_scenario_envelope": "Require a finite ordered manifest of computed digest-pinned electrochemical wall-thickness AssessmentResults. Enforce matching asset/location/time basis, physical and material scope, measured baseline identity/digest, required-thickness history and exact ordered time knots. Report per-knot minima/maxima of remaining thickness and limit-state margin with separate scenario witnesses, retaining every scenario result/input/projection digest. The extrema apply only to the complete caller-supplied finite scenario set; no scenario weights, probabilities, interpolation, continuous bound, first-passage event, remaining-life forecast or acceptance decision is inferred.",
    "electrochemical_metal_loss_to_crevice_geometry": "Require the computed digest-pinned metal-loss AssessmentResult and caller-declared slit geometry. Convert each reaction cumulative signed mass ledger to signed transferred volume using its evidence-linked caller density, distribute that volume over cells using caller-supplied cumulative per-reaction fractions at every exact time knot, and enforce unit fraction sums plus total signed-volume closure. Map the first supplied source time to elapsed geometry time zero; a nonzero source origin requires explicit review and the source-to-elapsed mapping is retained. Divide cell volume by the caller-declared combined reactive wall area and pass the resulting cellwise recession history to the existing sequential aperture remap. Require explicit reaction-to-face, cell allocation, volume conservation, area basis, cell mapping, geometry basis, equal-face (for two-face geometry) and computational-use reviews. No local current distribution, wall-reaction allocation, moving-boundary transport or physical validation is inferred.",
    "external_crevice_solver_pressure_velocity_receipt": "Require a caller-normalized external solver record and its source digest, provider revision/run ID, mesh revision, coordinate-system identity, explicit SI units, mouth origin, mouth-to-tip positive direction, exact geometry/time mapping, cell/face field cardinalities and evidence. Bind every pressure/velocity knot to a digest-pinned aperture-history state and reject extrapolation, mismatched mesh dimensions or unreviewed face orientation. Expose reviewed piecewise-linear interpolation of face velocity as a callable for the existing restricted-transport consumer and preserve the provider/configuration digest. This is an exchange adapter, not a CFD solver or validation of its numerical method or accuracy.",
    "electrochemical_chemistry_state_boundary_audit": "Audit a caller-ordered chain of computed chemistry, speciation or transport results by exact result/input/context digests and caller-selected JSON result paths. Require exact asset/location/clock, time knots, temperature, material condition, solvent and activity standard-state agreement. Require a unique explicit Evidence-backed disposition for every source species at every adjacent stage boundary and verify that downstream-consumed IDs are covered by mapped targets. Preserve resolved state digests and source references. This is a provenance/state-boundary check; it does not discover species, convert standard states/units, balance reactions, solve chemistry or validate physics.",
    "caller_qualified_gasket_leakage_flux_calibration": "Use a joint- and condition-matched caller calibration table of local molar leakage flux versus measured or solver-derived mean contact pressure and differential pressure. Interpolate only within its declared rectangular support and integrate over a reviewed complete partition of contact areas. For interval totals, assume linearly reconstructed pressure paths, split at every crossed calibration-axis knot, then apply Simpson integration on each resulting at-most-quadratic segment, which is exact for the declared bilinear surface and reconstruction. Enforce the declared total integration subinterval budget and a two-million-cell maximum calibration table. Preserve calibration, pressure, transfer and area-partition reviews. No universal gasket law, leakage mechanism, between-knot contact evolution, seal acceptance limit or design qualification is provided.",
    "caller_scale_coverage_attachment_detachment_law": "For one caller-identified scale phase, integrate the first-order area-average coverage balance d(theta)/dt = a(1-theta)-b*theta with caller-selected attachment and detachment power laws. Use a closed-form update for interval-constant saturation; for caller-reviewed piecewise-linear saturation use bounded adaptive RK4 step doubling on coverage and separate attachment/detachment inventories with caller absolute/relative tolerances. Optionally scale both caller rate constants from a reference temperature with separate supplied activation energies using the Arrhenius relation, only when target/reference and every declared piecewise-constant interval temperature lie inside the absolute-temperature support and explicit applicability review is present. Interval temperatures require complete per-interval values and an explicit profile review; no temperature interpolation occurs between intervals. Record effective temperature-specific rates, inventory closure and integration diagnostics. No nucleation, morphology, porosity, adhesion, transport protection or corrosion law is inferred.",
    "caller_aqueous_saturation_to_surface_scale_kinetics": "Consume a computed, digest-pinned aqueous van't Hoff saturation-history AssessmentResult and transfer one caller-selected candidate solid log10 saturation ratio at every exact time knot into the adjacent intervals of an explicit caller surface-scale thickness kinetics request. Recompute and verify registry input/result digests, the embedded computed van't Hoff history result and input digest, exact equilibrium source-knot result digests, knot clocks and temperatures, each nested saturation-screen upstream result and solubility-record digest, a unique matching solid at every knot, exact interval endpoint equality and finite log-ratio transfer range. Varying temperatures require the declared kinetic temperature to match the first history knot, explicit knot-to-interval review and caller Arrhenius parameters within their declared support; each kinetic interval holds the corresponding left-knot temperature constant while saturation uses its reviewed endpoint path. Preserve source history and per-knot screen digests, then delegate thickness and optional coverage evolution to existing caller-calibrated single-phase models. Require matching phase/specimen/condition identities; coverage accepts varying knot temperatures only with explicit knot mapping, per-interval constant temperature interpretation and supported caller Arrhenius parameters. The two laws are not coupled through evolving thickness, transport or corrosion. Do not infer candidate phase selection, precipitation/dissolution coefficients, chemistry-derived kinetics, morphology, corrosion protection or qualification.",
    "caller_aqueous_candidate_saturation_screen": "For each explicitly declared candidate solid, calculate the logarithmic ion-activity product from caller-supplied dimensionless aqueous activities and positive exponents, then subtract the caller-supplied temperature-applicable log10 solubility product. Require a row-level solubility record ID and a matching Evidence source ID per candidate, and carry citation, license and checksum into each result. A Python composition adapter accepts computed fixed-gamma, Davies, B-dot, or tabulated-activity aqueous Calculation results or registered AssessmentResults, checks supported model identity for the latter, carries the complete upstream digest plus activity provider/record lineage, and rejects noncomputed or untraceable states. It also accepts a digest-pinned candidate-network speciation AssessmentResult by verifying wrapper input digest, embedded workflow result and input digests, assembled mass-action system digest, and nested speciation result digest before forwarding its activity state and retaining workflow/system/speciation lineage. It accepts a registered exact-knot B-dot history only with an explicit knot index, verifies full assessment/input/history/knot/request/result and parameter-record digests, and preserves selected time, temperature and parameter lineage in the saturation result. Callers may add absolute log10 activity bounds keyed by the exact upstream species ID set; partial or extra mappings return needs_data rather than silently dropping bounds. Propagate caller-supplied absolute log10 bounds for species activities and each solubility product by conservative interval arithmetic, reporting lower/upper saturation-index bounds and whether the interval lies wholly below, wholly above, or overlaps saturation. Nonzero activity and solubility bounds require separate caller review flags; otherwise the calculation returns needs_data without an interval classification. These deterministic intervals are not probabilities or confidence bounds. Return ordered candidate results with activity-state and solubility-data digests. The time-history adapter additionally requires an exact computed van't Hoff history digest, aligned Ksp records at every knot, matching candidate definitions and explicit per-record temperature support; it does not interpolate between knots. Do not choose stable phases, solve competing-solid mass balance, infer precipitation amount or kinetics, or predict corrosion.",
    "caller_general_aqueous_mass_action_speciation": "Solve a caller-defined square single-phase aqueous network in natural-log dimensionless activities. Use caller-supplied fixed activity coefficients and temperature-matched log10 equilibrium constants; solve caller-provided linear species amount and/or charge constraints after normalization by declared positive scales. A damped Newton method with finite-range checks and line search returns species activities, concentrations, balance closure, reaction residuals and full input/provider digests only within the declared tolerance. At a computed root, solve the converged Jacobian for implicit local derivatives of log activities and concentrations with respect to each log10(K), constraint target and fixed ln(gamma), without finite differencing. If explicitly reviewed, propagate a finite symmetric positive-semidefinite caller parameter covariance through those derivatives using first-order JΣJᵀ; condition and finite checks can make sensitivities unavailable while preserving the equilibrium result. No automatic electroneutrality, ionic-strength iteration, water balance, gas/solid phase, precipitation, kinetics, corrosion, or acceptance is inferred.",
    "caller_element_charge_balanced_aqueous_reaction_candidate_enumeration": "Enumerate primitive integer stoichiometric candidates from a caller-declared closed species list, complete elemental formulas and ionic charges within explicit total-order, side-multiset, candidate-pair and output budgets. Candidates conserve the supplied atom counts and charge; deterministic digest-derived candidate IDs, review gates and input digest are retained. This is a bounded balance screen, not chemical reaction discovery, phase selection, equilibrium-constant assignment, kinetics, network completeness or corrosion prediction.",
    "caller_aqueous_candidate_reaction_binding": "Bind manually selected, digest-verified atom/charge-balanced candidate stoichiometries to caller-supplied signed mass-action equilibrium constants and temperature-specific source records. Verify candidate identities, preserve candidate and parameter lineage, and reverse signs and log10(K) only when the caller explicitly selects the reverse direction. Do not infer chemical feasibility, reaction selection, direction, constants, temperature transferability, activity conventions or kinetics.",
    "caller_aqueous_mass_action_system_assembly": "Assemble a strict square single-liquid mass-action system from caller-provided aqueous species, activity provider lineage and analytical/charge constraints plus an already computed candidate-binding result. Require exact target activity standard state and temperature agreement, parse each reaction into the registered reaction contract, preserve ordered parameter lineage in an aggregate record digest, and reject equation-count or conservation-contract failures before returning solver inputs. Do not execute equilibrium calculation, infer chemical feasibility or qualify parameters.",
    "caller_single_salt_pitzer_mean_activity": "Calculate Pitzer-Debye-Huckel plus caller beta0/beta1/beta2 and Cphi virial contributions to the mean ionic activity coefficient and osmotic coefficient for one electroneutral pure electrolyte. The caller supplies molality-scale coefficients, temperature/ionic-strength support and rights evidence. It assigns no individual-ion gamma convention and omits mixed-salt theta/psi interactions, fitting, phase equilibrium, corrosion kinetics and qualification.",
    "zenodo_ti6al4v_cathodic_polarization_csv_import": "Import the selected CC0 Zenodo Ti-6Al-4V Fig1 CSV by an expected SHA-256, explicit medium and source-condition review. Preserve source row identities, reverse a whole monotone descending branch only when required by the increasing-potential contract, reject nonmonotone scans, convert provider microampere/cm2 current densities to A/m2, and keep electrochemical net current separate from ICP-AES-derived Ti dissolution current. Do not infer sign convention, exposed area, metal loss, specimen independence, or transferability.",
    "caller_tabulated_aqueous_activity_coefficients": "Iterate a caller-defined single-liquid mass-action network with species-specific activity-coefficient tables indexed by molal ionic strength. Recalculate ionic strength from caller water-mass conversion and solved concentrations, interpolate ln(gamma) using caller-selected piecewise linear or explicitly reviewed shape-preserving PCHIP only inside each caller table support, and damp updates in log space. Require measured/open dataset knots to map both source_id and source_record_id to declared licensed Evidence. Preserve separate normalized-table, row-lineage, Evidence, provider and configuration digests through speciation and transport callbacks, together with charge/reaction closure, fixed-point history and explicit temperature/solvent/species mapping review. This is a user-supplied table evaluator, not a qualified electrolyte law; no extrapolation, table fitting, phase change, precipitation, scale protection or corrosion rate is inferred.",
    "self_consistent_davies_aqueous_speciation": "Compose the caller-defined square single-liquid mass-action solver with a damped outer fixed-point iteration. Convert computed molar concentrations to molality using explicit caller-supplied kilograms of water per litre of solution, calculate ionic strength from the complete charged inventory, and recalculate Davies coefficients from a caller-evidenced temperature-specific A value. Require explicit charge tolerance, a Davies ionic-strength ceiling no greater than 0.5 mol/kg water, convergence tolerance and iteration budget. Preserve inner solver diagnostics and input/provider digests; do not add species or equations, infer water content, substitute Pitzer/SIT, model other phases, kinetics, scale, corrosion or acceptance.",
    "caller_surface_scale_kinetic_balance": "Integrate caller-calibrated precipitation and dissolution molar flux laws for one identified scale phase over ordered intervals with either constant saturation or explicitly reviewed linear saturation endpoints. Analytically integrate positive-part power laws max(Ω−1,0)^n and max(1−Ω,0)^n across the threshold Ω=1. Bound dissolution by the existing uniform scale inventory; for a descending supersaturated-to-undersaturated interval, generated precipitate may dissolve after the crossing, whereas an ascending path cannot spend future precipitation. Convert cumulative net molar amount per area to thickness using caller molar volume. Optionally scale both rate constants from a reference temperature with separate activation energies inside explicitly reviewed absolute-temperature support. Preserve physical scope, specimen/source/condition/provider/configuration digests and every interval balance. Do not solve saturation chemistry, phase competition, nucleation, morphology, transport, scale protection, corrosion rate, life or acceptance.",
    "caller_gasket_leakage_pressure_envelope": "Bound the area-weighted instantaneous gasket leakage rate for caller-declared independent contact-pressure and differential-pressure intervals at every contact node under one fixed caller calibration table. Partition each rectangular uncertainty region at all crossed table knots; within each subcell the bilinear flux has no strict interior extrema, and its boundary restrictions are linear, so all exact extrema occur among the subcell corners. Preserve a witness pressure pair for each node bound and sum nodewise area-weighted extrema. Do not interpret interval bounds as a probability distribution, assume pressure correlations, include calibration/area uncertainty, extrapolate, integrate over time or infer seal acceptance.",
    "caller_layered_scale_diffusion_limit": "Calculate steady series diffusion resistance across caller-defined scale layers and a bare solution film, then mix covered and uncovered patch fluxes in parallel using a caller-reviewed area fraction. Convert transported-species flux to its electron-equivalent Faraday current bound. Preserve species, condition, layer order and provider digests. This does not determine layer morphology or coverage, solve charge balance or electrode kinetics, infer a corrosion current or claim an actual protection factor.",
    "caller_planar_scale_diffusion_reaction_balance": "Advance a caller-defined planar scale thickness over contiguous time intervals by balancing diffusion-limited reactant supply against a declared interfacial reaction demand. The supplied transport path includes the solution film, scale diffusivity and an optional interface resistance; the moving-boundary update is piecewise constant and stops at complete scale depletion when dissolution exceeds supply. Preserve units, species, interval order, parameter provenance and mass-balance diagnostics. This reduced model does not identify scale phases, derive kinetic parameters, resolve spatial concentration fields or establish field applicability.",
    "caller_planar_scale_reaction_demand_balance": "Advance a single dense planar scale with a monotone scalar moving-boundary balance between series-resistance diffusion supply and caller-specified interfacial consumption over ordered constant-parameter intervals. Accept either a nonnegative scale consumption flux or a sign-reviewed partial current with explicit Faraday and solid stoichiometry mapping; stop at complete scale depletion and report area-based supply, consumption, transported-reactant and net-scale ledgers with provider and evidence lineage. Do not derive demand from net current, infer chemistry or substrate attack, or solve potential feedback, porosity, finite reservoirs, phase competition or qualification.",
    "caller_gasket_leakage_surface_fit": "Fit a nonnegative bilinear gasket leakage surface from caller-provided pressure-pair observations using weighted least squares, with calibration and holdout rows kept distinct. Report parameter support, rank diagnostics, residuals and fit provenance; require evidence and reuse rights to accompany observations. The fitted surface is an empirical caller calibration and does not establish a universal gasket law, extrapolation validity, seal acceptance or qualification.",
    "layered_scale_history_transport_binding": "Bind one exact recorded knot from a computed single-phase caller scale-kinetics AssessmentResult to one explicitly selected caller transport layer. Require matching physical scope, substrate/solution condition and phase identities, a unique layer ID and a separate mapping review. Replace only that layer thickness and retain full scale-result digest/time/phase/layer lineage. Do not interpolate time or infer coverage, diffusivity, partitioning or a multilayer structure.",
    "layered_scale_history_stack_assembly": "For an ordered caller-defined layered scale transport request, bind each layer to a distinct computed, digest-verified single-phase caller scale-kinetics result at one exact common output time. Require a complete one-to-one layer mapping, matching physical/substrate/solution and asset/location/time-basis scope, and explicit mapping and use reviews. Substitute only the selected layer thicknesses and delegate the diffusion bound to the existing layered transport model. Do not infer phases, co-precipitation, time interpolation, kinetics, diffusivity or qualification.",
    "caller_gasket_contact_pressure_screen_window": "Compare an explicitly declared static or exact-knot spatial gasket contact pressure field in pascals with caller-provided minimum and optional maximum pressure screening bounds. Pin the full upstream result and criterion record digests, require matching asset/location/physical scope, exact node selection, Evidence/rights and applicability reviews, and report per-node margins and the controlling screening margin. This does not establish a seal criterion, acceptance, leakage performance, probability or qualification.",
    "caller_lumped_crevice_exchange_first_order_reaction": "Propagate one caller-declared dissolved species in a fixed-volume, well-mixed control volume under nonnegative piecewise-constant bulk concentration, exchange flow and first-order sink coefficient. Use exact closed-form state updates and analytic interval integrals to report concentration, exchange, sink and inventory ledgers with closure residuals. Require ordered time inputs, aligned intervals, provider Evidence, use rights and physical/unit reviews. This does not represent spatial gradients, electro-migration, multicomponent speciation, precipitation, calibrated kinetics or wall loss.",
    "caller_lumped_slit_inertance_resistance": "Evaluate the caller-reviewed reduced planar-slit momentum law with the declared resistance and inertance correction factors; factors default to unity and non-unity values require exact fit-result Evidence and an applicability review.",
    "caller_reviewed_dynamic_slit_pressure_and_boundary_composition_schedule": "Bind a reviewed, digest-fixed pressure-drop and electroneutral reservoir-composition history to a moving-volume slit-transport calculation. The reduced Newtonian laminar slit model uses caller-declared fluid properties, correction factors and support limits; directional volume-rate estimation and physical validation remain explicit limitations.",
    "caller_reviewed_dynamic_slit_pressure_and_boundary_composition_schedule": "Bind a reviewed, digest-fixed pressure-drop and electroneutral reservoir-composition history to a moving-volume slit-transport calculation. The reduced Newtonian laminar slit model uses caller-declared fluid properties, correction factors and support limits; directional volume-rate estimation and physical validation remain explicit limitations.",
    "caller_crevice_laminar_wall_shear_exposure": "Bind one exact computed, digest-pinned planar-slit transient hydraulic AssessmentResult and derive each cell's fully developed wide-slit wall shear tau_w=6*mu*Q/(w*h^2). Use the hydraulic source's exponential first-order flow path to integrate signed shear impulse and exact absolute shear exposure, splitting at each reported internal flow reversal. Preserve hydraulic result, geometry, pressure and fluid-property provider digests and identities. Require explicit wide-slit, profile and descriptor-only reviews. This quasi-steady shear descriptor does not solve a velocity field, local turbulence, erosion, corrosion, damage or qualification.",
    "caller_weighted_finite_multiaxial_life_scenario_moments": "Evaluate complete digest-pinned multiaxial fatigue life scenario results and compute weighted finite-set mean, population variance, standard deviation and extrema using one strictly positive explicit caller weight per ordered scenario. Optionally calculate caller-reviewed left-continuous weighted inverse-ECDF quantiles, exact lower-tail weighted means using fractional boundary-scenario mass, and weighted scenario mass at or below explicit cycle-life thresholds, with the number of matched scenarios; scenario identities remain available in the shared digest-pinned life table. Sort once and use cumulative weights plus binary search for bounded query cost. Bind the ordered weight vector to provider/revision/Evidence/rights, require sum-to-one without normalization, and retain life-result witnesses. Quantiles and threshold masses describe only the declared finite scenario set; threshold mass is not failure probability. Do not infer event probability, confidence, distribution tails, or a continuous life bound.",
    "scale_limited_electrochemical_surface_boundary": "Bind one or more digest-pinned computed layered-scale molar-flux bounds to complete caller-selected species-production branch sets at tip or wall boundaries. Evaluate each species cap against original partial currents; where caps share a productive branch, apply the most restrictive implied factor once. Preserve opposite partial-current branches and reconstruct net reaction extent and every stoichiometric species flux. Require unique boundary/species bindings and matching physical-scope, scale-state, surface-reference, area-basis and constant-state reviews. This is a fixed upper-bound limiter, not evolving scale coverage, direct diffusion-reaction coupling, corrosion qualification or acceptance.",
    "sequential_crevice_geometry_transport_campaign": "Run the conservative restricted-transport solver over a caller-pinned aperture history, with each interval held at its left-knot geometry and boundary callbacks translated to global campaign time. Require exact coincidence of geometry and transport clocks, a matching fixed reference area, and explicit review. At geometry knots, remap cell concentrations by cell-volume ratio to preserve per-cell species inventory. This is one-way operator splitting: transport does not generate or update the supplied recession history and no within-step moving geometry or momentum solution is inferred.",
    "sequential_transport_derived_crevice_recession_feedback": "Run restricted transport on consecutive fixed-geometry slit intervals, convert a selected caller-reviewed signed metal-species wall ledger to cell-average recession using declared metal molar mass, density, reactive-face area and cell widths, then update the next interval aperture and conservatively remap cell concentrations. Optionally reject and bisect an uncommitted segment when its maximum cellwise relative aperture change exceeds a caller limit; require reviewed linear-time subdivision, deterministic callback reevaluation, and segment/refinement budgets, then rerun both subsegments from the unchanged pretrial state. Optionally calculate steady planar-slit face velocities from caller pressure samples aligned to requested output times and reviewed fluid properties. A separate bounded within-segment fixed-point mode can iterate the reviewed linear aperture path against the signed metal ledger; only with additional review gates does it also use the public `PlanarSlitEndpointVelocityPath` contract to interpolate between start/end steady hydraulic face-velocity vectors computed at the current start and guessed end aperture/pressure. The path contract validates global interval, ordered face-grid shape, finite endpoints, review state and endpoint digests; its callback rejects local-time extrapolation. Record endpoint result digests, pressure interpolation lineage, velocity-path review and rejected/uncommitted trials. These options do not solve transient momentum, fully coupled flow/geometry/chemistry, inferred chemistry, corrosion qualification or acceptance.",
    "fault_tree_inspection_risk_campaign_execution": "Compose one exact action-specific fault-tree result per expected action into inspection.action_expected_loss inputs, invoke that registered ModelRegistry calculator with the caller's RunContext, and return a digest-bound campaign report embedding the comparison AssessmentResult and per-action FTA model/input/result digests. Return needs-data comparison results without selecting a minimum action when review gates are open. Do not infer action effects, event probabilities, costs or consequences.",
    "fault_tree_inspection_expected_loss_adapter": "Accept one caller-reviewed action-specific computed FTA AssessmentResult per expected action, each paired with an exact top-event IntegrityEventBasis and caller-owned action definition, configuration digest, probability bound, common-cause group and cost components. Convert results through the strict action-probability adapter and the existing expected-loss composer, preserving exact action coverage, shared event/scope/horizon/conditioning, one zero-cost baseline, complete costs and evidence. No intervention effect, costs, consequences or probability is inferred.",
    "fault_tree_action_event_probability_adapter": "Adapt one action-specific computed minimal-cut-set result into the inspection action probability exchange contract only when its basic events share conditional-first-failure-in-period semantics and the exact same conditioning statement, and the caller-supplied IntegrityEventBasis exactly matches the top-event ID, probability, model/version/input digest and full result digest. Preserve caller cost/action configuration and common-cause grouping. Do not infer inspection effectiveness; every intervention that changes the event tree requires its own evaluated tree.",
    "independent_basic_event_minimal_cut_sets": "Represent caller-declared minimal cut sets as AND gates and the top event as their OR. For reviewed independent basic events, compute each intersection probability as the product over the union of event IDs in the selected cut sets and combine intersections by exact inclusion-exclusion; report exact Birnbaum and probability-weighted basic-event importance. Bound the exact calculation to 16 cut sets; require a shared probability meaning and scope ID across events, retain conditioning and evidence digest, and optionally reconcile the existing integrity-event exchange contract including clock/horizon. Do not infer event probabilities, compatible horizons, independence, common causes, repair, initiating frequency or acceptance.",
    "critical_plane_interval_overlap_pairing_proposal": "Read two independently rainflow-counted scalar channels from one digest-pinned projected result and propose allocations only where normal-stress and shear-strain cycle sample-index intervals overlap. A deterministic continuous-capacity bipartite min-cost max-flow first maximizes total paired cycle equivalent, then maximizes allocated-count-weighted interval IoU; stable source order resolves equal-cost paths. Return unallocated counts and exact lineage. The optimization is a temporal-overlap proxy, not a validated physical pairing law, and the proposal must be reviewed before calibrated damage evaluation.",
    "planar_slit_geometry_reduction": "Reduce explicit constant-aperture, constant-cross-section slit dimensions and axial cell widths to cell volumes, selected broad-wall areas and reactive wall area per solution volume. Keep axial-area molar ledgers distinct from wall-area fluxes. No wall kinetics, side-edge area, advection, transverse gradients or aperture evolution is inferred.",
    "planar_slit_aperture_evolution": "Map either a caller-pinned cumulative signed cell-average wall recession or a digest-pinned cellwise wall-metal-loss result to sequential planar-slit apertures, cross sections, volumes and RestrictedTransportRequest-compatible geometry fields within a declared provider aperture range. Preserve cell order and clock; reconcile the source reactive wall areas against the declared face count, transverse width, reference area and cell widths. Positive recession denotes metal loss and increases aperture; negative recession denotes net deposition and reduces aperture. Two opposing reactive faces and piecewise-linear center-to-face area interpolation with constant boundary extrapolation require review. Support failures preserve the accepted geometry prefix and first failed interval with status out_of_scope. This is a geometry remap for a subsequent fixed-geometry solve; no within-step flow, chemistry, deposit mechanics or constitutive coupling is inferred.",
    "multiaxial_cycle_life_composition": "Compose the declared closed local tensor cycle, finite supplied plane factors and caller material-matched FS or SWT strain-life coefficients. Keep directional, pairwise-chord and enclosing-circle shear ranges explicit and retain exactly tied sampled planes. Root finding is restricted to calibrated cycle support; no continuous optimum, rainflow, nonproportional qualification or acceptance is inferred.",
    "reversible_gasket_contact_equilibrium": "Solve elastic-bolt force equilibrium against an explicitly authorized monotone piecewise-linear reversible gasket compression-force curve. Preserve initial preload, bolt free-length change and external separation load; distinguish closed contact, incipient separation, open gap and unsupported compression. No proprietary curve, hysteresis, flange bending, relaxation, leakage or acceptance rule is supplied.",
    "caller_nonlinear_bolt_gasket_equilibrium": "Solve a single-degree-of-freedom quasi-static force balance with caller-supplied monotone piecewise-linear bolt force-change versus signed extension and gasket force versus compression curves. Initialize bolt preload from the gasket force at declared initial compression, apply external separating force and bolt free-length change, and solve only inside both curve supports. Separate closed contact from separation and retain source/configuration digests. The curves may encode an independently justified equivalent assembly compliance, but the API does not infer it, transfer curves, model hysteresis/history, resolve a spatial flange field, predict leakage, or establish acceptance.",
    "calibrated_condition_loss_response": "Evaluate an explicit caller-calibrated log-rate response from normalized unit-labelled features and optional symmetric quadratic interactions, only inside declared support. Preserve material/mechanism/provider revision, source and configuration digests, computational-use authorization and condition review. Compose contiguous piecewise-constant histories through the existing calibrated-rate integral; withhold the total for any unsupported interval. No default microbial or cavitation law, automatic fit, causal inference or physical qualification is supplied.",
    "single_solid_stoichiometric_equilibrium": "Apply aqueous c_i = c_i0 - nu_i*extent and solid s = s0 + extent for one explicitly declared neutral pure solid, requiring elemental and charge conservation. With fixed caller activity coefficients and explicit concentration standard states, bracket the monotone log ion-activity product against the supplied dimensionless solubility product. Distinguish precipitation, partial dissolution and solid exhaustion without extrapolation, clipping, other aqueous speciation, competing phases, kinetics, transport coupling or protective-scale claims.",
    "ideal_single_solid_split_transport": "Compose fixed-geometry conservative transport and local atom/charge-conserving single-neutral-solid equilibrium with explicit initial projection and transport-then-phase operator ordering at declared time boundaries. Track each cell immobile solid inventory, preserve absolute callback time across restarted intervals and distinguish reference-area transported and phase-transfer aqueous inventories. Require one common ideal-activity phase law and retain every failed stage without total aggregation. No simultaneous geochemical solve, splitting-error guarantee, precipitation kinetics, porosity evolution or protective-scale effect is inferred.",
    "digest_pinned_activity_single_solid_split_transport": "Extend the fixed-geometry one-solid operator split with one caller-supplied activity-coefficient callback whose provider ID, configuration SHA-256 and chemical-potential/tracer-diffusivity review are pinned by the transport request. Use the same callback for nonideal transport drift and each phase-projection state, retain absolute time across restarted intervals, and require the initial cell phase gamma values to agree with the callback. This does not derive speciation, choose activity models or constants, solve competing phases simultaneously, update geometry, qualify the operator split or infer a protective-scale effect.",
    "explicit_co2_corrosion_campaign": "Compose a reviewed carbonate equilibrium boundary, explicit electrochemical reaction/transport request, and one selected tip metal-dissolution current mapping. Optionally bind a reviewed signed wall-metal ledger selection to caller-pinned reference area and species stoichiometry, preserving tip-reaction loss separately from wall-ledger loss. Optionally bind an identical-transport ideal single-solid split request with network/phase elemental consistency and separate aqueous/solid ledgers. Preserve constituent digests/statuses; no competing phases, precipitation kinetics, moving geometry, protective-scale effect, automatic calibration or acceptance is inferred.",
    "explicit_electrolyte_species_extension": "Extend an exactly ordered reaction network and concentration boundary with explicit species identities, charges, elemental compositions, concentrations and optional reactions. Revalidate charge/element conservation and report boundary charge without inventing counterions or neutralizing concentrations.",
    "explicit_carbonate_transport_boundary": "Map a completed carbonate equilibrium result from mol/L to mol/m3 and split CO2-star only with a caller-reviewed hydration fraction. Preserve solvent, result and partition digests and explicit water concentration. Do not invent counterions, infer complete-solution electroneutrality or convert unresolved molality.",
    "explicit_water_carbonate_network": "Assemble explicit-water carbon dioxide hydration, carbonic acid and bicarbonate dissociation, and water dissociation using caller forward/reverse concentration-based constants. Preserve charge and elemental stoichiometry; no equilibrium or hydration constant, activity law or solvent concentration is inferred.",
    "calibrated_fs_factor_life": "Solve a caller-calibrated engineering-shear strain-life relation against an explicitly identified Fatemi-Socie factor in log-cycle coordinates inside declared cycle support. Preserve plane-result lineage without inferring nonproportional material coefficients or experimental qualification.",
    "caller_shear_normal_strain_curve_life": "For each caller-supplied finite plane, combine nonnegative shear-strain amplitude with caller-weighted normal-strain amplitude. Select the largest declared parameter, retain exact sampled ties, and interpolate log(cycles) against log(parameter) only between ordered, same-condition caller calibration points. Bind ordered curve and full calibration digests and point-level source records. This is a generic independently authored user-curve mapping, not a claim to reproduce a named criterion; do not extrapolate or infer calibration rights, continuous-plane extrema, path-sensitive law, qualification or acceptance.",
    "kandil_brown_miller_curve_life": "For each supplied finite plane, obtain sampled shear-strain range from the maximum pairwise chord of the in-plane engineering-shear vector path. Restrict the KBM parameter to planes tied for the largest sampled shear range, then combine shear-strain amplitude with a caller-calibrated coefficient times the full normal-strain range on that plane. Map only by bounded log-log interpolation on an ordered, same-condition caller life curve and bind curve/calibration digests plus point-level Evidence. This is a sampled, caller-calibrated implementation of the KBM parameter form; it does not imply a continuous-plane optimum, universal coefficient, cycle counting, data rights, material qualification or acceptance.",
    "continuous_plane_fs_life_bound_mapping": "Map the certified sampled-cycle continuous-plane Fatemi-Socie factor bracket into a conservative cycle-life interval using the caller's existing FS strain-life calibration. Recompute life at both factor endpoints, require exact digest/parameter matching and a separate monotonicity review, and fail closed unless both roots lie within declared cycle support. The result is conditional on the supplied sampled cycle and factor-bound method; it does not cover unsampled history, calibration uncertainty, transfer, material/model error or qualification.",
    "explicit_critical_plane_cycle_pair_damage": "Apply a caller-declared mapping and cycle-count allocation between scalar normal-stress and engineering-shear-strain rainflow cycles on one identified plane. Require complete count coverage, prevent over-allocation, evaluate each mapped Fatemi-Socie factor against caller-calibrated engineering-shear strain-life coefficients, and sum linear Miner damage only when every cycle has in-support life. An optional digest-pinned interval-overlap proposal may be reconciled to the source result, plane, projection, method and configuration; reviewed mappings may revise counts only on proposed edges. Pairing convention, material calibration, unallocated-cycle treatment and Miner accumulation require caller review; this does not establish nonproportional fatigue qualification.",
    "closed_tensor_work_life_calibration": "Integrate stress contraction with strain increments over each caller-supplied ordered, endpoint-closed 3D tensor cycle using trapezoidal segment work for piecewise-linear paths or exact polynomial-product integration for cubic-Hermite paths with caller-supplied times and endpoint derivatives. Use the selected tensor or engineering shear convention. Map positive absolute loop work to a material-condition-matched caller calibration using bounded piecewise log-log interpolation, then sum explicitly allocated counts with linear Miner damage only when all cycles are closed and supported. Require caller review of tensor basis, conjugacy, cycle extraction/reconstruction, calibration applicability and accumulation rule; do not infer rainflow cycles, derivatives, slopes, extrapolation, a universal nonproportional law or code acceptance.",
    "caller_multiaxial_path_damage_integration": "Integrate a caller-pinned, memoryless nonnegative multiaxial damage-rate callback over ordered time-resolved six-component tensor cycles using adaptive composite Gauss-Legendre quadrature and caller-selected piecewise-linear or cubic-Hermite reconstruction. Require material/calibration/provider identity and rights review, exact source/configuration digests, path closure and conjugacy checks, and a bounded quadrature budget. Preserve cycle allocation, integration error estimate and per-cycle/global damage. This is a provider composition and numerical integrator; it does not define fatigue physics, stateful sequence effects, calibration, validity transfer or code acceptance.",
    "caller_multiaxial_law_applicability_binding": "Bind a caller-owned memoryless or stateful six-component tensor damage callback to an evidence-linked law/revision, provider and calibration digest, exact material condition, stress/strain measure and units, tensor component order, shear convention, componentwise stress/strain calibration envelopes, supported cycle duration/count/repetitions and time-reconstruction family. Check every runtime callback tensor sample against that profile and preserve the profile and source-configuration digests in the integration result. Reject metadata or reconstructed states outside declared support. The provider remains responsible for law physics, calibration quality, environment applicability, transfer, uncertainty and acceptance; this interface does not supply a universal multiaxial fatigue law.",
    "ordered_multiaxial_cycle_block_state_exchange": "Bind an externally produced ordered sequence of tensor-cycle blocks to the stateful damage request only when cycle arrays/order and stress/strain source digests match exactly. Verify each block payload digest, positive integer repetition semantics, unique cycle/block identities, zero-based block order and continuity of caller material-state identity from first to terminal block; preserve receipt digest, provider ID/revision/run ID/result digest, block IDs, source clock and both material-state endpoints in the integration result. Do not sort or infer missing order, repair state discontinuity, or convert material states into the fatigue law's internal state variables.",
    "external_flange_fe_compliance_receipt": "Require a digest-verified finite-element provider receipt and exact load-case, boundary-condition, mesh, frame, matrix-field identity/shape/unit/content digest, node/component DOF order, support indices, contact node/normal DOFs, closure signs and DOF-transform lineage. Convert only the caller-provided already reduced translational tangent stiffness matrix into the existing flange contact compliance reduction API; preserve provider, mesh, field and mapping lineage. This adapter does not run or assemble FE, infer transformations, handle mixed rotational DOFs, model nonlinear contact or establish seal qualification.",
    "external_flange_fe_compliance_receipt_history": "Bind one caller-declared increasing time knot to each digest-verified finite-element stiffness receipt and reduce each already normalized translational tangent matrix with a stable provider/model revision, asset scope, frame, node/component DOF order, supports, contact mapping and closure signs. Require caller review of receipt-to-time correspondence and preserve per-knot provider, mesh, field, source-array and transformation lineage. Do not infer physical timestamps, interpolate between receipts, execute FE, or qualify structural sealing.",
    "caller_correlated_gasket_leakage_joint_scenario_envelope": "Evaluate each caller-declared complete joint scenario with its correlated node contact pressures, common differential pressure, node areas and scenario-specific calibration flux grid on the fixed calibrated axes. Bilinearly interpolate only inside calibration support and area-weight node fluxes. Return extrema and witnesses over the finite enumerated scenarios, with calibration/scenario/license evidence and bounded work budgets. Do not independently recombine variables, infer probability weights or distributions, claim continuous uncertainty bounds, extrapolate or determine seal acceptance.",
    "caller_joint_gasket_leakage_covariance_delta_method": "Propagate a caller-provided symmetric positive-semidefinite covariance through total gasket leakage using a local Jacobian of the piecewise-bilinear calibration map. The vector order is node contact pressures, common differential pressure, node areas, then row-major calibration flux cells. Require nominal pressures strictly inside interpolation cells and preserve covariance/calibration/scenario evidence. Report first-order variance only; do not imply a probability interval or nonlinear bound.",
    "caller_gasket_leakage_independent_box_envelope": "Compute minimum and maximum total gasket leak rate over a caller-declared independent rectangular set of node contact pressures, positive areas, one common differential pressure and entrywise calibration-flux bounds. Require the nominal calibration table to lie inside the declared flux intervals, exact calibration-grid shapes, matching Evidence and usage rights, explicit box-independence and coverage reviews, and no extrapolation. Evaluate contact-pressure endpoints and table knots within each node interval, and common differential-pressure endpoints and table knots within the common interval; use nonnegative interpolation weights and positive area bounds to combine witnesses. The extrema are exact only for this finite-dimensional rectangular set and piecewise-bilinear reconstruction, not correlated/continuous mechanics, a probability/confidence interval, seal acceptance or qualification.",
    "caller_weighted_gasket_leakage_joint_scenario_moments": "Evaluate the calibrated total leakage response separately for each complete caller-supplied joint scenario, preserving each scenario's node pressures, common differential pressure, areas and calibration flux table. Bind an explicitly reviewed strictly positive ordered weight vector and its Evidence/license lineage to the exact scenario order; require the weights to sum to one without silent renormalization. Report weighted finite-set mean, population variance and standard deviation plus extrema/witnesses. These are descriptive moments of the declared finite weighted support, not failure probabilities, confidence bounds, continuous uncertainty bounds, extrapolation or seal acceptance.",
    "caller_stateful_multiaxial_damage_sequence_integration": "Integrate a caller-owned state derivative and nonnegative damage rate jointly with classical fixed-step or caller-controlled adaptive step-doubling RK4 over declared closed six-component tensor paths. Carry bounded dimensionless state across finite positive integer cycle repetitions and ordered cycle types, preflight the minimum callback evaluation budget, require explicit initialization/bounds, time reconstruction, closure, material/calibration/provider/rights reviews, and enforce callback identity and evaluation budgets. For repeated identical paths, optionally compare the terminal state after the last two repetitions against caller absolute/relative tolerances; this is a local cyclic-state diagnostic, not an asymptotic fixed-point or fatigue stabilization proof. The caller defines the constitutive state law and fatigue rate. Step convergence, fatigue validity, calibration transfer and code acceptance are not inferred.",
    "caller_adaptive_cycle_block_state_damage_ode": "Integrate a caller-defined bounded state derivative and nonnegative damage rate per cycle across ordered integer cycle blocks using RK4 step doubling, componentwise local error controls and a finite function-evaluation/rejection budget. Carry only accepted state, commit completed blocks, and retain an accepted prefix when a state boundary, unresolved event, provider mismatch or numerical limit stops the path. Bind provider/calibration/configuration digests and ordered state units. This is numerical integration of the caller's model, not an inferred fatigue law, cycle counter, life estimate, probability or material qualification.",
    "caller_aqueous_solid_phase_candidate_enumeration": "Screen caller-proposed, formula-reviewed neutral solids against a caller-closed aqueous species inventory by bounded integer stoichiometric enumeration. Retain only reactions with one solid unit on one side and aqueous species on the other; preserve request/evidence digest lineage. This does not infer phase formulas, validate chemical feasibility or stability, assign Ksp, choose precipitation direction, represent solvent/activity corrections, or predict corrosion scale formation.",
    "caller_zenodo_ti12mo5hf_aesec_row_reader": "Stream only the two allowlisted, hash-pinned AESEC worksheets from the depositor-declared CC0 archive after explicit local computational-use authorization. Preserve provider row order, headers, raw cells, member and archive digests, and declared units without conversion, filtering, segmentation, fitting or corrosion-rate interpretation. The reader does not parse the separate ICP-MS sheets or redistribute measurements.",
    "caller_declared_weld_dilution_uncertainty": "Mix explicitly identified melted base, filler and previous-layer constituents by their supplied masses. For each selected element, preserve missing assays instead of treating them as zero. Optionally propagate a caller-supplied joint covariance of all constituent elemental mass fractions using the exact linear mass-weight Jacobian and declared variable order. Retain source IDs, record digests and covariance basis. Melt masses are treated as exact inputs; no measurement uncertainty in melt weights, burnoff, segregation, weldability or corrosion/acceptance conclusion is inferred.",
    "explicit_coupled_dissolution_selection": "Select one explicitly reviewed dissolution-only reaction from complete aligned coupled-output partial-current histories and construct a digest-bound Faraday recession input. Reject missing, negative or nonfinite currents rather than taking absolute values or clipping. Output-clock integration resolution remains caller-reviewed.",
    "explicit_coupled_wall_metal_loss": "Map a coupled transport result's signed, integrated lateral-wall metal-species ledger to total molar/mass/volume change and area-average recession using a caller-reviewed physical reference area, reactive wall area, species stoichiometry, molar mass and density. Bind the full coupled result digest and retain source amount per reference area. Positive uptake denotes loss, negative uptake denotes redeposition. This is a whole-selected-area volume balance, not a local thinning field, corrosion-rate qualification, capacity or acceptance result.",
    "sequence_zone_memory_and_partial_dissolution": "Step ordered whole cycles with an explicit caller-calibrated opening ratio and plastic-zone extent memory, preserving integration-resolution and calibration boundaries. Separately integrate identified nonnegative partial anodic dissolution-current histories by trapezoids and Faraday stoichiometry with caller efficiency, molar mass and density. Net mixed-potential current is never substituted for dissolution current.",
    "electrochemical_transport_composition": "Compose exact species/charge-ordered homogeneous mass-action sources with Butler-Volmer tip and optional cellwise wall boundary fluxes at imposed potential or an explicitly reviewed zero-current condition. Bind tip and wall reaction configurations to separate digests; wall reactions use cell-local solution potential, caller-supplied area density, and an explicit reviewed equipotential-metal assumption. An optional ideal single-solid split transport request must match the base transport exactly and retain elemental, time and phase-input identities. Do not infer competing phases, protective-scale effects, calibrated CO2 chemistry or qualified metal recession.",
    "explicit_mass_action_transport_source": "Build concentration-based elementary mass-action source terms from explicit forward/reverse constants and stoichiometry. Require charge-conserving homogeneous reactions, exact species order and rate-unit tokens; preserve configuration digest. No kinetic constants, activities or elemental composition are inferred.",
    "caller_butler_volmer_stoichiometry": "Evaluate a caller-calibrated signed Butler-Volmer current inside explicit overpotential support and convert reaction extent to species boundary flux using caller stoichiometry. Bind surface callback identity and configuration to the restricted-transport request. Do not infer CO2 kinetics, calibration, activity corrections or corrosion qualification.",
    "fire_flux_conduction_composition": "Compose aligned caller incident flux and absorbed fractions as an explicitly reviewed net inward boundary for the existing multilayer transient conduction solver. Preserve incident and material configuration digests and propagate solver status. No fire curve, ablation, intumescence or unstated surface cooling is inferred.",
    "restricted_fick_reaction_transport": "Conservative nonuniform cells with explicit fixed cell/face/reference cross sections, area-weighted Poisson conductances and separately integrated homogeneous, mouth, tip and reviewed lateral-wall source ledgers, including a species-by-cell wall ledger. Reference-area inventories and local tip-area dimensional change remain distinct. Construct conservative one-dimensional cell-centered diffusion fluxes with a fixed mouth reservoir and sealed distal tip; add explicit caller volumetric reaction sources and integrate using BDF. First-order upwind advection accepts a fixed nonnegative face profile or a reviewed time-dependent Python callback returning signed face velocities. Flow reversal requires a reviewed distal inflow concentration; mouth, tip and cell fluxes use signed conservative ledgers. Caller attests volumetric-flow continuity with face areas; no momentum solution is inferred. Preserve species and provider configuration; reject negative output rather than clipping. Optional prescribed-field or self-consistent Poisson potential supplies Scharfetter-Gummel ion migration. Poisson uses an explicit mouth potential, sealed-tip zero field, permittivity and optional fixed charge. Surface charge, activities, moving geometry and kinetic calibration remain caller inputs or separate models.",
    "caller_prescribed_moving_geometry_transport": "Interpolate caller-provided cell/face cross-section histories linearly on the requested output clock, interpolate wall-area density when wall flux is enabled, and add the conservative concentration dilution/expansion term -C (dV/dt)/V so stored inventory C*V is preserved under changing cell volume. Include the time-varying volumes in every inventory output and retain provider/configuration/source/time-basis lineage. Geometry is prescribed independently of transport chemistry and wall flux; this API does not solve moving-boundary feedback, pressure/momentum continuity, mesh motion, phase mechanics, or a qualified corrosion law.",
    "caller_coupled_crevice_diffusive_recession_fixed_point": "For a bounded segment, guess a linearly varying end aperture, derive aligned cell/face cross-section and reactive-wall-area histories, and solve conservative transport with moving-volume dilution. The default fixed-point mode excludes axial advection. An opt-in hydraulic extension requires reviewed steady slit hydraulics, piecewise-linear pressure history, flow continuity, endpoint-velocity-path assumptions and reversal/distal-inflow inputs; it evaluates the guessed endpoint steady face velocity and passes an explicit local-time linear interpolation callback to transport. Convert the selected signed cellwise wall-metal ledger to a candidate end aperture and iterate with caller-selected relaxation until the declared relative endpoint residual is met. Require reviewed deterministic callbacks, mapping and convergence gates, finite iteration/time/change budgets, and declared geometry support; commit only a converged segment and preserve every iteration/input/result digest and rejected prefix. Exclude transient momentum, simultaneous flow/chemistry, evolving chemistry parameters, phase mechanics and calibrated wall-law qualification.",
    "calibrated_damage_and_plane_life_composition": "Integrate explicitly calibrated local loss rates over contiguous supported intervals, and separately map caller-reviewed critical-plane normal stress/strain amplitudes to the existing calibrated SWT life relation. Do not infer damage rates from microbial indicators or cavitation margin, or infer independent validation from model predictions.",
    "cylindrical_surface_energy_balance": "Solve the monotone steady balance between radial cylindrical conduction, caller constant convection, and gray radiation to declared surroundings. Bracket surface temperature between the specified boundary temperatures and retain heat-balance residual without inferring transient protection performance.",
    "caller_fad_and_assembly_geometry": "Interpolate a caller FAD curve without extrapolation; calculate regular tube lattice void and bore areas, identified tube wall-loss inventory, and linear two-spring joint load partition. Preserve explicit support and closed-contact limitations without embedding code limits or predicting nonlinear gasket response.",
    "caller_gasket_relaxation_curve": "Interpolate an authorized, specimen- and condition-identified caller gasket preload-retention curve only within its measured time support and scale by a caller-supplied initial preload. Preserve provider revision, source and condition digests; do not fit a universal law, extrapolate, infer leakage, model unload/reload hysteresis or decide acceptance.",
    "caller_gasket_prony_constitutive_response": "Integrate caller-authorized generalized Maxwell branch stresses over a piecewise-linear compressive-strain history using the closed-form update for each declared relaxation time. Preserve initial internal stresses, material condition, specimen, temperature, provider revision and source/configuration digests. Do not fit or transfer coefficients, model tensile contact loss, flange flexibility, leakage or acceptance.",
    "caller_coupled_prony_bolt_gasket_history": "At each supplied time knot, update caller-authorized generalized-Maxwell branch stresses for a piecewise-linear gasket compression-strain segment and solve the affine force balance against a linear elastic bolt, caller external separating load and bolt free-length change. Preserve material/provider/source identity, initial branch state, input digest and force residual. Restrict the result to reviewed closed contact and declared strain support; do not fit or transfer Prony coefficients, model contact opening, spatial flange flexibility, leakage or acceptance.",
    "caller_nonlinear_gasket_prony_joint_history": "Represent the gasket equilibrium response and each generalized-Maxwell branch with caller-authorized monotone piecewise-linear stress-strain backbones. Split a linear strain interval at every crossed backbone knot and exactly integrate each first-order branch state over each constant-slope segment; at each declared time knot solve closed-contact equilibrium against a caller-supplied nonlinear bolt force-extension curve and external separating load. Preserve initial branch state, calibration/provider/source digests and force residual. Do not extrapolate, fit or transfer curves, model unilateral contact opening, spatial flange flexibility, leakage or acceptance.",
    "caller_unilateral_nonlinear_gasket_prony_joint_history": "Use caller-authorized nonlinear generalized-Maxwell gasket backbones and a pinned nonlinear bolt force-extension curve in a single-degree-of-freedom quasi-static joint. Enforce compression-only gasket reaction and record closed, opened, remained-open and reclosed contact states at declared time knots. Freeze branch state at zero compression while separated and require separate review of this assumption. Do not infer transition times between knots, fit or transfer curves, resolve flange fields, predict leakage or establish acceptance.",
    "caller_spatial_flange_contact_compliance": "Solve a nodal unilateral contact complementarity problem from a caller-supplied symmetric positive-semidefinite relative flange compliance matrix, caller-composed free-closure vector, and local linear gasket stiffnesses. The active-set method requires nonnegative contact forces and gaps, checks the matrix support and preserves each provider result digest. It consumes but does not calculate the flange compliance operator, infer bolt/load composition, reconstruct local stress, predict leakage or establish sealing acceptance.",
    "caller_spatial_nonlinear_flange_contact_compliance": "Solve compression-only nodal equilibrium from a caller-supplied symmetric positive-semidefinite flange compliance matrix, free-closure vector, contact areas and strictly increasing reversible piecewise-linear gasket force-compression curves. A damped Newton method solves only inside each declared curve support and preserves provider configuration/result digests. It does not generate a flange finite-element response, infer loading, transfer material curves, represent gasket hysteresis or viscoelasticity, resolve local stress, predict leakage or establish acceptance.",
    "caller_spatial_linear_prony_flange_contact_history": "Advance caller-calibrated linear generalized-Maxwell gasket branches at spatial contact nodes over explicitly sampled free-closure history, using exact exponential branch updates over piecewise-linear strain segments. At each declared knot, solve a unilateral quasi-static contact problem against a caller-supplied symmetric positive-semidefinite flange compliance matrix. Preserve provider result lineage and fail closed on unsupported compliance, unmet review gates or contact iteration limits. The initial knot is an instantaneous load from a reviewed zero-compression branch state. No flange FE response, within-interval contact transition, nonlinear hysteresis, leakage or acceptance is inferred.",
    "caller_linear_flange_contact_compliance_history": "Reduce caller-supplied symmetric translational stiffness matrices to an aligned contact-compliance history using declared retained degrees of freedom and condensation constraints at each time knot. Preserve matrix order, knot alignment, source digests and positive-semidefinite checks; do not generate a finite-element stiffness matrix, infer interpolation between knots or evaluate gasket contact.",
    "caller_linear_flange_contact_compliance_reduction": "For a caller-supplied symmetric incremental stiffness operator, constrain declared support DOFs, solve unit-load responses at uniquely mapped translational contact DOFs, apply the caller closure signs, and extract the resulting compliance block. Reject singular, ill-conditioned, asymmetric or non-positive-semidefinite operators; preserve solver and source lineage. Do not assemble or qualify the upstream finite-element model.",
    "caller_rate_competitive_solid_mass_balance_ledger": "Apply explicitly supplied signed molar extent rates for a caller-declared set of neutral solid phases over contiguous time intervals. Limit dissolution by available phase inventory, then limit simultaneous precipitation with one common aqueous-reactant factor that preserves the supplied phase-rate ratios. Verify each declared reaction's charge and elemental stoichiometry and report time-resolved dissolved and solid inventories with balance residuals. This is conservative bookkeeping for user-supplied rate outputs; it does not estimate kinetic laws, phase selection, saturation, scale morphology or corrosion protection.",
    "caller_rate_multiphase_transport_operator_split": "For each fixed-geometry transport interval, either apply explicit caller-provided cellwise phase rates or evaluate a caller activity/Ksp saturation callback after transport at the interval's right knot and map its cellwise saturation ratios through declared per-phase power laws. An adapter binds activity samples to reviewed source-backed solubility-product screens. Apply resulting signed rates with the conservative multicomponent phase inventory ledger. Preserve transport/kinetic source separation and campaign provenance. This lagged operator split does not qualify the activity model, propagate activity/Ksp uncertainty into rates, update rates within a time interval, select phases, evolve morphology or solve simultaneous chemistry and transport.",
    "caller_competing_solid_saturation_rate_law": "Use a caller-supplied dimensionless saturation ratio per declared neutral solid phase and interval to select a phase-specific precipitation power law above unity or dissolution power law below unity, then pass the signed extent rates into a conservative phase/aqueous inventory ledger. Coefficients, orders, standard state, temperature support, reaction network and qualification are user supplied. No saturation calculation, activity model, phase discovery, nucleation, or physical performance is inferred.",
    "competitive_pure_solid_fixed_gamma_equilibrium": "Minimize the dimensionless ideal-mixing Gibbs potential for a closed fixed-volume aqueous species set and declared neutral solid phases with fixed activity coefficients. Extent constraints enforce aqueous nonnegativity and nonnegative final solid inventories; equilibrium is checked with phase saturation inequalities, complementarity residuals, and species extent balances.",
    "caller_competitive_solid_equilibrium_transport_split": "At each declared output boundary, solve fixed-geometry restricted transport over the preceding interval, then project each cell onto its caller-declared competing neutral-solid equilibrium with an inner Davies ionic-strength fixed point. Preserve separate transport and phase source ledgers, solid inventories by phase and cell, provider digests and aqueous inventory closure. Require one aligned transport-activity callback configuration and an explicit activity-to-phase mapping review. Do not infer phase kinetics, evolving geometry, simultaneous transport-reaction equilibrium or qualification.",
    "planar_slit_steady_laminar_hydraulic_reduction": "For each caller-defined axial cell, calculate the wide-slit resistance 12 mu L/(w h^3), sum cell resistances in series, and derive a steady flow from the explicit pressure difference. Convert the common flow to cell and interpolated face velocities, reconstruct cell pressure drops, and report hydraulic-diameter Reynolds diagnostics. A supplied aperture-history result must be digest-bound to the final cell apertures.",
    "planar_slit_sequential_hydraulic_history": "Require a computed digest-bound planar-slit aperture history and one positive pressure-drop sample for each geometry knot. At each knot, independently evaluate the registered steady wide-slit hydraulic reduction and retain its flow, pressure and face-velocity diagnostics with the source geometry time. Aggregate only when every knot is within the declared aspect-ratio and Reynolds support.",
    "caller_nonlinear_maxwell_spatial_gasket_contact": "Couple caller-supplied monotone equilibrium and nonlinear generalized-Maxwell stress-strain backbones to a caller flange-compliance matrix at spatial contact nodes. Advance each branch over explicit piecewise-linear strain intervals with exact exponential updates split at backbone knots, and solve unilateral quasi-static contact at declared time knots using a bounded damped Newton active set. Preserve material and structural provider digests; fail closed on loss of local positive tangent, curve/support exceedance, nonconvergence or work-budget exhaustion. The initial knot is an instantaneous load from a reviewed zero-strain state. No flange FE response generation, intermediate contact transition, leakage, seal performance or acceptance is inferred.",
    "critical_plane_continuous_lipschitz_bound": "Construct deterministic successively refined icosphere vertex nets on the unit sphere, identify antipodal normals for unoriented planes, and bound the uncovered angular distance by the maximum spherical face-edge angle. Combine that coverage bound with tensor-Frobenius Lipschitz constants for the implemented maximum-pairwise engineering-shear-chord Fatemi-Socie and SWT sampled-cycle factors. Report lower sampled maxima and conservative continuous-orientation upper bounds; the guarantee excludes unsampled time, cycle-counting, calibration and physical-model errors.",
    "critical_plane_projected_rainflow_decomposition": "Project each caller-selected finite material plane into explicitly selected scalar normal-stress, normal-strain, signed in-plane shear-component or nonnegative shear-vector-magnitude histories. Apply the documented scalar rainflow library independently to each series, preserve residual half cycles and original sample/time identities, and return channels separately. Do not infer cross-channel cycle pairing, phase relation, multiaxial damage, life or acceptance.",
    "critical_plane_piecewise_linear_time_extrema": "Reconstruct symmetric stress and infinitesimal-strain tensor components linearly between caller-timed samples of one reviewed closed cycle. For the declared finite planes, normal scalar extrema occur at segment vertices; each in-plane shear-vector segment lies inside the convex hull of its endpoints, so vertex-based maximum chord and minimum-enclosing-circle radii are exact for this reconstructed path. This establishes interpolation-conditional FS/SWT factor extrema, not fidelity to unknown physical behavior, continuous-plane search, multiaxial rainflow pairing, variable-amplitude damage, life or material validation.",
    "subset_replicate_dispersion": "Build independent seed tasks with parent/input/result hashes; require exact unique result coverage and matching evaluator/event/sampling identities and one NumPy version before restoring manifest order for aggregation. Run the same deterministic limit-state mapping with distinct seeded random streams and summarize between-run probability dispersion only if every replicate completes. Preserve constituent results and withhold summaries when a replicate fails. Replicate dispersion does not establish estimator bias, model uncertainty or convergence.",
    "tangent_thermal_expansion_integration": "Integrate a caller-reviewed piecewise-linear tangent coefficient defined as d(log length)/d temperature using exact segment trapezoids. Convert log length change by expm1 and retain each table digest. Disable extrapolation and do not substitute secant coefficients or infer restraint stresses.",
    "declared_creep_fatigue_campaign_composition": "Compose reviewed creep rupture-time fractions and strain-life cycle fractions with an explicit caller interaction envelope. Preserve constituent statuses and input digests, reject material and damage-definition mismatches, and withhold interaction when constituent quantities are unavailable.",
    "declared_secondary_creep_history": "Integrate caller-calibrated constant-condition Norton secondary-creep rates over ordered contiguous intervals inside explicit parameter support. Separately sum duration over externally provided rupture time only after linear-fraction review. Preserve parameter and input digests without inferring redistribution, tertiary creep or interaction.",
    "declared_strain_life_block_accumulation": "Evaluate caller-selected fully reversed, Morrow or SWT calibrated strain-life blocks and sum cycle-count to predicted-life ratios only after explicit linear-accumulation review. Withhold the aggregate when any positive-count block lacks a supported life. Preserve request digest and per-block status without inferring sequence effects or probability.",
    "caller_creep_fatigue_interaction_curve": "Interpolate a caller-owned nonincreasing fatigue-limit curve against strictly increasing creep coordinates within declared temperature and material support. Preserve definitions and input hashes; report vertical margin and utilization without embedding code curves or inferring damage calibration or acceptance.",
    "usgs_phreeqc_davies_activity_coefficients": "Calculate ionic strength as one half the sum of molality times squared charge from the complete caller-supplied aqueous species inventory. For charged species use log10(gamma_i) = -A z_i^2 [sqrt(I)/(1+sqrt(I)) - 0.3 I], with temperature/solvent-specific A supplied and evidenced by the caller. Neutral-species gamma is unity only as an explicit convention. Require charge balance and restrict the caller-declared classic Davies range to at most 0.5 mol/kg water; do not extend to concentrated brines or infer gas solubility or corrosion.",
    "neuber_local_strain_compatibility": "For a caller-reviewed scalar elastic stress concentration factor Kt and nominal stress amplitude S, solve sigma times epsilon = Kt squared times S squared divided by E. The local stabilized cyclic strain is sigma/E plus (sigma/K-prime) raised to 1/n-prime. The implementation brackets the positive root and applies deterministic bisection; it does not infer Kt, material calibration or fatigue life.",
    "ramberg_osgood_cyclic_relation": "Use the caller-supplied stabilized cyclic strength coefficient K-prime, exponent n-prime and elastic modulus to partition local strain amplitude into elastic and plastic components. This relation alone does not establish material applicability, transient history, multiaxial response or life.",
    "morrow_mean_stress_strain_life": "Solve the caller-calibrated uniaxial relation epsilon_a = ((sigma_f_prime - sigma_m) / E) * (2 N_f)^b + epsilon_f_prime * (2 N_f)^c only where the effective elastic coefficient is positive and the root remains inside declared cycle support. Require an explicit tension-positive sign convention and material-applicability review. Do not infer multiaxial correction, variable-amplitude damage, fatigue coefficients, probability or acceptance.",
    "authored_storage_preservation_campaign_evidence_audit": "Preserve caller-supplied item, material, area, storage location, preservation method and material batch, ordered storage-exposure-inspection-renewal events, interval coverage, and temperature, humidity, dewpoint, ingress, desiccant, inhibitor, cover, seal, surface or corrosion observations. Apply only caller-authored criteria. Do not infer corrosion rate, remaining life, standard cycles or automatic acceptance.",
    "authored_test_water_quality_campaign_audit": "Preserve caller-supplied water source, batch, tank, circuit, contact material, ordered fill-hold-drain-dry history, sample identity and calibrated pH, conductivity, chloride, halide, oxygen, solids, microbiology, inhibitor or temperature results with exact species definition, unit, uncertainty and independence lineage. Apply only caller-authored criteria. Do not convert species, infer corrosion rate or MIC risk, embed limits or automatically accept water quality.",
    "authored_repair_welding_production_campaign_profile": "Preserve caller-supplied component, repair, weld, WPS, welder, base heat, consumable, prior repair count, defect-removal and excavation geometry, ordered removal-preheat-deposition-interpass-PWHT-cooling events, and NDE, hardness, dimensional, chemistry, mechanical or leak evidence. Apply only caller-authored criteria. Do not embed code acceptance, qualify a WPS, predict crack growth or infer remaining life.",
    "authored_exact_specification_alias_profile_set_audit": "Audit caller-owned exact designation profiles, aliases, material-family and condition bindings, query coverage, ambiguity, unknowns and deterministic provenance. Reuse exact matching only; do not apply fuzzy matching, infer standard equivalence or make an acceptance decision.",
    "authored_certificate_campaign_coverage_reconciliation": "Compose caller-owned certificate requirement reconciliation with document, product, heat and traceability identities plus chemistry, mechanical, heat-treatment, NDE and traceability coverage. Apply only caller criteria; do not embed specification values, infer designation equivalence, approve material or perform statistical inference.",
    "authored_cui_inspection_evidence_campaign_audit": "Preserve caller-defined CUI scope, insulation, jacketing, coating, material, service and environment identities, ordered access, inspection, repair and reinstatement events, explicit coverage and moisture, visual, thickness or NDE observations. Apply only caller criteria; do not extrapolate hidden areas, infer corrosion rate, remaining life, POD, risk or standard acceptance.",
    "authored_cui_digest_bound_downstream_evidence_receipt": "Create a compact downstream exchange record that binds reviewed CUI campaign outcome, accessed-area coverage, observation count and criterion outcomes to the assessment input and campaign report digests. The receipt does not infer corrosion rate, extrapolate hidden areas, or generate risk or failure probability.",
    "authored_allowable_property_provider_profile_audit": "Audit caller-owned or licensed material-property tables and exact material, product, condition, orientation, property, basis and edition identities, provider revision, applicability, units, temperature support, query and result digests. Reuse only reviewed in-support interpolation; do not extrapolate, embed proprietary tables, generate allowable stress or make acceptance decisions.",
    "authored_bounded_galvanic_coupling_assessment": "Compose reviewed electrode polarization curves within their common support while preserving metal, surface, area, electrolyte, environment, reference electrode, electrical connection, resistance and solver identities. Keep signed net current separate from partial dissolution observations; do not infer corrosion rate, life, acceptance or probability.",
    "authored_two_electrode_resistive_galvanic_balance": "For two caller-reviewed piecewise-linear signed polarization curves in one shared electrolyte, temperature and reference, solve every segment-pair equilibrium under one finite series resistance. Enforce current and voltage balance, retain multiple or continuous roots, reject roots outside either curve support, and keep net current distinct from partial dissolution. No corrosion rate, life, stability, acceptance or probability is inferred.",
    "authored_rectilinear_thickness_map_cell_area_balance": "Use explicit increasing x/y cell edges to compute actual rectilinear cell areas, observed-area-weighted thickness, missing coverage, signed observed reference-loss volume, and caller-selected four- or eight-neighbour threshold component areas. Missing cells are excluded from observations and never interpolated or assumed sound; geometry summaries are not structural acceptance or life predictions.",
    "authored_external_pressure_provider_receipt_campaign_audit": "Audit externally supplied external-pressure assessments, exact geometry, material, imperfection, boundary and load identities, pressure basis, solver and provider digests, applicability support, convergence and calibration or holdout evidence. Do not solve buckling, embed code curves or factors, accept a component or claim field qualification.",
    "authored_weld_hardness_mapping_campaign_audit": "Preserve caller-supplied weld, joint, WPS, heat, consumable, material, cross-section and coordinate frame, traverse, hardness configuration and calibrated point readings with caller-assigned weld-region labels, uncertainty and independence lineage. Apply only caller-authored criteria. Do not convert scales, infer strength, automatically classify HAZ regions, embed acceptance values or claim qualification.",
    "authored_replica_metallography_campaign_evidence_audit": "Preserve caller-supplied component, location, material, heat, ordered service history, surface preparation, replica medium, magnification, instrument, calibration, image digest, and quantitative or qualitative grain, cavity, phase, precipitate, decarburization or user observations with uncertainty and independence lineage. Apply only caller-authored criteria. Do not perform image analysis, embed grading tables, infer creep life or claim standard acceptance.",
    "authored_chemical_cleaning_production_campaign_profile": "Preserve caller-supplied asset, material, area, circuit, precondition, chemical batch composition and concentration, ordered fill-circulate-soak-rinse-neutralize-dry events, process conditions, coupon, solution, surface, residue, chemistry or NDE measurements, and waste-disposition evidence. Apply only caller-authored criteria. Do not infer kinetics, corrosion rate, material compatibility or standard acceptance.",
    "authored_bonded_layer_integrity_campaign_audit": "Preserve caller-supplied substrate, layer, material lot, interface geometry, coordinate frame, bond process, ordered preparation-application-cure-heat history, sample identity, and thickness, adhesion, shear, peel, porosity, disbond, continuity or NDE evidence with uncertainty and independence lineage. Apply only caller-authored criteria. Do not automatically classify cohesive or adhesive failure, embed standard acceptance, predict life or claim qualification.",
    "authored_surface_cleanliness_production_campaign_profile": "Preserve caller-supplied substrate, area, prior coating, contaminant, preparation process, ordered events, ambient, surface and dewpoint temperatures, and salt, dust, profile, oil, visual or roughness measurements with location, uncertainty and provenance. Apply only caller-authored criteria. Do not perform image classification, embed standard comparators or limits, or claim coating qualification.",
    "authored_tensile_offset_yield_campaign_evidence_audit": "Preserve caller-supplied tensile specimen, product, heat, orientation, geometry, machine, load-cell and extensometer calibration, temperature, strain rate, offset definition, reported modulus, yield, ultimate strength, elongation or reduction-area result, uncertainty and independence evidence. Apply only caller-authored criteria. Do not recalculate curves, automatically derive offset yield, embed official validity rules or claim design acceptance.",
    "authored_casting_forging_quality_campaign_audit": "Preserve caller-supplied product, heat, material, manufacturing route, forging-ratio definition or casting process, ordered heat treatment, sample location and orientation, and dimensional, surface, internal, NDE, macro, micro, chemistry or mechanical observations with uncertainty and independence lineage. Apply only caller-authored criteria. Do not embed minimum forging ratios, defect limits, code tables or material qualification.",
    "authored_hardness_testing_campaign_evidence_audit": "Preserve caller-supplied subject, material, heat, location, hardness method, scale, load, dwell, indenter, instrument, reference-block verification, surface, spacing, thickness, reading, uncertainty and independence evidence. Apply only caller-authored criteria. Do not convert scales, embed official validity rules, infer strength or claim design acceptance.",
    "authored_production_weld_test_campaign_profile": "Preserve caller-supplied weld, joint, WPS revision, welder, consumable lot, base heat, coupon extraction and bend, tensile, impact, hardness, macro, NDE, chemistry or user measurement evidence with uncertainty and independence lineage. Apply only caller-authored criteria. Do not embed code acceptance, qualify a WPS, convert strength or automatically accept production welds.",
    "authored_transport_erection_campaign_evidence_audit": "Preserve caller-supplied item, lift, transport, storage, erection and support identity; ordered handling events; acceleration, load, orientation, temperature, humidity and impact observations; temporary-support state; and alignment, geometry, damage-survey or NDE measurements. Compare only with caller-authored criteria. Do not solve structures, provide allowable loads or code tables, automatically classify damage or claim qualification.",
    "authored_impact_testing_campaign_evidence_audit": "Preserve caller-supplied impact specimen, product, heat, orientation, notch, dimensions, test temperature, machine, striker, calibration, reported energy, lateral expansion or shear-fracture result, uncertainty and independence groups. Apply only caller-authored campaign criteria. Do not embed official validity rules, temperature corrections, transition fitting, design allowables or qualification.",
    "authored_brazing_bonding_production_campaign_profile": "Preserve caller-supplied base, filler or adhesive lot, surface preparation, fit-up, atmosphere or flux, joint geometry, ordered thermal-pressure-cure cycle and destructive, NDE, leak, strength or continuity measurements. Compare only with caller-authored identity and metric criteria. Do not infer material compatibility, life, published acceptance or qualification.",
    "authored_fracture_toughness_testing_campaign_audit": "Preserve caller-supplied specimen identity, geometry, orientation, temperature, environment, loading, fatigue-precrack evidence, reported toughness result, exact unit, validity flags, uncertainty and independence groups. Compare only with caller-authored campaign criteria. Do not embed official validity rules, convert or recalculate toughness, supply design allowables or claim method qualification.",
    "authored_wave_reference_baseline_campaign_quality_audit": "Aggregate caller-supplied acoustic-emission or guided-wave array, coupling, acquisition, baseline, observation, channel, coverage and reference-check evidence. Compare timing, amplitude, noise, localization and reference consistency only with caller-authored criteria. Do not detect or size damage, estimate POD, apply published acceptance limits or claim physical qualification.",
    "authored_electromagnetic_reference_campaign_quality_audit": "Aggregate caller-supplied eddy-current or magnetic-flux-leakage configuration identities, physical reference features, encoded scan digests, channel and extent coverage, staged checks, sensitivity, noise, resolution and drift. Compare only with caller-authored criteria. Do not process waveforms, size or accept flaws, estimate POD, reproduce published limits or claim physical qualification.",
    "authored_imaging_reference_campaign_quality_audit": "Aggregate caller-supplied radiography or phased-array procedure identity, reference-standard features, encoded-acquisition digests, coverage and staged verification metrics. Compare sensitivity, resolution and coverage descriptors only with caller-authored criteria. Do not inspect image pixels, accept flaws, estimate POD, reproduce a published limit or claim physical qualification.",
    "authored_caller_leak_campaign_quality_audit": "Aggregate caller-supplied traceable reference-leak responses, blanks, state identities, repeat groups, sequence, uncertainty or detection-threshold evidence. Compare only derived repeatability, drift, background and uncertainty descriptors with caller-authored criteria. Do not fit a leak calibration, infer detection probability, solve leak physics, apply a published acceptance table or claim physical qualification.",
    "authored_caller_defined_scc_rule_screening": "Evaluate only caller-authored, evidence-linked material, environment and stress facts against caller-authored AND conditions grouped into OR screening rules. Preserve unknown and invalid facts, use the declared conservative unknown policy, and never convert an unknown into a screen-out. No proprietary threshold, acceptance rule, initiation model, growth rate, remaining life, failure probability or qualification claim is bundled.",
    "weighted_blank_corrected_known_volume_pressure_rise": "Fit caller-reviewed blank and test absolute-pressure histories on their original clocks with uncertainty weights, subtract their slopes, and multiply by a known volume to obtain signed net gas throughput with propagated uncertainty. Preserve independent run/source identities and optional reviewed reference-temperature conversion without separating outgassing from through-leak, locating a leak, deciding acceptance or creating probability.",
    "authored_multi_record_certificate_requirement_reconciliation": "Compare caller-supplied chemistry mass-fraction and SI property requirements with multiple provenance-bound material certificate or independent test records for one heat, lot and condition. Preserve aliases, duplicates, missing rows, uncertainty overlap and pairwise contradictions without averaging, embedding specification tables, choosing a material name, deciding code acceptance or creating failure probability.",
    "authored_dissimilar_weld_review_reconciliation": "Reconcile caller-owned applicability reviews for two base materials, deposited layers, fusion-boundary regions, ordered thermal history, service environment and optional transition measurements. Preserve material/provider/procedure/frame/digest identities and unresolved evidence without embedding alloy-pair rules, inferring compatibility, predicting life, deciding acceptance or creating probability.",
    "weighted_pre_necking_monotonic_hollomon_calibration": "Fit log true or engineering stress against log plastic strain for caller-reviewed, weighted pre-necking monotonic calibration points after explicit elastic-strain subtraction. Preserve specimen, source and independence partitions; evaluate holdout error only inside calibration support without post-necking extrapolation, cyclic inference, acceptance, life or probability.",
    "authored_cathodic_protection_field_survey_summary": "Preserve native, on, off and instant-off potential conventions, reference-electrode calibration support, IR-drop handling, rectifier or anode current, environment, uncertainty and immutable evidence identities. Summarize observations and caller-owned directional threshold margins without embedded protection criteria, coating inference, remaining life, compliance or probability.",
    "authored_trapezoidal_instrumented_impact_reduction": "Reduce one provenance-bound instrumented impact force-displacement-time signal over a caller-reviewed valid window using explicit force sign, trapezoidal work integration and plateau-aware peak reporting. Preserve specimen, notch, orientation, temperature, striker, calibration and optional independent machine-energy evidence without inferring crack initiation, transition temperature, toughness, acceptance or probability.",
    "weighted_archard_wear_coefficient_calibration": "Derive one positive dimensionless Archard coefficient per valid calibration record from measured wear volume, hardness, normal force and sliding distance, then form a caller-weighted geometric mean for one reviewed material, counterface, contact and lubrication regime. Preserve disjoint specimen/source partitions, uncertainties and excluded records; evaluate holdout only inside calibration support without modeling fretting-corrosion interaction, service life, acceptance or probability.",
    "authored_hardness_reference_block_bias_repeatability_calibration": "Estimate observed-minus-certified bias and instrument repeatability for one exact hardness method, scale, indenter, load, dwell and configuration using certified reference blocks and their stated uncertainty. Preserve disjoint physical-block/source/independence partitions and evaluate corrected holdout residuals only inside certified-value and temperature support without converting scales, inferring strength, deciding acceptance or creating probability.",
    "authored_weighted_elastic_offset_line_intersection": "Fit a weighted elastic line on a caller-reviewed window of a strictly ordered engineering stress-strain branch and locate the unique linearly interpolated crossing with a declared parallel offset line inside a reviewed pre-necking window. Preserve specimen, extensometer, instrument and source digests; optionally compare an independent reference result without true-stress conversion, acceptance or failure probability.",
    "weighted_polymer_arrhenius_time_shift_calibration": "Fit valid calibration natural-log time-shift factors against reciprocal absolute temperature relative to a caller reference using declared weights. Preserve exact polymer formulation, physical state, endpoint, provider digests and disjoint specimen/source/independence partitions; evaluate holdout only inside temperature support without inferring chemical compatibility, long-term life, acceptance or probability.",
    "authored_weighted_erosion_corrosion_power_law_calibration": "Fit a positive combined measured loss rate as a weighted log-linear power law in velocity and particle concentration for one reviewed material, fluid, geometry and mechanism regime. Preserve provider digests and disjoint partitions; evaluate holdout only inside the two-dimensional calibration hull without separating erosion from corrosion, changing regimes, forecasting service loss, or inferring acceptance or probability.",
    "authored_reference_leak_log_response_regression": "Fit detected, clock-aligned instrument response against traceable positive molar reference-leak rate in a fixed weighted log-log regression. Preserve gas, boundary, instrument configuration, uncertainties, provider digests and excluded non-detect/censored/missing rows; evaluate holdout only inside reference-leak support without inverting unknown leaks, estimating detection probability, deciding acceptance or creating FTA probabilities.",
    "two_stage_weighted_coffin_manson_basquin_calibration": "Fit separated elastic and plastic strain-amplitude components against log reversals in two calibration-only weighted log-linear stages, preserving endpoint and runout/censor status. Report holdout component diagnostics only inside calibration cycle support; do not substitute censored observations or infer acceptance, service life or probability.",
    "authored_partitioned_accelerated_lognormal_creep_rupture_likelihood": "Fit a fixed log-time regression in log inverse stress and reciprocal absolute temperature with a lognormal scale, using rupture density and right-censor survival likelihood terms in calibration records. Preserve exact stress/load convention and partition identity; evaluate holdout only inside the calibration covariate hull without inferring mechanism transitions, variable-history life, acceptance or probability.",
    "caller_supplied_sobol_replicate_estimates": "Reduce complete caller-supplied replicate first/total Sobol estimates with equal-replicate means, dispersion and pairwise rank-stability diagnostics under exact common distribution, dependence, design and evaluator identities. Do not execute an evaluator, estimate new indices, reinterpret dependent-input indices, or claim convergence, causality or validation.",
    "weighted_stabilized_cyclic_ramberg_osgood_fit": "Fit log stabilized cyclic stress amplitude as an affine function of log positive plastic strain amplitude using caller weights and calibration records only. Preserve exact stress/elastic-modulus units, material condition and disjoint specimen/source/independence groups; report holdout log-stress diagnostics without extrapolating or inferring fatigue life, acceptance or probability.",
    "reviewed_signal_response_pod_qualification_envelope": "Fit a caller-reviewed fixed-threshold normal-residual signal response linear in natural-log flaw size using uncensored calibration observations only, then report supported POD queries and independent holdout classification, log-score, Brier and residual diagnostics. Preserve censored/missing observations without substitution and do not claim code acceptance or field detection probability.",
    "reviewed_ctmc_transition_count_exposure_observations": "Estimate directed continuous-time transition rates as weighted calibration counts divided by weighted origin-state exposure and construct the aligned zero-row-sum generator. Evaluate holdout count likelihood without clipping zero-rate contradictions; do not propagate future reliability, infer repair policy, construct FTA probabilities or claim stationary causal physics.",
    "reviewed_atmospheric_first_year_time_transfer_envelope": "Apply the caller-qualified transfer identity loss(t)=loss at one year times t raised to a caller-supplied exponent only at ordered supported exposure times. Preserve material, surface, exposure-zone, climate/pollutant descriptors, provider digests and independent calibration/holdout evidence; do not infer climate effects, extrapolate, or create localized penetration, acceptance, life or probability.",
    "reviewed_temperature_dependent_parabolic_oxidation_rate_table": "Split a piecewise-linear temperature history at caller-owned rate-table knots and exactly integrate the linearly interpolated parabolic coefficient to obtain the oxide-thickness-squared increment. Do not extrapolate or infer spallation, breakaway oxidation, metal consumption, acceptance, remaining life or probability.",
    "reviewed_binary_event_pair_calibration_holdout_observations": "Form a weighted binary 2-by-2 event table from explicitly partitioned calibration observations and report marginals, joint frequency, covariance, phi and holdout category scores. Preserve physical sequence and independence groups; do not claim causality, independence, future-period probability or automatic FTA suitability.",
    "reviewed_insulation_condensation_exposure_accounting": "Account for recorded intervals where an insulation outer-surface temperature is at or below the independently supplied ambient dew point while a caller-mapped weather-barrier state permits moisture. Keep missing coverage and uncertainty margins explicit; do not infer water ingress, corrosion, coating failure, acceptance, remaining life or probability.",
    "normalized_absolute_error": "For each predeclared experiment, divide aligned absolute mean and amplitude residuals by separate caller-supplied positive scales, combine them with nonnegative weights summing to one, average over that experiment's supplied cycles and then average experiments equally. Never infer a possibly zero normalizer, resample cycle histories or treat the score as model validity.",
    "root_mean_square_log_error": "For a complete predeclared set of unique cases with positive observed and predicted lives, form one signed logarithmic residual per case and return the square root of their mean squared value. Preserve every residual and reject censored or missing outcomes rather than substituting a number.",
    "dynamic_modulus_endpoint": "Compare a strictly cycle-ordered compressive-branch dynamic-modulus history with a caller-declared positive reference times one minus a caller-declared loss fraction. Report the first observed threshold crossing or, only under an explicit policy, a linear interpolation inside its first descending bracket. A closed no-crossing history remains right-censored; an open window remains incomplete.",
    "portable_crack_growth_scenario_reduction": "Split a reviewed complete-input crack-growth ensemble into independently schedulable rows and bind every external evaluation to its scenario ID, canonical deterministic-input digest, evaluator identity, evaluator revision, evaluator-configuration digest and result digest. Before reduction, require unique manifest and evaluation identities, exact set coverage, a common physical scope, normalized manifest weights and exact input/evaluator matches. Preserve manifest order. Retain invalid, failed, needs-data and out-of-scope evaluations and withhold all aggregate statistics instead of filtering or renormalizing them. Do not infer scheduler correctness, scenario probabilities, model-form validity, period failure probability, FTA basic-event probability, confidence bounds or acceptance.",
    "complete_crack_growth_scenario_ensemble": "Accept two or more caller-reviewed normalized weighted scenarios, each containing a complete deterministic single-curve or curve-family crack-growth input and its own joint source identity and digest. Require a common physical scope while allowing joint changes to individual curve points, curve-family composition, geometry knots, ordered load blocks, toughness and numerical controls. Preserve the canonical digest and result of every complete input. Form weighted moments, discrete inverse-CDF quantiles and declared-depth exceedance mass only when every scenario computes. Never generate, fit, normalize, interpolate between, discard or assign probabilities to scenarios, and never relabel their push-forward mass as a period first-failure probability, FTA basic-event probability, model-form validation, confidence bound or code acceptance result.",
    "crack_growth_uncertainty_convergence_diagnostic": "Compare two or more ordered caller-reviewed uncertainty sample designs for one distribution and one deterministic crack-growth input. Preserve every level, its source digest and its declared relationship to the prior level. For nested refinement, require strictly more rows and retain every prior sample identity and multiplier tuple while allowing normalized weights to change. Compare weighted mean, standard deviation, discrete quantiles and declared-depth exceedance mass using caller-reviewed tolerances and a positive physical depth scale. Never discard failed rows or levels, and never describe satisfied diagnostics as a convergence proof, error bound, sample-size guarantee, distribution validation, period failure probability or FTA basic-event probability.",
    "joint_crack_growth_uncertainty_propagation": "Accept caller-reviewed normalized joint rows containing global multipliers for crack-growth rate, geometry factor, tensile stress and fracture toughness. Preserve sample identity, row weight, distribution and design identities, source digest and the declared dependence represented by each row. Evaluate every row through the unchanged deterministic model, then form weighted moments, discrete inverse-CDF quantiles and a declared-depth exceedance mass only when every row remains in scope. Never generate or refit samples, normalize weights, discard failures, or relabel the push-forward input-uncertainty probability as a period first-failure probability, observed frequency, FTA basic-event probability, confidence bound or model-form uncertainty.",
    "tabulated_curve_family_selection_derivation": "Require every curve in a family to share one reviewed material condition and environment while retaining unique curve and source identities. For each ordered tensile block, compare stress ratio by absolute difference and frequency by relative difference against caller-declared tolerances. Select only the unique minimum normalized distance inside both tolerances; stop when no candidate or an equal-distance tie remains. Do not interpolate, average or fit across stress ratio, frequency, environment, material condition or source group.",
    "tabulated_growth_interpolation_derivation": "Preserve a caller-authorized positive da/dN-versus-delta-K table, material condition, environment, stress ratio, frequency, source digest and applicability review. Interpolate linearly only between adjacent points in log(delta K)-log(da/dN) coordinates. For a reviewed nondecreasing geometry-factor table and ordered tensile blocks, integrate dN=da/(da/dN) within the curve support, split at geometry and curve knots, and invert the monotone cycle integral for depth. Keep curve support, maximum-K toughness and declared depth terminations distinct; do not infer a threshold, extrapolate, fit a design curve, model closure or retardation, or create acceptance or failure probability.",
    "liquid_penetrant_examination_definition": "Preserve one caller-controlled penetrant procedure and revision, visible or fluorescent system, removal method, consumable batch identities, material and surface condition, precleaning and drying bases, absolute examination temperature, penetrant dwell, excess-removal basis, developer application and development time, observation lighting, final cleaning, mutually exclusive coverage areas and evidence-bound reported indications. Missing review gates or an unreviewed empty indication list remain needs-data. Process records do not establish procedure compliance, indication relevance, flaw dimensions, acceptance, probability of detection, remaining life or failure probability.",
    "magnetic_particle_examination_definition": "Preserve one caller-controlled magnetic-particle procedure and revision, material and surface condition, particle/carrier batch, observation lighting, physical coverage areas, evidence-bound reported indications and uniquely identified magnetization passes. Each pass retains technique, current mode, unoriented field direction on a half-circle, field-adequacy basis, equipment and optional current magnitude. Compare each area's maximum acute separation only with a caller-declared reviewed minimum; zero or one direction remains insufficient. Ferromagnetic applicability, field adequacy and directional records do not establish procedure compliance, subsurface sensitivity, indication relevance, acceptance, probability of detection, remaining life or failure probability.",
    "visual_surface_examination_definition": "Preserve a caller-controlled visual-examination procedure and revision, direct or remote mode, surface preparation and condition, illumination and resolution-check bases, mutually exclusive physical target areas, examined area and explicit reasons for incomplete coverage. Bind each uniquely identified reported indication to one declared area and physical location with its own evidence, retaining optional reported dimensions without inventing them. Compute coverage and descriptive counts only after named review gates. An empty indication list requires a separately reviewed negative-result statement. Coverage or a negative record does not establish flaw absence, probability of detection, code acceptance, severity, repair disposition, remaining life or failure probability.",
    "radiographic_examination_geometry_definition": "Preserve one caller-controlled radiographic procedure and revision, physical scope, material condition, mutually exclusive X-ray or gamma source identity, exposure, detector, immutable image identity, image dimensions, image-quality indicator records and evidence-bound image-space indications. Require object mapping to carry a physical location and mapping basis together. Compute pinhole magnification, focal-spot geometric unsharpness and object-plane pixel pitch only from explicitly supplied geometry. Missing geometry, review gates, unreviewed image-quality records, unmapped indications or an unreviewed empty indication list remain needs-data. Projection descriptors do not establish total resolution, procedure compliance, flaw identity or size, acceptance, probability of detection, remaining life or failure probability.",
    "phased_array_acquisition_definition": "Preserve one caller-controlled phased-array procedure and revision, physical scope, material condition, specimen wave velocity and basis, probe element layout, wedge identities, focal laws, calibrated encoder direction, immutable frame hashes and evidence-bound indications. Support pulse-echo or separate transmit/receive probes and conventional beam-law or full-matrix capture records without converting one into the other. Preserve frame order and duplicate encoder positions. Compute only physical aperture, nominal specimen wavelength, pitch ratio, delay spans and encoder-spacing diagnostics. Do not synthesize missing delays, sort or resample waveforms, reconstruct TFM images, infer flaw size, apply acceptance limits, or create detection, life or failure probabilities.",
    "tofd_acquisition_definition": "Preserve one caller-controlled TOFD procedure and revision, physical scope, material condition, distinct transmit/receive probe and wedge identities, measured probe-index separation, specimen longitudinal velocity and wall-thickness bases, calibrated encoder direction, immutable frame hashes, same-frame lateral/backwall arrival picks and evidence-bound upper/lower diffraction picks. Under an explicitly reviewed symmetric straight-path assumption, compute only lateral/backwall path descriptors, pick depths relative to the same-frame lateral wave, paired-tip separation and encoder-spacing diagnostics. Keep missing or noncausal reference picks and reversed tip ordering visible. Do not process waveforms, automate time picking, qualify near-surface or backwall dead zones, infer flaw identity, apply acceptance limits, or create POD, life or failure probabilities.",
    "eddy_current_acquisition_definition": "Preserve one caller-controlled eddy-current procedure and revision, physical scope, material condition, probe mode, coil/channel identities, excitation frequencies, lift-off basis, physical reference-standard features, immutable encoded-scan hashes and evidence-bound indications. Require exact probe and frequency coverage by the reference standard and preserve signal-component order and caller-reviewed raster coordinates. Compute only scan extents and, when explicitly applicable with reviewed conductivity, relative permeability and temperature, the classical linear homogeneous skin-depth descriptor. Do not rotate, mix, filter or threshold signals, infer lift-off or defect dimensions, apply acceptance limits, or create POD, remaining-life or failure-probability claims.",
    "magnetic_flux_leakage_acquisition_definition": "Preserve one caller-controlled magnetic-flux-leakage procedure and revision, physical scope, material and surface condition, magnetizer identity and direction, calibrated sensor arrays and component mapping, physical reference-standard features, reviewed H/B field-state checkpoints, immutable encoded-scan hashes and evidence-bound indications. Require exact magnetizer and sensor-array coverage by the reference standard and preserve active channels, pass direction, speed and caller-reviewed encoder coordinates. Compute only encoded span, vector magnitudes and an explicitly non-constitutive B/H magnitude ratio. Do not infer saturation, field uniformity or flaw sensitivity, remove baselines, compensate velocity or lift-off, fuse signals, detect, classify, size, apply acceptance limits, or create POD, remaining-life or failure-probability claims.",
    "pulse_echo_sound_speed_fit_derivation": "With a caller-reviewed fixed time-zero offset and incidence angle, convert each positive round-trip time to one-way path time and fit reference thickness as sound speed times that coordinate through the physical zero. Use only predeclared calibration locations and source groups, then evaluate untouched holdout locations and groups. Ordinary fitting reports residual-conditional uncertainty. The optional iterative effective-variance fit weights each row by the sum of declared independent thickness variance and slope-scaled time variance, reports reduced chi-square and evaluates standardized holdout residuals. Return an explicitly unreviewed calibration fragment with no sample applicability. Neither fit covers shared time-zero, angle, temperature, coupling, probe, material-heterogeneity or model-form uncertainty and neither by itself qualifies field thickness measurements.",
    "atmospheric_first_year_loglinear_fit_derivation": "Transform reviewed positive first-year average atmospheric carbon-steel loss to log metres and regress it on a fixed five-column design: intercept, centered/scaled absolute temperature, centered/scaled relative humidity, log1p chloride deposition and log1p sulfur-dioxide deposition. Fit only predeclared calibration source groups by ordinary least squares and evaluate untouched holdout source groups. Preserve calibration support, conditional coefficient covariance and predeclared transfer criteria. This screening relation is not wet-CO2 corrosion, localized penetration, multi-year growth, remaining life, code acceptance or failure probability.",
    "atmospheric_first_year_loglinear_prediction_derivation": "Evaluate the fixed atmospheric log-linear feature vector and exponentiate the predicted log loss. Form a conditional prediction interval from coefficient covariance plus residual variance. Stop outside calibration support unless extrapolation is reviewed, and stop when source-separated transfer criteria failed unless a limited-transfer override is explicitly reviewed. The interval excludes covariate, source, model-form and population uncertainty.",
    "authored_atmospheric_scenario_ensemble": "Evaluate every first-year atmospheric scenario through the registered prediction model, preserving each input and output digest. Summarize caller-normalized scenario weights with a weighted arithmetic mean, range, and weighted empirical quantiles. Do not infer the meaning of weights, dependence, multi-year growth, localized penetration, remaining life, acceptance, or failure probability.",
    "gaussian_mean_shift_importance_sampling_derivation": "For a target vector of independent standard-normal latent coordinates and a proposal with the same unit covariance plus a caller-declared mean shift, evaluate the exact log likelihood ratio as minus the shift dot the proposal sample plus one half the squared shift norm. Average the likelihood ratio times a separately evaluated binary event indicator without clipping or self-normalizing. Compute finite-sample variance, normal-approximation interval, normalized-weight effective sample size and event-weight effective sample size as Monte Carlo diagnostics. Preserve the latent mapping, event, physical scope, horizon, survival conditioning, design and evaluator identities. Independence in latent coordinates does not assert independence of mapped physical inputs; estimator diagnostics do not cover input-distribution, mapping, evaluator, model-form, physical-data or consequence uncertainty.",
    "guided_wave_reference_ensemble_definition": "For one physical specimen, require at least three uniquely identified caller-selected baseline acquisitions plus a distinct observation, one exact frequency/mode channel, aligned nondecreasing provider distance grids, explicit source groups, selection basis, spatial window and repeated-distance policy. Form a pointwise mean or median reference, quantify baseline spread and leave-one-out residual RMS, then compare the observation with that reference without interpolation, sorting or probability conversion. These ratios describe the selected acquisition ensemble only; they are not an anomaly probability, POD, acceptance threshold, defect dimension, remaining thickness, life or failure probability, and repeated records from one specimen do not establish independent validation or separate coupling/environment effects from damage.",
    "guided_wave_pair_feature_definition": "For one physical specimen, one frequency and one propagation-mode voltage channel, require separate baseline and observation acquisition identities and aligned nondecreasing provider distance grids. Select only the caller-declared inclusive spatial window without interpolation or sorting. Preserve or explicitly reject repeated distances, or average only contiguous aligned duplicate pairs under a named policy. Report raw RMS, paired residual RMS, normalized residual, energy ratio, correlation and peak/mean difference while retaining undefined normalized quantities for a zero baseline. These descriptive features do not identify machining steps, remaining thickness, defect geometry, POD, acceptance, life or failure probability, and a single baseline does not separate environmental, coupling and damage effects.",
    "threshold_inspection_schedule_definition": "Preserve one reviewed cumulative first-crossing probability curve, event definition, physical scope, survival conditioning, forecast model revision and input digest. Inside caller-declared notice and maximum-deferral limits, select the latest supplied candidate whose estimate or supplied upper bound satisfies a user-approved probability criterion. Refuse mixed or nonmonotone probability curves, incomplete upper bounds and missing review gates. Do not interpolate between times, extrapolate beyond forecast support, optimize consequence, infer inspection effectiveness or convert a point-in-time state probability into a first-crossing probability.",
    "inspection_action_expected_loss_definition": "For one reviewed event, physical scope, horizon, survival conditioning and common cost basis, preserve exactly one zero-action-cost baseline and one or more complete intervention alternatives. Every action retains its definition, effect-model identity, revision, input digest, residual conditional first-failure probability estimate and optional upper bound. Add reviewed action-cost components to residual event probability times reviewed conditional consequence components, compare point-estimate or complete upper-bound totals, and withhold arbitrary selection when totals tie within a caller-declared absolute tolerance. Do not infer action effectiveness, event probabilities, dependencies, costs, consequences, risk tolerance, resource feasibility, value of information, regulatory acceptance or validation of the supplied models.",
    "inspection_disposition_tree_definition": "For one inspection action and one common event, scope, horizon, survival conditioning and cost basis, require a caller-reviewed mutually exclusive exhaustive outcome partition. Preserve every outcome probability, disposition identity and definition, disposition-effect model revision/configuration/input/result digests, conditional residual first-failure probability and additive disposition costs. Form only the finite probability-weighted expected disposition cost and residual event probability, then expose a digest-bound estimate-basis action candidate. Missing review gates withhold arithmetic and probabilities must sum to one within a caller tolerance. Do not infer branch probabilities from POD or false-call data, invent dispositions, produce confidence bounds, optimize a multi-period policy or claim regulatory acceptance.",
    "multi_period_inspection_policy_definition": "For one fixed externally generated multi-period inspection policy, require a complete reviewed finite path manifest over one event, physical scope, horizon, start-survival condition, cost basis and discount basis. Preserve each path probability and source digest, every ordered observation/action stage and its model revision/configuration/input digests, every action-cost component and caller-supplied present-value factor, and the first-failure time and consequence factor exactly when failure occurs. Compute only pathwise discounted costs and their finite probability-weighted expectations. Reject incomplete probability mass, duplicate identities, stages outside the horizon or after first failure, and missing review gates. Do not infer transitions, observations, probabilities, discount factors, consequences, confidence bounds, policy optimality, resource feasibility or regulatory acceptance.",
    "multi_period_inspection_policy_comparison_definition": "Compare at least two complete externally evaluated multi-period policies only after confirming a common event, physical scope, horizon, start-survival condition, cost basis, currency or normalized unit and discount basis. Preserve every policy and evaluator identity plus configuration/input/result digests, conditional first-failure estimate and optional qualified bound, additive expected-loss components and the exact declared resource set with units and optional bounds. Apply caller-approved hard probability and resource constraints before comparing expected total loss; never relax a constraint when no policy is compliant or break a cost tie arbitrarily. The unique least-loss compliant candidate is only the best member of the supplied reviewed set. Do not generate policies or transitions, infer probabilities, resources, bounds, constraints or costs, claim global optimality, resource scheduling, risk acceptance or regulatory compliance.",
    "finite_inspection_policy_path_generation_definition": "Expand a caller-reviewed finite policy definition over strictly ordered decision epochs. Require uniquely defined failure and nonfailure states, a complete initial distribution conditional on start survival, state-conditional observation distributions, one deterministic action for every observation, complete action definitions with model and cost identities, and state-action transition distributions. Every probability family must sum to one within a declared tolerance, failure consequence factors occur exactly on transitions into failure, and failure paths stop immediately. Enumerate every positive-probability path as the exact product of supplied table entries and preserve a digest of its full trace; omit only zero-probability branches. Stop with an explicit out-of-scope result before exceeding the caller path-count limit. Do not fit or infer states, observations, transitions, decisions, probabilities, costs or optimality, and do not treat reviewed tables as empirical validation.",
    "finite_policy_probability_calibration_definition": "Estimate finite state-conditional observation probabilities and action-conditioned state-transition probabilities from caller-reviewed weighted records. Require explicit physical-state truth, inspection labels, action assignments, ordered transition intervals and immutable calibration or holdout membership. Reject any sequence or source group crossing between partitions. Apply only a caller-declared symmetric pseudocount, report unsupported conditioning rows instead of inventing them, and score untouched holdout records with multiclass Brier score and negative log likelihood. Preserve exactly zero holdout probabilities as a diagnostic rather than clipping them. Do not infer record independence, confidence intervals, state definitions, labels, actions, feature matching, physical truth, transition causality or field applicability.",
    "burst_prediction_comparison_definition": "Preserve each reviewed experimental burst endpoint, physical specimen, source group, partition, material, geometry, load case, pressure basis, source hash and prediction-input digest. Require authorized observation use, one row per physical specimen, matching observed/predicted pressure bases, a prediction frozen before evaluation and no source group crossing from calibration into evaluation. Report pointwise predicted-to-observed ratios and separate calibration, holdout and external-validation descriptive summaries. These errors do not supply a pressure model, standard limit, safety factor, prediction interval, population coverage, remaining life or failure probability.",
    "hydrogen_slab_flow_multiplier_fit_derivation": "Preserve a reviewed signed outward hydrogen-atom flow series, exact elapsed-time alignment, physical slab area and a predeclared calibration/holdout partition. Apply one positive multiplier to one named complete transport-parameter history while fixing every other initial, geometric, boundary and trap input. Run the conservative planar forward solver inside bounded nonlinear least squares using calibration rows only; evaluate holdout residuals after fitting. Report local log-multiplier sensitivity, conditional uncertainty, boundary activity, the fitted reusable slab contract and its digest. This restricted profile does not establish global identifiability or cover fixed-input, model-form, detector, clock or source-group uncertainty.",
    "hydrogen_reduced_surface_reaction_derivation": "At each reviewed temperature knot, evaluate separate Arrhenius limiting absorption and desorption atom-molar flux capacities in log space. Multiply the absorption capacity by the square root of caller-supplied hydrogen fugacity divided by a declared reference fugacity, or use hydrogen partial pressure only after an explicit ideal-gas approximation review. Define the reduced net inward surface flux as J_abs times one minus lattice-surface occupancy minus J_des times lattice-surface occupancy. Algebraically eliminate the surface occupancy against the adjacent half-cell Fickian resistance, preserving signed flux and total atom inventory. This effective one-state boundary is not a full adsorption microkinetic model, a bulk solubility relation or a parameter inference method.",
    "hydrogen_thermal_rate_fit_derivation": "Transform reviewed positive rate observations to log frequency versus inverse temperature. For Arrhenius fitting use log(k)=log(A)-E/(RT). For fixed-transmission transition-state fitting use log[k h/(kappa k_B T)]=DeltaS/R-DeltaH/(RT). Fit only caller-labelled calibration rows with a centered and scaled weighted two-column design, transform the coefficient covariance to physical parameters, and evaluate untouched holdout rows only inside calibration temperature support. A rate-only transition-state fit cannot separate transmission coefficient from activation entropy, and conditional regression covariance excludes model-form, source-group and transport-inversion uncertainty.",
    "hydrogen_detector_observation_derivation": "For a reviewed signed outward hydrogen-atom molar flow, apply the declared electron-per-hydrogen-atom stoichiometry, current efficiency and exact-SI Faraday constant to form the ideal electrochemical current, or multiply by atomic molar mass and divide by reviewed sample mass to form a mass-normalized ppm rate. Preserve negative values and integrate only on the declared elapsed-time knots. This algebraic forward observation identity has no detector lag, gas-line volume, pumping, recombination, adsorption, noise, uncertainty or inverse boundary inference.",
    "cavitation_history_definition": "For each aligned reviewed sample subtract equilibrium vapor pressure from local absolute static pressure. On every declared linear time segment, locate zero-margin crossings exactly, union contiguous nonpositive-margin intervals and integrate the clipped negative linear margin as pressure-deficit exposure. Duration and pressure deficit are sampling-dependent screening descriptors, not nuclei, inception, collapse energy, erosion damage, life or probability.",
    "cavitation_margin_definition": "Subtract equilibrium vapor pressure from caller-reviewed local absolute static pressure. Divide that signed margin by liquid specific weight for static head and by one-half density times the square of a caller-defined characteristic velocity for a local cavitation number. A nonpositive thermodynamic margin does not predict nuclei, transient inception, bubble collapse, erosion, material damage, life, failure probability or acceptance.",
    "hemisphere_plane_grid_derivation": "Represent each unoriented material plane once by a unit normal on the closed upper hemisphere. Sample polar latitude uniformly from the pole through the equator and azimuth uniformly around intermediate latitudes; retain one pole and half the equatorial azimuths to remove exact n versus minus-n duplicates. Construct a deterministic in-plane unit direction from the least-aligned Cartesian axis. This finite latitude-azimuth grid is not equal-area and its nominal angular increments are not a coverage-error bound, convergence proof or continuous optimum.",
    "area_uniform_fibonacci_plane_grid_derivation": "Represent each unoriented plane once with a normal strictly inside the positive-z hemisphere. Partition the hemisphere into equal increments of z, place one normal at each stratum midpoint, and advance its azimuth by the golden angle with a caller-controlled phase. Assign the hemisphere area divided by point count only as a nominal quadrature weight. This deterministic area-stratified sequence is not an exact equal-area Voronoi tessellation, a nested refinement, a covering-radius bound or a continuous orientation optimum.",
    "critical_plane_tensor_projection": "For every caller-declared orthonormal normal n and in-plane direction m, independently project a symmetric local stress or small-strain tensor as n dot T dot n and m dot T dot n. Convert tensor shear strain to engineering shear strain by a factor of two, form half ranges over one reviewed closed representative cycle, and evaluate only the declared finite candidate set. Endpoint Frobenius errors qualify cycle closure. No continuous orientation optimization, rainflow extraction, notch solution, calibration, fatigue life or acceptance rule is inferred.",
    "critical_plane_vector_chord_projection": "For each caller-declared orthonormal plane frame, independently project the symmetric tensor path onto two in-plane shear directions. Form the exact maximum pairwise Euclidean chord of the sampled engineering-shear vectors and use half that named chord as a discrete amplitude. The Euclidean result is invariant to rotation or reversal of the supplied in-plane basis. Preserve chord endpoint sample identities and distinguish this O(n squared) sampled-path definition from continuous-time extrema, a minimum enclosing circle, rainflow extraction, continuous plane optimization, fatigue-life calibration and acceptance.",
    "critical_plane_minimum_enclosing_circle_projection": "For each caller-declared orthonormal plane frame, project the sampled symmetric tensor history into two in-plane shear components. Construct a deterministic finite-point minimum enclosing circle from one-point, diameter and three-point circumcircle supports, retaining up to three support sample identities and center components in the supplied frame. Use its radius as the sampled engineering-shear amplitude and report half the maximum sampled pairwise chord separately. Radius is invariant to in-plane rigid coordinate changes, but this order-insensitive finite point-set range does not bound an unsampled path, count cycles, prove orientation convergence or qualify fatigue life.",
    "critical_plane_grid_refinement_diagnostic": "Evaluate one reviewed tensor cycle independently on an explicitly ordered sequence of finite unoriented-plane grids. Between successive grids, normalize each FS and SWT maximum change by the larger absolute value and compute the acute angle between the selected unoriented plane normals. Compare those observations with caller-declared diagnostic tolerances. A finite sequence and a satisfied last-step tolerance do not bound the unsampled orientation error, prove convergence, resolve time discretization or qualify fatigue life and experiment agreement.",
    "critical_plane_time_refinement_diagnostic": "Hold one finite plane set fixed while evaluating explicitly ordered, strictly increasing and time-nested samplings of the same reviewed tensor cycle. Record each sampling interval, discrete FS/SWT maxima, selected unoriented normals and successive relative-factor and acute-plane-angle changes. Nested sampled histories and satisfied caller tolerances do not bound extrema between samples, prove temporal or orientation convergence, qualify fatigue life or establish experimental validity.",
    "critical_plane_grid_family_comparison_diagnostic": "Evaluate one reviewed sampled tensor cycle with at least two uniquely identified finite latitude-azimuth and/or area-stratified Fibonacci candidate sets. Preserve each generator definition, sampled FS/SWT maxima and selected normals. Relative to one caller-named finite reference grid, report normalized factor differences and acute angles between unoriented selected normals. Cross-grid agreement is not an orientation-error bound, continuous optimum, temporal convergence, fatigue-life calibration or experimental validation.",
    "critical_plane_adaptive_search_diagnostic": "Start from separate FS and SWT maxima on one caller-declared finite seed grid. For each objective independently, retain the current center and evaluate a deterministic tangent-plane ring whose angular radius follows a declared shrinking schedule. Preserve every radius, candidate count, selected unoriented normal, objective change and acute plane movement. This greedy local search can miss another maximum; a stable final step is not a global optimum, convergence proof, fatigue-life calibration or experimental validation.",
    "annular_section_equilibrium": (
        "Nominal axial stress is force divided by annular area and Saint-Venant torsional shear "
        "is torque times radius divided by the annular polar second moment; geometry and loads are "
        "supplied by the caller."
    ),
    "linear_elastic_fracture_ratios": "Independently form Kr from caller-supplied effective mode-I stress intensity and fracture resistance, and Lr from caller-supplied reference stress and normalizing strength. Preserve the geometry, load case, location, material and solution identities. These normalized coordinates do not establish test validity, constraint, load interaction, remaining life or failure probability.",
    "user_supplied_failure_assessment_boundary": "Interpolate only within a caller-licensed nonincreasing piecewise-linear Kr-versus-Lr boundary. Require explicit evidence and applicability review, retain the final supported Lr, and leave points beyond it outside scope. No standard curve, cutoff, safety factor, acceptance table or residual-stress interaction rule is bundled.",
    "user_supplied_pressure_temperature_envelope": "Interpolate pressure limits only between strictly increasing absolute-temperature knots supplied and reviewed by the caller. Preserve the applicability basis and content digest, compare identified operating points without extrapolation, and report pressure margin and utilization separately. No design-code table, service-category rule, load combination, uncertainty factor or acceptance decision is bundled.",
    "signed_interpolant_balance": "Independently form the area-scaled sum of signed net electrode-current interpolants on their common potential support. The union of knots partitions the balance into linear segments; retain every isolated zero and contiguous zero interval. Normalize finite currents, check cancellation and final residuals, and select a scalar result only for one numerically resolved root with no zero intervals. Do not extrapolate, convert potential references automatically, equate net current to metal-dissolution current, or infer physical stability and failure probability.",
    "authored_chronoamperometry_window_contract": "Independently summarize one provenance-bound, strictly time-ordered current trace over caller-declared analysis and optional baseline windows. Preserve the reviewed seconds, amperes, current sign, physical specimen, source group and source digest. Use either exact observed endpoints or explicit piecewise-linear boundary interpolation; integrate signed current and absolute piecewise-linear magnitude while retaining extrema plateaus. Do not filter, classify events, infer metal loss or pit dimensions, pool map points as specimens, or produce POD, life, acceptance or failure probability.",
    "sobol_design_quality_contract": "Independently compose paired native-unit A/B matrices from a 2d scrambled Sobol sequence, replacing one A column by its B counterpart for each mixed block. Preserve prefixes at declared power-of-two sizes. Bind every response to the design digest, replicate, block and point identity, and retain failed/missing states without subset filtering. Normalize complete finite outputs for representability, call SciPy estimators, and summarize independently randomized replicates with approximate t intervals plus explicit nested-size and theoretical-bound diagnostics. Repeat checks do not prove determinism, hashes do not certify execution, and numerical intervals do not cover model-form or marginal-estimation uncertainty.",
    "hydrogen_partition_derivation": "For fixed independent sites, lattice log odds u imply trap occupancies expit(u+E/RT). Solve summed atom concentration (or vacancies near filling) in log space. Differentiate trap occupancy with respect to lattice occupancy to obtain the local differential storage factor and D_L divided by that factor. No constant global effective diffusivity, gas solubility, kinetic barrier or fracture rule is inferred.",
    "hydrogen_bakeout_slab_derivation": "Transform the one-dimensional diffusion equation with spatially uniform time-dependent effective diffusivity by the cumulative diffusion time integral. For a finite slab with initially uniform diffusible concentration and zero concentration on both faces, evaluate the odd eigenfunction series for the volume-mean remaining fraction. Integrate caller-supplied piecewise-linear diffusivity exactly by the trapezoid rule at declared time knots and bound the omitted positive series tail. Preserve temperature as procedure evidence rather than generating hidden material properties. Do not infer diffusivity, traps, weld heterogeneity, surface kinetics, hydrogen cracking, procedure qualification or acceptance.",
    "hydrogen_slab_fvm_derivation": "Independently derive cell-average conservation on a uniform planar grid. Use half-cell distances at prescribed surfaces, zero normal flux at sealed surfaces, or combine a declared linear transfer or reduced reversible surface-reaction conductance with half-cell diffusion resistance. For each trap either derive the release/capture ratio from a reviewed binding-energy convention or interpolate separately reviewed capture and release histories without overwriting them from temperature. Eliminate each fixed-site backward-Euler kinetic state algebraically, then solve the monotone tridiagonal lattice residual with a bounded Newton iteration. Compare one full step with two half steps for occupancy and boundary-exchange error control; retain the two conservative half steps and their signed surface exchanges. Prescribed histories are piecewise linear, densities fixed, temperature spatially uniform. Check global inventory against surface exchanges; temporal local control does not prove spatial/global accuracy.",
    "hydrogen_finite_cylinder_fvm_derivation": "Independently derive axisymmetric cell-volume conservation on a finite radial-axial cylinder. Use annular cell volumes, cylindrical radial-face areas, planar end areas, axis symmetry, and half-cell distances at the curved wall and ends. Keep all three physical surfaces distinct and optionally combine each declared linear transfer or reduced reversible surface-reaction conductance with its half-cell diffusion resistance. For each trap either derive the release/capture ratio from a reviewed binding-energy convention or interpolate separately reviewed capture and release histories without overwriting them from temperature. Eliminate local fixed-site backward-Euler trap states, solve the sparse bounded Newton system, retain conservative step-doubling surface exchanges, and check total atom-mole inventory. Radial and axial mesh refinement remains a caller responsibility.",
    "arrhenius_frequency_history_derivation": "Evaluate each caller-reviewed absolute prefactor and activation energy in logarithmic form at aligned absolute-temperature knots. Refuse unsupported temperatures and nonrepresentable positive frequencies instead of clipping to zero or infinity. Preserve parameter and history digests; piecewise-linear downstream interpolation remains distinct from continuously reevaluating the thermal law.",
    "hydrogen_thermal_rate_contract": "Preserve trap, material, lattice, energy-reference and elapsed-time identities while producing separate capture and release frequency histories from reviewed single-path Arrhenius or transition-state parameterizations. Return a JSON-composable independent-frequency trap fragment and the diagnostic minus R T log of the release-to-capture ratio. This diagnostic is not relabelled as a measured trap binding energy, and the contract does not infer atomistic parameters, select mechanisms or fit observations.",
    "transient_fvm_enthalpy": "Independently balance cell enthalpy against face conduction, signed boundary heat, optional distributed convection and volumetric generation. Use planar or radial cell volumes, series face resistances, backward Euler time integration and a linear-work tridiagonal solve. Integrate linearly tabulated volumetric heat capacity to enthalpy and refuse property extrapolation. Iteratively linearize temperature-dependent properties and gray-surface radiation; report discrete energy residuals separately from geometry, property and experiment qualification.",
    "thermoelastic_section_resultants": "Independently integrate a piecewise-linear through-wall temperature and caller-supplied elastic-property profile under a plane-section assumption. Either solve membrane strain and curvature from declared force and moment resultants or evaluate declared kinematics. Retain one-direction versus equi-biaxial plane-stress modulus, elastic-limit screening and force/moment residuals. Do not infer pressure, discontinuity, plasticity, creep, fracture or code stress classification.",
    "creep_aft_likelihood": "Natural log lifetime has a stress-power/optional reciprocal-temperature mean and common Gaussian scatter. Sum failure log densities plus right-censored log survivals; use scaled full-rank features and observed information. Conditional failure is one minus the survival ratio, evaluated using stable normal-tail functions or the integrated Mills ratio for short intervals.",
    "piecewise_linear_loss_geometry": "For a nodal axial window of length L and reference wall t, integrate the piecewise-linear depth to obtain A and define alpha=A/(tL). Combine the area ratio with separately supplied pressure and bulging providers; no normative coefficients are embedded.",
    "independent_area_maxima": "For k independent equivalent surface blocks at the same exposure, P(max<=d)=F(d)^k. A Gumbel maximum law shifts location by scale*log(k); no time-growth or structural-failure law is inferred.",
    "declared_impact_transition": "Fit a nonnegative lower shelf and positive upper-minus-lower energy to an increasing logistic temperature relation within one declared series; do not infer toughness or a specimen-size transformation.",
    "declared_interval_comparison": "Compare a supplied observation interval to a supplied acceptance interval: containment, disjointness or unresolved boundary crossing. No acceptance values are bundled.",
    "explicit_identity_mapping": "Resolve an exact caller-reviewed designation tuple and retain mapping evidence; do not infer fuzzy matches, substitutions or transitive equivalence.",
    "dimensional_budget": "Subtract manufacturing dimensional allowance, then apply a declared fractional forming loss, then reserve future corrosion thickness; measured postfabrication dimensions take a separate path.",
    "line_geometry": "Fit two local surface lines outside an excluded joint zone; compare their zero-position intercepts and tangent angles.",
    "charge_budget": "Exactly integrate the product of linearly varying exposed fraction and current density plus linear drain; compare charge capacity and a separate peak-current output bound.",
    "mechanical_path_work": "Integrate stress against ordered strain increments using linear segments; only explicitly declared, sufficiently closed cycles receive closed-cycle work.",
    "linear_circuit_equilibrium": "Potential difference divided by electrode area-scaled polarization resistances and electrolyte resistance; declared linearity domain checked separately.",
    "parabolic_kinetics": "Integrate a declared inverse-thickness scale growth rate to obtain squared thickness linear in exposure; no material parameters bundled.",
    "archard_relation": "Caller-calibrated dimensionless coefficient multiplies normal work divided by hardness to obtain wear volume.",
    "discrete_geometry": "Equal-area measured cells, missing-area accounting and explicit four-neighbour connectivity; no structural acceptance criteria.",
    "rectilinear_cell_area_geometry": "Cell areas follow caller-supplied rectilinear edge intervals; observed-cell summaries retain missing coverage, signed thickness loss and explicit four-neighbour threshold components without interpolation or structural acceptance criteria.",
    "offset_intersection": "Intersect the piecewise-linear measured stress-strain branch with a caller-declared parallel elastic offset line.",
    "declared_rockwell_depth_scale": "Caller-declared scale offset minus permanent depth increment divided by caller-declared depth per scale unit. Independent arithmetic; NIST SP 960-5 explains the depth-scale principle (https://doi.org/10.6028/NBS.SP.960-5). No scale/load/acceptance table reproduced.",
    "indentation_geometry": "Force divided by ideal diamond or spherical indentation area, with standard gravity converting newtons to conventional kilogram-force reporting. Knoop rhombic geometry uses explicit caller edge angles; see NIST SRM 2828 certificate, equation 1 (https://tsapps.nist.gov/srmext/certificates/2828.pdf).",
    "gas_inventory_balance": "Endpoint molar inventories follow PV=ZnRT; pressure-rise throughput follows an isothermal rigid-volume balance.",
    "lumped_heat_balance": "Solve a first-order solid heat-capacity balance against a constant convection boundary and report Biot applicability.",
    "piecewise_linear_history": "Interpolate recorded linear segments to intersect a declared temperature band or temperature crossing; preserve actual continuous intervals.",
    "norton_power_law": "Caller-supplied reference creep rate times a dimensionless stress ratio raised to a supplied stress exponent.",
    "mass_conservation": "Loss volume equals mass loss divided by density; average penetration is volume divided by exposed area.",
    "section_area_change_kinematics": "Authored dimensionless section comparison: signed fractional reduction is the original-minus-deformed area divided by original area; logarithmic ratio uses a difference of logarithms. No material response or standard acceptance threshold is supplied.",
    "faraday_electrolysis": "Dissolution mass follows charge, molar equivalent and declared current efficiency. Faraday constant is derived from SI elementary charge and Avogadro constant.",
    "linear_degradation": "The time of crossing a thickness requirement follows a declared linear loss trajectory.",
    "empirical_power_law": "Dimensioned reference penetration times a dimensionless exposure ratio raised to a supplied exponent.",
    "arrhenius_kinetics": "Rate ratio for a single supplied activation energy between two absolute temperatures.",
    "membrane_equilibrium": "Force equilibrium of a thin closed cylindrical membrane with declared allowable stress.",
    "stress_invariants": "Eigenvalues of a two-dimensional stress tensor and the deviatoric stress invariant.",
    "thermoelasticity": "Uniaxial linear strain compatibility for a declared degree of restraint.",
    "basquin_relation": "A declared constant-amplitude stress-range power law with reference stress and life.",
    "miner_accumulation": "A declared linear sum of applied cycles divided by per-level fatigue lives.",
    "goodman_relation": "Linear tensile mean-stress correction with supplied ultimate strength.",
    "larson_miller_relation": "A declared empirical temperature-log-time parameter; time convention is hours and logarithm is base 10.",
    "robinson_time_fraction": "A linear sum of exposure durations divided by supplied rupture lives.",
    "bolt_torque_equilibrium": "User nut-factor approximation relating torque, diameter and preload; no prescribed torque table.",
    "beam_kinematics": "Outer-fibre bending strain from geometry under the stated neutral-axis approximation.",
    "volume_conservation": "Coating dry volume, solids fraction and transfer efficiency accounting.",
    "fourier_conduction": "Series thermal resistances of steady planar layers.",
    "declared_composition_index": "Weighted composition index with all coefficients supplied by the caller.",
    "declared_surface_cleanliness_comparison": "Compare reviewed surface observations and their caller-supplied expanded uncertainties with caller-owned metric limits. Preserve inspected-area coverage, observation and requirement identities, exact unit tokens and missing evidence; do not supply a coating, fabrication or design-code acceptance rule.",
    "declared_chemical_compatibility_envelope": "Compare ordered, reviewed cleaning-step concentration, temperature, pH and duration records with caller-owned material compatibility envelopes. Accumulate exposure only within each exact envelope identity; do not predict mixing, reaction, local chemistry, corrosion, residue removal or procedure acceptance.",
    "storage_preservation_interval_accounting": "Partition the full preservation horizon at ordered environment-record and inspection boundaries, retain source interval and inspection IDs with observed, invalid and uncovered spans, and report caller-declared temperature, humidity, preservation-state excursions and inspection-spacing overrun. Use a single forward sweep over sorted interval boundaries. Do not bridge missing intervals or supply preservation requirements, damage rates, remaining life or acceptance decisions.",
    "partitioned_coating_observation_summary": "Keep coating specimens and source groups in fixed calibration or holdout partitions, summarize exact-unit observations and expanded uncertainties, and compare them only with caller-owned one-sided limits. Do not infer laboratory-to-field transfer, coating service life, corrosion rate or acceptance.",
    "declared_test_water_envelope": "Compare reviewed time- and location-identified water samples with caller-owned temperature, pH, conductivity and chloride envelopes while preserving sampling coverage and exact SI quantities. Do not supply regulatory limits, interpolate unobserved water chemistry, or infer corrosion or microbial activity.",
    "transport_erection_record_accounting": "Account for explicit handling, transport and erection intervals, metric observations, caller-owned limits and required inspection stages. Preserve activity gaps, invalid records, unmatched metrics, unit conflicts and caller dispositions without inferring damage, remaining life or acceptance.",
    "declared_weld_consumable_compatibility": "Match production weld material-condition pairs, consumable lot, process and service environment exactly to caller-owned compatibility declarations and compare the declared temperature support. Do not provide consumable classifications, substitutions, mechanical properties, corrosion resistance, weldability or acceptance rules.",
    "declared_polymer_compatibility_envelope": "Match reviewed polymer grade, lot or explicitly authorized grade-level transfer, condition, medium, concentration-unit convention and loading descriptor to caller-owned compatibility envelopes, then compare temperature, absolute pressure, concentration and duration support. Do not infer swelling, permeation, degradation rate, lifetime, mixture effects or acceptance.",
    "declared_composite_qualification_envelope": "Preserve laminate, resin, fiber, manufacturing, layup and environment identities with coupon and source-group calibration or holdout partitions, then compare reviewed temperature, moisture, absolute-pressure and cumulative-time ranges with caller-owned qualification envelopes. Do not infer micromechanics, strength reduction, delamination, lifetime or acceptance.",
    "casting_forging_quality_evidence_accounting": "Account for component, heat, manufacturing route, heat treatment, inspection-region coverage, qualitative or quantitative indications, expanded uncertainty and caller-owned limits or dispositions. Preserve invalid and unmapped records without supplying defect criticality, fracture, remaining life, acceptance or standard tables.",
    "declared_under_insulation_exposure_accounting": "Classify explicit reviewed insulation intervals only when surface temperature, wetness state and insulation-condition state fall inside a caller-owned exposure definition. Preserve invalid and uncovered time without predicting corrosion rate, metal loss, cracking, remaining life or failure probability.",
    "declared_phase_fraction_evidence_comparison": "Compare explicit sample- and region-identified phase-fraction measurements and expanded uncertainty intervals with caller-owned ranges. Preserve invalid and missing observations and do not infer unmeasured phase balance, strength, toughness, corrosion resistance, cracking or service life.",
    "declared_phase_fraction_linear_contrast": "Combine one caller-defined linear contrast of phase-fraction measurements from one identified sample, region and method. Propagate the caller-supplied expanded covariance matrix, including cross-phase covariance, and compare the resulting interval only with caller-owned bounds. Do not infer missing phases, acceptance, material properties or service life.",
    "phase_label_map_area_counting": "Count explicitly mapped categorical labels within a caller-reviewed image region and multiply by declared uniform pixel area. Preserve missing and unclassified pixels, array hashes and specimen lineage; do not estimate measurement uncertainty, infer phase identity, predict material properties or create acceptance decisions.",
    "phase_map_topology_summary": "Independently label caller-declared categorical raster components under selected 4- or 8-neighbor connectivity and count shared 4-neighbor pixel edges by category pair. Convert edge counts to sampled image-grid lengths using declared rectangular pixel dimensions. Do not infer grain identity, stereological quantities, physical interface area, material properties or acceptance outcomes.",
    "reliability_subset_simulation_pcn": "Implement pCN subset simulation for a deterministic scalar limit-state callback on caller-reviewed independent standard-normal latent coordinates. Permit conversion to the neutral first-failure EventProbability contract only after a separate period-first-failure review. Use a reproducible PCG64 stream, empirical intermediate quantiles, conditional rejection transitions and the product of observed conditional fractions. Record thresholds, acceptance diagnostics, configuration digest and partial log-probability. Do not claim iid uncertainty bounds, convergence certification, physical-model uncertainty or qualification.",
    "declared_sour_environment_applicability_envelope": "Match material grade, heat, microstructure, hardness-unit convention, absolute H2S partial-pressure basis and stress descriptor to caller-owned qualification envelopes, then compare reviewed pH, temperature, chloride and exposure ranges with partitioned test evidence. Do not supply standard thresholds, SSC or HIC rates, crack growth, lifetime or acceptance.",
    "declared_chloride_scc_qualification_envelope": "Match material and metallurgical condition, chloride-unit convention, oxidizing-state or dissolved-oxygen basis, and applied or residual stress descriptor to caller-owned qualification evidence, then compare reviewed temperature, pH and exposure support. Do not infer SCC thresholds, initiation, growth, lifetime, probability or acceptance.",
    "microbial_campaign_evidence_accounting": "Account for campaign, site, clock, location coverage, valid samples, target- and method-specific assays, exact units, detection limits, censored below-detection records, water context and biofilm or deposit observations against caller-owned indicator definitions. Do not infer microbial corrosion causality, rate, lifetime or failure probability.",
    "declared_bonded_layer_observation_disposition": "Account for substrate, layer, interface, process and lot identities, region coverage, bond-strength or interface observations, expanded uncertainty, exact units and caller-owned requirements or dispositions. Preserve invalid, missing and unmapped evidence without inferring delamination growth, residual stress, fracture, lifetime or acceptance.",
    "declared_ammonia_scc_qualification_envelope": "Match material, metallurgy and heat-treatment identities, ammonia phase and concentration-unit convention, water, oxygen and impurity descriptors, temperature, applied and residual stress descriptors, and cumulative exposure to caller-owned qualification evidence. Do not infer thresholds, SCC initiation or growth, lifetime, probability or acceptance.",
    "alkaline_scc_qualification_envelope_accounting": "Match material and heat-treatment identities, alkaline species and exact concentration unit, temperature, electrochemical descriptor, reference and potential, applied and residual stress descriptors, and exposure duration to linked caller-owned qualification evidence. Do not infer SCC thresholds, initiation, growth, life, probability or acceptance.",
    "declared_weld_preheat_procedure_envelope": "Match material, joint, process, consumable, hydrogen-control and restraint identities exactly, then compare thickness, net heat input, recorded preheat and interpass temperatures with a caller-owned procedure envelope. Do not supply welding-code tables, weldability, hydrogen-cracking resistance, mechanical properties or acceptance.",
    "declared_sulfidation_applicability_envelope": "Match material and composition condition, sulfur species, quantity kind, exact unit and basis, temperature, absolute pressure, flow or deposit descriptor, and duration to caller-owned qualification evidence. Do not supply standard curves, metal-loss or scale kinetics, lifetime or acceptance.",
    "declared_carburization_qualification_envelope": "Match material or alloy condition, carbon activity or carburizing-potential basis and exact unit, temperature, absolute pressure, gas-composition descriptor, and cumulative exposure to caller-owned qualification evidence. Do not infer carbon profiles, kinetics, phase or property changes, lifetime or acceptance.",
    "nitriding_qualification_envelope_accounting": "Match material condition, nitrogen species, exact driving-force basis and unit, temperature, absolute pressure, gas descriptor and exposure duration to linked caller-owned qualification evidence. Do not infer nitrogen profiles, diffusion, kinetics, nitride phase or property changes, life or acceptance.",
    "declared_metallurgical_aging_equivalent_exposure": "Integrate explicit interval duration times caller-calibrated nonnegative equivalent-time rate multipliers within one reviewed material, mechanism and provider support. Compare only with a caller-owned equivalent-exposure limit; do not infer phase fraction, embrittlement, strength, toughness, remaining life or acceptance.",
    "caller_calibrated_acid_dissolution_rate_integration": "Integrate explicit interval duration times externally calibrated nonnegative acid-dissolution rate within exact material, acid, concentration-unit and basis, flow-descriptor and provider support. Preserve provider version and state digests; do not extrapolate or infer reaction chemistry, inhibitor depletion, localized attack, lifetime or acceptance.",
    "caller_calibrated_erosion_corrosion_loss_rate": "Integrate explicit interval duration times an externally calibrated nonnegative net erosion-corrosion loss rate within exact material, geometry, particle-loading unit, particle-size, fluid-chemistry and provider support. Do not infer mechanism synergy, CFD wall shear, particle trajectories, geometry evolution, lifetime or acceptance.",
    "selective_leaching_observation_envelope_accounting": "Compare exact alloy, composition, phase, environment, redox or potential basis and exposure conditions with linked caller-owned qualification evidence, then separately compare microscopy or composition observations and expanded uncertainty with exact method, definition and unit ranges. Do not infer dealloyed-depth growth, residual strength, fracture, life, probability or acceptance.",
    "external_under_deposit_local_loss_accounting": "Integrate explicit interval duration times externally calibrated local under-deposit loss rate while accounting for deposit-covered area-time inside one reviewed material, environment, temperature, coverage, stagnation, differential-aeration and provider support. Do not infer mechanism synergy, geometry evolution, remaining life, probability or acceptance.",
    "caller_under_deposit_environment_criteria_comparison": "Compare measured under-deposit local-environment facts with caller-owned bounds using method- and unit-matched expanded uncertainty intervals. Preserve sampling state, clock, material/environment, reference and evidence identity; missing or mismatched facts remain insufficient. Do not infer a corrosion mechanism, local-loss rate, lifetime or probability.",
    "caller_weighted_fixed_fugacity_carbonate_equilibrium_scenarios": "Propagate caller-supplied complete fixed-fugacity carbonate-equilibrium cases for one sample and exposure scope with normalized weights. Preserve each case and provider digest, fail aggregation if any scenario is unresolved, and report only descriptive weighted state summaries. Weights do not represent failure probability, event frequency or corrosion-rate distribution.",
    "reviewed_fire_protection_flux_coupling": "Combine caller-supplied incident heat-flux and reviewed protection transfer-fraction histories within exact provider flux and state support. Integrate their linearly interpolated product and emit a prescribed heat-flux boundary without supplying a fire curve, material properties, degradation, failure or acceptance.",
    "reviewed_local_heat_treatment_record_comparison": "Compare synchronized spatial temperature records with a caller-owned local heat-treatment envelope. Preserve sensor, heat-zone, provider and state identity; do not embed welding-code limits, metallurgical response or acceptance.",
    "reviewed_residual_stress_evidence_record": "Map measured or modelled residual-stress components and uncertainty to exact coordinate, provider, calibration and holdout support supplied by the caller. Do not infer redistribution, fracture, life, probability or acceptance.",
    "declared_wps_qualification_envelope_accounting": "Compare production welding-variable records with exact caller-owned qualified-procedure identities, units, ranges, categories and pinned specimen evidence. Do not bundle welding-code tables or make production acceptance decisions.",
    "partitioned_thermal_spray_condition_accounting": "Keep thermal-spray qualification and production observations in separate source groups, preserve coating-system, process, feedstock, substrate, region and provider lineage, and compare exact metric definitions, units and expanded uncertainty with caller-owned requirements. Do not infer coating life, corrosion rate, structural capacity or acceptance.",
    "authored_partitioned_thermal_spray_cross_section_geometry_summary": "Preserve calibrated cross-section fields, layer, substrate, spray batch and process identity, thickness traverses, caller-segmented pore geometry, uncertainty, edge and overlap handling, provider revision, immutable digests and disjoint calibration/holdout groups. Summarize thickness and area porosity only, without image segmentation, pore classification, bond-strength inference, embedded limits, acceptance, service life or probability.",
    "authored_partitioned_thermal_spray_thickness_uncertainty": "Apply caller-supplied additive instrument bias corrections to repeated SI coating-thickness measurements and combine reviewed repeatability, measurement and calibration standard-uncertainty components. Preserve physical specimen, source, independence and spatial partitions plus holdout reference lineage; do not perform segmentation or infer bond strength, acceptance, service life or probability.",
    "authored_partitioned_thermal_spray_porosity_uncertainty": "Convert caller-segmented pore pixels with reviewed area calibration, summarize field and replicate porosity, and combine segmentation-area and repeatability uncertainty while preserving physical specimen, source, independence, spatial and replicate partitions plus holdout reference lineage. Do not perform segmentation, classify pores or infer bond strength, acceptance, service life or probability.",
    "reviewed_duplex_weld_phase_envelope_comparison": "Compare measured weld-metal, heat-affected-zone and base-material phase-fraction uncertainty intervals with exact caller-owned regional envelopes while preserving process, heat history, method and provider digests. Do not infer unmeasured phases, properties, corrosion, cracking, life or code acceptance.",
    "reviewed_production_weld_test_evidence": "Account for destructive and nondestructive production-weld observations with exact specimen, source-group, procedure, lot, method, metric, unit, uncertainty and provider lineage against caller-owned requirements. Do not declare acceptance or infer defects, fracture, life or probability.",
    "declared_repair_welding_workflow_accounting": "Compare an ordered, non-overlapping repair-welding history with an exact caller-owned sequence of removal, inspection, deposition, heat-treatment and subsequent-examination stages, provider digests and metric envelopes. Do not infer repair effectiveness, structural integrity, life or acceptance.",
    "reviewed_acoustic_emission_campaign_summary": "Inventory acoustic-emission zones, sensors, calibrations, acquisition intervals, event features and reported source locations with exact provider and data lineage, then compare only with caller-owned feature support. Do not infer a defect or leak source, localization accuracy, POD, life, probability or acceptance.",
    "weighted_constant_speed_acoustic_emission_localization": "Estimate one acoustic-emission source position and origin time by weighted nonlinear least squares from caller-reviewed multi-sensor arrival picks, fixed homogeneous isotropic wave speed, sensor geometry, clock and uncertainty evidence. Preserve calibration/holdout source partitions, rank and spatial support diagnostics without generating picks or wave speed, classifying mechanisms, grading damage, deciding acceptance, life, POD or probability.",
    "deterministic_threshold_or_aic_acoustic_emission_pick": "Select one original-sample acoustic-emission arrival from a caller-reviewed waveform using an explicit threshold crossing or AIC-family split criterion. Preserve the original monotonic clock, signal unit, baseline and search windows, preprocessing, polarity, provider identity and immutable digests; report baseline and pick diagnostics without filtering, interpolation, event association, mechanism classification, damage grading, acceptance, POD or probability.",
    "weighted_known_source_acoustic_emission_wave_speed_calibration": "Fit a homogeneous acoustic-emission wave speed and clock offset from caller-reviewed known-source geometry and arrival picks using inverse-variance weighted travel time. Preserve sensor, channel, clock, specimen, source, calibration/holdout partitions, support and immutable digests; do not generate picks, infer anisotropy or dispersion, localize unknown sources, classify mechanisms, grade damage, decide acceptance, POD or probability.",
    "authored_weighted_transient_temperature_sensitivity_calibration": "Fit one caller-declared thermal-property multiplier or diffusivity from provenance-bound transient measured temperatures, external-provider baseline predictions and parameter sensitivities using weighted linear calibration. Preserve geometry, boundary, solver, sensor, clock, uncertainty, specimen/source partitions and support; report holdout residuals only inside support without implementing another PDE solver, inferring phase mechanisms, thermal stress, acceptance, life or probability.",
    "authored_transient_temperature_observation_comparison": "Compare caller-paired measured and external-solver transient temperature histories only after strict clock, sensor-position, provider-support and calibration/holdout partition review. Report point residuals and weighted bias, RMSE and MAE without fitting the solver, solving a PDE, inferring thermal stress, acceptance, life or probability.",
    "authored_external_thermal_discretization_refinement_diagnostic": "Compare ordered external-solver transient-temperature refinement levels at an identical reviewed query set while preserving geometry, boundary, material-property, solver, mesh, time-step, input, result and query digests. Report adjacent weighted temperature changes and an observed-order diagnostic only when its finite equal-ratio prerequisites hold; do not claim convergence, an error bound, PDE qualification, stress, fit, acceptance, life or probability.",
    "reviewed_replica_metallography_evidence": "Map replica sites, sampled area, preparation, microscope configuration, morphology descriptors and quantitative observations to caller-owned provider support with partition and uncertainty lineage. Do not fabricate grades or phases or infer aging class, damage rate, creep life, probability or acceptance.",
    "authored_replica_feature_geometry_reduction": "Preserve replica field, frame calibration, segmentation, observer review, caller feature type, centroid, bounding box, area, uncertainty, overlap, edge handling, validity and immutable evidence identities. Compute field area, reviewed feature count and density, segmented area fraction and nearest-neighbor spacing without automatically classifying creep cavities, assigning damage grade, predicting life, deciding acceptance or creating probability.",
    "partitioned_fracture_toughness_test_evidence_accounting": "Preserve material, physical specimen, geometry, orientation, test condition, endpoint, raw unit, uncertainty, caller validity evidence and provider digests in separate calibration, holdout and application partitions. Do not apply standards validity tables, convert endpoints, create FAD inputs, life, probability or acceptance.",
    "reviewed_cryogenic_cycle_leak_evidence": "Compare reviewed cryogenic temperature-pressure cycles and background, control and test leak observations with an exact caller-owned medium, method, metric, unit, detection-limit and support envelope. Preserve below-detection values as limits; do not infer a leak source, service leakage, POD, failure or acceptance.",
    "external_crevice_species_rate_inventory_accounting": "Integrate externally supplied net species source rates over a reviewed crevice clock and prescribed solution-volume history, then expose species inventories, concentrations, negative inventory and charge-balance diagnostics within exact provider support. Do not generate activities, pH, electrochemical kinetics, precipitation, susceptibility, damage, life, probability or acceptance.",
    "crevice_nernst_activity_potential": "Evaluate a caller-specified redox half-cell potential at each crevice-history knot using E = E0 - RT/(nF) ln(Q), caller-supplied dimensionless species activities, signed reaction-quotient stoichiometry and a caller-supplied standard-potential history. Preserve source-inventory digest, activity-provider and standard-potential-provider configuration/record identities, and the complete potential history. Require explicit reaction direction, electron count, standard-state mapping, temperature and local applicability review, with both providers mapped to declared Evidence. This computes neither activity/speciation nor mixed potential, reaction kinetics, corrosion rate, susceptibility or acceptance.",
    "nernst_driven_butler_volmer_history": "Bind a computed, input- and output-digest-checked caller Nernst half-cell potential history to one caller-calibrated Butler-Volmer reaction at an identical declared clock ID and exact time knots. Require matching reaction identity and explicitly identical potential reference identifiers, caller electrode-potential difference history, valid overpotential/temperature support, calibration lineage and direction/species-flux mapping review. Report signed partial current density, reaction extent and stoichiometric species flux only at supplied knots. Do not interpolate or integrate time, solve mixed potential, infer kinetics/activity, or convert partial current into total corrosion loss, protection or acceptance.",
    "crevice_multireaction_nernst_butler_volmer_balance": "At aligned caller crevice inventory knots, combine two or more digest-pinned half-cell potential profiles and calibrated Butler-Volmer branches, scale each partial current by caller exposed area relative to a reference area, and solve a common zero-net-current potential over the shared calibrated support. Require common clock, temperature and potential reference, complete caller reaction/area review, quasi-steady balance and negligible solution ohmic drop. Return instantaneous branch current and stoichiometric flux without time interpolation/integration, activity or kinetic inference, dynamic stability, total metal loss or acceptance.",
    "crevice_mixed_potential_species_flux_interval_inventory_transfer": "Accept only a computed digest-pinned multi-reaction crevice mixed-potential result. For each reaction/species flux on its existing reference-area basis, apply a caller-reviewed linear reconstruction between exact adjacent knots, integrate signed net plus positive and negative directional transfer exactly, and accumulate mole transfer while preserving upstream lineage. Do not infer bulk volume/concentration, transport, phase selection, metal loss, corrosion rate or acceptance.",
    "crevice_electrochemical_transfer_to_well_mixed_composition_history": "Consume a computed digest-verified area-scaled transfer ledger and caller initial mole inventory for every affected species plus liquid volumes at exactly aligned output knots. Apply cumulative signed species transfer to those amounts and divide by the caller volumes; require complete species/source-sink inventory, well-mixed compartment, mapping and use reviews. Do not solve chemistry, transport, precipitation, losses, or corrosion/material acceptance.",
    "crevice_composition_to_caller_aqueous_mass_action_knot_history": "Bind a computed digest-pinned caller-volume crevice composition history to one caller-supplied strict aqueous mass-action network per exact knot. Convert mol/m3 to mol/L for the declared 1 mol/L activity standard state, apply caller fixed activity coefficients for the positive initial activity guess (or an explicitly reviewed numerical seed for zero inventory), rebuild only explicitly selected constraint targets from the current composition while preserving all unselected caller targets, and solve the supplied network without changing its reaction or constraint topology. Require exact temperatures, evidence lineage and model review. Do not infer equilibrium constants, activity coefficients, reactions, multiphase chemistry, kinetics, transport or wall loss.",
    "aqueous_mass_action_activities_to_crevice_nernst_potential_history": "Consume only a computed digest-pinned knotwise aqueous mass-action result and bind its strictly positive dimensionless species activities to an explicitly caller-defined redox quotient, electron count, standard-potential reference and exact-knot standard-potential history. Preserve the upstream composition and solver-result digests, source inventory identity and exact clock/temperature knots. Require all quotient species, activity standard-state mapping, potential provider Evidence and reaction-direction reviews. This sequential adapter does not solve the redox reaction, infer E0 or activities, close current back into the same chemistry trajectory, add multiphase/transport kinetics, or infer corrosion/wall loss.",
    "reviewed_brittle_test_applicability_evidence": "Preserve material, product form, condition, thickness, orientation, minimum service temperature, loading descriptors and partitioned impact or toughness evidence, then compare only with a caller-owned applicability envelope. Do not bundle exemption curves, convert reference temperatures, infer fracture, life, probability or acceptance.",
    "reviewed_high_temperature_hydrogen_qualification_envelope": "Compare exact material composition and heat-treatment identity, absolute hydrogen partial-pressure and temperature-time exposure intervals, and microstructure or inspection evidence with a caller-owned qualification envelope. Do not bundle industry curves, reaction kinetics, property loss, damage, cracks, life, probability or acceptance.",
    "declared_liquid_metal_embrittlement_qualification_envelope": "Compare reviewed structural-material condition, liquid-metal composition and impurities, contact and wetting state, temperature, stress, strain-rate and exposure records with exact caller-owned test evidence and provider support. Do not bundle susceptibility tables or infer crack initiation, growth, property loss, life, probability or acceptance.",
    "reviewed_pressure_test_eligibility_envelope": "Compare exact component and material condition, test method, medium, pressure basis, planned pressure and temperature, stored-energy definition and complete prerequisite records with a caller-owned eligibility envelope. Preserve unsatisfied requirements as a computed outcome; do not supply code test pressures, structural capacity, fracture or leak risk, service fitness or regulatory acceptance.",
    "reviewed_solidification_cracking_qualification_envelope": "Compare exact weld-metal condition, process, consumable, chemistry profile, thermal, strain and restraint descriptors with partitioned caller-owned test evidence. Preserve methods, units, uncertainty and provider digests; do not bundle chemistry limits or infer cracking susceptibility, probability, life or acceptance.",
    "reviewed_reheat_cracking_qualification_envelope": "Compare exact material, weld and heat-affected-zone condition, welding process, heat input, ordered reheat history, stress and restraint descriptors with partitioned caller-owned qualification evidence. Do not bundle material rankings or infer cracking susceptibility, probability, life or acceptance.",
    "reviewed_lamellar_tearing_qualification_envelope": "Compare parent material, product, directionality, joint geometry, through-thickness loading, restraint, welding process, consumable and heat-input records with physical-specimen and source-group evidence. Do not bundle threshold tables or infer tearing susceptibility, flaw size, probability, life or acceptance.",
    "caller_licensed_joint_efficiency_rule_evaluation": "Select exactly one caller-supplied and computationally authorized joint-efficiency rule by joint, process, material group and examination method, then return its declared factor only when the exact examined extent is inside rule support. Preserve revision and content digests; do not bundle code tables, substitute factors, calculate strength or capacity, infer inspection reliability, life, probability or acceptance.",
    "reviewed_temper_bead_qualification_envelope": "Compare an ordered non-overlapping deposition-pass and layer sequence, heat input, interpass temperature and temper-bead descriptors with caller-owned hardness, microstructure or NDE evidence. Preserve specimen/source partitions and provider digests; do not bundle code limits or infer metallurgy, cracking, life, probability or acceptance.",
    "reviewed_hot_tap_provider_qualification_envelope": "Compare reviewed host-pipe condition, exact pressure basis, operating temperature, wall thickness, flow heat-extraction, branch and joint geometry, welding consumable and hydrogen-control identities with caller-owned thermal or burn-through and hydrogen-cracking provider outputs and partitioned qualification evidence. Do not bundle charts or infer acceptance, capacity, burn-through or crack probability, or life.",
    "reviewed_brazing_bonding_qualification_envelope": "Compare ordered member materials and surface conditions, bonding material and lot, process, flux, atmosphere, clearance, overlap and ordered heat-pressure cycle with physical-specimen and source-group observations. Preserve exact metric units, uncertainty and digests; do not infer unreported bond strength, failure probability, life or acceptance.",
    "reviewed_forming_qualification_envelope": "Compare component, material condition, product form, thickness, direction, cold or hot forming method, exact deformation metrics and ordered forming or post-forming thermal history with partitioned inspection and property evidence. Do not bundle forming-code limits or infer unreported strain, property degradation, life, probability or acceptance.",
    "reviewed_forming_geometry_strain_summary": "Preserve caller-reviewed original and final thickness, inside bend radius, angle, forming mode, direction, material condition, specimen/source identity, uncertainty and digests. Under one explicit circular-arc neutral-axis convention, summarize surface strain and thinning in one declared engineering or true convention, with caller threshold margins only and no embedded limits, heat-treatment requirement, acceptance, life or probability.",
    "authored_partitioned_pull_off_adhesion_evidence_calibration": "Preserve dolly, location, layer, substrate, preparation, cure, exposure, adhesive, break-mode components, calibration, provider and immutable evidence identities. Calculate force divided by area only for explicit SI inputs, retain provider stress separately, estimate paired calibration bias and compare independent holdout inside support without interpreting mixed break modes, embedding acceptance tables, predicting coating life or creating failure probability.",
    "reviewed_tube_bundle_integrity_evidence_envelope": "Preserve exchanger, bundle, tube, row and mapped location, material and geometry, support, baffle and vibration descriptors, operating clock, inspection or vibration observations and explicit caller disposition records, then compare only with caller-owned provider support and partitioned qualification evidence. Do not infer defect size, vibration response, repair or retubing decisions, life, probability or acceptance.",
    "reviewed_cryogenic_valve_qualification_envelope": "Compare exact valve, body, seat, stem, seal, medium and pressure-basis identities, ordered thermal-pressure-actuation cycles and leakage, torque or function observations with caller qualification evidence. Preserve below-detection and missing records; do not infer service performance, thermal stress, reliability, life, probability or acceptance.",
    "reviewed_peening_treatment_qualification_envelope": "Compare time-ordered zone treatment records, method, media, direction, exact intensity and coverage metrics with coordinate-, depth-, specimen- and source-group-identified residual-stress evidence inside caller-owned support. Do not infer stress redistribution, fatigue improvement, crack initiation, life, probability or acceptance.",
    "reviewed_external_pressure_provider_qualification_envelope": "Preserve shell, material, geometry, boundary, load, pressure-basis and measured-imperfection identities and bind eigen or nonlinear external-pressure results to exact solver, mesh, model and provider digests with calibration and holdout evidence. Do not bundle code charts or infer allowable pressure, safety factor, collapse probability, life or acceptance.",
    "reviewed_nozzle_local_stress_provider_qualification_envelope": "Preserve vessel, nozzle and opening geometry, material, coordinate frame, load components, mesh, result location, averaging and stress representation, then bind external provider results to exact revision and digests with disjoint calibration and holdout evidence. Do not bundle proprietary stress indices or infer acceptance, fatigue, life or probability.",
    "reviewed_finite_element_result_exchange_envelope": "Exchange digest-bound finite-element mesh and result metadata with model, mesh, coordinate, material assignment, load and boundary, step, result location, averaging, quantity, unit, component, shape and ordering identities plus solver convergence and partitioned verification records. Do not bundle large arrays, interpolate results, qualify a mesh, or infer acceptance, life or probability.",
    "reviewed_heat_exchanger_geometry_provider_envelope": "Preserve shell, bundle, tube-layout, tubesheet and baffle geometry with coordinate frame, component order, array shape, payload and provider digests, then compare provider values with partitioned metrology evidence inside caller support. Do not infer coordinates from counts or patterns or calculate flow, vibration, heat transfer, stress, capacity, life or acceptance.",
    "reviewed_gasket_joint_qualification_envelope": "Summarize direct bolt-preload records in one exact unit and compare flange, gasket and bolt material or lot identities, medium, pressure, temperature, seating-provider results and time-identified relaxation observations with caller-owned qualification evidence. Never convert torque to preload or infer gasket contact, leakage, relaxation, capacity, life, probability or acceptance.",
    "reviewed_hydrogen_fatigue_provider_qualification_envelope": "Preserve material condition, hydrogen species and exact absolute-partial-pressure or fugacity basis, temperature, load ratio, frequency, waveform, crack-growth metric definitions and external provider curve or rate results with partitioned qualification evidence. Do not bundle proprietary curves, convert pressure to fugacity, interpolate or integrate growth, or infer life, probability or acceptance.",
    "reviewed_hydrogen_cracking_provider_qualification_envelope": "Preserve material and heat, ordered hydrogen exposure with exact pressure or fugacity basis, crack geometry and orientation, toughness endpoint, crack-driving metric, load case, units, uncertainty and provider digests with disjoint calibration and holdout evidence. Do not mix endpoints or infer fracture acceptance, crack initiation or growth, life or probability.",
    "reviewed_pitting_ffs_provider_qualification_envelope": "Preserve component, material, coordinate frame, measured wall thickness, differential-pressure basis, pit-field or cluster geometry definition, units and digests, supplied inspection uncertainty or POD evidence, load case and external provider result with calibration and holdout partitions. Do not bundle proprietary FFS equations, reconstruct pits, infer interaction, capacity, acceptance, life or probability.",
    "reviewed_creep_fatigue_interaction_provider_envelope": "Preserve material, physical scope and clock, ordered temperature-stress-strain-cycle history blocks, immutable history digests, separately defined creep and fatigue exposure quantities, exact interaction basis and external provider result with calibration and holdout evidence. Do not calculate an independent linear damage sum, bundle proprietary interaction diagrams, or infer remaining life, probability, acceptance or compliance.",
    "ultrasonic_time_of_flight": "Round-trip travel distance and the declared sound-path projection.",
    "bayes_rule": "Prior bin weights multiplied by no-indication likelihood and renormalized.",
    "bayesian_linear_thickness_update_derivation": "Represent remaining thickness at one reviewed physical location by a two-parameter constant-linear Gaussian state: thickness at a declared reference time and signed loss rate. Condition a caller-supplied Gaussian prior on a predeclared update partition using reviewed Gaussian measurement errors, while keeping holdout rows outside the posterior. Propagate the posterior analytically to caller-supplied times and report any required-thickness exceedance only as a point-in-time model-implied state probability. This derivation supplies no process noise, model-form uncertainty, POD, first-passage probability, intervention model or acceptance criterion.",
    "linear_thickness_state_space_filter_derivation": "Represent remaining thickness and signed loss rate as a two-state linear Gaussian process. Propagate each caller-ordered interval with the constant-rate transition and add a reviewed full two-by-two state covariance rate multiplied by elapsed time. Apply scalar thickness observations sequentially with the Joseph covariance update, while predeclared holdout rows produce one-step-ahead residuals without changing the state. Propagate the final filtered state and uncertainty to requested times. This filter does not estimate its process noise, smooth past states, model nonlinear degradation, incorporate intervention or inspection effectiveness, or turn point-in-time state probabilities into first-passage probabilities.",
    "gaussian_thickness_posterior_sampling_derivation": "Generate a finite reproducible joint design from a caller-reviewed two-parameter Gaussian posterior for reference-time thickness and signed constant loss rate. Use an explicitly versioned SplitMix64 integer stream, open-unit conversion, Box-Muller standard-normal pair and analytical two-dimensional Cholesky map so the draw algorithm does not depend on a library distribution implementation. Preserve thickness-rate correlation and accept only rows with nonnegative loss rate and remaining thickness strictly above the reviewed threshold at assessment. Stop at a fixed candidate budget and return no partial design when the requested conditional count is unavailable. This conditioning operation supplies no process noise, nonlinear growth, intervention, confidence bound, field calibration or constant-rate qualification.",
    "sampled_linear_thickness_first_passage_derivation": "For each caller-supplied joint sample that is explicitly conditioned on remaining above a reviewed thickness threshold at assessment, preserve its remaining thickness, nonnegative constant loss rate, identity and normalized probability mass. A positive-rate row crosses exactly once at assessment time plus thickness margin divided by rate; a zero-rate row never crosses after assessment. Sum complete row weights directly at strictly ordered candidate horizons to form a cumulative conditional first-crossing curve, retaining assessment-conditioning conflicts instead of dropping or reconditioning them. This discrete input-distribution push-forward provides no confidence bound, process noise, model-form validation, inspection effect, consequence or field qualification.",
    "declared_pressure_test": "Caller-provided test multiplier and allowable ratio plus hydrostatic head; not a code-derived test prescription.",
    "ideal_gas_first_law": "Reversible adiabatic expansion work with constant heat-capacity ratio.",
    "weibull_survival": "Ratio of Weibull survivals over a finite interval conditional on current survival.",
    "probability_axioms": "Products and complements for explicitly independent events over a common conditioning basis.",
    "finite_joint_probability_space": "Sum caller-reviewed probabilities over an exhaustive finite binary state space. Marginals, pairwise moments and an independence reference follow from the same declared truth table; they do not identify causal common causes or justify a new dependence model.",
    "finite_state_ctmc": "Propagate a caller-reviewed finite-state time-homogeneous continuous-time Markov generator by a matrix exponential. A block exponential integrates state occupancy; an absorbing copy of declared event states gives first-entry probability while the original generator retains repair and replacement transitions.",
    "piecewise_finite_state_ctmc": "Sequentially propagate a caller-reviewed finite-state distribution through contiguous piecewise-constant Markov generators in the exact supplied order. Apply matching absorbing copies for cumulative first entry and integrate occupancy and expected transitions within each segment. Preserve segment boundaries and rate provenance; do not infer continuous time variation, aging or semi-Markov behavior.",
    "total_probability": "Allocation of one initiating intensity across exhaustive exclusive branches.",
    "gamma_poisson_conjugacy": "Gamma shape and exposure updates from explicitly ascertained Poisson event counts.",
    "uniaxial_test_kinematics": "Engineering force/area and gauge strain; uniform-volume conversion only when declared.",
    "declared_property_ratio": "Ratio to an explicitly supplied baseline property without clipping observed improvement.",
    "material_corrosion_rate_contrast": "Arithmetic difference, ratio, and log-ratio for two nonnegative caller-supplied uniform corrosion rates with distinct material identities and an explicit condition/source group; undefined ratios remain explicit when the reference rate is zero.",
    "numpy_quantile_linear": "Compute descriptive empirical quantiles from one caller-reviewed rate summary per identified physical specimen in a single material, condition, method and source group, using NumPy's explicitly selected linear sample quantile definition. The result describes only the supplied sample and does not estimate confidence, prediction, independence, transferability or life.",
    "caller_weighted_scenario_pushforward": "Propagate caller-supplied complete rate scenarios and normalized declared weights through a fixed linear wall-loss calculation. Preserve the weight meaning and report weighted threshold or wall-exhaustion mass without interpreting them automatically as event probabilities.",
    "caller_crevice_ionic_reactive_transport_species": "Caller declares ionic species identities, integer charge, diffusivity, elemental formula and initial cell inventories; this interface contains no bundled chemical property table.",
    "caller_crevice_ionic_reaction_network": "Caller declares reversible reaction stoichiometry, parameter records, units, rates and source digests; the evaluator checks elemental and charge closure but does not source kinetic data.",
    "caller_crevice_ionic_transport_boundary_history": "Caller-supplied electroneutral mouth concentration schedule with provenance and exact time-knot mapping.",
    "caller_crevice_axial_velocity_face_history": "Caller-supplied spatial face velocity schedule; the implementation does not derive flow from momentum equations.",
    "finite_volume_advection_nernst_planck_and_mass_action": "Independent finite-volume balance with dilute Nernst-Planck zero-current closure, caller advection and caller mass-action kinetics; applicability is an explicit user review responsibility.",
    "caller_bolt_proof_strength_temperature_curve": "Caller-supplied temperature-indexed nominal bolt proof-strength records; the module does not bundle or assert standard allowable values.",
    "piecewise_linear_bolt_nominal_strength_margin": "Linear interpolation within caller curve support and deterministic comparison against nominal axial stress; no design-code acceptance is inferred.",
    "mendeley_316l_metastable_pitting_rows": "Metadata-pinned Mendeley 316L metastable-pitting chronoamperometry dataset reader contract. The MPR decoder is injected by the caller; source files and measurement rows are not bundled.",
    "mendeley_az31b_corrosion_fatigue_lab_rows": "Metadata-pinned Mendeley AZ31B corrosion-fatigue workbook row reader. The declared dataset license is CC BY 4.0, subject to potential third-party rights in the files; original workbooks remain local-only, and the reader preserves source cells without interpretation or qualification.",
    "zenodo_cocr_wear_corrosion_rows": "Metadata-pinned Zenodo CC BY Co-Cr wear-corrosion workbook row reader. Original files remain local and caller authorization is required to read cell rows.",
    "caller_scale_reaction_diffusion_transport_parameters": "Caller-supplied scale thickness, temperature, diffusivity, sink rate, reactant boundary and kinetic parameters with explicit record provenance.",
    "caller_scale_anodic_butler_volmer_branches": "Caller-defined anodic electrode branches and metal stoichiometry; no empirical branch parameters are bundled.",
    "caller_scale_cathodic_butler_volmer_branches": "Caller-defined cathodic Butler-Volmer branches linked to caller-identified transported reactants.",
    "caller_scale_reactant_and_metal_stoichiometry": "Caller-reviewed reactant and metal reaction-extent mapping for the declared electrochemical branches.",
    "finite_volume_scale_first_order_sink_with_butler_volmer_mixed_potential": "Independent steady finite-volume first-order reactant sink coupled to a bounded common mixed-potential root solve.",
    "butler_erdey_gruz_volmer_electrode_kinetics": "Independently implemented Butler-Volmer kinetic relation with caller-defined branch parameters; applicability is not externally qualified.",
    "nist_codata_faraday_constant_2022": "CODATA Faraday constant used as an exact conversion constant; no source data table or prose is reproduced.",
    "caller_gasket_leak_calibration_map": "Caller-supplied calibrated gasket leakage relation with declared conditions and provenance.",
    "caller_gasket_contact_pressure_history": "Caller-supplied contact-pressure history that remains externally prescribed during the gas-inventory calculation.",
    "caller_gasket_gas_inventory_volume_temperature_pressure": "Caller-supplied fixed gas volume, isothermal temperature and initial/downstream pressure record.",
    "ideal_gas_inventory_balance_with_calibrated_leakage": "Fixed-volume isothermal ideal-gas inventory balance driven by a caller-calibrated leakage relation; no pressure-dependent gasket feedback is inferred.",
    "mcdiarmid_shear_stress_critical_plane_1994": "Independently coded finite-sample screening implementation based on McDiarmid's 1994 critical-plane strength relation; no article data or prose is bundled.",
    "caller_multiaxial_stress_tensor_history": "Caller-supplied ordered finite stress tensor samples with explicit physical-scope and convention review.",
    "caller_mcdiarmid_case_torsion_and_tensile_strengths": "Caller-supplied material strengths for the selected crack case, digest-bound with usage Evidence.",
    "finite_sampled_shear_traction_diameter_and_normal_stress_screen": "Finite set of plane candidates and sampled traction vectors; no continuous-plane or between-sample optimization is implied.",
    "caller_mcdiarmid_index_life_curve": "Caller-supplied same-condition monotone McDiarmid-index to life curve; interpolation is bounded to its tabulated support.",
    "caller_ordered_multiaxial_cycle_block_counts": "Caller-supplied ordered load-block cycle counts and complete upstream screen results.",
    "linear_miner_damage_rule_for_mcdiarmid_campaign": "Explicit linear cumulative damage assumption applied to caller-indexed life; sequence effects are not modeled.",
    "caller_gasket_annular_contact_pressure_map": "Caller-supplied radial/angular contact pressure cells and annular edge coordinates with provenance.",
    "caller_radial_seal_threshold_and_mesh_connectivity": "Caller-declared contact-pressure threshold and reviewed mesh connectivity convention.",
    "annular_cell_area_and_four_neighbor_radial_path_graph": "Geometric annular cell areas and four-neighbor graph with periodic angular wrapping, implemented independently from caller mesh values.",
    "gasket_contact_open_path_topology_screen": "Open-cell connected-component and radial bottleneck path calculation; it is a topology screen and not a leak-rate model.",
    "mendeley_ahss1300_hydrogen_permeation_rows": "Metadata-pinned Mendeley AHSS Grade 1300 hydrogen permeation workbook interface. The registry audit returns digest-pinned worksheet dimensions and formula counts only; the separate explicit local authorization helper streams source-ordered typed rows without unit or formula evaluation, and raw workbook assets remain outside releases.",
    "caller_gasket_compression_force_displacement_loops": "Caller-supplied ordered measured compression force-displacement loops and repeat counts with specimen Evidence.",
    "caller_gasket_specimen_area_thickness_and_condition": "Caller-declared initial thickness, loaded area, material condition and measurement convention.",
    "piecewise_linear_force_displacement_loop_work_integral": "Piecewise-linear reconstruction with trapezoidal force-displacement work integration.",
    "closed_loop_work_as_measured_hysteresis_energy_summary": "Signed loop work and its magnitude are reported as measured-loop summaries only; no constitutive or damage law is fitted.",
    "caller_gasket_temperature_bracket_loading_curves": "Caller-supplied monotone loading curves for the same specimen condition at two bracketing temperatures.",
    "caller_gasket_specimen_geometry_and_condition": "Caller-supplied initial specimen thickness, loaded area, specimen identity and material condition.",
    "linear_temperature_interpolation_at_fixed_compression_strain": "Linear interpolation of measured stress at fixed caller strain knots within the measured temperature bracket only.",
    "quasi_static_gasket_force_compression_curve_transfer": "Converts the bounded interpolated loading curve to nominal force-displacement points without unloading, dynamic or constitutive inference.",
    "caller_bolt_preload_stiffness_and_thermal_free_length": "Caller-supplied bolt preload, axial stiffness, free-length thermal shifts and provenance.",
    "caller_gasket_sector_area_compression_and_thermal_free_thickness": "Caller-supplied gasket-sector areas, initial compression, thermal free-thickness shifts and source evidence.",
    "quasi_static_parallel_bolt_gasket_force_equilibrium_with_temperature_curve_transfer": "Independent common-opening force equilibrium for parallel tension-only bolts and compression-only gasket sectors, using bounded temperature-interpolated caller loading curves.",
    "caller_bolt_and_gasket_sector_cte_temperature_tables": "Caller-supplied component-specific CTE(T) values with Evidence and temperature support for the identified bolt and gasket sectors.",
    "caller_component_effective_free_dimensions_and_reference_temperature": "Caller-supplied effective free length/thickness dimensions and reference temperature for thermal strain conversion.",
    "piecewise_linear_cte_thermal_strain_integral": "Independent trapezoidal integration of piecewise-linear CTE data over a bounded temperature interval; no out-of-range extrapolation.",
    "temperature_dependent_bolt_gasket_joint_equilibrium": "Thermal expansion adapter that passes computed free dimensional changes to the existing caller temperature-curve joint solver.",
    "caller_covariance_for_ordered_joint_load_coordinates": "Caller-supplied covariance for ordered non-reference joint load and free-expansion coordinates, linked to its record Evidence.",
    "central_finite_difference_local_sensitivity_of_quasistatic_gasket_equilibrium": "Central finite-difference sensitivities through the existing equilibrium solver at its nominal local contact active set.",
    "first_order_covariance_pushforward_joint_contact_outputs": "First-order J Sigma J-transpose covariance propagation; no nonlinear uncertainty or probability inference.",
    "caller_paired_reference_target_multiaxial_life_observations": "Caller-supplied paired reference/target fatigue lives at exact common parameter levels, with separate data provenance and rights Evidence.",
    "independent_weighted_log_life_ratio_summary": "Descriptive weighted mean and population spread of paired log life ratios without curve fitting or transfer.",
    "caller_joint_specific_elastic_interaction_matrix": "Caller-calibrated signed elastic bolt-to-bolt load-transfer coefficients for the identified joint.",
    "caller_ordered_bolt_tightening_operations_and_preload_increments": "Caller-supplied ordered tightening operations and applied preload increments for explicit tightening passes.",
    "sequential_linear_superposition_of_elastic_bolt_load_transfer": "Sequentially updates bolt loads using a caller matrix and linear superposition, without nonlinear contact or frictional slip.",
    "caller_wet_co2_initial_cylindrical_pipe_geometry": "Caller-declared initial cylindrical pipe dimensions and geometry provider evidence.",
    "caller_wet_co2_wall_recession_and_scale_phase_inventory_history": "Caller-supplied time-knot metal recession and per-phase line inventory with source digest.",
    "caller_wet_co2_scale_phase_molar_volume": "Caller-provided phase molar volumes and evidence for line-inventory to cylindrical scale-volume conversion.",
    "caller_gasket_compression_force_observations_and_uncertainties": "Caller-supplied compression force observations and positive measurement uncertainties, with specimen and source provenance.",
    "weighted_non_decreasing_isotonic_regression_pool_adjacent_violators": "Weighted pool-adjacent-violators isotonic regression for a nondecreasing compression loading path; independent implementation.",
    "caller_material_condition_temperature_rate_and_loading_branch": "Caller-declared material/test condition, temperature, loading rate and compression branch used to scope the fitted curve.",
    "caller_finite_element_gasket_field_receipt_and_normalized_arrays": "Caller-authorized provider receipt, selected normalized FE arrays and exact provider digests.",
    "caller_mesh_contact_location_area_and_coordinate_mapping": "Caller-mapped mesh nodes, contact areas, frames and direct one-to-one result locations.",
    "caller_solver_step_time_and_support_boundary_records": "Caller-bound FE solver-step time and optional explicit support observations; no hidden interpolation.",
    "imported_gasket_fe_stress_tensor_components_and_frame": "Imported six-component symmetric Cauchy stress tensor field with provider frame and exact scope lineage.",
    "three_dimensional_j2_von_mises_equivalent_stress_invariant": "Independent three-dimensional J2 equivalent stress invariant applied to the imported tensor components.",
    "caller_material_condition_temperature_and_equivalent_stress_limit": "Caller-supplied material condition, temperature and evidence-bound scalar stress threshold.",
    "independent_cylindrical_radial_finite_volume_species_balance": "Independent annular finite-volume diffusion balance using exact logarithmic radial resistances.",
    "caller_signed_cylindrical_wall_reaction_extent_schedule": "Caller-supplied signed interval reaction extents with declared species, elements and electronic charge transfer.",
    "independent_moving_cylinder_finite_volume_inventory_balance": "Transient finite-volume species inventory balance with conservative annular remapping and explicit wall transfer ledgers.",
    "caller_cylindrical_wall_activity_product_to_scale_kinetics": "Caller-defined activity product and saturation mapping from exact cylindrical wall-adjacent states to a caller scale law.",
    "caller_cylindrical_transient_species_history_for_wall_saturation": "Caller-paired transient cylindrical wall-adjacent concentration history at exact chemistry knots.",
    "caller_surface_scale_kinetics": "Caller-calibrated single-phase scale kinetic law; no phase discovery or parameter fitting is performed by the bridge.",
    "degradation.wet_co2_cylindrical_scale_geometry_history": "Registered caller-evidence-bound geometry calculation that maps metal recession and phase line inventories into exact-knot cylindrical radii, layer thicknesses, areas and wetted perimeter.",
    "caller_cylindrical_scale_geometry_record": "Caller-provided cylindrical dimensions and layer mapping for the existing geometry evaluator.",
    "caller_scale_thickness_kinetics_history": "Caller-calibrated scale-thickness history used as the phase-resolved layer inventory handoff input.",
    "cylindrical_annular_layer_inventory_geometry_handoff": "Maps caller layer thickness and molar volume into exact-knot lineal annular inventories without fitting kinetics or changing geometry law.",
    "computed_digest_pinned_multiaxial_paired_life_audit": "Consumes a computed digest-pinned exact-level paired life-ratio audit; no source data is bundled.",
    "caller_reference_condition_multiaxial_parameter_life_curve": "Caller-supplied reference material life curve restricted to exact parameter levels paired by the transfer audit.",
    "weighted_log_linear_paired_life_transfer": "Weighted log-linear relation fitted from paired observations and applied only to their exact shared parameter support.",
    "caller_cylindrical_phase_solution_diffusivity_records": "Caller-supplied per-phase and solution-film diffusivity values with evidence and exact species mapping.",
    "cylindrical_multilayer_radial_diffusion_resistance": "Independent sum of exact logarithmic radial Fick resistances across caller annular layers and solution film.",
    "caller_wet_co2_wall_saturation_scale_kinetics_result": "Caller-provided digest-bound saturation and scale-kinetics result at aligned cylindrical geometry knots.",
    "caller_wet_co2_cylindrical_multilayer_transport_result": "Caller-provided digest-bound species diffusion resistance and transport state on the matching geometry knots.",
    "caller_wet_co2_cylindrical_geometry_result": "Caller-provided computed exact-knot cylindrical geometry result with source and input digests.",
    "caller_cylindrical_geometry_result": "Caller-provided computed cylindrical geometry result with exact-knot input/result digest lineage; this is a software-model handoff contract, not independent experimental evidence or an external scientific constant.",
    "caller_balanced_solid_precipitation_consumption_stoichiometry": "Caller-reviewed balanced solid formation relation mapping consumed aqueous reactants to scale extent.",
    "caller_cylindrical_geometry_iteration_seed": "Caller-supplied initial geometry state used as the bounded replay seed.",
    "bounded_picard_replay_of_caller_transport_saturation_and_scale_growth": "Fixed-order bounded Picard replay with per-knot inventory residual gates; it is sequential composition, not a monolithic multiphysics solver.",
    "bounded_feedback_of_caller_scale_kinetics_diffusion_supply_and_bv_recession": "Iterate the registered cylindrical spatial BV/recession solver with caller wall-saturation kinetics, exact annular multilayer diffusion supply, phase inventory updates and cylindrical geometry. Saturation kinetics/transport and BV transport remain separate caller calculations; scale precipitation is not inserted as an aqueous sink in the BV ODE.",
    "caller_mass_action_activities_for_stage_scale_kinetics": "Uses the caller's fixed, evidence-bound aqueous reaction network and standard states to provide activities to the selected scale kinetic law.",
    "aqueous_mass_action_recomputed_from_stage_wall_composition": "Rebuilds caller linear component totals from each BDF-stage wall-cell molar composition and re-solves the declared log-activity mass-action system; no species or reaction topology is inferred.",
    "caller_finite_gas_cylindrical_two_film_transfer_and_inventory": "Uses caller-evidenced fixed-capacity gas inventory, Henry relation, interfacial area and two-film coefficients for cylindrical stage coupling.",
    "finite_gas_aqueous_bv_scale_element_balance": "Balances finite gas, aqueous species, scale phases, wall release and external radial exchange by element at each interval.",
    "caller_finite_gas_inventory_initial_state": "Pins the initial finite-gas fugacity and capacity to caller-provided licensed evidence.",
    "finite_gas_and_outer_liquid_stage_inventory_flux_limit": "Limits each BDF-stage two-film transfer rate by available finite gas or outer radial-cell liquid inventory over the interval remainder.",
    "same_stage_cylindrical_radius_from_wall_and_scale_inventories": "Recomputes cylindrical bore and steel inner radii algebraically from current BDF-stage wall release and scale phase inventories.",
    "lagrangian_radial_mesh_conserved_cell_inventory_transport": "Advances radial-cell molar inventories on a caller-reviewed Lagrangian mesh while the cylindrical inner boundary evolves.",
    "independent_cylindrical_annular_scale_inventory_volume_closure": "Map exact-knot caller-selected solid line inventory through its evidence-bound molar volume into the cylindrical annular volume used by radial transport and steel-recession geometry.",
    "computed_bv_alloy_element_release_to_cylindrical_recession": "Convert digest-pinned mixed-potential reaction extents into cumulative alloy-element release and map released mass to exact annular bore-radius changes using caller density and composition. This is a one-way geometry replay and does not re-solve electrochemistry on the changed geometry.",
    "caller_activity_corrected_reactive_transport_history": "Caller-provided digest-pinned activity-corrected reactive transport history on an exact fixed slit geometry and clock.",
    "caller_cellwise_competing_solid_kinetic_rate_campaign": "Caller-provided interval extent-rate campaign for a finite declared set of solid phases and exact spatial cells.",
    "caller_solid_molar_volume_and_deposition_coverage": "Caller-provided evidence-backed phase molar volumes and reviewed deposition coverage and face partition.",
    "sequential_finite_volume_phase_inventory_to_slit_aperture_handoff": "Sequential finite-volume solid inventory and aqueous-balance handoff into a next-segment equivalent slit aperture; no morphology or in-interval transport feedback is solved.",
    "mendeley_mdea_co2_eis_version3": "Mendeley Data v3 raw text spectra for experimental and simulated carbon-steel EIS in MDEA/CO2 environments, retained as separate provenance groups under CC BY 4.0; the local reader preserves row tokens and does not fit circuits or infer corrosion rates.",
    "caller_mendeley_eis_column_mapping": "Caller-reviewed exact source-header mapping, units, complex imaginary-axis sign and optional source-magnitude consistency tolerances; no provider-independent interpretation is inferred.",
    "explicit_real_imaginary_eis_channel_to_complex_impedance": "Calculate complex impedance magnitude and phase from caller-selected finite frequency, real and imaginary channels, preserving the source row order and row/file digests. No sorting, smoothing, circuit fitting or corrosion-rate inference is performed.",
    "bounded_relaxed_fixed_point_controller_for_caller_cylindrical_solver": "Bounded damped-Picard controller for exact-grid radius iteration, including an adapter that rebuilds cylindrical scale/wall geometry and reruns the transient spatial Butler-Volmer calculator in explicit trial mode; convergence requires radius and wall-element inventory residuals to pass.",
    "caller_selected_geometry_dependent_wet_co2_solver": "Caller-provided runtime solver contract that must recompute wet-CO2 transport, electrochemistry and material response for each trial cylindrical radius path.",
    "mendeley_internal_corrosion_doobn_xlsx_rows": "Read a version-pinned local Mendeley workbook by official file SHA-256 and preserve nonempty worksheet rows, raw cell values, storage types, source coordinates and authorization/Evidence digests. This does not interpret expert-elicited probabilities, construct or validate a Bayesian network, or reuse the bundled PDF.",
    "sequential_fixed_aperture_reactive_transport_segments": "Re-solve caller activity-corrected reactive transport once per exact time segment on its entering uniform aperture, then apply the explicit phase-rate interval and carry aqueous/solid inventories and uniform aperture to the next segment. No within-segment iteration or variable-area field is implied.",
    "endpoint_trapezoid_faradaic_inventory_split": "Apply caller-mapped Faradaic species sources and branch extents after each transport interval using endpoint trapezoidal integration; preserve this legacy operator-split method as the default and do not infer intra-interval kinetics.",
    "endpoint_linear_branch_current_bdf_stage_inventory_source": "Interpolate caller-computed Faradaic branch-current densities linearly between exact-knot mixed-potential solutions, then integrate branch extents and mapped aqueous species sources inside the transport BDF stages. The mixed-potential/equilibrium solves remain endpoint-coupled; this method is not a fully coupled electrochemical DAE or a qualified corrosion law.",
    "bdf_stage_spatial_ohmic_mixed_potential_and_faradaic_source": "At each BDF right-hand-side evaluation, solve the existing caller-parameterized spatial quasi-steady ohmic/Butler-Volmer mixed-potential problem from trial aqueous concentrations and stage geometry/conductivity records, then integrate its Faradaic branch sources and extents with transport. No double-layer storage, chemistry-phase discovery, or qualified corrosion kinetics are inferred.",
    "caller_evidence_bound_bdot_activity_refresh_at_bdf_stages": "At every BDF RHS evaluation in the reviewed spatial mixed-potential mode, recompute caller-parameterized B-dot activity coefficients from the trial aqueous state and use the same coefficients in Nernst-Planck activity gradients, homogeneous activity-based kinetics and stage Nernst/Butler-Volmer calculations. Bind interval parameter request digests and bound total callback evaluations. This does not solve mass-action speciation, solid equilibrium or activity parameter qualification.",
    "caller_explicit_aqueous_constraint_role_partition": "Require every aqueous mass-action linear constraint to have exactly one caller-declared role: conserved analytical component, fixed target, or charge neutrality. Validate a single zero-target charge row against the exact species charge map; role labels are explicit caller semantics and are not inferred from constraint names.",
    "caller_species_to_conserved_component_stoichiometric_map": "Bind each conserved aqueous component to the exact coefficient row of its declared mass-action constraint and require the mapping to remain invariant under all declared aqueous reaction stoichiometries.",
    "finite_volume_aqueous_component_inventory_flux_source_projection": "Project caller species inventories, signed left-to-right face transfers, and incoming-positive source transfers onto conserved component ledgers; compute per-cell and global inventory closure with caller absolute/relative tolerances and a bounded operation ceiling. This is ledger projection only, not a chemical equilibrium or transport solve.",
    "closed_batch_conserved_aqueous_component_mass_action_davies": "Derive conserved-component molar targets from caller initial species moles and fixed solution volume, preserve caller fixed-target and exact zero-charge constraints, solve the declared single-liquid Davies mass-action system, and verify final component inventory closure. No solids, gas exchange, reservoirs, transport or BDF coupling are implied.",
    "finite_volume_conserved_component_inventory_bdf_state": "Integrate per-cell conserved aqueous component moles as the BDF state on a fixed-volume mesh with closed external boundaries; species concentrations are equilibrium reconstructions and reaction-invariant component maps provide the transported inventory basis.",
    "caller_evidenced_cellwise_davies_mass_action_at_bdf_stages": "At every BDF trial stage, derive cellwise analytical component targets from the trial conserved inventories and solve the caller-evidenced Davies mass-action equilibrium; enforce explicit single-liquid, fixed-volume and bounded nested-work assumptions.",
    "electroneutral_nernst_planck_species_flux_projected_to_components": "Calculate species diffusion and activity-gradient fluxes on interior faces using caller diffusivities, solve an algebraic migration field for zero ionic current, and project species fluxes through reaction-conserved component maps into the finite-volume BDF state.",
    "caller_evidenced_charge_neutral_component_source_extent_schedule": "Apply caller-supplied, digest-bound per-cell reaction-extent-rate schedules at exact knots with piecewise-linear interpolation, project aqueous stoichiometry into conserved-component BDF states, and separately account for external reservoir component, element and charge changes. Nonzero net aqueous charge requires the paired caller-current schedule and knotwise continuity; the schedule is not derived from Butler-Volmer or mixed-potential kinetics.",
    "caller_evidenced_component_source_extent_schedule": "Apply caller-supplied, digest-bound per-cell reaction-extent-rate schedules at exact knots with piecewise-linear interpolation, project aqueous stoichiometry into conserved-component BDF states, and separately account for external reservoir component, element and charge changes. Charged extent schedules require the paired prescribed-current schedule and knotwise continuity; source rates are not derived from Butler-Volmer or mixed-potential kinetics.",
    "caller_evidenced_ionic_face_current_schedule": "Use review-gated caller-supplied exact-knot ionic currents on all faces, zero external boundary currents, and matching source-schedule times. Check each cell charge balance against Faraday-scaled reaction extents, solve the Nernst-Planck migration gradient to reproduce the requested interior current, and report ampere residuals and integrated charge; currents are not inferred from mixed-potential or Butler-Volmer kinetics.",
    "caller_evidenced_double_layer_capacitive_current_schedule": "Apply a caller-provided exact-knot, per-cell capacitive-current history to the component-state BDF charge-continuity ledger. Bind the complete schedule digest and licensed Evidence, require exact clock and cell ordering plus review, interpolate within intervals, and integrate signed charge on the same BDF state. This is prescribed-current forcing; it does not solve electrode potential, derive capacitance, or couple to the stage mixed-potential kernel.",
    "caller_digest_bound_planar_slit_inertance_upwind_component_advection": "Bind a committed exact-clock planar-slit inertance history and Evidence-pinned electroneutral inlet/outlet compositions to a fixed-volume component-state BDF mesh. At every BDF RHS state, evaluate signed inertance flow, select upwind aqueous stage concentrations, project species advection to conserved components, and integrate separate left/right component, elemental and charge reservoir exchanges. Requires fixed aperture and caller-reviewed geometry; it does not solve moving boundaries or general momentum flow.",
    "caller_mapped_committed_component_bdf_segment_transition": "Bind a committed, full-digest-pinned component-state BDF result and an Evidence-pinned caller-supplied target segment geometry. Preserve each conserved component mole inventory cellwise at the exact segment boundary, validate component/species identity and aperture-derived solution-volume closure, and construct a typed next-segment BDF request. This is an operator-split boundary transition; it does not derive geometry from deposits, remap across changing cell topology, or feed geometry back within a BDF RHS.",
    "digest_bound_saturation_nucleation_and_growth_kinetic_history": "Apply Evidence-pinned caller saturation intervals and bounded phase-specific molar nucleation/growth/dissolution laws to a closed aqueous batch. Before a caller inventory threshold is met, evaluate the declared supersaturation-dependent nucleation source; thereafter use the caller seeded growth/dissolution law. Delegate each interval to the conservative aqueous/solid kinetic ledger and record phase inventory, element/charge balance and law digests. No automatic thermodynamic phase discovery, particle population balance or qualification is inferred.",
    "caller_evidenced_crevice_molar_nucleation_source": "Define an Evidence/digest-bound caller-calibrated nucleation molar source with critical supersaturation, source coefficient, order, phase inventory seed threshold and rate ceiling. The record is a caller law, not a universal nucleation model or particle-number theory.",
    "caller_fixed_volume_cellwise_seed_threshold_kinetic_ledgers": "Apply digest-bound, exact seed-threshold nucleation/growth ledgers independently to ordered fixed-volume cells, convert concentration histories to cell moles and aggregate after every cell commits. The operator-split adapter has no inter-cell transport or geometry feedback.",
    "caller_component_bdf_then_cellwise_seed_kinetic_operator_split": "For each exact interval, integrate fixed-volume aqueous conserved-component BDF transport, apply independent digest-bound cell seed/growth ledgers, verify species-to-component and aqueous-plus-solid closure, and carry post-kinetic aqueous and solid inventories to the next interval. This sequential operator split rejects source, hydraulic, Faradaic, prescribed-current and moving-geometry modes.",
    "exact_translation_of_absolute_saturation_interval_to_local_ledger_clock": "Translate each absolute caller saturation interval to the zero-origin local clock required by the closed-batch kinetic ledger, pin the derived interval digest, preserve the original source digest and record the exact affine map for absolute event times.",
    "caller_evidenced_dynamic_double_layer_and_faradaic_polarization_curves": "Integrate independent lumped electrode-cell potentials from an exact-knot total-current history, caller-supplied signed polarization tables and a differential-capacitance curve using I_total = I_F + dQ/dt. Interpolate only within declared supports, preserve Evidence digests and fail closed on solver/support/work limits. This does not solve electrolyte ohmic coupling, ionic transport, active-area evolution, or procedure qualification.",
    "caller_evidenced_initial_crevice_double_layer_interfacial_state": "Pin the ordered cell identities, initial and reference interfacial potentials, and the exact differential-capacitance curve digest used to derive initial stored charge. The record is caller-supplied state evidence; it is not inferred from an independently solved voltage history.",
    "same_stage_component_bdf_dynamic_double_layer_spatial_ohmic_faradaic_feedback": "Append one integrated double-layer charge state per fixed-geometry cell to the component BDF. At each trial, invert the caller differential-capacitance charge relation, refresh Nernst potentials and electrolyte conductivity from trial chemistry, reconstruct spatial ohmic face current, evaluate local Butler-Volmer branches, and project Faradaic extents plus charge continuity into the same RHS. The present scope has insulated ionic ends and excludes moving hydraulic boundaries and external circuit-current forcing.",
    "caller_reviewed_dynamic_double_layer_faradaic_result_to_component_bdf_operator_split": "Recompute a digest-pinned independent-cell dynamic potential/Faradaic history, map each caller-reviewed branch to an aqueous reaction extent using its electron number, reverse electrode Cdl current to the aqueous sign convention, and reconstruct exact-knot ionic face currents. Bind schedules to component-state BDF only when species/reaction charge maps and insulated external-current boundaries close at every knot. This is a sequential handoff; BDF chemistry is not fed back into the potential history.",
    "caller_group_separated_transient_slit_flow_parameter_fit": "Fit positive lumped resistance and inertance correction factors to uncertainty-weighted, digest-pinned transient slit-flow observations from independent calibration groups; retain disjoint groups for holdout prediction and report local covariance. This is a caller-selected reduced law fit, not universal hydraulic qualification.",
    "caller_evidenced_solid_molar_volume_gap_occupancy_fixed_point_geometry": "Map caller-evidenced solid inventories to occupied gap volume with phase molar volumes, then update cell aperture, liquid volume and transport face area through a bounded damped stage fixed point. Geometry and occupancy are caller inputs; no mechanics, packing, porosity or kinetic phase evolution is inferred.",
    "bound_crevice_current_carrying_result_to_component_state_schedules": "Bind a fully committed, digest-matched exact-knot CREVICE current-carrying result into a conserved-component BDF request. Preserve cell order, match initial component inventories, convert caller branch current densities to signed per-cell extent-rate schedules using the declared electron number and reactive area, carry ionic face currents, and require review of the sequential reconstruction. Reject stage-re-solved mixed-potential results because endpoint knots cannot reproduce their within-stage current history.",
    "component_state_bdf_stage_spatial_ohmic_butler_volmer_faradaic_coupling": "At each conserved-component BDF trial, reconstruct caller-evidenced aqueous Davies/mass-action equilibrium, re-solve the existing spatial quasi-steady ohmic/Butler-Volmer mixed-potential branches from that trial chemistry, and project the branch extents plus matching electrolyte face current into the same RHS. Require exact chemistry/species/cell/clock alignment, fixed cell and face areas, consistent cell volumes/face areas/center distances, a reviewed branch map and caller extent-rate and solver-work bounds. This bounded mode has no moving-boundary dynamics, double-layer storage, automatic chemistry/phase discovery or material qualification.",
    "caller_reviewed_crevice_double_layer_capacitance_charge_integration": "Integrate a licensed caller-supplied piecewise-linear differential-capacitance-density curve over exact potential knots and reference potentials, multiply by digest-bound active-area histories, and calculate interval-mean current from stored-charge change with charge closure. This reports a caller-waveform double-layer descriptor only; it does not infer potential/area/capacitance, Faradaic kinetics, mixed potential, ionic transport or material qualification.",
    "charge_conserving_double_layer_current_schedule_to_component_bdf": "Recompute caller-pinned double-layer stored charge and require a digest/Evidence-bound piecewise-linear capacitive-current schedule to close the opposite aqueous/electrode charge change on every cell and interval before constructing a typed component-state BDF request. This binding is operator-split and does not solve electrode potential.",
    "caller_evidenced_planar_slit_instantaneous_hydraulic_rhs": "Evaluate a caller-evidenced instantaneous planar-slit resistance/inertance state and signed dQ/dt from current flow, pressure drop, geometry and fluid properties. This is a reusable stage RHS only; it does not integrate time or couple to reactive transport or moving-volume continuity.",
    "caller_reviewed_scc_crack_velocity_time_integration": "Integrate a licensed caller-tabulated, thresholded mode-I stress-intensity-to-crack-velocity law along a finite, piecewise-linear K_I history, splitting intervals exactly at crossed curve knots and refusing extrapolation. The calculation holds material, metallurgy, environment and loading identities fixed and excludes crack-geometry feedback, initiation, probability and qualification.",
    "caller_scc_crack_advance_limit_probability_binding": "Bind a deterministic SCC crack-advance limit history to an existing FTA basic-event exchange contract using a separately caller-supplied finite-period first-failure probability, conditioning, evidence and rights boundary. Recompute and digest-compare the source history; do not infer probability or an exact crossing time.",
    "caller_pinned_fad_curve_and_reviewed_provider_histories": "Evaluate caller-supplied effective mode-I stress intensity, fracture resistance, reference stress and normalizing-strength histories at exact shared time knots against a license-bound, digest-pinned finite FAD curve. Return knot margins and a first outside-boundary interval bracket without extrapolation, crossing-time interpolation, probability or remaining-life inference.",
    "caller_fad_boundary_first_passage_probability_binding": "Bind a recomputed, digest-matched FAD time-history first-boundary event to the existing FTA basic-event contract using only an independent caller-supplied conditional first-failure-in-period probability, conditioning, scope, evidence and rights boundary; reject start-of-period exceedance and never infer probability.",
    "caller_component_total_basis_competing_solid_equilibrium_partition": "Partition one finite caller total-component inventory across aqueous Davies/mass-action species and an ordered set of caller-defined solid phases using bounded sequential coordinate active-set bracketing. Enforce declared component, element and charge closure, active/absent saturation conditions and solver-work budgets; do not claim global Gibbs minimization, uniqueness, nucleation kinetics or BDF coupling.",
    "caller_reviewed_dynamic_slit_pressure_and_boundary_composition_schedule": "Bind a reviewed, digest-fixed pressure-drop and electroneutral reservoir-composition history to a moving-volume slit-transport calculation. The reduced Newtonian laminar slit model uses caller-declared fluid properties, correction factors and support limits; directional volume-rate estimation and physical validation remain explicit limitations.",
    "caller_covariance_for_waveform_heat_input_uncertainty": "Propagate a caller-pinned full covariance for ordered welding voltage/current samples, efficiency and travel distance through the trapezoidal arc-energy and net-heat-input equations with first-order gradients. Validate units, exact coordinate order, finite symmetric positive-semidefinite covariance, evidence/license and bounded sample count. Timing uncertainty, probability distributions, acceptance and procedure qualification are not inferred.",
    "caller_reviewed_tube_bundle_pressure_stress_history": "Evaluate caller-supplied absolute internal/external pressure and current minimum-wall geometry at exact tube-specific time knots using the registered Lamé thick-cylinder solution at inner and outer wall surfaces. Require matched asset/bundle/tube/clock/reference identities, digest-pinned geometry and pressure records, explicit axial-end and uniform axisymmetric elasticity reviews, and bounded work. No pressure capacity, code acceptance or remaining life is inferred.",
    "component_state_bdf_stage_total_component_solid_equilibrium_partition": "Opt-in conserved-component BDF mode treats each cell state as total aqueous-plus-solid component inventory and invokes the bounded solid-partition solver at every trial stage; Nernst-Planck and Faradaic terms use reconstructed aqueous species while knot outputs retain liquid/solid inventories and component/element/charge ledgers. Exact caller phase sets and solver-work budgets are required. This mode excludes kinetic nucleation/precipitation, automatic phase discovery, moving-boundary dynamics, a global Gibbs-minimum claim and qualification.",
    "caller_mapped_component_state_bdf_fixed_segment_handoff": "Verify an exact, result-digest-pinned committed component-state BDF Calculation with closed total-component ledgers, then preserve its final per-cell total component moles as candidate next-segment initial inventory. Caller-reviewed cell geometry, phase molar volumes and gap-occupancy mapping convert final candidate-solid moles to a positive next fixed-segment aperture, volume and interpolated face-area basis. No BDF request mutation, within-stage moving-boundary feedback, reaction, phase discovery or qualification is inferred.",
    "caller_crevice_variable_area_history": "Caller-provided exact-knot cell and face cross-sectional area histories, bound to geometry identity, provider revision, configuration digest, usage license and exact solver clock.",
    "finite_volume_variable_volume_activity_nernst_planck_mass_action": "Independent time-segmented finite-volume integration of species moles in linearly varying cell volumes using face-area-weighted activity-corrected Nernst-Planck/advection fluxes, zero-current closure and caller mass-action sources.",
    "caller_digest_bound_same_stage_solid_kinetic_input_contract": "Bind ordered caller phase candidates, initial solid amounts, nucleation/growth laws, temperature and BDF clock by canonical digest and Evidence pin. This identifies caller inputs, supplies no empirical rates, and makes no qualification claim.",
    "same_stage_activity_based_competing_solid_kinetics_with_seed_depletion_events": "At each spatial component-BDF trial, reconstruct dissolved components from total component inventory and explicit per-phase solid moles, solve local activity-corrected aqueous chemistry, derive phase saturation and evaluate caller-pinned nucleation/growth laws. Integrate solid moles alongside transport/source/hydraulic ledgers and restart at located seed/depletion events. Kinetic parameter values, phase-set completeness, numerical verification and physical qualification remain caller/research responsibilities.",
}


def main():
    registry = default_registry()
    ids = sorted(
        {source for model in registry.list_models() for source in registry.describe(model)["source_ids"]}
        | set(SENSITIVITY_SOURCE_IDS)
        | EXTERNAL_INTERFACE_SOURCE_IDS
        | {"caller_reviewed_dynamic_slit_pressure_and_boundary_composition_schedule",
           "caller_digest_bound_same_stage_solid_kinetic_input_contract"}
    )
    records = []
    for identifier in ids:
        if identifier == "mendeley_aisi1018_aerobic_corrosion_file_inventory":
            records.append(
                dict(
                    id=identifier,
                    basis="public_cc_by_dataset_metadata_and_local_file_inventory",
                    title="Corrosion of AISI 1018 steel by an aerobic bacterial consortium and mitigation by expired ceftriaxone and Justicia spicigera",
                    url="https://data.mendeley.com/datasets/zyy3yktzpf/1",
                    attribution="Mendeley Data v1, DOI https://doi.org/10.17632/zyy3yktzpf.1; contributor Ulises León.",
                    license="CC-BY-4.0 as declared in the Mendeley record; the provider warns that identified third-party content may require separate permission",
                    derivation=(
                        "Verify only the pinned provider file identity, byte count and SHA-256 for the 22 version-1 assets. Preserve optional caller-declared filename labels with user Evidence. Mixed text and OPJ formats do not provide one explicit complete table schema; text and project contents are not parsed and measurement semantics, units, specimens or treatment conditions are not inferred."
                    ),
                    reuse=(
                        "All raw files remain in ignored data/raw and are excluded from release artifacts. Public code contains only a local file inventory. Do not redistribute embedded content or extracted data until the provider's third-party-rights caveat is reviewed for each item. Several ZView text headers identify a 1993 demo.z context that conflicts with the other 2024-2025 instrument metadata; this identity discrepancy is unresolved."
                    ),
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "caller_aisi1018_corrosion_file_mapping":
            records.append(
                dict(
                    id=identifier,
                    basis="caller_declared_mapping_contract",
                    title="Caller-supplied labels for pinned AISI 1018 dataset files",
                    url="https://data.mendeley.com/datasets/zyy3yktzpf/1",
                    attribution="Mapping declarations are supplied by each caller and retain their own Evidence records.",
                    license="No dataset license asserted for caller-authored mapping metadata",
                    derivation="Preserve a caller-authored file label and mapping basis against an exact pinned provider filename. The label is not a validated specimen, treatment, replicate or measurement identity.",
                    reuse="Caller mapping metadata is not vendor or dataset content; callers remain responsible for its provenance and rights.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "caller_crevice_current_branch_metal_mapping":
            records.append(
                dict(
                    id=identifier,
                    basis="caller_declared_material_mapping_contract",
                    title="Caller-supplied CREVICE Faradaic branch-to-metal mapping",
                    attribution="Stoichiometry, metal identity, material property and reactive-area records are supplied by the caller.",
                    license="No external dataset or material-property license asserted; Evidence and reuse rights remain caller supplied.",
                    derivation="Bind reaction extent to a declared metal species, metal moles per extent, molar mass, density and ordered cell reactive areas. The contract performs dimensional conversion only and does not infer corrosion products or material properties.",
                    reuse="Caller must establish provenance, rights, source applicability and the review basis for every mapping and property record.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "caller_crevice_current_branch_disposition":
            records.append(
                dict(
                    id=identifier,
                    basis="caller_declared_reaction_branch_disposition",
                    title="Caller-supplied disposition of CREVICE Faradaic reaction branches",
                    attribution="Branch classification is supplied and reviewed by the caller for the exact source calculation.",
                    license="No external dataset or license asserted; Evidence and reuse rights remain caller supplied.",
                    derivation="Require every source reaction branch to be explicitly mapped as net metal dissolution or excluded as non-dissolution, and bind the ordered decision set to a digest. The software does not classify electrochemical mechanisms.",
                    reuse="Caller is responsible for the evidence, chemical interpretation and rights supporting each branch disposition.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "mendeley_explosive_weld_multilayer_fatigue_rows":
            records.append(
                dict(
                    id=identifier,
                    basis="public_cc_by_dataset_metadata_and_versioned_workbook_row_reader",
                    title="Fatigue test data of corrosion-resistant explosively welded heterostructured plates",
                    url="https://data.mendeley.com/datasets/mc8bc9tm59/1",
                    attribution="Karolczuk, Aleksander; Derda, Szymon; Robak, Grzegorz; Prazmowski, Mariusz (2022), Mendeley Data v1; https://doi.org/10.17632/mc8bc9tm59.1.",
                    license="CC-BY-4.0 as declared by the Mendeley dataset record; identified third-party content may need separate permission",
                    derivation=(
                        "Verify the exact provider filename, byte size and SHA-256 before reading; preserve workbook, worksheet, row and cell order, native stored values/types, and digest lineage. The reader does not infer units, stack-up identity, fatigue relations or corrosion behavior."
                    ),
                    reuse=(
                        "The original workbook remains in ignored data/raw and is excluded from release artifacts. Public code contains only an independently authored structural row reader and metadata. Attribute the versioned dataset, retain transformation notices, and separately review embedded third-party rights before extracted-value redistribution. The observations are study-specific and do not qualify a design, fatigue life or corrosion performance."
                    ),
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "mendeley_az31b_corrosion_fatigue_lab_rows":
            records.append(
                dict(
                    id=identifier,
                    basis="public_cc_by_dataset_metadata_and_versioned_workbook_row_reader",
                    title="Corrosion-fatigue and cold-spray data for AZ31B magnesium alloy",
                    url="https://data.mendeley.com/datasets/5b5rk27wmx/1",
                    attribution="Dataset version 1, DOI https://doi.org/10.17632/5b5rk27wmx.1; related article DOI https://doi.org/10.3390/coatings8120443.",
                    license="CC-BY-4.0 as declared by the Mendeley dataset record; possible third-party content is not covered without separate rights",
                    derivation=(
                        "Use the versioned provider file inventory and SHA-256 values to authorize local reads, then preserve workbook, worksheet, row and cell order, native cell values/types and digest lineage. The reader does not assign plotted-figure semantics, infer units or interpret electrochemical/corrosion-fatigue behavior."
                    ),
                    reuse=(
                        "The eight original workbooks remain in the ignored local data/raw tree and are excluded from release artifacts. Code contains only an independently authored structural reader and metadata. The provider declares CC BY 4.0, but embedded third-party rights may require separate permission. No pointwise data or article prose is redistributed; scientific interpretation, material comparison, calibration and qualification remain unestablished."
                    ),
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "dryad_formate_packer_corrosion_workbook_rows":
            records.append(
                dict(
                    id=identifier,
                    basis="public_dataset_metadata_and_pinned_archive_audit",
                    title="Dryad formate-packer fluid H2S/CO2 corrosion workbook structure reader",
                    url="https://doi.org/10.5061/dryad.p1mf340",
                    license="CC0-1.0 Dryad dataset; linked article CC-BY-4.0 is cited separately",
                    derivation="Verify the provider-declared workbook filename, byte size and MD5 against the local-only workbook, then preserve worksheet rows, cell coordinates/types and source-order digests without assigning figure/table semantics, test conditions, units or measured-versus-summary status.",
                    reuse="The CC0 provider workbook remains in ignored data/raw and is excluded from distributions. Public code contains only an independently authored local reader and contracts; no cell values or article text are copied. Row interpretation and corrosion-model calibration require separate review.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "dryad_downhole_tool_co2_corrosion_dataset_candidate":
            records.append(
                dict(
                    id=identifier,
                    basis="public_dataset_metadata_rights_review_candidate",
                    title="Data from: Mechanism and modelling of CO2 corrosion on downhole tools",
                    url="https://doi.org/10.5061/dryad.fn1r084",
                    attribution="Wang, J.; Meng, L.; Fan, Z.; Liu, Q.; Tong, Z. (2019). Data from: Mechanism and modelling of CO2 corrosion on downhole tools. Dryad. https://doi.org/10.5061/dryad.fn1r084; linked article DOI https://doi.org/10.1098/rsos.181899.",
                    license="CC0-1.0 Dryad dataset; dataset citation retained; linked article rights are separate",
                    derivation="Candidate metadata comes from the Dryad record and its linked article. Repository metadata describes a DOCX with corrosion-rate and elemental-composition data for downhole-tool materials. No file was downloaded or parsed, and no observations, values, prose, figures or tables were copied. File-level rights, row conditions, material mapping and overlap with existing compilations remain unresolved.",
                    reuse="Candidate metadata only. Do not bundle the provider file. Keep any future reader local-only until exact asset/version, source-row provenance and rights are reviewed; CC0 on the deposited dataset does not apply to the linked paper or third-party material.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "ccps_release_history_schema_bridge":
            records.append(
                dict(
                    id=identifier,
                    basis="pinned_external_api_contract",
                    title="CCPS Toolkit release-history request/result API contract",
                    url="https://github.com/lyullee/process-risk-consequence-toolkit/tree/4106da0020196fcf61c8b6264ae0598e63a881a1/contracts",
                    repository="lyullee/process-risk-consequence-toolkit",
                    reviewed_commit="4106da0020196fcf61c8b6264ae0598e63a881a1",
                    contract_id="ccps.release-history.v1",
                    request_schema="contracts/ccps.release_history_request.v1.schema.json",
                    request_schema_sha256="025c2df40b84dbd75b30295f6445416032500db9a549b343fa2cf0ff656ce707",
                    result_schema="contracts/ccps.release_history_result.v1.schema.json",
                    result_schema_sha256="4085015227fdee8d2c9e04da06d1e64b5f4a60e5b6f28f913addac66069d2c6d",
                    derivation="Define an independently authored typed adapter against caller-verified request/result contract bytes pinned to the reviewed repository commit. The adapter exports requests only and does not execute the provider or infer physical qualification.",
                    reuse="Contract metadata and digests identify the external API only. No external implementation, prose, empirical values or assets are copied; no license claim is made for the adapter or external material.",
                    limits="Supports only the pinned release-history contract and its declared approximation boundary. It does not infer release from wall loss or establish consequences or risk qualification.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "ince_glinka_generalized_strain_amplitude":
            title, url = REFERENCES["ince_glinka_gsa_2017"]
            records.append(
                dict(
                    id=identifier,
                    basis="cc_by_4_0_published_method_independent_code",
                    title=title,
                    url=url,
                    license="CC-BY-4.0 article; attribution required; no article text, tables or experimental values bundled",
                    derivation=DERIVATIONS[identifier],
                    reuse="Attribution to the cited article and independently authored implementation only; no pointwise fatigue data or article prose is redistributed.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "zenodo_mg_deis_archive_structure":
            records.append(
                dict(
                    id=identifier,
                    basis="cc0_zenodo_dataset_local_reader",
                    title="WE43/AZ31 molybdate DEIS archive structure and raw matrix reader",
                    url="https://doi.org/10.5281/zenodo.10482561",
                    license="CC0-1.0 declared by the dataset depositor; attribution is retained as scholarly provenance",
                    derivation=DERIVATIONS[identifier],
                    reuse="Raw archive remains in the ignored local research cache; package artifacts contain reader code and metadata only, without pointwise values or provider files.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "zenodo-ti12mo5hf-oxygen-corrosion":
            records.append(
                dict(
                    id=identifier,
                    basis="cc0_zenodo_dataset_local_archive_audit",
                    title="Ti-12Mo-5Hf oxygen interstitial corrosion dataset: local archive audit",
                    url="https://doi.org/10.5281/zenodo.19462164",
                    license="CC0-1.0 declared by the dataset depositor; preserve dataset citation",
                    derivation=DERIVATIONS[identifier],
                    reuse="Reader code and provider-described metadata only; no dataset archive, workbook cells, measurements or images are redistributed.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "zenodo-ti12mo5zr-aqueous-corrosion":
            records.append(
                dict(
                    id=identifier,
                    basis="cc0_zenodo_dataset_local_row_reader",
                    title="Ti-Mo-Zr aqueous hydrogen-peroxide corrosion archive: pinned OCP, EIS and AESEC row access",
                    url="https://doi.org/10.5281/zenodo.14981665",
                    license="CC0-1.0 declared by the dataset depositor; scholarly citation is retained",
                    derivation=DERIVATIONS[identifier],
                    reuse="Only reader code and reviewed metadata are distributed. The raw ZIP and point measurements stay in the ignored local cache.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "zenodo_18735817_cathodic_protection_typed_rows":
            records.append(
                dict(
                    id=identifier,
                    basis="cc_by_4_0_zenodo_local_typed_row_reader",
                    title="Cathodic-protection OCP and polarization export reader",
                    url="https://doi.org/10.5281/zenodo.18735817",
                    license="CC-BY-4.0 declared by the dataset depositor; attribution required; local-only use is enforced by this adapter authorization contract",
                    derivation=DERIVATIONS[identifier],
                    reuse="The provider CSV files are not redistributed. Fixed SHA-256 values are local-copy integrity pins, not publisher checksums. Sample rows require caller attribution and local/computational-use authorization.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "zenodo_galvanized_polarization_typed_rows":
            records.append(
                dict(
                    id=identifier,
                    basis="cc_by_4_0_zenodo_local_polarization_row_reader",
                    title="Low carbon steel formed by DRECE method with hot dip zinc galvanizing and potentiodynamic polarization tests to study its corrosion behavior",
                    url="https://doi.org/10.5281/zenodo.13886478",
                    license="CC-BY-4.0 declared by the dataset depositor; attribution required; caller authorization keeps raw row access local to the user's environment",
                    derivation=DERIVATIONS[identifier],
                    reuse="The selected polarization spreadsheets are not redistributed. Their MD5 values are checked against the catalog, with local SHA-256 added for file/row lineage. Do not bundle measurements or source documents.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "aquasoldb_gas_solubility_v2_1_audit":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="public_cc_by_compilation_and_private_archive_structure_audit",
                    title=title,
                    url=url,
                    license=(
                        "CC-BY-4.0 for compiler's selection, arrangement and metadata only; cited "
                        "experimental measurements are not licensed by the compiler and must be "
                        "attributed to their original sources"
                    ),
                    derivation=(
                        "Verify the fixed-version archive digest and archive member manifest, then "
                        "inspect only schema, gas/medium coverage, status/flag counts and aggregate "
                        "CO2 applicability. Do not derive a Henry coefficient from finite-pressure "
                        "solubility without a separately reviewed fugacity and thermodynamic basis."
                    ),
                    reuse=(
                        "The raw archive remains in the excluded data/raw tree. Public output is "
                        "limited to attributed aggregate audit results and independently authored "
                        "reader logic; do not redistribute point values, source reference text or "
                        "pointwise derived quantities. Any future use of a measurement requires "
                        "its original paper citation and rights/applicability review."
                    ),
                    checked_on="2026-10-29",
                )
            )
            continue
        if (
            identifier
            == "small_strain_j2_associative_return_mapping_with_linear_prager_kinematic_and_isotropic_hardening"
        ):
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="published_constitutive_method_cited_independent_code",
                    title=title,
                    url=url,
                    license="The cited publications remain under their respective terms; this project distributes an independently authored constitutive implementation, not article prose, figures, tables, or measurements.",
                    derivation=DERIVATIONS[identifier],
                    reuse="Bibliographic and mathematical provenance only. No source implementation or calibration data is bundled.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier in {
            "paolinelli_nesic_2021_chilton_colburn_liquid_transfer",
            "paolinelli_nesic_2021_chilton_colburn_gas_film",
        }:
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="published_method_cited_independent_code",
                    title=title,
                    url=url,
                    license="The cited journal article is copyrighted; this project distributes only independently authored code and bibliographic metadata, not article prose, figures, tables, or measurements.",
                    derivation=DERIVATIONS[identifier],
                    reuse="Citation is retained as technical provenance. The implementation is separately authored, and no publisher manuscript or experimental dataset is redistributed.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "plos_ct110_wet_co2_typed_rows":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="cc_by_4_0_local_typed_row_reader",
                    title=title,
                    url=url,
                    license="CC-BY-4.0 declared by PLOS Figshare; attribution and license link retained; source workbook stays in ignored local data/raw",
                    derivation=DERIVATIONS[identifier],
                    reuse=(
                        "Only the independently authored reader, source metadata and attributed row lineage are distributed. "
                        "The workbook is excluded from packages. Its provider MD5 and observed local SHA-256 are integrity "
                        "pins, not evidence of replicate independence or engineering qualification."
                    ),
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "ct110_weld_corrosion_supplement":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="public_cc_by_experimental_dataset_and_attributed_transcription",
                    title=title,
                    url=url,
                    license="CC-BY-4.0 supplementary datasets; retain attribution, DOI, license link and transformation note",
                    derivation=(
                        "Read the two versioned supplementary spreadsheets from the Figshare API, preserve "
                        "the six weld/base-metal weight-loss rate pairs and reported condition sweeps, and "
                        "convert the attributed mm/year values to SI m/s only in the project fixture."
                    ),
                    reuse=(
                        "The public fixture contains attributed, unit-converted reported rates under the "
                        "provider-declared CC BY 4.0 license. Raw workbooks remain outside releases. The "
                        "supplement does not identify physical coupons, replicate counts or uncertainty; "
                        "these data are one-study descriptive evidence, not general calibration or validation."
                    ),
                    checked_on="2026-10-29",
                )
            )
            continue
        if identifier == "seccm_316l_pitting_reader":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="public_correlative_electrochemistry_dataset_reader",
                    title=title,
                    url=url,
                    license="CC-BY-4.0",
                    derivation=(
                        "Verify the provider archive and independently preserve its exact membership, raw "
                        "two-row CA headers, map IDs, seconds and substrate-current amperes. The MIT provider "
                        "notebook at pinned commit 5ae5802d189cb100d0071b8efc557805060fcdf6 was inspected "
                        "only as format and unit evidence and was not executed or copied."
                    ),
                    reuse=(
                        "Attribution and independently authored raw-signal reader only. Raw and derived tables "
                        "remain outside distributions. Map sites are not independent specimens, and provider "
                        "descriptor extraction, normalization, labels, fits and cross-table alignments are not "
                        "reproduced or qualified."
                    ),
                    checked_on="2026-10-27",
                )
            )
            continue
        if identifier == "aa7050_local_pitting_reader":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="public_local_pitting_dataset_reader",
                    title=title,
                    url=url,
                    license="CC-BY-4.0",
                    derivation=(
                        "Verify caller-pinned file digests and preserve top-level real numeric MATLAB "
                        "variable names, classes, dtypes, shapes and nonfinite values without transforming arrays."
                    ),
                    reuse=(
                        "Attribution, independently authored reader and aggregate structure audit only. Raw MAT "
                        "arrays remain outside public distributions. One specimen and two exposure files are not "
                        "promoted to independent specimens, a general growth law, transition probabilities or POD."
                    ),
                    checked_on="2026-10-27",
                )
            )
            continue
        if identifier == "ceit_pulse_echo_method":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="public_method_and_calibration_reference",
                    title=title,
                    url=url,
                    license="CC-BY-4.0",
                    derivation=(
                        "Independently apply the longitudinal pulse-echo round-trip identity using a "
                        "caller-reviewed material/probe calibration. The reference documents one "
                        "laboratory sound-speed calibration, but that value is not made a field-data default."
                    ),
                    reuse=(
                        "Attribution and paraphrased method facts only. No article prose, figures, tables, "
                        "pointwise observations or upstream implementation are distributed."
                    ),
                    checked_on="2026-10-27",
                )
            )
            continue
        if identifier == "ceit_uniform_corrosion_field_reader":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="public_field_dataset_reader",
                    title=title,
                    url=url,
                    license="CC-BY-4.0",
                    derivation=(
                        "Verify the pinned JSON digest, exact record schema, strictly increasing provider "
                        "clock, device identities and finite raw, filtered, correlation and envelope arrays. "
                        "Preserve reported ToF and temperature without assigning units unless reviewed."
                    ),
                    reuse=(
                        "Attribution, independently authored reader and aggregate inspection only. Raw "
                        "observations and waveforms remain outside public source distributions. No thickness "
                        "or corrosion rate is derived without a qualified wave speed, path and calibration."
                    ),
                    checked_on="2026-10-27",
                )
            )
            continue
        if identifier == "coqtel_dataset_reader":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="public_experimental_dataset_reader",
                    title=title,
                    url=url,
                    license="CC-BY-4.0",
                    derivation=(
                        "Verify the two pinned HDF5 file digests, consecutive State_i to EC-row "
                        "alignment, nondecreasing electrochemical clocks, waveform matrices, signal "
                        "metadata, two-specimen boundary and the reported experiment-2 bubble interval."
                    ),
                    reuse=(
                        "Attribution, independently authored readers and aggregate inspection only. "
                        "Raw waveforms, electrochemical rows and images remain outside public source "
                        "distributions. Charge and waveform change are not relabelled as pit dimensions."
                    ),
                    checked_on="2026-10-27",
                )
            )
            continue
        if identifier == "wet_co2_hainan_secondary_evidence":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="official_secondary_reproduction_crosswalk",
                    title=title,
                    url=url,
                    license="publication-rights-not-cleared-for-redistribution",
                    derivation=(
                        "Parse only the five location rows reproduced in the pinned official article "
                        "response. Apply the article-declared kPa-to-bar transforms and its two-phase "
                        "wall-shear arithmetic mean, then search the compilation for one unique match "
                        "on six non-response fields before comparing corrosion rate."
                    ),
                    reuse=(
                        "Aggregate match counts and independently authored audit logic only. The API "
                        "response and pointwise table remain outside public distributions; five "
                        "reproduced rows do not qualify the unreproduced fifty-five rows."
                    ),
                    checked_on="2026-10-27",
                )
            )
            continue
        if identifier == "wet_co2_egua_publisher_preview":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="publisher_preview_availability_audit",
                    title=title,
                    url=url,
                    license="publisher-all-rights-reserved",
                    derivation=(
                        "Inspect the pinned twelve-page publisher preview and record only metadata: "
                        "the target title occurs in the contents page, while the rendered body starts "
                        "a different article and contains neither the target DOI nor its observation tables."
                    ),
                    reuse=(
                        "Metadata and negative availability evidence only. The preview PDF, article "
                        "prose, figures and tables remain outside public distributions."
                    ),
                    checked_on="2026-10-27",
                )
            )
            continue
        if identifier == "wet_co2_literature_crosswalk":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="caller_held_literature_crosswalk",
                    title=title,
                    url=url,
                    license="CC-BY-NC-ND-4.0",
                    derivation=(
                        "Compare caller-supplied literature values to one compilation row using only "
                        "explicit reviewed affine or arithmetic-mean mappings. Preserve source and "
                        "compilation values, missingness, tolerance and every mismatch without "
                        "altering the compilation row or assigning calibration readiness."
                    ),
                    reuse=(
                        "Independently authored comparison contracts and aggregate facts only. The "
                        "accepted manuscript, extracted tables and pointwise evidence remain outside "
                        "public distributions; publication access is kept separate from rights in "
                        "the underlying observations."
                    ),
                    checked_on="2026-10-27",
                )
            )
            continue
        if identifier == "caller_wet_co2_simulation_rows_to_wall_loss_scenarios":
            title, url = REFERENCES["wet_co2_simulation_source_crosswalk"]
            records.append(
                dict(
                    id=identifier,
                    basis="cc_by_4_0_attributed_finite_simulation_scenario_adapter",
                    title=title,
                    url=url,
                    license="CC-BY-4.0 dataset attribution is retained; provider simulation outputs are not physical observations",
                    derivation=DERIVATIONS[identifier],
                    reuse="Uses only caller-supplied exact provider rows and digest-bound local metadata; no provider workbook or NORSOK standard content is redistributed. No row-derived surrogate, field forecast, probability or qualification is claimed.",
                    checked_on="2026-10-31",
                )
            )
            continue
        if identifier == "wet_co2_simulation_source_crosswalk":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="public_dataset_crosswalk",
                    title=title,
                    url=url,
                    license="CC-BY-4.0",
                    derivation=(
                        "Verify the pinned provider workbook hash, one-sheet layout, eight headers, "
                        "unit table and 243 finite numeric rows. The reader converts only the declared "
                        "temperature, pressure, efficiency and corrosion-rate units to SI, attaches the "
                        "pinned source digest and CC-BY attribution, and labels every record as a "
                        "simulated-model output. Its equal-row summary reports only provider-table "
                        "ranges, arithmetic means and caller-level empirical quantiles without "
                        "probability claims. Separately require an exact positional eight-value "
                        "match to compilation provider rows 2 through 244 before assigning that source "
                        "group; the remaining 184 rows are not inferred from aggregate counts or missingness."
                    ),
                    reuse=(
                        "The workbook is fetched on demand and is not included in distributions. The "
                        "typed reader returns source rows with attribution, license, source digest and "
                        "simulation status so callers can use the dataset under its CC-BY terms. This "
                        "license is not treated as permission to redistribute NORSOK M-506 standard "
                        "content, implementation code or a surrogate trained on the provider grid."
                    ),
                    checked_on="2026-10-27",
                )
            )
            continue
        if identifier == "nist_corr_data_archive_structure_audit":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="public_dataset_metadata_and_pinned_archive_audit",
                    title=title,
                    url=url,
                    license=(
                        "NIST Open License as listed by Data.gov; underlying source-document rights "
                        "remain record-specific"
                    ),
                    derivation=(
                        "Verify the published archive hash, exact archive members, CSV schema, row "
                        "widths, field coverage and mixed scalar/rating/text tokens. Store only "
                        "aggregate structural counts and member digests; do not emit provider "
                        "observations or citation text."
                    ),
                    reuse=(
                        "The source database is locally acquired from the public NIST endpoint and "
                        "excluded from package artifacts. No row values, comments, citations, source "
                        "document text, fitted material correlations or legacy advisory behavior are "
                        "copied into public code or generated catalogs. Modeling use remains gated "
                        "on source-row provenance, applicable rights and engineering review."
                    ),
                    checked_on="2026-10-29",
                )
            )
            continue
        if identifier == "mendeley_304l_chloride_scc_archive_audit":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="public_cc_by_dataset_metadata_and_versioned_archive_audit",
                    title=title,
                    url=url,
                    license="CC-BY-4.0 dataset-level declaration; embedded third-party rights need review",
                    derivation=(
                        "Verify versioned provider archive bytes and SHA-256, nested archive membership, "
                        "workbook sheet dimensions and aggregate formula/nonempty-cell counts. Do not "
                        "emit workbook labels, headers or pointwise values."
                    ),
                    reuse=(
                        "The provider version is cached outside package artifacts. The provider checksum "
                        "is unavailable, so the project records the observed digest without presenting "
                        "it as a publisher checksum. The workbook contains formulas and very wide sheet "
                        "dimensions; numerical interpretation, specimen hierarchy and third-party rights "
                        "remain unqualified. No raw or pointwise data is copied into public code."
                    ),
                    checked_on="2026-10-29",
                )
            )
            continue
        if identifier == "pytzer_optional_gpl_provider_metadata":
            title, url = REFERENCES[identifier]
            records.append(
                dict(
                    id=identifier,
                    basis="optional_external_software_license_and_status_review",
                    title=title,
                    url=url,
                    license="GPLv3; beta software according to upstream documentation; not bundled or imported by this project",
                    reuse=(
                        "Metadata and callback interoperability only. Users who choose Pytzer must install and use it separately under its applicable GPLv3 terms and pin the software and parameter-library revision. The project contains no Pytzer source code, parameter tables or transcribed equations from that software."
                    ),
                    checked_on="2026-10-30",
                )
            )
            continue
        if identifier in REFERENCES:
            title, url = REFERENCES[identifier]
            sit_reference = identifier in {
                "nea_thermochemical_database_sit_method",
                "usgs_phreeqc_sit_model_documentation",
            }
            records.append(
                dict(
                    id=identifier,
                    basis="public_method_reference",
                    title=title,
                    url=url,
                    **(
                        {
                            "derivation": "The caller-parameterized SIT expression is independently implemented from the cited mathematical method. No prose, figures, fitted epsilon values, thermochemical tables or source code are copied."
                        }
                        if sit_reference
                        else {}
                    ),
                    reuse=(
                        "Citation only; the source document and parameter tables are not included. Users must establish rights, provenance, temperature/solvent basis and applicability for each parameter set."
                        if sit_reference
                        else "Reference only; no source prose, figures, tables or implementation copied. Libraries are called as dependencies where identified."
                    ),
                    checked_on=(
                        "2026-10-30"
                        if sit_reference
                        else "2026-10-27"
                        if identifier
                        in {
                            "iupac_fugacity_definition",
                            "nist_tn1297_uncertainty_propagation",
                            "sandia_helpr_v2_1_0",
                            "hymatbase_4130x_hydrogen_fatigue_reader",
                            "oxford_ebsd_defdap_reader",
                        }
                        else "2026-10-26"
                    ),
                )
            )
        elif identifier in DERIVATIONS:
            records.append(
                dict(
                    id=identifier,
                    basis="independent_algebraic_implementation",
                    derivation=DERIVATIONS[identifier],
                    reuse="No external empirical parameter table bundled; see model assumptions and verification tests.",
                )
            )
        else:
            raise ValueError(f"missing implementation-basis record: {identifier}")
    target = ROOT / "data/catalogs/sources.json"
    target.write_text(
        json.dumps(
            dict(schema_version="matintegrity.sources.v1", sources=records), ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    print(f"Recorded {len(records)} implementation bases")


if __name__ == "__main__":
    main()

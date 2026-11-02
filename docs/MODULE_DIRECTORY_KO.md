# 전체 단위 모듈 설명서

각 링크에는 목적, 모든 최상위 입력, 필수 여부, 기본값·제약, 전체 중첩 스키마, 선언 출력 단위, 호출 방법, 적용 한계, 구현 위치와 예제 보유 여부가 있다.

[README의 요약표](../README.md) · [기계 판독 API 목록](API_DIRECTORY.json)

## adapter: 다른 시스템으로 결과 전달

| API | 목적 |
|---|---|
| [`adapter.corrosion_rate_history_to_fault_tree_basic_event`](modules/api/adapter.corrosion_rate_history_to_fault_tree_basic_event.md) | The deterministic corrosion calculation defines the reviewed condition and finite support but never supplies an event probability. |
| [`adapter.crevice_faradaic_to_fault_tree_basic_event`](modules/api/adapter.crevice_faradaic_to_fault_tree_basic_event.md) | Only a computed integration.crevice_faradaic_spatial_chemistry_coupling result whose model ID, exact request digest, assessment ID and all interval endpoints match is eligible for binding. |
| [`adapter.fad_assessment_history_to_fault_tree_basic_event`](modules/api/adapter.fad_assessment_history_to_fault_tree_basic_event.md) | Only the exact computed structural.failure_assessment_history result for the supplied request is eligible; the full deterministic source calculation is recomputed and digest-compared. |
| [`adapter.scc_crack_growth_to_fault_tree_basic_event`](modules/api/adapter.scc_crack_growth_to_fault_tree_basic_event.md) | Only the exact computed degradation.scc_crack_velocity_history result for the supplied request is eligible; the complete source calculation is recomputed and digest-compared. |

## calibration: 재료·수송·관측 계수 보정

| API | 목적 |
|---|---|
| [`calibration.crevice_slit_hydraulic_law_parameters`](modules/api/calibration.crevice_slit_hydraulic_law_parameters.md) | Fit only two positive global correction multipliers on the caller-declared reduced lumped slit law; each observation record is digest-pinned. |

## chemistry: 수용액·활동도·평형·고체 반응

| API | 목적 |
|---|---|
| [`chemistry.aqueous_bdot_self_consistent_speciation`](modules/api/chemistry.aqueous_bdot_self_consistent_speciation.md) | Caller-defined aqueous mass-action balances are iterated with species-specific extended Debye-Huckel B-dot coefficients evaluated from the resulting molal ionic strength. |
| [`chemistry.aqueous_davies_self_consistent_speciation`](modules/api/chemistry.aqueous_davies_self_consistent_speciation.md) | Caller-defined square aqueous equilibrium/constraint system is solved repeatedly while Davies coefficients are recalculated from speciation-derived molal ionic strength. |
| [`chemistry.aqueous_extended_debye_huckel_activity`](modules/api/chemistry.aqueous_extended_debye_huckel_activity.md) | All Debye-Huckel A/B coefficients, ionic-strength support, and charged-species ion-size parameters are caller supplied and Evidence-bound. |
| [`chemistry.aqueous_extended_debye_huckel_self_consistent_speciation`](modules/api/chemistry.aqueous_extended_debye_huckel_self_consistent_speciation.md) | Caller-defined square mass-action constraints are solved repeatedly while extended Debye-Huckel gamma is updated from speciation-derived ionic strength. |
| [`chemistry.aqueous_mass_action_scenario_envelope`](modules/api/chemistry.aqueous_mass_action_scenario_envelope.md) | Each complete scenario is caller-provided and solved independently by the existing fixed-topology aqueous mass-action solver. |
| [`chemistry.aqueous_mass_action_speciation`](modules/api/chemistry.aqueous_mass_action_speciation.md) | Caller-supplied single-phase aqueous species, fixed activity coefficients, mass-action equilibrium constants, charge-balanced signed reaction stoichiometry, optional complete reviewed elemental formulas, linear analytical/charge constraints and explicit positive initial activities. |
| [`chemistry.aqueous_mass_action_topology_envelope`](modules/api/chemistry.aqueous_mass_action_topology_envelope.md) | Each case is a complete caller-declared single-liquid mass-action network using the same solution identity, temperature, species inventory, fixed activities, provider record, standard state and balance constraints. |
| [`chemistry.aqueous_reaction_candidate_enumeration`](modules/api/chemistry.aqueous_reaction_candidate_enumeration.md) | Complete caller-supplied formulas and ionic charges define a bounded integer search; candidates satisfy atom and charge conservation within the declared species set and total order. |
| [`chemistry.aqueous_saturation_history_events`](modules/api/chemistry.aqueous_saturation_history_events.md) | Audit threshold crossings between caller-computed, strictly ordered saturation-ratio knots by reviewed piecewise-linear interpolation. |
| [`chemistry.aqueous_saturation_screen`](modules/api/chemistry.aqueous_saturation_screen.md) | Caller-supplied dimensionless aqueous activities, activity standard state, candidate-solid activity products, and temperature-applicable solubility products. |
| [`chemistry.aqueous_sit_self_consistent_speciation`](modules/api/chemistry.aqueous_sit_self_consistent_speciation.md) | Caller-defined square aqueous mass-action equations are iterated with caller-parameterized SIT coefficients evaluated from the resulting molal ionic inventory and directional interaction records. |
| [`chemistry.aqueous_tabulated_activity_speciation`](modules/api/chemistry.aqueous_tabulated_activity_speciation.md) | Caller-defined single-liquid mass-action equations are iterated with species-specific caller activity tables using bounded piecewise-linear interpolation of ln(gamma) in ionic strength and, when supplied, temperature. |
| [`chemistry.aqueous_thermodynamic_cycle_audit`](modules/api/chemistry.aqueous_thermodynamic_cycle_audit.md) | All species formulas, charges, activity standard state, temperature and equilibrium-constant records are caller supplied and explicitly reviewed. |
| [`chemistry.caller_scale_coverage_kinetics`](modules/api/chemistry.caller_scale_coverage_kinetics.md) | A caller-supplied first-order surface-coverage attachment/detachment law uses a closed-form solution for constant saturation and adaptive RK4 step doubling for reviewed piecewise-linear saturation paths. |
| [`chemistry.caller_surface_scale_kinetics`](modules/api/chemistry.caller_surface_scale_kinetics.md) | Integrate caller-calibrated single-phase precipitation and dissolution flux laws over constant or explicitly reviewed linear saturation intervals, with inventory-bounded dissolution. |
| [`chemistry.carbonate_alkalinity_speciation`](modules/api/chemistry.carbonate_alkalinity_speciation.md) | Aqueous carbonate-only alkalinity balance with caller activity-based K1, K2, Kw and activity coefficients. |
| [`chemistry.co2_henry_vant_hoff_temperature_correction`](modules/api/chemistry.co2_henry_vant_hoff_temperature_correction.md) | The caller supplies a Henry solubility coefficient, dissolution enthalpy, optional constant heat-capacity change, solvent identity, thermochemical support and source lineage. |
| [`chemistry.competitive_solid_bdot_equilibrium`](modules/api/chemistry.competitive_solid_bdot_equilibrium.md) | The caller supplies temperature-matched, Evidence-linked extended Debye-Huckel A/B, ion-size and B-dot parameters for every phase species. |
| [`chemistry.competitive_solid_davies_equilibrium`](modules/api/chemistry.competitive_solid_davies_equilibrium.md) | Caller-declared competing neutral pure-solid equilibrium is iterated with Davies coefficients recalculated from the resulting single-liquid ionic strength. |
| [`chemistry.competitive_solid_equilibrium`](modules/api/chemistry.competitive_solid_equilibrium.md) | Caller-declared competing neutral pure solids in one fixed-volume liquid with fixed activity coefficients; candidate phase list, stoichiometry and source-backed equilibrium constants are explicit. |
| [`chemistry.competitive_solid_kinetic_ledger`](modules/api/chemistry.competitive_solid_kinetic_ledger.md) | Apply caller-supplied signed phase extent rates sequentially with explicit solid-inventory and common aqueous-reactant limits; verify elemental and charge ledgers. |
| [`chemistry.competitive_solid_saturation_kinetics`](modules/api/chemistry.competitive_solid_saturation_kinetics.md) | Map caller-reviewed interval saturation ratios to per-phase precipitation or dissolution power-law rates, then apply the existing elemental/charge-conserving solid inventory limiter. |
| [`chemistry.competitive_solid_sit_equilibrium`](modules/api/chemistry.competitive_solid_sit_equilibrium.md) | The caller supplies source-linked directional SIT interactions, temperature-specific A, standard-state mapping and complete phase chemistry; aqueous ionic strength is limited to the caller ceiling, capped at 6 mol/kg. |
| [`chemistry.crevice_activity_based_reaction_rates`](modules/api/chemistry.crevice_activity_based_reaction_rates.md) | Caller supplies one positive single-liquid state, single-ion activity coefficients and reversible rate records on a dimensionless activity basis. |
| [`chemistry.crevice_aqueous_kinetic_network`](modules/api/chemistry.crevice_aqueous_kinetic_network.md) | Finite caller-declared species and element/charge-balanced reversible reactions in a single constant-volume mixed liquid. |
| [`chemistry.crevice_bdf_kinetic_phase_set`](modules/api/chemistry.crevice_bdf_kinetic_phase_set.md) | The contract binds exact ordered caller phase and kinetic-law records; it does not calculate a trajectory. |
| [`chemistry.crevice_closed_batch_aqueous_equilibrium`](modules/api/chemistry.crevice_closed_batch_aqueous_equilibrium.md) | A complete explicit constraint role map distinguishes dynamic conserved components from caller-fixed targets and exact zero-target charge neutrality. |
| [`chemistry.crevice_competing_solid_equilibrium`](modules/api/chemistry.crevice_competing_solid_equilibrium.md) | One fixed, homogeneous solution volume and one temperature are used with fixed caller activity coefficients and standard states. |
| [`chemistry.crevice_component_solid_partition`](modules/api/chemistry.crevice_component_solid_partition.md) | Total component inventory includes all liquid and candidate solid material; the caller reviews candidate-set completeness and instantaneous equilibrium applicability. |
| [`chemistry.crevice_nucleation_kinetic_history`](modules/api/chemistry.crevice_nucleation_kinetic_history.md) | Saturation is caller supplied and held constant over each exact interval. |
| [`chemistry.crevice_spatial_activity_solid_fixed_point`](modules/api/chemistry.crevice_spatial_activity_solid_fixed_point.md) | Each caller cell is solved independently at one fixed geometry knot using the existing Davies activity/speciation and finite competing-solid equilibrium evaluators. |
| [`chemistry.crevice_steady_wall_sink`](modules/api/chemistry.crevice_steady_wall_sink.md) | One dissolved species follows steady one-dimensional diffusion and irreversible first-order wall consumption in a caller-reviewed fixed blind slit. |
| [`chemistry.crevice_transient_wall_sink`](modules/api/chemistry.crevice_transient_wall_sink.md) | One dissolved species follows fixed-geometry one-dimensional diffusion with a fixed-concentration mouth, zero-flux blind tip and first-order wall sink. |
| [`chemistry.davies_activity_coefficients`](modules/api/chemistry.davies_activity_coefficients.md) | Ionic strength is calculated from the caller-reviewed complete molal species inventory; electroneutrality is checked against an explicit tolerance. |
| [`chemistry.fixed_fugacity_carbonate_equilibrium`](modules/api/chemistry.fixed_fugacity_carbonate_equilibrium.md) | Fixed caller-supplied CO2 fugacity reservoir and Henry coefficient at the sample temperature; carbonate-only aqueous activity equilibrium and total-alkalinity closure. |
| [`chemistry.fixed_fugacity_carbonate_history`](modules/api/chemistry.fixed_fugacity_carbonate_history.md) | Solves each caller-supplied fixed-fugacity carbonate/alkalinity state at one exact ordered time point; no interpolation or kinetics are added. |
| [`chemistry.fixed_fugacity_carbonate_scenario_ensemble`](modules/api/chemistry.fixed_fugacity_carbonate_scenario_ensemble.md) | Each row is a complete reviewed fixed-fugacity carbonate-equilibrium case with common sample identity and caller-normalized weights. |
| [`chemistry.layered_scale_diffusion_limit`](modules/api/chemistry.layered_scale_diffusion_limit.md) | Caller-supplied layered effective diffusivity, partition coefficients, thickness, concentration endpoints and covered-area fraction define a steady diffusion-limit bound. |
| [`chemistry.layered_scale_history_series_transport`](modules/api/chemistry.layered_scale_history_series_transport.md) | One digest-pinned, caller-calibrated thickness history is supplied for each ordered diffusion layer, with identical exact time knots and shared physical context. |
| [`chemistry.layered_scale_history_stack_transport`](modules/api/chemistry.layered_scale_history_stack_transport.md) | Bind one exact common time knot from a distinct caller-calibrated single-phase thickness history into every named layer of an ordered transport stack. |
| [`chemistry.pitzer_salt_finite_scenario_envelope`](modules/api/chemistry.pitzer_salt_finite_scenario_envelope.md) | All scenarios share one caller-reviewed pure-salt formula and temperature and retain their supplied order. |
| [`chemistry.pitzer_salt_saturation_index`](modules/api/chemistry.pitzer_salt_saturation_index.md) | One caller-reviewed pure-salt Pitzer calculation and one temperature-matched caller Ksp record share the declared mean-ionic standard state. |
| [`chemistry.pitzer_single_salt_activity`](modules/api/chemistry.pitzer_single_salt_activity.md) | One pure aqueous electrolyte with a caller-reviewed electroneutral formula, molality-scale Pitzer-Debye-Huckel Aphi/b, beta0/beta1/beta2 and Cphi parameters inside caller-declared temperature and ionic-strength support. |
| [`chemistry.planar_scale_diffusion_reaction_history`](modules/api/chemistry.planar_scale_diffusion_reaction_history.md) | Fixed-area dense single-phase planar scale; one-to-one transported-species/solid molar balance. |
| [`chemistry.planar_scale_reaction_demand_balance`](modules/api/chemistry.planar_scale_reaction_demand_balance.md) | Single dense planar scale with quasi-steady diffusion/interface resistance and caller constant consuming reaction demand per interval. |
| [`chemistry.scale_precipitation_inventory_budget`](modules/api/chemistry.scale_precipitation_inventory_budget.md) | Use the gross per-area precipitation amounts from one exact digest-pinned caller scale history and multiply by one caller-declared exposed area. |
| [`chemistry.single_solid_precipitation_equilibrium`](modules/api/chemistry.single_solid_precipitation_equilibrium.md) | One explicitly declared neutral pure solid with fixed activity coefficients/solution volume and atom/charge-conserving extent; no competing phases or kinetic prediction. |
| [`chemistry.sit_activity_coefficients`](modules/api/chemistry.sit_activity_coefficients.md) | The caller provides every used directional interaction coefficient and reviews completeness, units, temperature and applicability. |
| [`chemistry.solution_concentration_conversion`](modules/api/chemistry.solution_concentration_conversion.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`chemistry.wet_co2_neutral_solid_formula_proposals`](modules/api/chemistry.wet_co2_neutral_solid_formula_proposals.md) | For every caller-listed positive cation and negative anion, reduce integer stoichiometric coefficients to the smallest charge-neutral pair and sum declared elemental formulae. |

## corrosion: 부식속도·전류·손실·틈 부식

| API | 목적 |
|---|---|
| [`corrosion.atmospheric_first_year_fit`](modules/api/corrosion.atmospheric_first_year_fit.md) | Conditional log-linear first-year atmospheric carbon-steel loss model with temperature, relative humidity, chloride and sulfur-dioxide covariates. |
| [`corrosion.atmospheric_first_year_prediction`](modules/api/corrosion.atmospheric_first_year_prediction.md) | Uses only a reviewed AtmosphericFirstYearModel over one first-year atmospheric carbon-steel exposure and explicit environmental covariates. |
| [`corrosion.charge_to_loss`](modules/api/corrosion.charge_to_loss.md) | Declared alloy dissolution equivalent and current efficiency; cathodic current is not included in anodic charge. |
| [`corrosion.chronoamperometry_window_summary`](modules/api/corrosion.chronoamperometry_window_summary.md) | Time and current units, strict sample order, current sign and source trace digest are explicitly reviewed. |
| [`corrosion.coupled_wall_metal_loss`](modules/api/corrosion.coupled_wall_metal_loss.md) | Signed integrated lateral-wall species flux is converted with reviewed metal stoichiometry, physical reference area, reactive wall area, molar mass and density; no local thinning map or acceptance is inferred. |
| [`corrosion.coupon_loss`](modules/api/corrosion.coupon_loss.md) | Uniform average loss over the declared exposed area; cleaning loss is corrected upstream. |
| [`corrosion.coupon_loss_with_uncertainty`](modules/api/corrosion.coupon_loss_with_uncertainty.md) | Caller supplies corrected mass loss, geometry, material density, exposure duration and joint input covariance. |
| [`corrosion.crevice_hydraulic_stage_rhs`](modules/api/corrosion.crevice_hydraulic_stage_rhs.md) | The API evaluates one instantaneous series-slit momentum RHS. |
| [`corrosion.crevice_moving_volume_hydraulic_history`](modules/api/corrosion.crevice_moving_volume_hydraulic_history.md) | Aperture varies linearly within each caller interval, so liquid volume rate is interval constant. |
| [`corrosion.crevice_solid_volume_rate`](modules/api/corrosion.crevice_solid_volume_rate.md) | Positive phase molar rate denotes precipitation and negative rate denotes dissolution. |
| [`corrosion.crevice_wall_shear_exposure`](modules/api/corrosion.crevice_wall_shear_exposure.md) | Derive wide-planar-slit wall shear per cell from a digest-pinned exact interval flow history; analytically integrate absolute shear exposure while honoring reported internal flow reversal. |
| [`corrosion.explicit_co2_campaign`](modules/api/corrosion.explicit_co2_campaign.md) | Explicit caller-calibrated carbonate boundary, reaction/ionic transport, surface kinetics and reviewed metal-dissolution mapping in fixed geometry. |
| [`corrosion.faraday`](modules/api/corrosion.faraday.md) | Declared dissolution valence and current efficiency; no automatic pit geometry inference. |
| [`corrosion.galvanic_linear`](modules/api/corrosion.galvanic_linear.md) | Same potential reference, linear electrode polarization and an explicit validity bound; no mass-transport limitation. |
| [`corrosion.gumbel_area_maximum`](modules/api/corrosion.gumbel_area_maximum.md) | Equal-area complete independent block maxima from one declared surface population and exposure; caller-selected Gumbel or generalized extreme-value maximum approximation with explicit diagnostics. |
| [`corrosion.material_rate_contrast`](modules/api/corrosion.material_rate_contrast.md) | Input rates and condition groups are supplied by the caller; matched methodology and exposure conditions require source review. |
| [`corrosion.mixed_potential`](modules/api/corrosion.mixed_potential.md) | Reviewed compatible signed net polarization curves share one reference, electrolyte and temperature; negligible ohmic drop and quasi-steady response are required. |
| [`corrosion.model_output_rate_wall_loss_scenario`](modules/api/corrosion.model_output_rate_wall_loss_scenario.md) | Accepts portable simulated or caller-assumed scenario rows with matching source evidence, digest and common source group. |
| [`corrosion.piecewise_linear_rate_thickness_history`](modules/api/corrosion.piecewise_linear_rate_thickness_history.md) | Each rate knot is caller supplied with Evidence and a canonical record digest; the rate path is piecewise linear only between adjacent knots. |
| [`corrosion.planar_slit_aperture_history`](modules/api/corrosion.planar_slit_aperture_history.md) | Sequential geometry remapping from a caller-pinned cell-average signed wall-recession history within declared aperture support; support failure preserves an out-of-scope prefix and failed interval, and subsequent transport is a separate calculation. |
| [`corrosion.planar_slit_geometry`](modules/api/corrosion.planar_slit_geometry.md) | Explicit constant-aperture planar slit and selected reactive broad faces; no kinetics or advection inferred. |
| [`corrosion.planar_slit_hydraulic_flow`](modules/api/corrosion.planar_slit_hydraulic_flow.md) | Steady incompressible Newtonian laminar flow in caller-declared variable-gap planar-slit cells; optional aperture state is digest-bound, and unsupported Reynolds/aspect ratios fail closed. |
| [`corrosion.planar_slit_hydraulic_history`](modules/api/corrosion.planar_slit_hydraulic_history.md) | Digest-bound pressure samples are paired to every computed aperture-history knot; each knot is solved independently and the result is operator-split, not transiently or fully coupled. |
| [`corrosion.planar_slit_transient_hydraulic_history`](modules/api/corrosion.planar_slit_transient_hydraulic_history.md) | Exact interval propagation for the caller-reviewed reduced balance I dQ/dt + R Q = pressure_drop with piecewise-constant pressure and aperture. |
| [`corrosion.power_law`](modules/api/corrosion.power_law.md) | Empirical coefficients apply only to their calibration domain and chosen reference time. |
| [`corrosion.rate_joint_scenario`](modules/api/corrosion.rate_joint_scenario.md) | Each rate and weight is a caller-supplied complete scenario; one-per-specimen sample lineage is preserved separately. |
| [`corrosion.rate_quantile_forecast`](modules/api/corrosion.rate_quantile_forecast.md) | Uses exactly one selected empirical quantile from one-per-specimen caller rate summaries after explicit material, transfer and fixed linear-loss applicability review. |
| [`corrosion.rate_sample_summary`](modules/api/corrosion.rate_sample_summary.md) | One caller-reviewed rate summary per unique physical specimen, all from one material, condition, method and source group. |
| [`corrosion.scale_diffusion_metal_loss_bound`](modules/api/corrosion.scale_diffusion_metal_loss_bound.md) | A single computed layered-scale flux limit caps a caller-declared complete set of branches that produce the same transported species. |
| [`corrosion.simulation_rate_wall_loss_scenario`](modules/api/corrosion.simulation_rate_wall_loss_scenario.md) | Uses attributed simulated-model-output rows as scenario inputs while keeping them distinct from physical specimen observations. |
| [`corrosion.stern_geary`](modules/api/corrosion.stern_geary.md) | Small-signal polarization resistance is corrected for solution resistance and normalized by exposed area. |
| [`corrosion.thickness_trend`](modules/api/corrosion.thickness_trend.md) | Same measurement location and unchanged repair/operating regime; residuals are not POD. |
| [`corrosion.ti12mo5zr_aesec_signed_equivalent_penetration`](modules/api/corrosion.ti12mo5zr_aesec_signed_equivalent_penetration.md) | Caller-approved Ti-12Mo-5Zr density is applicable to the analyzed material. |
| [`corrosion.ti12mo5zr_eis_complex_impedance`](modules/api/corrosion.ti12mo5zr_eis_complex_impedance.md) | Convert one exact allowlisted Ti-12Mo-5Zr EIS spectrum from provider impedance magnitude and degrees to complex components under a caller-evidenced phase-sign convention. |
| [`corrosion.ti12mo5zr_ocp_signed_window_summary`](modules/api/corrosion.ti12mo5zr_ocp_signed_window_summary.md) | OCP rows are complete and ordered within the exact pinned source member. |
| [`corrosion.ti12mo5zr_uniform_equivalent_remaining_thickness`](modules/api/corrosion.ti12mo5zr_uniform_equivalent_remaining_thickness.md) | The embedded source assessment, its registry input digest, complete result digest, and nested mass-balance digest are caller-pinned and independently verified. |
| [`corrosion.uniform_forecast`](modules/api/corrosion.uniform_forecast.md) | Constant nonnegative growth; required thickness supplied by a separately qualified assessment. |

## creep: 크리프 속도·파단·누적손상

| API | 목적 |
|---|---|
| [`creep.accelerated_lognormal_rupture_fit`](modules/api/creep.accelerated_lognormal_rupture_fit.md) | Log rupture time is linear in log(reference stress / stress) and reciprocal-temperature difference. |
| [`creep.conditional_life`](modules/api/creep.conditional_life.md) | Condition-bounded lognormal population under unchanged conditions from a fresh-material age origin. |
| [`creep.declared_log_slope_rupture_factor`](modules/api/creep.declared_log_slope_rupture_factor.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`creep.larson_miller`](modules/api/creep.larson_miller.md) | Base-10 logarithm uses hours and temperature uses Kelvin; constant is not supplied by the library. |
| [`creep.lognormal_life_fit`](modules/api/creep.lognormal_life_fit.md) | Independent constant-condition specimens with explicit right-censoring and one common rupture mechanism. |
| [`creep.norton`](modules/api/creep.norton.md) | Isothermal, constant-load empirical steady-creep power law with a dimensionless stress ratio. |
| [`creep.secondary_history`](modules/api/creep.secondary_history.md) | Ordered caller-calibrated secondary-creep history with separately reviewed rupture-time fractions inside explicit condition support. |
| [`creep.time_fraction`](modules/api/creep.time_fraction.md) | Linear life fractions with supplied rupture lives; creep-fatigue interaction excluded. |
| [`creep.zener_hollomon_parameter`](modules/api/creep.zener_hollomon_parameter.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |

## data: 허용된 외부 자료 구조 확인·읽기

| API | 목적 |
|---|---|
| [`data.bam_cmsx6_creep_lis_typed_rows`](modules/api/data.bam_cmsx6_creep_lis_typed_rows.md) | Only one catalog-pinned local LIS asset is accepted; raw records remain local-only. |
| [`data.coqtel_typed_electrochemistry_rows`](modules/api/data.coqtel_typed_electrochemistry_rows.md) | Only the two checksum-pinned COQTEL HDF5 assets are accepted through the existing source reader. |
| [`data.figshare_corrosion_alloy_metrics_typed_rows`](modules/api/data.figshare_corrosion_alloy_metrics_typed_rows.md) | Only the pinned CC BY compilation workbook is accepted; publisher MD5 and acquisition SHA-256 are checked before reusing the existing parser. |
| [`data.mendeley_ahss1300_hydrogen_permeation_workbook_audit`](modules/api/data.mendeley_ahss1300_hydrogen_permeation_workbook_audit.md) | Only the exact provider-pinned Mendeley workbook is accepted by filename, size, MD5 and SHA-256. |
| [`data.mendeley_aisi1018_aerobic_corrosion_file_inventory`](modules/api/data.mendeley_aisi1018_aerobic_corrosion_file_inventory.md) | Only the exact 22 Mendeley Data v1 files, byte sizes and provider SHA-256 digests are accepted. |
| [`data.mendeley_atmospheric_corrosion_typed_rows`](modules/api/data.mendeley_atmospheric_corrosion_typed_rows.md) | Only the catalogued archive name, byte count, Mendeley archive SHA-256 and MD5 are accepted. |
| [`data.mendeley_az31b_corrosion_fatigue_typed_rows`](modules/api/data.mendeley_az31b_corrosion_fatigue_typed_rows.md) | Only eight exact Mendeley Data version-1 XLSX assets are accepted by file name, byte count and SHA-256. |
| [`data.mendeley_crack_arrest_typed_rows`](modules/api/data.mendeley_crack_arrest_typed_rows.md) | Only the exact catalogued archive filename, byte count and SHA-256 are accepted before reusing the existing bounded CSV reader. |
| [`data.mendeley_explosive_weld_multilayer_fatigue_mapped_rows`](modules/api/data.mendeley_explosive_weld_multilayer_fatigue_mapped_rows.md) | The caller maps each worksheet, header value, inclusive row span, field meaning, unit token and field role. |
| [`data.mendeley_explosive_weld_multilayer_fatigue_typed_rows`](modules/api/data.mendeley_explosive_weld_multilayer_fatigue_typed_rows.md) | Only the exact Mendeley version-1 workbook is accepted by filename, byte count and SHA-256. |
| [`data.mendeley_fracture_toughness_temperature_typed_rows`](modules/api/data.mendeley_fracture_toughness_temperature_typed_rows.md) | Only the exact catalogued Mendeley archive name, byte count, SHA-256 and workbook member digest are accepted. |
| [`data.mendeley_guided_wave_typed_sample_rows`](modules/api/data.mendeley_guided_wave_typed_sample_rows.md) | Only the catalogued outer archive SHA-256 and byte count are accepted; the existing bounded nested-archive parser is reused. |
| [`data.mendeley_internal_corrosion_doobn_typed_rows`](modules/api/data.mendeley_internal_corrosion_doobn_typed_rows.md) | Audit the exact Mendeley Data version 3 workbook by official file size and SHA-256. |
| [`data.mendeley_mdea_co2_eis_typed_rows`](modules/api/data.mendeley_mdea_co2_eis_typed_rows.md) | Read only pinned Mendeley Data version 3 assets after manifest and provider SHA-256 checks. |
| [`data.mendeley_mg_fsp_scc_typed_rows`](modules/api/data.mendeley_mg_fsp_scc_typed_rows.md) | Only the four exact Mendeley Data version-1 XLSX assets are accepted by name, size and SHA-256. |
| [`data.mendeley_thermal_rod_typed_rows`](modules/api/data.mendeley_thermal_rod_typed_rows.md) | Only the catalogued archive name, byte count and SHA-256 are accepted; rows come from the existing raw-run parser. |
| [`data.mendeley_x80_srb_scc_typed_rows`](modules/api/data.mendeley_x80_srb_scc_typed_rows.md) | Audit only three exact Mendeley version-1 XLS assets using official byte counts and SHA-256 values. |
| [`data.plos_ct110_wet_co2_typed_rows`](modules/api/data.plos_ct110_wet_co2_typed_rows.md) | The exact publisher workbook size, MD5 and local SHA-256 must match before parsing. |
| [`data.uci_metropt3_process_history`](modules/api/data.uci_metropt3_process_history.md) | Only the exact UCI archive/member digest and local path are accepted. |
| [`data.zenodo_316l_polarization_typed_rows`](modules/api/data.zenodo_316l_polarization_typed_rows.md) | Only the catalogued archive filename, byte count, provider MD5 and SHA-256 are accepted. |
| [`data.zenodo_cathodic_protection_sample_rows`](modules/api/data.zenodo_cathodic_protection_sample_rows.md) | Only five locally held CSV files with exact SHA-256 pins and the reviewed DPlot layout are accepted. |
| [`data.zenodo_ceit_uniform_corrosion_field_typed_rows`](modules/api/data.zenodo_ceit_uniform_corrosion_field_typed_rows.md) | Only the catalogued CEIT JSON filename, byte count, MD5 and acquisition SHA-256 are accepted before invoking the existing parser. |
| [`data.zenodo_deis_archive_structure`](modules/api/data.zenodo_deis_archive_structure.md) | Read one pinned CC0 Zenodo archive from a caller-supplied local path; network access is not performed. |
| [`data.zenodo_galvanized_polarization_typed_rows`](modules/api/data.zenodo_galvanized_polarization_typed_rows.md) | Only the three catalogued polarization workbook assets with the declared file size and depositor MD5 are accepted. |
| [`data.zenodo_mg_deis_typed_matrix_rows`](modules/api/data.zenodo_mg_deis_typed_matrix_rows.md) | Only the catalogued CC0 archive filename, byte count, publisher MD5 and SHA-256 are accepted; the existing bounded matrix parser is reused. |
| [`data.zenodo_pressure_decay_leak_sample_rows`](modules/api/data.zenodo_pressure_decay_leak_sample_rows.md) | The exact CC BY 4.0 workbook digest, provider layout and caller attribution are required. |
| [`data.zenodo_ti12mo5hf_archive_audit`](modules/api/data.zenodo_ti12mo5hf_archive_audit.md) | Caller supplies a local file and explicitly authorizes computational use and local-only processing. |
| [`data.zenodo_zr_nb_sn_electrochemical_typed_rows`](modules/api/data.zenodo_zr_nb_sn_electrochemical_typed_rows.md) | Only the eight pinned Zenodo v2 XLSX files are accepted by filename, byte length, and SHA-256. |

## degradation: 열화·침식·산화·마모·환경 영향

| API | 목적 |
|---|---|
| [`degradation.acid_dissolution_history`](modules/api/degradation.acid_dissolution_history.md) | Dissolution rates are externally calibrated, explicitly supplied and constant within each declared interval. |
| [`degradation.alkaline_scc_applicability`](modules/api/degradation.alkaline_scc_applicability.md) | Material, heat treatment, alkaline chemistry, temperature, electrochemical descriptor, stresses and duration are checked only against caller-qualified evidence envelopes. |
| [`degradation.alkaline_scc_user_screening`](modules/api/degradation.alkaline_scc_user_screening.md) | Facts and rules are caller-authored and retain evidence record, source group and digest lineage. |
| [`degradation.ammonia_scc_applicability`](modules/api/degradation.ammonia_scc_applicability.md) | Material, metallurgy and heat-treatment identities match the qualification evidence exactly. |
| [`degradation.ammonia_scc_user_screening`](modules/api/degradation.ammonia_scc_user_screening.md) | Facts and rules are caller-authored and retain evidence record, source group and digest lineage. |
| [`degradation.archard_wear`](modules/api/degradation.archard_wear.md) | User-calibrated dimensionless wear coefficient, SI hardness and uniformly distributed loss. |
| [`degradation.archard_wear_coefficient_calibration`](modules/api/degradation.archard_wear_coefficient_calibration.md) | Calibration is restricted to one material/counterface/contact/lubrication regime with SI force, distance, hardness and wear volume. |
| [`degradation.atmospheric_multi_year_loss_history`](modules/api/degradation.atmospheric_multi_year_loss_history.md) | First-year loss and time exponent are externally supplied, reviewed quantities in exact caller units. |
| [`degradation.atmospheric_scenario_ensemble`](modules/api/degradation.atmospheric_scenario_ensemble.md) | Each scenario is independently passed to the registered first-year atmospheric prediction model. |
| [`degradation.calibrated_condition_loss_history`](modules/api/degradation.calibrated_condition_loss_history.md) | Ordered piecewise-constant conditions mapped through one reviewed calibrated response and integrated without dropping unsupported intervals. |
| [`degradation.calibrated_condition_loss_rate`](modules/api/degradation.calibrated_condition_loss_rate.md) | Explicit authorized material/mechanism-specific log-rate coefficients, native feature units and bounded support; no default biological or erosion-rate law. |
| [`degradation.calibrated_damage_history`](modules/api/degradation.calibrated_damage_history.md) | Explicit calibrated microbial or cavitation rate history; no indicator-to-rate inference. |
| [`degradation.carburization_applicability`](modules/api/degradation.carburization_applicability.md) | Material and alloy-condition identities match the caller-owned qualification evidence exactly. |
| [`degradation.cavitation_history`](modules/api/degradation.cavitation_history.md) | Aligned reviewed absolute local-pressure and equilibrium liquid-property samples with piecewise-linear crossings; duration and pressure deficit are not damage. |
| [`degradation.cavitation_margin`](modules/api/degradation.cavitation_margin.md) | Absolute local static pressure, equilibrium vapor pressure, liquid density and a caller-defined characteristic velocity; thermodynamic screening is separate from damage. |
| [`degradation.chloride_scc_applicability`](modules/api/degradation.chloride_scc_applicability.md) | Material condition and metallurgy identities must match the caller-owned test envelope exactly. |
| [`degradation.chloride_scc_user_screening`](modules/api/degradation.chloride_scc_user_screening.md) | Facts and rules are caller-authored and retain evidence record, source group and digest lineage. |
| [`degradation.crevice_aperture_displacement_flow`](modules/api/degradation.crevice_aperture_displacement_flow.md) | A pinned complete aperture history supplies fixed cell widths, transverse width and exact cell volumes. |
| [`degradation.crevice_lumped_exchange_reaction_history`](modules/api/degradation.crevice_lumped_exchange_reaction_history.md) | Solve a caller-declared fixed-volume, single-species well-mixed exchange and first-order sink balance with exact interval propagation. |
| [`degradation.crevice_nernst_potential_history`](modules/api/degradation.crevice_nernst_potential_history.md) | Apply the Nernst equation at supplied time knots using caller-provided dimensionless activities and standard-potential history. |
| [`degradation.crevice_species_inventory_history`](modules/api/degradation.crevice_species_inventory_history.md) | Geometry, volumes, species definitions, initial inventories and interval source rates are reviewed caller inputs. |
| [`degradation.crevice_wall_sink_arrhenius_calibration`](modules/api/degradation.crevice_wall_sink_arrhenius_calibration.md) | The supplied observations already represent an effective first-order wall-transfer velocity in m/s; this fit does not derive velocity from penetration, current or mass loss. |
| [`degradation.crevice_wall_sink_rate_history`](modules/api/degradation.crevice_wall_sink_rate_history.md) | Reference rate and activation energy are caller-supplied reviewed wall-law parameters; they are not fitted from the supplied temperature history. |
| [`degradation.damage_mechanism_screening`](modules/api/degradation.damage_mechanism_screening.md) | Explicit physical scope, caller facts/profiles and conservative missingness policy. |
| [`degradation.declared_temperature_rate_factor`](modules/api/degradation.declared_temperature_rate_factor.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`degradation.device_pressure_drop_cavitation_index`](modules/api/degradation.device_pressure_drop_cavitation_index.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`degradation.erosion_corrosion_loss`](modules/api/degradation.erosion_corrosion_loss.md) | Net thickness-loss rates are externally calibrated, reviewed and constant within each interval. |
| [`degradation.erosion_corrosion_power_law_calibration`](modules/api/degradation.erosion_corrosion_power_law_calibration.md) | Log measured loss rate is linear in log velocity and log particle concentration in one reviewed regime. |
| [`degradation.erosion_corrosion_synergy_decomposition`](modules/api/degradation.erosion_corrosion_synergy_decomposition.md) | Pure erosion, pure corrosion and combined loss are caller-supplied matched observations; residual synergy is their signed arithmetic difference. |
| [`degradation.galvanic_coupling`](modules/api/degradation.galvanic_coupling.md) | Caller-reviewed, condition-compatible signed polarization curves are solved only on their common measured support. |
| [`degradation.galvanic_resistive_coupling`](modules/api/degradation.galvanic_resistive_coupling.md) | Exactly two reviewed signed net polarization curves share one environment and reference electrode; every root is bounded by both supplied curve supports. |
| [`degradation.high_temperature_hydrogen_applicability`](modules/api/degradation.high_temperature_hydrogen_applicability.md) | Hydrogen pressure is an absolute partial pressure in pascals; gauge or total pressure is not silently substituted. |
| [`degradation.hydrogen_cracking_provider_evidence`](modules/api/degradation.hydrogen_cracking_provider_evidence.md) | Pressure or fugacity basis and unit are exact caller-reviewed tokens and are never interchanged. |
| [`degradation.hydrogen_fatigue_provider_evidence`](modules/api/degradation.hydrogen_fatigue_provider_evidence.md) | Material condition, hydrogen species, quantity basis and units match exactly. |
| [`degradation.liquid_metal_embrittlement_applicability`](modules/api/degradation.liquid_metal_embrittlement_applicability.md) | Structural material, condition, liquid-metal species, composition and impurity identities match qualification evidence exactly. |
| [`degradation.metallurgical_aging_exposure`](modules/api/degradation.metallurgical_aging_exposure.md) | Each interval uses a caller-calibrated equivalent-time rate multiplier at a reviewed temperature. |
| [`degradation.microbial_campaign_summary`](modules/api/degradation.microbial_campaign_summary.md) | Campaign, site, clock, sample validity, assay identity, detection limits, water context and biofilm/deposit observations remain separate evidence fields. |
| [`degradation.nitriding_applicability`](modules/api/degradation.nitriding_applicability.md) | Material, condition, nitrogen species and driving-force basis, temperature, absolute pressure, gas environment and duration are compared only with caller-qualified evidence envelopes. |
| [`degradation.nonisothermal_parabolic_oxidation`](modules/api/degradation.nonisothermal_parabolic_oxidation.md) | A retained protective scale follows a caller-qualified parabolic law over the full history. |
| [`degradation.parabolic_oxidation`](modules/api/degradation.parabolic_oxidation.md) | Retained protective scale in one declared isothermal parabolic-growth regime; spallation excluded. |
| [`degradation.scc_crack_velocity_history`](modules/api/degradation.scc_crack_velocity_history.md) | One caller-owned material/metallurgy/environment/loading state and thresholded K_I-to-da/dt law apply over the finite history. |
| [`degradation.selective_leaching_applicability`](modules/api/degradation.selective_leaching_applicability.md) | Alloy, composition, phase, environment, temperature, pH, electrochemical descriptor and exposure duration are compared only with caller-qualified support. |
| [`degradation.sour_environment_applicability`](modules/api/degradation.sour_environment_applicability.md) | Material, units, H2S partial-pressure definition and stress-state descriptors use exact matching. |
| [`degradation.sulfidation_exposure_applicability`](modules/api/degradation.sulfidation_exposure_applicability.md) | Material condition, sulfur definition, units, flow and deposit descriptors require exact identity matching. |
| [`degradation.under_deposit_calibrated_loss`](modules/api/degradation.under_deposit_calibrated_loss.md) | Each interval has a reviewed deposit state and an external calibrated local-loss rate within one provider support. |
| [`degradation.under_deposit_local_environment_review`](modules/api/degradation.under_deposit_local_environment_review.md) | Local-environment observations and caller criteria are reviewed and identity-linked. |
| [`degradation.under_insulation`](modules/api/degradation.under_insulation.md) | CUI scope, ordered access/inspection/repair events, explicit coverage and observations remain caller evidence. |
| [`degradation.under_insulation_exposure_history`](modules/api/degradation.under_insulation_exposure_history.md) | Surface temperature, wetness and insulation condition are piecewise-constant reviewed observations over explicit intervals. |
| [`degradation.wet_co2_cylindrical_scale_geometry_history`](modules/api/degradation.wet_co2_cylindrical_scale_geometry_history.md) | Caller-supplied lineal phase inventories and molar volumes map to an annular cylindrical scale volume. |
| [`degradation.wet_co2_gas_side_mass_transfer`](modules/api/degradation.wet_co2_gas_side_mass_transfer.md) | Caller supplies one turbulent gas state with mean velocity, wall shear, density, viscosity and CO2 diffusivity. |
| [`degradation.wet_co2_liquid_side_mass_transfer`](modules/api/degradation.wet_co2_liquid_side_mass_transfer.md) | The caller supplies the liquid-phase mean velocity and wall shear stress for one exact region/time from a separately identified hydrodynamics provider. |
| [`degradation.wet_co2_simulation_matched_contrast`](modules/api/degradation.wet_co2_simulation_matched_contrast.md) | Rows are provider-generated NORSOK M-506 simulation output with matched nonvaried inputs. |
| [`degradation.wet_co2_two_film_transfer`](modules/api/degradation.wet_co2_two_film_transfer.md) | Caller-supplied fugacity, Henry coefficient and gas/liquid film coefficients share one reviewed condition and area basis. |
| [`degradation.wet_co2_two_film_transfer_history`](modules/api/degradation.wet_co2_two_film_transfer_history.md) | Every point is a caller-declared steady gas/liquid state and uses the existing two-film point evaluator independently. |

## design: 설계 입력·사용자 기준 적용

| API | 목적 |
|---|---|
| [`design.piping_class_assessment`](modules/api/design.piping_class_assessment.md) | Caller-reviewed common gauge-pressure basis, piecewise-linear supported pressure-temperature envelope and exact component/material labels. |
| [`design.relief_pressure_envelope`](modules/api/design.relief_pressure_envelope.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |

## electrochemistry: 전위·편극·전극반응

| API | 목적 |
|---|---|
| [`electrochemistry.crevice_mixed_potential_history`](modules/api/electrochemistry.crevice_mixed_potential_history.md) | At every aligned knot, evaluate multiple caller-provided Nernst half-cell profiles and caller-calibrated Butler-Volmer reactions, area-normalize the currents, and solve for a common zero-net-current potential within all reaction overpotential supports. |
| [`electrochemistry.mendeley_mdea_eis_complex_channel_conversion`](modules/api/electrochemistry.mendeley_mdea_eis_complex_channel_conversion.md) | Caller explicitly maps source headers and the imaginary-axis sign convention. |
| [`electrochemistry.nernst_driven_butler_volmer_history`](modules/api/electrochemistry.nernst_driven_butler_volmer_history.md) | Evaluate one caller-calibrated Butler-Volmer reaction at exact common time knots using an upstream digest-bound Nernst equilibrium-potential history. |
| [`electrochemistry.restricted_transport_campaign`](modules/api/electrochemistry.restricted_transport_campaign.md) | Caller-calibrated homogeneous ionic reactions and Butler-Volmer tip/wall boundaries on a fixed one-dimensional transport grid; an optional digest-matched activity-coefficient correction multiplies species concentrations in homogeneous rates only when separately reviewed. |

## fabrication: 가공·볼트·가스켓·제작 품질

| API | 목적 |
|---|---|
| [`fabrication.bend_strain`](modules/api/fabrication.bend_strain.md) | Kinematic bending estimate; ovalization, thinning and plastic-neutral-axis movement excluded. |
| [`fabrication.bolt_preload`](modules/api/fabrication.bolt_preload.md) | Approximate torque-factor relation; friction scatter and joint stiffness require separate treatment. |
| [`fabrication.bolt_reference_torque_scaling`](modules/api/fabrication.bolt_reference_torque_scaling.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`fabrication.cathodic_protection_field_survey`](modules/api/fabrication.cathodic_protection_field_survey.md) | Field potential conventions, reference-electrode calibration and IR-drop status remain explicit. |
| [`fabrication.chemical_cleaning_bath_component_inventory`](modules/api/fabrication.chemical_cleaning_bath_component_inventory.md) | Component masses are caller-declared and expressed on one consistent component identity basis. |
| [`fabrication.chemical_cleaning_envelope`](modules/api/fabrication.chemical_cleaning_envelope.md) | Each recorded step has uniform declared solution properties and maps to one caller-owned material compatibility envelope. |
| [`fabrication.chemical_cleaning_production_campaign_evidence`](modules/api/fabrication.chemical_cleaning_production_campaign_evidence.md) | Caller criteria only; no kinetics or compatibility inference. |
| [`fabrication.coating_damage_area_inventory`](modules/api/fabrication.coating_damage_area_inventory.md) | Explicit inspected extent and reviewed nonoverlapping damage patch measurements; no uninspected-area inference. |
| [`fabrication.coating_qualification_assessment`](modules/api/fabrication.coating_qualification_assessment.md) | Specimens and source groups are assigned once to calibration or holdout and cannot cross partitions. |
| [`fabrication.cryogenic_valve_evidence`](modules/api/fabrication.cryogenic_valve_evidence.md) | Valve, body, seat, stem, seal, medium and pressure-basis identities match caller qualification evidence exactly. |
| [`fabrication.deposition_removal_history`](modules/api/fabrication.deposition_removal_history.md) | Reviewed uniform local layer thickness along one common normal; explicit deposition and top-down removal events. |
| [`fabrication.elastic_joint_load`](modules/api/fabrication.elastic_joint_load.md) | Reviewed linear two-spring closed-contact load partition with caller stiffness and differential thermal displacement. |
| [`fabrication.equipment_mass_properties`](modules/api/fabrication.equipment_mass_properties.md) | Complete caller-declared installed mass inventory in one explicit coordinate frame. |
| [`fabrication.equipment_two_support_lift`](modules/api/fabrication.equipment_two_support_lift.md) | Caller-reviewed body XY plane, explicit rotation about Z, rigid body and two parallel vertical support reactions. |
| [`fabrication.fire_protection_boundary_history`](modules/api/fabrication.fire_protection_boundary_history.md) | The caller supplies the incident flux, protection states, transfer fractions and their reviewed support. |
| [`fabrication.flange_contact_compliance_reduction`](modules/api/fabrication.flange_contact_compliance_reduction.md) | Condense an explicitly supplied constrained incremental translational stiffness operator to selected signed gasket-contact DOFs. |
| [`fabrication.flange_contact_compliance_reduction_history`](modules/api/fabrication.flange_contact_compliance_reduction_history.md) | Reduce one caller-supplied constrained linear incremental stiffness matrix per aligned geometry/time knot using a fixed node/DOF mapping. |
| [`fabrication.flange_contact_field`](modules/api/fabrication.flange_contact_field.md) | Caller-supplied symmetric positive-semidefinite relative flange compliance and per-node linear gasket springs define the spatial contact response. |
| [`fabrication.flange_nonlinear_contact_field`](modules/api/fabrication.flange_nonlinear_contact_field.md) | A caller-supplied symmetric positive-semidefinite flange operator is coupled to per-node reversible monotone piecewise-linear gasket force-compression curves. |
| [`fabrication.flange_nonlinear_viscoelastic_contact_history`](modules/api/fabrication.flange_nonlinear_viscoelastic_contact_history.md) | Caller nonlinear Maxwell branch backbones and equilibrium gasket backbone are coupled to caller-supplied positive-semidefinite flange compliance. |
| [`fabrication.flange_viscoelastic_contact_history`](modules/api/fabrication.flange_viscoelastic_contact_history.md) | Caller-supplied linear generalized-Maxwell gasket branches evolve exactly over declared piecewise-linear compression segments and are coupled to a caller-supplied symmetric positive-semidefinite flange compliance operator, optionally supplied as a digest-bound operator at every declared time knot. |
| [`fabrication.forming_area_reduction`](modules/api/fabrication.forming_area_reduction.md) | Matched material sections and SI areas are explicitly reviewed; no material constitutive law is inferred. |
| [`fabrication.forming_geometry_history`](modules/api/fabrication.forming_geometry_history.md) | Caller-reviewed circular-arc bend geometry with a mid-thickness neutral axis. |
| [`fabrication.forming_process_sequence`](modules/api/fabrication.forming_process_sequence.md) | Explicit caller material-specific process plan, ordered operation records and shared clock. |
| [`fabrication.forming_qualification`](modules/api/fabrication.forming_qualification.md) | Material, condition, product form, forming mode and method match the envelope exactly. |
| [`fabrication.friction_resolved_bolt_torque`](modules/api/fabrication.friction_resolved_bolt_torque.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`fabrication.gasket_bolt_cyclic_damage`](modules/api/fabrication.gasket_bolt_cyclic_damage.md) | Nominal tensile stress histories are read from one digest-pinned computed gasket multi-bolt equilibrium result. |
| [`fabrication.gasket_bolt_nominal_strength_screen`](modules/api/fabrication.gasket_bolt_nominal_strength_screen.md) | Consume a computed caller multi-bolt/sector equilibrium and compare its nominal axial bolt stresses with per-bolt caller strength curves at exact common knots. |
| [`fabrication.gasket_bolt_preload_sequence_redistribution`](modules/api/fabrication.gasket_bolt_preload_sequence_redistribution.md) | Each tightening operation adds its applied target increment multiplied by the corresponding caller interaction-matrix column to the complete bolt preload vector. |
| [`fabrication.gasket_calibrated_leakage_history`](modules/api/fabrication.gasket_calibrated_leakage_history.md) | Caller-calibrated pressure-dependent leakage flux is evaluated at each contact node and integrated over its declared area for an aligned joint history. |
| [`fabrication.gasket_calibrated_leakage_rate_envelope`](modules/api/fabrication.gasket_calibrated_leakage_rate_envelope.md) | Bound a caller-calibrated bilinear leakage flux at each node over independent declared contact-pressure and differential-pressure intervals. |
| [`fabrication.gasket_circumferential_contact_continuity`](modules/api/fabrication.gasket_circumferential_contact_continuity.md) | A computed gasket contact-pressure field is classified against a caller-evidenced minimum pressure and caller-evidenced periodic ring geometry. |
| [`fabrication.gasket_compression_curve_monotone_fit`](modules/api/fabrication.gasket_compression_curve_monotone_fit.md) | Observed force values are fit by weighted least-squares isotonic regression at sorted measured compression knots. |
| [`fabrication.gasket_compression_hysteresis_energy`](modules/api/fabrication.gasket_compression_hysteresis_energy.md) | Every cycle is a caller-segmented ordered compression force-displacement loop with a reviewed repeated count and closed endpoints. |
| [`fabrication.gasket_contact_distribution_statistics`](modules/api/fabrication.gasket_contact_distribution_statistics.md) | Summarize a digest-pinned computed flange gasket pressure field using its own declared finite nodal contact areas. |
| [`fabrication.gasket_contact_pressure_screen`](modules/api/fabrication.gasket_contact_pressure_screen.md) | Compare a digest-pinned upstream gasket contact-pressure field with a caller-declared screening window at an exact declared output knot. |
| [`fabrication.gasket_contact_pressure_window_events`](modules/api/fabrication.gasket_contact_pressure_window_events.md) | Audit exact computed gasket contact-pressure knots against a caller-declared node pressure window using reviewed piecewise-linear interpolation. |
| [`fabrication.gasket_contact_root_localization`](modules/api/fabrication.gasket_contact_root_localization.md) | A computed caller-supplied contact-transition bracket and digest-matched endpoint responses with strict opposite signs are required. |
| [`fabrication.gasket_contact_state_grid_sweep`](modules/api/fabrication.gasket_contact_state_grid_sweep.md) | Query a caller-declared finite time grid through an explicit external contact-state provider and preserve every provider response digest and Evidence. |
| [`fabrication.gasket_contact_subthreshold_exposure`](modules/api/fabrication.gasket_contact_subthreshold_exposure.md) | Integrate a caller-evidenced thresholded pressure exposure over a computed viscoelastic gasket contact history and its finite nodal area partition. |
| [`fabrication.gasket_contact_transition_brackets`](modules/api/fabrication.gasket_contact_transition_brackets.md) | Summarize contact-state changes visible between adjacent computed flange-history knots as time brackets. |
| [`fabrication.gasket_contact_transition_refinement`](modules/api/fabrication.gasket_contact_transition_refinement.md) | Refine one caller-selected contact-state bracket only with exact provider midpoint evaluations, matching provider identity/revision/configuration and Evidence-bound response digests. |
| [`fabrication.gasket_correlated_scenario_envelope`](modules/api/fabrication.gasket_correlated_scenario_envelope.md) | Evaluate leakage only over complete caller-supplied joint scenarios that preserve dependence among node pressure, common differential pressure, area and calibration-grid variation. |
| [`fabrication.gasket_evidence_bound_prony_history`](modules/api/fabrication.gasket_evidence_bound_prony_history.md) | The underlying caller-calibrated generalized-Maxwell strain update is reused unchanged; this adapter adds source/license/temperature support requirements. |
| [`fabrication.gasket_finite_scenario_dependence`](modules/api/fabrication.gasket_finite_scenario_dependence.md) | Caller-provided complete finite joint gasket scenarios and positive weights already summing to one. |
| [`fabrication.gasket_joint_evidence`](modules/api/fabrication.gasket_joint_evidence.md) | Flange, gasket, bolt lots, medium, pressure basis and operating state are caller reviewed. |
| [`fabrication.gasket_leakage_box_envelope`](modules/api/fabrication.gasket_leakage_box_envelope.md) | Returns deterministic extrema over caller-specified independent pressure, area and calibration-flux intervals using the piecewise-bilinear map without extrapolation. |
| [`fabrication.gasket_leakage_covariance_propagation`](modules/api/fabrication.gasket_leakage_covariance_propagation.md) | A caller-supplied symmetric positive-semidefinite covariance is propagated through the local piecewise-bilinear calibrated leakage map. |
| [`fabrication.gasket_leakage_fit_diagnostics`](modules/api/fabrication.gasket_leakage_fit_diagnostics.md) | Compute descriptive raw and residual-scale-normalized error summaries from a digest-pinned completed gasket leakage-map fit. |
| [`fabrication.gasket_leakage_map_fit`](modules/api/fabrication.gasket_leakage_map_fit.md) | Caller-reviewed nonnegative bilinear surface with supplied knot support and residual scales. |
| [`fabrication.gasket_leakage_weighted_scenario_moments`](modules/api/fabrication.gasket_leakage_weighted_scenario_moments.md) | Evaluate the calibrated leakage response within each complete correlated scenario, then compute descriptive finite-set moments using caller-supplied ordered weights. |
| [`fabrication.gasket_multi_bolt_sector_equilibrium`](modules/api/fabrication.gasket_multi_bolt_sector_equilibrium.md) | Each bolt is an independent caller-specified linear axial spring that carries tension only; each gasket sector carries compression only. |
| [`fabrication.gasket_prony_history`](modules/api/fabrication.gasket_prony_history.md) | Caller-authorized generalized Maxwell terms and separately reviewed explicit initial branch stresses are integrated over a reviewed piecewise-linear compression-strain history. |
| [`fabrication.gasket_prony_joint_history`](modules/api/fabrication.gasket_prony_joint_history.md) | Caller-authorized Prony gasket history is coupled to a linear bolt and quasi-static force equilibrium at each declared time knot. |
| [`fabrication.gasket_prony_relaxation_spectrum_fit`](modules/api/fabrication.gasket_prony_relaxation_spectrum_fit.md) | Fit a finite positive generalized-Maxwell relaxation spectrum from caller step-strain observations at one exact material condition and temperature. |
| [`fabrication.gasket_prony_temperature_shift_history`](modules/api/fabrication.gasket_prony_temperature_shift_history.md) | A caller-calibrated, thermorheologically simple time-temperature shift modifies the Prony relaxation clock while other material parameters remain at the reference condition. |
| [`fabrication.gasket_radial_open_path_screen`](modules/api/fabrication.gasket_radial_open_path_screen.md) | The supplied cell pressure map is interpreted on an annulus partitioned by radial and full-ring angular edges. |
| [`fabrication.gasket_relaxation_curve`](modules/api/fabrication.gasket_relaxation_curve.md) | Authorized caller retention observations are linearly interpolated only inside the exact declared time support; no universal gasket relaxation law or leakage/acceptance result is inferred. |
| [`fabrication.gasket_temperature_compression_curve_transfer`](modules/api/fabrication.gasket_temperature_compression_curve_transfer.md) | Only caller-supplied monotone loading curves at two temperatures are used, and they must share specimen, material condition, branch and strain knots. |
| [`fabrication.governing_thickness_recipe`](modules/api/fabrication.governing_thickness_recipe.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`fabrication.heat_exchanger_geometry_evidence`](modules/api/fabrication.heat_exchanger_geometry_evidence.md) | Exchanger, shell, bundle, coordinate frame, units, ordering and payload digests are caller reviewed. |
| [`fabrication.insulation_condensation_exposure`](modules/api/fabrication.insulation_condensation_exposure.md) | Piecewise-constant, non-overlapping surface and ambient dew-point observations on one reviewed clock. |
| [`fabrication.joint_efficiency_declaration`](modules/api/fabrication.joint_efficiency_declaration.md) | Joint, process, material group, examination method and physical scope are caller-reviewed exact identities. |
| [`fabrication.measured_pipe_ovality`](modules/api/fabrication.measured_pipe_ovality.md) | Caller selects nominal or measured-mean reference diameter; no tolerance or sampling rule is inferred. |
| [`fabrication.nonlinear_bolt_gasket_contact`](modules/api/fabrication.nonlinear_bolt_gasket_contact.md) | Single-degree-of-freedom quasi-static joint equilibrium using caller-authorized monotone nonlinear bolt force-extension and gasket force-compression curves, with no extrapolation. |
| [`fabrication.nonlinear_gasket_contact`](modules/api/fabrication.nonlinear_gasket_contact.md) | Elastic bolt and authorized reversible caller compression-force curve, with explicit contact loss and no extrapolation. |
| [`fabrication.nonlinear_gasket_prony_joint_history`](modules/api/fabrication.nonlinear_gasket_prony_joint_history.md) | Caller-authorized monotone nonlinear stress-strain backbones for equilibrium and generalized-Maxwell branches are coupled to a caller nonlinear bolt curve and knotwise force balance. |
| [`fabrication.pipe_bend_wall_allowance`](modules/api/fabrication.pipe_bend_wall_allowance.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`fabrication.pull_off_adhesion_calibration`](modules/api/fabrication.pull_off_adhesion_calibration.md) | Force-area stress requires explicit newtons and square metres and is kept separate from provider stress. |
| [`fabrication.regular_tube_layout`](modules/api/fabrication.regular_tube_layout.md) | Explicit regular square or triangular tube lattice geometry; no shell/baffle clearance or pressure-drop inference. |
| [`fabrication.storage_preservation`](modules/api/fabrication.storage_preservation.md) | Item, material, area, storage location, preservation method, material batch and event identities are exact caller inputs. |
| [`fabrication.storage_preservation_history`](modules/api/fabrication.storage_preservation_history.md) | Piecewise-constant environment observations remain separate from caller-declared temperature, humidity, preservation-state and inspection-spacing limits. |
| [`fabrication.surface_cleanliness_assessment`](modules/api/fabrication.surface_cleanliness_assessment.md) | Area coverage is summed only after the caller reviews areas as mutually exclusive. |
| [`fabrication.surface_cleanliness_production_campaign_evidence`](modules/api/fabrication.surface_cleanliness_production_campaign_evidence.md) | Caller criteria only; no standard comparator. |
| [`fabrication.surface_profile_deviation`](modules/api/fabrication.surface_profile_deviation.md) | Exact caller-reviewed point pairing in one SI coordinate frame and unit outward normals. |
| [`fabrication.thermal_spray_condition`](modules/api/fabrication.thermal_spray_condition.md) | System, process, feedstock lot, substrate condition and procedure identities are caller-reviewed. |
| [`fabrication.thermal_spray_cross_section_summary`](modules/api/fabrication.thermal_spray_cross_section_summary.md) | Caller-supplied thickness points and segmented pore areas share one calibrated field geometry. |
| [`fabrication.thermal_spray_porosity_uncertainty`](modules/api/fabrication.thermal_spray_porosity_uncertainty.md) | Caller-segmented pixel areas are converted with reviewed pixel-area calibration evidence. |
| [`fabrication.thermal_spray_thickness_uncertainty`](modules/api/fabrication.thermal_spray_thickness_uncertainty.md) | Repeated SI thickness measurements receive caller-provided additive calibration corrections. |
| [`fabrication.thickness_budget`](modules/api/fabrication.thickness_budget.md) | Caller-declared manufacturing, forming, future corrosion and structural requirements with a separate measured path. |
| [`fabrication.transport_erection`](modules/api/fabrication.transport_erection.md) | Ordered item, lift, transport, storage, support and erection evidence is caller supplied. |
| [`fabrication.transport_erection_history`](modules/api/fabrication.transport_erection_history.md) | Ordered handling, transport and erection activity intervals remain separate from metric observations, inspections and caller-owned limits. |
| [`fabrication.tube_bend_preform_thickness`](modules/api/fabrication.tube_bend_preform_thickness.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`fabrication.tube_bundle_integrity_evidence`](modules/api/fabrication.tube_bundle_integrity_evidence.md) | Exchanger, bundle, tube, row and physical location are exact caller-reviewed identities. |
| [`fabrication.tube_bundle_inventory`](modules/api/fabrication.tube_bundle_inventory.md) | Identified tube wall-loss and plugged-bore geometric inventory only; no tube capacity or leakage conclusion. |
| [`fabrication.tube_expansion_wall_reduction`](modules/api/fabrication.tube_expansion_wall_reduction.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`fabrication.unilateral_nonlinear_gasket_prony_joint_history`](modules/api/fabrication.unilateral_nonlinear_gasket_prony_joint_history.md) | Caller-authorized nonlinear generalized-Maxwell gasket curves and a nonlinear bolt curve are solved with compression-only contact at each declared time knot. |
| [`fabrication.winterization_inventory`](modules/api/fabrication.winterization_inventory.md) | Each interval uses constant ambient temperature, conductance, trace power and effective isobaric heat capacity. |

## fatigue: 피로·다축 경로·소성·수명

| API | 목적 |
|---|---|
| [`fatigue.area_uniform_fibonacci_plane_grid`](modules/api/fatigue.area_uniform_fibonacci_plane_grid.md) | Unoriented plane normals use midpoint-stratified positive-z coordinates with equal nominal solid-angle weights and a deterministic golden-angle azimuth sequence. |
| [`fatigue.basquin`](modules/api/fatigue.basquin.md) | Stress-range convention, constant amplitude, calibrated user coefficients; no endurance plateau. |
| [`fatigue.carpinteri_spagnoli_finite_limit_screen`](modules/api/fatigue.carpinteri_spagnoli_finite_limit_screen.md) | Uses the quadratic combination of maximum plane-normal stress and weighted shear-vector amplitude on caller-supplied finite planes. |
| [`fatigue.carpinteri_spagnoli_life_dependent_curve`](modules/api/fatigue.carpinteri_spagnoli_life_dependent_curve.md) | Uses finite caller planes and same-condition axial/torsion S-N curves; curve strengths define the life-dependent shear weighting. |
| [`fatigue.closed_tensor_work_life`](modules/api/fatigue.closed_tensor_work_life.md) | Caller-provided closed 3D stress-strain tensor cycles and material-matched work-life calibration with bounded log-log interpolation and explicit Miner accumulation. |
| [`fatigue.continuous_plane_fs_life_bound`](modules/api/fatigue.continuous_plane_fs_life_bound.md) | Map a certified sampled-cycle continuous-plane FS factor interval to a conservative caller-calibrated cycle-life interval over declared support. |
| [`fatigue.critical_plane_adaptive_search`](modules/api/fatigue.critical_plane_adaptive_search.md) | The caller supplies one reviewed closed local tensor cycle, one finite seed grid and an explicit tangent-ring refinement schedule. |
| [`fatigue.critical_plane_continuous_bound`](modules/api/fatigue.critical_plane_continuous_bound.md) | The caller supplies one reviewed closed local tensor cycle, calibrated Fatemi-Socie coefficient and normalization stress, plus explicit orientation and work budgets. |
| [`fatigue.critical_plane_factors`](modules/api/fatigue.critical_plane_factors.md) | The caller supplies a reviewed closed representative local cycle as aligned symmetric Cauchy-stress and small-strain tensors, using tensor rather than engineering shear components. |
| [`fatigue.critical_plane_findley_calibrated_life`](modules/api/fatigue.critical_plane_findley_calibrated_life.md) | Uses the independent finite-sample Findley parameter evaluator and an explicitly supplied, digest-bound monotone parameter-life curve. |
| [`fatigue.critical_plane_findley_parameter`](modules/api/fatigue.critical_plane_findley_parameter.md) | Uses the Findley critical-plane stress parameter with caller-supplied coefficient and reference strength; no coefficient, strength curve or cycle life is inferred. |
| [`fatigue.critical_plane_fs_life`](modules/api/fatigue.critical_plane_fs_life.md) | Identified Fatemi-Socie factor mapped to caller-calibrated engineering-shear strain-life coefficients inside declared cycle support. |
| [`fatigue.critical_plane_grid_family_comparison`](modules/api/fatigue.critical_plane_grid_family_comparison.md) | The caller supplies one reviewed closed local tensor cycle, at least two uniquely identified latitude-azimuth and/or area-stratified Fibonacci grids, an explicit finite reference grid and diagnostic tolerances. |
| [`fatigue.critical_plane_grid_refinement`](modules/api/fatigue.critical_plane_grid_refinement.md) | The caller supplies one reviewed closed local tensor cycle, at least two explicitly ordered hemisphere grids and diagnostic factor-change and plane-rotation tolerances. |
| [`fatigue.critical_plane_minimum_enclosing_circle_factors`](modules/api/fatigue.critical_plane_minimum_enclosing_circle_factors.md) | The caller supplies a reviewed closed local tensor cycle, tensor-shear components, finite orthonormal plane frames and qualified FS parameters. |
| [`fatigue.critical_plane_piecewise_linear_time_history`](modules/api/fatigue.critical_plane_piecewise_linear_time_history.md) | The caller supplies one timed, reviewed closed tensor cycle and explicitly declares piecewise-linear interpolation of the tensor components. |
| [`fatigue.critical_plane_projected_rainflow`](modules/api/fatigue.critical_plane_projected_rainflow.md) | The caller supplies ordered multiaxial stress/strain tensors, finite plane frames, explicit scalar projection choices, path boundary, tensor basis and interpretation reviews. |
| [`fatigue.critical_plane_time_refinement`](modules/api/fatigue.critical_plane_time_refinement.md) | The caller supplies one reviewed cycle at two or more strictly increasing nested time samplings, a fixed finite plane set and explicit time-match and diagnostic tolerances. |
| [`fatigue.critical_plane_vector_path_factors`](modules/api/fatigue.critical_plane_vector_path_factors.md) | The caller supplies a reviewed closed representative local cycle as aligned symmetric Cauchy-stress and small-strain tensors, using tensor rather than engineering shear components. |
| [`fatigue.crossland_proportional_miner_campaign`](modules/api/fatigue.crossland_proportional_miner_campaign.md) | Each block is evaluated by the finite proportional Crossland screen and bounded same-condition caller life curve. |
| [`fatigue.cyclic_response_relative_error`](modules/api/fatigue.cyclic_response_relative_error.md) | Caller-supplied observed/predicted mean and amplitude arrays share strict cycle alignment, explicit positive normalization and a predeclared experiment set. |
| [`fatigue.dang_van_finite_parameter_life`](modules/api/fatigue.dang_van_finite_parameter_life.md) | Consumes only a digest-verified computed result from the named finite-sample Dang Van screen. |
| [`fatigue.dang_van_finite_sample_limit_screen`](modules/api/fatigue.dang_van_finite_sample_limit_screen.md) | Uses the published Dang Van high-cycle form combining centered shear stress history and instantaneous hydrostatic stress, restricted to caller-declared finite shear systems and time samples. |
| [`fatigue.dynamic_modulus_drop_endpoint`](modules/api/fatigue.dynamic_modulus_drop_endpoint.md) | Caller supplies a strictly ordered compressive-branch dynamic-modulus history, explicit reference modulus, loss threshold and closed/open observation-window state. |
| [`fatigue.explicit_critical_plane_cycle_pair_damage`](modules/api/fatigue.explicit_critical_plane_cycle_pair_damage.md) | Caller-declared scalar normal/shear rainflow cycle allocations with calibrated Fatemi-Socie life and explicit Miner accumulation; no temporal pairing is inferred. |
| [`fatigue.goodman`](modules/api/fatigue.goodman.md) | Tensile mean stress only; empirical correction needs material qualification. |
| [`fatigue.hemisphere_plane_grid`](modules/api/fatigue.hemisphere_plane_grid.md) | Unoriented planes are sampled on a deterministic upper-hemisphere latitude-azimuth grid; exact pole and equatorial sign duplicates are removed. |
| [`fatigue.hysteresis_path`](modules/api/fatigue.hysteresis_path.md) | Ordered uniaxial stress-strain path with explicit cycle boundaries and closure quality. |
| [`fatigue.ince_glinka_generalized_strain_amplitude`](modules/api/fatigue.ince_glinka_generalized_strain_amplitude.md) | One caller-declared closed stress/elastic-strain/plastic-strain tensor cycle. |
| [`fatigue.ince_glinka_gsa_life_from_curve`](modules/api/fatigue.ince_glinka_gsa_life_from_curve.md) | One caller-reviewed repeated closed tensor cycle evaluated over the finite supplied plane set. |
| [`fatigue.ince_glinka_gsa_miner_campaign`](modules/api/fatigue.ince_glinka_gsa_miner_campaign.md) | Each declared cycle group reuses the existing caller-input finite-plane Ince–Glinka parameter and caller-monotone GSA-to-life curve; no curve is fitted or extrapolated. |
| [`fatigue.itoh_nonproportional_miner_blocks`](modules/api/fatigue.itoh_nonproportional_miner_blocks.md) | Caller-decomposed blocks each use a distinct closed Itoh strain cycle and a same-condition digest-pinned strain-life curve. |
| [`fatigue.itoh_nonproportional_strain_life`](modules/api/fatigue.itoh_nonproportional_strain_life.md) | A finite sampled Itoh non-proportional strain parameter is recomputed from the nested pinned history. |
| [`fatigue.itoh_nonproportional_strain_parameter`](modules/api/fatigue.itoh_nonproportional_strain_parameter.md) | The evaluated factor is a trapezoidal approximation over the caller-provided samples and clocks for one exactly closed cycle. |
| [`fatigue.j2_armstrong_frederick_strain_history`](modules/api/fatigue.j2_armstrong_frederick_strain_history.md) | Uses a small-strain associative J2 yield surface and one backward-Euler Armstrong-Frederick backstress update per caller strain interval. |
| [`fatigue.j2_prager_strain_history`](modules/api/fatigue.j2_prager_strain_history.md) | Six-component tensors use [xx, yy, zz, xy, yz, zx] order with tensor shear strain coordinates. |
| [`fatigue.life_rmsle`](modules/api/fatigue.life_rmsle.md) | Caller supplies one positive observed and predicted life for every unique predeclared case; censoring is outside this metric. |
| [`fatigue.mcdiarmid_calibrated_miner_campaign`](modules/api/fatigue.mcdiarmid_calibrated_miner_campaign.md) | Blocks consume computed McDiarmid finite-plane indices from one physical scope, asset and location. |
| [`fatigue.miner`](modules/api/fatigue.miner.md) | Linear accumulation omits load sequence and damage interaction; limit is explicitly declared. |
| [`fatigue.morrow_strain_life`](modules/api/fatigue.morrow_strain_life.md) | Caller-calibrated uniaxial Morrow mean-stress correction to the elastic Basquin term of a strain-life relation. |
| [`fatigue.multiaxial_calibration_transfer_audit`](modules/api/fatigue.multiaxial_calibration_transfer_audit.md) | Only exact caller-paired parameter levels and caller-normalized positive weights are summarized. |
| [`fatigue.multiaxial_crossland_proportional_limit_screen`](modules/api/fatigue.multiaxial_crossland_proportional_limit_screen.md) | Uses the maximum sampled hydrostatic stress and half-range of the collinear deviatoric path coordinate. |
| [`fatigue.multiaxial_deviatoric_stress_path_variation`](modules/api/fatigue.multiaxial_deviatoric_stress_path_variation.md) | Finite path variation is the sum of adjacent-sample increments; deviatoric increments use sqrt(J2) distance. |
| [`fatigue.multiaxial_invariant_limit_screen`](modules/api/fatigue.multiaxial_invariant_limit_screen.md) | Requires caller-reviewed coefficients, reference limit, calibration lineage and exact material-condition match; it does not estimate calibration parameters. |
| [`fatigue.multiaxial_life_campaign`](modules/api/fatigue.multiaxial_life_campaign.md) | Closed caller local tensor cycle to supplied sampled planes and same-condition FS/SWT or caller shear-normal calibration; preserve ties and support limits. |
| [`fatigue.multiaxial_life_scenario_envelope`](modules/api/fatigue.multiaxial_life_scenario_envelope.md) | The envelope consumes only digest-pinned computed results from the registered multiaxial critical-plane life campaign. |
| [`fatigue.multiaxial_mcdiarmid_finite_plane_limit_screen`](modules/api/fatigue.multiaxial_mcdiarmid_finite_plane_limit_screen.md) | Every plane is evaluated from the caller finite stress sample set, with its sampled shear-traction path and maximum normal stress. |
| [`fatigue.multiaxial_power_law_life_transfer`](modules/api/fatigue.multiaxial_power_law_life_transfer.md) | A positive weighted log-linear relation between paired target and reference lives is fit at the exact fatigue parameter knots in a digest-pinned calibration audit. |
| [`fatigue.multiaxial_principal_stress_axis_rotation`](modules/api/fatigue.multiaxial_principal_stress_axis_rotation.md) | The six supplied components form symmetric stress tensors in [xx, yy, zz, xy, yz, zx] order. |
| [`fatigue.multiaxial_sampled_shear_path_area`](modules/api/fatigue.multiaxial_sampled_shear_path_area.md) | Uses caller-ordered finite samples and caller-reviewed shear axes on one selected material plane. |
| [`fatigue.multiaxial_sines_life_fit`](modules/api/fatigue.multiaxial_sines_life_fit.md) | Fits a single log-log power relation by unweighted ordinary least squares to caller-declared uncensored failures. |
| [`fatigue.multiaxial_sines_mean_limit_screen`](modules/api/fatigue.multiaxial_sines_mean_limit_screen.md) | Uses caller-specified coefficients, limit and same-material calibration Evidence; no constants are inferred. |
| [`fatigue.multiaxial_sines_parameter_life`](modules/api/fatigue.multiaxial_sines_parameter_life.md) | Uses a caller Sines-style finite-sample parameter screen and a same-material-condition caller life curve. |
| [`fatigue.multiaxial_weighted_life_scenario_moments`](modules/api/fatigue.multiaxial_weighted_life_scenario_moments.md) | Compute descriptive weighted moments over complete digest-pinned multiaxial fatigue life scenarios with caller-supplied ordered weights. |
| [`fatigue.neuber_notch_strain_amplitude`](modules/api/fatigue.neuber_notch_strain_amplitude.md) | Caller-reviewed scalar uniaxial nominal stress amplitude, elastic concentration factor, modulus and stabilized cyclic Ramberg–Osgood parameters are required. |
| [`fatigue.neuber_strain_life_chain`](modules/api/fatigue.neuber_strain_life_chain.md) | Runs the reviewed scalar stabilized notch-root estimate first, then evaluates the local strain amplitude with caller-supplied strain-life coefficients and cycle support. |
| [`fatigue.papadopoulos_p1_calibrated_life`](modules/api/fatigue.papadopoulos_p1_calibrated_life.md) | P1 parameter is computed from a separately reviewed finite orientation quadrature and closed sampled stress cycle. |
| [`fatigue.papadopoulos_p1_calibration`](modules/api/fatigue.papadopoulos_p1_calibration.md) | Uses caller-supplied fully reversed axial and torsional endurance limits from a matched material condition and smooth-specimen basis. |
| [`fatigue.papadopoulos_p1_finite_integral_screen`](modules/api/fatigue.papadopoulos_p1_finite_integral_screen.md) | The integral criterion is approximated by caller-declared finite orientation quadrature; weights must sum to one. |
| [`fatigue.papadopoulos_p1_miner_blocks`](modules/api/fatigue.papadopoulos_p1_miner_blocks.md) | Caller supplies cycle blocks, repetitions, closed stress-cycle histories and the common material condition. |
| [`fatigue.papadopoulos_p2_finite_sample_limit_screen`](modules/api/fatigue.papadopoulos_p2_finite_sample_limit_screen.md) | The Papadopoulos P2 structure combines a critical-plane generalized shear amplitude with maximum hydrostatic stress; the implementation uses only caller-supplied finite planes and finite direction quadrature. |
| [`fatigue.periodic_fourier_tensor_work`](modules/api/fatigue.periodic_fourier_tensor_work.md) | Stress and strain use the same ordered closed tensor cycle and a caller-declared tensor or engineering shear convention. |
| [`fatigue.periodic_fourier_tensor_work_life`](modules/api/fatigue.periodic_fourier_tensor_work_life.md) | Each cycle's work is exact only for its declared full-bandwidth periodic trigonometric interpolant. |
| [`fatigue.periodic_tensor_fourier_rates`](modules/api/fatigue.periodic_tensor_fourier_rates.md) | Returns analytic derivatives with respect to physical time of the full-bandwidth real Fourier interpolants. |
| [`fatigue.periodic_tensor_fourier_reconstruction`](modules/api/fatigue.periodic_tensor_fourier_reconstruction.md) | Uses full-bandwidth trigonometric interpolation on a uniformly sampled, exactly closed periodic tensor cycle. |
| [`fatigue.pressure_loss_endpoint`](modules/api/fatigue.pressure_loss_endpoint.md) | The caller supplies a reviewed pressure-drop threshold, event origin, physical-specimen continuity, load-case identity and valid-cycle accounting; the calculator does not infer them from a pressure trace. |
| [`fatigue.pressurized_annulus_load_state`](modules/api/fatigue.pressurized_annulus_load_state.md) | Long homogeneous isotropic linear-elastic annulus with static pressure, nominal axial force and Saint-Venant torsion; end, notch, fixture, residual-stress and inelastic effects are excluded. |
| [`fatigue.propose_critical_plane_interval_overlap_pairing`](modules/api/fatigue.propose_critical_plane_interval_overlap_pairing.md) | Deterministic continuous-capacity bipartite min-cost max-flow proposal over overlapping sample-index intervals; maximize paired cycle count, then allocated-count-weighted interval IoU. |
| [`fatigue.rainflow`](modules/api/fatigue.rainflow.md) | Uses the installed rainflow library; output range unit matches input, residual excursions remain half cycles. |
| [`fatigue.sampled_stress_invariant_history`](modules/api/fatigue.sampled_stress_invariant_history.md) | Only caller-reviewed, exactly closed finite samples in the declared symmetric tensor basis are summarized. |
| [`fatigue.sampled_tensor_stress_strain_work_cycle`](modules/api/fatigue.sampled_tensor_stress_strain_work_cycle.md) | Stress and strain tensors must share a caller-reviewed conjugate basis, sign convention and exactly closed sample order. |
| [`fatigue.strain_life`](modules/api/fatigue.strain_life.md) | Combined Basquin and Coffin-Manson relation; two reversals per cycle and an explicit calibration interval. |
| [`fatigue.strain_life_campaign`](modules/api/fatigue.strain_life_campaign.md) | Explicit fully reversed, Morrow or SWT blocks with caller-reviewed linear cycle-fraction accumulation; constituent failures withhold the total. |
| [`fatigue.swt_strain_life`](modules/api/fatigue.swt_strain_life.md) | Caller-calibrated uniaxial Smith-Watson-Topper stress-strain parameter for a declared cycle-life interval. |
| [`fatigue.wang_brown_parameter_life_fit`](modules/api/fatigue.wang_brown_parameter_life_fit.md) | A log-log power law is estimated by ordinary least squares from at least three distinct caller test levels. |
| [`fatigue.wang_brown_reviewed_excursion_parameter`](modules/api/fatigue.wang_brown_reviewed_excursion_parameter.md) | Evaluates a finite-plane Wang-Brown-style parameter using explicitly reviewed shear-reversal endpoints and the normal-strain excursion on the ordered arc. |
| [`fatigue.wang_brown_temporal_normal_excursion`](modules/api/fatigue.wang_brown_temporal_normal_excursion.md) | The shear cycle sequence is caller-counted; normal-strain samples are associated by the cycle's inclusive sample-index interval. |

## flow: flow

| API | 목적 |
|---|---|
| [`flow.declared_inverse_sqrt_density_velocity`](modules/api/flow.declared_inverse_sqrt_density_velocity.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`flow.homogeneous_no_slip_mixture_density`](modules/api/flow.homogeneous_no_slip_mixture_density.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |

## fracture: 균열·응력확대계수·파괴역학

| API | 목적 |
|---|---|
| [`fracture.paris_constant_amplitude`](modules/api/fracture.paris_constant_amplitude.md) | Constant stress range and geometry factor; Paris region only, no initiation, closure, threshold or toughness termination inference. |
| [`fracture.sequence_zone_memory`](modules/api/fracture.sequence_zone_memory.md) | Caller-calibrated opening ratio and plastic-zone memory with explicit whole-cycle stepping, state checkpoints, and distinct fracture/depth/support termination. |
| [`fracture.stress_intensity`](modules/api/fracture.stress_intensity.md) | Mode-I LEFM and constant user geometry factor; plastic collapse and crack interaction excluded. |
| [`fracture.tabulated_crack_growth`](modules/api/fracture.tabulated_crack_growth.md) | Caller-authorized tabulated da/dN curve, explicitly matched and reviewed target material/environment, reviewed nondecreasing geometry provider and ordered tensile load blocks. |
| [`fracture.tabulated_crack_growth_scenario_ensemble`](modules/api/fracture.tabulated_crack_growth_scenario_ensemble.md) | Caller-reviewed weighted complete inputs for the single-curve or curve-family deterministic model preserve joint variation in curve points, geometry, ordered loads, toughness and controls. |
| [`fracture.tabulated_crack_growth_scenario_reduction`](modules/api/fracture.tabulated_crack_growth_scenario_reduction.md) | Portable reduction of externally evaluated complete crack-growth scenarios with exact manifest coverage, input digests and one evaluator identity/configuration. |
| [`fracture.tabulated_crack_growth_uncertainty`](modules/api/fracture.tabulated_crack_growth_uncertainty.md) | Caller-supplied normalized joint uncertainty rows multiply curve rates, geometry factors, tensile stresses and toughness while preserving row dependence. |
| [`fracture.tabulated_crack_growth_uncertainty_convergence`](modules/api/fracture.tabulated_crack_growth_uncertainty_convergence.md) | Two or more caller-reviewed uncertainty designs for one distribution and deterministic crack-growth input, with explicit nested, refined or replicate relationships. |
| [`fracture.tabulated_curve_family_growth`](modules/api/fracture.tabulated_curve_family_growth.md) | Caller-reviewed curve family explicitly matched to the assessment target material/environment; each block selects one curve by explicit stress-ratio and relative-frequency tolerances. |
| [`fracture.tabulated_growth_rate`](modules/api/fracture.tabulated_growth_rate.md) | Caller-authorized positive crack-growth points with strictly increasing delta K; log-log interpolation is confined to the supplied support. |
| [`fracture.variable_paris`](modules/api/fracture.variable_paris.md) | Ordered tensile blocks with explicit Paris calibration, threshold, toughness and bounded geometry provider. |

## geometry: 형상·손실 프로파일·공간 자료

| API | 목적 |
|---|---|
| [`geometry.rectilinear_thickness_map`](modules/api/geometry.rectilinear_thickness_map.md) | Cell edges define a rectilinear map in metres and matrix entries are cell-centred thicknesses in metres. |
| [`geometry.thickness_grid`](modules/api/geometry.thickness_grid.md) | Equal-area cell observations with explicit missing coverage; reporting threshold is caller supplied. |

## inspection: 검사·영상·관측·품질·절차

| API | 목적 |
|---|---|
| [`inspection.acoustic_emission_arrival_localization`](modules/api/inspection.acoustic_emission_arrival_localization.md) | Multi-sensor arrival-time localization in one reviewed frame with fixed caller-supplied wave speed. |
| [`inspection.acoustic_emission_arrival_pick`](modules/api/inspection.acoustic_emission_arrival_pick.md) | Caller-reviewed monotonic sample clock, waveform unit, immutable waveform digest and fixed windows. |
| [`inspection.acoustic_emission_campaign`](modules/api/inspection.acoustic_emission_campaign.md) | Asset geometry, zones, sensors, channels, acquisition intervals and event features are reviewed caller records. |
| [`inspection.acoustic_emission_campaign_quality`](modules/api/inspection.acoustic_emission_campaign_quality.md) | Array, coupling, acquisition, baseline, observation and reference identities are caller supplied. |
| [`inspection.acoustic_emission_wave_speed_calibration`](modules/api/inspection.acoustic_emission_wave_speed_calibration.md) | Weighted linear calibration of arrival minus known emission time against known source-sensor distance. |
| [`inspection.action_expected_loss`](modules/api/inspection.action_expected_loss.md) | One event, physical scope, horizon, survival conditioning and cost basis; every complete action retains an externally evaluated residual first-failure probability and reviewed additive costs; expectation is probability times conditional consequence plus action cost. |
| [`inspection.binomial_evidence`](modules/api/inspection.binomial_evidence.md) | Independent homogeneous inspection opportunities with explicit detection/false-call semantics. |
| [`inspection.blind_indicator_hole_ligament`](modules/api/inspection.blind_indicator_hole_ligament.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`inspection.boil_off_calorimetry`](modules/api/inspection.boil_off_calorimetry.md) | Isobaric saturated liquid bath; explicitly declared level/makeup mode and negligible unmodelled energy terms. |
| [`inspection.coupling_pressure`](modules/api/inspection.coupling_pressure.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`inspection.cryogenic_leak_test_evidence`](modules/api/inspection.cryogenic_leak_test_evidence.md) | Cycle temperature and pressure extrema, medium identity and pressure basis are reviewed caller records. |
| [`inspection.cryogenic_leak_testing_campaign_quality`](modules/api/inspection.cryogenic_leak_testing_campaign_quality.md) | Reference, blank/background, state, repeatability, drift and capability evidence is caller supplied. |
| [`inspection.declared_impact_subsize_requirements`](modules/api/inspection.declared_impact_subsize_requirements.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`inspection.disposition_decision_tree`](modules/api/inspection.disposition_decision_tree.md) | One reviewed exhaustive mutually exclusive inspection-outcome partition over one event context; each branch supplies its probability, complete disposition, conditional residual first-failure probability and costs; finite expectations only. |
| [`inspection.eddy_current_acquisition_summary`](modules/api/inspection.eddy_current_acquisition_summary.md) | Caller-controlled probe, reference standard, electromagnetic properties, encoded scan and indication record; no embedded detection or acceptance rule. |
| [`inspection.eddy_current_campaign_quality`](modules/api/inspection.eddy_current_campaign_quality.md) | Probe/sensor, magnetizer, excitation, lift-off, speed, channel and scan identities are caller supplied. |
| [`inspection.file_homogeneous_fmc_tfm`](modules/api/inspection.file_homogeneous_fmc_tfm.md) | Numeric NPY storage, dtype, complete ordered-pair row manifest and a common sample clock are explicit and digest-bound. |
| [`inspection.file_planar_multiview_fmc_tfm`](modules/api/inspection.file_planar_multiview_fmc_tfm.md) | Numeric NPY storage, dtype, complete ordered-pair row manifest and a common sample clock are explicit and digest-bound. |
| [`inspection.finite_policy_path_generation`](modules/api/inspection.finite_policy_path_generation.md) | Reviewed finite state, initial, observation, fixed decision-rule and transition tables over ordered epochs; enumerate every positive-probability path exactly within a caller-declared path-count limit. |
| [`inspection.finite_policy_probability_calibration`](modules/api/inspection.finite_policy_probability_calibration.md) | Reviewed finite physical-state truth, inspection labels and action-conditioned longitudinal transitions with immutable, sequence- and source-group-disjoint calibration/holdout partitions; weighted empirical frequencies and an explicit symmetric pseudocount only. |
| [`inspection.flux_leakage_campaign_quality`](modules/api/inspection.flux_leakage_campaign_quality.md) | Probe/sensor, magnetizer, excitation, lift-off, speed, channel and scan identities are caller supplied. |
| [`inspection.fracture_toughness_test_evidence`](modules/api/inspection.fracture_toughness_test_evidence.md) | Every record preserves material condition, specimen/source identity, geometry/orientation, test conditions, endpoint, unit and caller-supplied validity evidence. |
| [`inspection.fracture_toughness_testing`](modules/api/inspection.fracture_toughness_testing.md) | Specimen, geometry, orientation, precrack, loading, result, uncertainty and provenance remain caller evidence. |
| [`inspection.gas_expansion_energy`](modules/api/inspection.gas_expansion_energy.md) | Ideal reversible adiabatic gas expansion; not a blast model or exclusion-distance determination. |
| [`inspection.gas_pressure_decay`](modules/api/inspection.gas_pressure_decay.md) | Known compressibility at both equilibrated endpoints and an explicit reporting reference state. |
| [`inspection.guided_wave_pair_features`](modules/api/inspection.guided_wave_pair_features.md) | One physical specimen, aligned provider distance grids and one declared spatial window; paired descriptors do not separate environmental change from damage. |
| [`inspection.guided_wave_reference_ensemble`](modules/api/inspection.guided_wave_reference_ensemble.md) | At least three explicitly selected same-specimen baseline acquisitions, one aligned observation and one spatial window; ensemble descriptors are not detection calibration or acceptance. |
| [`inspection.guided_waves_campaign_quality`](modules/api/inspection.guided_waves_campaign_quality.md) | Array, coupling, acquisition, baseline, observation and reference identities are caller supplied. |
| [`inspection.hardness_reference_block_calibration`](modules/api/inspection.hardness_reference_block_calibration.md) | One exact method, scale, indenter, load, dwell and instrument configuration is calibrated. |
| [`inspection.hardness_testing_campaign`](modules/api/inspection.hardness_testing_campaign.md) | Subject, material, heat, method, scale, load, dwell, indenter, reference block and instrument identities are exact caller inputs. |
| [`inspection.hit_miss_pod`](modules/api/inspection.hit_miss_pod.md) | Increasing logistic POD in log flaw size, independent hit/miss observations and profile-likelihood confidence inference. |
| [`inspection.homogeneous_fmc_tfm`](modules/api/inspection.homogeneous_fmc_tfm.md) | All element and image coordinates share the explicit reviewed frame and material condition. |
| [`inspection.hot_tap_branch_test_pressure_cap`](modules/api/inspection.hot_tap_branch_test_pressure_cap.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`inspection.impact_metric_crossings`](modules/api/inspection.impact_metric_crossings.md) | One reviewed common material/geometry/orientation series, explicit point statistic, native SI/fraction metric and caller target. |
| [`inspection.impact_testing_campaign`](modules/api/inspection.impact_testing_campaign.md) | Specimen, product, heat, orientation, notch, size, machine, striker and calibration identities are exact caller inputs. |
| [`inspection.indication_window_accumulation`](modules/api/inspection.indication_window_accumulation.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`inspection.instrumented_impact_signal_summary`](modules/api/inspection.instrumented_impact_signal_summary.md) | The supplied signal is calibrated SI force, displacement and time with a reviewed sign convention and valid window. |
| [`inspection.known_volume_pressure_rise`](modules/api/inspection.known_volume_pressure_rise.md) | Rigid known volume, absolute pressure, one reviewed clock and independent blank/test source groups. |
| [`inspection.leak_rate_campaign_quality`](modules/api/inspection.leak_rate_campaign_quality.md) | Reference, blank/background, state, repeatability, drift and capability evidence is caller supplied. |
| [`inspection.liquid_penetrant_summary`](modules/api/inspection.liquid_penetrant_summary.md) | Caller-controlled material, consumables, sequence, temperature, time, lighting, coverage and indication records; no embedded acceptance rule. |
| [`inspection.logistic_pod`](modules/api/inspection.logistic_pod.md) | User-calibrated log-size logistic curve; false calls and confidence bounds are separate. |
| [`inspection.lot_sampling_escalation`](modules/api/inspection.lot_sampling_escalation.md) | Explicit physical population and caller-authorized sample/escalation plan for one method and criterion. |
| [`inspection.magnetic_flux_leakage_acquisition_summary`](modules/api/inspection.magnetic_flux_leakage_acquisition_summary.md) | Caller-controlled magnetizer, sensor array, field-state checkpoint, reference-standard, encoded-scan and indication record; no embedded sizing or acceptance rule. |
| [`inspection.magnetic_particle_summary`](modules/api/inspection.magnetic_particle_summary.md) | Caller-reviewed ferromagnetic applicability, media, equipment, field adequacy, directional requirement, coverage and indication records; no embedded acceptance rule. |
| [`inspection.multi_period_policy_comparison`](modules/api/inspection.multi_period_policy_comparison.md) | At least two complete externally evaluated policies over one common event, scope, horizon, start-survival condition, cost and discount basis; apply caller-approved hard probability and resource constraints before finite expected-loss comparison. |
| [`inspection.multi_period_policy_evaluation`](modules/api/inspection.multi_period_policy_evaluation.md) | One complete caller-reviewed finite policy-path ensemble over a common event, scope, horizon, start-survival condition, cost and discount basis; evaluate path-probability-weighted discounted action and first-failure consequence costs without policy search. |
| [`inspection.no_indication_update`](modules/api/inspection.no_indication_update.md) | POD conditional on each prior bin; random independent coverage and no false indication mechanism. |
| [`inspection.phased_array_acquisition_summary`](modules/api/inspection.phased_array_acquisition_summary.md) | Caller-controlled probe, wedge, material velocity, beam-law, encoder, frame and indication record; no embedded reconstruction or acceptance rule. |
| [`inspection.phased_array_campaign_quality`](modules/api/inspection.phased_array_campaign_quality.md) | Procedure, acquisition, reference standard, coverage and encoded-data identities are caller supplied. |
| [`inspection.pipe_membrane_test_pressure`](modules/api/inspection.pipe_membrane_test_pressure.md) | Caller provides the applicable material yield strength, factor and its review basis. |
| [`inspection.planar_multiview_fmc_tfm`](modules/api/inspection.planar_multiview_fmc_tfm.md) | Elements and image points occupy opposite sides of one explicit planar interface in the reviewed common coordinate frame. |
| [`inspection.pressure_test_eligibility`](modules/api/inspection.pressure_test_eligibility.md) | Test method, medium, pressure basis and component/material identities are caller-reviewed. |
| [`inspection.pressure_test_load`](modules/api/inspection.pressure_test_load.md) | User-selected factor and allowables; no automatic standard eligibility or test approval. |
| [`inspection.pulse_echo_sound_speed_fit`](modules/api/inspection.pulse_echo_sound_speed_fit.md) | Fixed reviewed time zero and incidence angle; through-origin least squares on independently measured reference thicknesses; conditional uncertainty excludes errors in predictors and fixed inputs. |
| [`inspection.radiographic_geometry_summary`](modules/api/inspection.radiographic_geometry_summary.md) | Caller-controlled radiographic source, exposure, detector, image, IQI, projection geometry and indication record; no embedded acceptance rule. |
| [`inspection.radiography_campaign_quality`](modules/api/inspection.radiography_campaign_quality.md) | Procedure, acquisition, reference standard, coverage and encoded-data identities are caller supplied. |
| [`inspection.reference_energy_mass`](modules/api/inspection.reference_energy_mass.md) | Caller supplies the reference identity, specific energy in J/kg and the physical basis of input energy. |
| [`inspection.reference_leak_response_calibration`](modules/api/inspection.reference_leak_response_calibration.md) | Only valid detected rows with positive traceable molar leak rate and response enter the fit. |
| [`inspection.replica_feature_density_summary`](modules/api/inspection.replica_feature_density_summary.md) | Frame calibration, SI scale and uncertainty are caller-reviewed and traceable. |
| [`inspection.replica_metallography_campaign`](modules/api/inspection.replica_metallography_campaign.md) | Component, location, material, heat and ordered service history are exact caller inputs. |
| [`inspection.replica_metallography_evidence`](modules/api/inspection.replica_metallography_evidence.md) | Replica sites and physical source groups retain caller-reviewed mappings. |
| [`inspection.signal_response_pod_calibration`](modules/api/inspection.signal_response_pod_calibration.md) | Signal is linear in natural-log flaw size with independent normal residuals and caller weights. |
| [`inspection.surface_profile_roughness`](modules/api/inspection.surface_profile_roughness.md) | Caller-reviewed filtered profile and evaluation direction; explicitly piecewise-linear positions/heights with a length-weighted mean removed. |
| [`inspection.tensile_offset_yield_campaign`](modules/api/inspection.tensile_offset_yield_campaign.md) | Specimen, product, heat, orientation, geometry, machine, load-cell and extensometer identities are exact caller inputs. |
| [`inspection.tensile_offset_yield_curve`](modules/api/inspection.tensile_offset_yield_curve.md) | The supplied curve is a reviewed monotonic engineering-strain loading branch inside a pre-necking analysis window. |
| [`inspection.test_water_quality`](modules/api/inspection.test_water_quality.md) | Source, batch, circuit, contact, history, sampling, laboratory and exact analytical identities are preserved. |
| [`inspection.test_water_quality_summary`](modules/api/inspection.test_water_quality_summary.md) | Samples retain explicit location, time, method and evidence identities on one reviewed test clock. |
| [`inspection.thread_connection_pressure`](modules/api/inspection.thread_connection_pressure.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`inspection.threshold_inspection_schedule`](modules/api/inspection.threshold_inspection_schedule.md) | Caller-reviewed cumulative first-crossing probabilities on strictly ordered candidate times; select the latest supplied candidate within notice and deferral limits that satisfies a user-approved probability criterion without interpolation or consequence optimization. |
| [`inspection.tofd_acquisition_summary`](modules/api/inspection.tofd_acquisition_summary.md) | Caller-controlled TOFD probe pair, velocity, wall, encoder, frame, time-pick and indication record; symmetric straight paths only. |
| [`inspection.tofd_depth`](modules/api/inspection.tofd_depth.md) | Straight longitudinal paths in a homogeneous flat section and a centred tip. |
| [`inspection.ultrasonic_thickness`](modules/api/inspection.ultrasonic_thickness.md) | Single homogeneous sound path and declared refracted angle; coating and mode conversion excluded. |
| [`inspection.vacuum_rise`](modules/api/inspection.vacuum_rise.md) | Isothermal pressure rise with declared background gas load; no material leak limit bundled. |
| [`inspection.vacuum_testing_campaign_quality`](modules/api/inspection.vacuum_testing_campaign_quality.md) | Reference, blank/background, state, repeatability, drift and capability evidence is caller supplied. |
| [`inspection.visual_surface_summary`](modules/api/inspection.visual_surface_summary.md) | Caller-defined mutually exclusive target areas, reviewed coverage and surface condition, traceable procedure and indication mapping; no acceptance or detection inference. |

## integration: 여러 계산 단계의 증거 기반 연결

| API | 목적 |
|---|---|
| [`integration.adaptive_cycle_block_damage`](modules/api/integration.adaptive_cycle_block_damage.md) | The caller supplies a deterministic provider whose identity, revision and configuration digest match the request. |
| [`integration.aqueous_bdot_speciation_history`](modules/api/integration.aqueous_bdot_speciation_history.md) | Each exact time knot carries a complete caller-reviewed mass-action system and B-dot parameter record matched to that knot's temperature. |
| [`integration.aqueous_candidate_network_speciation`](modules/api/integration.aqueous_candidate_network_speciation.md) | Only the exact computed mass-action system assembled by a digest-pinned candidate workflow is passed to the established aqueous speciation solver. |
| [`integration.aqueous_candidate_network_workflow`](modules/api/integration.aqueous_candidate_network_workflow.md) | A caller-defined closed candidate species inventory and formula/charge set is screened with explicit search budgets. |
| [`integration.aqueous_external_activity_speciation_history`](modules/api/integration.aqueous_external_activity_speciation_history.md) | Every exact time knot carries a separately reviewed mass-action system and caller-owned composition-dependent activity provider record. |
| [`integration.aqueous_mass_action_cycle_audit`](modules/api/integration.aqueous_mass_action_cycle_audit.md) | The existing mass-action species, formulas, charges, reaction direction, log10(K), temperature and standard state are reused without chemical reinterpretation. |
| [`integration.aqueous_mass_action_to_crevice_nernst_history`](modules/api/integration.aqueous_mass_action_to_crevice_nernst_history.md) | Only dimensionless activities and exact time/temperature knots from a computed digest-pinned crevice mass-action or B-dot speciation history are consumed. |
| [`integration.aqueous_mass_action_vant_hoff_history`](modules/api/integration.aqueous_mass_action_vant_hoff_history.md) | Integrate the van't Hoff relation with caller-supplied reference reaction enthalpy, then solve the existing single-phase aqueous mass-action system independently at aligned temperature knots. |
| [`integration.aqueous_saturation_to_surface_scale_kinetics`](modules/api/integration.aqueous_saturation_to_surface_scale_kinetics.md) | Transfers one caller-selected solid saturation-ratio history from exact digest-pinned aqueous equilibrium knots to an explicit single-phase scale-thickness law and optionally an area-average coverage law. |
| [`integration.aqueous_vant_hoff_saturation_events`](modules/api/integration.aqueous_vant_hoff_saturation_events.md) | Extract one explicitly selected solid from every exact computed knot of a digest-pinned aqueous van't Hoff saturation AssessmentResult and audit reviewed threshold crossings. |
| [`integration.aqueous_vant_hoff_saturation_history`](modules/api/integration.aqueous_vant_hoff_saturation_history.md) | Screens only caller-selected candidate solids using the exact computed species activities at each digest-pinned van't Hoff history knot. |
| [`integration.co2_henry_temperature_to_fixed_fugacity_carbonate`](modules/api/integration.co2_henry_temperature_to_fixed_fugacity_carbonate.md) | A completed Henry-temperature AssessmentResult is reconstructed and verified against its exact request, input digest, unit, solvent, temperature and output digest before handoff. |
| [`integration.co2_henry_temperature_to_fixed_fugacity_carbonate_history`](modules/api/integration.co2_henry_temperature_to_fixed_fugacity_carbonate_history.md) | Each point requires one computed and digest-verified Henry temperature-correction AssessmentResult and one aligned carbonate-equilibrium input. |
| [`integration.crevice_activity_gradient_nernst_planck_flux_1d`](modules/api/integration.crevice_activity_gradient_nernst_planck_flux_1d.md) | One-dimensional local face law with caller-resolved electroneutral states, linear concentration gradient and log-activity-coefficient gradient. |
| [`integration.crevice_activity_transport_sequential_aperture_campaign`](modules/api/integration.crevice_activity_transport_sequential_aperture_campaign.md) | Each exact caller time segment is solved once on its entering uniform aperture, then explicit phase rates update inventory and the next segment geometry. |
| [`integration.crevice_activity_transport_spatial_phase_aperture_handoff`](modules/api/integration.crevice_activity_transport_spatial_phase_aperture_handoff.md) | The activity-corrected reactive transport calculation is completed on a fixed, uniform initial slit geometry and exact caller clock. |
| [`integration.crevice_aperture_history_refinement`](modules/api/integration.crevice_aperture_history_refinement.md) | The source geometry result is pinned by digest and input state vectors are required to be finite, positive and time ordered. |
| [`integration.crevice_aqueous_component_ledger`](modules/api/integration.crevice_aqueous_component_ledger.md) | Every declared mass-action constraint has exactly one explicit role; the charge-neutrality row exactly matches species charge coefficients and has a zero target. |
| [`integration.crevice_bdf_nucleation_operator_split`](modules/api/integration.crevice_bdf_nucleation_operator_split.md) | Each original interval is operator split: aqueous-only fixed-volume component BDF first, cellwise seed/growth ledger second. |
| [`integration.crevice_calibrated_wall_flux_callback`](modules/api/integration.crevice_calibrated_wall_flux_callback.md) | A calibrated effective wall-transfer velocity and a caller-supplied equilibrium surface concentration define inward flux J=k_w(C_surface-C_bulk). |
| [`integration.crevice_calibrated_wall_sink_rate_history`](modules/api/integration.crevice_calibrated_wall_sink_rate_history.md) | The calibration request/result pair is digest-bound and the computed fit's IDs, parameters and temperature support must match the supplied source request. |
| [`integration.crevice_cellwise_nucleation_kinetic_history`](modules/api/integration.crevice_cellwise_nucleation_kinetic_history.md) | Cell rows are independent closed-batch kinetic ledgers with identical ordered species/phase laws and exact common output times. |
| [`integration.crevice_component_state_bdf`](modules/api/integration.crevice_component_state_bdf.md) | BDF state variables are component moles, and each aqueous reaction conserves every transported component map. |
| [`integration.crevice_component_state_faradaic_schedule_binding`](modules/api/integration.crevice_component_state_faradaic_schedule_binding.md) | Producer and component-state time knots, species order/charge, cell order and initial conserved inventories must match. |
| [`integration.crevice_component_state_segment_handoff`](modules/api/integration.crevice_component_state_segment_handoff.md) | The source BDF request and exact Calculation result are digest-pinned and the source is committed with closed total-component ledgers. |
| [`integration.crevice_component_state_segment_transition`](modules/api/integration.crevice_component_state_segment_transition.md) | Source BDF result is full-digest-bound, committed and component-ledger closed. |
| [`integration.crevice_composition_to_aqueous_mass_action_history`](modules/api/integration.crevice_composition_to_aqueous_mass_action_history.md) | Every composition knot binds to a caller-supplied aqueous reaction/constraint network and exact-temperature parameter set. |
| [`integration.crevice_current_carrying_aperture_feedback`](modules/api/integration.crevice_current_carrying_aperture_feedback.md) | Caller-specified solid molar volumes map endpoint aqueous/solid states to trial aperture histories. |
| [`integration.crevice_current_carrying_extent_to_metal_loss`](modules/api/integration.crevice_current_carrying_extent_to_metal_loss.md) | Consumes a computed, complete, digest-pinned current-carrying Faradaic AssessmentResult and its exact request. |
| [`integration.crevice_current_carrying_np_faradaic`](modules/api/integration.crevice_current_carrying_np_faradaic.md) | Cell 0 is the potential gauge at each exact knot; mouth and blind tip have zero ionic current. |
| [`integration.crevice_deposition_aperture_history`](modules/api/integration.crevice_deposition_aperture_history.md) | Each exact-knot solid-volume result is per the declared reference area and matches the physical scope, time and cell ordering. |
| [`integration.crevice_deposition_transport_geometry`](modules/api/integration.crevice_deposition_transport_geometry.md) | Only the upstream volume-conserving equivalent mean aperture is forwarded; it is treated as uniform within each transport cell after explicit caller review. |
| [`integration.crevice_double_layer_charge_history`](modules/api/integration.crevice_double_layer_charge_history.md) | Potential, active area, reference potential and differential-capacitance curve are caller records pinned by licensed Evidence. |
| [`integration.crevice_double_layer_to_component_bdf_binding`](modules/api/integration.crevice_double_layer_to_component_bdf_binding.md) | The double-layer history uses caller-pinned potential, reference potential, active area and differential capacitance; its stored charge is positive into the electrode. |
| [`integration.crevice_dynamic_double_layer_faradaic_history`](modules/api/integration.crevice_dynamic_double_layer_faradaic_history.md) | Caller-provided polarization and differential-capacitance curves are used only within their declared supports. |
| [`integration.crevice_dynamic_double_layer_to_component_bdf_binding`](modules/api/integration.crevice_dynamic_double_layer_to_component_bdf_binding.md) | Caller maps every signed polarization branch to an evidenced aqueous reaction and electron number. |
| [`integration.crevice_electrochemical_composition_history`](modules/api/integration.crevice_electrochemical_composition_history.md) | The digest-pinned upstream flux ledger is area-scaled and mapped directly into caller-declared aqueous species inventories using the caller sign convention. |
| [`integration.crevice_electrochemical_inventory_transfer`](modules/api/integration.crevice_electrochemical_inventory_transfer.md) | Only a computed digest-pinned crevice mixed-potential result is accepted, and the exact upstream reference-area basis is reused. |
| [`integration.crevice_external_activity_local_solid_saturation`](modules/api/integration.crevice_external_activity_local_solid_saturation.md) | The computed external-activity projection result must match its typed input, transport binding, exact knot and all cell context digests. |
| [`integration.crevice_faradaic_spatial_chemistry_coupling`](modules/api/integration.crevice_faradaic_spatial_chemistry_coupling.md) | Caller declares all branch kinetics, standard potentials, activity quotient coefficients, conductivity mappings, reaction stoichiometry and external element reservoirs. |
| [`integration.crevice_ionic_reactive_transport_1d`](modules/api/integration.crevice_ionic_reactive_transport_1d.md) | Fixed geometry dilute-ion finite-volume transport with caller-defined linearly varying axial face velocity, electroneutral states and zero ionic current. |
| [`integration.crevice_kinetic_solid_volume_history`](modules/api/integration.crevice_kinetic_solid_volume_history.md) | Upstream solid_inventory_mol_m3_by_phase values are per solution volume and their exact species/phase order is bound to the typed kinetic campaign. |
| [`integration.crevice_local_external_activity_projection`](modules/api/integration.crevice_local_external_activity_projection.md) | Transported cell compositions set only the explicitly selected mass-action constraint targets; each exact cell then solves an independent caller-reviewed activity fixed point. |
| [`integration.crevice_local_mass_action_projection`](modules/api/integration.crevice_local_mass_action_projection.md) | For every exact transport cell knot, the caller supplies a reviewed single-liquid mass-action system whose species order matches the transported composition. |
| [`integration.crevice_local_solid_saturation`](modules/api/integration.crevice_local_solid_saturation.md) | The selected local-speciation ledger result and each exact transport cell context must match their supplied canonical digests. |
| [`integration.crevice_local_speciation_volume_ledger`](modules/api/integration.crevice_local_speciation_volume_ledger.md) | Each local equilibrium result must be computed from the exact supplied mass-action request, and that request/result pair must be caller-mapped to the digest of one exact transport cell state. |
| [`integration.crevice_moving_volume_liquid_continuity`](modules/api/integration.crevice_moving_volume_liquid_continuity.md) | Linear aperture change between exact knots implies constant interval-mean volume rate. |
| [`integration.crevice_multispecies_wall_flux_callback`](modules/api/integration.crevice_multispecies_wall_flux_callback.md) | Each transported species has one digest-pinned calibrated wall-transfer history and an explicit equilibrium surface-concentration profile on the same geometry knots. |
| [`integration.crevice_neutral_reactive_transport_1d`](modules/api/integration.crevice_neutral_reactive_transport_1d.md) | Caller-defined neutral chemical species undergo reversible local mass-action reactions while diffusing through a fixed one-dimensional finite-volume geometry. |
| [`integration.crevice_saturation_exposure_history`](modules/api/integration.crevice_saturation_exposure_history.md) | Every upstream exact-knot saturation result is computed, digest-pinned, and belongs to the declared physical scope and exact time. |
| [`integration.crevice_saturation_interval_average_rates`](modules/api/integration.crevice_saturation_interval_average_rates.md) | Exact local saturation results cover every transport cell and candidate solid at each exact transport clock knot. |
| [`integration.crevice_solid_inventory_geometry_boundary_remap`](modules/api/integration.crevice_solid_inventory_geometry_boundary_remap.md) | The source kinetic result is computed, digest-bound, closed within its declared tolerance, and uses the typed fixed-geometry campaign. |
| [`integration.crevice_solid_volume_hydraulic_stage`](modules/api/integration.crevice_solid_volume_hydraulic_stage.md) | The adapter requires a committed, digest-matched signed phase-volume result and matching assessment, scope, stage time and ordered cells. |
| [`integration.crevice_solid_volume_inventory`](modules/api/integration.crevice_solid_volume_inventory.md) | Each phase inventory is nonnegative amount per caller-reviewed reference area for the same exact snapshot and spatial cell mapping. |
| [`integration.crevice_spatial_chemistry_aperture_fixed_point`](modules/api/integration.crevice_spatial_chemistry_aperture_fixed_point.md) | Each outer trial reruns the registered spatial chemistry-transport operator-split calculation on its exact knot history. |
| [`integration.crevice_spatial_mass_action_workflow`](modules/api/integration.crevice_spatial_mass_action_workflow.md) | A complete caller-provided aqueous mass-action system is solved independently at each exact transport knot and cell; only the existing solver is used. |
| [`integration.crevice_spatial_ohmic_mixed_potential`](modules/api/integration.crevice_spatial_ohmic_mixed_potential.md) | One continuous metal conductor has a common potential and caller-defined reaction branches act at finite slit cells. |
| [`integration.crevice_spatial_ohmic_partial_current_metal_loss`](modules/api/integration.crevice_spatial_ohmic_partial_current_metal_loss.md) | A computed spatial ohmic mixed-potential history is the sole current source and is pinned by its complete AssessmentResult digest. |
| [`integration.crevice_transport_to_local_mass_action`](modules/api/integration.crevice_transport_to_local_mass_action.md) | Caller-reviewed one-to-one mappings set one existing aqueous mass-action linear constraint from a transported concentration per exact cell and knot. |
| [`integration.crevice_transport_volume_weighted_composition`](modules/api/integration.crevice_transport_volume_weighted_composition.md) | Only a computed transport result whose digest is bound to the exact campaign request and geometry history is accepted. |
| [`integration.crevice_wall_flux_inventory_history`](modules/api/integration.crevice_wall_flux_inventory_history.md) | The callback rate, wall surface concentration, bulk concentration, wall-area density and slit cross section are reconstructed linearly within each exact shared time interval. |
| [`integration.cycle_block_feature_handoff`](modules/api/integration.cycle_block_feature_handoff.md) | Extract exact finite-plane scalar stress/strain features from each caller representative closed tensor cycle and map selected values, units, cycle population and integer repetition count into the adaptive cycle-block contract. |
| [`integration.elastic_joint_load_ordered_history`](modules/api/integration.elastic_joint_load_ordered_history.md) | Each ordered snapshot is evaluated independently with the declared elastic two-spring closed-contact model. |
| [`integration.elastic_joint_to_flange_contact_history`](modules/api/integration.elastic_joint_to_flange_contact_history.md) | At each exact caller load snapshot, apply only the supplied linear nodal closure-per-clamp-force mapping around its declared reference clamp force, then reuse the existing flange contact field solver. |
| [`integration.electrochemical_chemistry_boundary_audit`](modules/api/integration.electrochemical_chemistry_boundary_audit.md) | Digest-pinned computed chemistry/speciation/transport stages must align on asset, location, clock, exact times, temperatures, material condition, solvent and activity standard state. |
| [`integration.electrochemical_metal_loss_to_crevice_geometry`](modules/api/integration.electrochemical_metal_loss_to_crevice_geometry.md) | Only a computed digest-pinned electrochemical metal-loss result with every selected reaction explicitly allocated is accepted. |
| [`integration.electrochemical_metal_loss_wall_thickness_history`](modules/api/integration.electrochemical_metal_loss_wall_thickness_history.md) | Requires a computed digest-pinned electrochemical metal-loss result and an Evidence-linked measured wall-thickness baseline at the first interval start. |
| [`integration.electrochemical_partial_current_metal_loss`](modules/api/integration.electrochemical_partial_current_metal_loss.md) | A digest-pinned computed mixed-potential history is required; branch electron number and exposed area are read from that exact upstream request. |
| [`integration.electrochemical_wall_flux_schedule`](modules/api/integration.electrochemical_wall_flux_schedule.md) | The upstream metal-loss ledger is digest-pinned and only anodic metal removal is mapped. |
| [`integration.electrochemical_wall_thickness_scenario_envelope`](modules/api/integration.electrochemical_wall_thickness_scenario_envelope.md) | Consumes only complete digest-pinned computed wall-thickness history AssessmentResults on one common physical/material scope and measured baseline. |
| [`integration.external_crevice_solver_receipt`](modules/api/integration.external_crevice_solver_receipt.md) | An external solver receipt must match the pinned aperture history, cell mesh, face ordering, SI units, axial sign and exact time knots. |
| [`integration.external_flange_compliance_history`](modules/api/integration.external_flange_compliance_history.md) | Every caller-declared knot is paired with a digest-verified external FE stiffness receipt using a stable provider revision, asset scope and ordered translational contact mapping. |
| [`integration.external_flange_compliance_receipt`](modules/api/integration.external_flange_compliance_receipt.md) | A digest-pinned finite-element receipt must identify the selected load case, mesh, coordinate frame, stiffness result field, explicit translational DOF map and contact-normal signs before reduction. |
| [`integration.external_flange_diagnostic_screen`](modules/api/integration.external_flange_diagnostic_screen.md) | Criteria and uncertainty comparisons are caller-owned and evidence-backed. |
| [`integration.external_gasket_fe_field_import`](modules/api/integration.external_gasket_fe_field_import.md) | The adapter validates caller-supplied field metadata, array digests, direct location mapping, support data and exact solver-step time bindings against a structural provider receipt. |
| [`integration.findley_miner_ordered_block_history`](modules/api/integration.findley_miner_ordered_block_history.md) | Every block carries a computed, digest-consistent calibrated Findley life result for one shared asset, location and material condition. |
| [`integration.fixed_fugacity_carbonate_to_scale_kinetics`](modules/api/integration.fixed_fugacity_carbonate_to_scale_kinetics.md) | Use the exact computed fixed-fugacity carbonate history CO3 concentration, multiply by a caller-provided activity coefficient under the declared 1 mol/L standard state, add explicitly supplied activities for all other candidate-solid species, and screen one caller-selected phase with per-knot Ksp records. |
| [`integration.gasket_fe_von_mises_caller_limit_screen`](modules/api/integration.gasket_fe_von_mises_caller_limit_screen.md) | Six imported symmetric Cauchy stress components in one caller-mapped Cartesian frame are reduced by the J2/von Mises invariant. |
| [`integration.gasket_joint_equilibrium_local_covariance`](modules/api/integration.gasket_joint_equilibrium_local_covariance.md) | Caller-supplied covariance is propagated as J Sigma J^T using central finite differences of the existing multi-bolt sector equilibrium API. |
| [`integration.gasket_joint_spatial_resultant_balance`](modules/api/integration.gasket_joint_spatial_resultant_balance.md) | Only exact-knot per-bolt forces from one computed multi-bolt joint result are reconciled with one computed static unilateral contact field. |
| [`integration.gasket_leakage_pressure_inventory_decay`](modules/api/integration.gasket_leakage_pressure_inventory_decay.md) | Gas inventory follows a fixed-volume isothermal ideal-gas equation of state. |
| [`integration.gasket_leakage_rate_threshold_events`](modules/api/integration.gasket_leakage_rate_threshold_events.md) | The source must be a digest-pinned computed gasket leakage history with explicit mol/s and s units. |
| [`integration.gasket_leakage_scenario_exposure`](modules/api/integration.gasket_leakage_scenario_exposure.md) | Only a digest-pinned computed finite correlated leakage scenario snapshot is accepted. |
| [`integration.gasket_leakage_scenario_rate_interval`](modules/api/integration.gasket_leakage_scenario_rate_interval.md) | Only two digest-pinned computed envelopes with identical joint/scenario/calibration identity and node order are accepted. |
| [`integration.gasket_temperature_compression_joint_history`](modules/api/integration.gasket_temperature_compression_joint_history.md) | Every load step uses the same caller bolt preloads/stiffnesses and sector data with its exact temperature-specific interpolated gasket curve. |
| [`integration.gasket_thermoelastic_expansion_joint_history`](modules/api/integration.gasket_thermoelastic_expansion_joint_history.md) | Each component's free thermal change is its reference dimension times expm1 of the exact piecewise-linear integral of instantaneous alpha(T), interpreted as logarithmic strain. |
| [`integration.lh2dt_dynamic_network_node_state_history`](modules/api/integration.lh2dt_dynamic_network_node_state_history.md) | The upstream result revision, run result, and configuration digests are caller-pinned. |
| [`integration.multi_bolt_joint_to_flange_contact_request`](modules/api/integration.multi_bolt_joint_to_flange_contact_request.md) | Bolt force comes from a digest-pinned computed multi-bolt equilibrium AssessmentResult at one exact named knot. |
| [`integration.multiaxial_cycle_block_result_summary`](modules/api/integration.multiaxial_cycle_block_result_summary.md) | The stateful damage result, bound request and exchange receipt must have exact matching digests and ordered block lineage. |
| [`integration.spatial_piecewise_mass_action`](modules/api/integration.spatial_piecewise_mass_action.md) | Rates, reaction directions, concentration/activity approximation and local-use rights are caller-supplied. |
| [`integration.tube_bundle_lame_stress_history`](modules/api/integration.tube_bundle_lame_stress_history.md) | Each tube is modeled as a homogeneous isotropic linear-elastic annular cylinder using the caller's current inner diameter and minimum wall. |
| [`integration.wco2_species_transfer_audit`](modules/api/integration.wco2_species_transfer_audit.md) | Species formulas, formal charges, transfer coefficients and Evidence are caller supplied. |
| [`integration.wet_co2_carbonate_alkalinity_speciation`](modules/api/integration.wet_co2_carbonate_alkalinity_speciation.md) | Only CO2star, bicarbonate, carbonate, hydrogen and hydroxide contribute to the alkalinity balance. |
| [`integration.wet_co2_carbonate_transport_boundary_history`](modules/api/integration.wet_co2_carbonate_transport_boundary_history.md) | The input must be a complete computed fixed-fugacity carbonate history or digest-bound Henry-carbonate adapter history. |
| [`integration.wet_co2_condensate_film_history`](modules/api/integration.wet_co2_condensate_film_history.md) | The caller flux is the net retained water source per actual fixed wall-patch area, including condensation, evaporation, drainage and retention effects. |
| [`integration.wet_co2_condensate_state`](modules/api/integration.wet_co2_condensate_state.md) | Water fugacity and wall equilibrium fugacity are provider-supplied on one compatible fugacity/standard-state basis. |
| [`integration.wet_co2_cylindrical_aqueous_scale_sink_feedback`](modules/api/integration.wet_co2_cylindrical_aqueous_scale_sink_feedback.md) | Caller owns phase identity, stoichiometry, intrinsic phase flux law, and geometry inputs. |
| [`integration.wet_co2_cylindrical_bv_wall_recession`](modules/api/integration.wet_co2_cylindrical_bv_wall_recession.md) | Integrated reaction extents and explicit aqueous elemental stoichiometry determine the alloy-element release per unit axial length. |
| [`integration.wet_co2_cylindrical_coupled_scale_geometry_replay`](modules/api/integration.wet_co2_cylindrical_coupled_scale_geometry_replay.md) | The caller supplies all state, thermodynamic, kinetics, stoichiometry, transport and diffusivity records. |
| [`integration.wet_co2_cylindrical_diffusion_limited_scale_growth`](modules/api/integration.wet_co2_cylindrical_diffusion_limited_scale_growth.md) | The precipitation rate is limited by the least available reactant flux among caller-declared solid reactants. |
| [`integration.wet_co2_cylindrical_finite_gas_stage_geometry_feedback`](modules/api/integration.wet_co2_cylindrical_finite_gas_stage_geometry_feedback.md) | Caller transfer, mass-action, BV and scale laws remain fixed/evidence-bound. |
| [`integration.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback`](modules/api/integration.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback.md) | Caller supplies a complete finite aqueous mass-action network, activity and equilibrium provider lineage, reaction formulae, natural-log Ksp and kinetic parameters with bound Evidence. |
| [`integration.wet_co2_cylindrical_finite_liquid_transfer_inventory`](modules/api/integration.wet_co2_cylindrical_finite_liquid_transfer_inventory.md) | The transfer exposure result supplies a whole-segment conductance on the cylindrical wetted-area basis. |
| [`integration.wet_co2_cylindrical_geometry_coupled_history`](modules/api/integration.wet_co2_cylindrical_geometry_coupled_history.md) | Each outer iteration reruns the transient cylindrical finite-volume species balance and common BV mixed potential on a candidate exact-knot geometry path. |
| [`integration.wet_co2_cylindrical_geometry_fixed_point_controller`](modules/api/integration.wet_co2_cylindrical_geometry_fixed_point_controller.md) | A caller-owned runtime solver or bundled spatial-BV adapter must recompute declared physics for each supplied exact-knot radius path. |
| [`integration.wet_co2_cylindrical_hydraulics_to_scale_removal`](modules/api/integration.wet_co2_cylindrical_hydraulics_to_scale_removal.md) | The hydraulic and shear-removal contracts share exact scope, geometry result digest and time knots. |
| [`integration.wet_co2_cylindrical_liquid_transfer_capacity_history`](modules/api/integration.wet_co2_cylindrical_liquid_transfer_capacity_history.md) | The existing pointwise liquid-side mass-transfer correlation is evaluated at each exact cylindrical hydraulics knot. |
| [`integration.wet_co2_cylindrical_multilayer_transport_resistance`](modules/api/integration.wet_co2_cylindrical_multilayer_transport_resistance.md) | Piecewise constant caller diffusivities are combined as exact logarithmic cylindrical resistances in series. |
| [`integration.wet_co2_cylindrical_scale_kinetics_to_geometry`](modules/api/integration.wet_co2_cylindrical_scale_kinetics_to_geometry.md) | Caller phase thickness histories and wall recession are exact-knot aligned and independently reviewed. |
| [`integration.wet_co2_cylindrical_scale_recession_feedback`](modules/api/integration.wet_co2_cylindrical_scale_recession_feedback.md) | Every outer iteration recalculates spatial BV transport, phase saturation and wall kinetics, multilayer cylindrical diffusion supply, phase inventory and common wall geometry. |
| [`integration.wet_co2_cylindrical_shear_limited_scale_removal`](modules/api/integration.wet_co2_cylindrical_shear_limited_scale_removal.md) | Scale removal begins above a caller-declared critical wall shear stress and follows a caller-calibrated power law. |
| [`integration.wet_co2_cylindrical_spatial_mixed_potential`](modules/api/integration.wet_co2_cylindrical_spatial_mixed_potential.md) | Exact geometry knots with left-held interval inputs. |
| [`integration.wet_co2_cylindrical_stage_kinetic_scale_feedback`](modules/api/integration.wet_co2_cylindrical_stage_kinetic_scale_feedback.md) | Caller supplies activity coefficients, dimensionless activity reference concentrations, natural-log solubility products, reaction formulae, and kinetic parameters with bound Evidence. |
| [`integration.wet_co2_cylindrical_stage_speciation_scale_feedback`](modules/api/integration.wet_co2_cylindrical_stage_speciation_scale_feedback.md) | Caller supplies a complete finite aqueous mass-action network, activity and equilibrium provider lineage, reaction formulae, natural-log Ksp and kinetic parameters with bound Evidence. |
| [`integration.wet_co2_cylindrical_steady_hydraulics`](modules/api/integration.wet_co2_cylindrical_steady_hydraulics.md) | The circular bore is represented by the exact area and wetted perimeter of the supplied geometry history. |
| [`integration.wet_co2_cylindrical_transient_transport`](modules/api/integration.wet_co2_cylindrical_transient_transport.md) | Each time interval uses its left-knot boundary, transport and reaction records; geometric remapping uses annular overlap and explicit caller concentrations for added material. |
| [`integration.wet_co2_cylindrical_transport_mixed_potential`](modules/api/integration.wet_co2_cylindrical_transport_mixed_potential.md) | Geometry and electrochemical boundary are paired at exactly equal caller time knots; no interpolation is performed. |
| [`integration.wet_co2_cylindrical_wall_saturation_scale_kinetics`](modules/api/integration.wet_co2_cylindrical_wall_saturation_scale_kinetics.md) | Exact wall-adjacent cylindrical transport concentrations are paired with caller activity coefficients and a caller-supplied log10 Ksp at the same time and temperature knots. |
| [`integration.wet_co2_elemental_phase_handoff`](modules/api/integration.wet_co2_elemental_phase_handoff.md) | Only an already-computed source result payload with matching digest and exact species/phase formula mappings is consumed. |
| [`integration.wet_co2_film_transport_limited_mixed_potential`](modules/api/integration.wet_co2_film_transport_limited_mixed_potential.md) | A digest-pinned caller carbonate boundary and caller-reviewed reactant film records define the finite dissolved-species support. |
| [`integration.wet_co2_finite_gas_liquid_exchange_history`](modules/api/integration.wet_co2_finite_gas_liquid_exchange_history.md) | Each interval has fixed area, liquid volume, Henry coefficient, gas inventory capacity and two-film transfer coefficients. |
| [`integration.wet_co2_finite_gas_multispecies_wall_flux_history`](modules/api/integration.wet_co2_finite_gas_multispecies_wall_flux_history.md) | The interval species-flux schedule, transfer coefficient, Henry coefficient, inflow, area and initial inventories are caller owned. |
| [`integration.wet_co2_finite_gas_variable_liquid_history`](modules/api/integration.wet_co2_finite_gas_variable_liquid_history.md) | Per-area gas inventory capacity, patch area, volume flux, Henry coefficient and film coefficients are caller-reviewed. |
| [`integration.wet_co2_finite_gas_wall_reaction_inventory_history`](modules/api/integration.wet_co2_finite_gas_wall_reaction_inventory_history.md) | Finite gas inventory, Henry coefficient, film coefficients, volume flux, incoming dissolved CO2*, initial state and solver tolerances are caller-owned and Evidence-linked. |
| [`integration.wet_co2_finite_gas_water_condensation_history`](modules/api/integration.wet_co2_finite_gas_water_condensation_history.md) | Water vapor component pressure follows the ideal-gas relation from finite vapor moles at the supplied interval temperature and gas volume. |
| [`integration.wet_co2_finite_inventory_electrode_mixed_potential`](modules/api/integration.wet_co2_finite_inventory_electrode_mixed_potential.md) | The caller defines a common calibrated electrode potential interval at every exact geometry interval. |
| [`integration.wet_co2_finite_inventory_saturation_scale_geometry`](modules/api/integration.wet_co2_finite_inventory_saturation_scale_geometry.md) | Wall activities use molarity standard state, caller activity coefficients and a caller log10 Ksp at each exact time knot. |
| [`integration.wet_co2_finite_liquid_transfer_history`](modules/api/integration.wet_co2_finite_liquid_transfer_history.md) | Gas fugacity, Henry convention, interface area, liquid volume and two-film coefficients are constant within each exact interval and may change only at supplied interval boundaries. |
| [`integration.wet_co2_gas_film_condensation_transfer_history`](modules/api/integration.wet_co2_gas_film_condensation_transfer_history.md) | Gas-film molar flux follows a caller-supplied linear fugacity driving-force law on each interval. |
| [`integration.wet_co2_lumped_wall_thermal_condensation_history`](modules/api/integration.wet_co2_lumped_wall_thermal_condensation_history.md) | A single wall temperature is governed by a lumped areal heat capacity and caller heat boundary terms. |
| [`integration.wet_co2_parallel_zone_transfer`](modules/api/integration.wet_co2_parallel_zone_transfer.md) | Each caller-declared interface zone has one representative gas and liquid state and local two-film coefficients. |
| [`integration.wet_co2_reactive_film_transfer`](modules/api/integration.wet_co2_reactive_film_transfer.md) | One-dimensional steady stagnant liquid-film diffusion with constant diffusivity and a caller-supplied irreversible first-order sink in CO2star. |
| [`integration.wet_co2_scale_corrosion_moving_geometry_history`](modules/api/integration.wet_co2_scale_corrosion_moving_geometry_history.md) | Scale molar volume, metal conversion, product yield and external scale formation/dissolution schedules are caller provided and evidence linked. |
| [`integration.wet_co2_scale_corrosion_simultaneous_history`](modules/api/integration.wet_co2_scale_corrosion_simultaneous_history.md) | Scale thickness is a continuous ODE state and updates the nested film-transport cap at each electrochemical solver call. |
| [`integration.wet_co2_scale_diffusion_electrode_mixed_potential`](modules/api/integration.wet_co2_scale_diffusion_electrode_mixed_potential.md) | At each caller time knot, a one-dimensional steady finite-volume reactant balance inside a fixed scale is solved simultaneously with one common mixed potential. |
| [`integration.wet_co2_simulation_wall_loss_envelope`](modules/api/integration.wet_co2_simulation_wall_loss_envelope.md) | Each provider simulation scenario is bound to exactly one CC BY source row, row digest and archive evidence digest. |
| [`integration.wet_co2_transient_gas_carbonate_alkalinity_equilibrium`](modules/api/integration.wet_co2_transient_gas_carbonate_alkalinity_equilibrium.md) | Only the ideal carbonate-only system is equilibrated using caller conditional K1, K2 and Kw values with explicit pH support. |
| [`integration.wet_co2_variable_condensate_transfer_history`](modules/api/integration.wet_co2_variable_condensate_transfer_history.md) | Liquid volume per area changes linearly at caller-provided constant interval flux; volume flux cannot drive negative inventory. |

## kinetics: 반응속도·온도 이동

| API | 목적 |
|---|---|
| [`kinetics.arrhenius`](modules/api/kinetics.arrhenius.md) | Single thermally activated mechanism; parameters and applicable temperature range are user supplied. |

## maintenance: 유지관리·이력·사용자 지표

| API | 목적 |
|---|---|
| [`maintenance.declared_equipment_effectiveness`](modules/api/maintenance.declared_equipment_effectiveness.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`maintenance.declared_pareto_summary`](modules/api/maintenance.declared_pareto_summary.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |

## materials: 재료 구성식·조성·시험 해석

| API | 목적 |
|---|---|
| [`materials.allowable_property_provider`](modules/api/materials.allowable_property_provider.md) | Property identity, edition, applicability and provider lineage are exact caller declarations. |
| [`materials.bonded_layer_integrity`](modules/api/materials.bonded_layer_integrity.md) | Substrate, layer, lots, interface, geometry, process history, samples and observations remain caller evidence. |
| [`materials.bonded_layer_integrity_assessment`](modules/api/materials.bonded_layer_integrity_assessment.md) | Substrate, layer, interface, lot and process identities are caller-reviewed and preserved. |
| [`materials.brittle_applicability_evidence`](modules/api/materials.brittle_applicability_evidence.md) | Material, product form, condition, thickness, orientation and service descriptors are reviewed caller identities. |
| [`materials.casting_forging_quality`](modules/api/materials.casting_forging_quality.md) | Product, heat, route, process, heat treatment, sampling and observation evidence remains caller supplied. |
| [`materials.casting_forging_quality_record`](modules/api/materials.casting_forging_quality_record.md) | Component, heat, manufacturing route, heat treatment, inspection coverage, observations and caller limits retain separate identities and evidence. |
| [`materials.certificate_reconciliation`](modules/api/materials.certificate_reconciliation.md) | Certificate campaign coverage composed over lower-level reconciliation with exact reviewed target product and traceability binding. |
| [`materials.chemistry_reconciliation`](modules/api/materials.chemistry_reconciliation.md) | Exact supplied identity and interval-valued certificate/verification chemistry with an explicit comparison policy. |
| [`materials.component_material_class_assessment`](modules/api/materials.component_material_class_assessment.md) | Caller profile authority, physical scope, service and component role mapping are explicit; exact labels only. |
| [`materials.composite_compatibility_assessment`](modules/api/materials.composite_compatibility_assessment.md) | Laminate, resin, fiber, manufacturing, layup and environment identities must match exactly. |
| [`materials.composition_index_recipe`](modules/api/materials.composition_index_recipe.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`materials.composition_temperature_correlation`](modules/api/materials.composition_temperature_correlation.md) | Caller composition support, coefficients, temperature units, material condition and calibration population are explicit. |
| [`materials.cyclic_ramberg_osgood_fit`](modules/api/materials.cyclic_ramberg_osgood_fit.md) | Weighted log-space fit of stabilized cyclic stress amplitude against positive plastic strain amplitude. |
| [`materials.declared_analysis_tolerance_recipe`](modules/api/materials.declared_analysis_tolerance_recipe.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`materials.declared_chemical_analysis_comparison`](modules/api/materials.declared_chemical_analysis_comparison.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`materials.declared_classification_assignment`](modules/api/materials.declared_classification_assignment.md) | Caller classification records bind material designation, edition, product, condition, process, subject and qualification purpose. |
| [`materials.ductility_retention`](modules/api/materials.ductility_retention.md) | Matched test conditions and declared reference specimen; not a structural failure probability. |
| [`materials.floored_composition_index_recipe`](modules/api/materials.floored_composition_index_recipe.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`materials.impact_transition`](modules/api/materials.impact_transition.md) | One declared impact-test series with bounded logistic shelves, explicit robust-loss choice and observed-domain crossing. |
| [`materials.monotonic_hollomon_calibration`](modules/api/materials.monotonic_hollomon_calibration.md) | Weighted log-space Hollomon fit to caller-reviewed monotonic pre-necking stress and elastic-subtracted plastic strain. |
| [`materials.multi_record_certificate_reconciliation`](modules/api/materials.multi_record_certificate_reconciliation.md) | One exact heat, lot and reviewed material-condition identity applies to every record. |
| [`materials.offset_yield`](modules/api/materials.offset_yield.md) | Caller supplies extensometer strain, corrected monotonic stress data, elastic modulus and offset. |
| [`materials.phase_fraction_linear_contrast`](modules/api/materials.phase_fraction_linear_contrast.md) | One sample, region and measurement method are assessed at a time. |
| [`materials.phase_microstructure_assessment`](modules/api/materials.phase_microstructure_assessment.md) | Every phase fraction and expanded uncertainty is a reviewed measurement on an explicit sample and region. |
| [`materials.pitting_composition_index`](modules/api/materials.pitting_composition_index.md) | User-declared composition coefficients; index is not a corrosion rate or material acceptance rule. |
| [`materials.polymer_arrhenius_shift_calibration`](modules/api/materials.polymer_arrhenius_shift_calibration.md) | Weighted calibration is restricted to one polymer formulation, physical state and endpoint definition. |
| [`materials.polymer_compatibility_envelope_match`](modules/api/materials.polymer_compatibility_envelope_match.md) | Material, media, unit and loading identifiers are compared exactly without aliases or hidden conversions. |
| [`materials.ramberg_osgood`](modules/api/materials.ramberg_osgood.md) | Stabilized uniaxial cyclic amplitude relation with caller-calibrated K-prime and n-prime. |
| [`materials.resin_hdt_headroom`](modules/api/materials.resin_hdt_headroom.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`materials.scaled_strength_minimum`](modules/api/materials.scaled_strength_minimum.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`materials.specification_aliases`](modules/api/materials.specification_aliases.md) | The existing exact resolver compares namespace, designation, edition, form and condition without normalization. |
| [`materials.steel_composition_index`](modules/api/materials.steel_composition_index.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`materials.strain_life_coefficient_calibration`](modules/api/materials.strain_life_coefficient_calibration.md) | Two-stage weighted log-linear CMB calibration requires separated elastic and plastic strain amplitudes. |
| [`materials.temperature_trend_strength_scaling`](modules/api/materials.temperature_trend_strength_scaling.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`materials.tensile_point`](modules/api/materials.tensile_point.md) | Gauge extension and original section are supplied; uniform-volume conversion excludes necking. |

## mechanics: 압력응력·열응력·접촉·탄성

| API | 목적 |
|---|---|
| [`mechanics.gasket_nominal_contact_pressure`](modules/api/mechanics.gasket_nominal_contact_pressure.md) | The compressive force and effective contact area refer to the same reviewed physical load state and scope. |
| [`mechanics.lame_cylinder`](modules/api/mechanics.lame_cylinder.md) | Long homogeneous isotropic linear-elastic cylinder; end effects and instability excluded. |
| [`mechanics.plane_stress`](modules/api/mechanics.plane_stress.md) | Two-dimensional Cauchy stress with zero out-of-plane normal/shear components. |
| [`mechanics.thermal_restraint`](modules/api/mechanics.thermal_restraint.md) | Uniform temperature change, uniaxial linear elasticity and constant properties. |
| [`mechanics.thin_cylinder`](modules/api/mechanics.thin_cylinder.md) | Closed-end membrane approximation, t/r <= 0.1; user allowable is not an inferred code value. |
| [`mechanics.through_wall_thermal_stress`](modules/api/mechanics.through_wall_thermal_stress.md) | Linear-elastic plane-section thermal stress under explicit resultants or explicit membrane strain and curvature. |

## piping: 배관 조건·사용자 기준

| API | 목적 |
|---|---|
| [`piping.displacement_stress_allowance`](modules/api/piping.displacement_stress_allowance.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |

## protection: protection

| API | 목적 |
|---|---|
| [`protection.cathodic_budget`](modules/api/protection.cathodic_budget.md) | Declared piecewise-linear coating/current histories, charge capacity and an independent current-output bound. |
| [`protection.coating_coverage`](modules/api/protection.coating_coverage.md) | Uniform deposited film; solids fraction and transfer losses are declared. |

## reliability: 신뢰도·위험도 계산

| API | 목적 |
|---|---|
| [`reliability.bayesian_linear_thickness_update`](modules/api/reliability.bayesian_linear_thickness_update.md) | Caller-reviewed Gaussian prior and thickness measurement-error model for one physical location under a constant linear thickness-loss relation. |
| [`reliability.binary_event_pair_calibration`](modules/api/reliability.binary_event_pair_calibration.md) | Calibration and holdout physical sequences, source groups and independence groups are disjoint. |
| [`reliability.continuous_time_markov_chain`](modules/api/reliability.continuous_time_markov_chain.md) | Caller-reviewed finite-state time-homogeneous continuous-time Markov generator over one physical scope and interval. |
| [`reliability.ctmc_generator_calibration`](modules/api/reliability.ctmc_generator_calibration.md) | State/transition definitions and exposure units are exact caller-reviewed identities. |
| [`reliability.exclusive_paths`](modules/api/reliability.exclusive_paths.md) | Mutually exclusive and complete conditional paths allocate initiation exactly once. |
| [`reliability.fault_tree_minimal_cut_sets`](modules/api/reliability.fault_tree_minimal_cut_sets.md) | Caller-declared minimal cut sets; AND within each cut, OR across cuts; exact inclusion-exclusion under reviewed independent basic events. |
| [`reliability.gamma_poisson`](modules/api/reliability.gamma_poisson.md) | Stationary Poisson event counts with Gamma(shape, exposure) prior and complete ascertainment. |
| [`reliability.gaussian_mean_shift_importance_sampling`](modules/api/reliability.gaussian_mean_shift_importance_sampling.md) | Caller-reviewed samples are drawn from an independent unit-normal mean-shift proposal in a named latent space and evaluated by one deterministic finite-period event indicator. |
| [`reliability.gaussian_thickness_posterior_sample_design`](modules/api/reliability.gaussian_thickness_posterior_sample_design.md) | Caller-reviewed two-dimensional Gaussian posterior for reference-time thickness and signed constant loss rate at one physical location. |
| [`reliability.independent_gate`](modules/api/reliability.independent_gate.md) | Input events share a horizon and conditioning; statistical independence must be explicitly declared. |
| [`reliability.joint_event_probability`](modules/api/reliability.joint_event_probability.md) | Caller-reviewed exhaustive joint distribution over binary events sharing one physical scope, horizon and conditioning basis. |
| [`reliability.linear_thickness_state_space_update`](modules/api/reliability.linear_thickness_state_space_update.md) | Caller-reviewed two-state linear thickness/loss-rate transition with additive covariance rate and independent sequential thickness-measurement errors. |
| [`reliability.piecewise_continuous_time_markov_chain`](modules/api/reliability.piecewise_continuous_time_markov_chain.md) | Caller-reviewed finite-state piecewise-constant continuous-time Markov generators over contiguous chronological segments. |
| [`reliability.sampled_linear_thickness_first_passage`](modules/api/reliability.sampled_linear_thickness_first_passage.md) | Caller-reviewed joint weighted samples describe remaining thickness and a nonnegative constant loss rate at one physical location, conditional on no threshold crossing by assessment time. |
| [`reliability.sobol_replicate_stability`](modules/api/reliability.sobol_replicate_stability.md) | All replicates share exact output, parameter, distribution, dependence, design and evaluator identities. |
| [`reliability.weibull_interval`](modules/api/reliability.weibull_interval.md) | Conditional on survival to current age and a fixed Weibull lifetime model; repair/replacement excluded. |

## structural: 두께·압력 용량·FAD·구조 평가

| API | 목적 |
|---|---|
| [`structural.burst_pressure_comparison`](modules/api/structural.burst_pressure_comparison.md) | Partition-aware descriptive comparison of caller-supplied pressure predictions with qualified burst tests; no pressure equation, acceptance limit or standard table is bundled. |
| [`structural.caller_fad_envelope`](modules/api/structural.caller_fad_envelope.md) | Compare identified provider FAD coordinates only against a reviewed caller curve with matching material/geometry/load basis. |
| [`structural.component_pressure_reference`](modules/api/structural.component_pressure_reference.md) | Static connected fluid, uniform caller density and gravity; upward-positive elevations in a reviewed common frame. |
| [`structural.creep_fatigue_campaign`](modules/api/structural.creep_fatigue_campaign.md) | Compose same-history creep rupture-time fractions, fatigue cycle fractions and a caller-owned interaction envelope without substituting secondary strain for damage. |
| [`structural.creep_fatigue_interaction_provider_evidence`](modules/api/structural.creep_fatigue_interaction_provider_evidence.md) | Material, interaction basis and separate creep/fatigue quantity definitions match exactly. |
| [`structural.declared_pressure_thickness_relation`](modules/api/structural.declared_pressure_thickness_relation.md) | Caller supplies reviewed dimension conventions, signed thickness coefficient, numerator factor, allowable stress, joint efficiency and pressure/thickness support. |
| [`structural.declared_shell_characteristic_lengths`](modules/api/structural.declared_shell_characteristic_lengths.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`structural.external_pressure`](modules/api/structural.external_pressure.md) | Existing provider assessments retain exact geometry, material, imperfection, boundary, load, mesh, model, pressure and digest identities. |
| [`structural.external_pressure_provider_evidence`](modules/api/structural.external_pressure_provider_evidence.md) | Shell, material condition, boundary, load case and pressure basis match exactly. |
| [`structural.failure_assessment_history`](modules/api/structural.failure_assessment_history.md) | All physical input histories and the finite nonincreasing FAD boundary are caller-owned, reviewed and digest-bound. |
| [`structural.failure_assessment_points`](modules/api/structural.failure_assessment_points.md) | Deterministic assessment points against a caller-licensed, nonincreasing piecewise-linear FAD boundary; all physical solutions and applicability remain external evidence. |
| [`structural.finite_element_result_exchange`](modules/api/structural.finite_element_result_exchange.md) | Mesh and result identities, coordinate frame, ordering, quantity definitions and content digests are caller-reviewed metadata. |
| [`structural.mean_shear_stress`](modules/api/structural.mean_shear_stress.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`structural.nozzle_local_stress_provider_evidence`](modules/api/structural.nozzle_local_stress_provider_evidence.md) | Geometry, load component and stress metric units are exact caller/provider tokens. |
| [`structural.pitting_ffs_provider_evidence`](modules/api/structural.pitting_ffs_provider_evidence.md) | Component, material, coordinate frame, pressure and load bases are caller-reviewed exact identities. |
| [`structural.planar_stress_linearization`](modules/api/structural.planar_stress_linearization.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`structural.pressure_temperature_envelope`](modules/api/structural.pressure_temperature_envelope.md) | Caller-reviewed positive pressure limit at strictly increasing absolute-temperature knots; piecewise-linear interpolation is restricted to supplied support. |
| [`structural.pressure_temperature_ramp_limits`](modules/api/structural.pressure_temperature_ramp_limits.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`structural.profile_capacity`](modules/api/structural.profile_capacity.md) | Nodal axial blunt-loss area scan with exact caller-matched reference pressure and bounded nondecreasing bulging table; no automatic engineering qualification. |
| [`structural.profile_capacity_corrosion_scenario`](modules/api/structural.profile_capacity_corrosion_scenario.md) | The supplied axial remaining-thickness profile is re-evaluated after a caller-declared spatially uniform constant loss rate over a fixed horizon. |
| [`structural.profile_capacity_rate_field_scenario`](modules/api/structural.profile_capacity_rate_field_scenario.md) | A caller-provided axial-by-time rate field is integrated nodewise and passed to the same reviewed profile-capacity provider. |
| [`structural.thermal_gradient_discretization_convergence`](modules/api/structural.thermal_gradient_discretization_convergence.md) | All refinement levels share exact geometry, boundary, property, provider and common-query identity. |
| [`structural.thermal_gradient_observation_comparison`](modules/api/structural.thermal_gradient_observation_comparison.md) | Measured and predicted histories are paired by reviewed clock and sensor identities. |
| [`structural.thermal_gradient_parameter_calibration`](modules/api/structural.thermal_gradient_parameter_calibration.md) | Caller-reviewed transient measurements align to supplied baseline and sensitivity responses. |

## testing: 재료시험·통계·시험 지표

| API | 목적 |
|---|---|
| [`testing.brinell`](modules/api/testing.brinell.md) | Spherical indentation geometry; force and dimensions are SI inputs. |
| [`testing.grain_planimetry_summary`](modules/api/testing.grain_planimetry_summary.md) | Caller-reviewed specimen-plane areas, effective boundary counts and logarithmic number calibration are explicit. |
| [`testing.knoop`](modules/api/testing.knoop.md) | Ideal rhombic projected area from explicitly declared indenter edge angles and measured long diagonal. |
| [`testing.mating_brinell_hardness_difference`](modules/api/testing.mating_brinell_hardness_difference.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`testing.phase_point_count_summary`](modules/api/testing.phase_point_count_summary.md) | Caller phase labels and immutable image/grid records; same physical specimen and reviewed nonoverlap. |
| [`testing.rockwell_depth`](modules/api/testing.rockwell_depth.md) | Caller-defined scale constants and common preliminary-force depth reference; no automatic scale selection. |
| [`testing.vickers`](modules/api/testing.vickers.md) | Opposite-face diamond angle is 136 degrees; both measured diagonals are explicit. |

## thermal: 열전도·열이력·열처리

| API | 목적 |
|---|---|
| [`thermal.cylindrical_layers`](modules/api/thermal.cylindrical_layers.md) | Concentric cylindrical layers with two convection boundaries and optional outer radiation. |
| [`thermal.fire_flux_response`](modules/api/thermal.fire_flux_response.md) | Reviewed net absorbed boundary flux composed with explicit multilayer transient conduction; no fire curve, ablation or intumescence law inferred. |
| [`thermal.insulation_surface_balance`](modules/api/thermal.insulation_surface_balance.md) | Steady single-layer radial conduction with caller constant convection and gray radiation boundaries. |
| [`thermal.lumped_temperature`](modules/api/thermal.lumped_temperature.md) | Lumped thermal capacitance; caller specifies the maximum applicable Biot number. |
| [`thermal.piecewise_thickness_soak_duration`](modules/api/thermal.piecewise_thickness_soak_duration.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`thermal.planar_layers`](modules/api/thermal.planar_layers.md) | Steady planar one-dimensional conduction with constant per-layer conductivity. |
| [`thermal.thickness_scaled_rate_limit`](modules/api/thermal.thickness_scaled_rate_limit.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`thermal.thickness_soak_duration`](modules/api/thermal.thickness_soak_duration.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`thermal.transient_conduction_1d`](modules/api/thermal.transient_conduction_1d.md) | One-dimensional planar or radial conduction with caller-supplied property curves, boundaries, distributed convection/gray radiation and heat generation. |

## thermo: 열역학 상태·퓨가시티

| API | 목적 |
|---|---|
| [`thermo.co2_fugacity_coolprop`](modules/api/thermo.co2_fugacity_coolprop.md) | CoolProp pure-component CO2 EOS is evaluated at caller-supplied absolute CO2 partial pressure. |
| [`thermo.co2_mixture_fugacity_coolprop`](modules/api/thermo.co2_mixture_fugacity_coolprop.md) | CoolProp's caller-configured mixture EOS evaluates the CO2 component fugacity at total pressure and normalized gas mole fractions. |
| [`thermo.co2_mixture_fugacity_history`](modules/api/thermo.co2_mixture_fugacity_history.md) | Evaluate ordered caller-specified gas-mixture CO2 component fugacity at exact PT time knots with CoolProp. |
| [`thermo.co2_pure_fugacity_history`](modules/api/thermo.co2_pure_fugacity_history.md) | Evaluate ordered caller-supplied pure-CO2 PT requests with the selected optional CoolProp backend at exact time points. |
| [`thermo.coolprop_pure_water_saturated_vapor_fugacity`](modules/api/thermo.coolprop_pure_water_saturated_vapor_fugacity.md) | Pure-water saturated vapor is evaluated at the caller wall temperature using the requested CoolProp backend. |
| [`thermo.coolprop_pure_water_single_phase_state`](modules/api/thermo.coolprop_pure_water_single_phase_state.md) | Pure water is evaluated at the caller absolute-pressure/temperature state with the selected CoolProp backend. |

## transport: 확산·이온·성분 수송

| API | 목적 |
|---|---|
| [`transport.crevice_activity_corrected_nernst_planck_1d`](modules/api/transport.crevice_activity_corrected_nernst_planck_1d.md) | Fixed-geometry finite-volume transport on caller time knots; diffusivity is constant over the supplied run. |
| [`transport.crevice_activity_corrected_reactive_nernst_planck_1d`](modules/api/transport.crevice_activity_corrected_reactive_nernst_planck_1d.md) | Caller activity-coefficient cell/time fields drive both the activity-gradient flux term and reversible local mass-action rates. |
| [`transport.crevice_component_diffusion_1d`](modules/api/transport.crevice_component_diffusion_1d.md) | A caller-defined scalar component diffuses along a constant-cross-section one-dimensional crevice with fixed mouth concentration and a closed tip. |
| [`transport.crevice_electroneutral_multispecies_diffusion_1d`](modules/api/transport.crevice_electroneutral_multispecies_diffusion_1d.md) | Fixed-geometry one-dimensional finite-volume transport of a caller-defined dilute ionic species set with constant diffusivities. |
| [`transport.crevice_spatial_activity_solid_nernst_planck_1d`](modules/api/transport.crevice_spatial_activity_solid_nernst_planck_1d.md) | Each interval uses the existing conservative variable-volume finite-volume Nernst-Planck BDF solver, including caller face areas, velocity, ionic diffusivity, zero-current closure and blind-tip no-flux boundary. |
| [`transport.crevice_variable_area_activity_corrected_reactive_nernst_planck_1d`](modules/api/transport.crevice_variable_area_activity_corrected_reactive_nernst_planck_1d.md) | Concentration state is advanced through the conservative cell-mole balance using linearly interpolated caller cell volumes and face areas. |
| [`transport.hydrogen_detector_observation`](modules/api/transport.hydrogen_detector_observation.md) | Instantaneous reviewed Faraday or sample-mass observation identity for a signed hydrogen-atom release history; detector dynamics and transport inversion are excluded. |
| [`transport.hydrogen_dissociative_surface_rates`](modules/api/transport.hydrogen_dissociative_surface_rates.md) | Reviewed hydrogen fugacity, or explicitly reviewed ideal-gas partial-pressure approximation, and two effective Arrhenius surface-capacity laws over declared temperature and gas-driver support. |
| [`transport.hydrogen_finite_cylinder_kinetic`](modules/api/transport.hydrogen_finite_cylinder_kinetic.md) | Finite axisymmetric radial-axial Fickian transport with separately declared curved/end boundaries, fixed independent dilute traps, reviewed detailed-balance or independent-frequency kinetics and spatially uniform temperature. |
| [`transport.hydrogen_slab_flow_multiplier_fit`](modules/api/transport.hydrogen_slab_flow_multiplier_fit.md) | One reviewed positive history multiplier, calibrated against signed outward planar hydrogen-atom flow with a predeclared calibration/holdout partition and all other transport inputs fixed. |
| [`transport.hydrogen_slab_kinetic`](modules/api/transport.hydrogen_slab_kinetic.md) | Planar Fickian lattice transport with fixed independent dilute trap populations, reviewed detailed-balance or independent-frequency kinetics, spatially uniform temperature and declared surface boundaries. |
| [`transport.hydrogen_thermal_rate_fit`](modules/api/transport.hydrogen_thermal_rate_fit.md) | Weighted log-linear calibration of one reviewed effective Arrhenius or fixed-transmission transition-state frequency law with preserved calibration/holdout identities. |
| [`transport.hydrogen_trap_equilibrium`](modules/api/transport.hydrogen_trap_equilibrium.md) | Fast local equilibrium of fixed, independent single-occupancy trap populations in one uniform-temperature material condition. |
| [`transport.hydrogen_trap_thermal_rates`](modules/api/transport.hydrogen_trap_thermal_rates.md) | Reviewed single-path Arrhenius or transition-state frequency parameters, one common energy reference, a supported absolute-temperature interval and an aligned elapsed-time history. |
| [`transport.semi_infinite_diffusion`](modules/api/transport.semi_infinite_diffusion.md) | One-dimensional semi-infinite Fickian diffusion with a constant boundary concentration. |

## validation: 증거 정렬·비교·검증 지표

| API | 목적 |
|---|---|
| [`validation.crevice_repassivation_excursion_duration_history`](modules/api/validation.crevice_repassivation_excursion_duration_history.md) | Each reported duration covers only an interval bounded by two measured exact knots; no within-interval crossing time is inferred. |
| [`validation.crevice_repassivation_margin_history`](modules/api/validation.crevice_repassivation_margin_history.md) | Threshold and operating potentials refer to the same exact material, test condition, electrolyte record, temperature, reference electrode and sign convention. |
| [`validation.crevice_wall_sink_source_group_stability`](modules/api/validation.crevice_wall_sink_source_group_stability.md) | Only observations predeclared as calibration rows are partitioned; the original independent holdout is never included in any fold. |

## welding: 용접 열·수소·야금·절차

| API | 목적 |
|---|---|
| [`welding.arc_energy`](modules/api/welding.arc_energy.md) | Constant arc voltage/current; thermal efficiency is explicit and procedure-specific. |
| [`welding.brazing_bonding_production_campaign_evidence`](modules/api/welding.brazing_bonding_production_campaign_evidence.md) | Caller-owned campaign criteria only; no qualification claim. |
| [`welding.brazing_bonding_qualification`](modules/api/welding.brazing_bonding_qualification.md) | Member ordering, material and surface-condition identities are preserved and compared exactly. |
| [`welding.carbon_equivalent_recipe`](modules/api/welding.carbon_equivalent_recipe.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`welding.carbon_equivalents`](modules/api/welding.carbon_equivalents.md) | All elements are mass percent; indices do not prescribe preheat or demonstrate weldability. |
| [`welding.conductivity_preheat_correlation`](modules/api/welding.conductivity_preheat_correlation.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`welding.consumable_compatibility`](modules/api/welding.consumable_compatibility.md) | Base-material pair order is non-directional, while all material-condition, consumable-lot, process and service-environment identities must match exactly. |
| [`welding.cooling_interval`](modules/api/welding.cooling_interval.md) | Caller-selected monotonic cooling branch and caller-supplied target temperatures; not a thermal-cycle prediction. |
| [`welding.cooling_interval_batch`](modules/api/welding.cooling_interval_batch.md) | Apply independently caller-selected monotonic cooling branches and threshold pairs to one common recorded history. |
| [`welding.cooling_interval_sensor_batch`](modules/api/welding.cooling_interval_sensor_batch.md) | Apply sensor-local cooling branches to aligned traces sharing one explicit clock. |
| [`welding.cooling_time_correlation`](modules/api/welding.cooling_time_correlation.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`welding.declared_consumable_deposition_rate`](modules/api/welding.declared_consumable_deposition_rate.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`welding.declared_flux_basicity_ratio`](modules/api/welding.declared_flux_basicity_ratio.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`welding.declared_hydrogen_susceptibility_index`](modules/api/welding.declared_hydrogen_susceptibility_index.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`welding.dilution`](modules/api/welding.dilution.md) | Known constituent melted masses and reported elemental fractions; no inferred elemental balance or dilution threshold. |
| [`welding.dilution_with_uncertainty`](modules/api/welding.dilution_with_uncertainty.md) | Provenance-pinned declared melted constituent chemistry with a full caller-supplied joint covariance and explicit variable order. |
| [`welding.dissimilar_weld_applicability_evidence`](modules/api/welding.dissimilar_weld_applicability_evidence.md) | Base A/B, deposited layers, fusion-boundary sides, procedures, thermal history and service environment retain exact identities. |
| [`welding.duplex_phase_balance`](modules/api/welding.duplex_phase_balance.md) | Region, material, welding-process and thermal-history identities are reviewed caller records. |
| [`welding.flux_moisture_hydrogen`](modules/api/welding.flux_moisture_hydrogen.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`welding.hardness_mapping`](modules/api/welding.hardness_mapping.md) | Weld identity, exact test configuration, coordinates, caller regions, readings, uncertainty and lineage are preserved. |
| [`welding.hardness_traverse`](modules/api/welding.hardness_traverse.md) | Declared per-region upper hardness requirements and expanded measurement intervals, without spatial extrapolation. |
| [`welding.heat_treatment_history`](modules/api/welding.heat_treatment_history.md) | Complete sensor histories on one clock; all sensors must occupy the declared hold band simultaneously. |
| [`welding.hot_tap_applicability`](modules/api/welding.hot_tap_applicability.md) | Host pipe, material condition and operating pressure basis are exact caller-reviewed identities. |
| [`welding.hydrogen_bakeout_slab`](modules/api/welding.hydrogen_bakeout_slab.md) | One-dimensional finite planar diffusion screening with an initially uniform diffusible-hydrogen field, zero concentration on both reviewed exposed faces and caller-supplied effective diffusivity history. |
| [`welding.joint_profile`](modules/api/welding.joint_profile.md) | Transverse equal-reference surface observations outside an explicitly excluded joint zone. |
| [`welding.lamellar_tearing_applicability`](modules/api/welding.lamellar_tearing_applicability.md) | Parent material, product form, material condition and directionality identity match caller qualification evidence exactly. |
| [`welding.local_heat_treatment`](modules/api/welding.local_heat_treatment.md) | Sensor positions and synchronized histories are reviewed caller records. |
| [`welding.measured_energy_per_length`](modules/api/welding.measured_energy_per_length.md) | Measured source energy and deposited length cover the same observation interval. |
| [`welding.peening_treatment_evidence`](modules/api/welding.peening_treatment_evidence.md) | Component, material, zones, treatment clock, method, media, equipment and direction are caller reviewed. |
| [`welding.power_travel_energy`](modules/api/welding.power_travel_energy.md) | Source power and travel speed are constant over the declared weld interval. |
| [`welding.preheat_history_binding`](modules/api/welding.preheat_history_binding.md) | Exact required sensor surface/placement/scope/clock roles and explicit phase windows; caller-owned unique procedure envelope. |
| [`welding.preheat_procedure_envelope`](modules/api/welding.preheat_procedure_envelope.md) | Material, joint, process, consumable, hydrogen-control and restraint identities match exactly. |
| [`welding.production_weld_test_campaign_evidence`](modules/api/welding.production_weld_test_campaign_evidence.md) | Caller criteria only; no WPS or code qualification claim. |
| [`welding.production_weld_test_evidence`](modules/api/welding.production_weld_test_evidence.md) | Production-weld, procedure, material-lot and consumable-lot identities are caller-reviewed. |
| [`welding.reheat_cracking_applicability`](modules/api/welding.reheat_cracking_applicability.md) | Material, weld, HAZ and welding-process identities are exact caller-reviewed tokens. |
| [`welding.repair_welding`](modules/api/welding.repair_welding.md) | Caller criteria only; no WPS qualification or life inference. |
| [`welding.repair_welding_history`](modules/api/welding.repair_welding_history.md) | Recorded repair steps use one reviewed clock, remain ordered and cannot overlap. |
| [`welding.residual_stress_evidence`](modules/api/welding.residual_stress_evidence.md) | Each residual-stress value retains its declared tensor-component meaning and coordinate frame. |
| [`welding.rosenthal_3d_point_source_temperature`](modules/api/welding.rosenthal_3d_point_source_temperature.md) | Steady three-dimensional moving point source in a semi-infinite homogeneous solid with constant properties. |
| [`welding.rosenthal_cooling_interval`](modules/api/welding.rosenthal_cooling_interval.md) | Compose a fixed-point sampled Rosenthal moving-source history with caller-selected cooling-branch interval extraction. |
| [`welding.solidification_cracking_applicability`](modules/api/welding.solidification_cracking_applicability.md) | Weld-metal condition, process, consumable classification and chemistry basis match exactly. |
| [`welding.temper_bead_qualification`](modules/api/welding.temper_bead_qualification.md) | Repair scope, joint, base/deposited material conditions and process match exactly. |
| [`welding.waveform_energy`](modules/api/welding.waveform_energy.md) | Time-aligned sampled arc voltage/current; resolution must resolve the actual waveform. |
| [`welding.waveform_energy_uncertainty`](modules/api/welding.waveform_energy_uncertainty.md) | The full covariance follows the fixed coordinate order of every voltage sample, every current sample, efficiency, and travel distance with corresponding declared units. |
| [`welding.well_mixed_gas_purge`](modules/api/welding.well_mixed_gas_purge.md) | Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned. |
| [`welding.wps_qualification_envelope`](modules/api/welding.wps_qualification_envelope.md) | Qualified-procedure, revision, material-side, joint and welding-process identities match exactly. |

## workflow: 사용자 기준과 평가 절차

| API | 목적 |
|---|---|
| [`workflow.pressure_fatigue`](modules/api/workflow.pressure_fatigue.md) | Neutral operating history mapped through explicitly bounded membrane stress and user-calibrated fatigue parameters. |
| [`workflow.service_category_screening`](modules/api/workflow.service_category_screening.md) | Caller profiles bind code edition, equipment boundary, authority and reviewed evidence. |


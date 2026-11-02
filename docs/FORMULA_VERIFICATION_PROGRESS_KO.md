# 63개 계산군 계산식 확인 결과

대표 기준값 시험 통과: **63/63개 계산군**. 실행 사례: 79개.

각 계산군에 지정한 대표 문제의 수치 비교 결과다. 하위 모델과 물리 분기 전체, 실험자료 검증 및 시스템 통합 완료를 뜻하지 않는다.
Sines의 입력검사 우회 fixture는 이 계산식 시험에 사용하지 않는다.

| 번호 | 계산군 | 결과 | 실행한 비교 시험 |
|---|---|---|---|
| 1 | 질량감소 기반 부식속도 | passed | tests/test_engineering.py::test_coupon_loss_matches_removed_volume_and_annual_exposure |
| 2 | Faraday 전류·전하 기반 금속손실 | passed | tests/test_faraday_numeric_range.py::test_standard_declared_dissolution_relation |
| 3 | 분극저항 기반 부식전류 | passed | tests/test_extended_physics.py::test_stern_geary_has_explicit_decimal_tafel_units |
| 4 | 갈바닉 전류 및 저항 결합 | passed | tests/test_extended_physics.py::test_galvanic_current_closes_circuit_and_enforces_linearity |
| 5 | 혼합전위·Butler–Volmer 전극반응 | passed | tests/test_electrochemistry.py::test_mixed_potential_matches_independent_linear_circuit_and_area_weighting |
| 6 | Nernst 평형전위 | passed | tests/test_formula_reference_cases.py::test_group_06_nernst_against_activity_ratio |
| 7 | 경험식 기반 시간별 부식·두께손실 | passed | tests/test_formula_reference_cases.py::test_group_07_power_law_nonunit_exponent |
| 8 | 대기환경 기반 부식손실 | passed | tests/test_atmospheric_corrosion.py::test_loglinear_fit_recovers_authored_coefficients_and_holdout |
| 9 | 침식·부식 결합 손실 | passed | tests/test_erosion_corrosion.py::test_supported_piecewise_constant_rates_integrate_exactly |
| 10 | 응력부식균열 성장 | passed | tests/test_formula_reference_cases.py::test_group_10_scc_linear_velocity_time_integral |
| 11 | 질량작용·탄산계 수용액 평형 | passed | tests/test_carbonate_alkalinity.py::test_closed_form_aqueous_species_match_independent_synthetic_balance |
| 12 | 비이상 용액 활동도 | passed | tests/test_davies_activity.py::test_davies_coefficients_match_equation_and_report_dimensionless_activity |
| 13 | 단일·경쟁 고체상 평형 | passed | tests/test_formula_reference_cases.py::test_group_13_competing_solids_algebraic_solution |
| 14 | 수용액 반응망 속도 적분 | passed | tests/test_formula_reference_cases.py::test_group_14_reversible_dissociation_riccati_solution |
| 15 | 핵생성·석출·용해 속도 및 재고 | passed | tests/test_formula_reference_cases.py::test_group_15_precipitation_and_dissolution_thickness_ledger |
| 16 | 표면 피복·스케일 반응속도 | passed | tests/test_formula_reference_cases.py::test_group_16_coverage_attachment_exact_exponential |
| 17 | 다층 스케일 확산·반응·이동경계 | passed | tests/test_formula_reference_cases.py::test_group_17_layer_resistances_parallel_surface_flux |
| 18 | 기액 물질전달·이중막 | passed | tests/test_formula_reference_cases.py::test_group_18_two_film_nonzero_flux |
| 19 | 습윤 CO2 반응·수송·전극·스케일 동시결합 | passed | tests/test_formula_reference_cases.py::test_group_19_cylindrical_one_cell_diffusion_exact_exponential |
| 20 | Fick 확산 | passed | tests/test_extended_physics.py::test_diffusion_integral_and_surface_flux_obey_mass_balance |
| 21 | 벽 반응을 포함한 확산 | passed | tests/test_formula_reference_cases.py::test_group_21_blind_slit_nonzero_sink_exact_cosh |
| 22 | 이온 Nernst–Planck 수송 | passed | tests/test_formula_reference_cases.py::test_group_22_binary_ambipolar_diffusion_matrix_exponential |
| 23 | 틈 내부 성분·화학·전극·고체 동시 적분 | passed | tests/test_crevice_coupled_phase_rhs.py::test_bdf_internal_stage_feedback_matches_closed_form |
| 24 | 슬릿 유동·관성·압력·체적 연속 | passed | tests/test_formula_reference_cases.py::test_group_24_slit_momentum_exponential_and_signed_volume |
| 25 | 수소 확산·포획·방출·표면반응 | passed | tests/test_hydrogen_cylinder.py::test_radial_step_volume_mean_matches_bessel_series_and_refines |
| 26 | 박육·후육 원통 압력응력 | passed | tests/test_engineering.py::test_lame_boundary_tractions_and_hydrostatic_limit |
| 27 | 응력텐서·주응력·불변량 | passed | tests/test_reassessment_mechanics_materials.py::test_plane_stress_against_independent_tensor_eigensolution |
| 28 | 열팽창 구속·두께방향 열응력 | passed | tests/test_thermal_transient.py::test_uniform_fully_restrained_uniaxial_stress |
| 29 | 볼트 체결·탄성 조인트·마찰 토크 | passed | tests/test_blind_hole_and_bolt_torque.py::test_frictionless_thread_work_per_turn_matches_axial_work |
| 30 | 플랜지·가스켓 비선형 접촉평형 | passed | tests/test_formula_reference_cases.py::test_group_30_piecewise_linear_contact_spring_solution |
| 31 | 가스켓 점탄성·응력완화 | passed | tests/test_formula_reference_cases.py::test_group_31_prony_endpoint_force_balance_closed_form |
| 32 | 보정 누설식·가스켓 누설 이력 | passed | tests/test_formula_reference_cases.py::test_group_32_leakage_bilinear_spatial_and_time_integral |
| 33 | 잔존두께·프로파일 압력용량 | passed | tests/test_declared_pressure_relation.py::test_forward_and_inverse_authored_relation |
| 34 | 균열 응력확대계수 | passed | tests/test_reassessment_mechanics_materials.py::test_mode_i_length_scaling_and_zero_load_does_not_invent_critical_depth |
| 35 | FAD 파괴평가점·경계 비교 | passed | tests/test_fad.py::test_curve_is_linearly_interpolated |
| 36 | Paris·표 기반 균열전파 적분 | passed | tests/test_engineering.py::test_paris_integral_against_independent_quadrature |
| 37 | Norton 정상 크리프 변형 | passed | tests/test_formula_reference_cases.py::test_group_37_norton_nonreference_stress |
| 38 | Larson–Miller 등 크리프 파단 관계 | passed | tests/test_formula_reference_cases.py::test_group_38_larson_miller_hours_conversion |
| 39 | 크리프 시간분율·크리프–피로 손상 | passed | tests/test_formula_reference_cases.py::test_group_39_time_fraction_independent_sum |
| 40 | 응력–수명·평균응력 보정 | passed | tests/test_physical_consistency_review.py::test_group40_basquin_load_scaling_against_declared_power_law; tests/test_physical_consistency_review.py::test_group40_goodman_tensile_mean_stress_increases_equivalent_amplitude |
| 41 | 변형률–수명·Morrow·SWT | passed | tests/test_extended_physics.py::test_strain_life_recovers_cycles_and_rejects_extrapolation |
| 42 | Miner 누적손상 | passed | tests/test_formula_reference_cases.py::test_group_42_miner_independent_sum |
| 43 | 임계면 다축피로 | passed | tests/test_critical_plane.py::test_uniaxial_closed_form_swt_and_rotated_fs |
| 44 | 응력불변량 기반 다축피로 | passed | tests/test_formula_reference_cases.py::test_group_44_crossland_proportional_pure_shear |
| 45 | 비비례 다축 변형경로 피로 | passed | tests/test_formula_reference_cases.py::test_group_45_itoh_zero_additional_hardening_life_limit |
| 46 | J2 반복소성·이동경화 | passed | tests/test_formula_reference_cases.py::test_group_46_j2_perfect_plastic_radial_return |
| 47 | Neuber 노치 응력–변형률 | passed | tests/test_neuber_notch_strain_amplitude.py::test_neuber_solution_satisfies_local_compatibility |
| 48 | 이력 에너지·텐서 일 기반 피로 | passed | tests/test_fatigue_observations.py::test_hysteresis_path_work_orientation_and_open_boundary |
| 49 | 다층 정상 열전도·대류·복사 | passed | tests/test_insulation_surface_numerics.py::test_convection_only_matches_independent_resistance_solution |
| 50 | 과도 열전도·집중열용량 | passed | tests/test_thermal_transient.py::test_uniform_generation_matches_enthalpy_gain |
| 51 | Rosenthal 이동 용접열원 | passed | tests/test_formula_reference_cases.py::test_group_51_rosenthal_points_against_closed_form |
| 52 | CoolProp 상태방정식·퓨가시티 | passed | tests/test_cavitation.py::test_coolprop_adapter_preserves_versioned_saturation_state; tests/test_physical_consistency_review.py::test_group52_saturation_clapeyron_identity |
| 53 | 응축막 열·물질 수지 | passed | tests/test_formula_reference_cases.py::test_group_53_condensation_film_inventory_from_nonzero_flux |
| 54 | 기체 압력감쇠·누설·팽창 에너지 | passed | tests/test_pressure_test_numeric_range.py::test_isentropic_integral_known_gamma_two |
| 55 | Archard 마모 | passed | tests/test_formula_reference_cases.py::test_group_55_archard_volume_and_depth |
| 56 | 포물선 산화·비등온 산화 | passed | tests/test_nonisothermal_oxidation.py::test_isothermal_history_matches_constant_parabolic_increment |
| 57 | Arrhenius 반응·열적 노화 | passed | tests/test_metallurgical_aging.py::test_equivalent_exposure_is_exact_weighted_duration_sum |
| 58 | Ramberg–Osgood·Hollomon 재료 구성관계 | passed | tests/test_monotonic_plastic_curve.py::test_fit |
| 59 | 완전혼합 가스 퍼지 | passed | tests/test_well_mixed_gas_purge.py::test_half_life_analytic_case |
| 60 | 음극방식 전류·전하·양극 수명 수지 | passed | tests/test_identification_and_quality.py::test_cathodic_budget_integrates_joint_variation_and_interior_peak |
| 61 | 캐비테이션 여유·압력강하 지표 | passed | tests/test_cavitation.py::test_cavitation_margin_matches_independent_pressure_and_head_relations |
| 62 | 음향 도달시간 기반 위치·깊이 역산 | passed | tests/test_extended_physics.py::test_tofd_matches_independent_pythagorean_path_and_backwall_domain |
| 63 | FMC/TFM 초음파 영상 재구성 | passed | tests/test_fmc_tfm.py::test_analytic_three_four_five_focus_and_off_focus |

재현: `.venv\Scripts\python.exe -X utf8 scripts/verify_core_physics_formulas.py`

실행 근거: `artifacts/validation/formula_63/results.xml`, `coverage.json`. 시험 소스 해시는 `tests/data/core_physics_formula_cases.json`에 고정한다.

## 해석 범위

- 5번은 선형 전류수지, 19번은 고정 원통 한 셀 확산을 확인했다. 비선형 전극·이동경계 전체 결합은 별도다.
- 25번은 원통 수소 확산, 31번은 구간 선형 변형률 Prony 끝점 평형 사례다. 모든 포획·방출·연속시간 분기의 검증을 뜻하지 않는다.
- 44번은 비례 순수전단 Crossland, 45번은 추가 경화계수 0인 Itoh 수명 한계 사례다. 다른 다축 기준과 비비례 경로 전체는 별도다.
- 49번은 대류 저항, 53번은 비영 응축 질량·액막 수지다. 복사·잠열을 포함한 모든 결합 분기의 검증은 아니다.

63/63은 각 계산군에 최소 하나의 대표 수학적 기준값 비교가 통과했다는 뜻이다. 극단값·연결·전체 실행 완료율로 전용하지 않는다.

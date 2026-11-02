# 개별 계산 실행 및 누락 검사 결과

개별 공개 JSON API 계산 완료: **230/232개**.

63개 계산군은 기능 묶음이며, 그 안에서 이번 감사 대상으로 명시한 고유 API가 232개다. 이전 116개는 입력 계약 감사 대상 집합이다. 757개 전체 등록 API와 혼동하지 않는다.

검사 사례는 자체 작성 수학 문제를 우선 사용한다. Sines 수명 피팅은 Hannover 공개 시험의 실제 파단 수명과 별도로 재구성한 공칭 단축 응력을 사용했다. 다축 실험 검증이나 재료 허용치 검증은 아니다.
Hannover 자료: Christian Dänekas, DOI [10.25835/0dojws6u](https://doi.org/10.25835/0dojws6u), CC BY 4.0. 원자료·관측행·로컬 경로는 공개 영수증에 포함하지 않는다.

## 완료하지 않은 외부 근거

- `corrosion.piecewise_linear_rate_thickness_history`: 실측 초기 두께와 측정 근거 필요; 임의 값을 실측으로 표시하지 않음.
- `data.mendeley_atmospheric_corrosion_typed_rows`: 기초 관측자료 사용권한 확인 필요; 편집 데이터 라이선스와 구분.

위 두 항목은 정상 계산 완료 수에 포함하지 않았다. 근거 누락·권한 미승인 거부 시험은 별도로 수행했다. 거부 시험의 통과가 정상 계산 실행을 대신하지 않는다.

## 실행 영수증

| 검사 | 실행 사례 | 실패 | 건너뜀 |
|---|---:|---:|---:|
| formula | 70 | 0 | 0 |
| extreme | 69 | 0 | 0 |
| physical_connections | 14 | 0 | 0 |
| rule_handoff | 63 | 0 | 0 |
| regression_selected | 299 | 0 | 0 |
| repairs | 13 | 0 | 0 |
| external_prerequisites | 10 | 0 | 0 |
| analytic_examples | 3 | 0 | 0 |
| full_suite | 15693 | 25 | 3 |
| review_gates_after_repairs | 435 | 0 | 0 |
| examples_catalog_sensitivity_after_repairs | 433 | 1 | 0 |

전수 실행 후 수정한 파일의 재실행 영수증을 대체 대조한 결과: 15706개 중 15702개 통과, 1개 실패, 3개 건너뜀. 전체를 수정 후 새로 실행한 결과와는 구분한다.
주 예제 JSON에는 400개 API가 들어 있고 전체 등록 API는 757개여서, 단일 파일이 전체 API를 포함해야 한다는 기존 검사 1개가 남는다. 이 검사나 기대조건을 삭제하지 않았다. 누락 357개는 그 파일에 없는 API 수이며, 계산 코드 미구현 수나 미시험 모델 수가 아니다. 별도 계산·입력 fixture의 실행 근거는 이 문서의 232개 목록과 영수증으로 판단한다.
전수 실행의 건너뜀 3개는 옛 116개 입력 감사 범위 밖의 보조 baseline이다. 해당 B-dot·Davies·SIT 모델은 이번 232개 전수 공개 API 실행에서 별도로 계산 완료했다.

동일 시험이 여러 묶음에 포함될 수 있으므로 사례 수를 합산하지 않는다. 대표 계산식·극단값·선택 회귀는 63개 군별 확인이다. 물리 계산 간 연결 확인 15/63과 결과→규칙 소비 모듈 연결 63/63을 구분한다.

## 개별 API 실행 목록

| 계산군 | 모델 ID | 정상 계산 | 비고 |
|---|---|---|---|
| 1. 질량감소 기반 부식속도 | `corrosion.coupon_loss` | 완료 |  |
| 1. 질량감소 기반 부식속도 | `corrosion.coupon_loss_with_uncertainty` | 완료 |  |
| 2. Faraday 전류·전하 기반 금속손실 | `corrosion.charge_to_loss` | 완료 |  |
| 2. Faraday 전류·전하 기반 금속손실 | `corrosion.coupled_wall_metal_loss` | 완료 |  |
| 2. Faraday 전류·전하 기반 금속손실 | `corrosion.faraday` | 완료 |  |
| 3. 분극저항 기반 부식전류 | `corrosion.stern_geary` | 완료 |  |
| 4. 갈바닉 전류 및 저항 결합 | `corrosion.galvanic_linear` | 완료 |  |
| 4. 갈바닉 전류 및 저항 결합 | `degradation.galvanic_coupling` | 완료 |  |
| 4. 갈바닉 전류 및 저항 결합 | `degradation.galvanic_resistive_coupling` | 완료 |  |
| 5. 혼합전위·Butler–Volmer 전극반응 | `corrosion.mixed_potential` | 완료 |  |
| 5. 혼합전위·Butler–Volmer 전극반응 | `electrochemistry.crevice_mixed_potential_history` | 완료 |  |
| 5. 혼합전위·Butler–Volmer 전극반응 | `electrochemistry.nernst_driven_butler_volmer_history` | 완료 |  |
| 5. 혼합전위·Butler–Volmer 전극반응 | `integration.crevice_spatial_ohmic_mixed_potential` | 완료 |  |
| 5. 혼합전위·Butler–Volmer 전극반응 | `integration.wet_co2_cylindrical_spatial_mixed_potential` | 완료 |  |
| 5. 혼합전위·Butler–Volmer 전극반응 | `integration.wet_co2_cylindrical_transport_mixed_potential` | 완료 |  |
| 5. 혼합전위·Butler–Volmer 전극반응 | `integration.wet_co2_film_transport_limited_mixed_potential` | 완료 |  |
| 5. 혼합전위·Butler–Volmer 전극반응 | `integration.wet_co2_finite_inventory_electrode_mixed_potential` | 완료 |  |
| 5. 혼합전위·Butler–Volmer 전극반응 | `integration.wet_co2_scale_diffusion_electrode_mixed_potential` | 완료 |  |
| 6. Nernst 평형전위 | `degradation.crevice_nernst_potential_history` | 완료 |  |
| 7. 경험식 기반 시간별 부식·두께손실 | `corrosion.piecewise_linear_rate_thickness_history` | 보류 | 실측 초기 두께와 측정 근거 필요; 임의 값을 실측으로 표시하지 않음 |
| 7. 경험식 기반 시간별 부식·두께손실 | `corrosion.power_law` | 완료 |  |
| 7. 경험식 기반 시간별 부식·두께손실 | `corrosion.uniform_forecast` | 완료 |  |
| 7. 경험식 기반 시간별 부식·두께손실 | `degradation.calibrated_condition_loss_history` | 완료 |  |
| 7. 경험식 기반 시간별 부식·두께손실 | `degradation.calibrated_condition_loss_rate` | 완료 |  |
| 7. 경험식 기반 시간별 부식·두께손실 | `degradation.calibrated_damage_history` | 완료 |  |
| 8. 대기환경 기반 부식손실 | `corrosion.atmospheric_first_year_fit` | 완료 |  |
| 8. 대기환경 기반 부식손실 | `corrosion.atmospheric_first_year_prediction` | 완료 |  |
| 8. 대기환경 기반 부식손실 | `data.mendeley_atmospheric_corrosion_typed_rows` | 보류 | 기초 관측자료 사용권한 확인 필요; 편집 데이터 라이선스와 구분 |
| 8. 대기환경 기반 부식손실 | `degradation.atmospheric_multi_year_loss_history` | 완료 |  |
| 8. 대기환경 기반 부식손실 | `degradation.atmospheric_scenario_ensemble` | 완료 |  |
| 9. 침식·부식 결합 손실 | `degradation.erosion_corrosion_loss` | 완료 |  |
| 9. 침식·부식 결합 손실 | `degradation.erosion_corrosion_power_law_calibration` | 완료 |  |
| 9. 침식·부식 결합 손실 | `degradation.erosion_corrosion_synergy_decomposition` | 완료 |  |
| 10. 응력부식균열 성장 | `degradation.scc_crack_velocity_history` | 완료 |  |
| 11. 질량작용·탄산계 수용액 평형 | `chemistry.aqueous_bdot_self_consistent_speciation` | 완료 |  |
| 11. 질량작용·탄산계 수용액 평형 | `chemistry.aqueous_davies_self_consistent_speciation` | 완료 |  |
| 11. 질량작용·탄산계 수용액 평형 | `chemistry.aqueous_extended_debye_huckel_self_consistent_speciation` | 완료 |  |
| 11. 질량작용·탄산계 수용액 평형 | `chemistry.aqueous_mass_action_speciation` | 완료 |  |
| 11. 질량작용·탄산계 수용액 평형 | `chemistry.aqueous_sit_self_consistent_speciation` | 완료 |  |
| 11. 질량작용·탄산계 수용액 평형 | `chemistry.aqueous_tabulated_activity_speciation` | 완료 |  |
| 11. 질량작용·탄산계 수용액 평형 | `chemistry.carbonate_alkalinity_speciation` | 완료 |  |
| 11. 질량작용·탄산계 수용액 평형 | `chemistry.crevice_closed_batch_aqueous_equilibrium` | 완료 |  |
| 11. 질량작용·탄산계 수용액 평형 | `chemistry.fixed_fugacity_carbonate_equilibrium` | 완료 |  |
| 11. 질량작용·탄산계 수용액 평형 | `chemistry.fixed_fugacity_carbonate_history` | 완료 |  |
| 11. 질량작용·탄산계 수용액 평형 | `chemistry.fixed_fugacity_carbonate_scenario_ensemble` | 완료 |  |
| 12. 비이상 용액 활동도 | `chemistry.aqueous_extended_debye_huckel_activity` | 완료 |  |
| 12. 비이상 용액 활동도 | `chemistry.davies_activity_coefficients` | 완료 |  |
| 12. 비이상 용액 활동도 | `chemistry.pitzer_single_salt_activity` | 완료 |  |
| 12. 비이상 용액 활동도 | `chemistry.sit_activity_coefficients` | 완료 |  |
| 13. 단일·경쟁 고체상 평형 | `chemistry.competitive_solid_bdot_equilibrium` | 완료 |  |
| 13. 단일·경쟁 고체상 평형 | `chemistry.competitive_solid_davies_equilibrium` | 완료 |  |
| 13. 단일·경쟁 고체상 평형 | `chemistry.competitive_solid_equilibrium` | 완료 |  |
| 13. 단일·경쟁 고체상 평형 | `chemistry.competitive_solid_sit_equilibrium` | 완료 |  |
| 13. 단일·경쟁 고체상 평형 | `chemistry.crevice_competing_solid_equilibrium` | 완료 |  |
| 13. 단일·경쟁 고체상 평형 | `chemistry.crevice_component_solid_partition` | 완료 |  |
| 13. 단일·경쟁 고체상 평형 | `chemistry.single_solid_precipitation_equilibrium` | 완료 |  |
| 14. 수용액 반응망 속도 적분 | `chemistry.crevice_activity_based_reaction_rates` | 완료 |  |
| 14. 수용액 반응망 속도 적분 | `chemistry.crevice_aqueous_kinetic_network` | 완료 |  |
| 15. 핵생성·석출·용해 속도 및 재고 | `chemistry.competitive_solid_saturation_kinetics` | 완료 |  |
| 15. 핵생성·석출·용해 속도 및 재고 | `chemistry.crevice_nucleation_kinetic_history` | 완료 |  |
| 15. 핵생성·석출·용해 속도 및 재고 | `integration.crevice_cellwise_nucleation_kinetic_history` | 완료 |  |
| 16. 표면 피복·스케일 반응속도 | `chemistry.caller_scale_coverage_kinetics` | 완료 |  |
| 16. 표면 피복·스케일 반응속도 | `chemistry.caller_surface_scale_kinetics` | 완료 |  |
| 17. 다층 스케일 확산·반응·이동경계 | `chemistry.layered_scale_diffusion_limit` | 완료 |  |
| 17. 다층 스케일 확산·반응·이동경계 | `chemistry.planar_scale_diffusion_reaction_history` | 완료 |  |
| 17. 다층 스케일 확산·반응·이동경계 | `chemistry.planar_scale_reaction_demand_balance` | 완료 |  |
| 18. 기액 물질전달·이중막 | `degradation.wet_co2_gas_side_mass_transfer` | 완료 |  |
| 18. 기액 물질전달·이중막 | `degradation.wet_co2_liquid_side_mass_transfer` | 완료 |  |
| 18. 기액 물질전달·이중막 | `degradation.wet_co2_two_film_transfer` | 완료 |  |
| 18. 기액 물질전달·이중막 | `degradation.wet_co2_two_film_transfer_history` | 완료 |  |
| 19. 습윤 CO2 반응·수송·전극·스케일 동시결합 | `integration.wet_co2_cylindrical_finite_gas_stage_geometry_feedback` | 완료 |  |
| 19. 습윤 CO2 반응·수송·전극·스케일 동시결합 | `integration.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback` | 완료 |  |
| 19. 습윤 CO2 반응·수송·전극·스케일 동시결합 | `integration.wet_co2_cylindrical_stage_speciation_scale_feedback` | 완료 |  |
| 19. 습윤 CO2 반응·수송·전극·스케일 동시결합 | `integration.wet_co2_cylindrical_transient_transport` | 완료 |  |
| 19. 습윤 CO2 반응·수송·전극·스케일 동시결합 | `integration.wet_co2_scale_corrosion_moving_geometry_history` | 완료 |  |
| 19. 습윤 CO2 반응·수송·전극·스케일 동시결합 | `integration.wet_co2_scale_corrosion_simultaneous_history` | 완료 |  |
| 20. Fick 확산 | `transport.crevice_component_diffusion_1d` | 완료 |  |
| 20. Fick 확산 | `transport.semi_infinite_diffusion` | 완료 |  |
| 21. 벽 반응을 포함한 확산 | `chemistry.crevice_steady_wall_sink` | 완료 |  |
| 21. 벽 반응을 포함한 확산 | `chemistry.crevice_transient_wall_sink` | 완료 |  |
| 22. 이온 Nernst–Planck 수송 | `integration.crevice_activity_gradient_nernst_planck_flux_1d` | 완료 |  |
| 22. 이온 Nernst–Planck 수송 | `transport.crevice_activity_corrected_nernst_planck_1d` | 완료 |  |
| 22. 이온 Nernst–Planck 수송 | `transport.crevice_activity_corrected_reactive_nernst_planck_1d` | 완료 |  |
| 22. 이온 Nernst–Planck 수송 | `transport.crevice_electroneutral_multispecies_diffusion_1d` | 완료 |  |
| 22. 이온 Nernst–Planck 수송 | `transport.crevice_spatial_activity_solid_nernst_planck_1d` | 완료 |  |
| 22. 이온 Nernst–Planck 수송 | `transport.crevice_variable_area_activity_corrected_reactive_nernst_planck_1d` | 완료 |  |
| 23. 틈 내부 성분·화학·전극·고체 동시 적분 | `integration.crevice_component_state_bdf` | 완료 |  |
| 24. 슬릿 유동·관성·압력·체적 연속 | `corrosion.crevice_hydraulic_stage_rhs` | 완료 |  |
| 24. 슬릿 유동·관성·압력·체적 연속 | `corrosion.crevice_moving_volume_hydraulic_history` | 완료 |  |
| 24. 슬릿 유동·관성·압력·체적 연속 | `corrosion.planar_slit_hydraulic_flow` | 완료 |  |
| 24. 슬릿 유동·관성·압력·체적 연속 | `corrosion.planar_slit_hydraulic_history` | 완료 |  |
| 24. 슬릿 유동·관성·압력·체적 연속 | `corrosion.planar_slit_transient_hydraulic_history` | 완료 |  |
| 25. 수소 확산·포획·방출·표면반응 | `transport.hydrogen_dissociative_surface_rates` | 완료 |  |
| 25. 수소 확산·포획·방출·표면반응 | `transport.hydrogen_finite_cylinder_kinetic` | 완료 |  |
| 25. 수소 확산·포획·방출·표면반응 | `transport.hydrogen_slab_kinetic` | 완료 |  |
| 25. 수소 확산·포획·방출·표면반응 | `transport.hydrogen_trap_equilibrium` | 완료 |  |
| 25. 수소 확산·포획·방출·표면반응 | `transport.hydrogen_trap_thermal_rates` | 완료 |  |
| 25. 수소 확산·포획·방출·표면반응 | `welding.hydrogen_bakeout_slab` | 완료 |  |
| 26. 박육·후육 원통 압력응력 | `mechanics.lame_cylinder` | 완료 |  |
| 26. 박육·후육 원통 압력응력 | `mechanics.thin_cylinder` | 완료 |  |
| 27. 응력텐서·주응력·불변량 | `fatigue.sampled_stress_invariant_history` | 완료 |  |
| 27. 응력텐서·주응력·불변량 | `mechanics.plane_stress` | 완료 |  |
| 28. 열팽창 구속·두께방향 열응력 | `mechanics.thermal_restraint` | 완료 |  |
| 28. 열팽창 구속·두께방향 열응력 | `mechanics.through_wall_thermal_stress` | 완료 |  |
| 29. 볼트 체결·탄성 조인트·마찰 토크 | `fabrication.elastic_joint_load` | 완료 |  |
| 29. 볼트 체결·탄성 조인트·마찰 토크 | `fabrication.friction_resolved_bolt_torque` | 완료 |  |
| 30. 플랜지·가스켓 비선형 접촉평형 | `fabrication.flange_contact_field` | 완료 |  |
| 30. 플랜지·가스켓 비선형 접촉평형 | `fabrication.flange_nonlinear_contact_field` | 완료 |  |
| 30. 플랜지·가스켓 비선형 접촉평형 | `fabrication.gasket_multi_bolt_sector_equilibrium` | 완료 |  |
| 30. 플랜지·가스켓 비선형 접촉평형 | `fabrication.nonlinear_bolt_gasket_contact` | 완료 |  |
| 30. 플랜지·가스켓 비선형 접촉평형 | `fabrication.nonlinear_gasket_contact` | 완료 |  |
| 31. 가스켓 점탄성·응력완화 | `fabrication.flange_nonlinear_viscoelastic_contact_history` | 완료 |  |
| 31. 가스켓 점탄성·응력완화 | `fabrication.flange_viscoelastic_contact_history` | 완료 |  |
| 31. 가스켓 점탄성·응력완화 | `fabrication.gasket_evidence_bound_prony_history` | 완료 |  |
| 31. 가스켓 점탄성·응력완화 | `fabrication.gasket_prony_history` | 완료 |  |
| 31. 가스켓 점탄성·응력완화 | `fabrication.gasket_prony_joint_history` | 완료 |  |
| 31. 가스켓 점탄성·응력완화 | `fabrication.gasket_prony_relaxation_spectrum_fit` | 완료 |  |
| 31. 가스켓 점탄성·응력완화 | `fabrication.gasket_prony_temperature_shift_history` | 완료 |  |
| 31. 가스켓 점탄성·응력완화 | `fabrication.gasket_relaxation_curve` | 완료 |  |
| 31. 가스켓 점탄성·응력완화 | `fabrication.nonlinear_gasket_prony_joint_history` | 완료 |  |
| 31. 가스켓 점탄성·응력완화 | `fabrication.unilateral_nonlinear_gasket_prony_joint_history` | 완료 |  |
| 32. 보정 누설식·가스켓 누설 이력 | `fabrication.gasket_calibrated_leakage_history` | 완료 |  |
| 32. 보정 누설식·가스켓 누설 이력 | `fabrication.gasket_calibrated_leakage_rate_envelope` | 완료 |  |
| 32. 보정 누설식·가스켓 누설 이력 | `integration.gasket_leakage_pressure_inventory_decay` | 완료 |  |
| 33. 잔존두께·프로파일 압력용량 | `structural.declared_pressure_thickness_relation` | 완료 |  |
| 33. 잔존두께·프로파일 압력용량 | `structural.profile_capacity` | 완료 |  |
| 34. 균열 응력확대계수 | `fracture.stress_intensity` | 완료 |  |
| 35. FAD 파괴평가점·경계 비교 | `structural.caller_fad_envelope` | 완료 |  |
| 35. FAD 파괴평가점·경계 비교 | `structural.failure_assessment_history` | 완료 |  |
| 35. FAD 파괴평가점·경계 비교 | `structural.failure_assessment_points` | 완료 |  |
| 36. Paris·표 기반 균열전파 적분 | `fracture.paris_constant_amplitude` | 완료 |  |
| 36. Paris·표 기반 균열전파 적분 | `fracture.sequence_zone_memory` | 완료 |  |
| 36. Paris·표 기반 균열전파 적분 | `fracture.tabulated_crack_growth` | 완료 |  |
| 36. Paris·표 기반 균열전파 적분 | `fracture.tabulated_crack_growth_scenario_ensemble` | 완료 |  |
| 36. Paris·표 기반 균열전파 적분 | `fracture.tabulated_crack_growth_scenario_reduction` | 완료 |  |
| 36. Paris·표 기반 균열전파 적분 | `fracture.tabulated_crack_growth_uncertainty` | 완료 |  |
| 36. Paris·표 기반 균열전파 적분 | `fracture.tabulated_crack_growth_uncertainty_convergence` | 완료 |  |
| 36. Paris·표 기반 균열전파 적분 | `fracture.tabulated_curve_family_growth` | 완료 |  |
| 36. Paris·표 기반 균열전파 적분 | `fracture.variable_paris` | 완료 |  |
| 37. Norton 정상 크리프 변형 | `creep.norton` | 완료 |  |
| 37. Norton 정상 크리프 변형 | `creep.secondary_history` | 완료 |  |
| 38. Larson–Miller 등 크리프 파단 관계 | `creep.accelerated_lognormal_rupture_fit` | 완료 |  |
| 38. Larson–Miller 등 크리프 파단 관계 | `creep.conditional_life` | 완료 |  |
| 38. Larson–Miller 등 크리프 파단 관계 | `creep.larson_miller` | 완료 |  |
| 38. Larson–Miller 등 크리프 파단 관계 | `creep.lognormal_life_fit` | 완료 |  |
| 39. 크리프 시간분율·크리프–피로 손상 | `creep.time_fraction` | 완료 |  |
| 39. 크리프 시간분율·크리프–피로 손상 | `structural.creep_fatigue_campaign` | 완료 |  |
| 40. 응력–수명·평균응력 보정 | `fatigue.basquin` | 완료 |  |
| 40. 응력–수명·평균응력 보정 | `fatigue.goodman` | 완료 |  |
| 41. 변형률–수명·Morrow·SWT | `fatigue.morrow_strain_life` | 완료 |  |
| 41. 변형률–수명·Morrow·SWT | `fatigue.strain_life` | 완료 |  |
| 41. 변형률–수명·Morrow·SWT | `fatigue.strain_life_campaign` | 완료 |  |
| 41. 변형률–수명·Morrow·SWT | `fatigue.swt_strain_life` | 완료 |  |
| 42. Miner 누적손상 | `fatigue.miner` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.critical_plane_adaptive_search` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.critical_plane_continuous_bound` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.critical_plane_factors` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.critical_plane_findley_calibrated_life` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.critical_plane_findley_parameter` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.critical_plane_fs_life` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.critical_plane_grid_family_comparison` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.critical_plane_grid_refinement` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.critical_plane_minimum_enclosing_circle_factors` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.critical_plane_piecewise_linear_time_history` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.critical_plane_projected_rainflow` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.critical_plane_time_refinement` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.critical_plane_vector_path_factors` | 완료 |  |
| 43. 임계면 다축피로 | `fatigue.multiaxial_mcdiarmid_finite_plane_limit_screen` | 완료 |  |
| 44. 응력불변량 기반 다축피로 | `fatigue.dang_van_finite_parameter_life` | 완료 |  |
| 44. 응력불변량 기반 다축피로 | `fatigue.dang_van_finite_sample_limit_screen` | 완료 |  |
| 44. 응력불변량 기반 다축피로 | `fatigue.multiaxial_crossland_proportional_limit_screen` | 완료 |  |
| 44. 응력불변량 기반 다축피로 | `fatigue.multiaxial_invariant_limit_screen` | 완료 |  |
| 44. 응력불변량 기반 다축피로 | `fatigue.multiaxial_sines_life_fit` | 완료 |  |
| 44. 응력불변량 기반 다축피로 | `fatigue.multiaxial_sines_mean_limit_screen` | 완료 |  |
| 44. 응력불변량 기반 다축피로 | `fatigue.multiaxial_sines_parameter_life` | 완료 |  |
| 44. 응력불변량 기반 다축피로 | `fatigue.papadopoulos_p1_calibrated_life` | 완료 |  |
| 44. 응력불변량 기반 다축피로 | `fatigue.papadopoulos_p1_calibration` | 완료 |  |
| 44. 응력불변량 기반 다축피로 | `fatigue.papadopoulos_p1_finite_integral_screen` | 완료 |  |
| 44. 응력불변량 기반 다축피로 | `fatigue.papadopoulos_p1_miner_blocks` | 완료 |  |
| 44. 응력불변량 기반 다축피로 | `fatigue.papadopoulos_p2_finite_sample_limit_screen` | 완료 |  |
| 45. 비비례 다축 변형경로 피로 | `fatigue.ince_glinka_generalized_strain_amplitude` | 완료 |  |
| 45. 비비례 다축 변형경로 피로 | `fatigue.ince_glinka_gsa_life_from_curve` | 완료 |  |
| 45. 비비례 다축 변형경로 피로 | `fatigue.ince_glinka_gsa_miner_campaign` | 완료 |  |
| 45. 비비례 다축 변형경로 피로 | `fatigue.itoh_nonproportional_miner_blocks` | 완료 |  |
| 45. 비비례 다축 변형경로 피로 | `fatigue.itoh_nonproportional_strain_life` | 완료 |  |
| 45. 비비례 다축 변형경로 피로 | `fatigue.itoh_nonproportional_strain_parameter` | 완료 |  |
| 45. 비비례 다축 변형경로 피로 | `fatigue.wang_brown_parameter_life_fit` | 완료 |  |
| 45. 비비례 다축 변형경로 피로 | `fatigue.wang_brown_reviewed_excursion_parameter` | 완료 |  |
| 45. 비비례 다축 변형경로 피로 | `fatigue.wang_brown_temporal_normal_excursion` | 완료 |  |
| 46. J2 반복소성·이동경화 | `fatigue.j2_armstrong_frederick_strain_history` | 완료 |  |
| 46. J2 반복소성·이동경화 | `fatigue.j2_prager_strain_history` | 완료 |  |
| 47. Neuber 노치 응력–변형률 | `fatigue.neuber_notch_strain_amplitude` | 완료 |  |
| 47. Neuber 노치 응력–변형률 | `fatigue.neuber_strain_life_chain` | 완료 |  |
| 48. 이력 에너지·텐서 일 기반 피로 | `fatigue.closed_tensor_work_life` | 완료 |  |
| 48. 이력 에너지·텐서 일 기반 피로 | `fatigue.hysteresis_path` | 완료 |  |
| 48. 이력 에너지·텐서 일 기반 피로 | `fatigue.periodic_fourier_tensor_work` | 완료 |  |
| 48. 이력 에너지·텐서 일 기반 피로 | `fatigue.periodic_fourier_tensor_work_life` | 완료 |  |
| 48. 이력 에너지·텐서 일 기반 피로 | `fatigue.sampled_tensor_stress_strain_work_cycle` | 완료 |  |
| 49. 다층 정상 열전도·대류·복사 | `thermal.cylindrical_layers` | 완료 |  |
| 49. 다층 정상 열전도·대류·복사 | `thermal.insulation_surface_balance` | 완료 |  |
| 49. 다층 정상 열전도·대류·복사 | `thermal.planar_layers` | 완료 |  |
| 50. 과도 열전도·집중열용량 | `thermal.lumped_temperature` | 완료 |  |
| 50. 과도 열전도·집중열용량 | `thermal.transient_conduction_1d` | 완료 |  |
| 51. Rosenthal 이동 용접열원 | `welding.rosenthal_3d_point_source_temperature` | 완료 |  |
| 52. CoolProp 상태방정식·퓨가시티 | `thermo.co2_fugacity_coolprop` | 완료 |  |
| 52. CoolProp 상태방정식·퓨가시티 | `thermo.co2_mixture_fugacity_coolprop` | 완료 |  |
| 52. CoolProp 상태방정식·퓨가시티 | `thermo.co2_mixture_fugacity_history` | 완료 |  |
| 52. CoolProp 상태방정식·퓨가시티 | `thermo.co2_pure_fugacity_history` | 완료 |  |
| 52. CoolProp 상태방정식·퓨가시티 | `thermo.coolprop_pure_water_saturated_vapor_fugacity` | 완료 |  |
| 52. CoolProp 상태방정식·퓨가시티 | `thermo.coolprop_pure_water_single_phase_state` | 완료 |  |
| 53. 응축막 열·물질 수지 | `integration.wet_co2_gas_film_condensation_transfer_history` | 완료 |  |
| 53. 응축막 열·물질 수지 | `integration.wet_co2_lumped_wall_thermal_condensation_history` | 완료 |  |
| 54. 기체 압력감쇠·누설·팽창 에너지 | `inspection.gas_expansion_energy` | 완료 |  |
| 54. 기체 압력감쇠·누설·팽창 에너지 | `inspection.gas_pressure_decay` | 완료 |  |
| 55. Archard 마모 | `degradation.archard_wear` | 완료 |  |
| 56. 포물선 산화·비등온 산화 | `degradation.nonisothermal_parabolic_oxidation` | 완료 |  |
| 56. 포물선 산화·비등온 산화 | `degradation.parabolic_oxidation` | 완료 |  |
| 57. Arrhenius 반응·열적 노화 | `degradation.metallurgical_aging_exposure` | 완료 |  |
| 57. Arrhenius 반응·열적 노화 | `kinetics.arrhenius` | 완료 |  |
| 58. Ramberg–Osgood·Hollomon 재료 구성관계 | `materials.monotonic_hollomon_calibration` | 완료 |  |
| 58. Ramberg–Osgood·Hollomon 재료 구성관계 | `materials.ramberg_osgood` | 완료 |  |
| 59. 완전혼합 가스 퍼지 | `welding.well_mixed_gas_purge` | 완료 |  |
| 60. 음극방식 전류·전하·양극 수명 수지 | `protection.cathodic_budget` | 완료 |  |
| 61. 캐비테이션 여유·압력강하 지표 | `degradation.cavitation_margin` | 완료 |  |
| 61. 캐비테이션 여유·압력강하 지표 | `degradation.device_pressure_drop_cavitation_index` | 완료 |  |
| 62. 음향 도달시간 기반 위치·깊이 역산 | `inspection.acoustic_emission_arrival_localization` | 완료 |  |
| 62. 음향 도달시간 기반 위치·깊이 역산 | `inspection.tofd_depth` | 완료 |  |
| 62. 음향 도달시간 기반 위치·깊이 역산 | `inspection.ultrasonic_thickness` | 완료 |  |
| 63. FMC/TFM 초음파 영상 재구성 | `inspection.file_homogeneous_fmc_tfm` | 완료 |  |
| 63. FMC/TFM 초음파 영상 재구성 | `inspection.file_planar_multiview_fmc_tfm` | 완료 |  |
| 63. FMC/TFM 초음파 영상 재구성 | `inspection.homogeneous_fmc_tfm` | 완료 |  |
| 63. FMC/TFM 초음파 영상 재구성 | `inspection.planar_multiview_fmc_tfm` | 완료 |  |

## 재현

프로젝트 루트에서 다음 순서로 실행한다. 과학·열역학 선택 의존성이 필요하다.

```powershell
python scripts/prepare_core_full_run_inputs.py
# 아래 단계는 별도 취득한 해시 고정 Hannover 자료가 로컬에 있을 때만 실행
python scripts/prepare_hannover_sines_execution.py
python scripts/run_core_physics_full_calculations.py
python scripts/summarize_three_stage_review.py --run
python -m pytest -q
python scripts/report_core_execution.py
```

전체 계산 스크립트는 232개 전부 계산되지 않으면 종료 코드 1을 반환한다. `--pending`은 재개용이며 최종 전수 실행에는 사용하지 않았다.
공개 요약은 `validation/core_execution_receipt.json`, 로컬 상세 입력·결과·실행 XML은 제외 폴더 `artifacts/validation/`에 있다.
실행 성공은 수식 타당성·현장 적합성·모든 분기·모든 물리 결합·실험 검증 완료를 뜻하지 않는다.

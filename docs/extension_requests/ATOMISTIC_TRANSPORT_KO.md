# 원자 규모 수소 연구와 수송 공급자 연결 요청

각 트랩의 `material_condition_id`, `reference_lattice_id`는 평가 모델과 정확히 일치해야 한다. 격자간 site의 정의와 금속 원자당 site 수를 제공하며 금속 원자의 몰밀도와 site density를 자동으로 같게 놓지 않는다.

추가 송신 계약은 `HydrogenTrapPopulation`이다. `transport.hydrogen_trap_equilibrium`에 연결하려면 각 population의 site density(mol/m³), **격자 site 대비 양의 결합에너지(J/mol)**, 점유율 적용 한계와 근거를 공급한다. 이동 활성화장벽·단일 H의 결합에너지·다중 H의 추가 결합에너지는 다른 값이다. eV/H는 mol 기준으로 명시적으로 변환하고 원 부호·기준 구조·영점에너지·불확실성을 보존한다. 부호를 자동 절댓값으로 바꾸지 않는다.

여러 H가 한 결함을 점유할 때의 상호작용을 독립 site 여러 개로 자동 쪼개지 않는다. 평형 수신 모델은 독립 단일 점유·빠른 국소 평형 조건을 요구한다. 동역학 수신 경로는 아래 계약을 사용하며 다중 점유·상호작용은 여전히 별도 공급자가 필요하다. 국소 미분 확산계수를 전체 벽의 일정 D나 설비 수명으로 승격하지 않는다. 격자 확산계수와 기체→격자 경계 농도도 각각 근거가 필요하다.

조사 기준은 `hydrogen-local-energetics`의 `75987a93695e49561dfa81024e12bfa25fe2b20c`다. 초기 연결 범위는 원자 계산에서 확인된 에너지·이동·트랩 근거를 버전 있는 자료로 교환하는 것이다. 원자 에너지나 짧은 궤적만으로 설비 균열 성장률·수명을 직접 산출하지 않는다.

외부 공급자는 합금/상·결함 구조·격자/입계·온도 범위·계산 방법·포텐셜 또는 전자구조 설정·원시 결과 해시·불확실성을 제공한다. 유효 확산계수 D(T)를 제공하려면 관측한 이동의 충분성, 시간·크기 수렴, 활성화에너지와 prefactor의 식별, trap과 가역 포획의 모델을 별도로 기록한다. 이동이 관측되지 않은 궤적에서 0 확산계수나 정확한 절대 수명을 만들지 않는다.

MatIntegrity의 `transport.semi_infinite_diffusion`는 trap이 없는 일정 D·고정 표면농도의 수학 경로다. 유한 평판은 `transport.hydrogen_slab_kinetic`, 반경–축 유한 원통은 `transport.hydrogen_finite_cylinder_kinetic`이 고정 site의 포획·탈리와 선언한 표면 경계를 함께 계산한다. 교환 계약 `HydrogenKineticTrap`은 `HydrogenTrapPopulation`·시간 knot별 capture frequency(s⁻¹)·선택적인 독립 release frequency(s⁻¹)·초기 셀 점유율·별도 속도 근거를 받는다. `binding_energy_ratio`와 `independent_frequencies` 모드를 구분하며 후자는 입력 속도를 온도나 결합에너지로 다시 계산하지 않는다. 전체 입력은 각각 `HydrogenSlab`과 `HydrogenFiniteCylinder`다. 동일 재료·격자 기준과 원자 mol 단위, 온도/시간 범위·유효 매질 조건을 유지한다.

`transport.hydrogen_trap_thermal_rates`와 `HydrogenTrapThermalRates`는 외부에서 검토된 capture/release Arrhenius 또는 전이상태 파라미터를 공통 온도 knot의 독립 속도 이력으로 변환한다. 원자 규모 공급자는 `frequency_id`, trap/material/lattice/energy-reference ID, 유효 온도 범위, prefactor·활성화에너지 또는 활성화 엔탈피·엔트로피·transmission coefficient, 단위·부호·에너지 zero와 근거를 제공해야 한다. 결과의 `-RT ln(release/capture)`는 결합에너지 측정값으로 자동 채택하지 않는다. 다중 전이경로나 자유에너지 곡면을 한 개의 유효 장벽으로 줄인 경우 그 축약과 지원 범위를 별도로 기록한다.

`transport.hydrogen_slab_flow_multiplier_fit`은 공급된 전체 이력 하나에 양수 배수 하나를 적합해 실험 flow와 제한적으로 profile할 수 있다. 이는 원자 규모 공급자를 대체하지 않는다. 공급자는 배수 적용 전 이력, 지원 온도·농도·재료 상태, 계산 revision/configuration, 불확실성과 원 결과 digest를 그대로 제공해야 한다. 수신 측 적합은 calibration/holdout, 표면 면적·시계·검출기 보정과 모든 고정 입력을 별도로 검토하고, 배수가 1에서 벗어난 이유를 원자 모형 오차로 단정하지 않는다. 여러 에너지·prefactor·site density·surface capacity를 한꺼번에 조정하거나 국소 Jacobian을 전역 식별성으로 해석하지 않는다.

기체 표면 경로는 `transport.hydrogen_dissociative_surface_rates`와 `ThermallyActivatedSurfaceFlux`를 사용한다. 외부 공급자는 material/lattice/surface/species ID, gas-state provider와 fugacity 정의, reference fugacity, 온도·fugacity 지원 범위, 빈 격자 표면 흡수 및 단위 격자 점유 방출에 대응하는 atom-molar capacity prefactor·활성화에너지·근거를 제공해야 한다. 현재 수신식은 `J_abs(1-theta_L,s)-J_des theta_L,s`의 한 상태 축약이며 `J_abs`에 `sqrt(f/f_ref)`를 적용한다. 외부 결과가 실제 흡착 피복률, 두 site 해리, 재결합, 산화막·오염 또는 다중 경로를 포함하면 그 변수를 이 두 capacity에 자동 압축하지 말고 새 버전 계약을 제안한다. Partial/total 및 absolute/gauge pressure, 혼합가스 fugacity coefficient와 표면 상태를 명시하고, CoolProp pressure만으로 fugacity 자격을 주장하지 않는다.

현재 탈리 빈도는 capture frequency에 `exp[-binding/(R*T)]`를 곱해 계산하므로 해당 rate ratio와 prefactor/에너지 관례를 별도로 검토한다. 이동 장벽 하나를 포획 빈도로 바꾸거나 보편적인 `D/a²`를 근거 없이 사용하지 않는다. 시도 빈도·경로 중복성·격자/트랩 연결성·온도 지원 범위·식별 불확실성을 공급한다. 양자/영점에너지·엔트로피 차이를 생략한 비율이 유효하지 않으면 현재 모델에 억지로 맞추지 않는다. 독립 capture/release·상호작용·생성 trap·응력 결합·입계 네트워크는 후속 확장 항목이다. 원통 TDS 관측도 시편 대응·표면 경계·검출기 clock 없이 수송 검증으로 자동 변환하지 않는다.

인수 조건은 단위·재료 상태 대조, 공개 단순 확산 한계의 회복, trap 없는 해와의 일치, 공간·시간 수렴, 독립 permeation 시험과의 비교, 분해능이나 식별 부족 시 needs-data 처리다. 원자 규모 결과의 연계와 가스 수소 설비 파괴 모델의 실험 검증을 구분한다.

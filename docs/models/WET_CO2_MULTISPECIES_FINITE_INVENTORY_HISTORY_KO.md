# 습윤 CO₂ 유한 기상·다종 액상 물질수지 이력

## 목적과 계산 범위

이 계산은 유한한 CO₂ 기상 재고, 변하는 액상 부피, caller가 제공하는 구간별 벽면 전기화학 종 플럭스를 하나의 과도 물질수지로 연결한다. 기존 CO₂* 단일종 sink 모델보다 확장해, 반응에서 생성되거나 소비되는 여러 명시 종의 액상 재고와 종별 보존잔차를 동시에 추적한다.

기상과 직접 교환하는 액상 종은 `co2star_species_id`로 한정한다. 그 밖의 수용액 종은 caller가 준 벽 플럭스와 액상 유입/유출만 반영하는 독립 재고다. 탄산 평형이나 산·염기 반응을 자동 계산하지 않는다.

## API

모듈: `matintegrity.wet_co2_multispecies_finite_inventory_history`

- `WetCo2SpeciesFluxInterval`: 정확한 시간 구간의 signed 종별 벽 플럭스와 공급자/Evidence 계보.
- `WetCo2FiniteGasMultispeciesHistoryRequest`: 종 순서, 초기 재고, 기상 용량, Henry 계수, 물질전달속도, 액량 유량/유입 조성, 벽 플럭스 구간을 선언한다.
- `evaluate_wet_co2_finite_gas_multispecies_history(request)`: DOP853를 사용한 구간별 연속 적분.
- `specifications()`: 상위 registry 통합에 필요한 `ModelSpec` 선언.

상위 Model ID 후보: `integration.wet_co2_finite_gas_multispecies_wall_flux_history`.

## 수지 방정식

상태량은 액상 종별 물질량 `Nᵢ` [mol], 기상 CO₂ fugacity `f` [Pa], 액상 부피 `V` [m³]다. 액상 농도는 `Cᵢ=Nᵢ/V`로 계산한다. 전체 유효 전달속도 `k` [m/s], Henry 농도/fugacity 계수 `H` [mol/(m³·Pa)], 벽면적 `A` [m²]라 하면 기상-액상 전달률은 다음이다.

`Jgl = A k (H f − Cco2*)`  [mol/s]

`q`는 액상 부피 변화율 [m³/s]이다. 양수이면 유입이고 유입수의 종 농도 `Cin,ᵢ`를 더한다. 음수이면 잘 혼합된 액상 유출로 순간 벌크 조성 `Cᵢ`가 빠져나간다. caller 종별 벽 플럭스 `jw,ᵢ` [mol/(m²·s)]의 양수 방향은 액상 안쪽이다.

`dNᵢ/dt = 1(i=CO2*) Jgl + A jw,ᵢ + max(q,0) Cin,ᵢ + min(q,0) Cᵢ`

`df/dt = −Jgl / β`

여기서 `β`는 기상 몰 용량 [mol/Pa]이다. 기상-액상 교환은 CO₂*에만 적용되며 기상 재고 감소/증가와 액상 재고 변화를 함께 보존한다. 나머지 종의 수지는 caller 제공 경계 플럭스만 포함한다.

## 입력 계보와 검토

종 ID와 플럭스 사전의 키 순서를 정확히 일치시켜야 한다. 플럭스 구간은 빈틈·중첩 없이 정확히 연속이어야 한다. 각 구간에는 upstream 모델 ID, 결과 SHA-256, record ID, provider ID/revision, Evidence를 첨부한다. API는 이 구간 플럭스가 upstream 계산으로부터 어떻게 생성되었는지 추론하지 않으므로, 연결 변환은 상위 어댑터에서 그 source digest와 종/면적/부호 매핑을 검증해야 한다.

필수 검토 사항은 초기 상태 근거, 기상-액상 전달계수, 액상 유량/유입 조성, 벽 플럭스의 방향과 면적 기준, 공정 범위와 시계 일치다. 초기 농도는 mol/m³, 액상 부피는 m³, gas fugacity는 Pa, 기상 용량은 mol/Pa, Henry 계수는 mol/(m³·Pa), 전달속도는 m/s, 액량 유량은 m³/s, 벽 플럭스는 mol/(m²·s) 단위다.

## 가정과 제한

- 한 구간 내 벽 플럭스, 액상 부피 유량, 유입 조성, Henry 계수 및 전달속도는 상수로 유지한다. 구간 사이 시간 보간은 하지 않는다.
- 액상은 완전혼합으로 취급한다. 기상은 하나의 유한 재고로 나타낸다.
- CO₂* 수지는 기상과 연동되지만 H⁺, HCO₃⁻, CO₃²⁻ 등 별도 종의 생성·전환은 자동화하지 않는다. 전하중성, 전체 수용액 speciation, pH 반응 피드백을 계산하지 않는다.
- 전기화학 속도식 자체를 풀지 않는다. 입력 플럭스는 별도 upstream 모델에서 계산/검토된 구간 평균 공급량이어야 한다.
- 다공성 scale 내부 확산, 침전/용해, 반응 전면 이동, 국부 부식 깊이, 형상 변화를 풀지 않는다.
- 적분 실패, 음의 재고 또는 구간별 수지 폐쇄 실패는 해당 구간에서 중단하고 이미 계산된 구간 prefix만 반환한다.
- SciPy의 `solve_ivp(method="DOP853")`를 runtime dependency로 사용한다. 테스트·과학적 검증은 별도 절차이며 이 API 호출만으로 검증이 성립하지 않는다.

## 구현 및 재사용 권리 경계

모듈은 caller가 제공한 파라미터와 일반적인 물질수지/확산식으로 독립 구현했다. 특정 외부 문서의 문장, 데이터 표 또는 실험값을 포함하지 않는다. 전기화학 계수·측정 기록·공급자 데이터는 각각의 라이선스와 출처 조건을 호출자가 확인해야 한다. 프로젝트 공개 라이선스는 저장소의 별도 LICENSE 파일에서 관리한다.

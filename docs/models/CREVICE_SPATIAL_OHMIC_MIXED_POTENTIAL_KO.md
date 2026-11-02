# 전해질 저항을 포함한 크리비스 공간 혼합전위

## 목적

`integration.crevice_spatial_ohmic_mixed_potential`은 축방향 전해질 저항을 셀 사이에 둔 1차원 전류 원장과 국부 Butler–Volmer 반응을 결합해, 하나의 전기적으로 연속된 금속 표면에 형성되는 공간 전위 및 반응 전류 분포를 각 caller 시간점에서 계산한다. 기존 단일 혼합전위 계산은 모든 반응의 용액 전위를 하나로 두므로 간극 길이 방향 저항강하를 표현하지 않는다.

## 입력과 수치식

`CreviceSpatialOhmicMixedPotentialRequest`에는 순서 고정 셀의 길이·개구부, 유효 폭, 반응면 수, 온도, 셀별 전해질 전도도, branch별 셀 교환전류밀도 및 exact-knot 평형전위를 제공한다. 각 반응 branch에는 전자수, anodic/cathodic 전달계수, 서명 전류 방향, 적용 과전압 범위와 digest 고정 kinetics 출처가 필요하다. 기하, 전도도 및 각 branch 자료는 별도 Evidence와 이용조건에 결속한다.

미지수는 공통 금속 전위, gauge가 고정된 각 셀 용액전위 및 이웃 셀 간 전해질 전류다. 각 셀에서 반응전류와 전류차의 보존을, 각 셀 간에서 전도도·단면·간격으로 정의한 옴 관계를 동시에 만족하도록 비선형 방정식을 푼다. 입구와 막힌 끝은 전기 절연이며 금속은 등전위다. 시간점별 정상 상태를 독립적으로 해석한다.

## 결과

각 시간점의 금속전위, 셀별 gauge 상대 용액전위, 셀 경계 전해질 전류, branch별 셀 전류밀도, 반응별 총전류 및 전류 보존 잔차를 반환한다. 솔버가 발산하거나 결과가 caller support를 벗어나면 유효 계산 결과 대신 실패/범위 상태를 보존한다.

## 적용범위와 제외사항

- 전해질은 caller 제공 일정 국소 전도도로 표현한다. migration, 농도분극, 수송제한, activity/speciation은 포함하지 않는다.
- 금속은 전기적으로 연속인 등전위로 가정한다. 금속 저항, 이중층 충전, 시간 의존 전기화학, 용액 유동, 움직이는 간극은 제외한다.
- 평형전위·교환전류·전달계수와 방향은 caller 입력 및 증거에 따른다. 모델이 반응기구나 보정값을 추정하지 않는다.
- 공간 전위·부분 전류 결과는 부식률, 금속손실, 수명, 고장확률, 합격 또는 설비 qualification이 아니다.
- 과전압 support, nonlinear convergence, mesh/time sensitivity 및 독립 실험 자료를 별도로 검증해야 한다.

## 식별자

- Model ID: `integration.crevice_spatial_ohmic_mixed_potential`
- 입력: `CreviceSpatialOhmicMixedPotentialRequest`
- 반응 branch: `CreviceSpatialReactionBranch`
- 계산 API: `solve_crevice_spatial_ohmic_mixed_potential(request)`
- Source IDs: `caller_crevice_spatial_butler_volmer_branch_profiles`, `caller_crevice_spatial_electrolyte_conductivity`, `finite_volume_electrolyte_resistance_with_local_butler_volmer_balance`, `nist_molar_gas_constant`, `iupac_faradays_laws_of_electrolysis`

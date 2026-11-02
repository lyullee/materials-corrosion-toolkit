# Wet-CO₂ 원통 공간 과도 수송과 혼합전위 연성

## API와 범위

`integration.wet_co2_cylindrical_spatial_mixed_potential`은 원통 액막의 방사 유한체적 종 농도장을 시간에 따라
적분하면서, 매 적분 상태에서 caller가 제공한 Butler–Volmer 반응 가지들의 공통 영전류 전위를 다시 구한다.
농도장과 전위가 같은 순간 상태를 공유하는 semi-discrete 연성 계산이다. 기존 knot별 정상 수송 계산과 달리
유한 초기 액막 inventory와 시간에 따른 셀 농도 변화를 유지한다. 기존 prescribed extent 과도 계산과 달리
반응률을 외부에서 고정하지 않고 혼합전위와 반응별 물질 공급 한도로 결정한다.

- 요청: `matintegrity.wet_co2_cylindrical_spatial_mixed_potential.WetCo2CylindricalSpatialMixedPotential`
- 시간 절점: `WetCo2SpatialElectrochemicalKnot`
- 반응 가지: `electrode_kinetics.ButlerVolmerReaction`
- 실행: `evaluate_wet_co2_cylindrical_spatial_mixed_potential(request)`
- 사양: `specifications()`

## 계산식과 결합 순서

축방향 단위 길이의 환형 셀 부피는 `π(r_outer²-r_inner²)`이다. 셀 중심 사이 확산은 각 구간의
`ln(r₂/r₁)/D` 저항을 더해 계산한다. 외측 액막 경계에는 절점별 bulk 농도를 적용한다. 시간 간격 내부에서는
경계 농도, film 두께, 셀별 확산계수, BV 가지를 왼쪽 절점 값으로 유지한다. 형상과 전기화학 입력 절점은
정확히 같은 시각·순서여야 하며, 절점 도달 시 이전·새 방사 격자의 겹치는 부피에 대해 농도를 보존적으로
재매핑하고 새로 포함된 영역 및 잘려 나간 영역을 별도 inventory 장부에 기록한다.

각 적분기 상태에서 첫 셀과 벽 사이의 원통 확산 저항으로 종별 순간 공급 한도를 만든다. 공통 전위 후보마다
BV 산화·환원 가지 전류를 계산하고, 해당 가지가 소비하는 종의 전체 요구량이 공급 한도보다 크면 관련 가지에
같은 제한 계수를 적용한다. 제한 전류 합이 0이 되는 전위를 공통 반응 상태로 선택한다. 그 전위와 가지별
전류에서 반응 진행률을 계산하고, 화학양론에 따라 벽 셀 종 source/sink, reaction extent, 원소 및 전하 장부를
함께 적분한다. 영전류 전위의 bracket이 caller가 제공한 교정 범위 안에서 성립하지 않으면 계산을 중단한다.

## 보존 및 실패 조건

셀별 비음수 유한 농도, 전체 종별 몰수, 재격자화 유입·유출, 수용액 전하, BV 전자 전하 전달, 형상에서 계산한
벽 원소 inventory 감소를 검사한다. BV 반응의 명시적 종 조성은 caller formula로 원소·전하 균형을 확인하고,
모든 절점의 공급 경계 및 교정자료는 digest와 사용권 Evidence로 묶는다. 수렴하지 않는 잠재전위, 음의 셀 농도,
비유한 상태, 물질 공급 초과 또는 inventory closure 초과가 생기면 해당 절점 결과는 내지 않고 성공한 절점
prefix와 실패 이유를 반환한다.

이 계산은 긴 길이 1 m당 축대칭 bookkeeping을 사용한다. geometry history의 벽 원소 감소가 caller의 BV
화학양론과 일치하지 않으면 계산을 통과시키지 않는다. 통과 결과도 numerical balance 및 입력 내부 일관성에
대한 확인일 뿐이다.

## 모델 한계

- 종 목록, 전하수, 화학식, 경계 농도, 확산계수, BV 교정값과 반응 방향을 caller가 제공해야 한다.
- CO₂ 수용액 speciation, 평형상수, pH, 상 선택, 석출/용해 반응, 산화막·스케일 구조, 난류 및 비축대칭 효과는
  추론하지 않는다.
- 벽 근처 공급 제한은 첫 radial cell의 농도와 벽-셀 중심 간 원통 저항을 이용하는 결정론적 가지 제한이다.
  이것은 계면 반응의 검증된 물질전달 상관식 또는 표면농도 모델이 아니다.
- 사용 조건 사이의 외삽, 잠재전위 calibration 범위 밖 계산, 임의의 reaction branch 선택은 허용하지 않는다.
- 축방향 혼합·분산, 전해질 전도 전위장, 국부 전류 분포, 이중층 충전, 반응 중 geometry 연속 변화는 모델링하지
  않는다. 형상은 주어진 절점에서 계단형으로 고정된다.
- 결과는 검증된 설계 허용치, 실험적 적합성, 수명, 위험도 또는 실패확률이 아니다.

## 출처와 근거

- `independent_transient_cylindrical_finite_volume_electrochemical_inventory`: 축대칭 환형 유한체적 확산·재고
  균형을 계산 코드에 명시한 수치 모델 정의. 물리 입력은 모두 caller가 제출한다.
- `caller_calibrated_butler_volmer_reaction_set`: caller가 허가와 적용성을 확인한 반응별 교정값, 전자수, BV 계수,
  평형전위 범위 및 종 화학양론.
- `degradation.wet_co2_cylindrical_scale_geometry_history`: 정확히 정렬된 원통 형상 절점 입력.
- `caller_boundary_transport_initial_inventory_and_alloy_records`: 경계·확산·초기 상태·벽 물성의 digest와 Evidence.

수치 구현 개요는 Python `solve_ivp`의 BDF 적분기와 원통 셀 사이 logarithmic resistance를 사용한다. 수치
적분기 사용 사실은 입력 계수나 실험 검증을 대신하지 않는다.

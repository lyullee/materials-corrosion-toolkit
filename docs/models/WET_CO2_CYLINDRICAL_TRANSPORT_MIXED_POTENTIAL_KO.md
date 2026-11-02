# Wet-CO₂ 원주형 액막의 방사 수송·혼합전위 연동

## 목적과 연계

integration.wet_co2_cylindrical_transport_mixed_potential은 원주형 스케일 형상 API가 만든 정확한 시간
절점별 bore radius를 입력으로 사용해, caller가 정의한 액막 안에서 각 반응물의 방사 확산과 Butler–Volmer
전극 반응을 연결한다. 각 시간 절점의 형상·경계농도·확산계수·반응 kinetic record를 한 번씩 독립 계산한다.

Python API:

- 요청: matintegrity.wet_co2_cylindrical_transport_mixed_potential.WetCo2CylindricalTransportMixedPotential
- 절점: WetCo2CylindricalElectrodeKnot
- 종별 경계·확산 입력: WetCo2CylindricalSpeciesBoundary
- 계산: evaluate_wet_co2_cylindrical_transport_mixed_potential(request)
- Model ID: integration.wet_co2_cylindrical_transport_mixed_potential

## 방법

형상 요청은 WetCo2CylindricalScaleGeometryHistory로 입력하며, 그 전체 JSON digest를 함께 요구한다.
전극 절점의 시각 배열은 형상 절점과 정확히 일치해야 한다. 보간은 수행하지 않는다.

각 절점의 bore 반경 r₀에서 caller 액막 두께 δ만큼 바깥 경계를 설정한다. 그 구간을 caller가 제공한 셀별
확산계수로 나눈다. k번째 환형 셀의 단위 길이당 저항은 다음과 같다.

    R_k = ln(r_(k+1) / r_k) / D_k
    K_inner = 1 / (r_0 × Σ R_k)
    J_wall = K_inner × (C_bulk - C_wall)
    capacity = K_inner × C_bulk

각 셀 경계 농도는 inner-wall 소비 플럭스에서 바깥 방향으로 환형 저항을 누적해 재구성한다. 일정한 확산계수의
원통 steady 확산에는 이 로그 반경 저항이 연속 원통 Fick 법칙을 그대로 나타낸다. 여러 셀은 caller의
piecewise-constant 확산계수를 보존하는 직렬 유한체적 저항망이다.

각 potential에서 기존 ButlerVolmerReaction의 caller 교정 kinetics를 계산한다. 반응 화학양론에 따라
반응물 소비가 생기는 gross partial-current branch의 몰 요구량을 각 종의 원주 저항 기반 capacity와
비교한다. 요구량이 capacity를 넘으면 해당 종을 소비하는 가지들을 동일 비율로 제한하고, 여러 종을
소비하는 반응에는 가장 강한 제한을 적용한다. 조정 후 반응들의 net current가 0이 되는 potential을 각
반응의 공통 교정 구간에서 이분법으로 찾는다. 소비 플럭스로 내벽과 셀 경계 농도를 복원하며, 외벽 플럭스는
원통 면적비 r₀/r_outer로 나타낸다.

## 입력 근거와 출처 경계

- 내경·외경·축 길이, wall recession, 고체상 inventory 및 geometry/history digest는
  degradation.wet_co2_cylindrical_scale_geometry_history 계약에서 받는다.
- 각 절점에서 species별 bulk 농도와 방사 셀 확산계수, 액막 두께를 caller가 제공한다.
- 온도별 Butler–Volmer 반응은 기존 electrode_kinetics.ButlerVolmerReaction을 재사용하며, 각 교정 digest가
  caller Evidence와 라이선스 ID에 연결되어야 한다.
- 이번 방법은 원통 환형 셀 저항, 종 보존식과 전류 균형의 독립 구현이다. 신규 관측자료, 경험 상수,
  물성표, 문헌 원문 또는 외부 solver 코드를 포함하지 않는다.
- source IDs: independent_cylindrical_radial_finite_volume_species_balance,
  caller_calibrated_butler_volmer_reaction_set,
  degradation.wet_co2_cylindrical_scale_geometry_history.

## 제한

- 각 knot는 독립 정상 상태다. 종의 시간 축적, 대류, 축방향 변화 및 반응-확산 PDE를 시간 적분하지 않는다.
- 액막 두께, bulk 농도, 종별 diffusivity profile 및 kinetics는 입력값이다. 완전한 carbonate speciation,
  pH 피드백, 수용액 활동도, homogeneous reaction, Henry/CO₂ 흡수는 추론하지 않는다.
- branch 제한은 질량 공급량을 어기지 않는 reduced steady closure다. 표면 농도 의존 kinetics, 다공성 스케일
  내부 확산, 공간적으로 분해된 전극 반응을 대신하지 않는다.
- 스케일 생성·용해, 보호도와 벽 후퇴를 이 계산이 업데이트하지 않는다. geometry API에 입력한 history를
  다시 바꾸지 않는 일방향 연동이다.
- 정확한 시간 knot만 계산하며 값의 시간 보간·적분은 하지 않는다. 결과는 적합성, 부식률, 잔여수명, 확률,
  물리검증 또는 재료 qualification이 아니다.

## 개발·검증 상태

계약과 계산 코드, 본 방법 문서만 작성했다. 단위·수치 테스트, package build, 장시간 계산과 독립 실험 비교는
아직 하지 않았다. digest·Evidence 검사는 입력 계보를 보존하기 위한 조건이지 과학적 타당성 검증이 아니다.

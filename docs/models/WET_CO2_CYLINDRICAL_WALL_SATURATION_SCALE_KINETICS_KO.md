# 원통형 Wet-CO₂ 벽인접 활동도에서 caller scale kinetics로의 연결

## 목적

integration.wet_co2_cylindrical_wall_saturation_scale_kinetics는 이미 구현된 세 경로를 한 호출에서 연결한다.

1. caller의 정확한 moving-cylinder geometry knot에서 방사 수송·유한 species inventory를 계산한다.
2. 사용자가 선택한 wall-adjacent cell 농도에 caller activity coefficient와 Ksp를 결합해 neutral solid saturation ratio를 계산한다.
3. exact-knot saturation history를 caller single-phase scale-thickness kinetics로 전달한다.

이는 새로운 activity model, phase discovery, precipitation law가 아니다. 기존 wet-CO₂ API와 사용자 자료 사이의
보수적인 접착 API다.

## Python API

- 모듈: matintegrity.wet_co2_cylindrical_wall_saturation_scale_kinetics
- 요청: WetCo2CylindricalWallSaturationScaleKinetics
- phase activity 자료: WetCo2CylindricalPhaseActivityKnot
- 계산: evaluate_wet_co2_cylindrical_wall_saturation_scale_kinetics(request)
- Model ID: integration.wet_co2_cylindrical_wall_saturation_scale_kinetics

## 계산과 연결 규칙

Transport API의 history에서 caller가 고른 near-wall radial cell 농도 Cᵢ [mol/m³]를 mol/L로 변환한다.
각 참여 이온의 activity coefficient γᵢ는 매 시각마다 caller가 제공한다. 표준상태는 1 mol/L이며,
무차원 activity는 aᵢ=γᵢ(Cᵢ/1000)로 계산한다. neutral 후보 고체의 용해식에서 caller가 제시한 이온
활동도 곱 지수 νᵢ, caller Ksp에 대해:

    log10(Q) = Σ νᵢ log10(aᵢ)
    log10(Ω) = log10(Q) - log10(Ksp)
    Ω = Q / Ksp

고체 formula의 원소수와 이온 항의 지수 가중 원소수 및 전체 전하를 계약에서 맞춘다. Ksp·gamma record,
provider revision, Evidence digest 및 시간/온도를 개별 knot마다 고정한다. zero concentration이 활동도 곱의
인자를 0으로 만들면 saturation ratio를 0으로 보존한다. 모든 history knot가 transport·activity·equilibrium
기록과 exact time order로 일치해야 한다.

계산된 Ω 값은 CallerSurfaceScaleKinetics의 각 인접 구간 시작·끝 값에 연결된다. 구간 양 끝 saturation이
달라지면 값 사이를 선형 경로로 해석하므로 호출자가 그 보간 가정을 검토해야 한다. 온도 변화가 있을 때는
caller가 구간의 좌측 온도를 rate 계산에 사용할지 명시적으로 확인해야 하며, Arrhenius profile은 별도로
reviewed된 경우에만 kinetics 모델이 허용한다.

## 입력 근거와 source 경계

- cylindrical transient transport request와 완전한 SHA-256
- 선택 phase ID 및 neutral solid formula
- 그 solid의 용해 활동도곱 지수·원소·전하 balance를 결합한 caller stoichiometry record와 Evidence
- wall-adjacent cell index (기본 0, inner-to-outer 셀순서)
- 이온별 activity-product exponent
- 각 exact knot의 caller γ 표와 digest/Evidence
- 같은 knot의 caller log10 Ksp와 digest/Evidence
- 동일 phase와 동일 molar-volume을 사용하는 caller scale-kinetics request
- material/solution/geometry ID가 일치하는 physical-scope·asset·location·clock

Source IDs: caller_cylindrical_wall_activity_product_to_scale_kinetics,
caller_cylindrical_transient_species_history_for_wall_saturation,
caller_surface_scale_kinetics. 새 실측값, gamma 식, Ksp, 보정계수, 문헌 표 또는 원문은 포함하지 않는다.
활동도 계수, Ksp, phase stoichiometry, 단위·표준상태, reaction direction 및 재사용 권리는 caller가
해당 Evidence를 기반으로 결정한다.

## 제한

- 이 API는 transport history를 계산한 뒤 결과를 chemistry/scale law에 전달하는 순차 합성이다. scale growth가
  앞서 계산한 transport, liquid boundary, bore radius 또는 corrosion flux를 다시 갱신하지 않는다.
- transport state는 선택된 radial FV cell의 대표농도다. 셀 중심 농도를 전극 표면농도나 pore 내부 농도로
  해석하지 않는다.
- speciation, electroneutrality 재해석, 활동도 모델, pH 변화, 경쟁 상 안정성, 핵생성, scale morphology·porosity,
  부착/박리 및 protective effect는 자동 계산하지 않는다.
- saturation path를 선형화한 값은 두 endpoint 사이에서 caller가 승인한 근사다. 실제 화학시간 이력의 연속
  궤적을 복원하지 않는다.
- 각 결과는 caller thermodynamic inputs와 scale kinetic calibration의 범위에 종속된다. 이는 실험 검증,
  부식률 qualification, 수명·확률 또는 코드 수용 판정이 아니다.

## 개발·검증 상태

typed input 연결, 선택된 phase의 charge/formula balance, digest/Evidence binding, exact-knot saturation 계산과
기존 caller scale kinetic API로의 요청 합성을 추가했다. 테스트, 장시간 수치 검증, package build와 실험 비교는
실행하지 않았다.

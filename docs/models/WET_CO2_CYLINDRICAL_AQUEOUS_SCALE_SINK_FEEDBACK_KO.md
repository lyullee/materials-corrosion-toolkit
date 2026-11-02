# Wet-CO₂ 원통형 scale sink와 BV 수송 피드백

## API

- Model ID: `integration.wet_co2_cylindrical_aqueous_scale_sink_feedback`
- Schema: `matintegrity.wet_co2_cylindrical_aqueous_scale_sink_feedback.v1`
- 입력: `WetCo2CylindricalAqueousScaleSinkFeedback`
- phase 입력: `WetCo2AqueousScalePhase`
- exact-knot flux 입력: `WetCo2ScaleReactionKnot`
- 계산 함수: `evaluate_wet_co2_cylindrical_aqueous_scale_sink_feedback`
- provenance source IDs: `bounded_bv_transport_with_caller_scale_reaction_interval_sources`, `cylindrical_radial_supply_cap_for_scale_reactants`

## 모델 범위

기존 공간 원통형 BV solver의 exact time knot, 방사 유한체적 격자, 공통 혼합전위 계산 및 Butler–Volmer branch 제한을 사용한다. 별도 API의 interval RHS에 caller가 제공한 scale 반응 항을 추가한다. 양의 flux는 caller가 지정한 상의 침전이며, 반응식의 aqueous 계수에 따라 용액 종을 소비한다. 음의 flux는 용해이며 같은 화학량론으로 용액에 종을 공급한다. 이 source/sink는 각 interval의 BDF 우변에 BV 반응과 동시에 들어가고, interval 종료 시 종별 액상 inventory 잔차를 계산한다.

각 상의 반응 화학량론, 고체 원소식, 그리고 exact-knot의 intrinsic signed precipitation flux는 caller 입력이며 digest 및 사용 허가가 있는 Evidence에 결속한다. 양의 stoichiometric coefficient는 침전에서 소모되는 aqueous reactant, 음의 coefficient는 생성되는 aqueous species다. 이 모듈은 상 선택, 평형상수, 활동도, 포화도, kinetic law의 계수를 만들거나 추론하지 않는다. flux의 물리적 의미와 계수는 외부에서 검토되어야 한다.

침전 flux는 모든 소비 aqueous species 각각의 radial 원통 확산 공급량으로 제한된다. 동일 종을 소비하는 여러 상은 합산 공급량을 넘지 않도록 flux를 비례 축소한다. 용해 flux는 해당 exact interval 시작점의 고체 재고를 초과할 수 없다. flux와 경계조건은 왼쪽 exact knot 값으로 interval 전체에 고정한다.

모델은 제한된 Picard 반복에서 좌측 knot의 농도·geometry로 확산 제한 flux를 다시 계산하고, 그 flux를 다음 BV transport solve의 source/sink 항으로 적용한다. 같은 반복에서 wall BV release와 고체 line inventory를 원통 annulus 식에 넣어 모든 exact knot의 bore 및 steel radius 경로를 갱신한다. 반경과 flux residual이 입력 허용오차를 만족하지 않으면 완료로 반환하지 않고 완료 prefix와 함께 `out_of_scope`를 반환한다.

## 보존 장부와 digest

각 interval 결과는 아래를 별도로 보존한다.

- 경계 교환, BV 반응, scale 반응이 액상 종 inventory에 준 변화와 종별 잔차
- charge 및 원소 잔차
- scale 반응에 의한 종별 molar transfer, 상별 signed flux, aqueous–solid 원소 increment closure
- 보수적 격자 이동 함수가 반환한 inner/outer 경계 fill 또는 sweep 기록
- exact-knot별 phase line inventory, wall 원소 release 및 반경 경로
- caller flux/stoichiometry digest와 상위 요청 digest, 반복 geometry digest

종 inventory 잔차는 각 고정-geometry interval의 BV·scale source/sink·외부 경계 항에 대해 계산한다. 격자 이동은 다음 interval의 초기 상태로 remap하며 remap 경계 유입·유출을 별도 기록한다. 이 버전에서는 여러 interval에 걸친 전역 누적 aqueous element/charge 장부를 독립된 총괄 잔차로 묶지 않는다. 각 exact-knot 원소별 wall release가 합금 조성의 원통 recession과 맞는지는 별도 geometry gate로 확인한다. `computed`는 이 제한된 수치 계약의 성립을 뜻하며 외부 화학의 타당성이나 실험 검증을 의미하지 않는다.

## 제한 및 적용 전 검토

- 반응 flux는 left-held caller 값이다. 제한 flux는 interval 시작점에서 구해 같은 BV interval RHS 전체에 일정하게 넣는다. interval 내부에서 포화도나 전기화학 상태에 반응하여 달라지는 연속 kinetic law는 풀지 않는다.
- 확산 공급은 caller BV 수송 경로의 piecewise radial diffusivity와 film 경계에서 얻는 제한량이다. 침전 상의 핵생성, 표면 피복에 따른 유효면적 감소, scale 내부 확산, 열역학 상 선택은 포함하지 않는다.
- 침전은 용액 종 농도에 영향을 주므로 다음 interval BV solve와 혼합전위에는 전달된다. 하지만 scale 반응식은 BV branch의 전하전류 항이 아니다. 중성 scale 반응식이 요구되고 산화환원·산염기 부반응은 caller가 별도로 모델링해야 한다.
- aqueous reaction stoichiometry와 solid formula의 원소식이 일치하고 수용액 전하가 보존되는지 입력 검증한다. 이는 반응 경로의 현실성이나 phase identity를 입증하지 않는다.
- 원통 균일성, alloy release mapping, flux law, phase identity 및 입력 데이터의 권리는 caller가 확인해야 한다. 서비스 수명, 손상허용성, 위험 등급, 코드 적합성 또는 실험 qualification을 제공하지 않는다.
- 본 구현은 테스트, benchmark, package build 또는 HPC 실행으로 검증되지 않았다.

# Wet-CO₂ 원통형 stage-coupled scale kinetics

## API

- Model ID: `integration.wet_co2_cylindrical_stage_kinetic_scale_feedback`
- Schema: `matintegrity.wet_co2_cylindrical_stage_kinetic_scale_feedback.v1`
- 입력: `WetCo2CylindricalStageKineticScaleFeedback`
- 상별 law: `WetCo2StageKineticPhase`
- exact-knot 활동도 입력: `WetCo2StageActivityKnot`
- 활동도 곱 term: `WetCo2StageActivityProductTerm`
- 계산 함수: `evaluate_wet_co2_cylindrical_stage_kinetic_scale_feedback`
- provenance source IDs: `caller_activity_driven_stage_scale_kinetics`, `multireactant_cylindrical_supply_and_inventory_limiter_at_bdf_stages`

## 계산 계약

이 모델은 원통 방사 유한체적 BV 수송 ODE의 BDF 각 stage에서 wall-adjacent aqueous 농도를 읽어 활동도곱 `Q`와 caller가 제공한 natural `ln(Ksp)`를 계산한다. 초포화에서는 caller `k_precipitation * max(ln(Q/Ksp), 0)^n`을, 미포화에서는 caller `-k_dissolution * max(-ln(Q/Ksp), 0)^m`을 사용한다. 두 속도는 각 caller finite flux cap에 의해 제한된다. 양의 값은 고체 생성, 음의 값은 고체 용해다. Activity coefficient와 기준농도는 각각 caller가 제공하며 `gamma*c/c_ref`를 무차원 activity로 해석한다.

그 순간의 rate는 same-stage BV source/sink와 나란히 ODE에 들어간다. 반응식은 양의 stoichiometric coefficient를 침전 때 소비되는 수용액 종, 음의 값을 생성되는 종으로 해석한다. 상 반응식의 charge balance와 고체 원소식 일치를 입력 단계에서 확인한다. caller의 `log(Ksp)`, 활동도계수, rate 상수, 반응차수, 최대 flux, phase formula 및 Evidence가 입력이며 모델이 물성이나 상 정체성을 추론하지 않는다.

각 stage에서 모든 상이 소비하는 동일 aqueous reactant의 총량을 합산해 cylindrical radial supply cap을 적용한다. 침전 flux 전체가 이 공급량을 초과하지 않게 phase rate를 제한한다. 용해 flux는 stage의 현재 solid inventory와 interval 잔여시간으로 제한하여 재고 음수화를 막고, 마지막에 재고 음수 또는 계산 불안정이 남으면 fail-closed 한다. BV transport와 scale kinetics는 같은 aqueous stage 농도를 사용하며, 그 결과 profile과 phase inventory는 다음 exact knot 및 moving-geometry remap으로 이어진다.

Caller activity schedule, `log(Ksp)` 및 경계조건은 exact knot의 왼쪽 값을 interval 전체에 고정한다. 농도와 반응속도는 BDF stage마다 달라진다. 제한된 outer Picard loop는 이 stage-integrated scale inventory와 BV metal release로 원통 bore/steel radius를 다시 계산한다. 지정 반경 허용오차를 달성하지 못하면 완료 계산으로 반환하지 않고 iteration/interval prefix를 반환한다.

## 반환 장부 및 적용 한계

각 interval은 exact geometry radius, RHS stage evaluation budget, time-averaged 상별 flux, endpoint saturation ratio, aqueous boundary/BV/scale transfer, 종별 aqueous 잔차, charge·원소·electronic-charge 잔차 및 moving-mesh sweep 기록을 반환한다. Exact-knot history에는 phase inventory, solid 원소 inventory와 누적 wall element release가 들어간다. 최종 geometry path에는 steel/bore radius와 alloy-release geometry residual이 포함된다. Caller kinetic/activity records, source IDs, input digest와 geometry digest로 lineage를 남긴다.

속도식은 로그 supersaturation/undersaturation의 거듭제곱 형태 중 caller가 선택한 한 가지 parameterization이다. 보편적인 침전 법칙이 아니다. 온도·pH·이온강도 의존성은 caller가 knot별 계수에 반영해야 한다. 핵생성, metastability, 다른 상 경쟁의 열역학 선택, scale porosity/내부 확산, gas dissolution, complexation/speciation, surface blocking은 모델링하지 않는다. BV 분기와 scale 반응은 각 interval의 유한체적 수송과 결합되지만, 이 API가 물리 qualification이나 안전성 판정을 제공하지 않는다.

이 소스는 새로 작성된 코드이며 아직 테스트, benchmark, 패키지 빌드 또는 HPC 계산으로 검증되지 않았다.

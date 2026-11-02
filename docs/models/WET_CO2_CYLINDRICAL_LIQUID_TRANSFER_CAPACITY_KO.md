# 원통형 액상 물질전달 용량 이력

## 목적/API

`integration.wet_co2_cylindrical_liquid_transfer_capacity_history`는 계산된 원통형 단상 pipe hydraulics를 기존 pointwise `wet_co2_liquid_side_mass_transfer` 상관식과 연결하고, 그 계수를 실제 원통형 보어의 전 벽면적으로 확장한다. 기존 correlation을 새로 만들거나 바꾸지 않는다.

- 계약: `WetCo2CylindricalLiquidTransferCapacityHistory`
- knot 물성 계약: `WetCo2CylindricalLiquidDiffusivityKnot`
- 평가 함수: `evaluate_wet_co2_cylindrical_liquid_transfer_capacity_history`
- catalog 명세: `specifications()`

입력 hydraulics 결과와 geometry result는 정확한 동일 geometry 해시 및 시간점을 가져야 한다. 매 knot마다 corrosive species ID, 용액 분자확산계수, source record와 Evidence를 제공한다. 해당 correlation의 single-phase pipe, turbulent shear, liquid wetting/area basis, property identity, friction exponent 및 Schmidt range review gate를 연결한다. Reynolds number가 correlation 요구 영역 밖이면 기존 pointwise evaluator의 상태를 그대로 전달한다.

## 계산 및 적분

각 knot에서 기존 liquid-side evaluator를 호출하며, 보어의 전 둘레가 액상에 젖었다고 가정한 벽면적을 `A_w=2πr_b L`로 계산한다. 전달 conductance는 `G=k_L A_w` (m³/s)다. 다음 knot까지는 caller review 하에 `G`를 왼쪽 knot 값으로 유지하고 interval exposure `E=G Δt` (m³)를 계산한다. 이 시간 적분은 농도차가 없는 conductance 노출량이며 몰수 또는 반응 플럭스가 아니다.

유량 부호가 역방향이거나 영유량이면 이 상관식에 맞지 않으므로 계산이 중단된다. hydraulics 출력의 liquid density/viscosity와 원 요청 diffusivity record를 결합하고, 모든 correlation 결과 digest를 보존한다.

## 범위 제한

이 모듈은 기존 correlation이 설정한 유동/Schmidt 범위와 제한을 그대로 따른다. 새로운 유동 상관식, 보간 또는 extrapolation을 추가하지 않는다. 유체 전체 단면이 액상이라는 단상 가정만 처리한다. 기체-액체 holdup, wetting fraction, 계면면적, 반응, carbonate chemistry, speciation, wall consumption, 부식률 및 수명을 계산하지 않는다. pressure drop/flow regime 역시 upstream steady hydraulics 모델의 한계와 가정을 이어받는다. interval에서 area와 kL은 왼쪽 knot 값으로 처리한다.

## 계보/검증 상태

source IDs: `caller_cylindrical_steady_hydraulics_result`, `caller_liquid_species_diffusivity_record`, `caller_cylindrical_segment_wetted_area_geometry`, `registered_liquid_side_mass_transfer_correlation`. upstream geometry, hydraulics, pointwise correlation, diffusivity record digest를 유지한다.

구현과 설명서만 추가했으며 테스트, 패키징, HPC 검증은 수행하지 않았다. 후속 검증은 기존 pointwise evaluator와 knot별 값 일치, 원통 벽면적 차원/값, 일정 조건의 cumulative `k_L A Δt`, 시간 knot 불일치, 유동 방향 역전·저Re의 거부, Schmidt 범위 gate, 결과/evidence hash 변조 차단을 확인해야 한다.

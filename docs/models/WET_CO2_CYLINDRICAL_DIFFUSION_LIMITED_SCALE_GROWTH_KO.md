# 원통형 확산 제한 스케일 성장 장부

## 목적과 API

`integration.wet_co2_cylindrical_diffusion_limited_scale_growth`는 caller가 선택한 한 고체상에 대해 기존 원통형 saturation→surface kinetics가 산출한 석출률을 원통형 다층 확산의 반응물 공급 한도로 제한한다. 활동도, Ksp, 고체 선택, kinetics 파라미터는 새로 추정하지 않는다.

- 입력 계약: `WetCo2CylindricalDiffusionLimitedScaleGrowth`
- 입력 하위 자료: `WetCo2DiffusionLimitedSolidReactant`, `WetCo2DiffusionLimitedBulkKnot`
- 실행 함수: `evaluate_wet_co2_cylindrical_diffusion_limited_scale_growth`
- 카탈로그 명세: `specifications()`

입력에는 계산 완료 상태의 geometry, multilayer transport resistance, wall saturation/scale kinetics 결과가 필요하다. 각 결과의 `model_id`, 원통 geometry 결과 digest, 전체 knot 시간이 맞는지 확인한다. 고체 ID는 saturation adapter의 선택과 같아야 한다. 반응물 농도는 각 knot별 caller bulk record로 전달하고 digest 및 사용허가 Evidence로 묶는다. 침전 반응물 계수는 고체 1 mol을 생성할 때 소비되는 각 수용종 mol 수로 명시하며 전체 계수표 digest를 제공한다.

## 계산

각 수용종 `i`의 inward 공급 상한은 `J_i = k_i max(C_bulk,i - C_wall,i, 0)`이다. 고체 생성 속도의 확산 상한은 `J_s,max = min_i(J_i / ν_i)`이며, 결과 석출 속도는 caller kinetics의 석출 속도와 이 상한 중 작은 값이다. caller kinetics의 용해 속도는 변경하지 않고 순 성장 속도에서 뺀다.

knot 속도는 검토 플래그가 승인한 대로 다음 knot까지 왼쪽 knot에서 일정하다고 둔다. 축방향 단위 길이당 고체 몰수 증분은 `J_net × 2π r_b × Δt`로 적분한다. 결과에는 각 knot의 확산 제한 석출/용해 속도, 종별 공급 제한, phase 재고, 입력 geometry 상 재고와의 차이를 기록한다. 기준 재고는 시작 geometry의 해당 상 몰수다.

## 한계와 안전한 해석

이것은 고정 geometry 위의 operator-split diagnostic ledger다. 계산 중 수송 계수, saturation, 반응 속도, scale 두께 및 geometry를 다시 갱신하지 않는다. 그래서 geometry 재고와 장부 재고의 차이는 자동 수정하지 않고 비교 자료로 남긴다. 증착률이 instantaneous inner wetted area 기준인지 검토가 필요하다. 용해가 해당 상의 누적 재고를 음수로 만들면 해당 구간에서 범위 밖 결과를 반환한다.

반응 균형, 활동도, 종 선택, 다상 상호작용, 용액 speciation, 표면 피복, porosity, 수송의 transient 저장, 시간 적응 및 재료 성능 검증은 제공하지 않는다. 한 고체상과 caller 선언 반응물 계수만 다룬다. 결과는 안전성 판정, 수명 또는 현장 성능 보증이 아니다.

## 계보와 검증 현황

source IDs: `caller_wet_co2_cylindrical_scale_geometry_result`, `caller_wet_co2_cylindrical_multilayer_transport_result`, `caller_wet_co2_wall_saturation_scale_kinetics_result`, `caller_balanced_solid_precipitation_consumption_stoichiometry`. 각 upstream Calculation, bulk-knot, 반응물 계수 digest를 결과에 보존한다.

구현과 문서만 추가했으며 테스트·패키징·HPC 검증은 실행하지 않았다. 후속 검증은 단일 반응물 cap의 무제한/공급제한 양 끝, 복수 반응물 중 최솟값 선택, bulk 농도가 wall보다 낮은 경우 무공급, kinetics 석출량보다 큰 제한 flux가 나오지 않는 조건, 용해 재고 고갈, 면적기준 단위 및 exact-knot/geometry digest 불일치를 다뤄야 한다.

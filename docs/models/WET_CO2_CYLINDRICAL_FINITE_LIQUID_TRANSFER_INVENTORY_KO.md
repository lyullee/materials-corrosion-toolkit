# 원통형 구간 bulk–wall 액상 유한재고 전달 장부

## 목적/API

`integration.wet_co2_cylindrical_finite_liquid_transfer_inventory`는 기존 원통형 액상 transfer conductance history와 caller가 제공하는 bulk/wall 농도·액체부피를 결합해 종별 분자 몰 전달량과 유한 재고 폐쇄를 계산한다. 새 물질전달 상관식이나 화학 평형은 추가하지 않는다.

- 요청 계약: `WetCo2CylindricalFiniteLiquidTransferInventory`
- 농도 knot: `WetCo2CylindricalLiquidConcentrationKnot`
- 외부 inventory 교환 구간: `WetCo2CylindricalExternalLiquidExchange`
- 평가 함수: `evaluate_wet_co2_cylindrical_finite_liquid_transfer_inventory`
- 카탈로그 명세: `specifications()`

기하, 수력, 기존 transfer conductance 결과는 계산 완료 상태여야 한다. 세 결과의 geometry digest가 같고 시간점이 정확히 정렬되어야 한다. 종 ID와 농도 단위 mol/m³가 명시되며, 매 knot의 bulk/wall 농도 및 부피 기록은 Evidence로 고정한다. 각 interval의 외부 bulk 및 wall 재고 변화도 부호를 가진 signed mol 단위로 입력하고 digest/Evidence로 고정한다. 외부 교환 기록은 0에서 마지막 시간까지 각 인접 knot 구간을 빠짐없이 덮는다.

## 전달 및 재고식

`G`는 upstream에서 이미 계산한 segment-level transfer conductance (m³/s)다. 농도차는 `ΔC=C_bulk−C_wall`이고, signed 전달률을 `n_dot=G ΔC` (mol/s)로 둔다. 양수는 bulk에서 wall 방향이다. 다음 knot까지 왼쪽 knot의 conductance와 농도차를 고정하고 `Δn=n_dot Δt`를 적분한다.

외부 bulk/wall inventory 변화량을 각각 `S_b`, `S_w`라 하면 구간 끝 재고는 다음과 같다.

- `N_b,new = N_b,old + S_b − Δn`
- `N_w,new = N_w,old + S_w + Δn`

여기서 `N=C V`로 각 compartment 유한 몰수를 계산한다. 어느 쪽 재고가 허용 오차 이상 음수가 되면 계산을 중지한다. 다음 knot에서 caller 농도×부피 값이 계산 재고와 허용오차 안에서 일치하는지도 확인한다. 전체 bulk+wall 잔차는 초기 총 재고와 모든 외부 교환 합에 대해 계산한다. 내부 전달은 두 compartment 사이에서만 이동하므로 전체 잔차에서 상쇄된다.

## 범위와 한계

모델은 하나의 caller 선언 종, well-mixed bulk compartment 하나, wall liquid compartment 하나를 계산한다. 부피가 변해도 caller가 제공한 knot별 농도·부피가 이전 재고 및 외부 교환과 일치해야 한다. 반응, speciation, 기상-액상 전달, 흡수, 침전, wall 소비를 추론하지 않으며 이를 포함하려면 해당 원천/소모량을 외부 exchange 기록으로 제공해야 한다. 시간구간 중 변화는 왼쪽 고정이며, chemistry의 완전한 수지와 동일하지 않다. 고갈·상태 불일치·closure 위반을 자동 보정하지 않고 fail-closed 한다.

## 계보 및 검증 상태

source IDs: `caller_cylindrical_liquid_transfer_capacity_history`, `caller_cylindrical_geometry_history`, `caller_cylindrical_hydraulics_history`, `caller_bulk_wall_liquid_concentration_records`, `caller_bulk_wall_external_inventory_exchange_records`, `finite_two_compartment_liquid_transfer_balance`. 모든 상위 결과 digest, 농도 knot와 외부 교환 기록 digest를 유지한다.

코드와 문서만 작성했으며 테스트, 패키징, HPC 검증은 실행하지 않았다. 후속 검증은 ΔC=0, 양/음 방향 전달 부호, 고정 농도/부피의 해석해, 양측 compartment 고갈 경계, 외부 유입/유출에 의한 closure, volume 변화와 concentration consistency, exact-knot 및 upstream geometry/hydraulic hash mismatch를 포함해야 한다.

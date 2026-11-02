# 유한 액상재고와 혼합전위 전극 반응의 구간 결합

## 목적/API

`integration.wet_co2_finite_inventory_electrode_mixed_potential`은 원통형 구간의 기존 liquid-transfer conductance를 통해 이동하는 종과 양쪽 유한 액상 재고, caller Butler–Volmer 반응 가지의 공통 혼합전위를 하나의 interval ledger에서 결합한다. 기존 steady radial sink/BV 모델의 고정 bulk 경계 대신 각 구간에서 bulk 및 wall liquid 재고가 소진되거나 외부 source/sink를 받는 상태를 보존한다.

- 요청: `WetCo2FiniteInventoryElectrodeMixedPotential`
- 종: `WetCo2LumpedElectrochemicalSpecies`
- 초기 재고: `WetCo2LumpedElectrochemicalInitialInventory`
- interval 반응: `WetCo2LumpedElectrochemicalInterval`, `WetCo2LumpedElectrochemicalReaction`
- 외부 재고 변화: `WetCo2LumpedElectrochemicalExternalExchange`
- 평가: `evaluate_wet_co2_finite_inventory_electrode_mixed_potential`
- 명세: `specifications()`

입력 geometry 결과, 각 종의 기존 cylindrical liquid transfer-capacity 결과, 정확히 일치하는 bulk/wall compartment 부피 knot, 초기 유한 재고, 외부 유입/유출, interval별 electrode reaction calibration을 요구한다. 고체/수용종 원소식과 전하수지는 입력 reaction 방향 convention에 맞춰 확인한다.

## 구간 계산

각 interval 시작점에서 현재 `N/V`로 bulk/wall 농도를 계산하고 기존 conductance `G`로 `Q=G(C_bulk−C_wall)` (mol/s)를 얻는다. positive `Q`는 bulk에서 wall 방향이다. BV branch current들은 공통 calibration-potential bracket 안에서 평가된다. 각 anodic/cathodic 소비 가지는 전극 반응 전 wall 재고(초기 재고 + caller 외부 변화 + interval transfer)에 의해 해당 interval에서 제한된다. 이 branch 공급제한을 포함한 총 current가 0이 되는 전위를 bisection으로 찾는다.

혼합전위에서 각 반응의 signed extent와 종별 변화량을 segment wetted area×interval duration으로 구하고, transfer·외부 교환과 함께 두 reservoir 재고를 갱신한다. 총 종 재고 변화와 외부 source/sink + 전극 반응 변화가 지정오차 내에 맞아야 다음 구간으로 넘어간다. 어느 reservoir가 음수가 되거나 전극 반응 뒤 재고가 소진되면 실패한다. Geometry/time/transport 입력은 exact knot만 쓰며 각 interval의 flow, area 및 branch calibration은 고정한다.

## 제한

이 모델은 radial cell profile, transient radial diffusion PDE, electrolyte activity/speciation, kinetic phase saturation, scale diffusion/reaction, scale 성장·부착·박리를 해석하지 않는다. 기존 transfer-capacity가 제공하는 whole-segment conductance와 두 well-mixed 액상 구획으로 단순화한다. Branch 제한은 finite interval stock budget 기반의 lumped cap이며 실제 diffusion-layer 전위/농도 분포가 아니다. Reaction exchange current, equilibrium potential, stoichiometry, external exchange 및 fluid properties는 전부 caller calibration/data다. 혼합전위와 재고 폐쇄가 계산되어도 부식률·수명·현장 성능은 보증되지 않는다.

## 계보와 검증 상태

source IDs: `caller_cylindrical_liquid_transfer_capacity_history`, `caller_cylindrical_geometry_result`, `caller_calibrated_butler_volmer_branch_set`, `caller_finite_bulk_wall_liquid_inventories`, `caller_interval_external_liquid_sources_sinks`, `finite_reservoir_species_limited_mixed_potential_ledger`. 각 상위 결과 digest와 initial/external record Evidence, reaction calibration digest를 추적한다.

구현·문서만 추가했으며 테스트, 패키징, HPC 계산은 실행하지 않았다. 후속 검증에는 두 branch의 단순 BV zero-current root, 제한이 없는 충분 재고 한계, 반응물 유한재고가 제한한 경우의 branch factor, transfer 방향 역전, 두 reservoir 고갈, reaction charge/element 불일치, pressure/calibration/time/geometry digest mismatch, interval별 종 질량수지 closure가 포함돼야 한다.

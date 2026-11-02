# 크리비스 벽면 species flux의 누적 inventory

## 목적

`crevice_multispecies_wall_flux_callback`가 제공하는 독립 species별 벽면 경계 flux를, caller가 준 bulk concentration 이력 및 geometry history와 결합해 셀별·구간별 이동 몰수로 적분한다. 결과는 wall boundary를 통해 용액에 들어오거나 빠져나간 species 양의 장부다.

## API

- Python 모듈: `matintegrity.crevice_wall_flux_inventory_history`
- 입력 계약: `CreviceWallFluxInventoryHistoryRequest`
- 계산: `evaluate_crevice_wall_flux_inventory_history()`
- ModelSpec: `specifications()`
- model ID: `integration.crevice_wall_flux_inventory_history`
- source ID: `caller_crevice_wall_flux_to_species_inventory_history`

입력은 기존 `CreviceMultispeciesWallFluxRequest`, geometry와 정확히 정렬된 bulk 농도 배열 `[knot][species][cell]`, 그리고 그 배열의 canonical SHA-256다. 각 concentration은 `mol/m3`이며 유한하고 음수가 아니어야 한다. species 순서는 callback 요청의 `transport_species_order`와 같다.

## 적분 방법

각 시간 구간 안에서 다음 변수를 선형으로 재구성한다.

- calibrated wall transfer velocity `k` (`m/s`)
- wall surface equilibrium concentration `C_s` (`mol/m3`)
- bulk concentration `C_b` (`mol/m3`)
- wall-area density `a_w` (`m2/m3`)
- cell cross section `A` (`m2`)

기존 callback의 부호 약속을 따라 inward flux는 `J = k * (C_s - C_b)` (`mol/(m2 s)`)다. 셀 벽면적은 `a_w * A * dx`로 계산한다. 그러면 셀별 물질 이동 속도는 `J * a_w * A * dx` (`mol/s`)이고, 그 시간 적분이 결과 mol이다.

다섯 양을 선형으로 둔 경우 flux 항은 최대 2차, 면적은 최대 2차, 곱은 최대 4차 다항식이다. 3점 Gauss-Legendre 적분은 최대 5차 다항식까지 정확하므로 이 선언된 경로에는 적분 오차가 없다. 입력 이력이 선형이 아니거나 구간 내 반응/경계 거동이 비다항이면 이 정확성 주장은 적용되지 않는다.

## 결과 해석

`intervals[].net_wall_transfer_mol_by_species_cell`은 각 정확한 geometry 구간에서 종별·셀별 순 이동량이다. 양수는 용액으로 유입, 음수는 용액에서 벽으로 유출이다. `net_wall_transfer_mol_by_species`는 셀 합이며 최상위 결과에는 전 시간 구간 합도 있다. 완료 prefix와 첫 실패 구간을 유지해 부분 결과를 추적한다.

## 입력 검토와 한계

요청에는 공통 clock/species/cell mapping, bulk 농도의 구간 선형 경로, geometry 기반 벽면적 계산, flux 부호 및 결과가 반응 extent가 아니라는 점을 각각 caller가 검토했다는 표시가 필요하다. geometry의 셀 폭, cross section, wall-area density는 양의 유한값이어야 한다.

이 API는 callback 입력과 bulk 이력을 적분할 뿐 transport 방정식을 풀지 않는다. 별도 종의 wall transfer가 독립적이라는 기존 callback 가정을 유지하며 표면 반응량, 금속 손실, 전하/원소 반응 closure, 침전량 또는 부식속도로 해석할 수 없다. 단위, callback parameter 및 geometry 상관의 물리적 타당성과 적용범위는 caller가 확인해야 한다. SHA-256은 입력 계보 및 무결성 확인용이며 모델 검증을 대신하지 않는다.

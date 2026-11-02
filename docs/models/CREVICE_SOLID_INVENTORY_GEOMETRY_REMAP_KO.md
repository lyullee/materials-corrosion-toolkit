# 크리비스 고체 inventory의 geometry 경계 remap

## 목적

이 모듈은 고정 geometry에서 계산된 셀별 고체상 농도를, 정확히 같은 시간의 새 geometry 상태에 맞는 고체상 초기농도로 변환한다. 셀·상별 고체 몰수는 보존하고, 기준 면적당 액체 체적 변화에 따라 `mol/m3` 정규화만 바꾼다.

이 계산은 움직이는 geometry 해석기나 고체반응 solver가 아니다. 기존 kinetics 결과와 별도 geometry history를 하나의 operator-split 경계에서 이어 주는 제한된 adapter다.

## API 및 식별자

- Python 모듈: `matintegrity.crevice_solid_inventory_geometry_remap`
- 입력 계약: `CreviceSolidInventoryGeometryRemapRequest`
- evaluator: `remap_crevice_solid_inventory_at_geometry_boundary()`
- ModelSpec 제공자: `specifications()`
- model ID: `integration.crevice_solid_inventory_geometry_boundary_remap`
- source ID: `caller_crevice_solid_inventory_immobile_geometry_remap`

입력은 typed `CompetingSolidKineticTransport` campaign, 해당 campaign 결과와 canonical SHA-256, target geometry history 및 digest, 정확한 target state index다. 결과가 계산 완료 상태이고 campaign·scope·입력 digest·고체상 순서에 연결되며 upstream inventory balance가 허용오차를 만족해야 한다.

## 변환

기준면적당 셀 액체체적은 다음과 같다.

`v_i = (A_i / A_ref) * dx_i`  (`m3/m2`, 즉 m)

각 셀 `i`의 고체 농도 `c_i` (`mol/m3`)를 기준면적당 inventory로 바꾼다.

`n_i = c_i * v_i`  (`mol/m2`)

target geometry의 해당 셀 기준면적당 체적 `v_i,target`에 대해 새로운 초기농도는 다음과 같다.

`c_i,target = n_i / v_i,target`  (`mol/m3`)

따라서 geometry 경계 양쪽에서 셀·고체상별 `mol/m2` inventory를 보존한다. 출력의 `target_initial_solid_inventory_mol_m3_by_phase`는 다음 `CompetingSolidKineticTransport.initial_solid_inventory_mol_m3_by_phase`에 넣을 수 있다. 새 campaign 생성과 다음 계산 구간 실행은 caller가 수행한다.

## Fail-closed 조건 및 검토 입력

아래 네 가지를 사용자가 검토해 명시해야 계산한다.

- 고체상이 같은 축방향 셀에 남는다는 가정
- source와 target geometry 시간이 정확히 일치한다는 대응
- 기준 면적 및 셀 체적 기준이 동일하다는 점
- remap 순간에 고체 생성·소실이 없다는 점

또한 source/target의 셀 수, 폭 배열, 기준 단면적 및 고체상 순서가 일치해야 한다. target geometry는 각 셀에 유한한 양의 단면적이 있어야 한다. 시간이나 grid 불일치, 누락된 검토, 손상된 inventory 필드는 각각 범위 제외 또는 추가 데이터 상태로 반환한다.

## 한계와 후속 결합

- 정적 source campaign에서 계산한 고체상 분포만 받는다.
- remap은 같은 cell 안에서 고체 몰수를 보존한다. 셀 간 고체 이동, 벽면 침착 재배치, 용해, 석출, 상변화, 유동에 의한 고체 제거는 계산하지 않는다.
- target geometry의 시간 변화와 고체 상태 사이를 보간하지 않는다. 동일한 단일 시간 상태만 허용한다.
- target 고체 농도는 target geometry의 액체 체적을 분모로 삼는다. 고체 자체가 차지하는 체적이나 공극률·형상 변화를 따로 모델링하지 않는다.
- 결과는 geometry/kinetics의 완전 결합 해가 아니다. 각 고정 geometry 구간의 campaign 사이에서 사용자가 경계 remap으로 적용한다.
- 입력 결과 digest는 데이터 무결성/계보 확인용이며 과학적 타당성이나 독립 검증을 증명하지 않는다.

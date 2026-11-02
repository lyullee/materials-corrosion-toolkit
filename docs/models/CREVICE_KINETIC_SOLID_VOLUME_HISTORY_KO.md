# 크리비스 kinetic solid inventory에서 고체 체적 이력으로 변환

## 역할

기존 `CompetingSolidKineticTransport` 결과의 셀별 고체 inventory 농도(`mol/m3 solution`)를 고정 geometry 수송 셀 체적을 이용해 기준면적당 inventory(`mol/m2 reference area`)로 바꾸고, caller가 제공한 phase별 solid molar volume을 기존 `crevice_solid_volume_inventory` evaluator에 전달한다.

이 API는 kinetic rate나 aqueous transport를 다시 풀지 않는다. 입력된 계산의 고체 상태를 더 자연스러운 geometry/체적 downstream API가 사용할 수 있게 단위 변환한다.

## API

- 모듈: `matintegrity.crevice_kinetic_solid_volume_history`
- 입력: `CreviceKineticSolidVolumeHistoryRequest`
- 계산: `convert_crevice_kinetic_solid_volume_history()`
- ModelSpec: `specifications()`
- 모델 ID: `integration.crevice_kinetic_solid_volume_history`
- source ID: `caller_crevice_kinetic_solid_inventory_to_solid_volume`

요청은 typed `CompetingSolidKineticTransport`, 전체 raw kinetic transport 결과와 SHA-256, phase ID별 solid molar volume, 해당 값 Evidence 및 4개 review gate를 갖는다. 입력 결과 digest, campaign digest, campaign ID, physical scope, phase order, exact transport clock와 고체 inventory closure를 확인한다.

고정 geometry만 허용한다. 셀 체적 per reference area는 `cell_cross_section / reference_cross_section * cell_width`로 계산한다. 단면적이 지정되지 않았다면 kinetic transport의 상수 단면 기준(`area ratio=1`)을 사용한다. 각 phase의 셀별 areal inventory는 다음 단위 변환이다.

`n_areal[i, cell] = c_solid[i, cell] * (V_cell / A_reference)[cell]`

`c_solid`는 `mol/m3 solution`, 괄호 항은 `m3 solution/m2 reference area`, 결과는 `mol/m2 reference area`다. 이후 기존 `CreviceSolidVolumeInventory` evaluator가 `mol/m2 * m3/mol = m3/m2`로 변환한다.

## 결과와 다음 단계

성공 결과의 `solid_volume_history`는 시간 knot마다 원 phase 상태 digest, 셀별 `mol/m2` inventory, 기존 solid-volume evaluator의 전체 결과와 result digest를 보존한다. 각 row의 `elapsed_time_s`, `solid_volume_result`, `solid_volume_result_sha256`를 `CreviceDepositionVolumeKnot` 입력으로 옮기면 이전 `crevice_deposition_aperture_history` API로 연결할 수 있다. 그 뒤 deposition geometry bridge와 기존 operator-split transport campaign이 가능하다.

계산 오류가 발생하면 완료한 exact knot prefix와 첫 실패 knot/phase를 남긴다. 고체 inventory closure가 upstream 허용오차 안에 있지 않거나 geometry가 움직이는 경우 닫힌다.

## 한계

Molar volume은 caller가 선언한 각 phase의 현재 상태에 맞아야 한다. 코드가 polymorph, 조성, 온도/압력 의존성, 고체의 용액 내 실제 밀도, 소실된 고체상 또는 source license를 결정하지 않는다. 반응/수송이 아니라 inventory 단위 환산이므로 kinetics나 phase selection을 새로 수행하지 않는다.

결과는 기준면적당 compact-solid 체적의 등가값이다. 이것을 aperture 손실로 바꾸려면 앞서 제공한 deposition mapping API의 wall side count, coverage 및 geometry review가 필요하다. Morphology, porosity, adhesion, 침전 위치, 표면 피복률, aperture 폐쇄, corrosion protection, acceptance 또는 qualification을 이 모델이 추론하지 않는다.

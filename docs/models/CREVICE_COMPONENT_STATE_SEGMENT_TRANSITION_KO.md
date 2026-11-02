# Crevice component-state BDF 고정 형상 segment transition

## 목적과 적용 범위

`integration.crevice_component_state_segment_transition`은 하나의 committed component-state BDF segment가 끝난 뒤, caller가 제공한 다음 segment geometry를 넣어 새 BDF 요청을 구성한다. 전 segment의 최종 conserved-component 몰수를 셀별로 그대로 다음 요청의 초기 inventory에 넣는다. 농도값을 새 체적으로 재정규화하지 않는다.

이 operator-split 경로는 caller가 각 segment 경계의 aperture·volume·face area·center spacing을 산출하고 Evidence와 digest로 고정한다. 이 API가 침전량이나 금속 손실에서 aperture를 계산하는 것은 아니다. BDF interval/RHS 내부의 moving-boundary coupling 또는 monolithic transport-chemistry-hydraulic solve도 아니다.

## 입력

- 정확한 `CreviceComponentStateBDFRequest`와 계산 전체 digest가 일치하는 `computed`, `committed` 결과. `all_component_ledgers_close`도 true여야 한다.
- 다음 고정 geometry template: 대상 clock 첫 knot는 직전 결과의 최종 knot와 정확히 같아야 한다. 셀 ID와 순서는 유지한다.
- caller geometry receipt: 셀별 길이·폭·aperture·용액부피 및 interior-face area/center distance를 제공하고 전체 배열 digest를 Evidence로 고정한다. 각 셀의 `volume_L = length × width × aperture × 1000`을 확인한다.
- source commitment, conserved-component basis continuity, geometry transition review를 선언한다.

## 출력과 실행 절차

출력의 `next_segment_bdf_request`는 다음 solver 호출에 넘길 typed BDF request다. 이 요청은 caller template의 다른 solver 옵션을 보존하면서 source result의 최종 component mole vector를 `initial_component_inventory`로 치환한다. `next_segment_request_ready`는 입력 구성/정합 확인을 뜻하며, 다음 segment의 계산 완료나 physical qualification을 뜻하지 않는다.

1. caller가 현재 geometry에서 BDF를 계산한다.
2. source 계산이 committed이고 모든 component ledger가 닫혔는지 확인한다.
3. 별도 geometry/provider가 다음 구간의 geometry와 boundary를 산출하고 digest/Evidence를 제공한다.
4. transition API가 다음 BDF 입력을 구성한다.
5. 다음 segment를 별도로 계산한 뒤 반복한다.

## 보존과 한계

전환 경계에서 component moles는 셀별로 정확히 이어진다. 체적은 달라도 초기 mole inventory는 보존되므로 다음 구간 농도는 새 geometry와 평형 계산에서 결정된다. 이 모듈은 같은 셀 ID/순서와 같은 component basis를 요구하며, cell split/merge나 cross-cell remap을 수행하지 않는다. geometry provider, 압력-유동 feedback, 반응·상 탐색, nucleation kinetics, 물리 실험 검증 및 qualification은 포함되지 않는다.

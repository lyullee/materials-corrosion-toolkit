# 외부 접촉 해석 응답으로 단일 전이 근 구간 좁히기

## 목적과 범위

이 독립 API는 이미 계산된 가스켓 접촉 이력의 한 전이 bracket을 받아, caller가 지정한 스칼라 응답이 부호를 바꾸는 **한 개의 caller-reviewed root bracket**만 이분 축소한다. 중간 시각 응답은 외부 FE/contact solver callback이 계산한다. 이 모듈은 solver, 구조 모델, 재료 법칙, solver 설정 또는 해석의 수렴·물리적 타당성을 제공하지 않는다.

계산은 선택된 두 endpoint의 응답이 유한하고 서로 반대 부호이며, 해당 bracket 안에 연속인 단조 단일 근이 있다는 caller review가 있을 때만 의미를 가진다. 같은 상태의 endpoint 사이에 숨어 있는 접촉 전이를 찾아내거나, 여러 근을 탐색하거나, 단조성을 입증하지 않는다.

## Python API

모듈 위치: `matintegrity.models.gasket_contact_root_localization`

- 요청 계약: `GasketContactRootLocalization`
- 외부 질의 계약: `ContactResponseQuery`
- 외부 결과 영수증: `ContactResponseReceipt`
- 함수: `localize_gasket_contact_response_root(request, *, contact_response_provider=...)`
- callback 형식: `provider(query) -> ContactResponseReceipt | dict`

중앙 registry, schema, catalog, 패키지 export는 이 독립 추가 범위에 포함하지 않았다.

## 입력과 계보

요청은 `fabrication.gasket_contact_transition_brackets`의 계산 완료 결과와 그 canonical SHA-256을 요구한다. `node_id`, 하한/상한 시각은 해당 결과의 transition bracket 하나와 정확히 일치해야 한다. 결과 input digest, 물리 범위, RunContext, 원 contact-history digest를 함께 고정한다.

양 endpoint마다 provider 영수증을 입력한다. 영수증에는 정확한 질의 digest, 원 bracket 및 contact-history digest, 물리 범위와 RunContext, node, 시각, caller가 정의한 응답 ID·단위·스칼라 값, provider ID/revision/configuration digest, 외부 solver result digest, `Evidence`, 결과 canonical digest가 있어야 한다. endpoint 영수증도 동일한 provider 설정과 요청 범위를 사용해야 한다. endpoint 응답 값은 strict opposite sign이어야 한다.

모든 중간 질의는 정확한 중점 시각으로 생성되며 bracket·history·RunContext·node·응답 정의·단위·provider identity/revision/configuration digest를 포함한다. callback 응답은 해당 질의 digest와 모든 필드를 동일하게 되돌려야 한다. `Evidence` 중 하나는 declared `provider_id`를 source로 식별해야 한다. `solver_result_sha256`는 callback 소유 계산 결과의 digest이며, 이 모듈은 그 FE 결과를 재계산하거나 검증하지 않는다.

## 종료 및 실패 동작

각 중간점에서 응답이 반대부호 bracket의 어느 쪽에 속하는지에 따라 그 쪽 endpoint를 갱신한다. 중간 응답값이 현재 endpoint 응답값 범위를 벗어나면 선언된 단조 응답과 일치하지 않으므로 즉시 중지한다. bracket 시간 폭이 요청 tolerance 이내가 되면 축소된 두 endpoint, 양 끝 응답값과 receipt digest, 전체 성공 evaluation prefix를 반환한다.

누락된 caller review, provider 예외, 형식·digest·revision·설정 불일치, 응답 시간이나 node mismatch, 단조 endpoint 범위 위반, 부호 bracket 손실, floating-point 중점 축소 실패 또는 evaluation budget 초과는 성공 결과로 포장하지 않는다. 계산은 `needs_data`로 끝나며 마지막 bracket, 성공한 응답 prefix와 첫 실패 이유를 유지한다.

중간점에서 callback이 정확히 0을 반환하면 그 시간과 응답 영수증을 별도 표시한다. 그래도 `event_time_s`와 `root_estimate_time_s`는 제공하지 않으며, 정확한 물리 event time이나 접촉 전이 시각으로 해석하지 않는다. tolerance 종료 결과도 root time을 찍지 않고 유효 bracket만 보고한다.

## 출력의 해석 한계

- 출력은 caller가 선택한 단일 부호변화 구간을 지정 폭으로 축소한 수치 결과다.
- 단조·연속·단일근 가정은 검토된 사실이 아니라 caller-provided review assertion이다.
- 다른 bracket, 숨은 전이, 여러 근 또는 동일 endpoint 상태의 내부 동작은 검색하지 않는다.
- scalar 응답 정의와 부호 의미를 caller가 문서화해야 한다. 이를 자동으로 gap, pressure, contact force 또는 acceptance criterion으로 해석하지 않는다.
- 실링 승인, leakage 합격/불합격, 누설률, 안전성, 확률, 구조 적합성, 잔여 수명 또는 코드 적합성을 추론하지 않는다.

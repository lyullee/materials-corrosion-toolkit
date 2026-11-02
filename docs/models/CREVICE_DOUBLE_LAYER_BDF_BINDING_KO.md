# 크리비스 이중층 전하에서 component-state BDF 연동

## 목적

`integration.crevice_double_layer_to_component_bdf_binding`는 caller가 제공한 전위·활성면적·미분용량 history에서 저장 전하를 다시 계산하고, caller가 제공한 capacitive-current knot schedule이 각 cell/time interval의 저장전하 변화와 일치할 때만 해당 schedule을 component-state BDF 요청에 연결한다. BDF의 독립 validator도 새 요청에 다시 적용해 전류/성분/전하 계약을 재검사한다.

이 API는 Cdl 또는 전극 전위를 풀지 않는다. 입력된 전류 knot 사이에는 기존 BDF 규약에 따라 piecewise-linear current를 사용하며, 확인되는 것은 interval 적분 charge closure다.

## 부호 규약

이중층 기록의 저장 전하는 **전극 쪽 양전하 증가**를 양수로 표현한다. BDF capacitive source는 **전류가 수용액으로 들어가는 방향**을 양수로 정의한다. 그러므로 각 셀/구간에서

`∫ I_cap,aqueous dt = −(Q_electrode,right − Q_electrode,left)`

가 허용 오차 내에서 성립해야 한다. 이 검사는 면적 변화가 포함된 저장 전하 결과와 전류 knot의 사다리꼴 적분을 비교한다.

## 입력과 처리

1. 기존의 검토된 `CreviceComponentStateBDFRequest`를 제공한다. 그 요청에는 capacitive-current schedule이 없어야 한다.
2. BDF와 동일한 정확한 시간 knot 및 ordered cell ID를 갖는 `CreviceDoubleLayerChargeHistoryRequest`를 제공한다. 전위·면적·capacitance curve는 각각 원래 API의 Evidence와 SHA-256 검증을 받는다.
3. 각 knot/cell의 signed current, schedule digest, 라이선스가 있는 Evidence를 제공한다.
4. evaluator는 이중층 history를 재계산한 뒤 모든 interval/cell에서 trapezoidal current charge와 저장 전하 감소량을 비교한다. 하나라도 허용오차를 넘으면 `needs_data`, 요청은 미생성으로 반환한다.
5. 모두 닫히면 typed BDF request에 schedule을 연결하고 BDF request 전체 validator를 다시 실행한다. 반환 Calculation의 `component_state_request`를 이후 BDF 계산 입력으로 사용한다.

## 한계

- 순간적인 `I = dQ/dt` constitutive law는 수용액 solver에 연성되지 않는다. 입력 current history가 주어진 저장 전하 변화와 구간별로 맞는지 확인하는 adapter다.
- 전극 전위, capacitance, 활성면적, Faradaic kinetics를 추론하지 않으며, qualification이나 부식률도 산출하지 않는다.
- Faradaic source 및 ionic face-current schedule이 포함되면 BDF 원래 요청의 knot별 charge-continuity와 적용 범위 검토를 통과해야 한다.
- 시간·cell 순서 불일치, Evidence/digest 오류, charge 불일치 또는 BDF 원 요청 제약 위반은 fail-closed 처리한다.

## API

- Request: `CreviceDoubleLayerBDFBindingRequest`
- Evaluator: `evaluate_crevice_double_layer_bdf_binding`
- Result fields: `component_state_request`, `component_state_request_sha256`, `interval_charge_closure`, `maximum_normalized_charge_residual`

수치 검증과 패키지 빌드는 별도 작업으로 남아 있다.

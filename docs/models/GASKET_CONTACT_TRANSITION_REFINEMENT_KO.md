# 외부 접촉 solver를 이용한 가스켓 전이 구간 축소

## 목적

이 bridge는 이미 계산된 플랜지 접촉 이력에서 관측된 `open`↔`closed` 절점 쌍 하나를 받아, caller가 제공하는 FE/contact solver callback에 중간 시각의 상태를 질의합니다. 검증된 중간 상태에 따라 시간 bracket 한쪽 끝을 갱신해 지정된 폭까지 구간을 좁힙니다.

이 패키지에는 FE solver가 포함되지 않습니다. 외부 provider의 호출, 입력 생성, 단위 변환, 해석 수렴 판단은 caller 책임입니다.

## Python API

- 입력: `GasketContactTransitionRefinement`
- 중간 질의: `ExternalContactStateQuery`
- callback 응답: `ExternalContactStateResponse`
- 계산 함수: `refine_gasket_contact_transition_bracket`
- registry 연결용 사양: `specifications()`
- model ID: `fabrication.gasket_contact_transition_refinement`
- runtime dependency key: `contact_state_provider`

함수는 다음 signature의 provider callable을 받습니다.

```python
provider(query: ExternalContactStateQuery) -> ExternalContactStateResponse | dict
```

## 입력과 계보 확인

입력 bracket은 `fabrication.gasket_contact_transition_brackets`의 계산된 `AssessmentResult`여야 합니다. 요청에는 초기 bracket 결과 digest, 원 contact-history digest, 물리 범위, node ID, 양 끝 상태, 정확한 양 끝 시각을 넣습니다. 함수는 bracket 결과의 input digest와 RunContext, 원 contact-history digest, node별 endpoint 상태까지 대조합니다. 선택한 node/state/time 조합은 원 결과에서 정확히 한 행이어야 합니다.

provider ID, revision, 설정 SHA-256, 양의 시간 허용오차와 최대 평가 횟수도 요청에 고정합니다. provider configuration은 사용 전에 caller가 검토하고 digest를 제공해야 합니다.

각 callback 질의는 다음 digest와 맥락을 포함합니다.

- bracket 결과 및 원 contact-history digest
- 물리 범위, 자산, 위치, 시간 기준, node ID
- 초기 bracket의 상태 방향
- 질의 시간과 provider ID/revision/configuration digest
- RunContext digest

응답은 정확한 질의 시간·node·provider revision·configuration digest와 물리 범위/RunContext를 되돌려야 합니다. 또한 provider를 식별하는 `Evidence`를 포함해야 합니다. `result_sha256`는 응답 계약을 JSON 형식으로 직렬화하고 해당 필드를 제외한 객체의 canonical SHA-256이어야 합니다. 질의 digest가 다르거나 응답 시간 또는 맥락이 다르면 계산은 중단됩니다.

## 계산과 실패 동작

시작 bracket의 폭이 요청 허용오차 이하가 될 때까지 매 반복에서 시간 중점을 계산해 provider에 요청합니다. 검증된 상태가 왼쪽 endpoint 상태와 같으면 왼쪽 끝을, 오른쪽 endpoint 상태와 같으면 오른쪽 끝을 중점으로 갱신합니다. endpoint 사이에 단일 단조 전이만 있다는 caller review가 없으면 provider를 호출하지 않습니다.

누락·digest 불일치·잘못된 시간·provider 예외·방향 모순·평가 예산 소진 시 `needs_data`와 함께 마지막 성공 구간, 성공한 평가 prefix, 첫 실패 이유를 반환합니다. 결과는 성공한 경우에도 **전이 구간**일 뿐이며 `event_time_s`는 항상 `None`입니다.

## 경계

- 연속시간 FE 모델, constitutive law, 접촉 solver, mesh 처리 또는 수렴 기준을 제공하지 않습니다.
- 단조 단일 전이는 caller가 검토해야 합니다. 이 가정이 잘못되면 이분 축소 결과는 유효하지 않습니다.
- provider의 수치 정확도, 모델 적합성 또는 실험 검증을 판정하지 않습니다.
- 실링 합격, 누설률, 구조 건전성, 고장 확률 또는 코드 적합성을 계산하지 않습니다.
- 모듈은 독립 파일로 추가됐습니다. 중앙 registry/schema/catalog와 패키지 연결, 계산 실행 및 검증은 별도 후속 작업입니다.

# 가스켓 접촉 상태 전이 구간 요약

## 목적

이 API는 기존 플랜지 접촉 이력 계산의 각 절점 결과에서 `open`과 `closed` 상태가 바뀐 구간을 찾습니다. 입력 시간 절점의 순서대로 상태를 비교해, 상태가 달라지는 두 계산 시각을 전이 구간의 하한·상한으로 기록합니다.

## API

- 입력 계약: `GasketContactTransitionBrackets`
- 계산 함수: `audit_gasket_contact_transition_brackets`
- 결과: `Calculation`
- 계산 ID: `fabrication.gasket_contact_transition_brackets`

입력 `contact_history`는 다음 기존 모델에서 생성한 `computed` 상태의 `AssessmentResult`여야 합니다.

- `fabrication.flange_viscoelastic_contact_history`
- `fabrication.flange_nonlinear_viscoelastic_contact_history`

결과 전체 SHA-256과 입력·RunContext digest를 확인합니다. 계산한 물리 범위는 요청에 적은 범위와 일치해야 합니다. 절점 목록은 모든 시각에서 같은 ID와 순서를 가져야 하며, 시각은 유한하고 엄격히 증가해야 합니다. 계산 예산은 최대 절점 수와 최대 공간 노드 수로 제한할 수 있습니다.

## 사용 예

```python
from matintegrity.models.gasket_contact_transition_brackets import (
    GasketContactTransitionBrackets,
    audit_gasket_contact_transition_brackets,
)
from matintegrity.contracts import canonical_digest

request = GasketContactTransitionBrackets(
    assessment_id="joint-contact-transitions-001",
    physical_scope_id="joint-scope-01",
    contact_history=computed_contact_history,
    contact_history_sha256=canonical_digest(
        computed_contact_history.model_dump(mode="json")
    ),
    physical_scope_and_time_basis_reviewed=True,
    contact_state_semantics_reviewed=True,
    computational_use_authorized=True,
)
calculation = audit_gasket_contact_transition_brackets(request)
```

## 결과 해석

`transition_brackets`의 각 행에는 노드 ID, 상태 변화 방향, 두 solver 절점 시각과 구간 너비가 들어갑니다. `event_time_s`는 항상 `None`입니다. 절점 사이 응답식이나 추가 solver 평가 없이 정확한 사건 시각을 계산하지 않습니다. 각 노드별 상태 변화 개수도 제공하지만, 관측 시각 사이에 발생했다가 되돌아온 미관측 전이는 집계하지 않습니다.

## 적용 경계

- 이 API는 이미 계산된 접촉 이력을 요약하며 플랜지 유한요소 응답을 만들지 않습니다.
- 절점 사이 접촉 상태를 선형 보간하거나 단일 전이만 있었다고 가정하지 않습니다.
- 같은 상태로 시작·종료한 구간에 숨은 접촉 변화가 없다고 보증하지 않습니다.
- 전이 구간은 실링 성능, 누설률, 재료 국부 응력, 설계 기준 적합성 또는 고장 확률을 뜻하지 않습니다.
- 검증 실행과 패키지 연결 전의 독립 계산 모듈입니다. 중앙 모델 registry, catalog 및 schema에 연결하려면 해당 메타데이터를 별도로 동기화해야 합니다.

# 수용액 포화도 시간 이력 이벤트 감사

`chemistry.aqueous_saturation_history_events`는 호출자가 이미 계산한 단일 고체 후보의 `log10(Q/K)` 시간 절점을 입력받아 임계값 교차 시점과 초과 지속시간을 산출합니다. 기본 임계값 0은 포화 경계입니다. 계산은 선언한 절점 사이의 선형 보간만 사용합니다.

요청에는 후보 고체와 용액 범위, 제공자 식별자·버전·설정 digest, 순서가 보존된 절점, 그리고 절점 배열의 canonical SHA-256이 포함됩니다. 모델은 배열 digest를 재계산해 대조합니다. 동일 고체·표준상태, 시간축, 보간 의미와 계산 사용을 호출자가 승인하지 않으면 `needs_data`를 반환합니다.

시작 또는 끝 절점에서 이미 임계값 위에 있으면 관측 구간 경계에서 검열된 상태로 기록합니다. 각 내부 구간의 지속시간은 교차점을 선형식으로 계산하며 수치 오버플로가 나면 부분 결과를 반환하고 계산을 중단합니다. 입력 절점은 외부 계산기의 결과이므로 이 모델은 화학 평형, 상 안정성, 석출량·속도, 보호막 성장, 부식률 또는 수명을 추론하지 않습니다.

```python
from matintegrity.saturation_history_events import (
    SaturationHistoryEventRequest,
    SaturationHistoryKnot,
    audit_saturation_history_events,
)
from matintegrity.contracts import canonical_digest

knots = (
    SaturationHistoryKnot(time_s=0, log10_saturation_ratio=-0.2),
    SaturationHistoryKnot(time_s=10, log10_saturation_ratio=0.2),
    SaturationHistoryKnot(time_s=20, log10_saturation_ratio=-0.1),
)
request = SaturationHistoryEventRequest(
    solid_id="caller-phase-1", solution_scope_id="run-01",
    provider_id="caller-equilibrium-solver", provider_revision="rev-1",
    provider_configuration_sha256="a" * 64,
    input_history_sha256=canonical_digest([k.model_dump(mode="json") for k in knots]),
    knots=knots, consistent_solid_and_standard_state_reviewed=True,
    time_basis_and_order_reviewed=True,
    piecewise_linear_interpolation_reviewed=True,
    computational_use_authorized=True,
)
result = audit_saturation_history_events(request)
```

이 코드는 사용법을 보이기 위한 문서 예시이며 실행·수치 검증을 수행하지 않았습니다. `crossing_times_s`와 `above_threshold_intervals`는 입력된 로그 포화비 기준의 구간 기술량입니다. 물리적 상 변화나 부식 위험 판단에는 별도 모델·데이터·검증이 필요합니다.

이미 `integration.aqueous_vant_hoff_saturation_history`가 만든 `AssessmentResult`가 있으면 `SaturationHistoryAssessmentBinding`과 `bind_vant_hoff_saturation_events()`를 사용합니다. 이 경로는 입력 digest, 전체 upstream result digest, context, 시간 배열과 각 knot 상태를 검사하고, 사용자가 지정한 고체 후보가 모든 knot에서 정확히 하나씩 계산됐는지 확인합니다. 결과는 부모 digest와 추출한 knot를 함께 보존합니다. 보간 검토 승인은 이 adapter에서도 별도로 필요합니다.

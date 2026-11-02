# 순수 염 Pitzer 유한 시나리오 요약

`PitzerSaltFiniteScenarioEnvelope`는 같은 염 화학식과 용액 온도를 공유하는 caller 제공 `PitzerSingleSaltActivity` 요청을 입력 순서대로 계산합니다. 각 시나리오의 molality, 상호작용 계수, 파라미터 기록과 Evidence는 개별 요청에 남습니다.

모든 요청이 계산된 경우에만 이 입력 목록 안에서 이온강도, 평균 이온 활동도 계수, 평균 이온 활동도, 삼투계수와 물 활동도의 최솟값 및 최댓값을 반환합니다. 한 항목이 미계산이면 성공한 prefix와 최초 실패를 보존하고 전체 목록의 extrema라고 오인할 요약은 제공하지 않습니다.

## 경계

- 결과는 caller가 제시한 유한 목록에 대한 결정론적 요약입니다. 연속 파라미터 범위나 전역 bound를 증명하지 않습니다.
- 가중치·확률분포·신뢰구간을 만들지 않습니다.
- 각 요청의 단일 순수 전해질 Pitzer 계산을 재사용합니다. 혼합 전해질 상호작용, 단일 이온 활동도 또는 parameter fit은 구현하지 않습니다.
- 데이터 출처, 파라미터 사용 허가, 유효 온도·이온강도 구간은 각 요청의 Evidence와 review flag를 caller가 제공해야 합니다.
- 부식률, 석출 안정성, 수명, 설계 허용 또는 건전성 적합성을 추론하지 않습니다.

## Python API

```python
from matintegrity.pitzer_salt_finite_scenario_envelope import (
    PitzerSaltFiniteScenarioEnvelope,
    evaluate_pitzer_salt_finite_scenario_envelope,
)

request = PitzerSaltFiniteScenarioEnvelope(
    envelope_id="salt-parameter-sensitivity-cases",
    scenarios=(scenario_a, scenario_b),  # 각각 독립된 PitzerSingleSaltActivity 계약
    shared_salt_and_temperature_scope_reviewed=True,
    scenario_order_reviewed=True,
    finite_set_interpretation_reviewed=True,
)
result = evaluate_pitzer_salt_finite_scenario_envelope(request)
```

## 개발·검증 기록

계산은 기존 순수 염 Pitzer 식을 그대로 호출하고 scenario별 입력/출력 digest를 보존합니다. 유한 목록 전체가 완료된 뒤에만 해당 목록의 extrema를 계산하며, 실패 prefix는 완전한 envelope로 오인되지 않도록 따로 반환합니다. 이 모듈 자체의 수치 검증과 패키지 포함 검증은 별도 일괄 검증 단계에서 수행합니다.

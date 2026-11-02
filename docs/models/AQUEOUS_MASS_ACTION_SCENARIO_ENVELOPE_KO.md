# 고정 네트워크 수용액 질량작용의 유한 시나리오 응답범위

## 목적

`chemistry.aqueous_mass_action_scenario_envelope`는 동일한 수용액 반응·제약 topology를 가진 caller 제공 입력 사례를 각각 기존 질량작용 계산기에 넣고, 계산된 종 활동도와 농도의 사례별 최솟값·최댓값을 정리합니다. 입력 사례는 계산 전에 모두 명시되어야 합니다.

## 고정되는 네트워크

각 시나리오는 기존 `AqueousMassActionSystem` 전체 계약을 제공합니다. 모든 사례에서 아래 항목이 순서까지 일치해야 합니다.

- 용액 ID, 활동도 표준상태, 활동도/평형 공급자 ID와 revision
- 종 ID, 전하, 선언된 원소 조성
- 반응 ID와 종별 화학양론 계수
- 물질/전하 제약 ID와 종별 계수

온도, 고정 활동도계수, 초기 활동도 추정값, 평형상수, 제약 목표량과 각 자료 record digest는 시나리오별로 달라질 수 있습니다. 각 사례는 자신의 Evidence, review flag와 자료 계보를 유지합니다.

## 계산 및 실패 처리

모델은 시나리오를 입력 순서대로 기존 aqueous mass-action solver에 독립 입력합니다. 모든 사례가 `computed`여야 종별 envelope를 반환합니다. 첫 `needs_data` 또는 `out_of_scope`가 있으면 해당 오류와 미계산 suffix, 앞서 성공한 prefix를 기록하고 전체 envelope는 만들지 않습니다.

## 결과 의미

최솟값과 최댓값은 **정확히 전달된 유한 사례 집합**에서 나온 값입니다. 시나리오를 생성하거나 가중하거나 확률표본으로 해석하지 않습니다. 이는 모든 물성 범위의 전역 상한, 신뢰구간, 불확실성 분포 또는 모델 정확도 검증이 아닙니다. 종 네트워크의 변경, 고체상 선택, 석출·용해 속도, 물질전달, 부식률 및 자격판정을 추론하지 않습니다.

## Python API 형태

```python
from matintegrity.aqueous_mass_action_scenario_envelope import (
    AqueousMassActionScenario,
    AqueousMassActionScenarioEnvelope,
    evaluate_aqueous_mass_action_scenario_envelope,
)

request = AqueousMassActionScenarioEnvelope(
    envelope_id="wco2-scenario-set-A",
    scenarios=(
        AqueousMassActionScenario(scenario_id="case-low", scenario_label="caller low case", request=low_case),
        AqueousMassActionScenario(scenario_id="case-high", scenario_label="caller high case", request=high_case),
    ),
    solution_identity_and_fixed_network_topology_reviewed=True,
    finite_scenario_set_is_caller_owned_and_complete_for_comparison_reviewed=True,
    provider_family_and_revision_are_comparable_reviewed=True,
    no_probability_or_distribution_interpretation_reviewed=True,
)
result = evaluate_aqueous_mass_action_scenario_envelope(request)
```

`low_case`와 `high_case`는 호출자가 실제 원자료와 검토를 바탕으로 별도 작성한 전체 질량작용 시스템입니다. 위 레이블은 확률적 분위수나 극단조건을 정의하지 않습니다.

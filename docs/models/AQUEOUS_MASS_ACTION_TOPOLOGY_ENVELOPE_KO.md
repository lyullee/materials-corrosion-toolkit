# 고정 용액 상태에서 대안 수용액 반응 네트워크 비교

## 목적

`chemistry.aqueous_mass_action_topology_envelope`는 동일한 용액 정체성, 온도, 종 목록, 활동도 상태와 물질수지 제약을 사용하는 서로 다른 caller 반응 topology를 각각 기존 질량작용 solver로 계산하고, 종별 활동도·농도의 유한 사례 범위를 보고합니다.

## 고정 입력과 바뀌는 입력

각 사례는 완전한 `AqueousMassActionSystem`이어야 합니다. 모든 사례는 아래 데이터를 정확히 공유해야 합니다.

- 용액 ID, 온도, 표준상태
- 종 ID·순서, 전하, 원소식, 고정 활동도계수, 초기 활동도 추정값
- 물질/전하 제약의 ID·계수·목표량·정규화 크기
- activity provider ID/revision/record digest
- equilibrium provider ID/revision

반응 ID·화학양론 topology와 그 반응에 적용되는 equilibrium configuration/record는 topology별로 다를 수 있습니다. 각 사례 자체는 같은 종 수와 제약 수에 맞는 완전한 네트워크여야 하며, 기존 solver의 charge/formula 보존 검토를 거칩니다. 최소 두 topology가 서로 달라야 합니다.

## 계산 및 종료 규칙

모델은 각 topology를 독립적으로 계산합니다. 각 사례에 source request/result digest와 평형상수 자료 Evidence를 남깁니다. 어떤 사례든 `needs_data` 또는 `out_of_scope`이면 전체 envelope를 만들지 않고 성공 prefix, 첫 실패 및 미완료 topology를 보존합니다. 실패 사례를 빼고 나머지만으로 범위를 만들지 않습니다.

## 해석 경계

종별 최솟값/최댓값은 caller가 정확히 전달한 유한 반응 topology 집합의 값입니다. 이 범위는 네트워크 완전성, 반응 메커니즘의 정확성, 확률·신뢰수준, 가능한 모든 대안의 전역 경계가 아닙니다. topology를 자동 생성하거나 안정상을 선택하지 않습니다. 상변화·침전·속도론·물질전달·부식률·재료 자격도 추론하지 않습니다.

## Python API 형태

```python
from matintegrity.aqueous_mass_action_topology_envelope import (
    AqueousMassActionTopologyCase,
    AqueousMassActionTopologyEnvelope,
    evaluate_aqueous_mass_action_topology_envelope,
)

request = AqueousMassActionTopologyEnvelope(
    comparison_id="co2-network-comparison-01",
    topologies=(
        AqueousMassActionTopologyCase(topology_id="network-A", description="caller network A", request=system_a),
        AqueousMassActionTopologyCase(topology_id="network-B", description="caller network B", request=system_b),
    ),
    alternative_networks_are_complete_caller_systems_reviewed=True,
    fixed_species_inventory_and_solution_state_reviewed=True,
    common_balance_constraints_and_standard_state_reviewed=True,
    provider_revisions_and_topology_comparability_reviewed=True,
    finite_topology_set_and_no_probability_interpretation_reviewed=True,
)
result = evaluate_aqueous_mass_action_topology_envelope(request)
```

`system_a`와 `system_b`는 호출자가 검토한 대안 전체 네트워크입니다. API는 사례에 가중치, 순위 또는 선택 결정을 부여하지 않습니다.

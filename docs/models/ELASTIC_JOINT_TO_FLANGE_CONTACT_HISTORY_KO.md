# Elastic joint clamp history에서 공간 가스켓 접촉장으로 전달

## 목적과 경계

`integration.elastic_joint_to_flange_contact_history`는 기존 elastic two-spring `integration.elastic_joint_load_ordered_history`의 정확 snapshot별 clamp force를 호출자가 제공한 nodal free-closure transfer에 넣고, 각 snapshot마다 기존 unilateral `flange_contact_field` solver를 실행합니다. 기존 두 계산기가 각각 내놓던 전역 clamp-force history와 정적 공간 contact-field 계산을 caller 검토가 명시된 handoff 하나로 연결합니다.

이 API는 FE flange response를 만들거나 transfer 계수를 맞추지 않습니다. 볼트/가스켓 물성 법칙, 하중 분배, contact time response, snapshot 사이 보간을 추정하지 않습니다. 접촉 압력장은 가스켓 누설 예측, seal acceptance 또는 qualification으로 해석할 수 없습니다.

## 입력

- `joint_load_history`: 기존 `ElasticJointLoadHistoryRequest`와 순서가 지정된 clamp-load snapshot.
- `contact_template`: 기존 `FlangeContactFieldRequest`. contact node 순서, 면적, 선형 gasket stiffness, flange relative-compliance matrix, 기준 자유 폐쇄 벡터, 응답 lineage, 증거 및 기존 contact applicability review를 제공합니다.
- `reference_clamp_force_N`: template의 자유 폐쇄 벡터가 대응하는 clamp force.
- `nodal_free_closure_change_m_per_N`: contact-template node 순서와 일치하는 caller 제공 벡터. 점 i에서 적용식은 다음과 같습니다.

  `free_closure_i(t) = template_free_closure_i + transfer_i × (clamp_force(t) − reference_clamp_force)`

- `joint_id`: 명시한 contact template joint ID와 일치해야 하는 transfer mapping identity.
- 검토 플래그는 전역 clamp-force-to-nodal-closure 관계, 적용 scope/reference 상태, 고정된 다른 하중과 선형 증분 가정을 확인합니다. 접촉 계산 자체는 template의 flange/gasket/compression-only 검토 플래그도 요구합니다.

## 계산 흐름

1. 기존 elastic-joint load-history evaluator가 모든 caller snapshot의 clamp force를 계산합니다. 일부 snapshot이 불완전하면 contact solver를 호출하지 않습니다.
2. 각 load 결과 knot의 index/time을 원 요청과 확인한 뒤, reference force에서의 증분만 caller transfer 벡터에 곱합니다.
3. 계산된 free-closure 벡터를 contact template에 넣고 기존 spatial unilateral contact solver를 정확한 입력 시각마다 호출합니다.
4. 첫 비계산 contact knot에서 멈추며 성공 prefix와 최초 실패 결과를 반환합니다. 두 시각 사이 응답은 만들지 않습니다.

## Python API

```python
from matintegrity.elastic_joint_to_flange_contact_history import (
    ElasticJointToFlangeContactHistory,
    evaluate_elastic_joint_to_flange_contact_history,
)

request = ElasticJointToFlangeContactHistory.model_validate(payload)
calculation = evaluate_elastic_joint_to_flange_contact_history(request)
```

표준 registry 연결에는 `specifications()`를 중앙 통합 단계에서 사용합니다.

## 결과 해석

각 접촉 결과는 clamp history knot 및 contact request와 함께 digest로 보존됩니다. 이 결과는 caller가 선언한 선형 전달식과 template flange-compliance/contact model의 조건부 계산입니다. FE 해석, material law fitting/transfer, contact 사건 시점, leakage, seal acceptance, 확률 또는 engineering qualification을 대신하지 않습니다.

# `inspection.disposition_decision_tree`

**목적:** One reviewed exhaustive mutually exclusive inspection-outcome partition over one event context; each branch supplies its probability, complete disposition, conditional residual first-failure probability and costs; finite expectations only.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.inspection_disposition_tree.v1", "default": "matintegrity.inspection_disposition_tree.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `tree_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `horizon_start_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `horizon_end_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `conditioning` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_probability_meaning` | 예 | `{"const": "conditional_first_failure_in_period", "type": "string"}` | 계약·필드 설명 참조 |
| `inspection_action_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `inspection_action_label` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `inspection_action_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `inspection_outcome_model_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `inspection_outcome_model_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `inspection_outcome_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `inspection_outcome_input_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `risk_model_structure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `common_cause_group_ids` | 아니오 | `{"items": {"type": "string"}, "type": "array"}` | 계약·필드 설명 참조 |
| `cost_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `currency_or_normalized_unit` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `inspection_cost_components` | 아니오 | `{"items": {"$ref": "#/$defs/RiskCostComponent"}, "type": "array"}` | 계약·필드 설명 참조 |
| `outcome_branches` | 예 | `{"items": {"$ref": "#/$defs/InspectionDispositionOutcomeBranch"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_outcome_probability_sum_error` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `outcome_partition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `outcome_probabilities_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `disposition_definitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `disposition_effects_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `costs_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/InspectionDispositionDecisionTree.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `horizon_start_s` | `s` |
| `horizon_end_s` | `s` |
| `outcome_probability_sum` | `1` |
| `inspection_cost` | `declared_cost_unit` |
| `expected_disposition_cost` | `declared_cost_unit` |
| `expected_total_action_cost` | `declared_cost_unit` |
| `residual_failure_probability_estimate` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- One reviewed exhaustive mutually exclusive inspection-outcome partition over one event context; each branch supplies its probability, complete disposition, conditional residual first-failure probability and costs; finite expectations only.

## 구현 근거·독립 설명

- `inspection_disposition_tree_definition`: For one inspection action and one common event, scope, horizon, survival conditioning and cost basis, require a caller-reviewed mutually exclusive exhaustive outcome partition. Preserve every outcome probability, disposition identity and definition, disposition-effect model revision/configuration/input/result digests, conditional residual first-failure probability and additive disposition costs. Form only the finite probability-weighted expected disposition cost and residual event probability, then expose a digest-bound estimate-basis action candidate. Missing review gates withhold arithmetic and probabilities must sum to one within a caller tolerance. Do not infer branch probabilities from POD or false-call data, invent dispositions, produce confidence bounds, optimize a multi-period policy or claim regulatory acceptance.

확률 의미: `{"residual_failure_probability_estimate": "conditional_first_failure_in_period"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.disposition_decision_tree"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.disposition_decision_tree"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "tree_id": "synthetic-inspection-disposition-tree",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "synthetic-wall-location",
  "event_id": "synthetic-first-threshold-crossing",
  "event_definition": "first crossing of an independently authored synthetic limit",
  "horizon_start_s": 0.0,
  "horizon_end_s": 31557600.0,
  "conditioning": "synthetic asset has not crossed the declared limit at horizon start",
  "event_probability_meaning": "conditional_first_failure_in_period",
  "inspection_action_id": "synthetic-inspect-and-dispose",
  "inspection_action_label": "inspect and apply a disposition table",
  "inspection_action_definition": "one inspection followed by a reviewed synthetic disposition",
  "inspection_outcome_model_id": "synthetic.inspection-outcomes",
  "inspection_outcome_model_revision": "1",
  "inspection_outcome_configuration_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "inspection_outcome_input_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "risk_model_structure_id": "synthetic-top-event-with-inspection",
  "common_cause_group_ids": [
    "synthetic-shared-environment"
  ],
  "cost_basis_id": "synthetic-normalized-costs-v1",
  "currency_or_normalized_unit": "normalized_cost_unit",
  "inspection_cost_components": [
    {
      "component_id": "inspection-cost",
      "category": "inspection",
      "amount": 50.0,
      "basis": "independently authored synthetic value"
    }
  ],
  "outcome_branches": [
    {
      "outcome_id": "clear",
      "outcome_label": "clear outcome",
      "probability_given_inspection": 0.7,
      "disposition_id": "continue",
      "disposition_label": "continue operation",
      "disposition_definition": "reviewed synthetic continue disposition",
      "disposition_effect_model_id": "synthetic.continue-forecast",
      "disposition_effect_model_revision": "1",
      "disposition_effect_configuration_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
      "disposition_effect_input_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
      "disposition_event_result_sha256": "3333333333333333333333333333333333333333333333333333333333333333",
      "residual_failure_probability_given_outcome_and_disposition": 0.1,
      "disposition_cost_components": []
    },
    {
      "outcome_id": "indication",
      "outcome_label": "actionable indication",
      "probability_given_inspection": 0.2,
      "disposition_id": "repair",
      "disposition_label": "repair",
      "disposition_definition": "reviewed synthetic repair disposition",
      "disposition_effect_model_id": "synthetic.repair-forecast",
      "disposition_effect_model_revision": "1",
      "disposition_effect_configuration_sha256": "4444444444444444444444444444444444444444444444444444444444444444",
      "disposition_effect_input_sha256": "5555555555555555555555555555555555555555555555555555555555555555",
      "disposition_event_result_sha256": "6666666666666666666666666666666666666666666666666666666666666666",
      "residual_failure_probability_given_outcome_and_disposition": 0.01,
      "disposition_cost_components": [
        {
          "component_id": "repair-cost",
          "category": "repair",
          "amount": 400.0,
          "basis": "independently authored synthetic value"
        }
      ]
    },
    {
      "outcome_id": "inconclusive",
      "outcome_label": "inconclusive outcome",
      "probability_given_inspection": 0.1,
      "disposition_id": "monitor",
      "disposition_label": "additional monitoring",
      "disposition_definition": "reviewed synthetic monitoring disposition",
      "disposition_effect_model_id": "synthetic.monitoring-forecast",
      "disposition_effect_model_revision": "1",
      "disposition_effect_configuration_sha256": "7777777777777777777777777777777777777777777777777777777777777777",
      "disposition_effect_input_sha256": "8888888888888888888888888888888888888888888888888888888888888888",
      "disposition_event_result_sha256": "9999999999999999999999999999999999999999999999999999999999999999",
      "residual_failure_probability_given_outcome_and_disposition": 0.05,
      "disposition_cost_components": [
        {
          "component_id": "monitoring-cost",
          "category": "monitoring",
          "amount": 100.0,
          "basis": "independently authored synthetic value"
        }
      ]
    }
  ],
  "maximum_outcome_probability_sum_error": 1e-12,
  "outcome_partition_reviewed": true,
  "outcome_probabilities_reviewed": true,
  "disposition_definitions_reviewed": true,
  "disposition_effects_reviewed": true,
  "costs_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-disposition-tree-example",
      "origin": "synthetic",
      "citation": "independently authored finite decision tree"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/inspection.py#L1276)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

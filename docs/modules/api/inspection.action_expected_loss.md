# `inspection.action_expected_loss`

**목적:** One event, physical scope, horizon, survival conditioning and cost basis; every complete action retains an externally evaluated residual first-failure probability and reviewed additive costs; expectation is probability times conditional consequence plus action cost.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.inspection_action_expected_loss.v1", "default": "matintegrity.inspection_action_expected_loss.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `comparison_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `horizon_start_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `horizon_end_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `conditioning` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_probability_meaning` | 예 | `{"const": "conditional_first_failure_in_period", "type": "string"}` | 계약·필드 설명 참조 |
| `probability_basis` | 예 | `{"enum": ["estimate", "upper_bound"], "type": "string"}` | 계약·필드 설명 참조 |
| `cost_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `currency_or_normalized_unit` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `failure_consequence_components` | 예 | `{"items": {"$ref": "#/$defs/RiskCostComponent"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidates` | 예 | `{"items": {"$ref": "#/$defs/InspectionActionRiskCandidate"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `cost_tie_absolute_tolerance` | 아니오 | `{"default": 0.0, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `action_definitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `residual_probabilities_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `costs_and_consequences_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `decision_criterion_user_approved` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/InspectionActionExpectedLossComparison.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `horizon_start_s` | `s` |
| `horizon_end_s` | `s` |
| `failure_consequence_cost` | `declared_cost_unit` |
| `baseline_total_expected_loss` | `declared_cost_unit` |
| `minimum_total_expected_loss` | `declared_cost_unit` |
| `cost_tie_absolute_tolerance` | `declared_cost_unit` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- One event, physical scope, horizon, survival conditioning and cost basis; every complete action retains an externally evaluated residual first-failure probability and reviewed additive costs; expectation is probability times conditional consequence plus action cost.

## 구현 근거·독립 설명

- `inspection_action_expected_loss_definition`: For one reviewed event, physical scope, horizon, survival conditioning and common cost basis, preserve exactly one zero-action-cost baseline and one or more complete intervention alternatives. Every action retains its definition, effect-model identity, revision, input digest, residual conditional first-failure probability estimate and optional upper bound. Add reviewed action-cost components to residual event probability times reviewed conditional consequence components, compare point-estimate or complete upper-bound totals, and withhold arbitrary selection when totals tie within a caller-declared absolute tolerance. Do not infer action effectiveness, event probabilities, dependencies, costs, consequences, risk tolerance, resource feasibility, value of information, regulatory acceptance or validation of the supplied models.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.action_expected_loss"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.action_expected_loss"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "comparison_id": "synthetic-inspection-action-risk",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "synthetic-wall-location",
  "event_id": "synthetic-first-threshold-crossing",
  "event_definition": "first crossing of an independently authored synthetic limit",
  "horizon_start_s": 0.0,
  "horizon_end_s": 31557600.0,
  "conditioning": "synthetic asset has not crossed the declared limit at horizon start",
  "event_probability_meaning": "conditional_first_failure_in_period",
  "probability_basis": "estimate",
  "cost_basis_id": "synthetic-normalized-costs-v1",
  "currency_or_normalized_unit": "normalized_cost_unit",
  "failure_consequence_components": [
    {
      "component_id": "failure-repair",
      "category": "physical repair",
      "amount": 1000.0,
      "basis": "independently authored synthetic value"
    },
    {
      "component_id": "failure-outage",
      "category": "lost operation",
      "amount": 4000.0,
      "basis": "independently authored synthetic value"
    }
  ],
  "candidates": [
    {
      "action_id": "continue",
      "action_label": "continue without intervention",
      "candidate_kind": "baseline",
      "action_definition": "no action during the common horizon",
      "action_effect_model_id": "synthetic.no-action-forecast",
      "action_effect_model_revision": "1",
      "action_effect_input_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "action_effect_configuration_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
      "risk_model_structure_id": "synthetic-top-event-v1",
      "event_probability_result_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "common_cause_group_ids": [
        "synthetic-shared-environment"
      ],
      "residual_failure_probability_estimate": 0.1,
      "residual_failure_probability_upper_bound": 0.12,
      "action_cost_components": []
    },
    {
      "action_id": "inspect",
      "action_label": "inspect and apply a supplied disposition rule",
      "candidate_kind": "intervention",
      "action_definition": "reviewed synthetic inspection and disposition action",
      "action_effect_model_id": "synthetic.inspection-decision-tree",
      "action_effect_model_revision": "1",
      "action_effect_input_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "action_effect_configuration_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
      "risk_model_structure_id": "synthetic-top-event-v1-inspection",
      "event_probability_result_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "common_cause_group_ids": [
        "synthetic-shared-environment"
      ],
      "residual_failure_probability_estimate": 0.04,
      "residual_failure_probability_upper_bound": 0.1,
      "action_cost_components": [
        {
          "component_id": "inspection",
          "category": "inspection",
          "amount": 100.0,
          "basis": "independently authored synthetic value"
        }
      ]
    },
    {
      "action_id": "repair",
      "action_label": "execute a supplied repair action",
      "candidate_kind": "intervention",
      "action_definition": "reviewed synthetic repair action",
      "action_effect_model_id": "synthetic.repair-forecast",
      "action_effect_model_revision": "1",
      "action_effect_input_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "action_effect_configuration_sha256": "3333333333333333333333333333333333333333333333333333333333333333",
      "risk_model_structure_id": "synthetic-top-event-v1-repair",
      "event_probability_result_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "common_cause_group_ids": [
        "synthetic-shared-environment"
      ],
      "residual_failure_probability_estimate": 0.01,
      "residual_failure_probability_upper_bound": 0.02,
      "action_cost_components": [
        {
          "component_id": "planned-repair",
          "category": "repair",
          "amount": 400.0,
          "basis": "independently authored synthetic value"
        }
      ]
    }
  ],
  "cost_tie_absolute_tolerance": 0.0,
  "action_definitions_reviewed": true,
  "residual_probabilities_reviewed": true,
  "costs_and_consequences_reviewed": true,
  "decision_criterion_user_approved": true,
  "evidence": [
    {
      "source_id": "authored-action-risk-example",
      "origin": "synthetic",
      "citation": "independently authored expected-loss example"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/inspection.py#L1062)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

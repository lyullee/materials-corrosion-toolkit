# `inspection.multi_period_policy_evaluation`

**목적:** One complete caller-reviewed finite policy-path ensemble over a common event, scope, horizon, start-survival condition, cost and discount basis; evaluate path-probability-weighted discounted action and first-failure consequence costs without policy search.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.multi_period_inspection_policy.v1", "default": "matintegrity.multi_period_inspection_policy.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `evaluation_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `policy_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `policy_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `policy_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `policy_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `path_generator_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `path_generator_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `path_generator_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `path_manifest_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `horizon_start_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `horizon_end_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `conditioning` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_probability_meaning` | 예 | `{"const": "conditional_first_failure_in_period", "type": "string"}` | 계약·필드 설명 참조 |
| `cost_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `currency_or_normalized_unit` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `discount_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `failure_consequence_components` | 예 | `{"items": {"$ref": "#/$defs/RiskCostComponent"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `paths` | 예 | `{"items": {"$ref": "#/$defs/InspectionPolicyPath"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_path_probability_sum_error` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `complete_path_manifest_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `path_probabilities_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `policy_actions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `first_failure_events_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `costs_and_discount_factors_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/MultiPeriodInspectionPolicyEvaluation.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `horizon_start_s` | `s` |
| `horizon_end_s` | `s` |
| `path_probability_sum` | `1` |
| `conditional_first_failure_probability` | `1` |
| `failure_consequence_cost_at_undiscounted_basis` | `declared_cost_unit` |
| `expected_discounted_action_cost` | `declared_cost_unit` |
| `expected_discounted_failure_consequence` | `declared_cost_unit` |
| `expected_discounted_total_loss` | `declared_cost_unit` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- One complete caller-reviewed finite policy-path ensemble over a common event, scope, horizon, start-survival condition, cost and discount basis; evaluate path-probability-weighted discounted action and first-failure consequence costs without policy search.

## 구현 근거·독립 설명

- `multi_period_inspection_policy_definition`: For one fixed externally generated multi-period inspection policy, require a complete reviewed finite path manifest over one event, physical scope, horizon, start-survival condition, cost basis and discount basis. Preserve each path probability and source digest, every ordered observation/action stage and its model revision/configuration/input digests, every action-cost component and caller-supplied present-value factor, and the first-failure time and consequence factor exactly when failure occurs. Compute only pathwise discounted costs and their finite probability-weighted expectations. Reject incomplete probability mass, duplicate identities, stages outside the horizon or after first failure, and missing review gates. Do not infer transitions, observations, probabilities, discount factors, consequences, confidence bounds, policy optimality, resource feasibility or regulatory acceptance.

확률 의미: `{"conditional_first_failure_probability": "conditional_first_failure_in_period"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.multi_period_policy_evaluation"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.multi_period_policy_evaluation"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.multi_period_inspection_policy.v1",
  "evaluation_id": "synthetic-fixed-policy-evaluation",
  "policy_id": "synthetic-inspect-monitor-repair-policy",
  "policy_revision": "1",
  "policy_definition": "reviewed finite policy with inspection, monitoring and repair actions",
  "policy_configuration_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "path_generator_id": "synthetic.policy-path-generator",
  "path_generator_revision": "1",
  "path_generator_configuration_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "path_manifest_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "synthetic-wall-location",
  "event_id": "synthetic-first-threshold-crossing",
  "event_definition": "first crossing of an independently authored synthetic limit",
  "horizon_start_s": 1000.0,
  "horizon_end_s": 2000.0,
  "conditioning": "synthetic integrity function survived through horizon start",
  "event_probability_meaning": "conditional_first_failure_in_period",
  "cost_basis_id": "synthetic-normalized-costs-v1",
  "currency_or_normalized_unit": "normalized_cost_unit",
  "discount_basis_id": "synthetic-reviewed-present-value-factors-v1",
  "failure_consequence_components": [
    {
      "component_id": "failure-consequence",
      "category": "failure consequence",
      "amount": 1000.0,
      "basis": "independently authored synthetic value at event time"
    }
  ],
  "paths": [
    {
      "path_id": "clear-monitor",
      "path_probability_given_start_survival": 0.5,
      "path_source_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "stages": [
        {
          "stage_id": "clear-inspection",
          "stage_time_s": 1100.0,
          "observed_state_id": "clear",
          "action_id": "inspect",
          "action_definition": "reviewed synthetic inspection action",
          "action_model_id": "synthetic.inspect",
          "action_model_revision": "1",
          "action_model_configuration_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
          "action_model_input_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
          "cost_components": [
            {
              "component_id": "inspection",
              "category": "inspection",
              "amount_at_stage_time": 100.0,
              "present_value_factor": 1.0,
              "basis": "synthetic reviewed factor"
            }
          ]
        },
        {
          "stage_id": "clear-monitoring",
          "stage_time_s": 1600.0,
          "observed_state_id": "stable",
          "action_id": "monitor",
          "action_definition": "reviewed synthetic monitoring action",
          "action_model_id": "synthetic.monitor",
          "action_model_revision": "1",
          "action_model_configuration_sha256": "3333333333333333333333333333333333333333333333333333333333333333",
          "action_model_input_sha256": "4444444444444444444444444444444444444444444444444444444444444444",
          "cost_components": [
            {
              "component_id": "monitoring",
              "category": "monitoring",
              "amount_at_stage_time": 50.0,
              "present_value_factor": 0.9,
              "basis": "synthetic reviewed factor"
            }
          ]
        }
      ],
      "first_failure_occurred": false,
      "first_failure_time_s": null,
      "failure_consequence_present_value_factor": null
    },
    {
      "path_id": "indication-repair",
      "path_probability_given_start_survival": 0.3,
      "path_source_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "stages": [
        {
          "stage_id": "indication-inspection",
          "stage_time_s": 1100.0,
          "observed_state_id": "indication",
          "action_id": "inspect",
          "action_definition": "reviewed synthetic inspection action",
          "action_model_id": "synthetic.inspect",
          "action_model_revision": "1",
          "action_model_configuration_sha256": "5555555555555555555555555555555555555555555555555555555555555555",
          "action_model_input_sha256": "6666666666666666666666666666666666666666666666666666666666666666",
          "cost_components": [
            {
              "component_id": "inspection",
              "category": "inspection",
              "amount_at_stage_time": 100.0,
              "present_value_factor": 1.0,
              "basis": "synthetic reviewed factor"
            }
          ]
        },
        {
          "stage_id": "indication-repair-action",
          "stage_time_s": 1300.0,
          "observed_state_id": "repair-required",
          "action_id": "repair",
          "action_definition": "reviewed synthetic repair action",
          "action_model_id": "synthetic.repair",
          "action_model_revision": "1",
          "action_model_configuration_sha256": "7777777777777777777777777777777777777777777777777777777777777777",
          "action_model_input_sha256": "8888888888888888888888888888888888888888888888888888888888888888",
          "cost_components": [
            {
              "component_id": "repair",
              "category": "repair",
              "amount_at_stage_time": 400.0,
              "present_value_factor": 0.95,
              "basis": "synthetic reviewed factor"
            }
          ]
        }
      ],
      "first_failure_occurred": false,
      "first_failure_time_s": null,
      "failure_consequence_present_value_factor": null
    },
    {
      "path_id": "failure-after-inspection",
      "path_probability_given_start_survival": 0.2,
      "path_source_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "stages": [
        {
          "stage_id": "failure-path-inspection",
          "stage_time_s": 1100.0,
          "observed_state_id": "clear-before-failure",
          "action_id": "inspect",
          "action_definition": "reviewed synthetic inspection action",
          "action_model_id": "synthetic.inspect",
          "action_model_revision": "1",
          "action_model_configuration_sha256": "9999999999999999999999999999999999999999999999999999999999999999",
          "action_model_input_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
          "cost_components": [
            {
              "component_id": "inspection",
              "category": "inspection",
              "amount_at_stage_time": 100.0,
              "present_value_factor": 1.0,
              "basis": "synthetic reviewed factor"
            }
          ]
        }
      ],
      "first_failure_occurred": true,
      "first_failure_time_s": 1500.0,
      "failure_consequence_present_value_factor": 0.8
    }
  ],
  "maximum_path_probability_sum_error": 1e-12,
  "complete_path_manifest_reviewed": true,
  "path_probabilities_reviewed": true,
  "policy_actions_reviewed": true,
  "first_failure_events_reviewed": true,
  "costs_and_discount_factors_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-multi-period-policy-example",
      "origin": "synthetic",
      "citation": "independently authored finite policy-path ensemble"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/inspection.py#L2169)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

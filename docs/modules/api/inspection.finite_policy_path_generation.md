# `inspection.finite_policy_path_generation`

**목적:** Reviewed finite state, initial, observation, fixed decision-rule and transition tables over ordered epochs; enumerate every positive-probability path exactly within a caller-declared path-count limit.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.finite_inspection_policy_path_generation.v1", "default": "matintegrity.finite_inspection_policy_path_generation.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `generation_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `generator_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `policy_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `policy_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `policy_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `policy_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
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
| `states` | 예 | `{"items": {"$ref": "#/$defs/FinitePolicyState"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `initial_state_probabilities` | 예 | `{"items": {"$ref": "#/$defs/InitialPolicyStateProbability"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `decision_epochs` | 예 | `{"items": {"$ref": "#/$defs/FinitePolicyDecisionEpoch"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_probability_sum_error` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_generated_paths` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `state_space_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `initial_distribution_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_models_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `decision_rules_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `transition_models_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `action_costs_and_discount_factors_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FiniteInspectionPolicyPathGeneration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `horizon_start_s` | `s` |
| `horizon_end_s` | `s` |
| `stage_time_s` | `s` |
| `path_probability_sum` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Reviewed finite state, initial, observation, fixed decision-rule and transition tables over ordered epochs; enumerate every positive-probability path exactly within a caller-declared path-count limit.

## 구현 근거·독립 설명

- `finite_inspection_policy_path_generation_definition`: Expand a caller-reviewed finite policy definition over strictly ordered decision epochs. Require uniquely defined failure and nonfailure states, a complete initial distribution conditional on start survival, state-conditional observation distributions, one deterministic action for every observation, complete action definitions with model and cost identities, and state-action transition distributions. Every probability family must sum to one within a declared tolerance, failure consequence factors occur exactly on transitions into failure, and failure paths stop immediately. Enumerate every positive-probability path as the exact product of supplied table entries and preserve a digest of its full trace; omit only zero-probability branches. Stop with an explicit out-of-scope result before exceeding the caller path-count limit. Do not fit or infer states, observations, transitions, decisions, probabilities, costs or optimality, and do not treat reviewed tables as empirical validation.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.finite_policy_path_generation"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.finite_policy_path_generation"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.finite_inspection_policy_path_generation.v1",
  "generation_id": "synthetic-finite-policy-generation",
  "generator_configuration_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "policy_id": "synthetic-monitor-repair-policy",
  "policy_revision": "1",
  "policy_definition": "clear observations trigger monitoring and alerts trigger repair",
  "policy_configuration_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
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
  "states": [
    {
      "state_id": "healthy",
      "state_definition": "reviewed synthetic healthy state",
      "is_failure_state": false
    },
    {
      "state_id": "degraded",
      "state_definition": "reviewed synthetic degraded state",
      "is_failure_state": false
    },
    {
      "state_id": "failure",
      "state_definition": "reviewed synthetic first-failure state",
      "is_failure_state": true
    }
  ],
  "initial_state_probabilities": [
    {
      "state_id": "healthy",
      "probability_given_start_survival": 0.8
    },
    {
      "state_id": "degraded",
      "probability_given_start_survival": 0.2
    }
  ],
  "decision_epochs": [
    {
      "stage_id": "epoch-1",
      "stage_time_s": 1200.0,
      "observation_probabilities": [
        {
          "state_id": "healthy",
          "observation_id": "clear",
          "probability_given_state": 0.9
        },
        {
          "state_id": "healthy",
          "observation_id": "alert",
          "probability_given_state": 0.1
        },
        {
          "state_id": "degraded",
          "observation_id": "clear",
          "probability_given_state": 0.2
        },
        {
          "state_id": "degraded",
          "observation_id": "alert",
          "probability_given_state": 0.8
        }
      ],
      "decision_rules": [
        {
          "observation_id": "clear",
          "action_id": "monitor"
        },
        {
          "observation_id": "alert",
          "action_id": "repair"
        }
      ],
      "actions": [
        {
          "action_id": "monitor",
          "action_definition": "reviewed synthetic monitoring action",
          "action_model_id": "synthetic.monitor",
          "action_model_revision": "1",
          "action_model_configuration_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
          "action_model_input_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
          "cost_components": [
            {
              "component_id": "monitor",
              "category": "monitoring",
              "amount_at_stage_time": 10.0,
              "present_value_factor": 1.0,
              "basis": "synthetic reviewed factor"
            }
          ]
        },
        {
          "action_id": "repair",
          "action_definition": "reviewed synthetic repair action",
          "action_model_id": "synthetic.repair",
          "action_model_revision": "1",
          "action_model_configuration_sha256": "3333333333333333333333333333333333333333333333333333333333333333",
          "action_model_input_sha256": "4444444444444444444444444444444444444444444444444444444444444444",
          "cost_components": [
            {
              "component_id": "repair",
              "category": "repair",
              "amount_at_stage_time": 50.0,
              "present_value_factor": 1.0,
              "basis": "synthetic reviewed factor"
            }
          ]
        }
      ],
      "transition_probabilities": [
        {
          "from_state_id": "healthy",
          "action_id": "monitor",
          "to_state_id": "healthy",
          "probability_given_state_and_action": 0.95,
          "failure_consequence_present_value_factor": null
        },
        {
          "from_state_id": "healthy",
          "action_id": "monitor",
          "to_state_id": "failure",
          "probability_given_state_and_action": 0.05,
          "failure_consequence_present_value_factor": 0.9
        },
        {
          "from_state_id": "healthy",
          "action_id": "repair",
          "to_state_id": "healthy",
          "probability_given_state_and_action": 1.0,
          "failure_consequence_present_value_factor": null
        },
        {
          "from_state_id": "degraded",
          "action_id": "monitor",
          "to_state_id": "degraded",
          "probability_given_state_and_action": 0.7,
          "failure_consequence_present_value_factor": null
        },
        {
          "from_state_id": "degraded",
          "action_id": "monitor",
          "to_state_id": "failure",
          "probability_given_state_and_action": 0.3,
          "failure_consequence_present_value_factor": 0.9
        },
        {
          "from_state_id": "degraded",
          "action_id": "repair",
          "to_state_id": "healthy",
          "probability_given_state_and_action": 0.9,
          "failure_consequence_present_value_factor": null
        },
        {
          "from_state_id": "degraded",
          "action_id": "repair",
          "to_state_id": "failure",
          "probability_given_state_and_action": 0.1,
          "failure_consequence_present_value_factor": 0.9
        }
      ]
    }
  ],
  "maximum_probability_sum_error": 1e-12,
  "maximum_generated_paths": 20,
  "state_space_reviewed": true,
  "initial_distribution_reviewed": true,
  "observation_models_reviewed": true,
  "decision_rules_reviewed": true,
  "transition_models_reviewed": true,
  "action_costs_and_discount_factors_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-finite-policy-example",
      "origin": "synthetic",
      "citation": "independently authored finite probability tables"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/inspection.py#L1924)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

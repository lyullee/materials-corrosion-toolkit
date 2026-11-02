# `inspection.multi_period_policy_comparison`

**목적:** At least two complete externally evaluated policies over one common event, scope, horizon, start-survival condition, cost and discount basis; apply caller-approved hard probability and resource constraints before finite expected-loss comparison.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.multi_period_inspection_policy_comparison.v1", "default": "matintegrity.multi_period_inspection_policy_comparison.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `comparison_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `horizon_start_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `horizon_end_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `conditioning` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_probability_meaning` | 예 | `{"const": "conditional_first_failure_in_period", "type": "string"}` | 계약·필드 설명 참조 |
| `cost_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `currency_or_normalized_unit` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `discount_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `probability_basis` | 예 | `{"enum": ["estimate", "upper_bound"], "type": "string"}` | 계약·필드 설명 참조 |
| `maximum_conditional_first_failure_probability` | 예 | `{"maximum": 1, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `resource_constraints` | 아니오 | `{"items": {"$ref": "#/$defs/PolicyResourceConstraint"}, "type": "array"}` | 계약·필드 설명 참조 |
| `candidates` | 예 | `{"items": {"$ref": "#/$defs/MultiPeriodInspectionPolicyCandidate"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `cost_tie_absolute_tolerance` | 아니오 | `{"default": 0.0, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `complete_policy_set_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `policy_evaluations_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `probability_criterion_user_approved` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `resource_constraints_user_approved` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `cost_comparison_user_approved` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/MultiPeriodInspectionPolicyComparison.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `horizon_start_s` | `s` |
| `horizon_end_s` | `s` |
| `maximum_conditional_first_failure_probability` | `1` |
| `conditional_first_failure_probability_for_comparison` | `1` |
| `expected_discounted_total_loss` | `declared_cost_unit` |
| `minimum_constraint_compliant_expected_loss` | `declared_cost_unit` |
| `cost_tie_absolute_tolerance` | `declared_cost_unit` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- At least two complete externally evaluated policies over one common event, scope, horizon, start-survival condition, cost and discount basis; apply caller-approved hard probability and resource constraints before finite expected-loss comparison.

## 구현 근거·독립 설명

- `multi_period_inspection_policy_comparison_definition`: Compare at least two complete externally evaluated multi-period policies only after confirming a common event, physical scope, horizon, start-survival condition, cost basis, currency or normalized unit and discount basis. Preserve every policy and evaluator identity plus configuration/input/result digests, conditional first-failure estimate and optional qualified bound, additive expected-loss components and the exact declared resource set with units and optional bounds. Apply caller-approved hard probability and resource constraints before comparing expected total loss; never relax a constraint when no policy is compliant or break a cost tie arbitrarily. The unique least-loss compliant candidate is only the best member of the supplied reviewed set. Do not generate policies or transitions, infer probabilities, resources, bounds, constraints or costs, claim global optimality, resource scheduling, risk acceptance or regulatory compliance.

확률 의미: `{"maximum_conditional_first_failure_probability": "conditional_first_failure_in_period", "conditional_first_failure_probability_for_comparison": "conditional_first_failure_in_period"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.multi_period_policy_comparison"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.multi_period_policy_comparison"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.multi_period_inspection_policy_comparison.v1",
  "comparison_id": "synthetic-policy-comparison",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "synthetic-wall-location",
  "event_id": "synthetic-first-threshold-crossing",
  "horizon_start_s": 1000.0,
  "horizon_end_s": 2000.0,
  "conditioning": "synthetic integrity function survived through horizon start",
  "event_probability_meaning": "conditional_first_failure_in_period",
  "cost_basis_id": "synthetic-normalized-costs-v1",
  "currency_or_normalized_unit": "normalized_cost_unit",
  "discount_basis_id": "synthetic-reviewed-present-value-factors-v1",
  "probability_basis": "estimate",
  "maximum_conditional_first_failure_probability": 0.15,
  "resource_constraints": [
    {
      "resource_id": "outage-days",
      "unit": "day",
      "comparison_basis": "expected",
      "maximum_usage": 8.0,
      "criterion_basis": "independently authored synthetic hard constraint"
    }
  ],
  "candidates": [
    {
      "policy_id": "synthetic-baseline-policy",
      "policy_revision": "1",
      "policy_definition": "reviewed synthetic baseline policy",
      "policy_configuration_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
      "evaluation_model_id": "inspection.multi_period_policy_evaluation",
      "evaluation_model_revision": "0.1.0",
      "evaluation_configuration_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
      "evaluation_input_sha256": "3333333333333333333333333333333333333333333333333333333333333333",
      "evaluation_result_sha256": "4444444444444444444444444444444444444444444444444444444444444444",
      "asset_id": "synthetic",
      "location_id": "synthetic",
      "physical_scope_id": "synthetic-wall-location",
      "event_id": "synthetic-first-threshold-crossing",
      "horizon_start_s": 1000.0,
      "horizon_end_s": 2000.0,
      "conditioning": "synthetic integrity function survived through horizon start",
      "event_probability_meaning": "conditional_first_failure_in_period",
      "cost_basis_id": "synthetic-normalized-costs-v1",
      "currency_or_normalized_unit": "normalized_cost_unit",
      "discount_basis_id": "synthetic-reviewed-present-value-factors-v1",
      "conditional_first_failure_probability": 0.2,
      "conditional_first_failure_probability_upper_bound": 0.25,
      "expected_discounted_action_cost": 240.0,
      "expected_discounted_failure_consequence": 160.0,
      "expected_discounted_total_loss": 400.0,
      "resource_usage": [
        {
          "resource_id": "outage-days",
          "unit": "day",
          "expected_usage": 10.0,
          "upper_bound_usage": 12.0
        }
      ]
    },
    {
      "policy_id": "synthetic-safer-policy",
      "policy_revision": "1",
      "policy_definition": "reviewed synthetic safer policy",
      "policy_configuration_sha256": "5555555555555555555555555555555555555555555555555555555555555555",
      "evaluation_model_id": "inspection.multi_period_policy_evaluation",
      "evaluation_model_revision": "0.1.0",
      "evaluation_configuration_sha256": "6666666666666666666666666666666666666666666666666666666666666666",
      "evaluation_input_sha256": "7777777777777777777777777777777777777777777777777777777777777777",
      "evaluation_result_sha256": "8888888888888888888888888888888888888888888888888888888888888888",
      "asset_id": "synthetic",
      "location_id": "synthetic",
      "physical_scope_id": "synthetic-wall-location",
      "event_id": "synthetic-first-threshold-crossing",
      "horizon_start_s": 1000.0,
      "horizon_end_s": 2000.0,
      "conditioning": "synthetic integrity function survived through horizon start",
      "event_probability_meaning": "conditional_first_failure_in_period",
      "cost_basis_id": "synthetic-normalized-costs-v1",
      "currency_or_normalized_unit": "normalized_cost_unit",
      "discount_basis_id": "synthetic-reviewed-present-value-factors-v1",
      "conditional_first_failure_probability": 0.08,
      "conditional_first_failure_probability_upper_bound": 0.12,
      "expected_discounted_action_cost": 360.0,
      "expected_discounted_failure_consequence": 90.0,
      "expected_discounted_total_loss": 450.0,
      "resource_usage": [
        {
          "resource_id": "outage-days",
          "unit": "day",
          "expected_usage": 7.0,
          "upper_bound_usage": 9.0
        }
      ]
    },
    {
      "policy_id": "synthetic-cheap-unsafe-policy",
      "policy_revision": "1",
      "policy_definition": "reviewed synthetic low-cost policy that violates the probability criterion",
      "policy_configuration_sha256": "9999999999999999999999999999999999999999999999999999999999999999",
      "evaluation_model_id": "inspection.multi_period_policy_evaluation",
      "evaluation_model_revision": "0.1.0",
      "evaluation_configuration_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evaluation_input_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evaluation_result_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "asset_id": "synthetic",
      "location_id": "synthetic",
      "physical_scope_id": "synthetic-wall-location",
      "event_id": "synthetic-first-threshold-crossing",
      "horizon_start_s": 1000.0,
      "horizon_end_s": 2000.0,
      "conditioning": "synthetic integrity function survived through horizon start",
      "event_probability_meaning": "conditional_first_failure_in_period",
      "cost_basis_id": "synthetic-normalized-costs-v1",
      "currency_or_normalized_unit": "normalized_cost_unit",
      "discount_basis_id": "synthetic-reviewed-present-value-factors-v1",
      "conditional_first_failure_probability": 0.3,
      "conditional_first_failure_probability_upper_bound": 0.35,
      "expected_discounted_action_cost": 150.0,
      "expected_discounted_failure_consequence": 150.0,
      "expected_discounted_total_loss": 300.0,
      "resource_usage": [
        {
          "resource_id": "outage-days",
          "unit": "day",
          "expected_usage": 4.0,
          "upper_bound_usage": 5.0
        }
      ]
    }
  ],
  "cost_tie_absolute_tolerance": 0.0,
  "complete_policy_set_reviewed": true,
  "policy_evaluations_reviewed": true,
  "probability_criterion_user_approved": true,
  "resource_constraints_user_approved": true,
  "cost_comparison_user_approved": true,
  "evidence": [
    {
      "source_id": "authored-policy-comparison-example",
      "origin": "synthetic",
      "citation": "independently authored constrained finite policy comparison"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/inspection.py#L2418)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

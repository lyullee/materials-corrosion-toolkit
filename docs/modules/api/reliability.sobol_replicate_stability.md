# `reliability.sobol_replicate_stability`

**목적:** All replicates share exact output, parameter, distribution, dependence, design and evaluator identities.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `output_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `output_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `output_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `parameter_ids` | 예 | `{"items": {"type": "string"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `parameter_distribution_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `distribution_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `dependence_assumption_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `design_family_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `design_family_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `evaluator_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `evaluator_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `evaluator_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `replicates` | 예 | `{"items": {"$ref": "#/$defs/SobolEstimateReplicate"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_replicate_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_first_order_replicate_range` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_total_order_replicate_range` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_pooled_sample_standard_deviation` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_reported_estimator_uncertainty` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `rank_tie_tolerance` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `output_parameter_distribution_and_dependence_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `design_family_and_evaluator_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `replicate_independence_ids_and_seeds_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `complete_parameter_sets_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `estimator_uncertainty_ess_and_sample_counts_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `result_digests_and_missingness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `diagnostic_tolerances_and_rank_definition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/SobolReplicateStabilityAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `output_id` | `1` |
| `parameter_ids` | `1` |
| `replicate_ids` | `1` |
| `replicate_seeds` | `1` |
| `sample_counts` | `sample` |
| `effective_sample_sizes` | `sample` |
| `parameter_diagnostics` | `mixed` |
| `first_order_unstable_parameter_pairs` | `1` |
| `total_order_unstable_parameter_pairs` | `1` |
| `rank_order_stable_at_declared_tie_tolerance` | `1` |
| `dispersion_criteria_satisfied` | `1` |
| `all_declared_stability_criteria_satisfied` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- All replicates share exact output, parameter, distribution, dependence, design and evaluator identities.
- Replicate IDs and seeds are unique and every replicate contains the complete parameter set.
- Stability diagnostics do not prove convergence, causality or physical-model validity.

## 구현 근거·독립 설명

- `caller_supplied_sobol_replicate_estimates`: Reduce complete caller-supplied replicate first/total Sobol estimates with equal-replicate means, dispersion and pairwise rank-stability diagnostics under exact common distribution, dependence, design and evaluator identities. Do not execute an evaluator, estimate new indices, reinterpret dependent-input indices, or claim convergence, causality or validation.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "reliability.sobol_replicate_stability"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["reliability.sobol_replicate_stability"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "output_id": "output-1",
  "output_definition": "caller scalar response",
  "output_unit_token": "custom-output-unit",
  "parameter_ids": [
    "parameter-a",
    "parameter-b"
  ],
  "parameter_distribution_id": "distribution-1",
  "distribution_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "dependence_assumption_id": "caller-independent-marginals",
  "design_family_id": "sobol-design-family-1",
  "design_family_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "evaluator_id": "evaluator-1",
  "evaluator_revision": "revision-1",
  "evaluator_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "replicates": [
    {
      "replicate_id": "replicate-1",
      "seed": 101,
      "output_id": "output-1",
      "output_definition": "caller scalar response",
      "output_unit_token": "custom-output-unit",
      "parameter_distribution_id": "distribution-1",
      "distribution_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "dependence_assumption_id": "caller-independent-marginals",
      "design_family_id": "sobol-design-family-1",
      "design_family_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evaluator_id": "evaluator-1",
      "evaluator_revision": "revision-1",
      "evaluator_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "sample_count": 100,
      "effective_sample_size": 80.0,
      "parameter_estimates": [
        {
          "parameter_id": "parameter-a",
          "first_order_index": 0.7,
          "total_order_index": 0.8,
          "first_order_estimator_uncertainty": 0.02,
          "total_order_estimator_uncertainty": 0.025,
          "uncertainty_definition": "caller standard error"
        },
        {
          "parameter_id": "parameter-b",
          "first_order_index": 0.2,
          "total_order_index": 0.3,
          "first_order_estimator_uncertainty": 0.015,
          "total_order_estimator_uncertainty": 0.02,
          "uncertainty_definition": "caller standard error"
        }
      ],
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored Sobol replicate"
        }
      ]
    },
    {
      "replicate_id": "replicate-2",
      "seed": 102,
      "output_id": "output-1",
      "output_definition": "caller scalar response",
      "output_unit_token": "custom-output-unit",
      "parameter_distribution_id": "distribution-1",
      "distribution_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "dependence_assumption_id": "caller-independent-marginals",
      "design_family_id": "sobol-design-family-1",
      "design_family_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evaluator_id": "evaluator-1",
      "evaluator_revision": "revision-1",
      "evaluator_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "sample_count": 100,
      "effective_sample_size": 80.0,
      "parameter_estimates": [
        {
          "parameter_id": "parameter-a",
          "first_order_index": 0.71,
          "total_order_index": 0.81,
          "first_order_estimator_uncertainty": 0.02,
          "total_order_estimator_uncertainty": 0.025,
          "uncertainty_definition": "caller standard error"
        },
        {
          "parameter_id": "parameter-b",
          "first_order_index": 0.21,
          "total_order_index": 0.31,
          "first_order_estimator_uncertainty": 0.015,
          "total_order_estimator_uncertainty": 0.02,
          "uncertainty_definition": "caller standard error"
        }
      ],
      "result_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored Sobol replicate"
        }
      ]
    },
    {
      "replicate_id": "replicate-3",
      "seed": 103,
      "output_id": "output-1",
      "output_definition": "caller scalar response",
      "output_unit_token": "custom-output-unit",
      "parameter_distribution_id": "distribution-1",
      "distribution_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "dependence_assumption_id": "caller-independent-marginals",
      "design_family_id": "sobol-design-family-1",
      "design_family_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evaluator_id": "evaluator-1",
      "evaluator_revision": "revision-1",
      "evaluator_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "sample_count": 100,
      "effective_sample_size": 80.0,
      "parameter_estimates": [
        {
          "parameter_id": "parameter-a",
          "first_order_index": 0.69,
          "total_order_index": 0.79,
          "first_order_estimator_uncertainty": 0.02,
          "total_order_estimator_uncertainty": 0.025,
          "uncertainty_definition": "caller standard error"
        },
        {
          "parameter_id": "parameter-b",
          "first_order_index": 0.19,
          "total_order_index": 0.29,
          "first_order_estimator_uncertainty": 0.015,
          "total_order_estimator_uncertainty": 0.02,
          "uncertainty_definition": "caller standard error"
        }
      ],
      "result_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored Sobol replicate"
        }
      ]
    }
  ],
  "minimum_replicate_count": 3,
  "maximum_first_order_replicate_range": 0.05,
  "maximum_total_order_replicate_range": 0.05,
  "maximum_pooled_sample_standard_deviation": 0.02,
  "maximum_reported_estimator_uncertainty": 0.03,
  "rank_tie_tolerance": 0.01,
  "output_parameter_distribution_and_dependence_identity_reviewed": true,
  "design_family_and_evaluator_identity_reviewed": true,
  "replicate_independence_ids_and_seeds_reviewed": true,
  "complete_parameter_sets_reviewed": true,
  "estimator_uncertainty_ess_and_sample_counts_reviewed": true,
  "result_digests_and_missingness_reviewed": true,
  "diagnostic_tolerances_and_rank_definition_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/sobol_replicate_stability.py#L167)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

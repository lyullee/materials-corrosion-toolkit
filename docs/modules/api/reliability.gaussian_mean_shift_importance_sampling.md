# `reliability.gaussian_mean_shift_importance_sampling`

**목적:** Caller-reviewed samples are drawn from an independent unit-normal mean-shift proposal in a named latent space and evaluated by one deterministic finite-period event indicator.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.gaussian_mean_shift_importance_sampling.v1", "default": "matintegrity.gaussian_mean_shift_importance_sampling.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `estimate_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `horizon_start_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `horizon_end_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `conditioning` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_probability_meaning` | 예 | `{"const": "conditional_first_failure_in_period", "type": "string"}` | 계약·필드 설명 참조 |
| `latent_variable_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 64, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `target_distribution` | 아니오 | `{"const": "independent_standard_normal", "default": "independent_standard_normal", "type": "string"}` | 계약·필드 설명 참조 |
| `proposal_distribution` | 아니오 | `{"const": "independent_unit_normal_mean_shift", "default": "independent_unit_normal_mean_shift", "type": "string"}` | 계약·필드 설명 참조 |
| `proposal_shift` | 예 | `{"items": {"type": "number"}, "type": "array"}` | 계약·필드 설명 참조 |
| `sample_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 2000000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `proposal_samples` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 2000000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `event_indicators` | 예 | `{"items": {"type": "boolean"}, "maxItems": 2000000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `design_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `design_content_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `proposal_generator_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `proposal_generator_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `latent_mapping_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `latent_mapping_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `latent_mapping_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `evaluator_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `evaluator_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `evaluator_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `confidence_level` | 아니오 | `{"default": 0.95, "exclusiveMaximum": 1.0, "exclusiveMinimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |
| `samples_drawn_from_declared_proposal` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sample_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `latent_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `event_indicator_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `deterministic_evaluator_declared` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GaussianMeanShiftImportanceSampling.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `probability_given_survival` | `1` |
| `raw_importance_estimate` | `1` |
| `log_probability_estimate` | `1` |
| `probability_standard_error` | `1` |
| `log_probability_standard_error` | `1` |
| `normal_confidence_level` | `1` |
| `normal_confidence_interval_raw` | `1` |
| `normal_confidence_interval_bounded` | `1` |
| `self_normalized_probability_diagnostic` | `1` |
| `sample_count` | `count` |
| `observed_event_count` | `count` |
| `proposal_event_fraction` | `1` |
| `proposal_shift_norm` | `1` |
| `importance_weight_mean` | `1` |
| `log_importance_weight_mean` | `1` |
| `effective_sample_size` | `count` |
| `effective_sample_fraction` | `1` |
| `maximum_normalized_weight` | `1` |
| `importance_weight_coefficient_of_variation` | `1` |
| `event_weight_effective_sample_size` | `count` |
| `sample_ids` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-reviewed samples are drawn from an independent unit-normal mean-shift proposal in a named latent space and evaluated by one deterministic finite-period event indicator.
- The exact Gaussian target-to-proposal likelihood ratio is used without clipping; latent mapping, event semantics, horizon, conditioning and evaluator identity remain external reviewed inputs.
- Estimator diagnostics quantify Monte Carlo behavior only and do not cover input-distribution, mapping, model-form, physical-data or consequence uncertainty.

## 구현 근거·독립 설명

- `gaussian_mean_shift_importance_sampling_derivation`: For a target vector of independent standard-normal latent coordinates and a proposal with the same unit covariance plus a caller-declared mean shift, evaluate the exact log likelihood ratio as minus the shift dot the proposal sample plus one half the squared shift norm. Average the likelihood ratio times a separately evaluated binary event indicator without clipping or self-normalizing. Compute finite-sample variance, normal-approximation interval, normalized-weight effective sample size and event-weight effective sample size as Monte Carlo diagnostics. Preserve the latent mapping, event, physical scope, horizon, survival conditioning, design and evaluator identities. Independence in latent coordinates does not assert independence of mapped physical inputs; estimator diagnostics do not cover input-distribution, mapping, evaluator, model-form, physical-data or consequence uncertainty.

확률 의미: `{"probability_given_survival": "conditional_first_failure_in_period"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "reliability.gaussian_mean_shift_importance_sampling"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["reliability.gaussian_mean_shift_importance_sampling"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "estimate_id": "synthetic-rare-event-estimate",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "demo-pressure-boundary",
  "time_basis": "API contract check",
  "horizon_start_s": 0.0,
  "horizon_end_s": 1000.0,
  "conditioning": "demo asset survived to mission start",
  "event_id": "demo-first-failure",
  "event_definition": "authored demonstration event in the declared interval",
  "event_probability_meaning": "conditional_first_failure_in_period",
  "latent_variable_ids": [
    "standardized-load"
  ],
  "proposal_shift": [
    2.0
  ],
  "sample_ids": [
    "sample-0",
    "sample-1",
    "sample-2",
    "sample-3"
  ],
  "proposal_samples": [
    [
      1.0
    ],
    [
      2.0
    ],
    [
      3.0
    ],
    [
      4.0
    ]
  ],
  "event_indicators": [
    false,
    false,
    true,
    true
  ],
  "design_id": "authored-demo-design",
  "design_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "proposal_generator_id": "authored-example",
  "proposal_generator_revision": "1",
  "latent_mapping_id": "authored-example-mapping",
  "latent_mapping_revision": "1",
  "latent_mapping_configuration_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "evaluator_id": "authored-example-limit-state",
  "evaluator_revision": "1",
  "evaluator_configuration_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "confidence_level": 0.95,
  "samples_drawn_from_declared_proposal": true,
  "sample_alignment_reviewed": true,
  "latent_mapping_reviewed": true,
  "event_indicator_reviewed": true,
  "deterministic_evaluator_declared": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/reliability.py#L153)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

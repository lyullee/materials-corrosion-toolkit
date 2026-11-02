# `reliability.gaussian_thickness_posterior_sample_design`

**목적:** Caller-reviewed two-dimensional Gaussian posterior for reference-time thickness and signed constant loss rate at one physical location.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.gaussian_thickness_posterior_sample_design.v1", "default": "matintegrity.gaussian_thickness_posterior_sample_design.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `sample_design_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `posterior_definition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `posterior_source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `posterior_reference_time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `assessment_time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `posterior_remaining_thickness_at_reference_mean_m` | 예 | `{"type": "number"}` | m |
| `posterior_loss_rate_mean_m_s` | 예 | `{"type": "number"}` | m/s |
| `posterior_covariance` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "type": "array"}` | 계약·필드 설명 참조 |
| `required_thickness_m` | 예 | `{"minimum": 0, "type": "number"}` | m |
| `requested_accepted_sample_count` | 예 | `{"maximum": 100000, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_candidate_draw_multiplier` | 예 | `{"maximum": 1000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `random_seed_uint64` | 예 | `{"maximum": 18446744073709551615, "minimum": 0, "type": "integer"}` | 계약·필드 설명 참조 |
| `covariance_symmetry_tolerance` | 아니오 | `{"default": 1e-24, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `posterior_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `covariance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `assessment_conditioning_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `required_thickness_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `deterministic_sampler_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GaussianThicknessPosteriorSampleDesign.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_time_s` | `s` |
| `required_thickness_m` | `m` |
| `accepted_sample_count` | `count` |
| `candidate_draw_count` | `count` |
| `maximum_candidate_draw_count` | `count` |
| `negative_loss_rate_candidate_count` | `count` |
| `non_surviving_candidate_count` | `count` |
| `both_condition_failures_count` | `count` |
| `empirical_acceptance_fraction` | `1` |
| `samples` | `mixed SI [m,m/s,1]` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-reviewed two-dimensional Gaussian posterior for reference-time thickness and signed constant loss rate at one physical location.
- A versioned deterministic draw stream preserves thickness-rate correlation and uses explicit rejection to condition on nonnegative rate and assessment-time survival.
- The conditional sample design supplies no process noise, nonlinear growth, intervention, confidence bound, field calibration or constant-rate qualification.

## 구현 근거·독립 설명

- `gaussian_thickness_posterior_sampling_derivation`: Generate a finite reproducible joint design from a caller-reviewed two-parameter Gaussian posterior for reference-time thickness and signed constant loss rate. Use an explicitly versioned SplitMix64 integer stream, open-unit conversion, Box-Muller standard-normal pair and analytical two-dimensional Cholesky map so the draw algorithm does not depend on a library distribution implementation. Preserve thickness-rate correlation and accept only rows with nonnegative loss rate and remaining thickness strictly above the reviewed threshold at assessment. Stop at a fixed candidate budget and return no partial design when the requested conditional count is unavailable. This conditioning operation supplies no process noise, nonlinear growth, intervention, confidence bound, field calibration or constant-rate qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "reliability.gaussian_thickness_posterior_sample_design"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["reliability.gaussian_thickness_posterior_sample_design"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "sample_design_id": "synthetic-posterior-sample-design",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "synthetic-wall-location",
  "physical_location_id": "synthetic",
  "time_basis": "API contract check",
  "posterior_definition_id": "synthetic-linear-gaussian-posterior",
  "posterior_source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "posterior_reference_time_s": 0.0,
  "assessment_time_s": 1000000.0,
  "posterior_remaining_thickness_at_reference_mean_m": 0.012,
  "posterior_loss_rate_mean_m_s": 1e-10,
  "posterior_covariance": [
    [
      1.6e-07,
      -1.4e-15
    ],
    [
      -1.4e-15,
      1e-20
    ]
  ],
  "required_thickness_m": 0.006,
  "requested_accepted_sample_count": 32,
  "maximum_candidate_draw_multiplier": 4,
  "random_seed_uint64": 20261027,
  "covariance_symmetry_tolerance": 1e-24,
  "posterior_basis_reviewed": true,
  "covariance_reviewed": true,
  "assessment_conditioning_reviewed": true,
  "required_thickness_basis_reviewed": true,
  "deterministic_sampler_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/reliability.py#L1430)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

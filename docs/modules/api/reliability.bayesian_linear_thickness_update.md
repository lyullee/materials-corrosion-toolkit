# `reliability.bayesian_linear_thickness_update`

**목적:** Caller-reviewed Gaussian prior and thickness measurement-error model for one physical location under a constant linear thickness-loss relation.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `update_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reference_time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `prior_remaining_thickness_mean_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `prior_loss_rate_mean_m_s` | 예 | `{"type": "number"}` | m/s |
| `prior_remaining_thickness_standard_deviation_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `prior_loss_rate_standard_deviation_m_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m/s |
| `prior_thickness_loss_rate_correlation` | 예 | `{"exclusiveMaximum": 1.0, "exclusiveMinimum": -1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `prior_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `prior_source_content_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `linear_model_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `measurement_error_model_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `prediction_support_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/ThicknessObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `measurement_error_covariance_m2` | 아니오 | `{"anyOf": [{"items": {"items": {"type": "number"}, "type": "array"}, "type": "array"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `measurement_errors_independent_declared` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `prediction_times_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 1000, "minItems": 1, "type": "array"}` | s |
| `credible_level` | 예 | `{"exclusiveMaximum": 1.0, "exclusiveMinimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |
| `required_thickness_m` | 아니오 | `{"anyOf": [{"minimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | m |
| `prior_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `constant_linear_model_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_identities_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `measurement_error_model_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `prediction_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `required_thickness_basis_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `holdout_source_independence_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `covariance_symmetry_tolerance_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/BayesianLinearThicknessUpdate.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `update_observation_ids` | `1` |
| `holdout_observation_ids` | `1` |
| `measurement_error_basis` | `1` |
| `posterior_remaining_thickness_at_reference_mean_m` | `m` |
| `posterior_loss_rate_mean_m_s` | `m/s` |
| `posterior_covariance` | `mixed SI covariance [m,m/s]` |
| `posterior_remaining_thickness_standard_deviation_m` | `m` |
| `posterior_loss_rate_standard_deviation_m_s` | `m/s` |
| `posterior_thickness_loss_rate_correlation` | `1` |
| `probability_loss_rate_positive` | `1` |
| `prediction_times_s` | `s` |
| `predicted_remaining_thickness_mean_m` | `m` |
| `predicted_remaining_thickness_standard_deviation_m` | `m` |
| `credible_level` | `1` |
| `predicted_remaining_thickness_credible_lower_m` | `m` |
| `predicted_remaining_thickness_credible_upper_m` | `m` |
| `required_thickness_m` | `m` |
| `probability_below_required_thickness` | `1` |
| `holdout_residuals_m` | `m` |
| `holdout_standardized_residuals` | `1` |
| `holdout_source_independence_status` | `1` |
| `overlapping_holdout_source_group_ids` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-reviewed Gaussian prior and thickness measurement-error model for one physical location under a constant linear thickness-loss relation.
- Calibration and holdout partitions are fixed before updating; holdout observations never influence the posterior.
- No process noise, model-form uncertainty, POD, missed flaws, interventions or period first-passage calculation is included.

## 구현 근거·독립 설명

- `bayesian_linear_thickness_update_derivation`: Represent remaining thickness at one reviewed physical location by a two-parameter constant-linear Gaussian state: thickness at a declared reference time and signed loss rate. Condition a caller-supplied Gaussian prior on a predeclared update partition using reviewed Gaussian measurement errors, while keeping holdout rows outside the posterior. Propagate the posterior analytically to caller-supplied times and report any required-thickness exceedance only as a point-in-time model-implied state probability. This derivation supplies no process noise, model-form uncertainty, POD, first-passage probability, intervention model or acceptance criterion.

확률 의미: `{"probability_loss_rate_positive": "posterior_parameter_probability", "probability_below_required_thickness": "point_in_time_state_probability"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "reliability.bayesian_linear_thickness_update"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["reliability.bayesian_linear_thickness_update"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "update_id": "synthetic-linear-thickness-update",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "synthetic-pipe-course",
  "physical_location_id": "synthetic-cml-1",
  "time_basis": "API contract check",
  "reference_time_s": 0.0,
  "prior_remaining_thickness_mean_m": 0.012,
  "prior_loss_rate_mean_m_s": 1e-10,
  "prior_remaining_thickness_standard_deviation_m": 0.001,
  "prior_loss_rate_standard_deviation_m_s": 8e-10,
  "prior_thickness_loss_rate_correlation": 0.1,
  "prior_basis_id": "synthetic-reviewed-prior",
  "prior_source_content_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "linear_model_basis_id": "synthetic-constant-linear",
  "measurement_error_model_id": "synthetic-independent-ut-error",
  "prediction_support_id": "synthetic-time-support",
  "observations": [
    {
      "observation_id": "synthetic-update-1",
      "campaign_id": "synthetic-campaign-a",
      "physical_location_id": "synthetic-cml-1",
      "elapsed_time_s": 0.0,
      "remaining_thickness_m": 0.0118,
      "measurement_standard_deviation_m": 0.0002,
      "partition": "update",
      "source_group_id": "synthetic-campaign-a",
      "measurement_method_id": "synthetic-ut",
      "calibration_id": "synthetic-block",
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "test_validity_reviewed": true
    },
    {
      "observation_id": "synthetic-update-2",
      "campaign_id": "synthetic-campaign-a",
      "physical_location_id": "synthetic-cml-1",
      "elapsed_time_s": 1000000.0,
      "remaining_thickness_m": 0.011,
      "measurement_standard_deviation_m": 0.0002,
      "partition": "update",
      "source_group_id": "synthetic-campaign-a",
      "measurement_method_id": "synthetic-ut",
      "calibration_id": "synthetic-block",
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "test_validity_reviewed": true
    }
  ],
  "measurement_error_covariance_m2": null,
  "measurement_errors_independent_declared": true,
  "prediction_times_s": [
    0.0,
    2000000.0
  ],
  "credible_level": 0.95,
  "required_thickness_m": 0.009,
  "prior_basis_reviewed": true,
  "constant_linear_model_reviewed": true,
  "observation_identities_reviewed": true,
  "measurement_error_model_reviewed": true,
  "prediction_support_reviewed": true,
  "required_thickness_basis_reviewed": true,
  "holdout_source_independence_reviewed": false,
  "covariance_symmetry_tolerance_m2": 1e-18
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/reliability.py#L908)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

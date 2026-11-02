# `reliability.linear_thickness_state_space_update`

**목적:** Caller-reviewed two-state linear thickness/loss-rate transition with additive covariance rate and independent sequential thickness-measurement errors.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.linear_thickness_state_space_update.v1", "default": "matintegrity.linear_thickness_state_space_update.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `update_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `initial_state_time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `initial_remaining_thickness_mean_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `initial_loss_rate_mean_m_s` | 예 | `{"type": "number"}` | m/s |
| `initial_remaining_thickness_standard_deviation_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `initial_loss_rate_standard_deviation_m_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m/s |
| `initial_thickness_loss_rate_correlation` | 예 | `{"exclusiveMaximum": 1.0, "exclusiveMinimum": -1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `prior_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `prior_source_content_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `transition_model_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `process_noise_model_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `process_noise_covariance_rate` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "type": "array"}` | 계약·필드 설명 참조 |
| `measurement_error_model_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/ThicknessObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `measurement_errors_independent_declared` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `analysis_end_time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `prediction_times_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 1000, "minItems": 1, "type": "array"}` | s |
| `credible_level` | 예 | `{"exclusiveMaximum": 1.0, "exclusiveMinimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |
| `required_thickness_m` | 아니오 | `{"anyOf": [{"minimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | m |
| `prior_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `transition_model_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `process_noise_model_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_identities_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `measurement_error_model_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `prediction_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `required_thickness_basis_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `holdout_source_independence_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/LinearThicknessStateSpaceUpdate.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `observation_diagnostics` | `mixed SI [s,m,m/s,m^2,m^2/s,m^2/s^2,1]` |
| `state_time_s` | `s` |
| `posterior_remaining_thickness_at_state_time_mean_m` | `m` |
| `posterior_loss_rate_mean_m_s` | `m/s` |
| `posterior_covariance` | `mixed SI covariance [m,m/s]` |
| `posterior_remaining_thickness_standard_deviation_m` | `m` |
| `posterior_loss_rate_standard_deviation_m_s` | `m/s` |
| `posterior_thickness_loss_rate_correlation` | `1` |
| `probability_loss_rate_positive` | `1` |
| `prediction_times_s` | `s` |
| `predicted_remaining_thickness_mean_m` | `m` |
| `predicted_remaining_thickness_standard_deviation_m` | `m` |
| `predicted_remaining_thickness_credible_lower_m` | `m` |
| `predicted_remaining_thickness_credible_upper_m` | `m` |
| `required_thickness_m` | `m` |
| `probability_below_required_thickness` | `1` |
| `process_noise_covariance_rate` | `mixed SI covariance rate [m,m/s] per s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-reviewed two-state linear thickness/loss-rate transition with additive covariance rate and independent sequential thickness-measurement errors.
- Update and holdout rows are chronological and distinct; holdout values never alter the filtered state.
- The filter supplies no process-noise calibration, smoother, nonlinear growth, intervention, POD, first-passage probability or field qualification.

## 구현 근거·독립 설명

- `linear_thickness_state_space_filter_derivation`: Represent remaining thickness and signed loss rate as a two-state linear Gaussian process. Propagate each caller-ordered interval with the constant-rate transition and add a reviewed full two-by-two state covariance rate multiplied by elapsed time. Apply scalar thickness observations sequentially with the Joseph covariance update, while predeclared holdout rows produce one-step-ahead residuals without changing the state. Propagate the final filtered state and uncertainty to requested times. This filter does not estimate its process noise, smooth past states, model nonlinear degradation, incorporate intervention or inspection effectiveness, or turn point-in-time state probabilities into first-passage probabilities.

확률 의미: `{"probability_loss_rate_positive": "posterior_parameter_probability", "probability_below_required_thickness": "point_in_time_state_probability"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "reliability.linear_thickness_state_space_update"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["reliability.linear_thickness_state_space_update"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "update_id": "synthetic-state-space-update",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "synthetic-wall-location",
  "physical_location_id": "synthetic",
  "time_basis": "API contract check",
  "initial_state_time_s": 0.0,
  "initial_remaining_thickness_mean_m": 0.012,
  "initial_loss_rate_mean_m_s": 1e-10,
  "initial_remaining_thickness_standard_deviation_m": 0.0008,
  "initial_loss_rate_standard_deviation_m_s": 5e-11,
  "initial_thickness_loss_rate_correlation": -0.2,
  "prior_basis_id": "synthetic-reviewed-prior",
  "prior_source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "transition_model_basis_id": "synthetic-constant-linear-transition",
  "process_noise_model_id": "synthetic-additive-covariance-rate",
  "process_noise_covariance_rate": [
    [
      1e-16,
      0.0
    ],
    [
      0.0,
      1e-28
    ]
  ],
  "measurement_error_model_id": "synthetic-independent-errors",
  "observations": [
    {
      "observation_id": "ss-u1",
      "campaign_id": "campaign-1",
      "physical_location_id": "synthetic",
      "elapsed_time_s": 0.0,
      "remaining_thickness_m": 0.0119,
      "measurement_standard_deviation_m": 0.0002,
      "partition": "update",
      "source_group_id": "campaign-1",
      "measurement_method_id": "synthetic-ut",
      "calibration_id": "block-1",
      "source_content_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "test_validity_reviewed": true
    },
    {
      "observation_id": "ss-h1",
      "campaign_id": "holdout-1",
      "physical_location_id": "synthetic",
      "elapsed_time_s": 500000.0,
      "remaining_thickness_m": 0.0118,
      "measurement_standard_deviation_m": 0.0002,
      "partition": "holdout",
      "source_group_id": "holdout-1",
      "measurement_method_id": "synthetic-ut",
      "calibration_id": "block-1",
      "source_content_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "test_validity_reviewed": true
    },
    {
      "observation_id": "ss-u2",
      "campaign_id": "campaign-2",
      "physical_location_id": "synthetic",
      "elapsed_time_s": 1000000.0,
      "remaining_thickness_m": 0.01175,
      "measurement_standard_deviation_m": 0.0002,
      "partition": "update",
      "source_group_id": "campaign-2",
      "measurement_method_id": "synthetic-ut",
      "calibration_id": "block-1",
      "source_content_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "test_validity_reviewed": true
    }
  ],
  "measurement_errors_independent_declared": true,
  "analysis_end_time_s": 1500000.0,
  "prediction_times_s": [
    1500000.0,
    2000000.0
  ],
  "credible_level": 0.95,
  "required_thickness_m": 0.006,
  "prior_basis_reviewed": true,
  "transition_model_reviewed": true,
  "process_noise_model_reviewed": true,
  "observation_identities_reviewed": true,
  "measurement_error_model_reviewed": true,
  "prediction_support_reviewed": true,
  "required_thickness_basis_reviewed": true,
  "holdout_source_independence_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/reliability.py#L1155)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

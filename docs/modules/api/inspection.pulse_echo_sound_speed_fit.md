# `inspection.pulse_echo_sound_speed_fit`

**목적:** Fixed reviewed time zero and incidence angle; through-origin least squares on independently measured reference thicknesses; conditional uncertainty excludes errors in predictors and fixed inputs.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `calibration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `probe_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `wave_mode` | 아니오 | `{"const": "longitudinal", "default": "longitudinal", "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `time_zero_offset_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `incidence_angle_rad` | 예 | `{"exclusiveMaximum": 1.5707963267948966, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `reference_dimension_method` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `fit_method` | 아니오 | `{"default": "ordinary_through_origin", "enum": ["ordinary_through_origin", "iterative_effective_variance"], "type": "string"}` | 계약·필드 설명 참조 |
| `relative_convergence_tolerance` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_iterations` | 아니오 | `{"default": 100, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/PulseEchoCalibrationObservation"}, "minItems": 4, "type": "array"}` | 계약·필드 설명 참조 |
| `timing_and_path_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reference_dimensions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `holdout_partition_predeclared` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PulseEchoSoundSpeedFit.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `temperature_K` | `K` |
| `sound_speed_m_s` | `m/s` |
| `sound_speed_standard_error_m_s` | `m/s` |
| `sound_speed_residual_scaled_standard_error_m_s` | `m/s` |
| `calibration_rmse_m` | `m` |
| `calibration_maximum_absolute_residual_m` | `m` |
| `holdout_rmse_m` | `m` |
| `holdout_maximum_absolute_residual_m` | `m` |
| `holdout_standardized_residual_rmse` | `1` |
| `calibration_reference_thickness_range_m` | `m` |
| `holdout_reference_thickness_range_m` | `m` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Fixed reviewed time zero and incidence angle; through-origin least squares on independently measured reference thicknesses; conditional uncertainty excludes errors in predictors and fixed inputs.

## 구현 근거·독립 설명

- `pulse_echo_sound_speed_fit_derivation`: With a caller-reviewed fixed time-zero offset and incidence angle, convert each positive round-trip time to one-way path time and fit reference thickness as sound speed times that coordinate through the physical zero. Use only predeclared calibration locations and source groups, then evaluate untouched holdout locations and groups. Ordinary fitting reports residual-conditional uncertainty. The optional iterative effective-variance fit weights each row by the sum of declared independent thickness variance and slope-scaled time variance, reports reduced chi-square and evaluates standardized holdout residuals. Return an explicitly unreviewed calibration fragment with no sample applicability. Neither fit covers shared time-zero, angle, temperature, coupling, probe, material-heterogeneity or model-form uncertainty and neither by itself qualifies field thickness measurements.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.pulse_echo_sound_speed_fit"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.pulse_echo_sound_speed_fit"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "calibration_id": "example-reference-block-fit",
  "material_id": "example-reference-steel",
  "probe_id": "example-longitudinal-probe",
  "wave_mode": "longitudinal",
  "temperature_K": 293.15,
  "time_zero_offset_s": 4e-08,
  "incidence_angle_rad": 0.0,
  "reference_dimension_method": "caller-reviewed reference dimensions",
  "observations": [
    {
      "observation_id": "cal-1",
      "physical_location_id": "location-1",
      "source_group_id": "calibration-a",
      "partition": "calibration",
      "reference_thickness_m": 0.004,
      "round_trip_time_s": 1.3959322033898305e-06
    },
    {
      "observation_id": "cal-2",
      "physical_location_id": "location-2",
      "source_group_id": "calibration-a",
      "partition": "calibration",
      "reference_thickness_m": 0.006,
      "round_trip_time_s": 2.073898305084746e-06
    },
    {
      "observation_id": "cal-3",
      "physical_location_id": "location-3",
      "source_group_id": "calibration-b",
      "partition": "calibration",
      "reference_thickness_m": 0.008,
      "round_trip_time_s": 2.751864406779661e-06
    },
    {
      "observation_id": "holdout-1",
      "physical_location_id": "location-4",
      "source_group_id": "holdout-a",
      "partition": "holdout",
      "reference_thickness_m": 0.009,
      "round_trip_time_s": 3.090847457627119e-06
    }
  ],
  "timing_and_path_reviewed": true,
  "reference_dimensions_reviewed": true,
  "holdout_partition_predeclared": true,
  "evidence": [
    {
      "source_id": "example-reference-block",
      "origin": "synthetic",
      "citation": "authored API demonstration",
      "license_id": "MIT"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/inspection.py#L114)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

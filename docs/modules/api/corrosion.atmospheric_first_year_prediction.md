# `corrosion.atmospheric_first_year_prediction`

**목적:** Uses only a reviewed AtmosphericFirstYearModel over one first-year atmospheric carbon-steel exposure and explicit environmental covariates.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `prediction_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `exposure_environment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `exposure_start_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `exposure_duration_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `model` | 예 | `{"$ref": "#/$defs/AtmosphericFirstYearModel"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `relative_humidity_fraction` | 예 | `{"maximum": 1.0, "minimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |
| `chloride_deposition_mg_m2_day` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `sulfur_dioxide_deposition_mg_m2_day` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `confidence_level` | 아니오 | `{"default": 0.95, "exclusiveMaximum": 1.0, "exclusiveMinimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |
| `first_year_atmospheric_carbon_steel_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `covariates_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `model_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `extrapolation_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `limited_transfer_override_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AtmosphericFirstYearPrediction.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `predicted_first_year_loss_m` | `m` |
| `equivalent_first_year_rate_m_s` | `m/s` |
| `predicted_log_first_year_loss_m` | `log(m)` |
| `conditional_mean_standard_error_log_m` | `log(m)` |
| `conditional_prediction_standard_deviation_log_m` | `log(m)` |
| `conditional_prediction_level` | `1` |
| `conditional_prediction_interval_first_year_loss_m` | `m` |
| `support_checks` | `1` |
| `outside_support_fields` | `1` |
| `extrapolation_used` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Uses only a reviewed AtmosphericFirstYearModel over one first-year atmospheric carbon-steel exposure and explicit environmental covariates.
- Calibration-support departures stop unless extrapolation is explicitly reviewed; conditional intervals exclude model-form and covariate uncertainty.

## 구현 근거·독립 설명

- `atmospheric_first_year_loglinear_prediction_derivation`: Evaluate the fixed atmospheric log-linear feature vector and exponentiate the predicted log loss. Form a conditional prediction interval from coefficient covariance plus residual variance. Stop outside calibration support unless extrapolation is reviewed, and stop when source-separated transfer criteria failed unless a limited-transfer override is explicitly reviewed. The interval excludes covariate, source, model-form and population uncertainty.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.atmospheric_first_year_prediction"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["corrosion.atmospheric_first_year_prediction"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "prediction_id": "synthetic-atmospheric-prediction",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "external-wall",
  "material_condition_id": "synthetic-carbon-steel",
  "exposure_environment_id": "synthetic-atmosphere",
  "time_basis": "API contract check",
  "exposure_start_s": 0.0,
  "exposure_duration_s": 31557600.0,
  "model": {
    "model_id": "synthetic-atmospheric-model",
    "fit_id": "synthetic-atmospheric-fit",
    "coefficient_log_m": -11.0,
    "coefficient_temperature_per_10_K": 0.2,
    "coefficient_relative_humidity_per_0_1": 0.3,
    "coefficient_log1p_chloride": 0.4,
    "coefficient_log1p_sulfur_dioxide": 0.1,
    "coefficient_covariance": [
      [
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0
      ],
      [
        0,
        0,
        0,
        0,
        0
      ]
    ],
    "residual_standard_deviation_log_m": 0.001,
    "calibration_support_temperature_K": [
      280.0,
      305.0
    ],
    "calibration_support_relative_humidity_fraction": [
      0.6,
      0.9
    ],
    "calibration_support_chloride_mg_m2_day": [
      0.0,
      15.0
    ],
    "calibration_support_sulfur_dioxide_mg_m2_day": [
      0.0,
      15.0
    ],
    "calibration_observation_count": 8,
    "calibration_source_group_ids": [
      "cal-a",
      "cal-b"
    ],
    "calibration_input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "holdout_observation_count": 4,
    "holdout_log_rmse": 0.001,
    "holdout_absolute_log_bias": 0.001,
    "holdout_outside_support_fraction": 0.0,
    "maximum_holdout_log_rmse": 0.01,
    "maximum_absolute_holdout_log_bias": 0.01,
    "maximum_holdout_outside_support_fraction": 0.1,
    "transfer_criteria_met": true,
    "holdout_input_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "holdout_source_group_metrics": [
      {
        "source_group_id": "holdout-a",
        "observation_count": 2,
        "log_rmse": 0.001,
        "absolute_log_bias": 0.001,
        "outside_support_count": 0,
        "outside_support_fraction": 0.0
      },
      {
        "source_group_id": "holdout-b",
        "observation_count": 2,
        "log_rmse": 0.001,
        "absolute_log_bias": 0.001,
        "outside_support_count": 0,
        "outside_support_fraction": 0.0
      }
    ],
    "maximum_holdout_source_group_log_rmse": 0.001,
    "maximum_holdout_source_group_absolute_log_bias": 0.001,
    "source_group_transfer_criteria_met": true
  },
  "temperature_K": 292.0,
  "relative_humidity_fraction": 0.77,
  "chloride_deposition_mg_m2_day": 4.0,
  "sulfur_dioxide_deposition_mg_m2_day": 3.0,
  "confidence_level": 0.95,
  "first_year_atmospheric_carbon_steel_scope_reviewed": true,
  "covariates_reviewed": true,
  "model_applicability_reviewed": true,
  "extrapolation_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/atmospheric.py#L397)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

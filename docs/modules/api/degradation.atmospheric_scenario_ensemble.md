# `degradation.atmospheric_scenario_ensemble`

**목적:** Each scenario is independently passed to the registered first-year atmospheric prediction model.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `ensemble_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `scenarios` | 예 | `{"items": {"$ref": "#/$defs/AtmosphericScenario"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `quantile_probabilities` | 아니오 | `{"default": [0.05, 0.5, 0.95], "items": {"type": "number"}, "type": "array"}` | 계약·필드 설명 참조 |
| `independence_assumption_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `scenario_weights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AtmosphericScenarioEnsemble.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `ensemble_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `input_digest` | `1` |
| `scenario_count` | `count` |
| `scenario_rows` | `mixed` |
| `summary` | `mixed` |
| `independence_assumption_used` | `1` |
| `remaining_life_or_probability_generated` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Each scenario is independently passed to the registered first-year atmospheric prediction model.
- Scenario weights and transfer applicability require caller review; no dependence model is introduced.

## 구현 근거·독립 설명

- `authored_atmospheric_scenario_ensemble`: Evaluate every first-year atmospheric scenario through the registered prediction model, preserving each input and output digest. Summarize caller-normalized scenario weights with a weighted arithmetic mean, range, and weighted empirical quantiles. Do not infer the meaning of weights, dependence, multi-year growth, localized penetration, remaining life, acceptance, or failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.atmospheric_scenario_ensemble"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.atmospheric_scenario_ensemble"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "ensemble_id": "ensemble",
  "asset_id": "asset",
  "location_id": "location",
  "scenarios": [
    {
      "scenario_id": "low",
      "weight": 0.5,
      "prediction_input": {
        "prediction_id": "low",
        "asset_id": "asset",
        "location_id": "location",
        "physical_scope_id": "scope",
        "material_condition_id": "carbon-steel",
        "exposure_environment_id": "environment",
        "time_basis": "exposure seconds",
        "exposure_start_s": 0.0,
        "exposure_duration_s": 31557600.0,
        "model": {
          "schema_version": "matintegrity.atmospheric_first_year_model.v1",
          "model_id": "model",
          "fit_id": "fit",
          "feature_definition": "intercept,T_K_minus_288.15_over_10,RH_minus_0.75_over_0.1,log1p_Cl_mg_m2_day,log1p_SO2_mg_m2_day",
          "coefficient_log_m": -11.0,
          "coefficient_temperature_per_10_K": 0.0,
          "coefficient_relative_humidity_per_0_1": 0.0,
          "coefficient_log1p_chloride": 0.0,
          "coefficient_log1p_sulfur_dioxide": 0.0,
          "coefficient_covariance": [
            [
              0.0,
              0.0,
              0.0,
              0.0,
              0.0
            ],
            [
              0.0,
              0.0,
              0.0,
              0.0,
              0.0
            ],
            [
              0.0,
              0.0,
              0.0,
              0.0,
              0.0
            ],
            [
              0.0,
              0.0,
              0.0,
              0.0,
              0.0
            ],
            [
              0.0,
              0.0,
              0.0,
              0.0,
              0.0
            ]
          ],
          "residual_standard_deviation_log_m": 0.0,
          "calibration_support_temperature_K": [
            280.0,
            300.0
          ],
          "calibration_support_relative_humidity_fraction": [
            0.5,
            0.9
          ],
          "calibration_support_chloride_mg_m2_day": [
            0.0,
            10.0
          ],
          "calibration_support_sulfur_dioxide_mg_m2_day": [
            0.0,
            10.0
          ],
          "calibration_observation_count": 12,
          "calibration_source_group_ids": [
            "a",
            "b"
          ],
          "calibration_input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "holdout_observation_count": 4,
          "holdout_log_rmse": 0.1,
          "holdout_absolute_log_bias": 0.1,
          "holdout_outside_support_fraction": 0.0,
          "maximum_holdout_log_rmse": 1.0,
          "maximum_absolute_holdout_log_bias": 1.0,
          "maximum_holdout_outside_support_fraction": 0.2,
          "transfer_criteria_met": true,
          "parameter_uncertainty_scope": "conditional_ols_given_fixed_covariates_and_model_form",
          "holdout_source_group_metrics": [
            {
              "source_group_id": "synthetic-holdout-a",
              "observation_count": 2,
              "log_rmse": 0.1,
              "absolute_log_bias": 0.1,
              "outside_support_count": 0,
              "outside_support_fraction": 0.0
            },
            {
              "source_group_id": "synthetic-holdout-b",
              "observation_count": 2,
              "log_rmse": 0.1,
              "absolute_log_bias": 0.1,
              "outside_support_count": 0,
              "outside_support_fraction": 0.0
            }
          ],
          "maximum_holdout_source_group_log_rmse": 0.1,
          "maximum_holdout_source_group_absolute_log_bias": 0.1,
          "source_group_transfer_criteria_met": true,
          "holdout_input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        },
        "temperature_K": 285.0,
        "relative_humidity_fraction": 0.7,
        "chloride_deposition_mg_m2_day": 2.0,
        "sulfur_dioxide_deposition_mg_m2_day": 1.0,
        "confidence_level": 0.95,
        "first_year_atmospheric_carbon_steel_scope_reviewed": true,
        "covariates_reviewed": true,
        "model_applicability_reviewed": true,
        "extrapolation_reviewed": false,
        "limited_transfer_override_reviewed": false
      }
    },
    {
      "scenario_id": "high",
      "weight": 0.5,
      "prediction_input": {
        "prediction_id": "high",
        "asset_id": "asset",
        "location_id": "location",
        "physical_scope_id": "scope",
        "material_condition_id": "carbon-steel",
        "exposure_environment_id": "environment",
        "time_basis": "exposure seconds",
        "exposure_start_s": 0.0,
        "exposure_duration_s": 31557600.0,
        "model": {
          "schema_version": "matintegrity.atmospheric_first_year_model.v1",
          "model_id": "model",
          "fit_id": "fit",
          "feature_definition": "intercept,T_K_minus_288.15_over_10,RH_minus_0.75_over_0.1,log1p_Cl_mg_m2_day,log1p_SO2_mg_m2_day",
          "coefficient_log_m": -11.0,
          "coefficient_temperature_per_10_K": 0.0,
          "coefficient_relative_humidity_per_0_1": 0.0,
          "coefficient_log1p_chloride": 0.0,
          "coefficient_log1p_sulfur_dioxide": 0.0,
          "coefficient_covariance": [
            [
              0.0,
              0.0,
              0.0,
              0.0,
              0.0
            ],
            [
              0.0,
              0.0,
              0.0,
              0.0,
              0.0
            ],
            [
              0.0,
              0.0,
              0.0,
              0.0,
              0.0
            ],
            [
              0.0,
              0.0,
              0.0,
              0.0,
              0.0
            ],
            [
              0.0,
              0.0,
              0.0,
              0.0,
              0.0
            ]
          ],
          "residual_standard_deviation_log_m": 0.0,
          "calibration_support_temperature_K": [
            280.0,
            300.0
          ],
          "calibration_support_relative_humidity_fraction": [
            0.5,
            0.9
          ],
          "calibration_support_chloride_mg_m2_day": [
            0.0,
            10.0
          ],
          "calibration_support_sulfur_dioxide_mg_m2_day": [
            0.0,
            10.0
          ],
          "calibration_observation_count": 12,
          "calibration_source_group_ids": [
            "a",
            "b"
          ],
          "calibration_input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "holdout_observation_count": 4,
          "holdout_log_rmse": 0.1,
          "holdout_absolute_log_bias": 0.1,
          "holdout_outside_support_fraction": 0.0,
          "maximum_holdout_log_rmse": 1.0,
          "maximum_absolute_holdout_log_bias": 1.0,
          "maximum_holdout_outside_support_fraction": 0.2,
          "transfer_criteria_met": true,
          "parameter_uncertainty_scope": "conditional_ols_given_fixed_covariates_and_model_form",
          "holdout_source_group_metrics": [
            {
              "source_group_id": "synthetic-holdout-a",
              "observation_count": 2,
              "log_rmse": 0.1,
              "absolute_log_bias": 0.1,
              "outside_support_count": 0,
              "outside_support_fraction": 0.0
            },
            {
              "source_group_id": "synthetic-holdout-b",
              "observation_count": 2,
              "log_rmse": 0.1,
              "absolute_log_bias": 0.1,
              "outside_support_count": 0,
              "outside_support_fraction": 0.0
            }
          ],
          "maximum_holdout_source_group_log_rmse": 0.1,
          "maximum_holdout_source_group_absolute_log_bias": 0.1,
          "source_group_transfer_criteria_met": true,
          "holdout_input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        },
        "temperature_K": 295.0,
        "relative_humidity_fraction": 0.7,
        "chloride_deposition_mg_m2_day": 2.0,
        "sulfur_dioxide_deposition_mg_m2_day": 1.0,
        "confidence_level": 0.95,
        "first_year_atmospheric_carbon_steel_scope_reviewed": true,
        "covariates_reviewed": true,
        "model_applicability_reviewed": true,
        "extrapolation_reviewed": false,
        "limited_transfer_override_reviewed": false
      }
    }
  ],
  "quantile_probabilities": [
    0.05,
    0.5,
    0.95
  ],
  "independence_assumption_reviewed": true,
  "scenario_weights_reviewed": true,
  "evidence": [
    {
      "source_id": "fixture",
      "origin": "synthetic",
      "citation": "authored fixture",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/atmospheric_ensemble.py#L63)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

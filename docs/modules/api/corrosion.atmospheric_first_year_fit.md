# `corrosion.atmospheric_first_year_fit`

**목적:** Conditional log-linear first-year atmospheric carbon-steel loss model with temperature, relative humidity, chloride and sulfur-dioxide covariates.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `fit_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `model_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/AtmosphericFirstYearFitRow"}, "minItems": 12, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_calibration_source_groups` | 아니오 | `{"default": 2, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_source_groups` | 아니오 | `{"default": 2, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_holdout_log_rmse` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_absolute_holdout_log_bias` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_holdout_outside_support_fraction` | 예 | `{"maximum": 1.0, "minimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |
| `source_group_partition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `first_year_endpoint_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `atmospheric_carbon_steel_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `covariate_origin_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `aggregate_analysis_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pointwise_redistribution_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AtmosphericFirstYearFit.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `model` | `1` |
| `calibration_metrics` | `1` |
| `holdout_metrics` | `1` |
| `holdout_observation_count` | `count` |
| `holdout_source_group_ids` | `1` |
| `holdout_outside_calibration_support_count` | `count` |
| `holdout_outside_calibration_support_observation_ids` | `1` |
| `design_rank` | `count` |
| `design_condition_number` | `1` |
| `pointwise_redistribution_authorized` | `1` |
| `transfer_criteria_met` | `1` |
| `holdout_source_group_metrics` | `mixed` |
| `maximum_holdout_source_group_log_rmse` | `1` |
| `maximum_holdout_source_group_absolute_log_bias` | `1` |
| `source_group_transfer_criteria_met` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Conditional log-linear first-year atmospheric carbon-steel loss model with temperature, relative humidity, chloride and sulfur-dioxide covariates.
- Calibration and holdout source groups are predeclared and disjoint; no physical-specimen independence, long-term growth or localized loss is inferred.

## 구현 근거·독립 설명

- `atmospheric_first_year_loglinear_fit_derivation`: Transform reviewed positive first-year average atmospheric carbon-steel loss to log metres and regress it on a fixed five-column design: intercept, centered/scaled absolute temperature, centered/scaled relative humidity, log1p chloride deposition and log1p sulfur-dioxide deposition. Fit only predeclared calibration source groups by ordinary least squares and evaluate untouched holdout source groups. Preserve calibration support, conditional coefficient covariance and predeclared transfer criteria. This screening relation is not wet-CO2 corrosion, localized penetration, multi-year growth, remaining life, code acceptance or failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.atmospheric_first_year_fit"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["corrosion.atmospheric_first_year_fit"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "fit_id": "synthetic-atmospheric-fit",
  "model_id": "synthetic-atmospheric-model",
  "observations": [
    {
      "observation_id": "atm-0",
      "source_group_id": "cal-a",
      "partition": "calibration",
      "first_year_loss_m": 9.047699784654047e-06,
      "temperature_K": 280.0,
      "relative_humidity_fraction": 0.6,
      "chloride_deposition_mg_m2_day": 0.0,
      "sulfur_dioxide_deposition_mg_m2_day": 0.0,
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "observation_id": "atm-1",
      "source_group_id": "cal-b",
      "partition": "calibration",
      "first_year_loss_m": 2.0920158620956315e-05,
      "temperature_K": 285.0,
      "relative_humidity_fraction": 0.7,
      "chloride_deposition_mg_m2_day": 1.0,
      "sulfur_dioxide_deposition_mg_m2_day": 4.0,
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "observation_id": "atm-2",
      "source_group_id": "cal-a",
      "partition": "calibration",
      "first_year_loss_m": 3.757515348777019e-05,
      "temperature_K": 290.0,
      "relative_humidity_fraction": 0.8,
      "chloride_deposition_mg_m2_day": 3.0,
      "sulfur_dioxide_deposition_mg_m2_day": 1.0,
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "observation_id": "atm-3",
      "source_group_id": "cal-b",
      "partition": "calibration",
      "first_year_loss_m": 8.074222056952969e-05,
      "temperature_K": 295.0,
      "relative_humidity_fraction": 0.9,
      "chloride_deposition_mg_m2_day": 8.0,
      "sulfur_dioxide_deposition_mg_m2_day": 2.0,
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "observation_id": "atm-4",
      "source_group_id": "cal-a",
      "partition": "calibration",
      "first_year_loss_m": 3.093056955070849e-05,
      "temperature_K": 300.0,
      "relative_humidity_fraction": 0.65,
      "chloride_deposition_mg_m2_day": 2.0,
      "sulfur_dioxide_deposition_mg_m2_day": 10.0,
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "observation_id": "atm-5",
      "source_group_id": "cal-b",
      "partition": "calibration",
      "first_year_loss_m": 5.730513825590822e-05,
      "temperature_K": 305.0,
      "relative_humidity_fraction": 0.75,
      "chloride_deposition_mg_m2_day": 5.0,
      "sulfur_dioxide_deposition_mg_m2_day": 5.0,
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "observation_id": "atm-6",
      "source_group_id": "cal-a",
      "partition": "calibration",
      "first_year_loss_m": 5.7918497787956746e-05,
      "temperature_K": 282.0,
      "relative_humidity_fraction": 0.85,
      "chloride_deposition_mg_m2_day": 12.0,
      "sulfur_dioxide_deposition_mg_m2_day": 0.5,
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "observation_id": "atm-7",
      "source_group_id": "cal-b",
      "partition": "calibration",
      "first_year_loss_m": 2.8252770877835906e-05,
      "temperature_K": 298.0,
      "relative_humidity_fraction": 0.72,
      "chloride_deposition_mg_m2_day": 0.5,
      "sulfur_dioxide_deposition_mg_m2_day": 12.0,
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "observation_id": "atm-8",
      "source_group_id": "hold-a",
      "partition": "holdout",
      "first_year_loss_m": 9.287630040360677e-05,
      "temperature_K": 288.0,
      "relative_humidity_fraction": 0.88,
      "chloride_deposition_mg_m2_day": 15.0,
      "sulfur_dioxide_deposition_mg_m2_day": 8.0,
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "observation_id": "atm-9",
      "source_group_id": "hold-b",
      "partition": "holdout",
      "first_year_loss_m": 5.4138525391254464e-05,
      "temperature_K": 302.0,
      "relative_humidity_fraction": 0.68,
      "chloride_deposition_mg_m2_day": 7.0,
      "sulfur_dioxide_deposition_mg_m2_day": 15.0,
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "observation_id": "atm-10",
      "source_group_id": "hold-a",
      "partition": "holdout",
      "first_year_loss_m": 4.188447189396675e-05,
      "temperature_K": 292.0,
      "relative_humidity_fraction": 0.77,
      "chloride_deposition_mg_m2_day": 4.0,
      "sulfur_dioxide_deposition_mg_m2_day": 3.0,
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "observation_id": "atm-11",
      "source_group_id": "hold-b",
      "partition": "holdout",
      "first_year_loss_m": 7.356251655501648e-05,
      "temperature_K": 296.0,
      "relative_humidity_fraction": 0.82,
      "chloride_deposition_mg_m2_day": 9.0,
      "sulfur_dioxide_deposition_mg_m2_day": 6.0,
      "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ],
  "minimum_calibration_source_groups": 2,
  "minimum_holdout_source_groups": 2,
  "maximum_holdout_log_rmse": 0.01,
  "maximum_absolute_holdout_log_bias": 0.01,
  "maximum_holdout_outside_support_fraction": 1.0,
  "source_group_partition_reviewed": true,
  "first_year_endpoint_reviewed": true,
  "atmospheric_carbon_steel_scope_reviewed": true,
  "covariate_origin_reviewed": true,
  "aggregate_analysis_authorized": true,
  "pointwise_redistribution_authorized": false
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/atmospheric.py#L223)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

# `creep.accelerated_lognormal_rupture_fit`

**목적:** Log rupture time is linear in log(reference stress / stress) and reciprocal-temperature difference.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `fit_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `load_control_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `stress_convention` | 예 | `{"enum": ["initial_nominal_constant_load", "constant_true_stress"], "type": "string"}` | 계약·필드 설명 참조 |
| `regression_form` | 예 | `{"const": "log_time_intercept_plus_log_inverse_stress_plus_reciprocal_temperature", "type": "string"}` | 계약·필드 설명 참조 |
| `reference_stress_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa |
| `reference_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/CreepRuptureObservation"}, "minItems": 10, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_calibration_record_count` | 예 | `{"minimum": 8, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_calibration_rupture_count` | 예 | `{"minimum": 5, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_record_count` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `material_load_and_stress_convention_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_and_independence_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `stress_temperature_time_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `rupture_and_right_censor_definitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `censoring_independence_and_weights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `common_mechanism_over_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_support_hull_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `regression_form_and_minimum_counts_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreepRuptureFit.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `fit_id` | `1` |
| `physical_scope_id` | `1` |
| `reference_stress_Pa` | `Pa` |
| `reference_temperature_K` | `K` |
| `log_time_intercept_at_reference_conditions` | `ln(s)` |
| `log_inverse_stress_coefficient` | `1` |
| `reciprocal_temperature_coefficient_K` | `K` |
| `log_time_sigma` | `1` |
| `calibration_stress_range_Pa` | `Pa` |
| `calibration_temperature_range_K` | `K` |
| `outside_support_holdout_ids` | `1` |
| `holdout_rows` | `mixed` |
| `holdout_weighted_mean_negative_log_likelihood_seconds` | `1` |
| `holdout_rupture_weighted_mean_squared_standardized_residual` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Log rupture time is linear in log(reference stress / stress) and reciprocal-temperature difference.
- Weighted rupture density and right-censored survival likelihood share one constant log-time scatter.
- Calibration and holdout specimen, source and independence groups are disjoint.

## 구현 근거·독립 설명

- `authored_partitioned_accelerated_lognormal_creep_rupture_likelihood`: Fit a fixed log-time regression in log inverse stress and reciprocal absolute temperature with a lognormal scale, using rupture density and right-censor survival likelihood terms in calibration records. Preserve exact stress/load convention and partition identity; evaluate holdout only inside the calibration covariate hull without inferring mechanism transitions, variable-history life, acceptance or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "creep.accelerated_lognormal_rupture_fit"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["creep.accelerated_lognormal_rupture_fit"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "fit_id": "fit-1",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "creep-scope-1",
  "material_condition_id": "material-1",
  "load_control_id": "constant-load-1",
  "stress_convention": "initial_nominal_constant_load",
  "regression_form": "log_time_intercept_plus_log_inverse_stress_plus_reciprocal_temperature",
  "reference_stress_Pa": 150000000.0,
  "reference_temperature_K": 750.0,
  "observations": [
    {
      "observation_id": "cal-1",
      "physical_specimen_id": "specimen-cal-1",
      "source_group_id": "cal-source-a",
      "independence_group_id": "ind-cal-1",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "load_control_id": "constant-load-1",
      "stress_convention": "initial_nominal_constant_load",
      "stress_value_Pa": 100000000.0,
      "stress_unit_token": "Pa",
      "temperature_K": 700.0,
      "temperature_unit_token": "K",
      "endpoint_time_s": 8239.084414054632,
      "time_unit_token": "s",
      "endpoint_status": "rupture",
      "nominal_weight": 1.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored creep calibration"
        }
      ]
    },
    {
      "observation_id": "cal-2",
      "physical_specimen_id": "specimen-cal-2",
      "source_group_id": "cal-source-a",
      "independence_group_id": "ind-cal-2",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "load_control_id": "constant-load-1",
      "stress_convention": "initial_nominal_constant_load",
      "stress_value_Pa": 100000000.0,
      "stress_unit_token": "Pa",
      "temperature_K": 800.0,
      "temperature_unit_token": "K",
      "endpoint_time_s": 5546.5434793925515,
      "time_unit_token": "s",
      "endpoint_status": "rupture",
      "nominal_weight": 1.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored creep calibration"
        }
      ]
    },
    {
      "observation_id": "cal-3",
      "physical_specimen_id": "specimen-cal-3",
      "source_group_id": "cal-source-a",
      "independence_group_id": "ind-cal-3",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "load_control_id": "constant-load-1",
      "stress_convention": "initial_nominal_constant_load",
      "stress_value_Pa": 200000000.0,
      "stress_unit_token": "Pa",
      "temperature_K": 700.0,
      "temperature_unit_token": "K",
      "endpoint_time_s": 2143.831956907158,
      "time_unit_token": "s",
      "endpoint_status": "rupture",
      "nominal_weight": 1.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored creep calibration"
        }
      ]
    },
    {
      "observation_id": "cal-4",
      "physical_specimen_id": "specimen-cal-4",
      "source_group_id": "cal-source-a",
      "independence_group_id": "ind-cal-4",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "load_control_id": "constant-load-1",
      "stress_convention": "initial_nominal_constant_load",
      "stress_value_Pa": 200000000.0,
      "stress_unit_token": "Pa",
      "temperature_K": 800.0,
      "temperature_unit_token": "K",
      "endpoint_time_s": 1428.8652190275914,
      "time_unit_token": "s",
      "endpoint_status": "rupture",
      "nominal_weight": 1.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored creep calibration"
        }
      ]
    },
    {
      "observation_id": "cal-5",
      "physical_specimen_id": "specimen-cal-5",
      "source_group_id": "cal-source-b",
      "independence_group_id": "ind-cal-5",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "load_control_id": "constant-load-1",
      "stress_convention": "initial_nominal_constant_load",
      "stress_value_Pa": 100000000.0,
      "stress_unit_token": "Pa",
      "temperature_K": 700.0,
      "temperature_unit_token": "K",
      "endpoint_time_s": 9197.10925206866,
      "time_unit_token": "s",
      "endpoint_status": "rupture",
      "nominal_weight": 1.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored creep calibration"
        }
      ]
    },
    {
      "observation_id": "cal-6",
      "physical_specimen_id": "specimen-cal-6",
      "source_group_id": "cal-source-b",
      "independence_group_id": "ind-cal-6",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "load_control_id": "constant-load-1",
      "stress_convention": "initial_nominal_constant_load",
      "stress_value_Pa": 100000000.0,
      "stress_unit_token": "Pa",
      "temperature_K": 800.0,
      "temperature_unit_token": "K",
      "endpoint_time_s": 4968.782981746218,
      "time_unit_token": "s",
      "endpoint_status": "rupture",
      "nominal_weight": 1.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored creep calibration"
        }
      ]
    },
    {
      "observation_id": "cal-7",
      "physical_specimen_id": "specimen-cal-7",
      "source_group_id": "cal-source-b",
      "independence_group_id": "ind-cal-7",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "load_control_id": "constant-load-1",
      "stress_convention": "initial_nominal_constant_load",
      "stress_value_Pa": 200000000.0,
      "stress_unit_token": "Pa",
      "temperature_K": 700.0,
      "temperature_unit_token": "K",
      "endpoint_time_s": 2322.3854341858237,
      "time_unit_token": "s",
      "endpoint_status": "right_censored",
      "nominal_weight": 1.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored creep censor"
        }
      ]
    },
    {
      "observation_id": "cal-8",
      "physical_specimen_id": "specimen-cal-8",
      "source_group_id": "cal-source-b",
      "independence_group_id": "ind-cal-8",
      "partition": "calibration",
      "material_condition_id": "material-1",
      "load_control_id": "constant-load-1",
      "stress_convention": "initial_nominal_constant_load",
      "stress_value_Pa": 200000000.0,
      "stress_unit_token": "Pa",
      "temperature_K": 800.0,
      "temperature_unit_token": "K",
      "endpoint_time_s": 1517.2213096510372,
      "time_unit_token": "s",
      "endpoint_status": "right_censored",
      "nominal_weight": 1.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored creep censor"
        }
      ]
    },
    {
      "observation_id": "hold-1",
      "physical_specimen_id": "specimen-hold-1",
      "source_group_id": "hold-source",
      "independence_group_id": "ind-hold-1",
      "partition": "holdout",
      "material_condition_id": "material-1",
      "load_control_id": "constant-load-1",
      "stress_convention": "initial_nominal_constant_load",
      "stress_value_Pa": 130000000.0,
      "stress_unit_token": "Pa",
      "temperature_K": 730.0,
      "temperature_unit_token": "K",
      "endpoint_time_s": 4517.846532242646,
      "time_unit_token": "s",
      "endpoint_status": "rupture",
      "nominal_weight": 1.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored creep holdout"
        }
      ]
    },
    {
      "observation_id": "hold-2",
      "physical_specimen_id": "specimen-hold-2",
      "source_group_id": "hold-source",
      "independence_group_id": "ind-hold-2",
      "partition": "holdout",
      "material_condition_id": "material-1",
      "load_control_id": "constant-load-1",
      "stress_convention": "initial_nominal_constant_load",
      "stress_value_Pa": 160000000.0,
      "stress_unit_token": "Pa",
      "temperature_K": 770.0,
      "temperature_unit_token": "K",
      "endpoint_time_s": 2291.6488374824817,
      "time_unit_token": "s",
      "endpoint_status": "rupture",
      "nominal_weight": 1.0,
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored creep holdout"
        }
      ]
    }
  ],
  "minimum_calibration_record_count": 8,
  "minimum_calibration_rupture_count": 6,
  "minimum_holdout_record_count": 2,
  "material_load_and_stress_convention_reviewed": true,
  "specimen_source_and_independence_partitions_reviewed": true,
  "stress_temperature_time_units_reviewed": true,
  "rupture_and_right_censor_definitions_reviewed": true,
  "censoring_independence_and_weights_reviewed": true,
  "common_mechanism_over_support_reviewed": true,
  "calibration_support_hull_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "regression_form_and_minimum_counts_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored creep fit"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/creep_rupture_calibration.py#L103)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

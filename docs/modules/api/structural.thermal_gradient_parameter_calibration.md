# `structural.thermal_gradient_parameter_calibration`

**목적:** Caller-reviewed transient measurements align to supplied baseline and sensitivity responses.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `calibration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `experiment_or_campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `specimen_material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `specimen_material_state_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider` | 예 | `{"$ref": "#/$defs/ThermalResponseProviderIdentity"}` | 계약·필드 설명 참조 |
| `parameter` | 예 | `{"$ref": "#/$defs/ThermalCalibrationParameter"}` | 계약·필드 설명 참조 |
| `sensors` | 예 | `{"items": {"$ref": "#/$defs/ThermalSensorIdentity"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/TransientTemperatureResponse"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_time_alignment_error_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `maximum_sensor_position_alignment_error_m` | 예 | `{"minimum": 0, "type": "number"}` | m |
| `minimum_calibration_observation_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_observation_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_calibration_sequence_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_sequence_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_independence_group_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_weighted_sensitivity_information` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `specimen_material_state_and_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `geometry_boundary_and_provider_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sensor_positions_clocks_calibrations_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `parameter_definition_units_and_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `source_specimen_independence_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_provider_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_response_and_record_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `missing_invalid_and_support_gates_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ThermalGradientParameterCalibration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `calibration_id` | `1` |
| `parameter_id` | `1` |
| `parameter_kind` | `1` |
| `fitted_parameter_value` | `caller_parameter_unit` |
| `parameter_unit` | `1` |
| `weighted_sensitivity_information` | `mixed` |
| `calibration_observation_ids` | `1` |
| `holdout_observation_ids` | `1` |
| `calibration_weighted_rmse_K` | `K` |
| `holdout_weighted_bias_K` | `K` |
| `holdout_weighted_rmse_K` | `K` |
| `holdout_residuals` | `mixed` |
| `calibration_time_support_s` | `s` |
| `calibration_sensor_position_support_m` | `m` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-reviewed transient measurements align to supplied baseline and sensitivity responses.
- Calibration and holdout physical specimens, source groups and independence groups are disjoint.
- The fitted value and all scored holdout rows remain inside declared support.

## 구현 근거·독립 설명

- `authored_weighted_transient_temperature_sensitivity_calibration`: Fit one caller-declared thermal-property multiplier or diffusivity from provenance-bound transient measured temperatures, external-provider baseline predictions and parameter sensitivities using weighted linear calibration. Preserve geometry, boundary, solver, sensor, clock, uncertainty, specimen/source partitions and support; report holdout residuals only inside support without implementing another PDE solver, inferring phase mechanisms, thermal stress, acceptance, life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "structural.thermal_gradient_parameter_calibration"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["structural.thermal_gradient_parameter_calibration"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "calibration_id": "thermal-fit-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "component_id": "component-1",
  "experiment_or_campaign_id": "campaign-1",
  "specimen_material_id": "material-1",
  "specimen_material_state_id": "state-1",
  "physical_scope_definition": "reviewed one-dimensional specimen response scope",
  "time_basis": "experiment elapsed seconds",
  "provider": {
    "response_basis": "external_provider_sensitivity",
    "provider_id": "provider-1",
    "solver_or_response_id": "response-1",
    "provider_revision": "rev-1",
    "geometry_id": "geometry-1",
    "geometry_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "boundary_condition_id": "boundary-1",
    "boundary_condition_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "provider_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "provider_state_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "analytical_response_definition": null,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored thermal test",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "parameter": {
    "parameter_id": "conductivity-multiplier",
    "parameter_kind": "thermal_property_multiplier",
    "parameter_definition": "caller-defined multiplier applied by the response provider",
    "unit_token": "1",
    "reference_value": 1.0,
    "minimum_supported_value": 0.5,
    "maximum_supported_value": 1.5,
    "support_basis": "reviewed provider sensitivity support",
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored thermal test",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "sensors": [
    {
      "sensor_id": "sensor-1",
      "position_m": 0.0,
      "expanded_position_uncertainty_m": 0.001,
      "clock_id": "clock-1",
      "sensor_calibration_id": "sensor-cal-1",
      "sensor_calibration_provider_id": "cal-provider",
      "sensor_calibration_provider_revision": "cal-rev-1",
      "sensor_calibration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "calibration_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored thermal test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "sensor_id": "sensor-2",
      "position_m": 1.0,
      "expanded_position_uncertainty_m": 0.001,
      "clock_id": "clock-1",
      "sensor_calibration_id": "sensor-cal-2",
      "sensor_calibration_provider_id": "cal-provider",
      "sensor_calibration_provider_revision": "cal-rev-1",
      "sensor_calibration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "calibration_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored thermal test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "cal-1",
      "partition": "calibration",
      "sequence_id": "seq-cal",
      "physical_specimen_id": "spec-cal",
      "source_group_id": "source-cal",
      "independence_group_id": "ind-cal",
      "sensor_id": "sensor-1",
      "observation_clock_id": "clock-1",
      "observed_elapsed_time_s": 0.0,
      "provider_elapsed_time_s": 0.0,
      "provider_sensor_position_m": 0.0,
      "observed_temperature_K": 302.0,
      "expanded_observed_temperature_uncertainty_K": 0.5,
      "baseline_predicted_temperature_K": 300.0,
      "expanded_baseline_prediction_uncertainty_K": 0.4,
      "predicted_temperature_sensitivity_K_per_parameter_unit": 10.0,
      "sample_weight": 1.0,
      "sequence_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_response_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "observation_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "record_available": true,
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored thermal test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "cal-2",
      "partition": "calibration",
      "sequence_id": "seq-cal",
      "physical_specimen_id": "spec-cal",
      "source_group_id": "source-cal",
      "independence_group_id": "ind-cal",
      "sensor_id": "sensor-2",
      "observation_clock_id": "clock-1",
      "observed_elapsed_time_s": 10.0,
      "provider_elapsed_time_s": 10.0,
      "provider_sensor_position_m": 1.0,
      "observed_temperature_K": 314.0,
      "expanded_observed_temperature_uncertainty_K": 0.5,
      "baseline_predicted_temperature_K": 310.0,
      "expanded_baseline_prediction_uncertainty_K": 0.4,
      "predicted_temperature_sensitivity_K_per_parameter_unit": 20.0,
      "sample_weight": 1.0,
      "sequence_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_response_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "observation_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "record_available": true,
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored thermal test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "hold-1",
      "partition": "holdout",
      "sequence_id": "seq-hold",
      "physical_specimen_id": "spec-hold",
      "source_group_id": "source-hold",
      "independence_group_id": "ind-hold",
      "sensor_id": "sensor-1",
      "observation_clock_id": "clock-1",
      "observed_elapsed_time_s": 5.0,
      "provider_elapsed_time_s": 5.0,
      "provider_sensor_position_m": 0.0,
      "observed_temperature_K": 308.5,
      "expanded_observed_temperature_uncertainty_K": 0.5,
      "baseline_predicted_temperature_K": 305.0,
      "expanded_baseline_prediction_uncertainty_K": 0.4,
      "predicted_temperature_sensitivity_K_per_parameter_unit": 15.0,
      "sample_weight": 1.0,
      "sequence_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "provider_response_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "observation_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "record_available": true,
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored thermal test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "maximum_time_alignment_error_s": 0.1,
  "maximum_sensor_position_alignment_error_m": 0.001,
  "minimum_calibration_observation_count": 2,
  "minimum_holdout_observation_count": 1,
  "minimum_calibration_sequence_count": 1,
  "minimum_holdout_sequence_count": 1,
  "minimum_holdout_independence_group_count": 1,
  "minimum_weighted_sensitivity_information": 1.0,
  "specimen_material_state_and_scope_reviewed": true,
  "geometry_boundary_and_provider_identity_reviewed": true,
  "sensor_positions_clocks_calibrations_and_uncertainty_reviewed": true,
  "parameter_definition_units_and_support_reviewed": true,
  "source_specimen_independence_partitions_reviewed": true,
  "observation_provider_alignment_reviewed": true,
  "provider_response_and_record_digests_reviewed": true,
  "missing_invalid_and_support_gates_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored thermal test",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/thermal_gradient_calibration.py#L189)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

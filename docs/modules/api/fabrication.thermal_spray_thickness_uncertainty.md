# `fabrication.thermal_spray_thickness_uncertainty`

**목적:** Repeated SI thickness measurements receive caller-provided additive calibration corrections.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `coating_system_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `layer_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `substrate_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `spray_batch_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `process_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibrations` | 예 | `{"items": {"$ref": "#/$defs/ThicknessInstrumentCalibration"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `locations` | 예 | `{"items": {"$ref": "#/$defs/ThermalSprayThicknessLocation"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_repeats_per_location` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `expanded_uncertainty_coverage_factor` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `specimen_location_layer_and_process_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `instrument_calibration_support_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `repeated_measurement_method_units_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `spatial_groups_and_coordinate_frame_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_independence_and_spatial_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `holdout_reference_identity_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_independence_and_coverage_factor_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `missing_invalid_and_support_policy_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ThermalSprayThicknessUncertainty.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `physical_scope_id` | `1` |
| `coating_system_id` | `1` |
| `expanded_uncertainty_coverage_factor` | `1` |
| `location_rows` | `mixed` |
| `partition_summaries` | `mixed` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Repeated SI thickness measurements receive caller-provided additive calibration corrections.
- Calibration, measurement and repeatability uncertainty components are combined under reviewed independence.
- Calibration and holdout specimen, source, independence and spatial groups are disjoint.

## 구현 근거·독립 설명

- `authored_partitioned_thermal_spray_thickness_uncertainty`: Apply caller-supplied additive instrument bias corrections to repeated SI coating-thickness measurements and combine reviewed repeatability, measurement and calibration standard-uncertainty components. Preserve physical specimen, source, independence and spatial partitions plus holdout reference lineage; do not perform segmentation or infer bond strength, acceptance, service life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.thermal_spray_thickness_uncertainty"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.thermal_spray_thickness_uncertainty"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "coating-location-1",
  "physical_scope_id": "coating-scope-1",
  "coating_system_id": "coating-system-1",
  "layer_id": "layer-1",
  "substrate_condition_id": "substrate-1",
  "spray_batch_id": "batch-1",
  "process_condition_id": "process-1",
  "calibrations": [
    {
      "calibration_id": "calibration-1",
      "instrument_id": "instrument-1",
      "instrument_configuration_id": "configuration-1",
      "additive_bias_correction_m": -1e-06,
      "calibration_standard_uncertainty_m": 5e-07,
      "minimum_supported_thickness_m": 5e-05,
      "maximum_supported_thickness_m": 0.0002,
      "provider_id": "calibration-provider",
      "provider_revision": "1",
      "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored thickness example"
        }
      ]
    }
  ],
  "locations": [
    {
      "location_record_id": "cal-1",
      "physical_specimen_id": "spec-cal-1",
      "source_group_id": "source-cal-a",
      "independence_group_id": "ind-cal-1",
      "spatial_group_id": "spatial-cal-a",
      "partition": "calibration",
      "physical_location_id": "physical-cal-1",
      "coordinate_frame_id": "frame-1",
      "x_coordinate_m": 0.01,
      "y_coordinate_m": 0.02,
      "layer_id": "layer-1",
      "substrate_condition_id": "substrate-1",
      "spray_batch_id": "batch-1",
      "process_condition_id": "process-1",
      "measurements": [
        {
          "measurement_id": "cal-m1",
          "calibration_id": "calibration-1",
          "measured_thickness_m": 0.0001,
          "thickness_unit_token": "m",
          "measurement_standard_uncertainty_m": 1e-06,
          "method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored thickness example"
            }
          ]
        },
        {
          "measurement_id": "cal-m2",
          "calibration_id": "calibration-1",
          "measured_thickness_m": 0.000102,
          "thickness_unit_token": "m",
          "measurement_standard_uncertainty_m": 1e-06,
          "method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored thickness example"
            }
          ]
        }
      ],
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored thickness example"
        }
      ]
    },
    {
      "location_record_id": "cal-2",
      "physical_specimen_id": "spec-cal-2",
      "source_group_id": "source-cal-b",
      "independence_group_id": "ind-cal-2",
      "spatial_group_id": "spatial-cal-b",
      "partition": "calibration",
      "physical_location_id": "physical-cal-2",
      "coordinate_frame_id": "frame-1",
      "x_coordinate_m": 0.02,
      "y_coordinate_m": 0.02,
      "layer_id": "layer-1",
      "substrate_condition_id": "substrate-1",
      "spray_batch_id": "batch-1",
      "process_condition_id": "process-1",
      "measurements": [
        {
          "measurement_id": "cal2-m1",
          "calibration_id": "calibration-1",
          "measured_thickness_m": 0.000105,
          "thickness_unit_token": "m",
          "measurement_standard_uncertainty_m": 1e-06,
          "method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored thickness example"
            }
          ]
        },
        {
          "measurement_id": "cal2-m2",
          "calibration_id": "calibration-1",
          "measured_thickness_m": 0.000107,
          "thickness_unit_token": "m",
          "measurement_standard_uncertainty_m": 1e-06,
          "method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored thickness example"
            }
          ]
        }
      ],
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored thickness example"
        }
      ]
    },
    {
      "location_record_id": "hold-1",
      "physical_specimen_id": "spec-hold-1",
      "source_group_id": "source-hold",
      "independence_group_id": "ind-hold-1",
      "spatial_group_id": "spatial-hold",
      "partition": "holdout",
      "physical_location_id": "physical-hold-1",
      "coordinate_frame_id": "frame-1",
      "x_coordinate_m": 0.01,
      "y_coordinate_m": 0.02,
      "layer_id": "layer-1",
      "substrate_condition_id": "substrate-1",
      "spray_batch_id": "batch-1",
      "process_condition_id": "process-1",
      "measurements": [
        {
          "measurement_id": "hold-m1",
          "calibration_id": "calibration-1",
          "measured_thickness_m": 0.000103,
          "thickness_unit_token": "m",
          "measurement_standard_uncertainty_m": 1e-06,
          "method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored thickness example"
            }
          ]
        },
        {
          "measurement_id": "hold-m2",
          "calibration_id": "calibration-1",
          "measured_thickness_m": 0.000105,
          "thickness_unit_token": "m",
          "measurement_standard_uncertainty_m": 1e-06,
          "method_id": "method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored thickness example"
            }
          ]
        }
      ],
      "reference_thickness_m": 0.000102,
      "reference_standard_uncertainty_m": 1.5e-06,
      "reference_provider_id": "reference-provider",
      "reference_result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored thickness example"
        }
      ]
    }
  ],
  "minimum_repeats_per_location": 2,
  "expanded_uncertainty_coverage_factor": 2.0,
  "specimen_location_layer_and_process_identity_reviewed": true,
  "instrument_calibration_support_and_uncertainty_reviewed": true,
  "repeated_measurement_method_units_and_digests_reviewed": true,
  "spatial_groups_and_coordinate_frame_reviewed": true,
  "specimen_source_independence_and_spatial_partitions_reviewed": true,
  "holdout_reference_identity_and_uncertainty_reviewed": true,
  "uncertainty_independence_and_coverage_factor_reviewed": true,
  "missing_invalid_and_support_policy_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored thickness example"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/thermal_spray_thickness_uncertainty.py#L154)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

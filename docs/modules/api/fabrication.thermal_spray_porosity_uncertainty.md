# `fabrication.thermal_spray_porosity_uncertainty`

**목적:** Caller-segmented pixel areas are converted with reviewed pixel-area calibration evidence.

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
| `calibrations` | 예 | `{"items": {"$ref": "#/$defs/PorosityPixelAreaCalibration"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `fields` | 예 | `{"items": {"$ref": "#/$defs/ThermalSprayPorosityField"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_replicates_per_group` | 예 | `{"minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `expanded_uncertainty_coverage_factor` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `specimen_field_layer_and_process_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pixel_area_calibration_units_uncertainty_and_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_segmentation_area_uncertainty_edge_status_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `replicate_and_spatial_group_independence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_independence_spatial_and_partition_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `holdout_reference_lineage_digest_uncertainty_and_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_propagation_and_coverage_factor_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `missing_invalid_and_out_of_support_policy_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ThermalSprayPorosityUncertainty.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `physical_scope_id` | `1` |
| `coating_system_id` | `1` |
| `field_rows` | `mixed` |
| `replicate_group_rows` | `mixed` |
| `holdout_diagnostics` | `mixed` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-segmented pixel areas are converted with reviewed pixel-area calibration evidence.
- Replicate, specimen, source, independence and spatial groups remain partition-disjoint.
- Independent holdout references retain lineage, digests, uncertainty and field-area support.

## 구현 근거·독립 설명

- `authored_partitioned_thermal_spray_porosity_uncertainty`: Convert caller-segmented pore pixels with reviewed area calibration, summarize field and replicate porosity, and combine segmentation-area and repeatability uncertainty while preserving physical specimen, source, independence, spatial and replicate partitions plus holdout reference lineage. Do not perform segmentation, classify pores or infer bond strength, acceptance, service life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.thermal_spray_porosity_uncertainty"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.thermal_spray_porosity_uncertainty"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "porosity-assessment-1",
  "asset_id": "asset-1",
  "location_id": "coating-location-1",
  "physical_scope_id": "scope-1",
  "coating_system_id": "coating-1",
  "layer_id": "topcoat",
  "substrate_condition_id": "prepared-steel",
  "spray_batch_id": "batch-1",
  "process_condition_id": "process-1",
  "calibrations": [
    {
      "calibration_id": "pixel-cal-1",
      "coordinate_frame_id": "frame-1",
      "pixel_area_scale_m2_per_px2": 1e-12,
      "pixel_area_scale_standard_uncertainty_m2_per_px2": 1e-14,
      "minimum_supported_field_area_px2": 5000.0,
      "maximum_supported_field_area_px2": 20000.0,
      "maximum_supported_single_pore_area_px2": 500.0,
      "provider_id": "calibration-lab",
      "provider_revision": "1",
      "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "pixel-calibration",
          "origin": "measured",
          "citation": "caller evidence pixel-calibration",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "fields": [
    {
      "field_id": "cal-field-1",
      "replicate_group_id": "cal-group",
      "physical_specimen_id": "specimen-calibration-1",
      "source_group_id": "source-calibration-1",
      "independence_group_id": "independent-calibration-1",
      "spatial_group_id": "spatial-calibration-1",
      "partition": "calibration",
      "physical_location_id": "location-calibration-1",
      "coordinate_frame_id": "frame-1",
      "width_px": 100,
      "height_px": 100,
      "pixel_area_calibration_id": "pixel-cal-1",
      "layer_id": "topcoat",
      "substrate_condition_id": "prepared-steel",
      "spray_batch_id": "batch-1",
      "process_condition_id": "process-1",
      "pores": [
        {
          "pore_id": "pore-cal-field-1",
          "segmented_area_px2": 100.0,
          "segmented_area_standard_uncertainty_px2": 2.0,
          "area_unit_token": "px^2",
          "touches_field_edge": false,
          "segmentation_method_id": "caller-segment-v1",
          "provider_id": "caller-segmentation",
          "provider_revision": "1",
          "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "pore-pore-cal-field-1",
              "origin": "measured",
              "citation": "caller evidence pore-pore-cal-field-1",
              "license_id": null,
              "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            }
          ]
        }
      ],
      "reference": null,
      "field_provider_id": "microscopy-lab",
      "field_provider_revision": "3",
      "field_data_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "field-cal-field-1",
          "origin": "measured",
          "citation": "caller evidence field-cal-field-1",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    },
    {
      "field_id": "cal-field-2",
      "replicate_group_id": "cal-group",
      "physical_specimen_id": "specimen-calibration-2",
      "source_group_id": "source-calibration-2",
      "independence_group_id": "independent-calibration-2",
      "spatial_group_id": "spatial-calibration-2",
      "partition": "calibration",
      "physical_location_id": "location-calibration-2",
      "coordinate_frame_id": "frame-1",
      "width_px": 100,
      "height_px": 100,
      "pixel_area_calibration_id": "pixel-cal-1",
      "layer_id": "topcoat",
      "substrate_condition_id": "prepared-steel",
      "spray_batch_id": "batch-1",
      "process_condition_id": "process-1",
      "pores": [
        {
          "pore_id": "pore-cal-field-2",
          "segmented_area_px2": 110.0,
          "segmented_area_standard_uncertainty_px2": 2.0,
          "area_unit_token": "px^2",
          "touches_field_edge": false,
          "segmentation_method_id": "caller-segment-v1",
          "provider_id": "caller-segmentation",
          "provider_revision": "1",
          "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "pore-pore-cal-field-2",
              "origin": "measured",
              "citation": "caller evidence pore-pore-cal-field-2",
              "license_id": null,
              "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            }
          ]
        }
      ],
      "reference": null,
      "field_provider_id": "microscopy-lab",
      "field_provider_revision": "3",
      "field_data_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "field-cal-field-2",
          "origin": "measured",
          "citation": "caller evidence field-cal-field-2",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    },
    {
      "field_id": "hold-field-1",
      "replicate_group_id": "hold-group",
      "physical_specimen_id": "specimen-holdout-1",
      "source_group_id": "source-holdout-1",
      "independence_group_id": "independent-holdout-1",
      "spatial_group_id": "spatial-holdout-1",
      "partition": "holdout",
      "physical_location_id": "location-holdout-1",
      "coordinate_frame_id": "frame-1",
      "width_px": 100,
      "height_px": 100,
      "pixel_area_calibration_id": "pixel-cal-1",
      "layer_id": "topcoat",
      "substrate_condition_id": "prepared-steel",
      "spray_batch_id": "batch-1",
      "process_condition_id": "process-1",
      "pores": [
        {
          "pore_id": "pore-hold-field-1",
          "segmented_area_px2": 120.0,
          "segmented_area_standard_uncertainty_px2": 2.0,
          "area_unit_token": "px^2",
          "touches_field_edge": false,
          "segmentation_method_id": "caller-segment-v1",
          "provider_id": "caller-segmentation",
          "provider_revision": "1",
          "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "pore-pore-hold-field-1",
              "origin": "measured",
              "citation": "caller evidence pore-pore-hold-field-1",
              "license_id": null,
              "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            }
          ]
        }
      ],
      "reference": {
        "reference_id": "ref-hold-field-1",
        "porosity_area_fraction": 0.011,
        "porosity_standard_uncertainty_fraction": 0.0005,
        "minimum_supported_field_area_m2": 5e-09,
        "maximum_supported_field_area_m2": 2e-08,
        "method_id": "independent-reference-v1",
        "provider_id": "reference-lab",
        "provider_revision": "2",
        "source_lineage_id": "reference-series-2026",
        "source_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "record_valid": true,
        "invalid_basis": null,
        "evidence": [
          {
            "source_id": "reference-ref-hold-field-1",
            "origin": "measured",
            "citation": "caller evidence reference-ref-hold-field-1",
            "license_id": null,
            "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
          }
        ]
      },
      "field_provider_id": "microscopy-lab",
      "field_provider_revision": "3",
      "field_data_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "field-hold-field-1",
          "origin": "measured",
          "citation": "caller evidence field-hold-field-1",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    },
    {
      "field_id": "hold-field-2",
      "replicate_group_id": "hold-group",
      "physical_specimen_id": "specimen-holdout-2",
      "source_group_id": "source-holdout-2",
      "independence_group_id": "independent-holdout-2",
      "spatial_group_id": "spatial-holdout-2",
      "partition": "holdout",
      "physical_location_id": "location-holdout-2",
      "coordinate_frame_id": "frame-1",
      "width_px": 100,
      "height_px": 100,
      "pixel_area_calibration_id": "pixel-cal-1",
      "layer_id": "topcoat",
      "substrate_condition_id": "prepared-steel",
      "spray_batch_id": "batch-1",
      "process_condition_id": "process-1",
      "pores": [
        {
          "pore_id": "pore-hold-field-2",
          "segmented_area_px2": 130.0,
          "segmented_area_standard_uncertainty_px2": 2.0,
          "area_unit_token": "px^2",
          "touches_field_edge": false,
          "segmentation_method_id": "caller-segment-v1",
          "provider_id": "caller-segmentation",
          "provider_revision": "1",
          "input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "pore-pore-hold-field-2",
              "origin": "measured",
              "citation": "caller evidence pore-pore-hold-field-2",
              "license_id": null,
              "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            }
          ]
        }
      ],
      "reference": {
        "reference_id": "ref-hold-field-2",
        "porosity_area_fraction": 0.012,
        "porosity_standard_uncertainty_fraction": 0.0005,
        "minimum_supported_field_area_m2": 5e-09,
        "maximum_supported_field_area_m2": 2e-08,
        "method_id": "independent-reference-v1",
        "provider_id": "reference-lab",
        "provider_revision": "2",
        "source_lineage_id": "reference-series-2026",
        "source_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "record_valid": true,
        "invalid_basis": null,
        "evidence": [
          {
            "source_id": "reference-ref-hold-field-2",
            "origin": "measured",
            "citation": "caller evidence reference-ref-hold-field-2",
            "license_id": null,
            "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
          }
        ]
      },
      "field_provider_id": "microscopy-lab",
      "field_provider_revision": "3",
      "field_data_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "field-hold-field-2",
          "origin": "measured",
          "citation": "caller evidence field-hold-field-2",
          "license_id": null,
          "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        }
      ]
    }
  ],
  "minimum_replicates_per_group": 2,
  "expanded_uncertainty_coverage_factor": 2.0,
  "specimen_field_layer_and_process_identity_reviewed": true,
  "pixel_area_calibration_units_uncertainty_and_support_reviewed": true,
  "caller_segmentation_area_uncertainty_edge_status_and_digests_reviewed": true,
  "replicate_and_spatial_group_independence_reviewed": true,
  "specimen_source_independence_spatial_and_partition_groups_reviewed": true,
  "holdout_reference_lineage_digest_uncertainty_and_support_reviewed": true,
  "uncertainty_propagation_and_coverage_factor_reviewed": true,
  "missing_invalid_and_out_of_support_policy_reviewed": true,
  "evidence": [
    {
      "source_id": "assessment",
      "origin": "measured",
      "citation": "caller evidence assessment",
      "license_id": null,
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/thermal_spray_porosity_uncertainty.py#L175)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

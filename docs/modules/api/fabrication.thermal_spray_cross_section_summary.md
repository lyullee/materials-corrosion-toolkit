# `fabrication.thermal_spray_cross_section_summary`

**목적:** Caller-supplied thickness points and segmented pore areas share one calibrated field geometry.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `summary_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `coating_system_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `layer_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `substrate_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `spray_batch_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `process_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `frame_calibrations` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/CrossSectionFrameCalibration"}, "type": "array"}` | 계약·필드 설명 참조 |
| `fields` | 예 | `{"items": {"$ref": "#/$defs/ThermalSprayCrossSectionField"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `field_area_relative_tolerance` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `specimen_location_layer_and_substrate_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `spray_batch_and_process_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `frame_calibration_and_field_area_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `thickness_traverses_units_uncertainty_and_bounds_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_segmentation_pore_area_edge_and_overlap_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_and_independence_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `method_provider_revision_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `missing_invalid_and_support_policy_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ThermalSprayCrossSectionSummary.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `summary_id` | `1` |
| `physical_scope_id` | `1` |
| `coating_system_id` | `1` |
| `field_rows` | `mixed` |
| `partition_summaries` | `mixed` |
| `outside_calibration_field_area_support_holdout_ids` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-supplied thickness points and segmented pore areas share one calibrated field geometry.
- Calibration and holdout specimen, source and independence groups are disjoint.
- Duplicate, overlap, bounds, edge and missing/invalid states remain explicit.

## 구현 근거·독립 설명

- `authored_partitioned_thermal_spray_cross_section_geometry_summary`: Preserve calibrated cross-section fields, layer, substrate, spray batch and process identity, thickness traverses, caller-segmented pore geometry, uncertainty, edge and overlap handling, provider revision, immutable digests and disjoint calibration/holdout groups. Summarize thickness and area porosity only, without image segmentation, pore classification, bond-strength inference, embedded limits, acceptance, service life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.thermal_spray_cross_section_summary"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.thermal_spray_cross_section_summary"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "summary_id": "summary-1",
  "asset_id": "asset-1",
  "location_id": "cross-section-scope-1",
  "physical_scope_id": "physical-scope-1",
  "coating_system_id": "coating-system-1",
  "layer_id": "layer-1",
  "substrate_condition_id": "substrate-1",
  "spray_batch_id": "batch-1",
  "process_condition_id": "process-1",
  "frame_calibrations": [
    {
      "calibration_id": "frame-cal-1",
      "coordinate_frame_id": "frame-1",
      "x_scale_m_per_px": 1e-06,
      "y_scale_m_per_px": 1e-06,
      "x_scale_expanded_uncertainty_m_per_px": 1e-08,
      "y_scale_expanded_uncertainty_m_per_px": 1e-08,
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
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "fields": [
    {
      "field_id": "cal-1",
      "physical_specimen_id": "spec-cal-1",
      "source_group_id": "source-cal-a",
      "independence_group_id": "ind-spec-cal-1",
      "partition": "calibration",
      "physical_location_id": "location-cal-1",
      "layer_id": "layer-1",
      "substrate_condition_id": "substrate-1",
      "spray_batch_id": "batch-1",
      "process_condition_id": "process-1",
      "field_basis": "calibrated_image",
      "coordinate_frame_id": "frame-1",
      "frame_calibration_id": "frame-cal-1",
      "width_px": 100,
      "height_px": 100,
      "width_m": null,
      "height_m": null,
      "declared_field_area_m2": 1e-08,
      "thickness_traverses": [
        {
          "traverse_id": "traverse-cal-1",
          "points": [
            {
              "point_id": "cal-1-point-0",
              "x_coordinate": 10.0,
              "y_coordinate": 50.0,
              "coordinate_unit_token": "px",
              "thickness_m": 0.0001,
              "expanded_uncertainty_m": 2e-06
            },
            {
              "point_id": "cal-1-point-1",
              "x_coordinate": 30.0,
              "y_coordinate": 50.0,
              "coordinate_unit_token": "px",
              "thickness_m": 0.00011,
              "expanded_uncertainty_m": 2e-06
            },
            {
              "point_id": "cal-1-point-2",
              "x_coordinate": 50.0,
              "y_coordinate": 50.0,
              "coordinate_unit_token": "px",
              "thickness_m": 0.000105,
              "expanded_uncertainty_m": 2e-06
            }
          ],
          "method_id": "thickness-method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored test",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "pores": [
        {
          "pore_id": "pore-cal-1",
          "area_value": 100.0,
          "area_unit_token": "px^2",
          "coordinate_unit_token": "px",
          "minimum_x": 20.0,
          "maximum_x": 30.0,
          "minimum_y": 20.0,
          "maximum_y": 30.0,
          "touches_field_edge": false,
          "overlaps_pore_ids": [],
          "segmentation_method_id": "caller-segmentation-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored test",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "field_method_id": "cross-section-method-1",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "field_id": "cal-2",
      "physical_specimen_id": "spec-cal-2",
      "source_group_id": "source-cal-b",
      "independence_group_id": "ind-spec-cal-2",
      "partition": "calibration",
      "physical_location_id": "location-cal-2",
      "layer_id": "layer-1",
      "substrate_condition_id": "substrate-1",
      "spray_batch_id": "batch-1",
      "process_condition_id": "process-1",
      "field_basis": "calibrated_image",
      "coordinate_frame_id": "frame-1",
      "frame_calibration_id": "frame-cal-1",
      "width_px": 100,
      "height_px": 100,
      "width_m": null,
      "height_m": null,
      "declared_field_area_m2": 1e-08,
      "thickness_traverses": [
        {
          "traverse_id": "traverse-cal-2",
          "points": [
            {
              "point_id": "cal-2-point-0",
              "x_coordinate": 10.0,
              "y_coordinate": 50.0,
              "coordinate_unit_token": "px",
              "thickness_m": 0.000102,
              "expanded_uncertainty_m": 2e-06
            },
            {
              "point_id": "cal-2-point-1",
              "x_coordinate": 30.0,
              "y_coordinate": 50.0,
              "coordinate_unit_token": "px",
              "thickness_m": 0.000108,
              "expanded_uncertainty_m": 2e-06
            },
            {
              "point_id": "cal-2-point-2",
              "x_coordinate": 50.0,
              "y_coordinate": 50.0,
              "coordinate_unit_token": "px",
              "thickness_m": 0.000106,
              "expanded_uncertainty_m": 2e-06
            }
          ],
          "method_id": "thickness-method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored test",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "pores": [
        {
          "pore_id": "pore-cal-2",
          "area_value": 120.0,
          "area_unit_token": "px^2",
          "coordinate_unit_token": "px",
          "minimum_x": 20.0,
          "maximum_x": 30.0,
          "minimum_y": 20.0,
          "maximum_y": 30.0,
          "touches_field_edge": true,
          "overlaps_pore_ids": [],
          "segmentation_method_id": "caller-segmentation-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored test",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "field_method_id": "cross-section-method-1",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "field_id": "hold-1",
      "physical_specimen_id": "spec-hold-1",
      "source_group_id": "source-hold",
      "independence_group_id": "ind-spec-hold-1",
      "partition": "holdout",
      "physical_location_id": "location-hold-1",
      "layer_id": "layer-1",
      "substrate_condition_id": "substrate-1",
      "spray_batch_id": "batch-1",
      "process_condition_id": "process-1",
      "field_basis": "calibrated_image",
      "coordinate_frame_id": "frame-1",
      "frame_calibration_id": "frame-cal-1",
      "width_px": 100,
      "height_px": 100,
      "width_m": null,
      "height_m": null,
      "declared_field_area_m2": 1e-08,
      "thickness_traverses": [
        {
          "traverse_id": "traverse-hold-1",
          "points": [
            {
              "point_id": "hold-1-point-0",
              "x_coordinate": 10.0,
              "y_coordinate": 50.0,
              "coordinate_unit_token": "px",
              "thickness_m": 0.000101,
              "expanded_uncertainty_m": 2e-06
            },
            {
              "point_id": "hold-1-point-1",
              "x_coordinate": 30.0,
              "y_coordinate": 50.0,
              "coordinate_unit_token": "px",
              "thickness_m": 0.000109,
              "expanded_uncertainty_m": 2e-06
            },
            {
              "point_id": "hold-1-point-2",
              "x_coordinate": 50.0,
              "y_coordinate": 50.0,
              "coordinate_unit_token": "px",
              "thickness_m": 0.000104,
              "expanded_uncertainty_m": 2e-06
            }
          ],
          "method_id": "thickness-method-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored test",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "pores": [
        {
          "pore_id": "pore-hold-1",
          "area_value": 110.0,
          "area_unit_token": "px^2",
          "coordinate_unit_token": "px",
          "minimum_x": 20.0,
          "maximum_x": 30.0,
          "minimum_y": 20.0,
          "maximum_y": 30.0,
          "touches_field_edge": false,
          "overlaps_pore_ids": [],
          "segmentation_method_id": "caller-segmentation-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "record_valid": true,
          "invalid_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored test",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "field_method_id": "cross-section-method-1",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "field_area_relative_tolerance": 1e-09,
  "specimen_location_layer_and_substrate_reviewed": true,
  "spray_batch_and_process_condition_reviewed": true,
  "frame_calibration_and_field_area_reviewed": true,
  "thickness_traverses_units_uncertainty_and_bounds_reviewed": true,
  "caller_segmentation_pore_area_edge_and_overlap_reviewed": true,
  "specimen_source_and_independence_partitions_reviewed": true,
  "method_provider_revision_and_digests_reviewed": true,
  "missing_invalid_and_support_policy_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored test",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/thermal_spray_cross_section.py#L216)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

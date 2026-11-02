# `corrosion.planar_slit_aperture_history`

**목적:** Sequential geometry remapping from a caller-pinned cell-average signed wall-recession history within declared aperture support; support failure preserves an out-of-scope prefix and failed interval, and subsequent transport is a separate calculation.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `wall_loss_source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `cell_widths_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 2000, "minItems": 2, "type": "array"}` | m |
| `initial_cell_aperture_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 2000, "minItems": 2, "type": "array"}` | m |
| `transverse_width_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `reference_cross_section_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `reactive_broad_face_count` | 예 | `{"enum": [1, 2], "type": "integer"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 아니오 | `{"anyOf": [{"items": {"minimum": 0, "type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}, {"type": "null"}], "default": null}` | s |
| `cumulative_signed_cell_average_recession_m` | 아니오 | `{"anyOf": [{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 5000, "minItems": 2, "type": "array"}, {"type": "null"}], "default": null}` | m |
| `wall_loss_result` | 아니오 | `{"anyOf": [{"additionalProperties": true, "type": "object"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `supported_minimum_aperture_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `supported_maximum_aperture_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `wall_recession_is_per_combined_reactive_area_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `opposing_face_recession_is_equal_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `cell_center_to_face_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `geometry_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PlanarSlitApertureHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `cell_aperture_m` | `m` |
| `geometry_states[].elapsed_time_s` | `s` |
| `geometry_states[].cell_aperture_m` | `m` |
| `geometry_states[].axial_cross_section_m2` | `m2` |
| `geometry_states[].cell_volume_m3` | `m3` |
| `computed_prefix_geometry_states[].elapsed_time_s` | `s` |
| `computed_prefix_geometry_states[].cell_aperture_m` | `m` |
| `computed_prefix_geometry_states[].axial_cross_section_m2` | `m2` |
| `computed_prefix_geometry_states[].cell_volume_m3` | `m3` |
| `failed_elapsed_time_s` | `s` |
| `axial_cross_section_m2` | `m2` |
| `cell_volume_m3` | `m3` |
| `wall_area_per_volume_m2_m3` | `1/m` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Sequential geometry remapping from a caller-pinned cell-average signed wall-recession history within declared aperture support; support failure preserves an out-of-scope prefix and failed interval, and subsequent transport is a separate calculation.

## 구현 근거·독립 설명

- `planar_slit_aperture_evolution`: Map either a caller-pinned cumulative signed cell-average wall recession or a digest-pinned cellwise wall-metal-loss result to sequential planar-slit apertures, cross sections, volumes and RestrictedTransportRequest-compatible geometry fields within a declared provider aperture range. Preserve cell order and clock; reconcile the source reactive wall areas against the declared face count, transverse width, reference area and cell widths. Positive recession denotes metal loss and increases aperture; negative recession denotes net deposition and reduces aperture. Two opposing reactive faces and piecewise-linear center-to-face area interpolation with constant boundary extrapolation require review. Support failures preserve the accepted geometry prefix and first failed interval with status out_of_scope. This is a geometry remap for a subsequent fixed-geometry solve; no within-step flow, chemistry, deposit mechanics or constitutive coupling is inferred.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.planar_slit_aperture_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["corrosion.planar_slit_aperture_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "geometry_id": "authored-evolving-slit",
  "geometry_source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "wall_loss_source_sha256": "aaaef3027cd629dc5d0eba44c3bbcc5dc5cc8143b9b114bb35880bedab9bfae0",
  "cell_widths_m": [
    1e-05,
    3e-05,
    6e-05
  ],
  "initial_cell_aperture_m": [
    1e-05,
    1e-05,
    1e-05
  ],
  "transverse_width_m": 0.01,
  "reference_cross_section_m2": 0.0001,
  "reactive_broad_face_count": 2,
  "wall_loss_result": {
    "status": "computed",
    "values": {
      "selection_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "wall_metal_loss": {
        "reference_cross_section_m2": 0.0001,
        "reactive_wall_area_over_reference_area": 0.02,
        "cellwise_history": [
          {
            "elapsed_time_s": 0.0,
            "cells": [
              {
                "cell_index": 0,
                "reactive_wall_area_over_reference_area": 0.002,
                "signed_local_cell_average_recession_m": 0.0
              },
              {
                "cell_index": 1,
                "reactive_wall_area_over_reference_area": 0.006,
                "signed_local_cell_average_recession_m": 0.0
              },
              {
                "cell_index": 2,
                "reactive_wall_area_over_reference_area": 0.012,
                "signed_local_cell_average_recession_m": 0.0
              }
            ]
          },
          {
            "elapsed_time_s": 3600.0,
            "cells": [
              {
                "cell_index": 0,
                "reactive_wall_area_over_reference_area": 0.002,
                "signed_local_cell_average_recession_m": 1e-08
              },
              {
                "cell_index": 1,
                "reactive_wall_area_over_reference_area": 0.006,
                "signed_local_cell_average_recession_m": 2e-08
              },
              {
                "cell_index": 2,
                "reactive_wall_area_over_reference_area": 0.012,
                "signed_local_cell_average_recession_m": -1e-08
              }
            ]
          }
        ]
      }
    }
  },
  "supported_minimum_aperture_m": 2e-06,
  "supported_maximum_aperture_m": 2e-05,
  "wall_recession_is_per_combined_reactive_area_reviewed": true,
  "opposing_face_recession_is_equal_reviewed": true,
  "cell_center_to_face_mapping_reviewed": true,
  "geometry_basis_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/electrochemical_numeric.py#L74)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

# `structural.thermal_gradient_discretization_convergence`

**목적:** All refinement levels share exact geometry, boundary, property, provider and common-query identity.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `comparison_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `boundary_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `boundary_condition_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `material_property_state_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_property_state_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `solver_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `solver_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `common_queries` | 예 | `{"items": {"$ref": "#/$defs/ThermalObservationQuery"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `refinement_levels` | 예 | `{"items": {"$ref": "#/$defs/ThermalDiscretizationLevel"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `refinement_path_scale_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_change_normalization_scale_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `maximum_adjacent_weighted_rms_change_K` | 예 | `{"minimum": 0, "type": "number"}` | K |
| `maximum_adjacent_relative_rms_change` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `observed_order_refinement_ratio_tolerance` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `geometry_boundary_property_and_provider_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `input_result_mesh_and_time_step_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `common_query_identity_units_and_weights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `refinement_order_and_relationships_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `refinement_path_scale_definition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `level_validity_and_missingness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `diagnostic_norm_tolerances_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ThermalGradientDiscretizationConvergence.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `comparison_id` | `1` |
| `component_id` | `1` |
| `provider_id` | `1` |
| `solver_id` | `1` |
| `solver_revision` | `1` |
| `level_ids` | `1` |
| `common_query_ids` | `1` |
| `adjacent_level_diagnostics` | `mixed` |
| `observed_order_diagnostics` | `mixed` |
| `all_adjacent_levels_meet_declared_rms_diagnostics` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- All refinement levels share exact geometry, boundary, property, provider and common-query identity.
- Spatial and time discretization metadata and per-level input, result, mesh and time-step digests remain explicit.
- Adjacent changes and observed-order values are diagnostics rather than convergence claims.

## 구현 근거·독립 설명

- `authored_external_thermal_discretization_refinement_diagnostic`: Compare ordered external-solver transient-temperature refinement levels at an identical reviewed query set while preserving geometry, boundary, material-property, solver, mesh, time-step, input, result and query digests. Report adjacent weighted temperature changes and an observed-order diagnostic only when its finite equal-ratio prerequisites hold; do not claim convergence, an error bound, PDE qualification, stress, fit, acceptance, life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "structural.thermal_gradient_discretization_convergence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["structural.thermal_gradient_discretization_convergence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "comparison_id": "thermal-refinement-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "component_id": "component-1",
  "physical_scope_definition": "reviewed external transient solver scope",
  "time_basis": "solver elapsed seconds",
  "geometry_id": "geometry-1",
  "geometry_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "boundary_condition_id": "boundary-1",
  "boundary_condition_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "material_property_state_id": "property-state-1",
  "material_property_state_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "provider_id": "provider-1",
  "solver_id": "solver-1",
  "solver_revision": "rev-1",
  "provider_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "common_queries": [
    {
      "query_id": "q-1",
      "elapsed_time_s": 5.0,
      "position_m": 0.1,
      "query_definition": "temperature at first reviewed coordinate",
      "comparison_weight": 1.0,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored refinement test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "query_id": "q-2",
      "elapsed_time_s": 10.0,
      "position_m": 0.2,
      "query_definition": "temperature at second reviewed coordinate",
      "comparison_weight": 1.0,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored refinement test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "refinement_levels": [
    {
      "level_id": "coarse",
      "ordinal": 0,
      "relationship_to_previous": "initial",
      "spatial_characteristic_size_m": 0.1,
      "maximum_time_step_s": 1.0,
      "spatial_cell_count": 10,
      "time_step_count": 20,
      "refinement_path_scale": 1.0,
      "mesh_id": "mesh-0",
      "mesh_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "time_step_schedule_id": "time-0",
      "time_step_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "provider_input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "provider_result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "level_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "query_temperatures": [
        {
          "query_id": "q-1",
          "temperature_K": 300.0,
          "provider_query_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored refinement test",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "query_id": "q-2",
          "temperature_K": 320.0,
          "provider_query_result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored refinement test",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "level_record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored refinement test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "level_id": "medium",
      "ordinal": 1,
      "relationship_to_previous": "nested_refinement",
      "spatial_characteristic_size_m": 0.05,
      "maximum_time_step_s": 0.5,
      "spatial_cell_count": 20,
      "time_step_count": 40,
      "refinement_path_scale": 0.5,
      "mesh_id": "mesh-1",
      "mesh_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "time_step_schedule_id": "time-1",
      "time_step_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "provider_input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "provider_result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "level_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "query_temperatures": [
        {
          "query_id": "q-1",
          "temperature_K": 302.0,
          "provider_query_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored refinement test",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "query_id": "q-2",
          "temperature_K": 318.0,
          "provider_query_result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored refinement test",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "level_record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored refinement test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "level_id": "fine",
      "ordinal": 2,
      "relationship_to_previous": "nested_refinement",
      "spatial_characteristic_size_m": 0.025,
      "maximum_time_step_s": 0.25,
      "spatial_cell_count": 40,
      "time_step_count": 80,
      "refinement_path_scale": 0.25,
      "mesh_id": "mesh-2",
      "mesh_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "time_step_schedule_id": "time-2",
      "time_step_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "provider_input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "provider_result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "level_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "query_temperatures": [
        {
          "query_id": "q-1",
          "temperature_K": 303.0,
          "provider_query_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored refinement test",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "query_id": "q-2",
          "temperature_K": 317.0,
          "provider_query_result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored refinement test",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "level_record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored refinement test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "refinement_path_scale_definition": "caller dimensionless joint space-time path coordinate",
  "temperature_change_normalization_scale_K": 100.0,
  "maximum_adjacent_weighted_rms_change_K": 1.5,
  "maximum_adjacent_relative_rms_change": 0.02,
  "observed_order_refinement_ratio_tolerance": 1e-09,
  "geometry_boundary_property_and_provider_identity_reviewed": true,
  "input_result_mesh_and_time_step_digests_reviewed": true,
  "common_query_identity_units_and_weights_reviewed": true,
  "refinement_order_and_relationships_reviewed": true,
  "refinement_path_scale_definition_reviewed": true,
  "level_validity_and_missingness_reviewed": true,
  "diagnostic_norm_tolerances_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored refinement test",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/thermal_gradient_discretization_convergence.py#L140)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

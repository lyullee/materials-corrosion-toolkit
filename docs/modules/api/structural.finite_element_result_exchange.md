# `structural.finite_element_result_exchange`

**목적:** Mesh and result identities, coordinate frame, ordering, quantity definitions and content digests are caller-reviewed metadata.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `exchange_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `analysis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `model_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `model_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `mesh` | 예 | `{"$ref": "#/$defs/FEMeshDescriptor"}` | 계약·필드 설명 참조 |
| `material_assignments` | 예 | `{"items": {"$ref": "#/$defs/FEMaterialAssignment"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `load_boundary_cases` | 예 | `{"items": {"$ref": "#/$defs/FELoadBoundaryCase"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `result_fields` | 예 | `{"items": {"$ref": "#/$defs/FEResultFieldDescriptor"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `solver_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `solver_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `solver_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `solver_input_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `solver_result_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `convergence_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `convergence_record_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `convergence_record_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `verification_records` | 예 | `{"items": {"$ref": "#/$defs/FEVerificationRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `qualification_envelope` | 예 | `{"$ref": "#/$defs/FEResultExchangeEnvelope"}` | 계약·필드 설명 참조 |
| `model_mesh_and_coordinate_frame_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_assignments_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `load_and_boundary_cases_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `step_time_frequency_and_result_location_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `quantity_components_units_shape_and_order_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `solver_revision_configuration_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `verification_partitions_and_source_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FiniteElementResultExchange.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `exchange_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `physical_scope_id` | `1` |
| `analysis_id` | `1` |
| `model_id` | `1` |
| `mesh_id` | `1` |
| `qualification_envelope_id` | `1` |
| `mesh_outside_support_reasons` | `1` |
| `field_comparisons` | `mixed` |
| `outside_support_field_ids` | `1` |
| `verification_partition_counts` | `count` |
| `physical_specimen_ids` | `1` |
| `source_group_ids` | `1` |
| `declared_exchange_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Mesh and result identities, coordinate frame, ordering, quantity definitions and content digests are caller-reviewed metadata.
- Solver revision, configuration, input and result digests bind the exchange without embedding solver output arrays.
- Qualification support and verification partitions do not establish mesh convergence, solver validity or code acceptance.

## 구현 근거·독립 설명

- `reviewed_finite_element_result_exchange_envelope`: Exchange digest-bound finite-element mesh and result metadata with model, mesh, coordinate, material assignment, load and boundary, step, result location, averaging, quantity, unit, component, shape and ordering identities plus solver convergence and partitioned verification records. Do not bundle large arrays, interpolate results, qualify a mesh, or infer acceptance, life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "structural.finite_element_result_exchange"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["structural.finite_element_result_exchange"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "exchange_id": "authored-fe-exchange",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "scope-1",
  "analysis_id": "analysis-1",
  "model_id": "model-1",
  "model_revision": "1",
  "mesh": {
    "mesh_id": "mesh-1",
    "mesh_revision": "1",
    "coordinate_frame_id": "frame-1",
    "dimensionality": "3d",
    "element_family_ids": [
      "solid-a"
    ],
    "node_count": 10,
    "element_count": 4,
    "region_ids": [
      "region-1"
    ],
    "node_identity_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "element_identity_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "connectivity_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "geometry_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored mesh"
      }
    ]
  },
  "material_assignments": [
    {
      "assignment_id": "assignment-1",
      "region_id": "region-1",
      "material_id": "material-1",
      "material_condition_id": "condition-1",
      "property_provider_id": "provider-1",
      "property_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "assignment_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored assignment"
        }
      ]
    }
  ],
  "load_boundary_cases": [
    {
      "case_id": "case-1",
      "load_definition_id": "load-1",
      "boundary_definition_id": "boundary-1",
      "load_basis": "authored",
      "load_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "boundary_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored load case"
        }
      ]
    }
  ],
  "result_fields": [
    {
      "field_id": "field-1",
      "case_id": "case-1",
      "step_id": "step-1",
      "time_s": 1.0,
      "region_id": "region-1",
      "result_location": "integration_point",
      "averaging_basis": "unaveraged",
      "quantity_kind": "tensor",
      "quantity_id": "stress",
      "quantity_definition": "authored Cauchy stress",
      "unit_token": "Pa",
      "component_ids": [
        "xx",
        "yy",
        "zz",
        "xy",
        "yz",
        "zx"
      ],
      "array_shape": [
        4,
        6
      ],
      "array_order": "C",
      "identity_axis_basis": "element then component",
      "array_content_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored field"
        }
      ]
    }
  ],
  "solver_id": "solver-1",
  "solver_revision": "1",
  "solver_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "solver_input_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "solver_result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "convergence_definition": "authored residual and mesh review",
  "convergence_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "convergence_record_reviewed": true,
  "verification_records": [
    {
      "verification_id": "verify-1",
      "partition": "calibration",
      "physical_specimen_id": "specimen-1",
      "source_group_id": "source-1",
      "verification_kind": "authored comparison",
      "metric_id": "relative-error",
      "metric_value": 0.1,
      "metric_unit_token": "1",
      "provider_id": "provider-1",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored calibration"
        }
      ]
    },
    {
      "verification_id": "verify-2",
      "partition": "holdout",
      "physical_specimen_id": "specimen-2",
      "source_group_id": "source-2",
      "verification_kind": "authored comparison",
      "metric_id": "relative-error",
      "metric_value": 0.2,
      "metric_unit_token": "1",
      "provider_id": "provider-1",
      "result_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored holdout"
        }
      ]
    }
  ],
  "qualification_envelope": {
    "envelope_id": "envelope-1",
    "supported_dimensionalities": [
      "3d"
    ],
    "supported_element_family_ids": [
      "solid-a"
    ],
    "supported_result_locations": [
      "integration_point"
    ],
    "supported_quantity_ids": [
      "stress"
    ],
    "supported_unit_tokens": [
      "Pa"
    ],
    "maximum_node_count": 100,
    "maximum_element_count": 100,
    "required_partitions": [
      "calibration",
      "holdout"
    ],
    "solver_id": "solver-1",
    "solver_revision": "1",
    "solver_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "qualification_basis": "authored envelope",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored FE envelope"
      }
    ]
  },
  "model_mesh_and_coordinate_frame_reviewed": true,
  "material_assignments_reviewed": true,
  "load_and_boundary_cases_reviewed": true,
  "step_time_frequency_and_result_location_reviewed": true,
  "quantity_components_units_shape_and_order_reviewed": true,
  "solver_revision_configuration_and_digests_reviewed": true,
  "verification_partitions_and_source_groups_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored FE exchange"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/finite_element_exchange.py#L210)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

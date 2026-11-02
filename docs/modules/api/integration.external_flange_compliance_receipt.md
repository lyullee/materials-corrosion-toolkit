# `integration.external_flange_compliance_receipt`

**목적:** A digest-pinned finite-element receipt must identify the selected load case, mesh, coordinate frame, stiffness result field, explicit translational DOF map and contact-normal signs before reduction.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `binding_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_receipt` | 예 | `{"$ref": "#/$defs/StructuralProviderResultReceipt"}` | 계약·필드 설명 참조 |
| `load_case_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `boundary_condition_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `stiffness_field_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `stiffness_quantity_id` | 예 | `{"const": "incremental_stiffness_matrix", "type": "string"}` | 계약·필드 설명 참조 |
| `stiffness_array_content_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `stiffness_array_order` | 예 | `{"enum": ["C", "F"], "type": "string"}` | 계약·필드 설명 참조 |
| `mesh_node_id_map_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `dof_basis_transform_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `stiffness_matrix_N_m` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 128, "minItems": 2, "type": "array"}` | N·m |
| `normalized_stiffness_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `coordinate_frame_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `displacement_unit` | 예 | `{"const": "m", "type": "string"}` | 계약·필드 설명 참조 |
| `force_unit` | 예 | `{"const": "N", "type": "string"}` | 계약·필드 설명 참조 |
| `matrix_unit` | 예 | `{"const": "N/m", "type": "string"}` | 계약·필드 설명 참조 |
| `global_dof_node_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 128, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `global_dof_component_ids` | 예 | `{"items": {"enum": ["translation_x", "translation_y", "translation_z"], "type": "string"}, "maxItems": 128, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `fixed_incremental_dof_indices` | 아니오 | `{"default": [], "items": {"type": "integer"}, "type": "array"}` | 계약·필드 설명 참조 |
| `contact_node_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 64, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `contact_normal_dof_indices` | 예 | `{"items": {"type": "integer"}, "maxItems": 64, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `contact_closure_signs` | 예 | `{"items": {"enum": [-1, 1], "type": "integer"}, "maxItems": 64, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `stiffness_units_and_scaling_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `load_case_and_boundary_conditions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `mesh_frame_and_dof_order_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `dof_basis_transform_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `contact_normal_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `incremental_linear_elastic_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ExternalFlangeComplianceBinding.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `flange_relative_compliance_matrix_m_N` | `m/N` |
| `minimum_free_stiffness_eigenvalue_N_m` | `N/m` |
| `free_stiffness_condition_number` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- A digest-pinned finite-element receipt must identify the selected load case, mesh, coordinate frame, stiffness result field, explicit translational DOF map and contact-normal signs before reduction.
- This interface consumes an already reduced incremental stiffness matrix; it does not assemble/solve FE, transform mixed rotational DOFs, model nonlinear gasket response or qualify sealing.

## 구현 근거·독립 설명

- `external_flange_fe_compliance_receipt`: Require a digest-verified finite-element provider receipt and exact load-case, boundary-condition, mesh, frame, matrix-field identity/shape/unit/content digest, node/component DOF order, support indices, contact node/normal DOFs, closure signs and DOF-transform lineage. Convert only the caller-provided already reduced translational tangent stiffness matrix into the existing flange contact compliance reduction API; preserve provider, mesh, field and mapping lineage. This adapter does not run or assemble FE, infer transformations, handle mixed rotational DOFs, model nonlinear contact or establish seal qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.external_flange_compliance_receipt"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["integration.external_flange_compliance_receipt"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "binding_id": "synthetic-external-flange",
  "provider_receipt": {
    "schema_version": "matintegrity.structural_provider_receipt.v1",
    "receipt_id": "synthetic-receipt",
    "analysis_kind": "finite_element",
    "asset_id": "synthetic-asset",
    "component_id": "flange",
    "location_id": "synthetic-location",
    "physical_scope_id": "synthetic-scope",
    "analysis_id": "analysis-1",
    "model_id": "synthetic-fe",
    "model_revision": "1",
    "mesh": {
      "mesh_id": "mesh-1",
      "mesh_revision": "1",
      "coordinate_frame_id": "synthetic-frame",
      "dimensionality": "3d",
      "element_family_ids": [
        "solid"
      ],
      "node_count": 3,
      "element_count": 1,
      "mesh_content_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    "load_case_ids": [
      "load-1"
    ],
    "load_case_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "result_fields": [
      {
        "field_id": "stiffness-1",
        "load_case_id": "load-1",
        "step_id": "step-1",
        "coordinate_frame_id": "synthetic-frame",
        "region_id": "global",
        "result_location": "global",
        "averaging_basis": "none",
        "quantity_id": "incremental_stiffness_matrix",
        "quantity_definition": "Incremental tangent matrix",
        "unit_token": "N/m",
        "component_ids": [
          "i",
          "j"
        ],
        "array_shape": [
          3,
          3
        ],
        "array_order": "C",
        "array_content_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "result_record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
      }
    ],
    "diagnostics": [
      {
        "diagnostic_id": "diag-1",
        "category": "equilibrium",
        "metric_id": "residual",
        "metric_definition": "Synthetic zero residual",
        "status": "reported",
        "value": 0.0,
        "expanded_uncertainty": 0.0,
        "unit_token": "1",
        "provider_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "evidence": [
          {
            "source_id": "synthetic-fe",
            "origin": "synthetic",
            "citation": "Synthetic provider diagnostic.",
            "license_id": null,
            "sha256": null
          }
        ]
      }
    ],
    "provider_id": "synthetic-fe",
    "provider_revision": "1",
    "provider_configuration_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "provider_input_digest": "1111111111111111111111111111111111111111111111111111111111111111",
    "provider_result_digest": "2222222222222222222222222222222222222222222222222222222222222222",
    "evidence": [
      {
        "source_id": "synthetic-fe",
        "origin": "synthetic",
        "citation": "Synthetic provider receipt.",
        "license_id": null,
        "sha256": null
      }
    ],
    "payload_digest": "7bef153c147084f20e67616ee55895795f995da76374445e85755285a5e59d12"
  },
  "load_case_id": "load-1",
  "boundary_condition_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "stiffness_field_id": "stiffness-1",
  "stiffness_quantity_id": "incremental_stiffness_matrix",
  "stiffness_array_content_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "stiffness_array_order": "C",
  "mesh_node_id_map_sha256": "3333333333333333333333333333333333333333333333333333333333333333",
  "dof_basis_transform_sha256": "4444444444444444444444444444444444444444444444444444444444444444",
  "stiffness_matrix_N_m": [
    [
      3000.0,
      -1000.0,
      0.0
    ],
    [
      -1000.0,
      3000.0,
      -1000.0
    ],
    [
      0.0,
      -1000.0,
      2000.0
    ]
  ],
  "normalized_stiffness_sha256": "5258efa1a095533d45b9ed744fed1453bdb9e5bc2ab99436744675dee90d5334",
  "coordinate_frame_id": "synthetic-frame",
  "displacement_unit": "m",
  "force_unit": "N",
  "matrix_unit": "N/m",
  "global_dof_node_ids": [
    "fixed",
    "gasket-sector-1",
    "gasket-sector-2"
  ],
  "global_dof_component_ids": [
    "translation_x",
    "translation_y",
    "translation_z"
  ],
  "fixed_incremental_dof_indices": [
    0
  ],
  "contact_node_ids": [
    "gasket-sector-1",
    "gasket-sector-2"
  ],
  "contact_normal_dof_indices": [
    1,
    2
  ],
  "contact_closure_signs": [
    1,
    1
  ],
  "stiffness_units_and_scaling_reviewed": true,
  "load_case_and_boundary_conditions_reviewed": true,
  "mesh_frame_and_dof_order_reviewed": true,
  "dof_basis_transform_reviewed": true,
  "contact_normal_mapping_reviewed": true,
  "incremental_linear_elastic_applicability_reviewed": true,
  "computational_use_authorized": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/external_flange_compliance.py#L191)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

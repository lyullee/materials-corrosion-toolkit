# `fabrication.flange_contact_field`

**목적:** Caller-supplied symmetric positive-semidefinite relative flange compliance and per-node linear gasket springs define the spatial contact response.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.flange_contact_field.v1", "default": "matintegrity.flange_contact_field.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `response_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `response_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `response_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `response_result_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `node_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 256, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `circumferential_coordinate_rad` | 예 | `{"items": {"type": "number"}, "maxItems": 256, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `gasket_contact_area_m2` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 256, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `gasket_compressive_stiffness_N_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 256, "minItems": 2, "type": "array"}` | N·m |
| `free_closure_without_gasket_m` | 예 | `{"items": {"type": "number"}, "maxItems": 256, "minItems": 2, "type": "array"}` | m |
| `flange_relative_compliance_matrix_m_N` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 256, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `matrix_symmetry_tolerance_m_N` | 예 | `{"exclusiveMinimum": 0, "maximum": 1e-06, "type": "number"}` | 계약·필드 설명 참조 |
| `compliance_psd_tolerance_m_N` | 예 | `{"exclusiveMinimum": 0, "maximum": 1e-06, "type": "number"}` | 계약·필드 설명 참조 |
| `active_set_maximum_iterations` | 아니오 | `{"default": 10000, "maximum": 100000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `active_set_work_budget` | 아니오 | `{"default": 50000000, "maximum": 1000000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `force_tolerance_N` | 아니오 | `{"default": 1e-06, "exclusiveMinimum": 0, "type": "number"}` | N |
| `gap_tolerance_m` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | m |
| `complementarity_tolerance_N_m` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "type": "number"}` | N·m |
| `flange_operator_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `response_scope_and_coordinates_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `bolt_pressure_and_boundary_load_composition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `gasket_linearization_and_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `compression_only_contact_model_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FlangeContactFieldRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `response_field.circumferential_coordinate_rad` | `rad` |
| `response_field.contact_force_N` | `N` |
| `response_field.mean_contact_pressure_Pa` | `Pa` |
| `response_field.linearized_gasket_compression_m` | `m` |
| `response_field.contact_gap_m` | `m` |
| `response_field.free_closure_without_gasket_m` | `m` |
| `contact_force_sum_N` | `N` |
| `contact_area_sum_m2` | `m2` |
| `minimum_flange_compliance_eigenvalue_m_N` | `m/N` |
| `maximum_complementarity_residual_N_m` | `N m` |
| `active_set_iterations` | `1` |
| `active_set_work_units` | `1` |
| `node_count` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-supplied symmetric positive-semidefinite relative flange compliance and per-node linear gasket springs define the spatial contact response.
- A deterministic active-set complementarity solve enforces nonnegative contact force and nonnegative gap; every load, coordinate and response operator requires explicit scope and computational-use review.
- No FE response, bolt/load distribution, geometry, nonlinear gasket law, local pressure stress, leakage, seal criterion or acceptance is inferred.

## 구현 근거·독립 설명

- `caller_spatial_flange_contact_compliance`: Solve a nodal unilateral contact complementarity problem from a caller-supplied symmetric positive-semidefinite relative flange compliance matrix, caller-composed free-closure vector, and local linear gasket stiffnesses. The active-set method requires nonnegative contact forces and gaps, checks the matrix support and preserves each provider result digest. It consumes but does not calculate the flange compliance operator, infer bolt/load composition, reconstruct local stress, predict leakage or establish sealing acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.flange_contact_field"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.flange_contact_field"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.flange_contact_field.v1",
  "assessment_id": "synthetic-flange-contact-field",
  "joint_id": "synthetic-circumferential-joint",
  "physical_scope_id": "synthetic-one-fixture",
  "response_provider_id": "example://symmetric-compliance-fixture",
  "response_provider_revision": "synthetic-1",
  "response_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "response_result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "node_ids": [
    "c0",
    "c1",
    "c2",
    "c3"
  ],
  "circumferential_coordinate_rad": [
    0.0,
    1.5707963267948966,
    3.141592653589793,
    4.71238898038469
  ],
  "gasket_contact_area_m2": [
    0.01,
    0.01,
    0.01,
    0.01
  ],
  "gasket_compressive_stiffness_N_m": [
    1000000000.0,
    1000000000.0,
    1000000000.0,
    1000000000.0
  ],
  "free_closure_without_gasket_m": [
    1e-06,
    8e-07,
    -2e-07,
    2e-07
  ],
  "flange_relative_compliance_matrix_m_N": [
    [
      1e-09,
      2e-10,
      2e-10,
      2e-10
    ],
    [
      2e-10,
      1e-09,
      2e-10,
      2e-10
    ],
    [
      2e-10,
      2e-10,
      1e-09,
      2e-10
    ],
    [
      2e-10,
      2e-10,
      2e-10,
      1e-09
    ]
  ],
  "matrix_symmetry_tolerance_m_N": 1e-12,
  "compliance_psd_tolerance_m_N": 1e-12,
  "active_set_maximum_iterations": 100,
  "force_tolerance_N": 1e-06,
  "gap_tolerance_m": 1e-12,
  "complementarity_tolerance_N_m": 1e-09,
  "flange_operator_basis_reviewed": true,
  "response_scope_and_coordinates_reviewed": true,
  "bolt_pressure_and_boundary_load_composition_reviewed": true,
  "gasket_linearization_and_support_reviewed": true,
  "compression_only_contact_model_reviewed": true,
  "computational_use_authorized": true,
  "evidence": [
    {
      "source_id": "synthetic-flange-compliance-fixture",
      "origin": "synthetic",
      "citation": "Project-authored nodal compliance example"
    }
  ],
  "active_set_work_budget": 50000000
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/flange_contact_field.py#L594)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

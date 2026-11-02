# `fabrication.flange_contact_compliance_reduction_history`

**목적:** Reduce one caller-supplied constrained linear incremental stiffness matrix per aligned geometry/time knot using a fixed node/DOF mapping.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `upstream_solver_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `upstream_solver_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `times_s` | 예 | `{"items": {"type": "number"}, "maxItems": 1000, "minItems": 2, "type": "array"}` | s |
| `stiffness_source_sha256` | 예 | `{"items": {"type": "string"}, "maxItems": 1000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `stiffness_matrices_N_m` | 예 | `{"items": {"items": {"items": {"type": "number"}, "type": "array"}, "type": "array"}, "maxItems": 1000, "minItems": 2, "type": "array"}` | N·m |
| `fixed_incremental_dof_indices` | 아니오 | `{"default": [], "items": {"type": "integer"}, "type": "array"}` | 계약·필드 설명 참조 |
| `contact_node_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 64, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `contact_normal_dof_indices` | 예 | `{"items": {"type": "integer"}, "maxItems": 64, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `contact_closure_signs` | 예 | `{"items": {"enum": [-1, 1], "type": "integer"}, "maxItems": 64, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `symmetry_relative_tolerance` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "maximum": 1e-05, "type": "number"}` | 계약·필드 설명 참조 |
| `minimum_positive_stiffness_eigenvalue_N_m` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | N·m |
| `maximum_free_operator_condition_number` | 아니오 | `{"default": 1000000000000.0, "exclusiveMinimum": 0, "maximum": 100000000000000.0, "minimum": 1, "type": "number"}` | 계약·필드 설명 참조 |
| `stiffness_units_and_scaling_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `fixed_supports_and_boundary_dofs_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `contact_normal_dof_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `incremental_linear_elastic_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FlangeComplianceReductionHistoryRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `times_s` | `s` |
| `operator_history[].values.flange_relative_compliance_matrix_m_N` | `m/N` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Reduce one caller-supplied constrained linear incremental stiffness matrix per aligned geometry/time knot using a fixed node/DOF mapping.
- No matrix interpolation, FE response generation, nonlinear contact, leakage, seal qualification or between-knot transition is inferred.

## 구현 근거·독립 설명

- `caller_linear_flange_contact_compliance_history`: Reduce caller-supplied symmetric translational stiffness matrices to an aligned contact-compliance history using declared retained degrees of freedom and condensation constraints at each time knot. Preserve matrix order, knot alignment, source digests and positive-semidefinite checks; do not generate a finite-element stiffness matrix, infer interpolation between knots or evaluate gasket contact.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.flange_contact_compliance_reduction_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.flange_contact_compliance_reduction_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "synthetic-flange-operator-history",
  "upstream_solver_id": "caller-fea",
  "upstream_solver_revision": "synthetic-revision",
  "times_s": [
    0.0,
    10.0
  ],
  "stiffness_source_sha256": [
    "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "1111111111111111111111111111111111111111111111111111111111111111"
  ],
  "stiffness_matrices_N_m": [
    [
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
    [
      [
        3200.0,
        -1000.0,
        0.0
      ],
      [
        -1000.0,
        3200.0,
        -1000.0
      ],
      [
        0.0,
        -1000.0,
        2200.0
      ]
    ]
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
  "symmetry_relative_tolerance": 1e-10,
  "minimum_positive_stiffness_eigenvalue_N_m": 1e-12,
  "maximum_free_operator_condition_number": 1000000000000.0,
  "stiffness_units_and_scaling_reviewed": true,
  "fixed_supports_and_boundary_dofs_reviewed": true,
  "contact_normal_dof_mapping_reviewed": true,
  "incremental_linear_elastic_applicability_reviewed": true,
  "computational_use_authorized": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/flange_compliance_reduction.py#L215)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

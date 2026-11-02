# `fabrication.flange_viscoelastic_contact_history`

**목적:** Caller-supplied linear generalized-Maxwell gasket branches evolve exactly over declared piecewise-linear compression segments and are coupled to a caller-supplied symmetric positive-semidefinite flange compliance operator, optionally supplied as a digest-bound operator at every declared time knot.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.flange_viscoelastic_contact_history.v1", "default": "matintegrity.flange_viscoelastic_contact_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `response_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `response_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `response_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `response_result_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `node_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 128, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `times_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 10000, "minItems": 2, "type": "array"}` | s |
| `circumferential_coordinate_rad` | 예 | `{"items": {"type": "number"}, "maxItems": 128, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `gasket_contact_area_m2` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 128, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `gasket_thickness_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 128, "minItems": 2, "type": "array"}` | m |
| `equilibrium_modulus_Pa` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 128, "minItems": 2, "type": "array"}` | Pa |
| `prony_branches` | 예 | `{"items": {"items": {"$ref": "#/$defs/FlangePronyBranch"}, "type": "array"}, "maxItems": 128, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `initial_branch_stress_Pa` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 128, "minItems": 2, "type": "array"}` | Pa |
| `free_closure_without_gasket_m` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 10000, "minItems": 2, "type": "array"}` | m |
| `flange_relative_compliance_matrix_m_N` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 128, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `flange_compliance_history_result` | 아니오 | `{"anyOf": [{"additionalProperties": true, "type": "object"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `flange_compliance_history_sha256` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `matrix_symmetry_tolerance_m_N` | 예 | `{"exclusiveMinimum": 0, "maximum": 1e-06, "type": "number"}` | 계약·필드 설명 참조 |
| `compliance_psd_tolerance_m_N` | 예 | `{"exclusiveMinimum": 0, "maximum": 1e-06, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_contact_iterations` | 아니오 | `{"default": 10000, "maximum": 100000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_contact_work_units` | 아니오 | `{"default": 50000000, "maximum": 1000000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `gap_tolerance_m` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | m |
| `force_tolerance_N` | 아니오 | `{"default": 1e-06, "exclusiveMinimum": 0, "type": "number"}` | N |
| `flange_operator_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `response_scope_and_coordinates_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `bolt_pressure_and_boundary_load_composition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `gasket_prony_calibration_and_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `initial_branch_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `zero_compression_branch_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `compression_only_contact_model_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FlangeViscoelasticContactHistoryRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_history[].time_s` | `s` |
| `time_history[].contact_force_sum_N` | `N` |
| `time_history[].response_field[].circumferential_coordinate_rad` | `rad` |
| `time_history[].response_field[].contact_force_N` | `N` |
| `time_history[].response_field[].mean_contact_pressure_Pa` | `Pa` |
| `time_history[].response_field[].gasket_compression_m` | `m` |
| `time_history[].response_field[].gasket_stress_Pa` | `Pa` |
| `time_history[].response_field[].contact_gap_m` | `m` |
| `time_history[].response_field[].gasket_strain` | `1` |
| `time_history[].response_field[].branch_stress_Pa[]` | `Pa` |
| `minimum_flange_compliance_eigenvalue_m_N` | `m/N` |
| `contact_iteration_count` | `1` |
| `contact_work_units` | `1` |
| `node_count` | `1` |
| `time_knot_count` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-supplied linear generalized-Maxwell gasket branches evolve exactly over declared piecewise-linear compression segments and are coupled to a caller-supplied symmetric positive-semidefinite flange compliance operator, optionally supplied as a digest-bound operator at every declared time knot.
- Unilateral quasi-static contact is solved at declared time knots; the initial knot is an instantaneous load from the reviewed zero-compression branch state. No between-knot operator interpolation, transition time, FE response, leakage, peak stress or acceptance is inferred.

## 구현 근거·독립 설명

- `caller_spatial_linear_prony_flange_contact_history`: Advance caller-calibrated linear generalized-Maxwell gasket branches at spatial contact nodes over explicitly sampled free-closure history, using exact exponential branch updates over piecewise-linear strain segments. At each declared knot, solve a unilateral quasi-static contact problem against a caller-supplied symmetric positive-semidefinite flange compliance matrix. Preserve provider result lineage and fail closed on unsupported compliance, unmet review gates or contact iteration limits. The initial knot is an instantaneous load from a reviewed zero-compression branch state. No flange FE response, within-interval contact transition, nonlinear hysteresis, leakage or acceptance is inferred.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.flange_viscoelastic_contact_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.flange_viscoelastic_contact_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.flange_viscoelastic_contact_history.v1",
  "assessment_id": "synthetic-spatial-prony-history",
  "joint_id": "synthetic-circular-joint",
  "physical_scope_id": "synthetic-fixture",
  "response_provider_id": "example://coupled-compliance-fixture",
  "response_provider_revision": "synthetic-1",
  "response_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "response_result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "node_ids": [
    "n0",
    "n1"
  ],
  "times_s": [
    0.0,
    100.0,
    500.0
  ],
  "circumferential_coordinate_rad": [
    0.0,
    3.141592653589793
  ],
  "gasket_contact_area_m2": [
    0.01,
    0.01
  ],
  "gasket_thickness_m": [
    0.01,
    0.01
  ],
  "equilibrium_modulus_Pa": [
    10000000.0,
    10000000.0
  ],
  "prony_branches": [
    [
      {
        "modulus_Pa": 20000000.0,
        "relaxation_time_s": 100.0,
        "branch_id": "fast"
      }
    ],
    [
      {
        "modulus_Pa": 20000000.0,
        "relaxation_time_s": 100.0,
        "branch_id": "fast"
      }
    ]
  ],
  "initial_branch_stress_Pa": [
    [
      0.0
    ],
    [
      0.0
    ]
  ],
  "free_closure_without_gasket_m": [
    [
      1e-05,
      8e-06
    ],
    [
      9e-06,
      6e-06
    ],
    [
      7e-06,
      4e-06
    ]
  ],
  "flange_relative_compliance_matrix_m_N": [
    [
      1e-09,
      2e-10
    ],
    [
      2e-10,
      1e-09
    ]
  ],
  "matrix_symmetry_tolerance_m_N": 1e-12,
  "compliance_psd_tolerance_m_N": 1e-12,
  "maximum_contact_iterations": 10000,
  "maximum_contact_work_units": 1000000,
  "gap_tolerance_m": 1e-12,
  "force_tolerance_N": 1e-06,
  "flange_operator_basis_reviewed": true,
  "response_scope_and_coordinates_reviewed": true,
  "bolt_pressure_and_boundary_load_composition_reviewed": true,
  "gasket_prony_calibration_and_support_reviewed": true,
  "initial_branch_state_reviewed": true,
  "zero_compression_branch_state_reviewed": true,
  "compression_only_contact_model_reviewed": true,
  "computational_use_authorized": true,
  "evidence": [
    {
      "origin": "synthetic",
      "citation": "Project-authored synthetic fixture; not experimental data",
      "source_id": "synthetic-prony-compliance-fixture"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/flange_contact_field.py#L256)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

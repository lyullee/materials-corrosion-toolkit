# `fabrication.flange_nonlinear_viscoelastic_contact_history`

**목적:** Caller nonlinear Maxwell branch backbones and equilibrium gasket backbone are coupled to caller-supplied positive-semidefinite flange compliance.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.flange_nonlinear_viscoelastic_contact_history.v1", "default": "matintegrity.flange_nonlinear_viscoelastic_contact_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `response_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `response_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `response_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `response_result_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `material` | 예 | `{"$ref": "#/$defs/NonlinearGasketViscoelasticMaterial"}` | 계약·필드 설명 참조 |
| `node_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 64, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `times_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 10000, "minItems": 2, "type": "array"}` | s |
| `circumferential_coordinate_rad` | 예 | `{"items": {"type": "number"}, "maxItems": 64, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `gasket_contact_area_m2` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 64, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `gasket_thickness_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 64, "minItems": 2, "type": "array"}` | m |
| `initial_branch_stress_by_node_Pa` | 아니오 | `{"anyOf": [{"items": {"items": {"type": "number"}, "type": "array"}, "type": "array"}, {"type": "null"}], "default": null}` | Pa |
| `free_closure_without_gasket_m` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 10000, "minItems": 2, "type": "array"}` | m |
| `flange_relative_compliance_matrix_m_N` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 64, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `flange_relative_compliance_history_m_N` | 아니오 | `{"anyOf": [{"items": {"items": {"items": {"type": "number"}, "type": "array"}, "type": "array"}, "type": "array"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `compliance_history_interpolation_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_compressive_strain` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `matrix_symmetry_tolerance_m_N` | 예 | `{"exclusiveMinimum": 0, "maximum": 1e-06, "type": "number"}` | 계약·필드 설명 참조 |
| `compliance_psd_tolerance_m_N` | 예 | `{"exclusiveMinimum": 0, "maximum": 1e-06, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_contact_iterations` | 아니오 | `{"default": 10000, "maximum": 100000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_newton_iterations_per_active_set` | 아니오 | `{"default": 100, "maximum": 1000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_contact_work_units` | 아니오 | `{"default": 50000000, "maximum": 1000000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_contact_transition_step_s` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | s |
| `additional_contact_sampling_times_s` | 아니오 | `{"default": [], "items": {"minimum": 0, "type": "number"}, "maxItems": 9998, "type": "array"}` | s |
| `contact_transition_time_sampling_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `contact_transition_time_tolerance_s` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | s |
| `single_contact_transition_per_refined_interval_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_transition_refinement_solves` | 아니오 | `{"default": 100, "maximum": 10000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_transition_refinement_work_units` | 아니오 | `{"default": 50000000, "maximum": 1000000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `gap_tolerance_m` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | m |
| `force_tolerance_N` | 아니오 | `{"default": 1e-05, "exclusiveMinimum": 0, "type": "number"}` | N |
| `flange_operator_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `response_scope_and_coordinates_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `bolt_pressure_and_boundary_load_composition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_curve_condition_and_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `initial_branch_states_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `zero_compression_branch_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `nonlinear_history_integration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `unilateral_contact_model_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FlangeNonlinearViscoelasticContactHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_history[].time_s` | `s` |
| `requested_time_knots_s[]` | `s` |
| `evaluation_time_knots_s[]` | `s` |
| `maximum_contact_transition_step_s` | `s` |
| `contact_transition_time_tolerance_s` | `s` |
| `maximum_observed_transition_bracket_width_s` | `s` |
| `sampled_contact_transition_brackets[].lower_time_s` | `s` |
| `sampled_contact_transition_brackets[].upper_time_s` | `s` |
| `sampled_contact_transition_brackets[].bracket_width_s` | `s` |
| `sampled_contact_transition_brackets[].requested_time_tolerance_s` | `s` |
| `sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].time_s` | `s` |
| `sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].contact_force_N` | `N` |
| `sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].mean_contact_pressure_Pa` | `Pa` |
| `sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].gasket_compression_m` | `m` |
| `sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].gasket_strain` | `1` |
| `sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].gasket_constitutive_stress_Pa` | `Pa` |
| `sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].contact_gap_m` | `m` |
| `sampled_contact_transition_brackets[].refinement_observations[].time_s` | `s` |
| `sampled_contact_transition_brackets[].refinement_observations[].contact_force_N` | `N` |
| `sampled_contact_transition_brackets[].refinement_observations[].mean_contact_pressure_Pa` | `Pa` |
| `sampled_contact_transition_brackets[].refinement_observations[].gasket_compression_m` | `m` |
| `sampled_contact_transition_brackets[].refinement_observations[].gasket_strain` | `1` |
| `sampled_contact_transition_brackets[].refinement_observations[].gasket_constitutive_stress_Pa` | `Pa` |
| `sampled_contact_transition_brackets[].refinement_observations[].contact_gap_m` | `m` |
| `transition_refinement_complete` | `1` |
| `transition_refinement_solves` | `1` |
| `transition_refinement_work_units` | `1` |
| `transition_refinement_midpoint_times_s[]` | `s` |
| `time_history[].contact_force_sum_N` | `N` |
| `time_history[].maximum_active_force_residual_N` | `N` |
| `time_history[].response_field[].circumferential_coordinate_rad` | `rad` |
| `time_history[].response_field[].contact_force_N` | `N` |
| `time_history[].response_field[].mean_contact_pressure_Pa` | `Pa` |
| `time_history[].response_field[].gasket_compression_m` | `m` |
| `time_history[].response_field[].gasket_strain` | `1` |
| `time_history[].response_field[].gasket_constitutive_stress_Pa` | `Pa` |
| `time_history[].response_field[].contact_gap_m` | `m` |
| `time_history[].response_field[].branch_stress_Pa[]` | `Pa` |
| `minimum_flange_compliance_eigenvalue_m_N` | `m/N` |
| `time_history[].minimum_flange_compliance_eigenvalue_m_N` | `m/N` |
| `contact_work_units` | `1` |
| `contact_active_set_iterations` | `1` |
| `newton_iterations` | `1` |
| `node_count` | `1` |
| `time_knot_count` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller nonlinear Maxwell branch backbones and equilibrium gasket backbone are coupled to caller-supplied positive-semidefinite flange compliance. An optional time-varying matrix history is linearly interpolated only after explicit caller review and each evaluation matrix is checked for positive semidefiniteness.
- Optional replayed-path bisection narrows observed contact-state transition brackets only with caller-reviewed sampling and a single-transition-per-bracket assumption; it does not establish exact event timing. Each bracket preserves both sampled endpoint states and response quantities; each refinement replay also records its sampled midpoint response, applied compliance-operator digest, and replay-input digest. These records expose the bounded search history but do not establish an exact event root or detect unobserved transitions. No extrapolation, constitutive fitting/transfer, flange FE generation, leakage or seal acceptance is inferred.

## 구현 근거·독립 설명

- `caller_nonlinear_maxwell_spatial_gasket_contact`: Couple caller-supplied monotone equilibrium and nonlinear generalized-Maxwell stress-strain backbones to a caller flange-compliance matrix at spatial contact nodes. Advance each branch over explicit piecewise-linear strain intervals with exact exponential updates split at backbone knots, and solve unilateral quasi-static contact at declared time knots using a bounded damped Newton active set. Preserve material and structural provider digests; fail closed on loss of local positive tangent, curve/support exceedance, nonconvergence or work-budget exhaustion. The initial knot is an instantaneous load from a reviewed zero-strain state. No flange FE response generation, intermediate contact transition, leakage, seal performance or acceptance is inferred.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.flange_nonlinear_viscoelastic_contact_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.flange_nonlinear_viscoelastic_contact_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.flange_nonlinear_viscoelastic_contact_history.v1",
  "assessment_id": "synthetic-nonlinear-spatial-gasket-history",
  "joint_id": "synthetic-circular-flange-joint",
  "physical_scope_id": "synthetic-fixture",
  "response_provider_id": "example://coupled-compliance-fixture",
  "response_provider_revision": "synthetic-1",
  "response_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "response_result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "material": {
    "material_condition_id": "synthetic-gasket-condition",
    "physical_specimen_id": "synthetic-fixture-only",
    "source_group_id": "synthetic-example-no-observation",
    "condition_sha256": "7025be60187731de2b3ea0abd39206124247e3ef9c98f746f4c847e8889c50ac",
    "source_sha256": "91706b4e775f981efbadeabadc819e777c7f980b5faf0bf6c5bd6e14a377ccb5",
    "provider_id": "example://synthetic-fixture",
    "provider_revision": "1",
    "temperature_K": 293.15,
    "equilibrium_stress_strain_backbone": [
      {
        "compressive_strain": 0,
        "stress_Pa": 0
      },
      {
        "compressive_strain": 0.05,
        "stress_Pa": 5000000.0
      },
      {
        "compressive_strain": 0.15,
        "stress_Pa": 18000000.0
      }
    ],
    "branches": [
      {
        "branch_id": "short-relaxation",
        "relaxation_time_s": 3600.0,
        "stress_strain_backbone": [
          {
            "compressive_strain": 0,
            "stress_Pa": 0
          },
          {
            "compressive_strain": 0.05,
            "stress_Pa": 2000000.0
          },
          {
            "compressive_strain": 0.15,
            "stress_Pa": 7000000.0
          }
        ]
      },
      {
        "branch_id": "long-relaxation",
        "relaxation_time_s": 36000.0,
        "stress_strain_backbone": [
          {
            "compressive_strain": 0,
            "stress_Pa": 0
          },
          {
            "compressive_strain": 0.05,
            "stress_Pa": 1000000.0
          },
          {
            "compressive_strain": 0.15,
            "stress_Pa": 4000000.0
          }
        ]
      }
    ],
    "initial_branch_stress_Pa": [
      0.0,
      0.0
    ],
    "nonlinear_branch_calibration_reviewed": true,
    "initial_branch_state_reviewed": true,
    "computational_use_authorized": true
  },
  "node_ids": [
    "n0",
    "n1"
  ],
  "times_s": [
    0.0,
    3600.0,
    7200.0
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
  "free_closure_without_gasket_m": [
    [
      1e-05,
      8e-06
    ],
    [
      9e-06,
      7e-06
    ],
    [
      7e-06,
      5e-06
    ]
  ],
  "flange_relative_compliance_matrix_m_N": [
    [
      1e-10,
      2e-11
    ],
    [
      2e-11,
      1e-10
    ]
  ],
  "maximum_compressive_strain": 0.15,
  "matrix_symmetry_tolerance_m_N": 1e-12,
  "compliance_psd_tolerance_m_N": 1e-12,
  "maximum_contact_iterations": 10000,
  "maximum_newton_iterations_per_active_set": 100,
  "maximum_contact_work_units": 1000000,
  "gap_tolerance_m": 1e-12,
  "force_tolerance_N": 1e-05,
  "flange_operator_basis_reviewed": true,
  "response_scope_and_coordinates_reviewed": true,
  "bolt_pressure_and_boundary_load_composition_reviewed": true,
  "material_curve_condition_and_support_reviewed": true,
  "initial_branch_states_reviewed": true,
  "zero_compression_branch_state_reviewed": true,
  "nonlinear_history_integration_reviewed": true,
  "unilateral_contact_model_reviewed": true,
  "computational_use_authorized": true,
  "evidence": [
    {
      "source_id": "synthetic-nonlinear-gasket-compliance-fixture",
      "origin": "synthetic",
      "citation": "Project-authored synthetic example; not experimental material data"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/flange_nonlinear_viscoelastic.py#L146)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

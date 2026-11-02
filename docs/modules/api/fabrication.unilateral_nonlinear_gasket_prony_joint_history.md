# `fabrication.unilateral_nonlinear_gasket_prony_joint_history`

**목적:** Caller-authorized nonlinear generalized-Maxwell gasket curves and a nonlinear bolt curve are solved with compression-only contact at each declared time knot.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `request_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material` | 예 | `{"$ref": "#/$defs/NonlinearGasketViscoelasticMaterial"}` | 계약·필드 설명 참조 |
| `compression_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `gasket_compression_height_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `bolt_force_change_curve` | 예 | `{"items": {"$ref": "#/$defs/BoltForceChangePoint"}, "maxItems": 10000, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `bolt_curve_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `bolt_curve_source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `initial_compressive_strain` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_compressive_strain` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 100000, "minItems": 2, "type": "array"}` | s |
| `external_separating_force_N` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 100000, "minItems": 2, "type": "array"}` | N |
| `bolt_free_length_change_m` | 예 | `{"items": {"type": "number"}, "maxItems": 100000, "minItems": 2, "type": "array"}` | m |
| `joint_geometry_and_force_balance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `piecewise_linear_internal_strain_update_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `coupled_history_model_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `bolt_curve_and_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `schema_version` | 아니오 | `{"const": "matintegrity.unilateral_nonlinear_gasket_prony_joint_history.v1", "default": "matintegrity.unilateral_nonlinear_gasket_prony_joint_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `unilateral_contact_transition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `zero_compression_branch_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `between_knot_transition_interpretation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/UnilateralNonlinearGasketJointHistoryRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `response_history.elapsed_time_s` | `s` |
| `response_history.compressive_strain` | `1` |
| `response_history.compressive_displacement_m` | `m` |
| `response_history.branch_stress_Pa` | `Pa` |
| `response_history.gasket_force_N` | `N` |
| `response_history.bolt_force_N` | `N` |
| `response_history.external_separating_force_N` | `N` |
| `response_history.force_balance_residual_N` | `N` |
| `initial_bolt_preload_N` | `N` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-authorized nonlinear generalized-Maxwell gasket curves and a nonlinear bolt curve are solved with compression-only contact at each declared time knot.
- Open/reclose transitions are knotwise; branch state is frozen at zero compression while open. No between-knot event time, flange field, leakage or acceptance is inferred.

## 구현 근거·독립 설명

- `caller_nonlinear_gasket_prony_joint_history`: Represent the gasket equilibrium response and each generalized-Maxwell branch with caller-authorized monotone piecewise-linear stress-strain backbones. Split a linear strain interval at every crossed backbone knot and exactly integrate each first-order branch state over each constant-slope segment; at each declared time knot solve closed-contact equilibrium against a caller-supplied nonlinear bolt force-extension curve and external separating load. Preserve initial branch state, calibration/provider/source digests and force residual. Do not extrapolate, fit or transfer curves, model unilateral contact opening, spatial flange flexibility, leakage or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.unilateral_nonlinear_gasket_prony_joint_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.unilateral_nonlinear_gasket_prony_joint_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "request_id": "synthetic-unilateral-nonlinear-prony-joint-history",
  "joint_id": "synthetic-single-degree-of-freedom-joint",
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
  "compression_area_m2": 0.01,
  "gasket_compression_height_m": 0.01,
  "bolt_force_change_curve": [
    {
      "extension_change_m": -0.005,
      "force_change_N": -500000.0
    },
    {
      "extension_change_m": -0.002,
      "force_change_N": -200000.0
    },
    {
      "extension_change_m": 0.0,
      "force_change_N": 0.0
    },
    {
      "extension_change_m": 0.002,
      "force_change_N": 200000.0
    },
    {
      "extension_change_m": 0.005,
      "force_change_N": 500000.0
    }
  ],
  "bolt_curve_id": "synthetic-linear-shaped-curve-fixture",
  "bolt_curve_source_sha256": "283a1c696fc669d2ec0020bc51eb613e4558c3a100ad0a1327ebae7fa28e73bd",
  "initial_compressive_strain": 0.1,
  "maximum_compressive_strain": 0.15,
  "elapsed_time_s": [
    0.0,
    3600.0,
    7200.0
  ],
  "external_separating_force_N": [
    10000.0,
    12000.0,
    14000.0
  ],
  "bolt_free_length_change_m": [
    0.0,
    0.0,
    0.0
  ],
  "joint_geometry_and_force_balance_reviewed": true,
  "piecewise_linear_internal_strain_update_reviewed": true,
  "coupled_history_model_applicability_reviewed": true,
  "bolt_curve_and_support_reviewed": true,
  "unilateral_contact_transition_reviewed": true,
  "zero_compression_branch_state_reviewed": true,
  "between_knot_transition_interpretation_reviewed": true,
  "schema_version": "matintegrity.unilateral_nonlinear_gasket_prony_joint_history.v1"
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/assembly_numeric.py#L132)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

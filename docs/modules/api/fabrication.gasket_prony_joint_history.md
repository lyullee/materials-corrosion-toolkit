# `fabrication.gasket_prony_joint_history`

**목적:** Caller-authorized Prony gasket history is coupled to a linear bolt and quasi-static force equilibrium at each declared time knot.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `request_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material` | 예 | `{"$ref": "#/$defs/GasketViscoelasticMaterial"}` | 계약·필드 설명 참조 |
| `compression_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `gasket_compression_height_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `bolt_stiffness_N_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | N·m |
| `initial_compressive_strain` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_compressive_strain` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | s |
| `external_separating_force_N` | 예 | `{"items": {"minimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | N |
| `bolt_free_length_change_m` | 예 | `{"items": {"type": "number"}, "minItems": 2, "type": "array"}` | m |
| `joint_geometry_and_force_balance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `piecewise_linear_internal_strain_update_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `coupled_history_model_applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GasketViscoelasticJointHistoryRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `response_history.elapsed_time_s` | `s` |
| `response_history.compressive_strain` | `1` |
| `response_history.compressive_displacement_m` | `m` |
| `response_history.branch_stress_Pa` | `Pa` |
| `response_history.gasket_stress_Pa` | `Pa` |
| `response_history.gasket_force_N` | `N` |
| `response_history.bolt_force_N` | `N` |
| `response_history.external_separating_force_N` | `N` |
| `response_history.bolt_free_length_change_m` | `m` |
| `response_history.bolt_extension_change_m` | `m` |
| `response_history.force_balance_residual_N` | `N` |
| `initial_bolt_preload_N` | `N` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-authorized Prony gasket history is coupled to a linear bolt and quasi-static force equilibrium at each declared time knot.
- Only closed contact, piecewise-linear interval strain evolution and a uniform single-degree-of-freedom joint are represented; flange field, leakage and acceptance are outside scope.

## 구현 근거·독립 설명

- `caller_coupled_prony_bolt_gasket_history`: At each supplied time knot, update caller-authorized generalized-Maxwell branch stresses for a piecewise-linear gasket compression-strain segment and solve the affine force balance against a linear elastic bolt, caller external separating load and bolt free-length change. Preserve material/provider/source identity, initial branch state, input digest and force residual. Restrict the result to reviewed closed contact and declared strain support; do not fit or transfer Prony coefficients, model contact opening, spatial flange flexibility, leakage or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.gasket_prony_joint_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.gasket_prony_joint_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "request_id": "synthetic-prony-joint-history",
  "joint_id": "synthetic-uniform-joint-a",
  "material": {
    "material_condition_id": "synthetic-gasket-condition-a",
    "physical_specimen_id": "synthetic-gasket-specimen-a",
    "source_group_id": "synthetic-gasket-study-a",
    "condition_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "source_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "provider_id": "project-synthetic-prony-fit",
    "provider_revision": "1",
    "temperature_K": 298.15,
    "equilibrium_modulus_Pa": 10000000.0,
    "prony_branches": [
      {
        "branch_id": "branch-fast",
        "modulus_Pa": 20000000.0,
        "relaxation_time_s": 100.0
      },
      {
        "branch_id": "branch-slow",
        "modulus_Pa": 10000000.0,
        "relaxation_time_s": 1000.0
      }
    ],
    "initial_branch_stress_Pa": [
      0.0,
      0.0
    ],
    "initial_branch_state_reviewed": true,
    "calibration_basis_reviewed": true,
    "computational_use_authorized": true
  },
  "compression_area_m2": 0.01,
  "gasket_compression_height_m": 0.01,
  "bolt_stiffness_N_m": 10000000.0,
  "initial_compressive_strain": 0.01,
  "maximum_compressive_strain": 0.03,
  "elapsed_time_s": [
    0.0,
    100.0,
    1000.0
  ],
  "external_separating_force_N": [
    0.0,
    100.0,
    200.0
  ],
  "bolt_free_length_change_m": [
    0.0,
    0.0,
    1e-05
  ],
  "joint_geometry_and_force_balance_reviewed": true,
  "piecewise_linear_internal_strain_update_reviewed": true,
  "coupled_history_model_applicability_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/assembly_numeric.py#L83)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

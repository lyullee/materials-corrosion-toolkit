# `fatigue.critical_plane_continuous_bound`

**목적:** The caller supplies one reviewed closed local tensor cycle, calibrated Fatemi-Socie coefficient and normalization stress, plus explicit orientation and work budgets.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tensor_source_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tensor_history_record_digest` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `sample_ids` | 예 | `{"items": {"type": "string"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `stress_tensor_components_Pa` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "minItems": 3, "type": "array"}` | Pa |
| `strain_tensor_components` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `representative_cycle_declared` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_stress_closure_error_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `maximum_strain_closure_error` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `fatemi_socie_coefficient` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `normalization_stress_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa |
| `maximum_refinement_level` | 아니오 | `{"default": 4, "maximum": 5, "minimum": 0, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_candidate_evaluations` | 아니오 | `{"default": 15000, "maximum": 20000, "minimum": 12, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_sample_pair_plane_work` | 아니오 | `{"default": 30000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `fatemi_socie_bound_gap_tolerance` | 아니오 | `{"default": 0.0, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `swt_bound_gap_tolerance_Pa` | 아니오 | `{"default": 0.0, "minimum": 0, "type": "number"}` | Pa |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CriticalPlaneContinuousBound.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `sampled_maximum_fatemi_socie_factor` | `1` |
| `fatemi_socie_continuous_upper_bound` | `1` |
| `fatemi_socie_bound_gap` | `1` |
| `sampled_maximum_swt_factor_Pa` | `Pa` |
| `swt_continuous_upper_bound_Pa` | `Pa` |
| `swt_bound_gap_Pa` | `Pa` |
| `evaluated_candidate_count` | `1` |
| `maximum_refinement_level` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The caller supplies one reviewed closed local tensor cycle, calibrated Fatemi-Socie coefficient and normalization stress, plus explicit orientation and work budgets.
- A fully evaluated icosphere vertex net and tensor-norm Lipschitz constants yield conservative continuous-plane upper bounds for the implemented FS and SWT sampled-cycle factors.
- The bound covers orientation over the supplied discrete cycle only; it does not bound time interpolation, arbitrary cycle counting, calibration, local fields, physical-model error or acceptance.

## 구현 근거·독립 설명

- `critical_plane_continuous_lipschitz_bound`: Construct deterministic successively refined icosphere vertex nets on the unit sphere, identify antipodal normals for unoriented planes, and bound the uncovered angular distance by the maximum spherical face-edge angle. Combine that coverage bound with tensor-Frobenius Lipschitz constants for the implemented maximum-pairwise engineering-shear-chord Fatemi-Socie and SWT sampled-cycle factors. Report lower sampled maxima and conservative continuous-orientation upper bounds; the guarantee excludes unsampled time, cycle-counting, calibration and physical-model errors.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.critical_plane_continuous_bound"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.critical_plane_continuous_bound"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "synthetic-continuous-plane-bound",
  "material_condition_id": "synthetic-condition",
  "location_id": "reviewed-integration-point",
  "tensor_source_id": "synthetic-closed-form",
  "tensor_history_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
  "sample_ids": [
    "s0",
    "s1",
    "s2",
    "s3",
    "s4"
  ],
  "stress_tensor_components_Pa": [
    [
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0
    ],
    [
      100000000.0,
      0.0,
      0.0,
      20000000.0,
      0.0,
      0.0
    ],
    [
      0.0,
      100000000.0,
      0.0,
      0.0,
      10000000.0,
      0.0
    ],
    [
      -100000000.0,
      0.0,
      0.0,
      -20000000.0,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0
    ]
  ],
  "strain_tensor_components": [
    [
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0
    ],
    [
      0.001,
      0.0,
      0.0,
      0.0002,
      0.0,
      0.0
    ],
    [
      0.0,
      0.001,
      0.0,
      0.0,
      0.0001,
      0.0
    ],
    [
      -0.001,
      0.0,
      0.0,
      -0.0002,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      0.0,
      0.0,
      0.0,
      0.0
    ]
  ],
  "representative_cycle_declared": true,
  "maximum_stress_closure_error_Pa": 0.0,
  "maximum_strain_closure_error": 0.0,
  "fatemi_socie_coefficient": 0.3,
  "normalization_stress_Pa": 400000000.0,
  "maximum_refinement_level": 2,
  "maximum_candidate_evaluations": 200,
  "maximum_sample_pair_plane_work": 10000,
  "fatemi_socie_bound_gap_tolerance": 0.05,
  "swt_bound_gap_tolerance_Pa": 1000000.0
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fatigue.py#L1649)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

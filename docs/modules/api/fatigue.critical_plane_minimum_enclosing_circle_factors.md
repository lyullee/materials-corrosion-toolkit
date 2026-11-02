# `fatigue.critical_plane_minimum_enclosing_circle_factors`

**목적:** The caller supplies a reviewed closed local tensor cycle, tensor-shear components, finite orthonormal plane frames and qualified FS parameters.

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
| `load_case_id` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `tensor_provider_id` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `tensor_provider_version` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `solver_name` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `solver_version` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `analysis_id` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `solution_revision` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `mesh_id` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `field_location_kind` | 아니오 | `{"anyOf": [{"enum": ["node", "integration_point", "surface_point", "user_defined"], "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `field_location_id` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `spatial_averaging` | 아니오 | `{"anyOf": [{"enum": ["none", "nodal_averaged", "element_averaged", "other"], "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `coordinate_frame_id` | 아니오 | `{"anyOf": [{"minLength": 1, "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `coordinate_basis_vectors_global` | 아니오 | `{"anyOf": [{"items": {"items": {"type": "number"}, "type": "array"}, "type": "array"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `stress_measure` | 아니오 | `{"anyOf": [{"const": "cauchy", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `strain_measure` | 아니오 | `{"anyOf": [{"const": "infinitesimal", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `input_strain_shear_convention` | 아니오 | `{"anyOf": [{"enum": ["tensor", "engineering"], "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `source_content_sha256` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `provider_configuration_digest` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `tensor_history_record_digest` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `sample_ids` | 예 | `{"items": {"type": "string"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `sample_times_s` | 아니오 | `{"anyOf": [{"items": {"minimum": 0, "type": "number"}, "type": "array"}, {"type": "null"}], "default": null}` | s |
| `stress_tensor_components_Pa` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "minItems": 3, "type": "array"}` | Pa |
| `strain_tensor_components` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_planes` | 예 | `{"items": {"$ref": "#/$defs/CriticalPlaneCandidate"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `representative_cycle_declared` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_stress_closure_error_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `maximum_strain_closure_error` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `fatemi_socie_coefficient` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `normalization_stress_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CriticalPlaneHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `sample_count` | `1` |
| `candidate_count` | `1` |
| `stress_closure_error_Pa` | `Pa` |
| `strain_closure_error` | `1` |
| `maximum_fatemi_socie_factor` | `1` |
| `maximum_swt_factor_Pa` | `Pa` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The caller supplies a reviewed closed local tensor cycle, tensor-shear components, finite orthonormal plane frames and qualified FS parameters.
- For each plane, the sampled two-component engineering-shear path amplitude is the radius of its deterministic minimum enclosing circle; up to three support-sample identities and the half-maximum-chord comparison remain explicit.
- This finite point-set range ignores path order after closure review and does not qualify an unsampled continuous path, cycle counting, a continuous orientation optimum, fatigue life, acceptance or experiment agreement.

## 구현 근거·독립 설명

- [Fatemi and Socie, critical-plane fatigue approach including out-of-phase loading](https://doi.org/10.1111/j.1460-2695.1988.tb01169.x) · `fatemi_socie_1988`
- [Smith, Watson and Topper, stress-strain fatigue function with mean-stress effect](https://www.researchgate.net/publication/309476268_A_stress-strain_function_for_the_fatigue_of_metals_stress-strain_function_for_metal_fatigue_including_mean_stress_effect) · `smith_watson_topper_1970`
- `critical_plane_minimum_enclosing_circle_projection`: For each caller-declared orthonormal plane frame, project the sampled symmetric tensor history into two in-plane shear components. Construct a deterministic finite-point minimum enclosing circle from one-point, diameter and three-point circumcircle supports, retaining up to three support sample identities and center components in the supplied frame. Use its radius as the sampled engineering-shear amplitude and report half the maximum sampled pairwise chord separately. Radius is invariant to in-plane rigid coordinate changes, but this order-insensitive finite point-set range does not bound an unsampled path, count cycles, prove orientation convergence or qualify fatigue life.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.critical_plane_minimum_enclosing_circle_factors"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.critical_plane_minimum_enclosing_circle_factors"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "synthetic-equilateral-shear-cycle",
  "material_condition_id": "synthetic-condition",
  "location_id": "reviewed-integration-point",
  "tensor_source_id": "synthetic-closed-form",
  "sample_ids": [
    "v0",
    "v1",
    "v2",
    "v0-close"
  ],
  "stress_tensor_components_Pa": [
    [
      0.0,
      0.0,
      0.0,
      40000000.0,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      0.0,
      -20000000.0,
      0.0,
      34641016.151377544
    ],
    [
      0.0,
      0.0,
      0.0,
      -20000000.0,
      0.0,
      -34641016.151377544
    ],
    [
      0.0,
      0.0,
      0.0,
      40000000.0,
      0.0,
      0.0
    ]
  ],
  "strain_tensor_components": [
    [
      0.0,
      0.0,
      0.0,
      0.001,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      0.0,
      -0.0005,
      0.0,
      0.0008660254037844386
    ],
    [
      0.0,
      0.0,
      0.0,
      -0.0005,
      0.0,
      -0.0008660254037844386
    ],
    [
      0.0,
      0.0,
      0.0,
      0.001,
      0.0,
      0.0
    ]
  ],
  "candidate_planes": [
    {
      "plane_id": "normal-x",
      "normal": [
        1.0,
        0.0,
        0.0
      ],
      "in_plane_direction": [
        0.0,
        1.0,
        0.0
      ]
    }
  ],
  "representative_cycle_declared": true,
  "maximum_stress_closure_error_Pa": 0.0,
  "maximum_strain_closure_error": 0.0,
  "fatemi_socie_coefficient": 0.3,
  "normalization_stress_Pa": 400000000.0
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fatigue.py#L783)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

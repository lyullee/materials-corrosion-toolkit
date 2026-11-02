# `fatigue.critical_plane_time_refinement`

**목적:** The caller supplies one reviewed cycle at two or more strictly increasing nested time samplings, a fixed finite plane set and explicit time-match and diagnostic tolerances.

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
| `candidate_planes` | 예 | `{"items": {"$ref": "#/$defs/CriticalPlaneCandidate"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `sampling_levels` | 예 | `{"items": {"$ref": "#/$defs/CriticalPlaneTimeSampling"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `representative_cycle_declared` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_stress_closure_error_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `maximum_strain_closure_error` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_nested_time_match_error_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `fatemi_socie_coefficient` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `normalization_stress_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa |
| `declared_maximum_relative_factor_change` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `declared_maximum_plane_rotation_rad` | 예 | `{"maximum": 1.5707963267948966, "minimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CriticalPlaneTimeRefinement.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `candidate_count` | `1` |
| `refinement_level_count` | `1` |
| `evaluated_level_count` | `1` |
| `declared_maximum_relative_factor_change` | `1` |
| `declared_maximum_plane_rotation_rad` | `rad` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The caller supplies one reviewed cycle at two or more strictly increasing nested time samplings, a fixed finite plane set and explicit time-match and diagnostic tolerances.
- Every level uses the sampled maximum-pairwise shear-vector chord. Factor and selected-plane changes isolate temporal sampling only within the fixed candidate set.
- Meeting a declared diagnostic tolerance does not bound extrema between samples or prove continuous-time/orientation convergence, fatigue-life calibration, acceptance or experimental validity.

## 구현 근거·독립 설명

- `critical_plane_vector_chord_projection`: For each caller-declared orthonormal plane frame, independently project the symmetric tensor path onto two in-plane shear directions. Form the exact maximum pairwise Euclidean chord of the sampled engineering-shear vectors and use half that named chord as a discrete amplitude. The Euclidean result is invariant to rotation or reversal of the supplied in-plane basis. Preserve chord endpoint sample identities and distinguish this O(n squared) sampled-path definition from continuous-time extrema, a minimum enclosing circle, rainflow extraction, continuous plane optimization, fatigue-life calibration and acceptance.
- `critical_plane_time_refinement_diagnostic`: Hold one finite plane set fixed while evaluating explicitly ordered, strictly increasing and time-nested samplings of the same reviewed tensor cycle. Record each sampling interval, discrete FS/SWT maxima, selected unoriented normals and successive relative-factor and acute-plane-angle changes. Nested sampled histories and satisfied caller tolerances do not bound extrema between samples, prove temporal or orientation convergence, qualify fatigue life or establish experimental validity.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.critical_plane_time_refinement"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.critical_plane_time_refinement"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "synthetic-time-refinement-cycle",
  "material_condition_id": "synthetic-condition",
  "location_id": "reviewed-integration-point",
  "tensor_source_id": "synthetic-closed-form",
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
    },
    {
      "plane_id": "xy-45",
      "normal": [
        0.7071067811865476,
        0.7071067811865476,
        0.0
      ],
      "in_plane_direction": [
        -0.7071067811865476,
        0.7071067811865476,
        0.0
      ]
    }
  ],
  "sampling_levels": [
    {
      "sampling_id": "coarse",
      "sample_ids": [
        "c0",
        "c1",
        "c2",
        "c3",
        "c4"
      ],
      "sample_times_s": [
        0.0,
        0.25,
        0.5,
        0.75,
        1.0
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
          0.0,
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
        ],
        [
          -100000000.0,
          0.0,
          0.0,
          0.0,
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
          0.0005,
          0.0,
          0.0,
          0.0,
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
        ],
        [
          -0.0005,
          0.0,
          0.0,
          0.0,
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
      ]
    },
    {
      "sampling_id": "fine",
      "sample_ids": [
        "f0",
        "f1",
        "f2",
        "f3",
        "f4",
        "f5",
        "f6",
        "f7",
        "f8"
      ],
      "sample_times_s": [
        0.0,
        0.125,
        0.25,
        0.375,
        0.5,
        0.625,
        0.75,
        0.875,
        1.0
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
          70710678.11865476,
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
          0.0,
          0.0,
          0.0
        ],
        [
          70710678.11865476,
          0.0,
          0.0,
          0.0,
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
        ],
        [
          -70710678.11865476,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          -100000000.0,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          -70710678.11865476,
          0.0,
          0.0,
          0.0,
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
          0.0003535533905932738,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0005,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          0.0003535533905932738,
          0.0,
          0.0,
          0.0,
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
        ],
        [
          -0.0003535533905932738,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          -0.0005,
          0.0,
          0.0,
          0.0,
          0.0,
          0.0
        ],
        [
          -0.0003535533905932738,
          0.0,
          0.0,
          0.0,
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
      ]
    }
  ],
  "representative_cycle_declared": true,
  "maximum_stress_closure_error_Pa": 0.0,
  "maximum_strain_closure_error": 0.0,
  "maximum_nested_time_match_error_s": 0.0,
  "fatemi_socie_coefficient": 0.3,
  "normalization_stress_Pa": 400000000.0,
  "declared_maximum_relative_factor_change": 0.01,
  "declared_maximum_plane_rotation_rad": 0.0
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fatigue.py#L1908)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

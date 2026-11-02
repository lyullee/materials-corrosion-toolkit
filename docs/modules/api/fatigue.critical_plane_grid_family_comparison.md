# `fatigue.critical_plane_grid_family_comparison`

**목적:** The caller supplies one reviewed closed local tensor cycle, at least two uniquely identified latitude-azimuth and/or area-stratified Fibonacci grids, an explicit finite reference grid and diagnostic tolerances.

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
| `sample_ids` | 예 | `{"items": {"type": "string"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `stress_tensor_components_Pa` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "minItems": 3, "type": "array"}` | Pa |
| `strain_tensor_components` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `grid_definitions` | 예 | `{"items": {"anyOf": [{"$ref": "#/$defs/HemispherePlaneGrid"}, {"$ref": "#/$defs/AreaUniformFibonacciPlaneGrid"}]}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `reference_grid_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `representative_cycle_declared` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_stress_closure_error_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `maximum_strain_closure_error` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `fatemi_socie_coefficient` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `normalization_stress_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa |
| `declared_maximum_relative_factor_change` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `declared_maximum_plane_rotation_rad` | 예 | `{"maximum": 1.5707963267948966, "minimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CriticalPlaneGridFamilyComparison.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `grid_count` | `1` |
| `evaluated_grid_count` | `1` |
| `declared_maximum_relative_factor_change` | `1` |
| `declared_maximum_plane_rotation_rad` | `rad` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The caller supplies one reviewed closed local tensor cycle, at least two uniquely identified latitude-azimuth and/or area-stratified Fibonacci grids, an explicit finite reference grid and diagnostic tolerances.
- All grids use the same sampled maximum-pairwise shear-vector chord; candidate family, count and Fibonacci phase are compared without changing the tensor history.
- Agreement with the declared finite reference does not prove an orientation-error bound, continuous-plane/time convergence, fatigue-life calibration, acceptance or experimental validity.

## 구현 근거·독립 설명

- `hemisphere_plane_grid_derivation`: Represent each unoriented material plane once by a unit normal on the closed upper hemisphere. Sample polar latitude uniformly from the pole through the equator and azimuth uniformly around intermediate latitudes; retain one pole and half the equatorial azimuths to remove exact n versus minus-n duplicates. Construct a deterministic in-plane unit direction from the least-aligned Cartesian axis. This finite latitude-azimuth grid is not equal-area and its nominal angular increments are not a coverage-error bound, convergence proof or continuous optimum.
- `area_uniform_fibonacci_plane_grid_derivation`: Represent each unoriented plane once with a normal strictly inside the positive-z hemisphere. Partition the hemisphere into equal increments of z, place one normal at each stratum midpoint, and advance its azimuth by the golden angle with a caller-controlled phase. Assign the hemisphere area divided by point count only as a nominal quadrature weight. This deterministic area-stratified sequence is not an exact equal-area Voronoi tessellation, a nested refinement, a covering-radius bound or a continuous orientation optimum.
- `critical_plane_vector_chord_projection`: For each caller-declared orthonormal plane frame, independently project the symmetric tensor path onto two in-plane shear directions. Form the exact maximum pairwise Euclidean chord of the sampled engineering-shear vectors and use half that named chord as a discrete amplitude. The Euclidean result is invariant to rotation or reversal of the supplied in-plane basis. Preserve chord endpoint sample identities and distinguish this O(n squared) sampled-path definition from continuous-time extrema, a minimum enclosing circle, rainflow extraction, continuous plane optimization, fatigue-life calibration and acceptance.
- `critical_plane_grid_family_comparison_diagnostic`: Evaluate one reviewed sampled tensor cycle with at least two uniquely identified finite latitude-azimuth and/or area-stratified Fibonacci candidate sets. Preserve each generator definition, sampled FS/SWT maxima and selected normals. Relative to one caller-named finite reference grid, report normalized factor differences and acute angles between unoriented selected normals. Cross-grid agreement is not an orientation-error bound, continuous optimum, temporal convergence, fatigue-life calibration or experimental validation.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.critical_plane_grid_family_comparison"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.critical_plane_grid_family_comparison"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "synthetic-grid-family-cycle",
  "material_condition_id": "synthetic-condition",
  "location_id": "reviewed-integration-point",
  "tensor_source_id": "synthetic-closed-form",
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
  ],
  "grid_definitions": [
    {
      "grid_id": "latitude-reference",
      "polar_divisions": 4,
      "azimuthal_divisions": 16
    },
    {
      "grid_id": "fibonacci-phase-0",
      "candidate_count": 64,
      "azimuth_phase_rad": 0.0
    },
    {
      "grid_id": "fibonacci-phase-031",
      "candidate_count": 64,
      "azimuth_phase_rad": 0.31
    }
  ],
  "reference_grid_id": "latitude-reference",
  "representative_cycle_declared": true,
  "maximum_stress_closure_error_Pa": 0.0,
  "maximum_strain_closure_error": 0.0,
  "fatemi_socie_coefficient": 0.3,
  "normalization_stress_Pa": 400000000.0,
  "declared_maximum_relative_factor_change": 0.05,
  "declared_maximum_plane_rotation_rad": 0.17453292519943295
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fatigue.py#L1246)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

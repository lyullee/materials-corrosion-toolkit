# `fatigue.critical_plane_piecewise_linear_time_history`

**목적:** The caller supplies one timed, reviewed closed tensor cycle and explicitly declares piecewise-linear interpolation of the tensor components.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history` | 예 | `{"$ref": "#/$defs/CriticalPlaneHistory"}` | 계약·필드 설명 참조 |
| `shear_range_method` | 아니오 | `{"default": "maximum_pairwise_euclidean_chord", "enum": ["maximum_pairwise_euclidean_chord", "minimum_enclosing_circle_radius"], "type": "string"}` | 계약·필드 설명 참조 |
| `piecewise_linear_tensor_interpolation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `interpolation_scope_and_time_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_sample_plane_work` | 아니오 | `{"default": 5000000, "maximum": 50000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CriticalPlanePiecewiseLinearTimeHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `cycle_start_s` | `s` |
| `cycle_end_s` | `s` |
| `minimum_time_step_s` | `s` |
| `maximum_time_step_s` | `s` |
| `segment_tensor_frobenius_rates.tensor_stress_frobenius_rate_Pa_s` | `Pa/s` |
| `segment_tensor_frobenius_rates.tensor_strain_frobenius_rate_s_inverse` | `1/s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The caller supplies one timed, reviewed closed tensor cycle and explicitly declares piecewise-linear interpolation of the tensor components.
- For the selected finite plane set and chord or enclosing-circle definitions, extrema of the reconstructed path are exactly represented by the sample vertices; this is conditional on the declared interpolation.
- The model does not infer physical behavior between measurements, continuous-plane optima, multiaxial cycle pairing, damage accumulation, fatigue life or experimental validity.

## 구현 근거·독립 설명

- `critical_plane_piecewise_linear_time_extrema`: Reconstruct symmetric stress and infinitesimal-strain tensor components linearly between caller-timed samples of one reviewed closed cycle. For the declared finite planes, normal scalar extrema occur at segment vertices; each in-plane shear-vector segment lies inside the convex hull of its endpoints, so vertex-based maximum chord and minimum-enclosing-circle radii are exact for this reconstructed path. This establishes interpolation-conditional FS/SWT factor extrema, not fidelity to unknown physical behavior, continuous-plane search, multiaxial rainflow pairing, variable-amplitude damage, life or material validation.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.critical_plane_piecewise_linear_time_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.critical_plane_piecewise_linear_time_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history": {
    "history_id": "synthetic-linear-time-cycle",
    "material_condition_id": "synthetic-condition",
    "location_id": "synthetic-integration-point",
    "tensor_source_id": "authored-linear-interpolation",
    "sample_ids": [
      "t0",
      "t1",
      "t2"
    ],
    "sample_times_s": [
      0.0,
      0.5,
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
        25000000.0,
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
        0.0001,
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
  },
  "shear_range_method": "maximum_pairwise_euclidean_chord",
  "piecewise_linear_tensor_interpolation_reviewed": true,
  "interpolation_scope_and_time_units_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fatigue.py#L2050)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

# `fatigue.critical_plane_projected_rainflow`

**목적:** The caller supplies ordered multiaxial stress/strain tensors, finite plane frames, explicit scalar projection choices, path boundary, tensor basis and interpretation reviews.

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
| `sample_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 50000, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `sample_times_s` | 아니오 | `{"anyOf": [{"items": {"minimum": 0, "type": "number"}, "type": "array"}, {"type": "null"}], "default": null}` | s |
| `stress_tensor_components_Pa` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 50000, "minItems": 3, "type": "array"}` | Pa |
| `strain_tensor_components` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 50000, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `input_strain_shear_convention` | 예 | `{"enum": ["tensor", "engineering"], "type": "string"}` | 계약·필드 설명 참조 |
| `candidate_planes` | 예 | `{"items": {"$ref": "#/$defs/CriticalPlaneCandidate"}, "maxItems": 1000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `projections` | 예 | `{"items": {"enum": ["normal_stress", "normal_strain", "shear_stress_directional_component", "engineering_shear_strain_directional_component", "shear_stress_vector_magnitude", "engineering_shear_strain_vector_magnitude"], "type": "string"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `tensor_basis_and_order_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `path_boundary_and_sample_order_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `projection_method_and_use_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_projection_sample_work` | 아니오 | `{"default": 5000000, "maximum": 50000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CriticalPlaneProjectedRainflow.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `projection_cycle_results.projections.cycle_count_equivalents` | `cycle` |
| `projection_cycle_results.projections.cycles.range` | `input_quantity_unit` |
| `projection_cycle_results.projections.cycles.mean` | `input_quantity_unit` |
| `projection_cycle_results.projections.cycles.count` | `cycle` |
| `projection_cycle_results.projections.cycles.start_time_s` | `s` |
| `projection_cycle_results.projections.cycles.end_time_s` | `s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The caller supplies ordered multiaxial stress/strain tensors, finite plane frames, explicit scalar projection choices, path boundary, tensor basis and interpretation reviews.
- Rainflow is applied independently to each declared scalar projection; residual excursions remain half cycles and cycle endpoints retain caller sample identities.
- No cross-projection pairing, multiaxial damage parameter, life, closure correction, continuous-plane search, acceptance or probability is inferred.

## 구현 근거·독립 설명

- `critical_plane_projected_rainflow_decomposition`: Project each caller-selected finite material plane into explicitly selected scalar normal-stress, normal-strain, signed in-plane shear-component or nonnegative shear-vector-magnitude histories. Apply the documented scalar rainflow library independently to each series, preserve residual half cycles and original sample/time identities, and return channels separately. Do not infer cross-channel cycle pairing, phase relation, multiaxial damage, life or acceptance.
- [rainflow upstream Python package](https://github.com/iamlikeme/rainflow) · `rainflow_library`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.critical_plane_projected_rainflow"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.critical_plane_projected_rainflow"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "synthetic-projected-rainflow-path",
  "material_condition_id": "synthetic-condition",
  "location_id": "reviewed-integration-point",
  "tensor_source_id": "synthetic-ordered-tensor-path",
  "tensor_history_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
  "sample_ids": [
    "s0",
    "s1",
    "s2",
    "s3",
    "s4",
    "s5",
    "s6"
  ],
  "sample_times_s": [
    0.0,
    1.0,
    2.0,
    3.0,
    4.0,
    5.0,
    6.0
  ],
  "stress_tensor_components_Pa": [
    [
      0.0,
      0.0,
      10000000.0,
      0.0,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      50000000.0,
      10000000.0,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      -20000000.0,
      30000000.0,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      40000000.0,
      -20000000.0,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      -10000000.0,
      10000000.0,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      30000000.0,
      -10000000.0,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      10000000.0,
      0.0,
      0.0,
      0.0
    ]
  ],
  "strain_tensor_components": [
    [
      0.0,
      0.0,
      0.0001,
      0.0,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      0.0005,
      0.0001,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      -0.0002,
      0.0003,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      0.0004,
      -0.0002,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      -0.0001,
      0.0001,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      0.0003,
      -0.0001,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      0.0001,
      0.0,
      0.0,
      0.0
    ]
  ],
  "input_strain_shear_convention": "tensor",
  "candidate_planes": [
    {
      "plane_id": "synthetic-z-plane",
      "normal": [
        0.0,
        0.0,
        1.0
      ],
      "in_plane_direction": [
        1.0,
        0.0,
        0.0
      ]
    }
  ],
  "projections": [
    "normal_stress",
    "normal_strain",
    "shear_stress_directional_component",
    "engineering_shear_strain_directional_component",
    "shear_stress_vector_magnitude",
    "engineering_shear_strain_vector_magnitude"
  ],
  "tensor_basis_and_order_reviewed": true,
  "path_boundary_and_sample_order_reviewed": true,
  "projection_method_and_use_reviewed": true,
  "maximum_projection_sample_work": 10000
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fatigue.py#L2324)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

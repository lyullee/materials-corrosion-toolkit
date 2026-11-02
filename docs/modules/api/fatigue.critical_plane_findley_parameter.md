# `fatigue.critical_plane_findley_parameter`

**목적:** Uses the Findley critical-plane stress parameter with caller-supplied coefficient and reference strength; no coefficient, strength curve or cycle life is inferred.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `load_case_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `cycle_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tensor_source_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tensor_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tensor_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tensor_record_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `tensor_content_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `coordinate_frame_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `stress_measure` | 예 | `{"const": "cauchy", "type": "string"}` | 계약·필드 설명 참조 |
| `component_order` | 예 | `{"const": "xx,yy,zz,xy,yz,zx", "type": "string"}` | 계약·필드 설명 참조 |
| `sample_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 20000, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `sample_times_s` | 아니오 | `{"anyOf": [{"items": {"minimum": 0, "type": "number"}, "type": "array"}, {"type": "null"}], "default": null}` | s |
| `stress_tensor_components_Pa` | 예 | `{"items": {"maxItems": 6, "minItems": 6, "prefixItems": [{"type": "number"}, {"type": "number"}, {"type": "number"}, {"type": "number"}, {"type": "number"}, {"type": "number"}], "type": "array"}, "maxItems": 20000, "minItems": 3, "type": "array"}` | Pa |
| `candidate_planes` | 예 | `{"items": {"$ref": "#/$defs/CriticalPlaneCandidate"}, "maxItems": 20000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `representative_cycle_declared` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_stress_closure_error_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `findley_coefficient` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `reference_parameter_strength_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa |
| `reference_life_cycles` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `calibration_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_record_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `usage_rights_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_shear_pair_evaluations` | 아니오 | `{"default": 50000000, "maximum": 2000000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `tensor_units_and_component_order_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `candidate_plane_set_and_coverage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `cycle_definition_and_closure_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `findley_coefficient_and_calibration_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_same_material_and_reference_life_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `usage_rights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CriticalPlaneFindleyStressHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `stress_cycle_closure_error_Pa` | `Pa` |
| `stress_tensor_components_Pa[][]` | `Pa` |
| `candidate_plane_results[].maximum_pairwise_shear_chord_Pa` | `Pa` |
| `candidate_plane_results[].shear_stress_amplitude_Pa` | `Pa` |
| `candidate_plane_results[].maximum_normal_stress_Pa` | `Pa` |
| `candidate_plane_results[].findley_parameter_Pa` | `Pa` |
| `maximum_findley_parameter_Pa` | `Pa` |
| `reference_parameter_strength_Pa` | `Pa` |
| `reference_life_cycles` | `cycle` |
| `candidate_plane_results[].parameter_to_reference_strength_ratio` | `1` |
| `reference_strength_utilization_ratio` | `1` |
| `margin_to_reference_strength_Pa` | `Pa` |
| `candidate_plane_results[].margin_to_reference_strength_Pa` | `Pa` |
| `evaluated_shear_pair_count` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Uses the Findley critical-plane stress parameter with caller-supplied coefficient and reference strength; no coefficient, strength curve or cycle life is inferred.
- The sampled shear amplitude is one half of the maximum pairwise chord in the two-component in-plane shear-traction path and is evaluated only on caller-supplied planes.
- A computed value is a deterministic model output, not a code acceptance decision, life prediction, failure probability or material qualification.

## 구현 근거·독립 설명

- [W. N. Findley, A Theory for the Effect of Mean Stress on Fatigue of Metals Under Combined Torsion and Axial Load or Bending (1959)](https://doi.org/10.1115/1.4008327) · `findley_1959_mean_stress_critical_plane`
- `caller_findley_reference_strength_calibration`: Evaluate the finite-sample critical-plane parameter as the sampled shear-traction amplitude plus a caller-calibrated coefficient times the maximum sampled normal stress. The amplitude is explicitly one half of the maximum pairwise chord among supplied two-component in-plane shear tractions. Evaluate only caller-supplied plane orientations and compare against a caller-supplied parameter strength at one stated reference life. This deterministic screening calculation does not infer fatigue life, acceptance criteria, probability, material qualification, unsampled times or unsupplied plane orientations.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.critical_plane_findley_parameter"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.critical_plane_findley_parameter"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-findley-screen",
  "asset_id": "synthetic-fatigue-coupon",
  "location_id": "synthetic-gauge-section",
  "time_basis_id": "synthetic-cycle-time",
  "material_condition_id": "synthetic-steel-condition",
  "load_case_id": "synthetic-axial-cycle",
  "cycle_id": "synthetic-cycle-001",
  "tensor_source_id": "synthetic-stress-history",
  "tensor_provider_id": "synthetic-tensor-provider",
  "tensor_provider_revision": "1",
  "tensor_record_id": "stress-cycle-001",
  "tensor_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "coordinate_frame_id": "coupon-global-xyz",
  "stress_measure": "cauchy",
  "component_order": "xx,yy,zz,xy,yz,zx",
  "sample_ids": [
    "cycle-start",
    "peak-tension",
    "cycle-end"
  ],
  "sample_times_s": [
    0.0,
    0.5,
    1.0
  ],
  "stress_tensor_components_Pa": [
    [
      0,
      0,
      0,
      0,
      0,
      0
    ],
    [
      100000000,
      0,
      0,
      0,
      0,
      0
    ],
    [
      0,
      0,
      0,
      0,
      0,
      0
    ]
  ],
  "candidate_planes": [
    {
      "plane_id": "synthetic-45deg-plane",
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
  "representative_cycle_declared": true,
  "maximum_stress_closure_error_Pa": 1.0,
  "findley_coefficient": 0.25,
  "reference_parameter_strength_Pa": 50000000.0,
  "reference_life_cycles": 100000.0,
  "calibration_provider_id": "synthetic-findley-calibration-provider",
  "calibration_provider_revision": "1",
  "calibration_record_id": "synthetic-coefficient-strength-point",
  "calibration_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "evidence": [
    {
      "source_id": "synthetic-tensor-provider",
      "origin": "synthetic",
      "citation": "Project-authored synthetic stress history for API wiring only; not measured or validated.",
      "license_id": "CC0-1.0",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    {
      "source_id": "synthetic-findley-calibration-provider",
      "origin": "synthetic",
      "citation": "Project-authored synthetic Findley coefficient and one reference strength point for API wiring only.",
      "license_id": "CC0-1.0",
      "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    }
  ],
  "usage_rights_evidence": [
    {
      "source_id": "synthetic-findley-fixture",
      "origin": "synthetic",
      "citation": "Project-authored synthetic fixture; no external dataset is included.",
      "license_id": "CC0-1.0",
      "sha256": null
    }
  ],
  "maximum_shear_pair_evaluations": 1000,
  "tensor_units_and_component_order_reviewed": true,
  "candidate_plane_set_and_coverage_reviewed": true,
  "cycle_definition_and_closure_reviewed": true,
  "findley_coefficient_and_calibration_basis_reviewed": true,
  "calibration_same_material_and_reference_life_reviewed": true,
  "usage_rights_reviewed": true,
  "computational_use_authorized": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fatigue_findley.py#L115)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

# `integration.external_crevice_solver_receipt`

**목적:** An external solver receipt must match the pinned aperture history, cell mesh, face ordering, SI units, axial sign and exact time knots.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.external_crevice_solver_history.v1", "default": "matintegrity.external_crevice_solver_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_run_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `mesh_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_result` | 예 | `{"additionalProperties": true, "type": "object"}` | 계약·필드 설명 참조 |
| `geometry_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `coordinate_system_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `coordinate_origin` | 예 | `{"const": "mouth", "type": "string"}` | 계약·필드 설명 참조 |
| `positive_axial_direction` | 예 | `{"const": "mouth_to_tip", "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_unit` | 예 | `{"const": "Pa", "type": "string"}` | 계약·필드 설명 참조 |
| `velocity_unit` | 예 | `{"const": "m/s", "type": "string"}` | 계약·필드 설명 참조 |
| `length_unit` | 예 | `{"const": "m", "type": "string"}` | 계약·필드 설명 참조 |
| `time_unit` | 예 | `{"const": "s", "type": "string"}` | 계약·필드 설명 참조 |
| `elapsed_time_s` | 예 | `{"items": {"type": "number"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | s |
| `face_positions_m` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 2001, "minItems": 3, "type": "array"}` | m |
| `cell_widths_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 2000, "minItems": 2, "type": "array"}` | m |
| `cell_aperture_m` | 예 | `{"items": {"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | m |
| `face_pressure_Pa` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | Pa |
| `face_velocity_m_s` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | m/s |
| `time_interpolation` | 예 | `{"const": "piecewise_linear", "type": "string"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `source_result_digest_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `coordinate_and_unit_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `face_order_and_velocity_sign_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `mesh_to_geometry_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `geometry_revision_and_time_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `piecewise_linear_velocity_interpolation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ExternalCreviceSolverHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `elapsed_time_s` | `s` |
| `face_positions_m` | `m` |
| `cell_widths_m` | `m` |
| `cell_aperture_m` | `m` |
| `face_pressure_Pa` | `Pa` |
| `face_velocity_m_s` | `m/s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- An external solver receipt must match the pinned aperture history, cell mesh, face ordering, SI units, axial sign and exact time knots.
- Only caller-reviewed piecewise-linear interpolation inside the receipt clock is exposed; no extrapolation or solver validation is performed.

## 구현 근거·독립 설명

- `external_crevice_solver_pressure_velocity_receipt`: Require a caller-normalized external solver record and its source digest, provider revision/run ID, mesh revision, coordinate-system identity, explicit SI units, mouth origin, mouth-to-tip positive direction, exact geometry/time mapping, cell/face field cardinalities and evidence. Bind every pressure/velocity knot to a digest-pinned aperture-history state and reject extrapolation, mismatched mesh dimensions or unreviewed face orientation. Expose reviewed piecewise-linear interpolation of face velocity as a callable for the existing restricted-transport consumer and preserve the provider/configuration digest. This is an exchange adapter, not a CFD solver or validation of its numerical method or accuracy.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.external_crevice_solver_receipt"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["integration.external_crevice_solver_receipt"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "synthetic-receipt",
  "provider_id": "synthetic-cfd",
  "provider_revision": "1",
  "provider_run_id": "run-1",
  "time_basis_id": "elapsed_seconds",
  "provider_result_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "mesh_revision": "mesh-1",
  "geometry_result": {
    "status": "computed",
    "values": {
      "cell_widths_m": [
        0.005,
        0.005
      ],
      "geometry_states": [
        {
          "elapsed_time_s": 0.0,
          "cell_aperture_m": [
            0.001,
            0.001
          ]
        },
        {
          "elapsed_time_s": 1.0,
          "cell_aperture_m": [
            0.0011,
            0.001
          ]
        }
      ]
    }
  },
  "geometry_result_sha256": "be41a1e05f1f52506018fb41dc8ade55a84a5d4c352ecf556cf41b94a9400cd2",
  "coordinate_system_id": "axial",
  "coordinate_origin": "mouth",
  "positive_axial_direction": "mouth_to_tip",
  "pressure_unit": "Pa",
  "velocity_unit": "m/s",
  "length_unit": "m",
  "time_unit": "s",
  "elapsed_time_s": [
    0.0,
    1.0
  ],
  "face_positions_m": [
    0.0,
    0.005,
    0.01
  ],
  "cell_widths_m": [
    0.005,
    0.005
  ],
  "cell_aperture_m": [
    [
      0.001,
      0.001
    ],
    [
      0.0011,
      0.001
    ]
  ],
  "face_pressure_Pa": [
    [
      100.0,
      50.0,
      0.0
    ],
    [
      100.0,
      50.0,
      0.0
    ]
  ],
  "face_velocity_m_s": [
    [
      0.0,
      0.0,
      0.0
    ],
    [
      0.0,
      0.0,
      0.0
    ]
  ],
  "time_interpolation": "piecewise_linear",
  "evidence": [
    {
      "source_id": "synthetic-cfd",
      "origin": "synthetic",
      "citation": "API fixture",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ],
  "source_result_digest_reviewed": true,
  "coordinate_and_unit_mapping_reviewed": true,
  "face_order_and_velocity_sign_reviewed": true,
  "mesh_to_geometry_mapping_reviewed": true,
  "geometry_revision_and_time_alignment_reviewed": true,
  "piecewise_linear_velocity_interpolation_reviewed": true,
  "computational_use_authorized": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/external_crevice_solver.py#L177)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

# `inspection.magnetic_flux_leakage_acquisition_summary`

**목적:** Caller-controlled magnetizer, sensor array, field-state checkpoint, reference-standard, encoded-scan and indication record; no embedded sizing or acceptance rule.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `examination_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `surface_condition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `magnetizer` | 예 | `{"$ref": "#/$defs/MflMagnetizer"}` | 계약·필드 설명 참조 |
| `sensor_arrays` | 예 | `{"items": {"$ref": "#/$defs/MflSensorArray"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `reference_standard` | 예 | `{"$ref": "#/$defs/MflReferenceStandard"}` | 계약·필드 설명 참조 |
| `magnetic_field_checkpoints` | 아니오 | `{"items": {"$ref": "#/$defs/MflMagneticFieldCheckpoint"}, "type": "array"}` | 계약·필드 설명 참조 |
| `scans` | 예 | `{"items": {"$ref": "#/$defs/EncodedMflScan"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `indications` | 아니오 | `{"items": {"$ref": "#/$defs/MflIndication"}, "type": "array"}` | 계약·필드 설명 참조 |
| `magnetizer_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sensor_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reference_standard_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `magnetization_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `lift_off_and_surface_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `encoder_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `scan_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `indication_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `negative_result_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/MflExamination.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `scan_geometry_by_id` | `mixed; see nested field names` |
| `magnetic_field_checkpoints` | `mixed; see nested field names` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-controlled magnetizer, sensor array, field-state checkpoint, reference-standard, encoded-scan and indication record; no embedded sizing or acceptance rule.

## 구현 근거·독립 설명

- `magnetic_flux_leakage_acquisition_definition`: Preserve one caller-controlled magnetic-flux-leakage procedure and revision, physical scope, material and surface condition, magnetizer identity and direction, calibrated sensor arrays and component mapping, physical reference-standard features, reviewed H/B field-state checkpoints, immutable encoded-scan hashes and evidence-bound indications. Require exact magnetizer and sensor-array coverage by the reference standard and preserve active channels, pass direction, speed and caller-reviewed encoder coordinates. Compute only encoded span, vector magnitudes and an explicitly non-constitutive B/H magnitude ratio. Do not infer saturation, field uniformity or flaw sensitivity, remove baselines, compensate velocity or lift-off, fuse signals, detect, classify, size, apply acceptance limits, or create POD, remaining-life or failure-probability claims.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.magnetic_flux_leakage_acquisition_summary"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.magnetic_flux_leakage_acquisition_summary"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "examination_id": "synthetic-mfl-examination",
  "procedure_id": "synthetic-mfl-procedure",
  "procedure_revision": "A",
  "physical_scope_id": "synthetic-plate",
  "material_id": "synthetic-steel",
  "material_condition_id": "synthetic-condition",
  "surface_condition": "synthetic clean surface",
  "magnetizer": {
    "magnetizer_id": "magnetizer-1",
    "excitation_type": "permanent_magnet",
    "nominal_magnetization_direction": "axial",
    "pole_spacing_m": 0.1,
    "magnetization_control_basis": "synthetic fixture",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored MFL example"
      }
    ]
  },
  "sensor_arrays": [
    {
      "sensor_array_id": "array-1",
      "channel_ids": [
        "radial-1"
      ],
      "measured_components": [
        "radial"
      ],
      "channel_component_by_id": {
        "radial-1": "radial"
      },
      "nominal_channel_pitch_m": 0.002,
      "lift_off_control_basis": "synthetic fixed spacer",
      "calibration_id": "synthetic-calibration",
      "calibration_basis": "authored example",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored MFL example"
        }
      ]
    }
  ],
  "reference_standard": {
    "reference_standard_id": "reference-1",
    "material_id": "synthetic-steel",
    "material_condition_id": "synthetic-condition",
    "wall_thickness_m": 0.01,
    "applicable_magnetizer_ids": [
      "magnetizer-1"
    ],
    "applicable_sensor_array_ids": [
      "array-1"
    ],
    "features": [
      {
        "feature_id": "recess-1",
        "feature_kind": "synthetic recess",
        "surface": "external",
        "geometry_description": "authored rectangular recess",
        "nominal_depth_m": 0.002,
        "physical_feature_identity_reviewed": true,
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored MFL example"
          }
        ]
      }
    ],
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored MFL example"
      }
    ]
  },
  "magnetic_field_checkpoints": [
    {
      "checkpoint_id": "field-1",
      "physical_location_description": "synthetic plate centre",
      "coordinate_frame": "x axial, y circumferential, z outward",
      "magnetic_field_strength_A_m": [
        5000.0,
        0.0,
        0.0
      ],
      "magnetic_flux_density_T": [
        1.0,
        0.0,
        0.0
      ],
      "measurement_temperature_K": 293.15,
      "measurement_basis": "authored exact vector",
      "state_identity_reviewed": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored MFL example"
        }
      ]
    }
  ],
  "scans": [
    {
      "scan_id": "scan-1",
      "magnetizer_id": "magnetizer-1",
      "sensor_array_id": "array-1",
      "active_channel_ids": [
        "radial-1"
      ],
      "data_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
      "sample_count": 6,
      "signal_encoding": "synthetic float",
      "signal_unit_token": "T",
      "pass_direction": "forward",
      "scan_speed_m_s": 0.05,
      "scan_speed_basis": "synthetic constant speed",
      "sample_spacing_m": 0.002,
      "encoder_origin_m": 0.0,
      "coordinate_mapping_basis": "synthetic encoder",
      "acquisition_order": 0,
      "time_basis": "synthetic scan order"
    }
  ],
  "indications": [],
  "magnetizer_identity_reviewed": true,
  "sensor_calibration_reviewed": true,
  "reference_standard_reviewed": true,
  "magnetization_state_reviewed": true,
  "lift_off_and_surface_condition_reviewed": true,
  "encoder_calibration_reviewed": true,
  "scan_identity_reviewed": true,
  "indication_mapping_reviewed": true,
  "negative_result_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored MFL example"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/magnetic_flux_leakage.py#L230)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

# `inspection.tofd_acquisition_summary`

**목적:** Caller-controlled TOFD probe pair, velocity, wall, encoder, frame, time-pick and indication record; symmetric straight paths only.

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
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `specimen_longitudinal_velocity_m_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m/s |
| `specimen_velocity_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `wall_thickness_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `wall_thickness_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `probe_pair` | 예 | `{"$ref": "#/$defs/TofdProbePair"}` | 계약·필드 설명 참조 |
| `encoder_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `encoder_direction` | 예 | `{"enum": ["increasing", "decreasing"], "type": "string"}` | 계약·필드 설명 참조 |
| `frames` | 예 | `{"items": {"$ref": "#/$defs/EncodedTofdFrame"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `diffraction_picks` | 아니오 | `{"items": {"$ref": "#/$defs/TofdDiffractionPick"}, "type": "array"}` | 계약·필드 설명 참조 |
| `indications` | 아니오 | `{"items": {"$ref": "#/$defs/TofdIndication"}, "type": "array"}` | 계약·필드 설명 참조 |
| `probe_pair_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_velocity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `wall_thickness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `encoder_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `acquisition_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `frame_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `time_picks_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `indication_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `symmetric_path_applicable` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `negative_result_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TofdExamination.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `direct_lateral_path_length_m` | `m` |
| `declared_wall_backwall_path_length_m` | `m` |
| `declared_wall_backwall_delay_from_lateral_s` | `s` |
| `tip_depth_by_pick_id` | `m` |
| `indication_geometry_by_id` | `mixed; see nested field names` |
| `encoder_span_m` | `m` |
| `minimum_nonzero_encoder_increment_m` | `m` |
| `maximum_nonzero_encoder_increment_m` | `m` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-controlled TOFD probe pair, velocity, wall, encoder, frame, time-pick and indication record; symmetric straight paths only.

## 구현 근거·독립 설명

- `tofd_acquisition_definition`: Preserve one caller-controlled TOFD procedure and revision, physical scope, material condition, distinct transmit/receive probe and wedge identities, measured probe-index separation, specimen longitudinal velocity and wall-thickness bases, calibrated encoder direction, immutable frame hashes, same-frame lateral/backwall arrival picks and evidence-bound upper/lower diffraction picks. Under an explicitly reviewed symmetric straight-path assumption, compute only lateral/backwall path descriptors, pick depths relative to the same-frame lateral wave, paired-tip separation and encoder-spacing diagnostics. Keep missing or noncausal reference picks and reversed tip ordering visible. Do not process waveforms, automate time picking, qualify near-surface or backwall dead zones, infer flaw identity, apply acceptance limits, or create POD, life or failure probabilities.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.tofd_acquisition_summary"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.tofd_acquisition_summary"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "examination_id": "example-tofd",
  "procedure_id": "example-procedure",
  "procedure_revision": "1",
  "physical_scope_id": "example-weld-volume",
  "material_condition_id": "example-material-condition",
  "specimen_longitudinal_velocity_m_s": 5900.0,
  "specimen_velocity_basis": "synthetic example",
  "wall_thickness_m": 0.025,
  "wall_thickness_basis": "synthetic example",
  "probe_pair": {
    "pair_id": "pair-1",
    "transmit_probe_id": "tx",
    "receive_probe_id": "rx",
    "transmit_wedge_id": "tx-wedge",
    "receive_wedge_id": "rx-wedge",
    "probe_index_separation_m": 0.04,
    "center_frequency_Hz": 10000000.0,
    "nominal_refracted_angle_rad": 1.0,
    "index_separation_basis": "synthetic example",
    "evidence": [
      {
        "source_id": "example-tofd",
        "origin": "synthetic",
        "citation": "authored example"
      }
    ]
  },
  "encoder_id": "encoder-1",
  "encoder_direction": "increasing",
  "frames": [
    {
      "frame_id": "frame-1",
      "encoder_position_m": 0.0,
      "data_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
      "sample_count": 1000,
      "sample_interval_s": 1e-08,
      "amplitude_encoding": "synthetic",
      "time_zero_basis": "synthetic clock",
      "lateral_wave_arrival_time_s": 1e-05,
      "backwall_echo_arrival_time_s": 1.4073091927852285e-05
    }
  ],
  "diffraction_picks": [],
  "indications": [],
  "probe_pair_identity_reviewed": true,
  "specimen_velocity_reviewed": true,
  "wall_thickness_reviewed": true,
  "encoder_calibration_reviewed": true,
  "acquisition_calibration_reviewed": true,
  "frame_identity_reviewed": true,
  "time_picks_reviewed": true,
  "indication_mapping_reviewed": true,
  "symmetric_path_applicable": true,
  "negative_result_reviewed": true,
  "evidence": [
    {
      "source_id": "example-tofd",
      "origin": "synthetic",
      "citation": "authored example"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/tofd.py#L168)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

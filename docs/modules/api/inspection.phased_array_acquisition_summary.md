# `inspection.phased_array_acquisition_summary`

**목적:** Caller-controlled probe, wedge, material velocity, beam-law, encoder, frame and indication record; no embedded reconstruction or acceptance rule.

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
| `acquisition_mode` | 예 | `{"enum": ["sectorial", "linear", "transmit_receive", "full_matrix_capture"], "type": "string"}` | 계약·필드 설명 참조 |
| `specimen_wave_velocity_m_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m/s |
| `specimen_wave_velocity_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `encoder_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `encoder_direction` | 예 | `{"enum": ["increasing", "decreasing"], "type": "string"}` | 계약·필드 설명 참조 |
| `probes` | 예 | `{"items": {"$ref": "#/$defs/PhasedArrayProbe"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `wedges` | 예 | `{"items": {"$ref": "#/$defs/PhasedArrayWedge"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `beam_laws` | 아니오 | `{"items": {"$ref": "#/$defs/PhasedArrayBeamLaw"}, "type": "array"}` | 계약·필드 설명 참조 |
| `frames` | 예 | `{"items": {"$ref": "#/$defs/EncodedPhasedArrayFrame"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `indications` | 아니오 | `{"items": {"$ref": "#/$defs/PhasedArrayIndication"}, "type": "array"}` | 계약·필드 설명 참조 |
| `probe_and_wedge_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_velocity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `beam_law_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `encoder_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `acquisition_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `frame_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `indication_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `negative_result_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PhasedArrayExamination.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `probe_geometry_by_id` | `mixed; see nested field names` |
| `beam_law_delay_span_by_id` | `s` |
| `encoder_span_m` | `m` |
| `minimum_nonzero_encoder_increment_m` | `m` |
| `maximum_nonzero_encoder_increment_m` | `m` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-controlled probe, wedge, material velocity, beam-law, encoder, frame and indication record; no embedded reconstruction or acceptance rule.

## 구현 근거·독립 설명

- `phased_array_acquisition_definition`: Preserve one caller-controlled phased-array procedure and revision, physical scope, material condition, specimen wave velocity and basis, probe element layout, wedge identities, focal laws, calibrated encoder direction, immutable frame hashes and evidence-bound indications. Support pulse-echo or separate transmit/receive probes and conventional beam-law or full-matrix capture records without converting one into the other. Preserve frame order and duplicate encoder positions. Compute only physical aperture, nominal specimen wavelength, pitch ratio, delay spans and encoder-spacing diagnostics. Do not synthesize missing delays, sort or resample waveforms, reconstruct TFM images, infer flaw size, apply acceptance limits, or create detection, life or failure probabilities.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.phased_array_acquisition_summary"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.phased_array_acquisition_summary"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "examination_id": "example-paut-001",
  "procedure_id": "user-paut-procedure",
  "procedure_revision": "1",
  "physical_scope_id": "weld-22",
  "material_condition_id": "steel-weld-condition-a",
  "acquisition_mode": "sectorial",
  "specimen_wave_velocity_m_s": 5900.0,
  "specimen_wave_velocity_basis": "user-reviewed reference-block record",
  "encoder_id": "encoder-1",
  "encoder_direction": "increasing",
  "probes": [
    {
      "probe_id": "probe-a",
      "role": "pulse_echo",
      "element_count": 4,
      "element_pitch_m": 0.001,
      "element_width_m": 0.0008,
      "center_frequency_Hz": 5000000.0,
      "element_layout_basis": "user-controlled probe datasheet",
      "evidence": [
        {
          "source_id": "example-paut-record",
          "origin": "synthetic",
          "citation": "authored API demonstration",
          "license_id": "MIT"
        }
      ]
    }
  ],
  "wedges": [
    {
      "wedge_id": "wedge-a",
      "probe_id": "probe-a",
      "wedge_material_id": "polymer-a",
      "wedge_longitudinal_velocity_m_s": 2300.0,
      "nominal_exit_point_offset_m": 0.01,
      "mounting_orientation": "user-controlled mounting record",
      "evidence": [
        {
          "source_id": "example-paut-record",
          "origin": "synthetic",
          "citation": "authored API demonstration",
          "license_id": "MIT"
        }
      ]
    }
  ],
  "beam_laws": [
    {
      "law_id": "law-a",
      "transmit_probe_id": "probe-a",
      "receive_probe_id": "probe-a",
      "refracted_angle_rad": 0.7,
      "refracted_wave_mode": "longitudinal",
      "focus_distance_m": 0.02,
      "first_transmit_element": 0,
      "transmit_element_count": 4,
      "transmit_delay_s": [
        0.0,
        1e-08,
        2e-08,
        3e-08
      ],
      "first_receive_element": 0,
      "receive_element_count": 4,
      "receive_delay_s": [
        0.0,
        1e-08,
        2e-08,
        3e-08
      ],
      "law_generation_basis": "user-controlled focal-law export"
    }
  ],
  "frames": [
    {
      "frame_id": "frame-0",
      "encoder_position_m": 0.0,
      "beam_law_id": "law-a",
      "data_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "sample_count": 1024,
      "sample_interval_s": 1e-08,
      "transmit_event_count": 1,
      "receive_channel_count": 4,
      "amplitude_encoding": "signed-int16",
      "time_zero_basis": "user-controlled acquisition clock"
    }
  ],
  "indications": [],
  "probe_and_wedge_identity_reviewed": true,
  "material_velocity_reviewed": true,
  "beam_law_reviewed": true,
  "encoder_calibration_reviewed": true,
  "acquisition_calibration_reviewed": true,
  "frame_identity_reviewed": true,
  "indication_mapping_reviewed": true,
  "negative_result_reviewed": true,
  "evidence": [
    {
      "source_id": "example-paut-record",
      "origin": "synthetic",
      "citation": "authored API demonstration",
      "license_id": "MIT"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/phased_array.py#L167)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

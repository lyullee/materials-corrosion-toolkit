# `inspection.acoustic_emission_campaign`

**목적:** Asset geometry, zones, sensors, channels, acquisition intervals and event features are reviewed caller records.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `zones` | 예 | `{"items": {"$ref": "#/$defs/AcousticEmissionZone"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `sensors` | 예 | `{"items": {"$ref": "#/$defs/AcousticEmissionSensorChannel"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `calibrations` | 예 | `{"items": {"$ref": "#/$defs/AcousticEmissionCalibrationRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `acquisition_intervals` | 예 | `{"items": {"$ref": "#/$defs/AcousticEmissionAcquisitionInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `event_records` | 아니오 | `{"items": {"$ref": "#/$defs/AcousticEmissionEventFeatureRecord"}, "type": "array"}` | 계약·필드 설명 참조 |
| `source_location_records` | 아니오 | `{"items": {"$ref": "#/$defs/AcousticEmissionSourceLocationRecord"}, "type": "array"}` | 계약·필드 설명 참조 |
| `support_envelope` | 예 | `{"$ref": "#/$defs/AcousticEmissionSupportEnvelope"}` | 계약·필드 설명 참조 |
| `asset_zone_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sensor_channel_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sensor_coupling_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `acquisition_intervals_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `event_feature_definitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `source_location_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_and_digest_lineage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `support_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AcousticEmissionCampaign.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `campaign_id` | `1` |
| `valid_acquisition_duration_s` | `s` |
| `valid_event_count` | `1` |
| `valid_source_location_record_count` | `1` |
| `event_feature_summary` | `mixed` |
| `invalid_record_ids` | `1` |
| `missing_reference_records` | `1` |
| `missing_feature_support_records` | `1` |
| `outside_declared_support_records` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Asset geometry, zones, sensors, channels, acquisition intervals and event features are reviewed caller records.
- Calibration and source-location results retain exact provider, configuration, data and result digests.

## 구현 근거·독립 설명

- `reviewed_acoustic_emission_campaign_summary`: Inventory acoustic-emission zones, sensors, calibrations, acquisition intervals, event features and reported source locations with exact provider and data lineage, then compare only with caller-owned feature support. Do not infer a defect or leak source, localization accuracy, POD, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.acoustic_emission_campaign"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.acoustic_emission_campaign"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "campaign_id": "authored-ae-campaign",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "zones": [
    {
      "zone_id": "zone-1",
      "coordinate_frame": "asset-cartesian",
      "geometry_description": "authored synthetic zone",
      "geometry_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored AE zone"
        }
      ]
    }
  ],
  "sensors": [
    {
      "sensor_id": "sensor-1",
      "channel_id": "channel-1",
      "zone_ids": [
        "zone-1"
      ],
      "coordinate_frame": "asset-cartesian",
      "position_m": [
        0.0,
        0.0,
        0.0
      ],
      "coupling_description": "authored coupling",
      "calibration_id": "cal-1",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored AE sensor"
        }
      ]
    }
  ],
  "calibrations": [
    {
      "calibration_id": "cal-1",
      "channel_ids": [
        "channel-1"
      ],
      "source_location_coordinate_frame": "asset-cartesian",
      "source_location_m": [
        0.1,
        0.0,
        0.0
      ],
      "source_description": "authored artificial source",
      "method_id": "method-1",
      "provider_id": "provider-1",
      "provider_version": "1",
      "configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "data_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored AE calibration"
        }
      ]
    }
  ],
  "acquisition_intervals": [
    {
      "interval_id": "interval-1",
      "start_time_s": 0.0,
      "end_time_s": 60.0,
      "active_channel_ids": [
        "channel-1"
      ],
      "operating_state_id": "state-1",
      "provider_id": "provider-1",
      "provider_version": "1",
      "configuration_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "data_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored AE interval"
        }
      ]
    }
  ],
  "event_records": [
    {
      "event_id": "event-1",
      "interval_id": "interval-1",
      "zone_id": "zone-1",
      "channel_id": "channel-1",
      "event_time_s": 20.0,
      "feature_values": {
        "peak_voltage": 0.4,
        "duration": 0.01
      },
      "feature_units": {
        "peak_voltage": "V",
        "duration": "s"
      },
      "provider_id": "provider-1",
      "provider_version": "1",
      "configuration_digest": "1111111111111111111111111111111111111111111111111111111111111111",
      "data_digest": "2222222222222222222222222222222222222222222222222222222222222222",
      "result_digest": "3333333333333333333333333333333333333333333333333333333333333333",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored AE event"
        }
      ]
    }
  ],
  "source_location_records": [
    {
      "location_record_id": "location-1",
      "event_id": "event-1",
      "zone_id": "zone-1",
      "coordinate_frame": "asset-cartesian",
      "reported_location_m": [
        0.2,
        0.0,
        0.0
      ],
      "expanded_uncertainty_m": 0.05,
      "method_id": "location-method-1",
      "provider_id": "provider-1",
      "provider_version": "1",
      "configuration_digest": "4444444444444444444444444444444444444444444444444444444444444444",
      "data_digest": "5555555555555555555555555555555555555555555555555555555555555555",
      "result_digest": "6666666666666666666666666666666666666666666666666666666666666666",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored AE source location"
        }
      ]
    }
  ],
  "support_envelope": {
    "envelope_id": "support-1",
    "applicable_zone_ids": [
      "zone-1"
    ],
    "applicable_channel_ids": [
      "channel-1"
    ],
    "feature_support": [
      {
        "feature_id": "peak_voltage",
        "unit_token": "V",
        "minimum_value": 0.0,
        "maximum_value": 1.0
      },
      {
        "feature_id": "duration",
        "unit_token": "s",
        "minimum_value": 0.0,
        "maximum_value": 0.1
      }
    ],
    "provider_id": "support-provider",
    "provider_version": "1",
    "configuration_digest": "7777777777777777777777777777777777777777777777777777777777777777",
    "data_digest": "8888888888888888888888888888888888888888888888888888888888888888",
    "result_digest": "9999999999999999999999999999999999999999999999999999999999999999",
    "applicability_basis": "authored caller support",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored AE support"
      }
    ]
  },
  "asset_zone_geometry_reviewed": true,
  "sensor_channel_mapping_reviewed": true,
  "sensor_coupling_reviewed": true,
  "calibration_evidence_reviewed": true,
  "acquisition_intervals_reviewed": true,
  "event_feature_definitions_reviewed": true,
  "source_location_evidence_reviewed": true,
  "provider_and_digest_lineage_reviewed": true,
  "support_envelope_authority_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/acoustic_emission.py#L239)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

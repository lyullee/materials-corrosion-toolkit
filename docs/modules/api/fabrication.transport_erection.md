# `fabrication.transport_erection`

**목적:** Ordered item, lift, transport, storage, support and erection evidence is caller supplied.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `item_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `item_configuration_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `events` | 예 | `{"items": {"$ref": "#/$defs/OrderedHandlingEvent"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `temporary_supports` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/TemporarySupportEvidence"}, "type": "array"}` | 계약·필드 설명 참조 |
| `measurements` | 예 | `{"items": {"$ref": "#/$defs/ErectionMeasurement"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_profile` | 예 | `{"$ref": "#/$defs/TransportErectionCallerProfile"}` | 계약·필드 설명 참조 |
| `item_lift_transport_storage_erection_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `ordered_event_clock_and_orientation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_units_uncertainty_and_provenance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temporary_support_install_remove_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `alignment_geometry_damage_and_nde_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_profile_and_criteria_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `invalid_and_missing_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TransportErectionCampaignAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `report_schema_version` | `1` |
| `assessment_id` | `1` |
| `campaign_id` | `1` |
| `campaign_outcome` | `1` |
| `caller_profile_id` | `1` |
| `metric_values` | `mixed` |
| `criterion_findings` | `mixed` |
| `diagnostics` | `mixed` |
| `input_digest` | `1` |
| `caller_profile_only` | `1` |
| `structural_solver_or_allowable_load` | `1` |
| `automatic_damage_determination` | `1` |
| `physical_qualification` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Ordered item, lift, transport, storage, support and erection evidence is caller supplied.
- No structural solver, allowable load table, automatic damage decision, or qualification is produced.

## 구현 근거·독립 설명

- `authored_transport_erection_campaign_evidence_audit`: Preserve caller-supplied item, lift, transport, storage, erection and support identity; ordered handling events; acceleration, load, orientation, temperature, humidity and impact observations; temporary-support state; and alignment, geometry, damage-survey or NDE measurements. Compare only with caller-authored criteria. Do not solve structures, provide allowable loads or code tables, automatically classify damage or claim qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.transport_erection"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.transport_erection"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "campaign_id": "campaign-1",
  "item_id": "item-1",
  "item_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "clock_id": "clock-1",
  "events": [
    {
      "event_id": "transport-event",
      "sequence_index": 0,
      "event_kind": "transport",
      "activity_id": "activity-transport-event",
      "start_time_s": 0.0,
      "end_time_s": 10.0,
      "item_id": "item-1",
      "lift_id": null,
      "transport_id": "transport-1",
      "storage_id": null,
      "erection_id": null,
      "support_id": null,
      "orientation_definition": "caller orientation for transport-event",
      "event_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "observations": [
        {
          "observation_id": "accel-1",
          "event_id": "transport-event",
          "observation_time_s": 5.0,
          "observation_kind": "acceleration",
          "metric_id": "peak_acceleration",
          "metric_definition": "caller definition for peak_acceleration",
          "value": 1.5,
          "unit_token": "m/s2",
          "expanded_uncertainty": 0.1,
          "sensor_or_instrument_id": "instrument-accel-1",
          "provider_id": "provider-1",
          "provider_revision": "rev-1",
          "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "observation_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "observation_id": "temp-1",
          "event_id": "transport-event",
          "observation_time_s": 5.0,
          "observation_kind": "temperature",
          "metric_id": "temperature",
          "metric_definition": "caller definition for temperature",
          "value": 295.0,
          "unit_token": "K",
          "expanded_uncertainty": 0.1,
          "sensor_or_instrument_id": "instrument-temp-1",
          "provider_id": "provider-1",
          "provider_revision": "rev-1",
          "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "observation_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "observation_id": "humidity-1",
          "event_id": "transport-event",
          "observation_time_s": 5.0,
          "observation_kind": "humidity",
          "metric_id": "relative_humidity",
          "metric_definition": "caller definition for relative_humidity",
          "value": 40.0,
          "unit_token": "%",
          "expanded_uncertainty": 0.1,
          "sensor_or_instrument_id": "instrument-humidity-1",
          "provider_id": "provider-1",
          "provider_revision": "rev-1",
          "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "observation_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "observation_id": "impact-1",
          "event_id": "transport-event",
          "observation_time_s": 5.0,
          "observation_kind": "impact",
          "metric_id": "impact_index",
          "metric_definition": "caller definition for impact_index",
          "value": 0.0,
          "unit_token": "count",
          "expanded_uncertainty": 0.1,
          "sensor_or_instrument_id": "instrument-impact-1",
          "provider_id": "provider-1",
          "provider_revision": "rev-1",
          "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "observation_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "observation_id": "load-1",
          "event_id": "transport-event",
          "observation_time_s": 5.0,
          "observation_kind": "load",
          "metric_id": "transport_load",
          "metric_definition": "caller definition for transport_load",
          "value": 10.0,
          "unit_token": "kN",
          "expanded_uncertainty": 0.1,
          "sensor_or_instrument_id": "instrument-load-1",
          "provider_id": "provider-1",
          "provider_revision": "rev-1",
          "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "observation_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "observation_id": "orientation-1",
          "event_id": "transport-event",
          "observation_time_s": 5.0,
          "observation_kind": "orientation",
          "metric_id": "tilt",
          "metric_definition": "caller definition for tilt",
          "value": 0.01,
          "unit_token": "rad",
          "expanded_uncertainty": 0.1,
          "sensor_or_instrument_id": "instrument-orientation-1",
          "provider_id": "provider-1",
          "provider_revision": "rev-1",
          "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "observation_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "storage-event",
      "sequence_index": 1,
      "event_kind": "storage",
      "activity_id": "activity-storage-event",
      "start_time_s": 10.0,
      "end_time_s": 20.0,
      "item_id": "item-1",
      "lift_id": null,
      "transport_id": null,
      "storage_id": "storage-1",
      "erection_id": null,
      "support_id": null,
      "orientation_definition": "caller orientation for storage-event",
      "event_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "observations": [],
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "support-install",
      "sequence_index": 2,
      "event_kind": "temporary_support_install",
      "activity_id": "activity-support-install",
      "start_time_s": 20.0,
      "end_time_s": 21.0,
      "item_id": "item-1",
      "lift_id": null,
      "transport_id": null,
      "storage_id": null,
      "erection_id": null,
      "support_id": "support-1",
      "orientation_definition": "caller orientation for support-install",
      "event_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "observations": [],
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "lift-event",
      "sequence_index": 3,
      "event_kind": "lift",
      "activity_id": "activity-lift-event",
      "start_time_s": 21.0,
      "end_time_s": 30.0,
      "item_id": "item-1",
      "lift_id": "lift-1",
      "transport_id": null,
      "storage_id": null,
      "erection_id": null,
      "support_id": null,
      "orientation_definition": "caller orientation for lift-event",
      "event_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "observations": [],
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "erection-event",
      "sequence_index": 4,
      "event_kind": "erection",
      "activity_id": "activity-erection-event",
      "start_time_s": 30.0,
      "end_time_s": 40.0,
      "item_id": "item-1",
      "lift_id": null,
      "transport_id": null,
      "storage_id": null,
      "erection_id": "erection-1",
      "support_id": null,
      "orientation_definition": "caller orientation for erection-event",
      "event_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "observations": [],
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "support-remove",
      "sequence_index": 5,
      "event_kind": "temporary_support_remove",
      "activity_id": "activity-support-remove",
      "start_time_s": 40.0,
      "end_time_s": 41.0,
      "item_id": "item-1",
      "lift_id": null,
      "transport_id": null,
      "storage_id": null,
      "erection_id": null,
      "support_id": "support-1",
      "orientation_definition": "caller orientation for support-remove",
      "event_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "observations": [],
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "temporary_supports": [
    {
      "support_id": "support-1",
      "support_type_descriptor": "caller temporary support descriptor",
      "physical_location_definition": "reviewed item coordinate",
      "installation_event_id": "support-install",
      "removal_event_id": "support-remove",
      "final_state": "removed",
      "support_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "installation_record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "removal_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "measurements": [
    {
      "measurement_id": "alignment-1",
      "event_id": "erection-event",
      "measurement_time_s": 35.0,
      "measurement_kind": "alignment",
      "stage_id": "post_erection",
      "metric_id": "alignment_offset",
      "metric_definition": "caller definition for alignment_offset",
      "value": 0.5,
      "unit_token": "mm",
      "expanded_uncertainty": 0.2,
      "reported_finding": "caller-reported alignment finding",
      "caller_disposition_id": null,
      "instrument_or_nde_procedure_id": "procedure-alignment",
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "raw_data_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "measurement_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "measurement_id": "geometry-1",
      "event_id": "erection-event",
      "measurement_time_s": 35.0,
      "measurement_kind": "geometry",
      "stage_id": "post_erection",
      "metric_id": null,
      "metric_definition": null,
      "value": null,
      "unit_token": null,
      "expanded_uncertainty": null,
      "reported_finding": "caller-reported geometry finding",
      "caller_disposition_id": null,
      "instrument_or_nde_procedure_id": "procedure-geometry",
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "raw_data_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "measurement_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "measurement_id": "damage-1",
      "event_id": "erection-event",
      "measurement_time_s": 35.0,
      "measurement_kind": "damage_survey",
      "stage_id": "post_erection",
      "metric_id": null,
      "metric_definition": null,
      "value": null,
      "unit_token": null,
      "expanded_uncertainty": null,
      "reported_finding": "caller-reported damage_survey finding",
      "caller_disposition_id": null,
      "instrument_or_nde_procedure_id": "procedure-damage_survey",
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "raw_data_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "measurement_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "measurement_id": "nde-1",
      "event_id": "erection-event",
      "measurement_time_s": 35.0,
      "measurement_kind": "nde",
      "stage_id": "post_erection",
      "metric_id": null,
      "metric_definition": null,
      "value": null,
      "unit_token": null,
      "expanded_uncertainty": null,
      "reported_finding": "caller-reported nde finding",
      "caller_disposition_id": null,
      "instrument_or_nde_procedure_id": "procedure-nde",
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "raw_data_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "measurement_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "caller_profile": {
    "profile_id": "profile-1",
    "profile_version": "1.0.0",
    "required_event_kinds": [
      "transport",
      "storage",
      "temporary_support_install",
      "lift",
      "erection",
      "temporary_support_remove"
    ],
    "required_measurement_kinds": [
      "alignment",
      "geometry",
      "damage_survey",
      "nde"
    ],
    "required_measurement_stage_ids": [
      "post_erection"
    ],
    "criteria": [
      {
        "criterion_id": "acceleration-limit",
        "evidence_source": "observation",
        "metric_id": "peak_acceleration",
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": 2.0,
        "reject_limit": 4.0,
        "unit_token": "m/s2",
        "criterion_basis": "caller-authored handling criterion"
      },
      {
        "criterion_id": "alignment-limit",
        "evidence_source": "measurement",
        "metric_id": "alignment_offset",
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": 1.0,
        "reject_limit": 3.0,
        "unit_token": "mm",
        "criterion_basis": "caller-authored handling criterion"
      }
    ],
    "profile_provider_id": "caller-provider",
    "profile_revision": "rev-1",
    "profile_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "caller_acceptance_authority": "caller handling review team",
    "structural_solver_used": false,
    "allowable_load_or_code_table_embedded": false,
    "automatic_damage_determination_claimed": false,
    "physical_qualification_claimed": false,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored campaign",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "item_lift_transport_storage_erection_identity_reviewed": true,
  "ordered_event_clock_and_orientation_reviewed": true,
  "observation_units_uncertainty_and_provenance_reviewed": true,
  "temporary_support_install_remove_state_reviewed": true,
  "alignment_geometry_damage_and_nde_evidence_reviewed": true,
  "caller_profile_and_criteria_reviewed": true,
  "invalid_and_missing_records_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored campaign",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/transport_erection_campaign.py#L338)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

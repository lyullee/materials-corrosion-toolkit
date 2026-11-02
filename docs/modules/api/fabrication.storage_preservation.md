# `fabrication.storage_preservation`

**목적:** Item, material, area, storage location, preservation method, material batch and event identities are exact caller inputs.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `campaign_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `item_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `storage_area_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `storage_location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `horizon_start_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `horizon_end_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `preservation_systems` | 예 | `{"items": {"$ref": "#/$defs/PreservationSystemIdentity"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `events` | 예 | `{"items": {"$ref": "#/$defs/StoragePreservationEvent"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_profile` | 예 | `{"$ref": "#/$defs/StoragePreservationCallerProfile"}` | 계약·필드 설명 참조 |
| `item_material_area_and_storage_location_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `preservation_methods_material_batches_and_procedures_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `event_clock_order_and_interval_coverage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `environment_and_preservation_fact_units_uncertainties_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `inspections_renewals_surface_and_corrosion_observations_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_validity_profile_missingness_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/StoragePreservationCampaign.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `campaign_id` | `1` |
| `quality_outcome` | `1` |
| `caller_profile_id` | `1` |
| `criterion_findings` | `mixed` |
| `horizon_duration_s` | `s` |
| `represented_exposure_duration_s` | `s` |
| `uncovered_duration_s` | `s` |
| `inspection_count` | `count` |
| `renewal_count` | `count` |
| `event_ids` | `1` |
| `source_group_ids` | `1` |
| `input_digest` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Item, material, area, storage location, preservation method, material batch and event identities are exact caller inputs.
- Ordered exposure, inspection and renewal records retain environmental, preservation, surface and corrosion observations.
- Campaign outcomes use caller criteria without rate, life, standard-cycle or automatic acceptance inference.

## 구현 근거·독립 설명

- `authored_storage_preservation_campaign_evidence_audit`: Preserve caller-supplied item, material, area, storage location, preservation method and material batch, ordered storage-exposure-inspection-renewal events, interval coverage, and temperature, humidity, dewpoint, ingress, desiccant, inhibitor, cover, seal, surface or corrosion observations. Apply only caller-authored criteria. Do not infer corrosion rate, remaining life, standard cycles or automatic acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.storage_preservation"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.storage_preservation"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "physical_scope_id": "scope-1",
  "campaign_id": "campaign-1",
  "item_id": "item-1",
  "material_id": "material-1",
  "storage_area_id": "area-1",
  "storage_location_id": "store-1",
  "horizon_start_s": 0.0,
  "horizon_end_s": 100.0,
  "preservation_systems": [
    {
      "preservation_system_id": "system-1",
      "preservation_method_id": "method-1",
      "preservation_material_id": "material-preservative-1",
      "preservation_material_batch_id": "batch-1",
      "application_procedure_id": "procedure-1",
      "system_record_digest": "6666666666666666666666666666666666666666666666666666666666666666",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller storage data",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "events": [
    {
      "event_id": "start",
      "sequence_index": 0,
      "event_kind": "storage_start",
      "start_time_s": 0.0,
      "end_time_s": null,
      "storage_location_id": "store-1",
      "preservation_system_id": "system-1",
      "facts": [],
      "caller_validity_status": "valid",
      "caller_validity_basis": "caller reviewed event",
      "event_record_digest": "6666666666666666666666666666666666666666666666666666666666666666",
      "source_group_id": "source-start",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller storage data",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "exposure-1",
      "sequence_index": 1,
      "event_kind": "exposure",
      "start_time_s": 0.0,
      "end_time_s": 100.0,
      "storage_location_id": "store-1",
      "preservation_system_id": "system-1",
      "facts": [
        {
          "fact_id": "humidity",
          "fact_kind": "relative_humidity",
          "quantity_id": "relative_humidity",
          "result_mode": "quantitative",
          "status": "reported",
          "value": 0.4,
          "expanded_uncertainty": 0.02,
          "unit_token": "1",
          "qualitative_class": null,
          "qualitative_uncertainty_basis": null,
          "method_id": "sensor-1",
          "fact_record_digest": "6666666666666666666666666666666666666666666666666666666666666666",
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "campaign",
              "origin": "measured",
              "citation": "caller storage data",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "caller_validity_status": "valid",
      "caller_validity_basis": "caller reviewed event",
      "event_record_digest": "6666666666666666666666666666666666666666666666666666666666666666",
      "source_group_id": "logger-1",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller storage data",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "inspection",
      "sequence_index": 2,
      "event_kind": "inspection",
      "start_time_s": 50.0,
      "end_time_s": null,
      "storage_location_id": "store-1",
      "preservation_system_id": "system-1",
      "facts": [],
      "caller_validity_status": "valid",
      "caller_validity_basis": "caller reviewed event",
      "event_record_digest": "6666666666666666666666666666666666666666666666666666666666666666",
      "source_group_id": "source-inspection",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller storage data",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "renewal",
      "sequence_index": 3,
      "event_kind": "renewal",
      "start_time_s": 60.0,
      "end_time_s": null,
      "storage_location_id": "store-1",
      "preservation_system_id": "system-1",
      "facts": [],
      "caller_validity_status": "valid",
      "caller_validity_basis": "caller reviewed event",
      "event_record_digest": "6666666666666666666666666666666666666666666666666666666666666666",
      "source_group_id": "source-renewal",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller storage data",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "end",
      "sequence_index": 4,
      "event_kind": "storage_end",
      "start_time_s": 100.0,
      "end_time_s": null,
      "storage_location_id": "store-1",
      "preservation_system_id": "system-1",
      "facts": [],
      "caller_validity_status": "valid",
      "caller_validity_basis": "caller reviewed event",
      "event_record_digest": "6666666666666666666666666666666666666666666666666666666666666666",
      "source_group_id": "source-end",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller storage data",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "caller_profile": {
    "profile_id": "profile-1",
    "profile_revision": "1",
    "item_id": "item-1",
    "material_id": "material-1",
    "storage_area_id": "area-1",
    "storage_location_id": "store-1",
    "supported_preservation_system_ids": [
      "system-1"
    ],
    "maximum_uncovered_duration_s": 0.0,
    "minimum_inspection_count": 1,
    "minimum_renewal_count": 1,
    "fact_criteria": [
      {
        "criterion_id": "humidity-rule",
        "fact_kind": "relative_humidity",
        "quantity_id": "relative_humidity",
        "result_mode": "quantitative",
        "unit_token": "1",
        "minimum_acceptable": null,
        "maximum_acceptable": 0.6,
        "accepted_qualitative_classes": [],
        "required_event_kinds": [
          "exposure"
        ],
        "criterion_basis": "caller humidity criterion",
        "evidence": [
          {
            "source_id": "campaign",
            "origin": "measured",
            "citation": "caller storage data",
            "license_id": null,
            "sha256": null
          }
        ]
      }
    ],
    "profile_source_digest": "6666666666666666666666666666666666666666666666666666666666666666",
    "built_in_standard_cycle_used": false,
    "evidence": [
      {
        "source_id": "campaign",
        "origin": "measured",
        "citation": "caller storage data",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "item_material_area_and_storage_location_reviewed": true,
  "preservation_methods_material_batches_and_procedures_reviewed": true,
  "event_clock_order_and_interval_coverage_reviewed": true,
  "environment_and_preservation_fact_units_uncertainties_reviewed": true,
  "inspections_renewals_surface_and_corrosion_observations_reviewed": true,
  "caller_validity_profile_missingness_and_digests_reviewed": true,
  "evidence": [
    {
      "source_id": "campaign",
      "origin": "measured",
      "citation": "caller storage data",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/storage_preservation_campaign.py#L219)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

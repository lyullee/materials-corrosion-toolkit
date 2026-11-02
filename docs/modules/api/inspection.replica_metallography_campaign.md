# `inspection.replica_metallography_campaign`

**목적:** Component, location, material, heat and ordered service history are exact caller inputs.

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
| `component_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `heat_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `service_history` | 예 | `{"items": {"$ref": "#/$defs/ReplicaServiceInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `fields` | 예 | `{"items": {"$ref": "#/$defs/ReplicaCampaignField"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_profile` | 예 | `{"$ref": "#/$defs/ReplicaCampaignCallerProfile"}` | 계약·필드 설명 참조 |
| `component_location_material_heat_and_service_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `surface_preparation_medium_magnification_and_instrument_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_image_and_record_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_definitions_units_classes_and_uncertainties_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `replicate_source_and_independence_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_validity_flags_profile_and_missingness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ReplicaMetallographyCampaign.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `campaign_id` | `1` |
| `quality_outcome` | `1` |
| `caller_profile_id` | `1` |
| `criterion_findings` | `mixed` |
| `field_ids` | `1` |
| `replica_ids` | `1` |
| `source_group_ids` | `1` |
| `independence_group_ids` | `1` |
| `service_history_digest` | `1` |
| `input_digest` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Component, location, material, heat and ordered service history are exact caller inputs.
- Preparation, replication medium, magnification, instrument, calibration, images and reported observations retain provenance.
- Campaign outcomes use caller criteria without image analysis, grade tables, life inference or standard acceptance.

## 구현 근거·독립 설명

- `authored_replica_metallography_campaign_evidence_audit`: Preserve caller-supplied component, location, material, heat, ordered service history, surface preparation, replica medium, magnification, instrument, calibration, image digest, and quantitative or qualitative grain, cavity, phase, precipitate, decarburization or user observations with uncertainty and independence lineage. Apply only caller-authored criteria. Do not perform image analysis, embed grading tables, infer creep life or claim standard acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.replica_metallography_campaign"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.replica_metallography_campaign"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "physical_scope_id": "scope-1",
  "campaign_id": "campaign-1",
  "component_id": "component-1",
  "material_id": "material-1",
  "material_condition_id": "condition-1",
  "heat_id": "heat-1",
  "service_history": [
    {
      "interval_id": "service-interval-1",
      "start_time_s": 0.0,
      "end_time_s": 1000.0,
      "minimum_temperature_K": 700.0,
      "maximum_temperature_K": 800.0,
      "environment_descriptor_id": "service-1",
      "service_record_digest": "5555555555555555555555555555555555555555555555555555555555555555",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller replica data",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "fields": [
    {
      "field_id": "f1",
      "replica_id": "replica-f1",
      "replica_site_id": "site-1",
      "sequence_index": 1,
      "configuration": {
        "surface_preparation_id": "prep-1",
        "surface_preparation_definition": "caller preparation",
        "replication_medium_id": "medium-1",
        "replication_medium_lot_id": "lot-1",
        "magnification": 500.0,
        "magnification_unit_token": "1",
        "instrument_id": "microscope-1",
        "instrument_revision": "1",
        "instrument_configuration_digest": "5555555555555555555555555555555555555555555555555555555555555555",
        "calibration_id": "cal-1",
        "calibration_revision": "1",
        "calibration_status": "valid",
        "calibration_record_digest": "5555555555555555555555555555555555555555555555555555555555555555",
        "invalid_or_missing_basis": null,
        "evidence": [
          {
            "source_id": "campaign",
            "origin": "measured",
            "citation": "caller replica data",
            "license_id": null,
            "sha256": null
          }
        ]
      },
      "image_digest": "5555555555555555555555555555555555555555555555555555555555555555",
      "field_record_digest": "5555555555555555555555555555555555555555555555555555555555555555",
      "observations": [
        {
          "observation_id": "cavity-density",
          "observation_kind": "cavity",
          "metric_id": "cavity_density",
          "metric_definition": "caller-reported cavity count density",
          "result_mode": "quantitative",
          "status": "reported",
          "value": 2.0,
          "expanded_uncertainty": 0.2,
          "unit_token": "1/mm^2",
          "qualitative_class": null,
          "qualitative_uncertainty_basis": null,
          "observer_id": "observer-1",
          "observation_record_digest": "5555555555555555555555555555555555555555555555555555555555555555",
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "campaign",
              "origin": "measured",
              "citation": "caller replica data",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "replicate_group_id": "rep-group",
      "source_group_id": "source-f1",
      "independence_group_id": "ind-1",
      "caller_validity_status": "valid",
      "caller_validity_basis": "caller reviewed field",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller replica data",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "field_id": "f2",
      "replica_id": "replica-f2",
      "replica_site_id": "site-1",
      "sequence_index": 2,
      "configuration": {
        "surface_preparation_id": "prep-1",
        "surface_preparation_definition": "caller preparation",
        "replication_medium_id": "medium-1",
        "replication_medium_lot_id": "lot-1",
        "magnification": 500.0,
        "magnification_unit_token": "1",
        "instrument_id": "microscope-1",
        "instrument_revision": "1",
        "instrument_configuration_digest": "5555555555555555555555555555555555555555555555555555555555555555",
        "calibration_id": "cal-1",
        "calibration_revision": "1",
        "calibration_status": "valid",
        "calibration_record_digest": "5555555555555555555555555555555555555555555555555555555555555555",
        "invalid_or_missing_basis": null,
        "evidence": [
          {
            "source_id": "campaign",
            "origin": "measured",
            "citation": "caller replica data",
            "license_id": null,
            "sha256": null
          }
        ]
      },
      "image_digest": "5555555555555555555555555555555555555555555555555555555555555555",
      "field_record_digest": "5555555555555555555555555555555555555555555555555555555555555555",
      "observations": [
        {
          "observation_id": "cavity-density",
          "observation_kind": "cavity",
          "metric_id": "cavity_density",
          "metric_definition": "caller-reported cavity count density",
          "result_mode": "quantitative",
          "status": "reported",
          "value": 2.0,
          "expanded_uncertainty": 0.2,
          "unit_token": "1/mm^2",
          "qualitative_class": null,
          "qualitative_uncertainty_basis": null,
          "observer_id": "observer-1",
          "observation_record_digest": "5555555555555555555555555555555555555555555555555555555555555555",
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "campaign",
              "origin": "measured",
              "citation": "caller replica data",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "replicate_group_id": "rep-group",
      "source_group_id": "source-f2",
      "independence_group_id": "ind-2",
      "caller_validity_status": "valid",
      "caller_validity_basis": "caller reviewed field",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller replica data",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "caller_profile": {
    "profile_id": "profile-1",
    "profile_revision": "1",
    "component_id": "component-1",
    "material_id": "material-1",
    "material_condition_id": "condition-1",
    "heat_id": "heat-1",
    "supported_replica_site_ids": [
      "site-1"
    ],
    "supported_environment_descriptor_ids": [
      "service-1"
    ],
    "required_surface_preparation_id": "prep-1",
    "required_replication_medium_id": "medium-1",
    "required_magnification": 500.0,
    "magnification_tolerance": 0.0,
    "required_instrument_id": "microscope-1",
    "required_calibration_id": "cal-1",
    "criteria": [
      {
        "criterion_id": "cavity-rule",
        "observation_kind": "cavity",
        "metric_id": "cavity_density",
        "metric_definition": "caller-reported cavity count density",
        "result_mode": "quantitative",
        "unit_token": "1/mm^2",
        "minimum_acceptable": null,
        "maximum_acceptable": 3.0,
        "accepted_qualitative_classes": [],
        "criterion_basis": "caller cavity criterion",
        "evidence": [
          {
            "source_id": "campaign",
            "origin": "measured",
            "citation": "caller replica data",
            "license_id": null,
            "sha256": null
          }
        ]
      }
    ],
    "minimum_valid_field_count": 2,
    "minimum_independence_group_count": 2,
    "caller_validity_policy_id": "validity-1",
    "profile_source_digest": "5555555555555555555555555555555555555555555555555555555555555555",
    "built_in_grade_table_used": false,
    "evidence": [
      {
        "source_id": "campaign",
        "origin": "measured",
        "citation": "caller replica data",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "component_location_material_heat_and_service_history_reviewed": true,
  "surface_preparation_medium_magnification_and_instrument_reviewed": true,
  "calibration_image_and_record_digests_reviewed": true,
  "observation_definitions_units_classes_and_uncertainties_reviewed": true,
  "replicate_source_and_independence_groups_reviewed": true,
  "caller_validity_flags_profile_and_missingness_reviewed": true,
  "evidence": [
    {
      "source_id": "campaign",
      "origin": "measured",
      "citation": "caller replica data",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/replica_metallography_campaign.py#L231)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

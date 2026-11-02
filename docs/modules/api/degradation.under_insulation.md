# `degradation.under_insulation`

**목적:** CUI scope, ordered access/inspection/repair events, explicit coverage and observations remain caller evidence.

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
| `scope` | 예 | `{"$ref": "#/$defs/CUIScopeIdentity"}` | 계약·필드 설명 참조 |
| `events` | 예 | `{"items": {"$ref": "#/$defs/CUIAccessInspectionRepairEvent"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `coverage_regions` | 예 | `{"items": {"$ref": "#/$defs/CUIAccessCoverageRegion"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/CUIObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_profile` | 예 | `{"$ref": "#/$defs/CUICallerProfile"}` | 계약·필드 설명 참조 |
| `zone_insulation_jacketing_coating_material_service_environment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `ordered_access_inspection_repair_events_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `access_coverage_regions_overlap_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `moisture_visual_thickness_nde_observations_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `locations_methods_units_uncertainty_and_findings_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `source_independence_provenance_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `invalid_and_missing_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/UnderInsulationCampaignAssessment.json)

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
| `corrosion_rate_or_remaining_life` | `1` |
| `hidden_area_extrapolated` | `1` |
| `risk_pod_or_standard_acceptance` | `1` |
| `report_digest` | `1` |
| `downstream_receipt` | `mixed` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- CUI scope, ordered access/inspection/repair events, explicit coverage and observations remain caller evidence.
- No hidden-area extrapolation, corrosion rate, life, risk, POD, or standard acceptance is produced.

## 구현 근거·독립 설명

- `authored_cui_inspection_evidence_campaign_audit`: Preserve caller-defined CUI scope, insulation, jacketing, coating, material, service and environment identities, ordered access, inspection, repair and reinstatement events, explicit coverage and moisture, visual, thickness or NDE observations. Apply only caller criteria; do not extrapolate hidden areas, infer corrosion rate, remaining life, POD, risk or standard acceptance.
- `authored_cui_digest_bound_downstream_evidence_receipt`: Create a compact downstream exchange record that binds reviewed CUI campaign outcome, accessed-area coverage, observation count and criterion outcomes to the assessment input and campaign report digests. The receipt does not infer corrosion rate, extrapolate hidden areas, or generate risk or failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.under_insulation"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.under_insulation"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "campaign_id": "campaign-1",
  "scope": {
    "zone_id": "zone-1",
    "component_or_circuit_id": "circuit-1",
    "physical_scope_definition": "caller insulated piping zone",
    "coordinate_frame_id": "frame-1",
    "substrate_material_id": "material-1",
    "substrate_material_condition_id": "condition-1",
    "service_id": "service-1",
    "service_medium_definition": "caller service medium",
    "minimum_service_temperature_K": 300.0,
    "maximum_service_temperature_K": 400.0,
    "insulation_system_id": "insulation-1",
    "insulation_material_id": "insulation-material-1",
    "insulation_condition_id": "insulation-before-access",
    "jacketing_system_id": "jacketing-1",
    "jacketing_condition_id": "jacketing-before-access",
    "coating_system_id": "coating-1",
    "coating_condition_id": "coating-before-access",
    "external_environment_id": "environment-1",
    "external_environment_definition": "caller outdoor environment",
    "scope_configuration_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored CUI campaign",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "events": [
    {
      "event_id": "event-access",
      "sequence_index": 0,
      "event_kind": "access",
      "start_time_s": 0.0,
      "end_time_s": 100.0,
      "contractor_or_provider_id": "provider-1",
      "procedure_id": "procedure-access",
      "activity_definition": "caller access activity",
      "resulting_insulation_condition_id": null,
      "resulting_jacketing_condition_id": null,
      "resulting_coating_condition_id": null,
      "event_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "event_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored CUI campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "event-inspection",
      "sequence_index": 1,
      "event_kind": "inspection",
      "start_time_s": 100.0,
      "end_time_s": 200.0,
      "contractor_or_provider_id": "provider-1",
      "procedure_id": "procedure-inspection",
      "activity_definition": "caller inspection activity",
      "resulting_insulation_condition_id": null,
      "resulting_jacketing_condition_id": null,
      "resulting_coating_condition_id": null,
      "event_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "event_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored CUI campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "event-repair",
      "sequence_index": 2,
      "event_kind": "repair",
      "start_time_s": 200.0,
      "end_time_s": 300.0,
      "contractor_or_provider_id": "provider-1",
      "procedure_id": "procedure-repair",
      "activity_definition": "caller repair activity",
      "resulting_insulation_condition_id": "insulation-repaired",
      "resulting_jacketing_condition_id": "jacketing-repaired",
      "resulting_coating_condition_id": "coating-repaired",
      "event_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "event_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored CUI campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "coverage_regions": [
    {
      "access_region_id": "region-1",
      "access_event_id": "event-access",
      "physical_location_definition": "caller zone segment one",
      "coordinate_frame_id": "frame-1",
      "target_extent": 100.0,
      "accessed_extent": 80.0,
      "extent_unit_token": "m2",
      "coverage_uncertainty": 1.0,
      "overlap_group_id": "nonoverlap-group-1",
      "unaccessed_basis": "insulation not removed in remaining area",
      "coverage_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored CUI campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "observation-0",
      "inspection_event_id": "event-inspection",
      "access_region_id": "region-1",
      "observation_category": "moisture",
      "physical_location_definition": "caller point 0 inside accessed region",
      "coordinate_frame_id": "frame-1",
      "orientation_definition": "surface normal",
      "method_id": "method-moisture",
      "method_revision": "rev-1",
      "metric_id": "moisture_fraction",
      "metric_definition": "caller definition for moisture_fraction",
      "value": 0.1,
      "unit_token": "1",
      "expanded_uncertainty": 0.1,
      "uncertainty_basis": "caller uncertainty budget",
      "reported_finding": "caller-reported moisture finding",
      "caller_disposition_id": null,
      "source_group_id": "source-group-0",
      "independence_group_id": "independence-group-0",
      "provider_id": "inspection-provider",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "raw_data_digest": "0000000000000000000000000000000000000000000000000000000000000000",
      "observation_record_digest": "8888888888888888888888888888888888888888888888888888888888888888",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored CUI campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-1",
      "inspection_event_id": "event-inspection",
      "access_region_id": "region-1",
      "observation_category": "visual",
      "physical_location_definition": "caller point 1 inside accessed region",
      "coordinate_frame_id": "frame-1",
      "orientation_definition": "surface normal",
      "method_id": "method-visual",
      "method_revision": "rev-1",
      "metric_id": null,
      "metric_definition": null,
      "value": null,
      "unit_token": null,
      "expanded_uncertainty": null,
      "uncertainty_basis": null,
      "reported_finding": "caller-reported visual finding",
      "caller_disposition_id": null,
      "source_group_id": "source-group-1",
      "independence_group_id": "independence-group-1",
      "provider_id": "inspection-provider",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "raw_data_digest": "1111111111111111111111111111111111111111111111111111111111111111",
      "observation_record_digest": "9999999999999999999999999999999999999999999999999999999999999999",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored CUI campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-2",
      "inspection_event_id": "event-inspection",
      "access_region_id": "region-1",
      "observation_category": "thickness",
      "physical_location_definition": "caller point 2 inside accessed region",
      "coordinate_frame_id": "frame-1",
      "orientation_definition": "surface normal",
      "method_id": "method-thickness",
      "method_revision": "rev-1",
      "metric_id": "remaining_thickness",
      "metric_definition": "caller definition for remaining_thickness",
      "value": 9.0,
      "unit_token": "mm",
      "expanded_uncertainty": 0.1,
      "uncertainty_basis": "caller uncertainty budget",
      "reported_finding": "caller-reported thickness finding",
      "caller_disposition_id": null,
      "source_group_id": "source-group-2",
      "independence_group_id": "independence-group-2",
      "provider_id": "inspection-provider",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "raw_data_digest": "2222222222222222222222222222222222222222222222222222222222222222",
      "observation_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored CUI campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-3",
      "inspection_event_id": "event-inspection",
      "access_region_id": "region-1",
      "observation_category": "nde",
      "physical_location_definition": "caller point 3 inside accessed region",
      "coordinate_frame_id": "frame-1",
      "orientation_definition": "surface normal",
      "method_id": "method-nde",
      "method_revision": "rev-1",
      "metric_id": null,
      "metric_definition": null,
      "value": null,
      "unit_token": null,
      "expanded_uncertainty": null,
      "uncertainty_basis": null,
      "reported_finding": "caller-reported nde finding",
      "caller_disposition_id": null,
      "source_group_id": "source-group-3",
      "independence_group_id": "independence-group-3",
      "provider_id": "inspection-provider",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "raw_data_digest": "3333333333333333333333333333333333333333333333333333333333333333",
      "observation_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored CUI campaign",
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
      "access",
      "inspection",
      "repair"
    ],
    "required_observation_categories": [
      "moisture",
      "visual",
      "thickness",
      "nde"
    ],
    "criteria": [
      {
        "criterion_id": "coverage-criterion",
        "criterion_source": "campaign",
        "campaign_metric": "coverage_fraction",
        "observation_category": null,
        "observation_metric_id": null,
        "aggregation": "minimum",
        "direction": "minimum",
        "accept_limit": 0.8,
        "reject_limit": 0.5,
        "unit_token": "1",
        "criterion_basis": "caller CUI coverage criterion"
      },
      {
        "criterion_id": "thickness-criterion",
        "criterion_source": "observation",
        "campaign_metric": null,
        "observation_category": "thickness",
        "observation_metric_id": "remaining_thickness",
        "aggregation": "minimum",
        "direction": "minimum",
        "accept_limit": 8.0,
        "reject_limit": 6.0,
        "unit_token": "mm",
        "criterion_basis": "caller measured-thickness criterion"
      }
    ],
    "profile_provider_id": "caller-provider",
    "profile_revision": "rev-1",
    "profile_configuration_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "caller_acceptance_authority": "caller CUI review group",
    "corrosion_rate_inference_claimed": false,
    "remaining_life_claimed": false,
    "hidden_area_extrapolation_claimed": false,
    "risk_or_pod_claimed": false,
    "built_in_code_or_standard_acceptance_used": false,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored CUI campaign",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "zone_insulation_jacketing_coating_material_service_environment_reviewed": true,
  "ordered_access_inspection_repair_events_reviewed": true,
  "access_coverage_regions_overlap_and_units_reviewed": true,
  "moisture_visual_thickness_nde_observations_reviewed": true,
  "locations_methods_units_uncertainty_and_findings_reviewed": true,
  "source_independence_provenance_and_digests_reviewed": true,
  "caller_profile_reviewed": true,
  "invalid_and_missing_records_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored CUI campaign",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/under_insulation_campaign.py#L413)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

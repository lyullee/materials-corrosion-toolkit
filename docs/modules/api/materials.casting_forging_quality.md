# `materials.casting_forging_quality`

**목적:** Product, heat, route, process, heat treatment, sampling and observation evidence remains caller supplied.

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
| `products` | 예 | `{"items": {"$ref": "#/$defs/ManufacturedProductEvidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `samples` | 예 | `{"items": {"$ref": "#/$defs/ProductSampleEvidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/ProductQualityObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_profile` | 예 | `{"$ref": "#/$defs/CastingForgingCallerProfile"}` | 계약·필드 설명 참조 |
| `product_heat_route_and_process_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `forging_ratio_or_casting_process_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `heat_treatment_sequence_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sampling_location_orientation_and_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_method_units_uncertainty_and_findings_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `replicate_source_and_independence_claims_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_provenance_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `invalid_and_missing_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CastingForgingQualityCampaignAssessment.json)

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
| `specification_or_forging_ratio_limit_embedded` | `1` |
| `automatic_defect_acceptance` | `1` |
| `material_qualification` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Product, heat, route, process, heat treatment, sampling and observation evidence remains caller supplied.
- No embedded specification, forging ratio minimum, defect acceptance, or material qualification is produced.

## 구현 근거·독립 설명

- `authored_casting_forging_quality_campaign_audit`: Preserve caller-supplied product, heat, material, manufacturing route, forging-ratio definition or casting process, ordered heat treatment, sample location and orientation, and dimensional, surface, internal, NDE, macro, micro, chemistry or mechanical observations with uncertainty and independence lineage. Apply only caller-authored criteria. Do not embed minimum forging ratios, defect limits, code tables or material qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "materials.casting_forging_quality"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["materials.casting_forging_quality"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "campaign_id": "campaign-1",
  "products": [
    {
      "product_id": "product-1",
      "product_kind": "forging",
      "heat_id": "heat-1",
      "material_id": "material-1",
      "material_condition_id": "condition-1",
      "product_form_descriptor": "caller forging product form",
      "manufacturing_route_id": "route-1",
      "manufacturing_route_revision": "rev-1",
      "route_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "forging_ratio": 3.0,
      "forging_ratio_definition": "caller area-ratio definition",
      "forging_ratio_unit_token": "1",
      "casting_process_id": null,
      "casting_process_definition": null,
      "heat_treatments": [
        {
          "treatment_id": "treatment-1",
          "sequence_index": 0,
          "treatment_type": "caller heat-treatment description",
          "furnace_or_provider_id": "furnace-1",
          "start_time_s": 0.0,
          "end_time_s": 3600.0,
          "minimum_recorded_temperature_K": 1000.0,
          "maximum_recorded_temperature_K": 1010.0,
          "temperature_uncertainty_K": 2.0,
          "cooling_route_definition": "caller controlled cooling route",
          "controller_data_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "treatment_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored quality campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "product_record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored quality campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "product_id": "product-2",
      "product_kind": "casting",
      "heat_id": "heat-2",
      "material_id": "material-1",
      "material_condition_id": "condition-1",
      "product_form_descriptor": "caller casting product form",
      "manufacturing_route_id": "route-2",
      "manufacturing_route_revision": "rev-1",
      "route_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "forging_ratio": null,
      "forging_ratio_definition": null,
      "forging_ratio_unit_token": null,
      "casting_process_id": "casting-process-1",
      "casting_process_definition": "caller casting process description",
      "heat_treatments": [
        {
          "treatment_id": "treatment-2",
          "sequence_index": 0,
          "treatment_type": "caller heat-treatment description",
          "furnace_or_provider_id": "furnace-1",
          "start_time_s": 0.0,
          "end_time_s": 3600.0,
          "minimum_recorded_temperature_K": 1000.0,
          "maximum_recorded_temperature_K": 1010.0,
          "temperature_uncertainty_K": 2.0,
          "cooling_route_definition": "caller controlled cooling route",
          "controller_data_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "treatment_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored quality campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "product_record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored quality campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "samples": [
    {
      "sample_id": "sample-1",
      "product_id": "product-1",
      "sampling_plan_id": "sampling-plan-1",
      "physical_location_definition": "caller location 1",
      "orientation_id": "longitudinal",
      "thickness_or_depth_coordinate": 0.5,
      "coordinate_unit_token": "fraction",
      "replicate_group_id": "replicate-group-1",
      "source_group_id": "source-group-1",
      "independence_group_id": "independence-group-1",
      "sampling_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored quality campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "sample_id": "sample-2",
      "product_id": "product-2",
      "sampling_plan_id": "sampling-plan-1",
      "physical_location_definition": "caller location 2",
      "orientation_id": "longitudinal",
      "thickness_or_depth_coordinate": 0.5,
      "coordinate_unit_token": "fraction",
      "replicate_group_id": "replicate-group-1",
      "source_group_id": "source-group-2",
      "independence_group_id": "independence-group-2",
      "sampling_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored quality campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "observation-0",
      "product_id": "product-1",
      "sample_id": "sample-1",
      "observation_category": "dimensional",
      "examination_or_test_method_id": "method-dimensional",
      "method_revision": "rev-1",
      "metric_id": "dimension_deviation",
      "metric_definition": "caller definition for dimension_deviation",
      "value": 0.2,
      "unit_token": "mm",
      "expanded_uncertainty": 5.0,
      "uncertainty_basis": "caller uncertainty budget",
      "reported_finding": "caller-reported dimensional finding",
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "raw_data_digest": "0000000000000000000000000000000000000000000000000000000000000000",
      "observation_record_digest": "8888888888888888888888888888888888888888888888888888888888888888",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored quality campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-1",
      "product_id": "product-1",
      "sample_id": "sample-1",
      "observation_category": "surface",
      "examination_or_test_method_id": "method-surface",
      "method_revision": "rev-1",
      "metric_id": null,
      "metric_definition": null,
      "value": null,
      "unit_token": null,
      "expanded_uncertainty": null,
      "uncertainty_basis": null,
      "reported_finding": "caller-reported surface finding",
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "raw_data_digest": "1111111111111111111111111111111111111111111111111111111111111111",
      "observation_record_digest": "9999999999999999999999999999999999999999999999999999999999999999",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored quality campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-2",
      "product_id": "product-1",
      "sample_id": "sample-1",
      "observation_category": "internal",
      "examination_or_test_method_id": "method-internal",
      "method_revision": "rev-1",
      "metric_id": null,
      "metric_definition": null,
      "value": null,
      "unit_token": null,
      "expanded_uncertainty": null,
      "uncertainty_basis": null,
      "reported_finding": "caller-reported internal finding",
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "raw_data_digest": "2222222222222222222222222222222222222222222222222222222222222222",
      "observation_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored quality campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-3",
      "product_id": "product-1",
      "sample_id": "sample-1",
      "observation_category": "nde",
      "examination_or_test_method_id": "method-nde",
      "method_revision": "rev-1",
      "metric_id": null,
      "metric_definition": null,
      "value": null,
      "unit_token": null,
      "expanded_uncertainty": null,
      "uncertainty_basis": null,
      "reported_finding": "caller-reported nde finding",
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "raw_data_digest": "3333333333333333333333333333333333333333333333333333333333333333",
      "observation_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored quality campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-4",
      "product_id": "product-1",
      "sample_id": "sample-1",
      "observation_category": "macro",
      "examination_or_test_method_id": "method-macro",
      "method_revision": "rev-1",
      "metric_id": null,
      "metric_definition": null,
      "value": null,
      "unit_token": null,
      "expanded_uncertainty": null,
      "uncertainty_basis": null,
      "reported_finding": "caller-reported macro finding",
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "raw_data_digest": "4444444444444444444444444444444444444444444444444444444444444444",
      "observation_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored quality campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-5",
      "product_id": "product-1",
      "sample_id": "sample-1",
      "observation_category": "micro",
      "examination_or_test_method_id": "method-micro",
      "method_revision": "rev-1",
      "metric_id": null,
      "metric_definition": null,
      "value": null,
      "unit_token": null,
      "expanded_uncertainty": null,
      "uncertainty_basis": null,
      "reported_finding": "caller-reported micro finding",
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "raw_data_digest": "5555555555555555555555555555555555555555555555555555555555555555",
      "observation_record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored quality campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-6",
      "product_id": "product-1",
      "sample_id": "sample-1",
      "observation_category": "chemistry",
      "examination_or_test_method_id": "method-chemistry",
      "method_revision": "rev-1",
      "metric_id": "element_fraction",
      "metric_definition": "caller definition for element_fraction",
      "value": 0.1,
      "unit_token": "%",
      "expanded_uncertainty": 5.0,
      "uncertainty_basis": "caller uncertainty budget",
      "reported_finding": "caller-reported chemistry finding",
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "raw_data_digest": "6666666666666666666666666666666666666666666666666666666666666666",
      "observation_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored quality campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-7",
      "product_id": "product-1",
      "sample_id": "sample-1",
      "observation_category": "mechanical",
      "examination_or_test_method_id": "method-mechanical",
      "method_revision": "rev-1",
      "metric_id": "yield_strength",
      "metric_definition": "caller definition for yield_strength",
      "value": 450.0,
      "unit_token": "MPa",
      "expanded_uncertainty": 5.0,
      "uncertainty_basis": "caller uncertainty budget",
      "reported_finding": "caller-reported mechanical finding",
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "raw_data_digest": "7777777777777777777777777777777777777777777777777777777777777777",
      "observation_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored quality campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "caller_profile": {
    "profile_id": "profile-1",
    "profile_version": "1.0.0",
    "required_product_kinds": [
      "forging",
      "casting"
    ],
    "required_observation_categories": [
      "dimensional",
      "surface",
      "internal",
      "nde",
      "macro",
      "micro",
      "chemistry",
      "mechanical"
    ],
    "criteria": [
      {
        "criterion_id": "sample-count",
        "criterion_source": "campaign",
        "campaign_metric": "sample_count",
        "observation_category": null,
        "observation_metric_id": null,
        "aggregation": "minimum",
        "direction": "minimum",
        "accept_limit": 2.0,
        "reject_limit": 1.0,
        "unit_token": "count",
        "criterion_basis": "caller-authored quality criterion"
      },
      {
        "criterion_id": "independent-count",
        "criterion_source": "campaign",
        "campaign_metric": "independent_source_group_count",
        "observation_category": null,
        "observation_metric_id": null,
        "aggregation": "minimum",
        "direction": "minimum",
        "accept_limit": 2.0,
        "reject_limit": 1.0,
        "unit_token": "count",
        "criterion_basis": "caller-authored quality criterion"
      },
      {
        "criterion_id": "strength-criterion",
        "criterion_source": "observation",
        "campaign_metric": null,
        "observation_category": "mechanical",
        "observation_metric_id": "yield_strength",
        "aggregation": "minimum",
        "direction": "minimum",
        "accept_limit": 400.0,
        "reject_limit": 300.0,
        "unit_token": "MPa",
        "criterion_basis": "caller-authored strength criterion"
      }
    ],
    "profile_provider_id": "caller-provider",
    "profile_revision": "rev-1",
    "profile_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "caller_acceptance_authority": "caller material review group",
    "built_in_specification_table_used": false,
    "minimum_forging_ratio_embedded": false,
    "allowable_defect_rule_embedded": false,
    "material_qualification_claimed": false,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored quality campaign",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "product_heat_route_and_process_identity_reviewed": true,
  "forging_ratio_or_casting_process_basis_reviewed": true,
  "heat_treatment_sequence_and_digests_reviewed": true,
  "sampling_location_orientation_and_groups_reviewed": true,
  "observation_method_units_uncertainty_and_findings_reviewed": true,
  "replicate_source_and_independence_claims_reviewed": true,
  "provider_provenance_and_digests_reviewed": true,
  "caller_profile_reviewed": true,
  "invalid_and_missing_records_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored quality campaign",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/casting_forging_quality_campaign.py#L313)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

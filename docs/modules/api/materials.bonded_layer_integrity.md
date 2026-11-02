# `materials.bonded_layer_integrity`

**목적:** Substrate, layer, lots, interface, geometry, process history, samples and observations remain caller evidence.

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
| `assemblies` | 예 | `{"items": {"$ref": "#/$defs/BondedAssemblyEvidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `samples` | 예 | `{"items": {"$ref": "#/$defs/BondedLayerSample"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/BondedLayerObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_profile` | 예 | `{"$ref": "#/$defs/BondedLayerCallerProfile"}` | 계약·필드 설명 참조 |
| `substrate_layer_lot_interface_and_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `bond_process_provider_route_and_order_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `process_time_temperature_pressure_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sampling_location_orientation_and_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_method_units_uncertainty_and_findings_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `replicate_source_and_independence_claims_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_provenance_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `invalid_and_missing_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/BondedLayerIntegrityCampaignAssessment.json)

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
| `automatic_failure_mechanism` | `1` |
| `service_life_or_specification_acceptance` | `1` |
| `physical_qualification` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Substrate, layer, lots, interface, geometry, process history, samples and observations remain caller evidence.
- No automatic mechanism classification, specification acceptance, service life, or qualification is produced.

## 구현 근거·독립 설명

- `authored_bonded_layer_integrity_campaign_audit`: Preserve caller-supplied substrate, layer, material lot, interface geometry, coordinate frame, bond process, ordered preparation-application-cure-heat history, sample identity, and thickness, adhesion, shear, peel, porosity, disbond, continuity or NDE evidence with uncertainty and independence lineage. Apply only caller-authored criteria. Do not automatically classify cohesive or adhesive failure, embed standard acceptance, predict life or claim qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "materials.bonded_layer_integrity"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["materials.bonded_layer_integrity"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "campaign_id": "campaign-1",
  "assemblies": [
    {
      "assembly_id": "assembly-1",
      "product_id": "product-1",
      "substrate_id": "substrate-1",
      "substrate_material_id": "substrate-material-1",
      "substrate_material_lot_id": "substrate-lot-1",
      "substrate_condition_id": "substrate-condition-1",
      "layer_id": "layer-1",
      "layer_material_id": "layer-material-1",
      "layer_material_lot_id": "layer-lot-1",
      "layer_condition_id": "layer-condition-1",
      "interface_id": "interface-1",
      "interface_definition": "caller substrate-to-layer interface definition",
      "bond_process_id": "bond-process-1",
      "bond_process_revision": "rev-1",
      "bond_process_provider_id": "provider-1",
      "bond_process_route_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "geometry": {
        "geometry_id": "geometry-1",
        "substrate_thickness": 10.0,
        "layer_nominal_thickness": 1.0,
        "bonded_area": 100.0,
        "thickness_unit_token": "mm",
        "area_unit_token": "cm2",
        "geometry_uncertainty": 0.05,
        "coordinate_frame_id": "frame-1",
        "geometry_record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
      },
      "process_events": [
        {
          "event_id": "event-0",
          "sequence_index": 0,
          "process_kind": "surface_preparation",
          "process_step_id": "step-0",
          "start_time_s": 0.0,
          "end_time_s": 100.0,
          "minimum_recorded_temperature_K": 290.0,
          "maximum_recorded_temperature_K": 300.0,
          "expanded_temperature_uncertainty_K": 1.0,
          "applied_pressure": null,
          "pressure_unit_token": null,
          "expanded_pressure_uncertainty": null,
          "process_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "process_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored bonded-layer campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "event_id": "event-1",
          "sequence_index": 1,
          "process_kind": "layer_application",
          "process_step_id": "step-1",
          "start_time_s": 100.0,
          "end_time_s": 200.0,
          "minimum_recorded_temperature_K": 291.0,
          "maximum_recorded_temperature_K": 301.0,
          "expanded_temperature_uncertainty_K": 1.0,
          "applied_pressure": null,
          "pressure_unit_token": null,
          "expanded_pressure_uncertainty": null,
          "process_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "process_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored bonded-layer campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "event_id": "event-2",
          "sequence_index": 2,
          "process_kind": "bonding",
          "process_step_id": "step-2",
          "start_time_s": 200.0,
          "end_time_s": 300.0,
          "minimum_recorded_temperature_K": 292.0,
          "maximum_recorded_temperature_K": 302.0,
          "expanded_temperature_uncertainty_K": 1.0,
          "applied_pressure": 1.0,
          "pressure_unit_token": "MPa",
          "expanded_pressure_uncertainty": 0.05,
          "process_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "process_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored bonded-layer campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "event_id": "event-3",
          "sequence_index": 3,
          "process_kind": "heat_treatment",
          "process_step_id": "step-3",
          "start_time_s": 300.0,
          "end_time_s": 400.0,
          "minimum_recorded_temperature_K": 293.0,
          "maximum_recorded_temperature_K": 303.0,
          "expanded_temperature_uncertainty_K": 1.0,
          "applied_pressure": null,
          "pressure_unit_token": null,
          "expanded_pressure_uncertainty": null,
          "process_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "process_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored bonded-layer campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "assembly_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored bonded-layer campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "samples": [
    {
      "sample_id": "sample-1",
      "assembly_id": "assembly-1",
      "interface_id": "interface-1",
      "sampling_plan_id": "sampling-plan-1",
      "physical_location_definition": "caller reviewed center location",
      "orientation_id": "normal-to-interface",
      "coordinate_frame_id": "frame-1",
      "replicate_group_id": "replicate-group-1",
      "source_group_id": "source-group-1",
      "independence_group_id": "independence-group-1",
      "sampling_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored bonded-layer campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "observation-0",
      "assembly_id": "assembly-1",
      "sample_id": "sample-1",
      "interface_id": "interface-1",
      "observation_category": "thickness",
      "test_or_examination_method_id": "method-thickness",
      "method_revision": "rev-1",
      "metric_id": "layer_thickness",
      "metric_definition": "caller definition for layer_thickness",
      "value": 1.0,
      "unit_token": "mm",
      "expanded_uncertainty": 0.1,
      "uncertainty_basis": "caller uncertainty budget",
      "reported_finding": "caller-reported thickness finding",
      "caller_reported_failure_descriptor": null,
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "raw_data_digest": "0000000000000000000000000000000000000000000000000000000000000000",
      "observation_record_digest": "8888888888888888888888888888888888888888888888888888888888888888",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored bonded-layer campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-1",
      "assembly_id": "assembly-1",
      "sample_id": "sample-1",
      "interface_id": "interface-1",
      "observation_category": "adhesion",
      "test_or_examination_method_id": "method-adhesion",
      "method_revision": "rev-1",
      "metric_id": "adhesion_strength",
      "metric_definition": "caller definition for adhesion_strength",
      "value": 6.0,
      "unit_token": "MPa",
      "expanded_uncertainty": 0.1,
      "uncertainty_basis": "caller uncertainty budget",
      "reported_finding": "caller-reported adhesion finding",
      "caller_reported_failure_descriptor": "caller descriptor retained",
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "raw_data_digest": "1111111111111111111111111111111111111111111111111111111111111111",
      "observation_record_digest": "9999999999999999999999999999999999999999999999999999999999999999",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored bonded-layer campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-2",
      "assembly_id": "assembly-1",
      "sample_id": "sample-1",
      "interface_id": "interface-1",
      "observation_category": "shear",
      "test_or_examination_method_id": "method-shear",
      "method_revision": "rev-1",
      "metric_id": "shear_strength",
      "metric_definition": "caller definition for shear_strength",
      "value": 10.0,
      "unit_token": "MPa",
      "expanded_uncertainty": 0.1,
      "uncertainty_basis": "caller uncertainty budget",
      "reported_finding": "caller-reported shear finding",
      "caller_reported_failure_descriptor": null,
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "raw_data_digest": "2222222222222222222222222222222222222222222222222222222222222222",
      "observation_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored bonded-layer campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-3",
      "assembly_id": "assembly-1",
      "sample_id": "sample-1",
      "interface_id": "interface-1",
      "observation_category": "peel",
      "test_or_examination_method_id": "method-peel",
      "method_revision": "rev-1",
      "metric_id": "peel_force",
      "metric_definition": "caller definition for peel_force",
      "value": 20.0,
      "unit_token": "N/mm",
      "expanded_uncertainty": 0.1,
      "uncertainty_basis": "caller uncertainty budget",
      "reported_finding": "caller-reported peel finding",
      "caller_reported_failure_descriptor": null,
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "raw_data_digest": "3333333333333333333333333333333333333333333333333333333333333333",
      "observation_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored bonded-layer campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-4",
      "assembly_id": "assembly-1",
      "sample_id": "sample-1",
      "interface_id": "interface-1",
      "observation_category": "porosity",
      "test_or_examination_method_id": "method-porosity",
      "method_revision": "rev-1",
      "metric_id": "porosity_fraction",
      "metric_definition": "caller definition for porosity_fraction",
      "value": 0.01,
      "unit_token": "1",
      "expanded_uncertainty": 0.1,
      "uncertainty_basis": "caller uncertainty budget",
      "reported_finding": "caller-reported porosity finding",
      "caller_reported_failure_descriptor": null,
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "raw_data_digest": "4444444444444444444444444444444444444444444444444444444444444444",
      "observation_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored bonded-layer campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-5",
      "assembly_id": "assembly-1",
      "sample_id": "sample-1",
      "interface_id": "interface-1",
      "observation_category": "disbond",
      "test_or_examination_method_id": "method-disbond",
      "method_revision": "rev-1",
      "metric_id": "disbond_area_fraction",
      "metric_definition": "caller definition for disbond_area_fraction",
      "value": 0.0,
      "unit_token": "1",
      "expanded_uncertainty": 0.1,
      "uncertainty_basis": "caller uncertainty budget",
      "reported_finding": "caller-reported disbond finding",
      "caller_reported_failure_descriptor": null,
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "raw_data_digest": "5555555555555555555555555555555555555555555555555555555555555555",
      "observation_record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored bonded-layer campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-6",
      "assembly_id": "assembly-1",
      "sample_id": "sample-1",
      "interface_id": "interface-1",
      "observation_category": "continuity",
      "test_or_examination_method_id": "method-continuity",
      "method_revision": "rev-1",
      "metric_id": null,
      "metric_definition": null,
      "value": null,
      "unit_token": null,
      "expanded_uncertainty": null,
      "uncertainty_basis": null,
      "reported_finding": "caller-reported continuity finding",
      "caller_reported_failure_descriptor": null,
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "raw_data_digest": "6666666666666666666666666666666666666666666666666666666666666666",
      "observation_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored bonded-layer campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "observation_id": "observation-7",
      "assembly_id": "assembly-1",
      "sample_id": "sample-1",
      "interface_id": "interface-1",
      "observation_category": "nde",
      "test_or_examination_method_id": "method-nde",
      "method_revision": "rev-1",
      "metric_id": null,
      "metric_definition": null,
      "value": null,
      "unit_token": null,
      "expanded_uncertainty": null,
      "uncertainty_basis": null,
      "reported_finding": "caller-reported nde finding",
      "caller_reported_failure_descriptor": null,
      "caller_disposition_id": null,
      "provider_id": "provider-1",
      "provider_revision": "rev-1",
      "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "raw_data_digest": "7777777777777777777777777777777777777777777777777777777777777777",
      "observation_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored bonded-layer campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "caller_profile": {
    "profile_id": "profile-1",
    "profile_version": "1.0.0",
    "required_process_kinds": [
      "surface_preparation",
      "layer_application",
      "bonding",
      "heat_treatment"
    ],
    "required_observation_categories": [
      "thickness",
      "adhesion",
      "shear",
      "peel",
      "porosity",
      "disbond",
      "continuity",
      "nde"
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
        "accept_limit": 1.0,
        "reject_limit": 0.0,
        "unit_token": "count",
        "criterion_basis": "caller campaign coverage criterion"
      },
      {
        "criterion_id": "adhesion-strength",
        "criterion_source": "observation",
        "campaign_metric": null,
        "observation_category": "adhesion",
        "observation_metric_id": "adhesion_strength",
        "aggregation": "minimum",
        "direction": "minimum",
        "accept_limit": 5.0,
        "reject_limit": 3.0,
        "unit_token": "MPa",
        "criterion_basis": "caller-authored adhesion criterion"
      }
    ],
    "profile_provider_id": "caller-provider",
    "profile_revision": "rev-1",
    "profile_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "caller_acceptance_authority": "caller bonded-layer review group",
    "built_in_code_or_specification_limits_used": false,
    "automatic_cohesive_or_adhesive_mechanism_claimed": false,
    "service_life_claimed": false,
    "physical_qualification_claimed": false,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored bonded-layer campaign",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "substrate_layer_lot_interface_and_geometry_reviewed": true,
  "bond_process_provider_route_and_order_reviewed": true,
  "process_time_temperature_pressure_and_digests_reviewed": true,
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
      "citation": "authored bonded-layer campaign",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/bonded_layer_integrity_campaign.py#L344)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

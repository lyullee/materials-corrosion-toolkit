# `inspection.test_water_quality`

**목적:** Source, batch, circuit, contact, history, sampling, laboratory and exact analytical identities are preserved.

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
| `circuit_identity` | 예 | `{"$ref": "#/$defs/TestWaterCircuitIdentity"}` | 계약·필드 설명 참조 |
| `history` | 예 | `{"items": {"$ref": "#/$defs/TestWaterHistoryEvent"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `samples` | 예 | `{"items": {"$ref": "#/$defs/TestWaterSample"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_profile` | 예 | `{"$ref": "#/$defs/TestWaterCallerProfile"}` | 계약·필드 설명 참조 |
| `source_batch_tank_circuit_material_contact_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `ordered_fill_hold_drain_dry_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sampling_time_location_method_lab_and_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `analyte_species_units_uncertainty_and_methods_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `replicate_source_and_independence_claims_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_provenance_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `invalid_and_missing_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TestWaterQualityCampaignAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `report_schema_version` | `1` |
| `assessment_id` | `1` |
| `campaign_id` | `1` |
| `campaign_outcome` | `1` |
| `caller_profile_id` | `1` |
| `analyte_metric_values` | `exact caller units` |
| `criterion_findings` | `mixed` |
| `diagnostics` | `mixed` |
| `input_digest` | `1` |
| `caller_profile_only` | `1` |
| `chemical_species_converted` | `1` |
| `corrosion_rate_or_microbiological_risk_inferred` | `1` |
| `automatic_standard_acceptance` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Source, batch, circuit, contact, history, sampling, laboratory and exact analytical identities are preserved.
- No species conversion, corrosion-rate/MIC-risk inference, standard limit, or automatic acceptance is produced.

## 구현 근거·독립 설명

- `authored_test_water_quality_campaign_audit`: Preserve caller-supplied water source, batch, tank, circuit, contact material, ordered fill-hold-drain-dry history, sample identity and calibrated pH, conductivity, chloride, halide, oxygen, solids, microbiology, inhibitor or temperature results with exact species definition, unit, uncertainty and independence lineage. Apply only caller-authored criteria. Do not convert species, infer corrosion rate or MIC risk, embed limits or automatically accept water quality.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.test_water_quality"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.test_water_quality"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "campaign_id": "campaign-1",
  "circuit_identity": {
    "source_id": "source-1",
    "water_batch_id": "water-batch-1",
    "source_type_descriptor": "caller supplied source water",
    "tank_id": "tank-1",
    "circuit_id": "circuit-1",
    "circuit_scope_definition": "caller hydrotest circuit boundary",
    "contacted_material_ids": [
      "material-1",
      "material-2"
    ],
    "contact_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "source_batch_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored water campaign",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "history": [
    {
      "event_id": "event-fill",
      "sequence_index": 0,
      "event_kind": "fill",
      "state_definition": "caller fill state definition",
      "start_time_s": 0.0,
      "end_time_s": 100.0,
      "water_batch_id": "water-batch-1",
      "event_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "event_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored water campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "event-hold",
      "sequence_index": 1,
      "event_kind": "hold",
      "state_definition": "caller hold state definition",
      "start_time_s": 100.0,
      "end_time_s": 200.0,
      "water_batch_id": "water-batch-1",
      "event_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "event_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored water campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "event-drain",
      "sequence_index": 2,
      "event_kind": "drain",
      "state_definition": "caller drain state definition",
      "start_time_s": 200.0,
      "end_time_s": 300.0,
      "water_batch_id": "water-batch-1",
      "event_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "event_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored water campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "event_id": "event-dry",
      "sequence_index": 3,
      "event_kind": "dry",
      "state_definition": "caller dry state definition",
      "start_time_s": 300.0,
      "end_time_s": 400.0,
      "water_batch_id": null,
      "event_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "event_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored water campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "samples": [
    {
      "sample_id": "sample-1",
      "event_id": "event-hold",
      "sampling_time_s": 150.0,
      "sampling_location_id": "outlet-1",
      "sampling_location_definition": "caller circuit outlet sample point",
      "sampling_method_id": "sampling-method-1",
      "laboratory_id": "laboratory-1",
      "calibration_id": "calibration-1",
      "calibration_valid": true,
      "invalid_calibration_basis": null,
      "calibration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "replicate_group_id": "replicate-group-1",
      "source_group_id": "source-group-1",
      "independence_group_id": "independence-group-1",
      "results": [
        {
          "result_id": "result-0",
          "sample_id": "sample-1",
          "analyte": "ph",
          "species_or_quantity_definition": "hydrogen-ion activity pH",
          "value": 7.0,
          "unit_token": "1",
          "expanded_uncertainty": 0.1,
          "uncertainty_basis": "caller laboratory uncertainty budget",
          "analysis_method_id": "method-ph",
          "analysis_method_revision": "rev-1",
          "provider_id": "laboratory-1",
          "provider_revision": "lab-rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "0000000000000000000000000000000000000000000000000000000000000000",
          "result_record_digest": "7777777777777777777777777777777777777777777777777777777777777777",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored water campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "result_id": "result-1",
          "sample_id": "sample-1",
          "analyte": "conductivity",
          "species_or_quantity_definition": "electrical conductivity",
          "value": 10.0,
          "unit_token": "uS/cm",
          "expanded_uncertainty": 0.1,
          "uncertainty_basis": "caller laboratory uncertainty budget",
          "analysis_method_id": "method-conductivity",
          "analysis_method_revision": "rev-1",
          "provider_id": "laboratory-1",
          "provider_revision": "lab-rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "1111111111111111111111111111111111111111111111111111111111111111",
          "result_record_digest": "8888888888888888888888888888888888888888888888888888888888888888",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored water campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "result_id": "result-2",
          "sample_id": "sample-1",
          "analyte": "chloride",
          "species_or_quantity_definition": "chloride ion mass concentration",
          "value": 10.0,
          "unit_token": "mg/L",
          "expanded_uncertainty": 0.1,
          "uncertainty_basis": "caller laboratory uncertainty budget",
          "analysis_method_id": "method-chloride",
          "analysis_method_revision": "rev-1",
          "provider_id": "laboratory-1",
          "provider_revision": "lab-rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "2222222222222222222222222222222222222222222222222222222222222222",
          "result_record_digest": "9999999999999999999999999999999999999999999999999999999999999999",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored water campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "result_id": "result-3",
          "sample_id": "sample-1",
          "analyte": "halide",
          "species_or_quantity_definition": "caller total halide mass concentration",
          "value": 12.0,
          "unit_token": "mg/L",
          "expanded_uncertainty": 0.1,
          "uncertainty_basis": "caller laboratory uncertainty budget",
          "analysis_method_id": "method-halide",
          "analysis_method_revision": "rev-1",
          "provider_id": "laboratory-1",
          "provider_revision": "lab-rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "3333333333333333333333333333333333333333333333333333333333333333",
          "result_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored water campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "result_id": "result-4",
          "sample_id": "sample-1",
          "analyte": "oxygen",
          "species_or_quantity_definition": "dissolved molecular oxygen",
          "value": 2.0,
          "unit_token": "mg/L",
          "expanded_uncertainty": 0.1,
          "uncertainty_basis": "caller laboratory uncertainty budget",
          "analysis_method_id": "method-oxygen",
          "analysis_method_revision": "rev-1",
          "provider_id": "laboratory-1",
          "provider_revision": "lab-rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "4444444444444444444444444444444444444444444444444444444444444444",
          "result_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored water campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "result_id": "result-5",
          "sample_id": "sample-1",
          "analyte": "solids",
          "species_or_quantity_definition": "total suspended solids",
          "value": 1.0,
          "unit_token": "mg/L",
          "expanded_uncertainty": 0.1,
          "uncertainty_basis": "caller laboratory uncertainty budget",
          "analysis_method_id": "method-solids",
          "analysis_method_revision": "rev-1",
          "provider_id": "laboratory-1",
          "provider_revision": "lab-rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "5555555555555555555555555555555555555555555555555555555555555555",
          "result_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored water campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "result_id": "result-6",
          "sample_id": "sample-1",
          "analyte": "microbiology",
          "species_or_quantity_definition": "caller culturable count",
          "value": 5.0,
          "unit_token": "CFU/mL",
          "expanded_uncertainty": 0.1,
          "uncertainty_basis": "caller laboratory uncertainty budget",
          "analysis_method_id": "method-microbiology",
          "analysis_method_revision": "rev-1",
          "provider_id": "laboratory-1",
          "provider_revision": "lab-rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "6666666666666666666666666666666666666666666666666666666666666666",
          "result_record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored water campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "result_id": "result-7",
          "sample_id": "sample-1",
          "analyte": "inhibitor",
          "species_or_quantity_definition": "inhibitor active component",
          "value": 100.0,
          "unit_token": "mg/L",
          "expanded_uncertainty": 0.1,
          "uncertainty_basis": "caller laboratory uncertainty budget",
          "analysis_method_id": "method-inhibitor",
          "analysis_method_revision": "rev-1",
          "provider_id": "laboratory-1",
          "provider_revision": "lab-rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "7777777777777777777777777777777777777777777777777777777777777777",
          "result_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored water campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "result_id": "result-8",
          "sample_id": "sample-1",
          "analyte": "temperature",
          "species_or_quantity_definition": "sample temperature",
          "value": 298.0,
          "unit_token": "K",
          "expanded_uncertainty": 0.1,
          "uncertainty_basis": "caller laboratory uncertainty budget",
          "analysis_method_id": "method-temperature",
          "analysis_method_revision": "rev-1",
          "provider_id": "laboratory-1",
          "provider_revision": "lab-rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_data_digest": "8888888888888888888888888888888888888888888888888888888888888888",
          "result_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored water campaign",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "sample_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored water campaign",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "caller_profile": {
    "profile_id": "profile-1",
    "profile_version": "1.0.0",
    "required_history_kinds": [
      "fill",
      "hold",
      "drain",
      "dry"
    ],
    "required_analytes": [
      "ph",
      "conductivity",
      "chloride",
      "halide",
      "oxygen",
      "solids",
      "microbiology",
      "inhibitor",
      "temperature"
    ],
    "minimum_sample_count": 1,
    "minimum_independent_source_group_count": 1,
    "criteria": [
      {
        "criterion_id": "criterion-ph",
        "analyte": "ph",
        "species_or_quantity_definition": "hydrogen-ion activity pH",
        "aggregation": "minimum",
        "direction": "minimum",
        "accept_limit": 6.5,
        "reject_limit": 5.0,
        "unit_token": "1",
        "criterion_basis": "caller-authored water-quality criterion"
      },
      {
        "criterion_id": "criterion-conductivity",
        "analyte": "conductivity",
        "species_or_quantity_definition": "electrical conductivity",
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": 15.0,
        "reject_limit": 20.0,
        "unit_token": "uS/cm",
        "criterion_basis": "caller-authored water-quality criterion"
      },
      {
        "criterion_id": "criterion-chloride",
        "analyte": "chloride",
        "species_or_quantity_definition": "chloride ion mass concentration",
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": 15.0,
        "reject_limit": 20.0,
        "unit_token": "mg/L",
        "criterion_basis": "caller-authored water-quality criterion"
      },
      {
        "criterion_id": "criterion-halide",
        "analyte": "halide",
        "species_or_quantity_definition": "caller total halide mass concentration",
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": 18.0,
        "reject_limit": 24.0,
        "unit_token": "mg/L",
        "criterion_basis": "caller-authored water-quality criterion"
      },
      {
        "criterion_id": "criterion-oxygen",
        "analyte": "oxygen",
        "species_or_quantity_definition": "dissolved molecular oxygen",
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": 3.0,
        "reject_limit": 4.0,
        "unit_token": "mg/L",
        "criterion_basis": "caller-authored water-quality criterion"
      },
      {
        "criterion_id": "criterion-solids",
        "analyte": "solids",
        "species_or_quantity_definition": "total suspended solids",
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": 1.5,
        "reject_limit": 2.0,
        "unit_token": "mg/L",
        "criterion_basis": "caller-authored water-quality criterion"
      },
      {
        "criterion_id": "criterion-microbiology",
        "analyte": "microbiology",
        "species_or_quantity_definition": "caller culturable count",
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": 7.5,
        "reject_limit": 10.0,
        "unit_token": "CFU/mL",
        "criterion_basis": "caller-authored water-quality criterion"
      },
      {
        "criterion_id": "criterion-inhibitor",
        "analyte": "inhibitor",
        "species_or_quantity_definition": "inhibitor active component",
        "aggregation": "minimum",
        "direction": "minimum",
        "accept_limit": 90.0,
        "reject_limit": 50.0,
        "unit_token": "mg/L",
        "criterion_basis": "caller-authored water-quality criterion"
      },
      {
        "criterion_id": "criterion-temperature",
        "analyte": "temperature",
        "species_or_quantity_definition": "sample temperature",
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": 300.0,
        "reject_limit": 320.0,
        "unit_token": "K",
        "criterion_basis": "caller-authored water-quality criterion"
      }
    ],
    "profile_provider_id": "caller-provider",
    "profile_revision": "rev-1",
    "profile_configuration_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "caller_acceptance_authority": "caller hydrotest review group",
    "chemical_species_conversion_used": false,
    "corrosion_rate_inference_claimed": false,
    "microbiological_risk_inference_claimed": false,
    "built_in_code_or_standard_limits_used": false,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored water campaign",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "source_batch_tank_circuit_material_contact_identity_reviewed": true,
  "ordered_fill_hold_drain_dry_history_reviewed": true,
  "sampling_time_location_method_lab_and_calibration_reviewed": true,
  "analyte_species_units_uncertainty_and_methods_reviewed": true,
  "replicate_source_and_independence_claims_reviewed": true,
  "provider_provenance_and_digests_reviewed": true,
  "caller_profile_reviewed": true,
  "invalid_and_missing_records_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored water campaign",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/test_water_quality_campaign.py#L281)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

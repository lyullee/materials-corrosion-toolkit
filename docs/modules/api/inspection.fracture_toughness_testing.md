# `inspection.fracture_toughness_testing`

**목적:** Specimen, geometry, orientation, precrack, loading, result, uncertainty and provenance remain caller evidence.

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
| `records` | 예 | `{"items": {"$ref": "#/$defs/FractureToughnessSpecimenRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_profile` | 예 | `{"$ref": "#/$defs/FractureToughnessCallerProfile"}` | 계약·필드 설명 참조 |
| `specimen_geometry_orientation_and_extraction_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_loading_rate_and_environment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `notch_crack_and_fatigue_precrack_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `method_result_unit_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_validity_flags_and_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `replicate_source_and_independence_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_provenance_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FractureToughnessCampaignAssessment.json)

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
| `official_validity_rules_applied` | `1` |
| `toughness_converted_or_recalculated` | `1` |
| `design_allowable_produced` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Specimen, geometry, orientation, precrack, loading, result, uncertainty and provenance remain caller evidence.
- Only caller profile limits are applied; no official validity rule, conversion, recalculation or design allowable is embedded.

## 구현 근거·독립 설명

- `authored_fracture_toughness_testing_campaign_audit`: Preserve caller-supplied specimen identity, geometry, orientation, temperature, environment, loading, fatigue-precrack evidence, reported toughness result, exact unit, validity flags, uncertainty and independence groups. Compare only with caller-authored campaign criteria. Do not embed official validity rules, convert or recalculate toughness, supply design allowables or claim method qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.fracture_toughness_testing"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.fracture_toughness_testing"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "physical_scope_id": "scope-1",
  "campaign_id": "campaign-1",
  "records": [
    {
      "record_id": "record-1",
      "physical_specimen_id": "specimen-1",
      "replicate_group_id": "replicate-group-1",
      "source_group_id": "source-group-1",
      "independence_group_id": "independence-group-1",
      "material_id": "material-1",
      "material_condition_id": "condition-1",
      "product_form_id": "plate-1",
      "extraction_location_definition": "caller reviewed plate coordinate",
      "notch_orientation_id": "L-T-notch",
      "crack_plane_orientation_id": "L-T-plane",
      "crack_growth_direction_id": "T-direction",
      "geometry": {
        "geometry_id": "geometry-1",
        "specimen_type_descriptor": "caller compact specimen descriptor",
        "width": 50.0,
        "thickness": 25.0,
        "net_thickness": 25.0,
        "initial_notch_length": 20.0,
        "final_crack_length": 25.0,
        "dimension_unit_token": "mm",
        "geometry_measurement_uncertainty": 0.05,
        "geometry_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      },
      "test_temperature_K": 293.15,
      "expanded_temperature_uncertainty_K": 0.5,
      "environment_id": "laboratory-air",
      "loading_mode": "opening mode",
      "loading_control_definition": "caller displacement-rate control",
      "loading_rate_value": 1.0,
      "loading_rate_unit_token": "mm/min",
      "expanded_loading_rate_uncertainty": 0.05,
      "fatigue_precrack": {
        "precrack_method_id": "fatigue-precrack-1",
        "cycle_count": 10000,
        "maximum_load_value": 10.0,
        "load_unit_token": "kN",
        "load_ratio": 0.1,
        "frequency_hz": 10.0,
        "precrack_extension": 5.0,
        "extension_unit_token": "mm",
        "precrack_front_definition": "caller measured final crack front",
        "precrack_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored test",
            "license_id": null,
            "sha256": null
          }
        ]
      },
      "toughness_kind": "K",
      "user_defined_toughness_description": null,
      "test_method_id": "caller-method-1",
      "test_method_revision": "rev-1",
      "reported_toughness": 100.0,
      "toughness_unit_token": "MPa*sqrt(m)",
      "expanded_toughness_uncertainty": 4.0,
      "uncertainty_coverage_definition": "caller expanded uncertainty budget",
      "caller_validity_flags": [
        {
          "flag_id": "caller-validity-flag-1",
          "flag_result": "satisfied",
          "flag_definition": "caller-authored validity condition",
          "review_basis": "caller reviewed test record",
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored test",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "caller_overall_valid": true,
      "caller_validity_record_id": "validity-1",
      "invalid_or_limiting_basis": null,
      "provider_id": "laboratory-provider",
      "provider_revision": "provider-rev-1",
      "provider_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "raw_data_digest": "1111111111111111111111111111111111111111111111111111111111111111",
      "result_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "record_id": "record-2",
      "physical_specimen_id": "specimen-2",
      "replicate_group_id": "replicate-group-1",
      "source_group_id": "source-group-2",
      "independence_group_id": "independence-group-2",
      "material_id": "material-1",
      "material_condition_id": "condition-1",
      "product_form_id": "plate-1",
      "extraction_location_definition": "caller reviewed plate coordinate",
      "notch_orientation_id": "L-T-notch",
      "crack_plane_orientation_id": "L-T-plane",
      "crack_growth_direction_id": "T-direction",
      "geometry": {
        "geometry_id": "geometry-2",
        "specimen_type_descriptor": "caller compact specimen descriptor",
        "width": 50.0,
        "thickness": 25.0,
        "net_thickness": 25.0,
        "initial_notch_length": 20.0,
        "final_crack_length": 25.0,
        "dimension_unit_token": "mm",
        "geometry_measurement_uncertainty": 0.05,
        "geometry_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      },
      "test_temperature_K": 293.15,
      "expanded_temperature_uncertainty_K": 0.5,
      "environment_id": "laboratory-air",
      "loading_mode": "opening mode",
      "loading_control_definition": "caller displacement-rate control",
      "loading_rate_value": 1.0,
      "loading_rate_unit_token": "mm/min",
      "expanded_loading_rate_uncertainty": 0.05,
      "fatigue_precrack": {
        "precrack_method_id": "fatigue-precrack-1",
        "cycle_count": 10000,
        "maximum_load_value": 10.0,
        "load_unit_token": "kN",
        "load_ratio": 0.1,
        "frequency_hz": 10.0,
        "precrack_extension": 5.0,
        "extension_unit_token": "mm",
        "precrack_front_definition": "caller measured final crack front",
        "precrack_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored test",
            "license_id": null,
            "sha256": null
          }
        ]
      },
      "toughness_kind": "K",
      "user_defined_toughness_description": null,
      "test_method_id": "caller-method-1",
      "test_method_revision": "rev-1",
      "reported_toughness": 105.0,
      "toughness_unit_token": "MPa*sqrt(m)",
      "expanded_toughness_uncertainty": 4.0,
      "uncertainty_coverage_definition": "caller expanded uncertainty budget",
      "caller_validity_flags": [
        {
          "flag_id": "caller-validity-flag-1",
          "flag_result": "satisfied",
          "flag_definition": "caller-authored validity condition",
          "review_basis": "caller reviewed test record",
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored test",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "caller_overall_valid": true,
      "caller_validity_record_id": "validity-2",
      "invalid_or_limiting_basis": null,
      "provider_id": "laboratory-provider",
      "provider_revision": "provider-rev-1",
      "provider_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "raw_data_digest": "2222222222222222222222222222222222222222222222222222222222222222",
      "result_record_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "caller_profile": {
    "profile_id": "profile-1",
    "profile_version": "1.0.0",
    "toughness_kind": "K",
    "test_method_id": "caller-method-1",
    "test_method_revision": "rev-1",
    "toughness_unit_token": "MPa*sqrt(m)",
    "loading_rate_unit_token": "mm/min",
    "minimum_temperature_K": 290.0,
    "maximum_temperature_K": 300.0,
    "minimum_loading_rate": 0.5,
    "maximum_loading_rate": 2.0,
    "criteria": [
      {
        "criterion_id": "criterion-specimen_count",
        "metric_id": "specimen_count",
        "direction": "minimum",
        "accept_limit": 2.0,
        "reject_limit": 1.0,
        "unit_token": "count",
        "criterion_basis": "caller-authored campaign criterion"
      },
      {
        "criterion_id": "criterion-replicate_group_count",
        "metric_id": "replicate_group_count",
        "direction": "minimum",
        "accept_limit": 1.0,
        "reject_limit": 0.0,
        "unit_token": "count",
        "criterion_basis": "caller-authored campaign criterion"
      },
      {
        "criterion_id": "criterion-independent_source_group_count",
        "metric_id": "independent_source_group_count",
        "direction": "minimum",
        "accept_limit": 2.0,
        "reject_limit": 1.0,
        "unit_token": "count",
        "criterion_basis": "caller-authored campaign criterion"
      },
      {
        "criterion_id": "criterion-caller_valid_fraction",
        "metric_id": "caller_valid_fraction",
        "direction": "minimum",
        "accept_limit": 1.0,
        "reject_limit": 0.5,
        "unit_token": "1",
        "criterion_basis": "caller-authored campaign criterion"
      },
      {
        "criterion_id": "criterion-minimum_reported_toughness",
        "metric_id": "minimum_reported_toughness",
        "direction": "minimum",
        "accept_limit": 90.0,
        "reject_limit": 70.0,
        "unit_token": "MPa*sqrt(m)",
        "criterion_basis": "caller-authored campaign criterion"
      },
      {
        "criterion_id": "criterion-maximum_expanded_uncertainty",
        "metric_id": "maximum_expanded_uncertainty",
        "direction": "maximum",
        "accept_limit": 5.0,
        "reject_limit": 10.0,
        "unit_token": "MPa*sqrt(m)",
        "criterion_basis": "caller-authored campaign criterion"
      }
    ],
    "profile_provider_id": "caller-provider",
    "profile_revision": "profile-rev-1",
    "profile_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "caller_acceptance_authority": "caller fracture review group",
    "official_standard_validity_rules_embedded": false,
    "toughness_conversion_or_recalculation_claimed": false,
    "design_allowable_claimed": false,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored test",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "specimen_geometry_orientation_and_extraction_reviewed": true,
  "temperature_loading_rate_and_environment_reviewed": true,
  "notch_crack_and_fatigue_precrack_reviewed": true,
  "method_result_unit_and_uncertainty_reviewed": true,
  "caller_validity_flags_and_basis_reviewed": true,
  "replicate_source_and_independence_groups_reviewed": true,
  "provider_provenance_and_digests_reviewed": true,
  "caller_profile_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored test",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fracture_toughness_testing.py#L286)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

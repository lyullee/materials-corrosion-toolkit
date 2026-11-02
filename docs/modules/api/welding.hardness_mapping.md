# `welding.hardness_mapping`

**목적:** Weld identity, exact test configuration, coordinates, caller regions, readings, uncertainty and lineage are preserved.

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
| `subject` | 예 | `{"$ref": "#/$defs/WeldHardnessSubject"}` | 계약·필드 설명 참조 |
| `configuration` | 예 | `{"$ref": "#/$defs/HardnessTestConfiguration"}` | 계약·필드 설명 참조 |
| `traverses` | 예 | `{"items": {"$ref": "#/$defs/WeldHardnessTraverse"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_profile` | 예 | `{"$ref": "#/$defs/WeldHardnessCallerProfile"}` | 계약·필드 설명 참조 |
| `weld_joint_wps_heat_consumable_material_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `coordinate_frame_traverse_and_orientation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_region_assignment_and_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `method_scale_load_dwell_indenter_and_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `point_coordinates_readings_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `replicate_source_and_independence_claims_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_provenance_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `invalid_and_missing_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WeldHardnessMappingCampaignAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `report_schema_version` | `1` |
| `assessment_id` | `1` |
| `campaign_id` | `1` |
| `campaign_outcome` | `1` |
| `caller_profile_id` | `1` |
| `region_metric_values` | `hardness scale unit` |
| `criterion_findings` | `mixed` |
| `diagnostics` | `mixed` |
| `input_digest` | `1` |
| `caller_profile_only` | `1` |
| `hardness_scale_converted` | `1` |
| `strength_inferred` | `1` |
| `automatic_haz_classification` | `1` |
| `specification_acceptance_or_qualification` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Weld identity, exact test configuration, coordinates, caller regions, readings, uncertainty and lineage are preserved.
- No scale conversion, strength inference, automatic region classification, standard limit, or qualification is produced.

## 구현 근거·독립 설명

- `authored_weld_hardness_mapping_campaign_audit`: Preserve caller-supplied weld, joint, WPS, heat, consumable, material, cross-section and coordinate frame, traverse, hardness configuration and calibrated point readings with caller-assigned weld-region labels, uncertainty and independence lineage. Apply only caller-authored criteria. Do not convert scales, infer strength, automatically classify HAZ regions, embed acceptance values or claim qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.hardness_mapping"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.hardness_mapping"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "campaign_id": "campaign-1",
  "subject": {
    "weld_id": "weld-1",
    "joint_id": "joint-1",
    "joint_configuration_id": "joint-configuration-1",
    "wps_id": "wps-1",
    "wps_revision": "rev-1",
    "production_heat_id": "production-heat-1",
    "consumable_id": "consumable-1",
    "consumable_lot_id": "consumable-lot-1",
    "base_material_a_id": "base-a",
    "base_material_a_heat_id": "base-a-heat",
    "base_material_b_id": "base-b",
    "base_material_b_heat_id": "base-b-heat",
    "weld_metal_material_id": "weld-metal-1",
    "coordinate_frame_id": "frame-1",
    "cross_section_id": "cross-section-1",
    "cross_section_record_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "subject_configuration_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored weld map",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "configuration": {
    "configuration_id": "configuration-1",
    "method_id": "method-1",
    "method_revision": "rev-1",
    "hardness_scale_id": "HV10",
    "hardness_unit_token": "HV10",
    "test_load_value": 10.0,
    "test_load_unit_token": "kgf",
    "dwell_time_s": 10.0,
    "indenter_id": "indenter-1",
    "instrument_id": "instrument-1",
    "reference_calibration_id": "calibration-1",
    "reference_calibration_provider_id": "calibration-provider",
    "reference_calibration_valid": true,
    "invalid_calibration_basis": null,
    "reference_calibration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored weld map",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "traverses": [
    {
      "traverse_id": "traverse-1",
      "coordinate_frame_id": "frame-1",
      "orientation_definition": "caller transverse line at reviewed depth",
      "nominal_offset_or_depth": 1.0,
      "coordinate_unit_token": "mm",
      "replicate_group_id": "replicate-group-1",
      "source_group_id": "source-group-1",
      "independence_group_id": "independence-group-1",
      "points": [
        {
          "point_id": "point-0",
          "traverse_id": "traverse-1",
          "coordinate_frame_id": "frame-1",
          "coordinate_x": 0.0,
          "coordinate_y": 1.0,
          "coordinate_z": 0.0,
          "coordinate_unit_token": "mm",
          "caller_assigned_region": "base_material",
          "user_defined_region_description": null,
          "region_assignment_basis": "caller-reviewed macrograph coordinate assignment",
          "hardness_value": 220.0,
          "hardness_unit_token": "HV10",
          "expanded_hardness_uncertainty": 5.0,
          "uncertainty_basis": "caller uncertainty budget",
          "provider_id": "laboratory-provider",
          "provider_revision": "rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_reading_digest": "0000000000000000000000000000000000000000000000000000000000000000",
          "point_record_digest": "8888888888888888888888888888888888888888888888888888888888888888",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored weld map",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "point_id": "point-1",
          "traverse_id": "traverse-1",
          "coordinate_frame_id": "frame-1",
          "coordinate_x": 1.0,
          "coordinate_y": 1.0,
          "coordinate_z": 0.0,
          "coordinate_unit_token": "mm",
          "caller_assigned_region": "haz",
          "user_defined_region_description": null,
          "region_assignment_basis": "caller-reviewed macrograph coordinate assignment",
          "hardness_value": 320.0,
          "hardness_unit_token": "HV10",
          "expanded_hardness_uncertainty": 5.0,
          "uncertainty_basis": "caller uncertainty budget",
          "provider_id": "laboratory-provider",
          "provider_revision": "rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_reading_digest": "1111111111111111111111111111111111111111111111111111111111111111",
          "point_record_digest": "9999999999999999999999999999999999999999999999999999999999999999",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored weld map",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "point_id": "point-2",
          "traverse_id": "traverse-1",
          "coordinate_frame_id": "frame-1",
          "coordinate_x": 2.0,
          "coordinate_y": 1.0,
          "coordinate_z": 0.0,
          "coordinate_unit_token": "mm",
          "caller_assigned_region": "fusion_boundary",
          "user_defined_region_description": null,
          "region_assignment_basis": "caller-reviewed macrograph coordinate assignment",
          "hardness_value": 330.0,
          "hardness_unit_token": "HV10",
          "expanded_hardness_uncertainty": 5.0,
          "uncertainty_basis": "caller uncertainty budget",
          "provider_id": "laboratory-provider",
          "provider_revision": "rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_reading_digest": "2222222222222222222222222222222222222222222222222222222222222222",
          "point_record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored weld map",
              "license_id": null,
              "sha256": null
            }
          ]
        },
        {
          "point_id": "point-3",
          "traverse_id": "traverse-1",
          "coordinate_frame_id": "frame-1",
          "coordinate_x": 3.0,
          "coordinate_y": 1.0,
          "coordinate_z": 0.0,
          "coordinate_unit_token": "mm",
          "caller_assigned_region": "weld_metal",
          "user_defined_region_description": null,
          "region_assignment_basis": "caller-reviewed macrograph coordinate assignment",
          "hardness_value": 300.0,
          "hardness_unit_token": "HV10",
          "expanded_hardness_uncertainty": 5.0,
          "uncertainty_basis": "caller uncertainty budget",
          "provider_id": "laboratory-provider",
          "provider_revision": "rev-1",
          "provider_configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "raw_reading_digest": "3333333333333333333333333333333333333333333333333333333333333333",
          "point_record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "record_valid": true,
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "authored",
              "origin": "synthetic",
              "citation": "authored weld map",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "traverse_record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored weld map",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "caller_profile": {
    "profile_id": "profile-1",
    "profile_version": "1.0.0",
    "required_regions": [
      "base_material",
      "haz",
      "fusion_boundary",
      "weld_metal"
    ],
    "minimum_traverse_count": 1,
    "minimum_independent_source_group_count": 1,
    "required_configuration_id": "configuration-1",
    "required_method_id": "method-1",
    "required_method_revision": "rev-1",
    "required_hardness_scale_id": "HV10",
    "required_hardness_unit_token": "HV10",
    "required_test_load_value": 10.0,
    "required_test_load_unit_token": "kgf",
    "required_dwell_time_s": 10.0,
    "required_indenter_id": "indenter-1",
    "criteria": [
      {
        "criterion_id": "criterion-base_material",
        "region": "base_material",
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": 250.0,
        "reject_limit": 300.0,
        "hardness_unit_token": "HV10",
        "criterion_basis": "caller-authored regional hardness criterion"
      },
      {
        "criterion_id": "criterion-haz",
        "region": "haz",
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": 350.0,
        "reject_limit": 400.0,
        "hardness_unit_token": "HV10",
        "criterion_basis": "caller-authored regional hardness criterion"
      },
      {
        "criterion_id": "criterion-fusion_boundary",
        "region": "fusion_boundary",
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": 350.0,
        "reject_limit": 400.0,
        "hardness_unit_token": "HV10",
        "criterion_basis": "caller-authored regional hardness criterion"
      },
      {
        "criterion_id": "criterion-weld_metal",
        "region": "weld_metal",
        "aggregation": "maximum",
        "direction": "maximum",
        "accept_limit": 350.0,
        "reject_limit": 400.0,
        "hardness_unit_token": "HV10",
        "criterion_basis": "caller-authored regional hardness criterion"
      }
    ],
    "profile_provider_id": "caller-provider",
    "profile_revision": "rev-1",
    "profile_configuration_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "caller_acceptance_authority": "caller welding review group",
    "scale_conversion_used": false,
    "strength_inference_claimed": false,
    "built_in_code_or_standard_limits_used": false,
    "automatic_haz_classification_claimed": false,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored weld map",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "weld_joint_wps_heat_consumable_material_identity_reviewed": true,
  "coordinate_frame_traverse_and_orientation_reviewed": true,
  "caller_region_assignment_and_basis_reviewed": true,
  "method_scale_load_dwell_indenter_and_calibration_reviewed": true,
  "point_coordinates_readings_units_and_uncertainty_reviewed": true,
  "replicate_source_and_independence_claims_reviewed": true,
  "provider_provenance_and_digests_reviewed": true,
  "caller_profile_reviewed": true,
  "invalid_and_missing_records_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored weld map",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/weld_hardness_mapping_campaign.py#L269)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

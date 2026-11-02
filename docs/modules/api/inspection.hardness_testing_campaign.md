# `inspection.hardness_testing_campaign`

**목적:** Subject, material, heat, method, scale, load, dwell, indenter, reference block and instrument identities are exact caller inputs.

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
| `subjects` | 예 | `{"items": {"$ref": "#/$defs/HardnessTestSubject"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `configuration` | 예 | `{"$ref": "#/$defs/HardnessTestConfiguration"}` | 계약·필드 설명 참조 |
| `reference_block` | 예 | `{"$ref": "#/$defs/HardnessReferenceBlockEvidence"}` | 계약·필드 설명 참조 |
| `readings` | 예 | `{"items": {"$ref": "#/$defs/HardnessReading"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_profile` | 예 | `{"$ref": "#/$defs/HardnessCampaignCallerProfile"}` | 계약·필드 설명 참조 |
| `subject_component_location_material_and_heat_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `method_scale_load_dwell_indenter_and_instrument_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_and_reference_block_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `surface_spacing_thickness_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `replicate_source_and_independence_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_validity_flags_and_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provenance_and_record_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HardnessTestingCampaign.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `campaign_id` | `1` |
| `quality_outcome` | `1` |
| `caller_profile_id` | `1` |
| `criterion_findings` | `mixed` |
| `reading_ids` | `1` |
| `specimen_ids` | `1` |
| `source_group_ids` | `1` |
| `independence_group_ids` | `1` |
| `input_digest` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Subject, material, heat, method, scale, load, dwell, indenter, reference block and instrument identities are exact caller inputs.
- Surface, spacing, thickness, readings, uncertainty, provenance and independence groups remain explicit evidence.
- Campaign outcomes use caller validity flags and bounds without conversion, strength inference or bundled acceptance rules.

## 구현 근거·독립 설명

- `authored_hardness_testing_campaign_evidence_audit`: Preserve caller-supplied subject, material, heat, location, hardness method, scale, load, dwell, indenter, instrument, reference-block verification, surface, spacing, thickness, reading, uncertainty and independence evidence. Apply only caller-authored criteria. Do not convert scales, embed official validity rules, infer strength or claim design acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.hardness_testing_campaign"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.hardness_testing_campaign"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "physical_scope_id": "scope-1",
  "campaign_id": "campaign-1",
  "subjects": [
    {
      "specimen_id": "specimen-1",
      "component_id": "component-1",
      "location_id": "location-1",
      "material_id": "material-1",
      "material_condition_id": "condition-1",
      "heat_id": "heat-1",
      "subject_record_digest": "3333333333333333333333333333333333333333333333333333333333333333",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller hardness data",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "configuration": {
    "method_id": "method-1",
    "scale_id": "scale-X",
    "hardness_unit_token": "scale-X",
    "applied_load": 10.0,
    "applied_load_unit_token": "kgf",
    "dwell_time_s": 10.0,
    "indenter_id": "indenter-1",
    "indenter_definition": "caller indenter identity",
    "instrument_id": "instrument-1",
    "instrument_revision": "1",
    "configuration_digest": "3333333333333333333333333333333333333333333333333333333333333333",
    "evidence": [
      {
        "source_id": "campaign",
        "origin": "measured",
        "citation": "caller hardness data",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "reference_block": {
    "reference_block_id": "block-1",
    "reference_block_condition_id": "condition-a",
    "scale_id": "scale-X",
    "certified_value": 200.0,
    "certified_expanded_uncertainty": 2.0,
    "hardness_unit_token": "scale-X",
    "certificate_id": "certificate-1",
    "certificate_revision": "1",
    "certificate_digest": "3333333333333333333333333333333333333333333333333333333333333333",
    "verification_status": "valid",
    "verification_record_digest": "3333333333333333333333333333333333333333333333333333333333333333",
    "invalid_or_missing_basis": null,
    "evidence": [
      {
        "source_id": "campaign",
        "origin": "measured",
        "citation": "caller hardness data",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "readings": [
    {
      "reading_id": "r1",
      "specimen_id": "specimen-1",
      "sequence_index": 1,
      "hardness_value": 200.0,
      "expanded_hardness_uncertainty": 5.0,
      "hardness_unit_token": "scale-X",
      "surface_condition_id": "prepared-1",
      "nearest_indent_spacing": 5.0,
      "edge_distance": 4.0,
      "local_thickness": 8.0,
      "geometry_unit_token": "mm",
      "expanded_geometry_uncertainty": 0.1,
      "replicate_group_id": "rep-1",
      "source_group_id": "source-r1",
      "independence_group_id": "ind-1",
      "caller_validity_status": "valid",
      "caller_validity_basis": "caller reviewed reading",
      "reading_record_digest": "3333333333333333333333333333333333333333333333333333333333333333",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller hardness data",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "reading_id": "r2",
      "specimen_id": "specimen-1",
      "sequence_index": 2,
      "hardness_value": 200.0,
      "expanded_hardness_uncertainty": 5.0,
      "hardness_unit_token": "scale-X",
      "surface_condition_id": "prepared-1",
      "nearest_indent_spacing": 5.0,
      "edge_distance": 4.0,
      "local_thickness": 8.0,
      "geometry_unit_token": "mm",
      "expanded_geometry_uncertainty": 0.1,
      "replicate_group_id": "rep-1",
      "source_group_id": "source-r2",
      "independence_group_id": "ind-2",
      "caller_validity_status": "valid",
      "caller_validity_basis": "caller reviewed reading",
      "reading_record_digest": "3333333333333333333333333333333333333333333333333333333333333333",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller hardness data",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "caller_profile": {
    "profile_id": "profile-1",
    "profile_revision": "1",
    "supported_component_ids": [
      "component-1"
    ],
    "supported_material_ids": [
      "material-1"
    ],
    "supported_material_condition_ids": [
      "condition-1"
    ],
    "supported_heat_ids": [
      "heat-1"
    ],
    "required_method_id": "method-1",
    "required_scale_id": "scale-X",
    "required_hardness_unit_token": "scale-X",
    "required_applied_load": 10.0,
    "required_applied_load_unit_token": "kgf",
    "required_dwell_time_s": 10.0,
    "dwell_time_tolerance_s": 0.5,
    "required_indenter_id": "indenter-1",
    "required_instrument_id": "instrument-1",
    "required_reference_block_id": "block-1",
    "supported_surface_condition_ids": [
      "prepared-1"
    ],
    "geometry_unit_token": "mm",
    "minimum_indent_spacing": 4.0,
    "minimum_edge_distance": 3.0,
    "minimum_local_thickness": 7.0,
    "minimum_hardness": 150.0,
    "maximum_hardness": null,
    "minimum_valid_reading_count": 2,
    "minimum_independence_group_count": 2,
    "caller_validity_policy_id": "caller-validity-1",
    "profile_source_digest": "3333333333333333333333333333333333333333333333333333333333333333",
    "built_in_standard_rules_used": false,
    "evidence": [
      {
        "source_id": "campaign",
        "origin": "measured",
        "citation": "caller hardness data",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "subject_component_location_material_and_heat_reviewed": true,
  "method_scale_load_dwell_indenter_and_instrument_reviewed": true,
  "calibration_and_reference_block_reviewed": true,
  "surface_spacing_thickness_and_uncertainty_reviewed": true,
  "replicate_source_and_independence_groups_reviewed": true,
  "caller_validity_flags_and_profile_reviewed": true,
  "provenance_and_record_digests_reviewed": true,
  "evidence": [
    {
      "source_id": "campaign",
      "origin": "measured",
      "citation": "caller hardness data",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/hardness_testing_campaign.py#L161)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

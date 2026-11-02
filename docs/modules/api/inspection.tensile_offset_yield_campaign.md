# `inspection.tensile_offset_yield_campaign`

**목적:** Specimen, product, heat, orientation, geometry, machine, load-cell and extensometer identities are exact caller inputs.

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
| `specimens` | 예 | `{"items": {"$ref": "#/$defs/TensileSpecimenIdentity"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `machine` | 예 | `{"$ref": "#/$defs/TensileMachineConfiguration"}` | 계약·필드 설명 참조 |
| `tests` | 예 | `{"items": {"$ref": "#/$defs/TensileTestRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_profile` | 예 | `{"$ref": "#/$defs/TensileCampaignCallerProfile"}` | 계약·필드 설명 참조 |
| `specimen_product_heat_orientation_and_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `machine_load_cell_extensometer_and_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_strain_rate_and_offset_definition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `raw_curve_and_reported_result_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `result_units_uncertainties_and_validity_flags_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `replicate_source_and_independence_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_profile_and_missing_evidence_policy_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TensileOffsetYieldCampaign.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `campaign_id` | `1` |
| `quality_outcome` | `1` |
| `caller_profile_id` | `1` |
| `criterion_findings` | `mixed` |
| `test_ids` | `1` |
| `specimen_ids` | `1` |
| `source_group_ids` | `1` |
| `independence_group_ids` | `1` |
| `input_digest` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Specimen, product, heat, orientation, geometry, machine, load-cell and extensometer identities are exact caller inputs.
- Temperature, strain rate, raw/result digests, offset definition and reported result uncertainties remain explicit.
- Campaign outcomes use caller criteria without curve recomputation, automatic offset construction or bundled design rules.

## 구현 근거·독립 설명

- `authored_tensile_offset_yield_campaign_evidence_audit`: Preserve caller-supplied tensile specimen, product, heat, orientation, geometry, machine, load-cell and extensometer calibration, temperature, strain rate, offset definition, reported modulus, yield, ultimate strength, elongation or reduction-area result, uncertainty and independence evidence. Apply only caller-authored criteria. Do not recalculate curves, automatically derive offset yield, embed official validity rules or claim design acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.tensile_offset_yield_campaign"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.tensile_offset_yield_campaign"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "assessment-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "physical_scope_id": "scope-1",
  "campaign_id": "campaign-1",
  "specimens": [
    {
      "specimen_id": "s1",
      "product_id": "product-1",
      "heat_id": "heat-1",
      "material_condition_id": "condition-1",
      "orientation_id": "longitudinal",
      "geometry_id": "round-1",
      "initial_gauge_length": 50.0,
      "initial_cross_section_area": 20.0,
      "geometry_unit_token": "mm",
      "area_unit_token": "mm^2",
      "specimen_record_digest": "4444444444444444444444444444444444444444444444444444444444444444",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller tensile data",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "specimen_id": "s2",
      "product_id": "product-1",
      "heat_id": "heat-1",
      "material_condition_id": "condition-1",
      "orientation_id": "longitudinal",
      "geometry_id": "round-1",
      "initial_gauge_length": 50.0,
      "initial_cross_section_area": 20.0,
      "geometry_unit_token": "mm",
      "area_unit_token": "mm^2",
      "specimen_record_digest": "4444444444444444444444444444444444444444444444444444444444444444",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller tensile data",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "machine": {
    "machine_id": "machine-1",
    "machine_revision": "1",
    "load_cell_id": "load-cell-1",
    "load_cell_revision": "1",
    "extensometer_id": "extenso-1",
    "extensometer_revision": "1",
    "machine_configuration_digest": "4444444444444444444444444444444444444444444444444444444444444444",
    "load_cell_calibration_id": "lc-cal-1",
    "load_cell_calibration_status": "valid",
    "load_cell_calibration_digest": "4444444444444444444444444444444444444444444444444444444444444444",
    "extensometer_calibration_id": "ex-cal-1",
    "extensometer_calibration_status": "valid",
    "extensometer_calibration_digest": "4444444444444444444444444444444444444444444444444444444444444444",
    "invalid_or_missing_basis": null,
    "evidence": [
      {
        "source_id": "campaign",
        "origin": "measured",
        "citation": "caller tensile data",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "tests": [
    {
      "test_id": "t1",
      "specimen_id": "s1",
      "sequence_index": 1,
      "test_temperature_K": 300.0,
      "expanded_temperature_uncertainty_K": 1.0,
      "strain_rate_per_s": 0.001,
      "expanded_strain_rate_uncertainty_per_s": 0.0001,
      "offset_definition_id": "offset-0.2-percent",
      "offset_strain": 0.002,
      "offset_strain_unit_token": "1",
      "raw_curve_digest": "4444444444444444444444444444444444444444444444444444444444444444",
      "result_set_digest": "4444444444444444444444444444444444444444444444444444444444444444",
      "results": [
        {
          "result_id": "yield-result",
          "metric": "offset_yield_strength",
          "metric_definition": "reported caller offset yield",
          "status": "reported",
          "value": 300000000.0,
          "expanded_uncertainty": 5000000.0,
          "unit_token": "Pa",
          "result_record_digest": "4444444444444444444444444444444444444444444444444444444444444444",
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "campaign",
              "origin": "measured",
              "citation": "caller tensile data",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "replicate_group_id": "rep-1",
      "source_group_id": "source-t1",
      "independence_group_id": "ind-1",
      "caller_validity_status": "valid",
      "caller_validity_basis": "caller validity review",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller tensile data",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "test_id": "t2",
      "specimen_id": "s2",
      "sequence_index": 2,
      "test_temperature_K": 300.0,
      "expanded_temperature_uncertainty_K": 1.0,
      "strain_rate_per_s": 0.001,
      "expanded_strain_rate_uncertainty_per_s": 0.0001,
      "offset_definition_id": "offset-0.2-percent",
      "offset_strain": 0.002,
      "offset_strain_unit_token": "1",
      "raw_curve_digest": "4444444444444444444444444444444444444444444444444444444444444444",
      "result_set_digest": "4444444444444444444444444444444444444444444444444444444444444444",
      "results": [
        {
          "result_id": "yield-result",
          "metric": "offset_yield_strength",
          "metric_definition": "reported caller offset yield",
          "status": "reported",
          "value": 300000000.0,
          "expanded_uncertainty": 5000000.0,
          "unit_token": "Pa",
          "result_record_digest": "4444444444444444444444444444444444444444444444444444444444444444",
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "campaign",
              "origin": "measured",
              "citation": "caller tensile data",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "replicate_group_id": "rep-1",
      "source_group_id": "source-t2",
      "independence_group_id": "ind-2",
      "caller_validity_status": "valid",
      "caller_validity_basis": "caller validity review",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller tensile data",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "caller_profile": {
    "profile_id": "profile-1",
    "profile_revision": "1",
    "product_id": "product-1",
    "heat_id": "heat-1",
    "material_condition_id": "condition-1",
    "supported_orientation_ids": [
      "longitudinal"
    ],
    "supported_geometry_ids": [
      "round-1"
    ],
    "geometry_unit_token": "mm",
    "area_unit_token": "mm^2",
    "required_machine_id": "machine-1",
    "required_load_cell_id": "load-cell-1",
    "required_extensometer_id": "extenso-1",
    "minimum_temperature_K": 290.0,
    "maximum_temperature_K": 310.0,
    "minimum_strain_rate_per_s": 0.0005,
    "maximum_strain_rate_per_s": 0.002,
    "required_offset_definition_id": "offset-0.2-percent",
    "required_offset_strain": 0.002,
    "offset_strain_tolerance": 0.0,
    "required_metrics": [
      "offset_yield_strength"
    ],
    "metric_criteria": [
      {
        "criterion_id": "yield-rule",
        "metric": "offset_yield_strength",
        "unit_token": "Pa",
        "minimum_acceptable": 250000000.0,
        "maximum_acceptable": null,
        "criterion_basis": "caller yield criterion",
        "evidence": [
          {
            "source_id": "campaign",
            "origin": "measured",
            "citation": "caller tensile data",
            "license_id": null,
            "sha256": null
          }
        ]
      }
    ],
    "minimum_valid_test_count": 2,
    "minimum_independence_group_count": 2,
    "caller_validity_policy_id": "caller-validity-1",
    "profile_source_digest": "4444444444444444444444444444444444444444444444444444444444444444",
    "built_in_standard_rules_used": false,
    "evidence": [
      {
        "source_id": "campaign",
        "origin": "measured",
        "citation": "caller tensile data",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "specimen_product_heat_orientation_and_geometry_reviewed": true,
  "machine_load_cell_extensometer_and_calibration_reviewed": true,
  "temperature_strain_rate_and_offset_definition_reviewed": true,
  "raw_curve_and_reported_result_digests_reviewed": true,
  "result_units_uncertainties_and_validity_flags_reviewed": true,
  "replicate_source_and_independence_groups_reviewed": true,
  "caller_profile_and_missing_evidence_policy_reviewed": true,
  "evidence": [
    {
      "source_id": "campaign",
      "origin": "measured",
      "citation": "caller tensile data",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/tensile_offset_yield_campaign.py#L216)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

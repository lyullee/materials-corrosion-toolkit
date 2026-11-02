# `inspection.impact_testing_campaign`

**목적:** Specimen, product, heat, orientation, notch, size, machine, striker and calibration identities are exact caller inputs.

**모델 버전:** `1.0.1` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

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
| `specimens` | 예 | `{"items": {"$ref": "#/$defs/ImpactSpecimenIdentity"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `machine` | 예 | `{"$ref": "#/$defs/ImpactMachineConfiguration"}` | 계약·필드 설명 참조 |
| `tests` | 예 | `{"items": {"$ref": "#/$defs/ImpactTestRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `caller_profile` | 예 | `{"$ref": "#/$defs/ImpactCampaignCallerProfile"}` | 계약·필드 설명 참조 |
| `specimen_product_heat_orientation_notch_and_size_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_results_units_and_uncertainties_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `machine_striker_and_calibration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `replicate_source_and_independence_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_validity_flags_and_profile_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provenance_and_record_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ImpactTestingCampaign.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `campaign_id` | `1` |
| `quality_outcome` | `1` |
| `acceptance_profile_id` | `1` |
| `criterion_findings` | `mixed` |
| `test_ids` | `1` |
| `specimen_ids` | `1` |
| `source_group_ids` | `1` |
| `independence_group_ids` | `1` |
| `exact_temperature_replicate_counts` | `count` |
| `input_digest` | `1` |
| `report_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Specimen, product, heat, orientation, notch, size, machine, striker and calibration identities are exact caller inputs.
- Reported energy, lateral expansion and shear-fracture evidence retains exact units, uncertainty and source independence.
- Campaign outcomes use caller validity flags and criteria without bundled standard rules or design acceptance.

## 구현 근거·독립 설명

- `authored_impact_testing_campaign_evidence_audit`: Preserve caller-supplied impact specimen, product, heat, orientation, notch, dimensions, test temperature, machine, striker, calibration, reported energy, lateral expansion or shear-fracture result, uncertainty and independence groups. Apply only caller-authored campaign criteria. Do not embed official validity rules, temperature corrections, transition fitting, design allowables or qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.impact_testing_campaign"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.impact_testing_campaign"]`. 합성값이며 물성·허용값·실측값이 아니다.

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
      "orientation_id": "orientation-1",
      "notch_id": "notch-1",
      "notch_definition": "caller notch identity",
      "size_id": "size-1",
      "thickness": 10.0,
      "width": 10.0,
      "length": 55.0,
      "dimension_unit_token": "mm",
      "specimen_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller impact data",
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
      "orientation_id": "orientation-1",
      "notch_id": "notch-1",
      "notch_definition": "caller notch identity",
      "size_id": "size-1",
      "thickness": 10.0,
      "width": 10.0,
      "length": 55.0,
      "dimension_unit_token": "mm",
      "specimen_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller impact data",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "machine": {
    "machine_id": "machine-1",
    "machine_revision": "1",
    "striker_id": "striker-1",
    "striker_definition": "caller striker identity",
    "striker_radius": 2.0,
    "striker_radius_unit_token": "mm",
    "machine_capacity": 300.0,
    "machine_capacity_unit_token": "J",
    "calibration_id": "cal-1",
    "calibration_revision": "1",
    "calibration_status": "valid",
    "calibration_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
    "invalid_or_missing_basis": null,
    "evidence": [
      {
        "source_id": "campaign",
        "origin": "measured",
        "citation": "caller impact data",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "tests": [
    {
      "test_id": "t1",
      "specimen_id": "s1",
      "test_temperature": 250.0,
      "expanded_temperature_uncertainty": 1.0,
      "temperature_unit_token": "K",
      "replicate_group_id": "rep-250K",
      "source_group_id": "source-t1",
      "independence_group_id": "ind-1",
      "sequence_index": 1,
      "results": [
        {
          "result_id": "energy-result",
          "metric": "absorbed_energy",
          "metric_definition": "reported machine absorbed energy",
          "status": "reported",
          "value": 50.0,
          "expanded_uncertainty": 2.0,
          "unit_token": "J",
          "result_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "campaign",
              "origin": "measured",
              "citation": "caller impact data",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "caller_validity_status": "valid",
      "caller_validity_basis": "caller reviewed record",
      "test_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller impact data",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "test_id": "t2",
      "specimen_id": "s2",
      "test_temperature": 250.0,
      "expanded_temperature_uncertainty": 1.0,
      "temperature_unit_token": "K",
      "replicate_group_id": "rep-250K",
      "source_group_id": "source-t2",
      "independence_group_id": "ind-2",
      "sequence_index": 2,
      "results": [
        {
          "result_id": "energy-result",
          "metric": "absorbed_energy",
          "metric_definition": "reported machine absorbed energy",
          "status": "reported",
          "value": 50.0,
          "expanded_uncertainty": 2.0,
          "unit_token": "J",
          "result_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
          "invalid_or_missing_basis": null,
          "evidence": [
            {
              "source_id": "campaign",
              "origin": "measured",
              "citation": "caller impact data",
              "license_id": null,
              "sha256": null
            }
          ]
        }
      ],
      "caller_validity_status": "valid",
      "caller_validity_basis": "caller reviewed record",
      "test_record_digest": "2222222222222222222222222222222222222222222222222222222222222222",
      "evidence": [
        {
          "source_id": "campaign",
          "origin": "measured",
          "citation": "caller impact data",
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
    "orientation_id": "orientation-1",
    "notch_id": "notch-1",
    "size_id": "size-1",
    "specimen_dimension_unit_token": "mm",
    "minimum_test_temperature_K": 240.0,
    "maximum_test_temperature_K": 260.0,
    "required_metrics": [
      "absorbed_energy"
    ],
    "metric_criteria": [
      {
        "criterion_id": "energy-rule",
        "metric": "absorbed_energy",
        "unit_token": "J",
        "minimum_acceptable": 40.0,
        "maximum_acceptable": null,
        "criterion_basis": "caller energy criterion",
        "evidence": [
          {
            "source_id": "campaign",
            "origin": "measured",
            "citation": "caller impact data",
            "license_id": null,
            "sha256": null
          }
        ]
      }
    ],
    "minimum_valid_replicates_per_exact_temperature": 2,
    "minimum_independence_group_count": 2,
    "required_machine_id": "machine-1",
    "required_striker_id": "striker-1",
    "required_calibration_id": "cal-1",
    "caller_validity_policy_id": "caller-validity-1",
    "profile_source_digest": "2222222222222222222222222222222222222222222222222222222222222222",
    "built_in_standard_criteria_used": false,
    "evidence": [
      {
        "source_id": "campaign",
        "origin": "measured",
        "citation": "caller impact data",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "specimen_product_heat_orientation_notch_and_size_reviewed": true,
  "temperature_results_units_and_uncertainties_reviewed": true,
  "machine_striker_and_calibration_reviewed": true,
  "replicate_source_and_independence_groups_reviewed": true,
  "caller_validity_flags_and_profile_reviewed": true,
  "provenance_and_record_digests_reviewed": true,
  "evidence": [
    {
      "source_id": "campaign",
      "origin": "measured",
      "citation": "caller impact data",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/impact_testing_campaign.py#L200)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

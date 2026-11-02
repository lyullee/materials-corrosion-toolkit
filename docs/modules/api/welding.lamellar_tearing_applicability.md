# `welding.lamellar_tearing_applicability`

**목적:** Parent material, product form, material condition and directionality identity match caller qualification evidence exactly.

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
| `parent_material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `product_form_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `directionality_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joints` | 예 | `{"items": {"$ref": "#/$defs/LamellarTearingJointCondition"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `qualification_envelope` | 예 | `{"$ref": "#/$defs/LamellarTearingQualificationEnvelope"}` | 계약·필드 설명 참조 |
| `material_product_and_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `directionality_and_thickness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `joint_geometry_and_through_thickness_loading_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `restraint_descriptor_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `welding_process_consumable_and_heat_input_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_specimen_and_source_group_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `test_method_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/LamellarTearingApplicability.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `physical_scope_id` | `1` |
| `qualification_envelope_id` | `1` |
| `joint_comparisons` | `1` |
| `outside_support_joint_ids` | `1` |
| `evidence_requirement_counts` | `1` |
| `test_evidence_summary` | `1` |
| `declared_applicability_outcome` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Parent material, product form, material condition and directionality identity match caller qualification evidence exactly.
- Heat input is compared only under an exact caller-declared unit token; no conversion or code limit is inferred.
- Joint geometry, through-thickness loading, restraint, welding process and consumable support are caller declarations.

## 구현 근거·독립 설명

- `reviewed_lamellar_tearing_qualification_envelope`: Compare parent material, product, directionality, joint geometry, through-thickness loading, restraint, welding process, consumable and heat-input records with physical-specimen and source-group evidence. Do not bundle threshold tables or infer tearing susceptibility, flaw size, probability, life or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.lamellar_tearing_applicability"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.lamellar_tearing_applicability"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-lamellar",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "scope-1",
  "parent_material_id": "plate-1",
  "material_condition_id": "condition-1",
  "product_form_id": "rolled-plate",
  "directionality_descriptor": "through-thickness-z",
  "joints": [
    {
      "joint_id": "joint-1",
      "joint_geometry_descriptor": "tee-joint",
      "governing_thickness_m": 0.03,
      "through_thickness_loading_descriptor": "weld-shrinkage-normal-to-plate",
      "restraint_descriptor": "caller-restraint-a",
      "weld_process_id": "process-1",
      "consumable_id": "consumable-1",
      "minimum_heat_input_value": 0.8,
      "maximum_heat_input_value": 1.5,
      "heat_input_unit_token": "custom-energy-per-length",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored lamellar joint"
        }
      ]
    }
  ],
  "qualification_envelope": {
    "envelope_id": "envelope-1",
    "parent_material_id": "plate-1",
    "material_condition_id": "condition-1",
    "product_form_id": "rolled-plate",
    "directionality_descriptor": "through-thickness-z",
    "minimum_thickness_m": 0.01,
    "maximum_thickness_m": 0.05,
    "supported_joint_geometry_descriptors": [
      "tee-joint"
    ],
    "supported_through_thickness_loading_descriptors": [
      "weld-shrinkage-normal-to-plate"
    ],
    "supported_restraint_descriptors": [
      "caller-restraint-a"
    ],
    "supported_weld_process_ids": [
      "process-1"
    ],
    "supported_consumable_ids": [
      "consumable-1"
    ],
    "minimum_heat_input_value": 0.5,
    "maximum_heat_input_value": 2.0,
    "heat_input_unit_token": "custom-energy-per-length",
    "evidence_requirements": [
      {
        "requirement_id": "z-test",
        "observation_kind": "through-thickness-test",
        "result_name": "reported-reduction",
        "direction_id": "Z",
        "result_unit_token": "fraction",
        "minimum_record_count": 1,
        "requirement_basis": "authored evidence plan"
      }
    ],
    "test_evidence": [
      {
        "evidence_record_id": "record-1",
        "physical_specimen_id": "specimen-1",
        "source_group_id": "source-record-1",
        "independence_group_id": "independent-record-1",
        "parent_material_id": "plate-1",
        "material_condition_id": "condition-1",
        "product_form_id": "rolled-plate",
        "specimen_thickness_m": 0.03,
        "directionality_descriptor": "through-thickness-z",
        "provider_id": "laboratory-1",
        "provider_revision": "1",
        "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "input_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "observations": [
          {
            "observation_id": "observation-record-1",
            "observation_kind": "through-thickness-test",
            "result_name": "reported-reduction",
            "direction_id": "Z",
            "method_id": "caller-method",
            "result_value": 0.25,
            "result_unit_token": "fraction",
            "expanded_uncertainty": 0.02,
            "coverage_factor": 2.0,
            "result_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "record_available": true,
            "evidence": [
              {
                "source_id": "authored-example",
                "origin": "synthetic",
                "citation": "authored lamellar observation"
              }
            ]
          }
        ],
        "record_valid": true,
        "supports_declared_envelope": true,
        "evidence": [
          {
            "source_id": "authored-example",
            "origin": "synthetic",
            "citation": "authored lamellar evidence"
          }
        ]
      }
    ],
    "qualification_basis": "authored qualification programme",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored lamellar envelope"
      }
    ]
  },
  "material_product_and_condition_reviewed": true,
  "directionality_and_thickness_reviewed": true,
  "joint_geometry_and_through_thickness_loading_reviewed": true,
  "restraint_descriptor_reviewed": true,
  "welding_process_consumable_and_heat_input_reviewed": true,
  "physical_specimen_and_source_group_partitions_reviewed": true,
  "test_method_units_and_uncertainty_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "qualification_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored lamellar assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/lamellar_tearing.py#L182)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

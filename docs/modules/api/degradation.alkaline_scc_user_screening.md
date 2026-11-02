# `degradation.alkaline_scc_user_screening`

**목적:** Facts and rules are caller-authored and retain evidence record, source group and digest lineage.

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
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `mechanism` | 예 | `{"enum": ["chloride_scc", "ammonia_scc", "alkaline_scc"], "type": "string"}` | 계약·필드 설명 참조 |
| `facts` | 예 | `{"items": {"$ref": "#/$defs/SCCScreeningFact"}, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `mechanism_profile` | 예 | `{"$ref": "#/$defs/SCCMechanismProfile"}` | 계약·필드 설명 참조 |
| `environment_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `stress_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `fact_definitions_units_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `mechanism_profile_rules_and_unknown_policy_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `screening_and_qualification_boundary_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/UserDefinedSCCScreening.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `mechanism` | `1` |
| `profile_id` | `1` |
| `profile_version` | `1` |
| `profile_provider_id` | `1` |
| `unknown_policy` | `1` |
| `screening_outcome` | `1` |
| `screening_outcome_basis` | `1` |
| `rule_findings` | `mixed` |
| `invalid_fact_ids` | `1` |
| `unknown_fact_ids` | `1` |
| `missing_reviews` | `1` |
| `screening_only` | `1` |
| `qualification_outcome` | `1` |
| `input_digest` | `1` |
| `result_digest` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Facts and rules are caller-authored and retain evidence record, source group and digest lineage.
- Unknown inputs cannot produce a not-indicated result.
- Screening does not establish qualification, acceptance, life or failure probability.

## 구현 근거·독립 설명

- `authored_caller_defined_scc_rule_screening`: Evaluate only caller-authored, evidence-linked material, environment and stress facts against caller-authored AND conditions grouped into OR screening rules. Preserve unknown and invalid facts, use the declared conservative unknown policy, and never convert an unknown into a screen-out. No proprietary threshold, acceptance rule, initiation model, growth rate, remaining life, failure probability or qualification claim is bundled.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.alkaline_scc_user_screening"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.alkaline_scc_user_screening"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "alkaline_scc-screen-1",
  "asset_id": "asset-1",
  "location_id": "location-1",
  "physical_scope_id": "scope-1",
  "material_condition_id": "material-condition-1",
  "mechanism": "alkaline_scc",
  "facts": [
    {
      "fact_id": "environment.temperature",
      "domain": "environment",
      "definition": "caller-reviewed exposure temperature",
      "value_kind": "number",
      "status": "known",
      "numeric_value": 350.0,
      "unit_token": "K",
      "descriptor_value": null,
      "boolean_value": null,
      "unknown_or_invalid_basis": null,
      "evidence_record_id": "environment-record-1",
      "source_group_id": "environment-source-1",
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored SCC screening test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "fact_id": "material.condition",
      "domain": "material",
      "definition": "caller-defined material screening descriptor",
      "value_kind": "descriptor",
      "status": "known",
      "numeric_value": null,
      "unit_token": null,
      "descriptor_value": "caller-susceptible-condition",
      "boolean_value": null,
      "unknown_or_invalid_basis": null,
      "evidence_record_id": "material-record-1",
      "source_group_id": "material-source-1",
      "record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored SCC screening test",
          "license_id": null,
          "sha256": null
        }
      ]
    },
    {
      "fact_id": "stress.tensile_present",
      "domain": "stress",
      "definition": "caller-reviewed tensile-stress presence",
      "value_kind": "boolean",
      "status": "known",
      "numeric_value": null,
      "unit_token": null,
      "descriptor_value": null,
      "boolean_value": true,
      "unknown_or_invalid_basis": null,
      "evidence_record_id": "stress-record-1",
      "source_group_id": "stress-source-1",
      "record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored SCC screening test",
          "license_id": null,
          "sha256": null
        }
      ]
    }
  ],
  "mechanism_profile": {
    "profile_id": "alkaline_scc-profile-1",
    "profile_version": "1.0.0",
    "mechanism": "alkaline_scc",
    "mechanism_definition": "caller-authored conjunction of reviewed screening facts",
    "unknown_policy": "indeterminate",
    "rules": [
      {
        "rule_id": "caller-rule-1",
        "rule_definition": "all three caller-defined conditions are present",
        "conditions": [
          {
            "condition_id": "temperature-condition",
            "fact_id": "environment.temperature",
            "expected_fact_kind": "number",
            "operator": "greater_than_or_equal",
            "unit_token": "K",
            "threshold": 300.0,
            "lower_bound": null,
            "upper_bound": null,
            "expected_descriptors": [],
            "condition_basis": "caller-selected research screening threshold"
          },
          {
            "condition_id": "material-condition",
            "fact_id": "material.condition",
            "expected_fact_kind": "descriptor",
            "operator": "equals",
            "unit_token": null,
            "threshold": null,
            "lower_bound": null,
            "upper_bound": null,
            "expected_descriptors": [
              "caller-susceptible-condition"
            ],
            "condition_basis": "caller material grouping"
          },
          {
            "condition_id": "stress-condition",
            "fact_id": "stress.tensile_present",
            "expected_fact_kind": "boolean",
            "operator": "is_true",
            "unit_token": null,
            "threshold": null,
            "lower_bound": null,
            "upper_bound": null,
            "expected_descriptors": [],
            "condition_basis": "caller stress evidence interpretation"
          }
        ],
        "evidence": [
          {
            "source_id": "authored",
            "origin": "synthetic",
            "citation": "authored SCC screening test",
            "license_id": null,
            "sha256": null
          }
        ]
      }
    ],
    "profile_provider_id": "caller-profile-provider",
    "profile_revision": "rev-1",
    "profile_configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "profile_source_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "screening_only": true,
    "qualification_claimed": false,
    "evidence": [
      {
        "source_id": "authored",
        "origin": "synthetic",
        "citation": "authored SCC screening test",
        "license_id": null,
        "sha256": null
      }
    ]
  },
  "environment_evidence_reviewed": true,
  "material_evidence_reviewed": true,
  "stress_evidence_reviewed": true,
  "fact_definitions_units_and_digests_reviewed": true,
  "mechanism_profile_rules_and_unknown_policy_reviewed": true,
  "screening_and_qualification_boundary_reviewed": true,
  "evidence": [
    {
      "source_id": "authored",
      "origin": "synthetic",
      "citation": "authored SCC screening test",
      "license_id": null,
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/scc_rule_screening.py#L275)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

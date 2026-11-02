# `welding.wps_qualification_envelope`

**목적:** Qualified-procedure, revision, material-side, joint and welding-process identities match exactly.

**모델 버전:** `1.1.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `production_weld_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `production_procedure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `production_procedure_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `base_material_side_a_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `base_material_side_b_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `joint_configuration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `welding_process_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `production_variables` | 예 | `{"items": {"$ref": "#/$defs/ProductionEssentialVariableRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/DeclaredWPSQualificationEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `production_procedure_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_and_joint_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `variable_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_specimen_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `qualification_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WPSQualificationAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `selected_envelope_id` | `1` |
| `comparison_rows` | `mixed` |
| `qualification_test_ids` | `1` |
| `physical_specimen_ids` | `1` |
| `source_group_ids` | `1` |
| `invalid_qualification_evidence_ids` | `1` |
| `missing_production_variable_ids` | `1` |
| `unmatched_production_variable_ids` | `1` |
| `variables_without_supporting_evidence_ids` | `1` |
| `unit_mismatch_variable_ids` | `1` |
| `outside_declared_envelope_variable_ids` | `1` |
| `outside_essential_variable_ids` | `1` |
| `outside_supplementary_essential_variable_ids` | `1` |
| `outside_nonessential_variable_ids` | `1` |
| `requalification_required_variable_ids` | `1` |
| `all_variables_within_declared_envelope` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Qualified-procedure, revision, material-side, joint and welding-process identities match exactly.
- Variable kinds and unit tokens are never converted or inferred.
- Essential and supplementary-essential variables require valid caller-supplied test-evidence links with pinned provider state; nonessential variables are checked against their declared envelope without implying qualification-test support.

## 구현 근거·독립 설명

- `declared_wps_qualification_envelope_accounting`: Compare production welding-variable records with exact caller-owned qualified-procedure identities, units, ranges, categories and pinned specimen evidence. Do not bundle welding-code tables or make production acceptance decisions.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.wps_qualification_envelope"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.wps_qualification_envelope"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-wps-assessment",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "production_weld_id": "weld-1",
  "production_procedure_id": "wps-1",
  "production_procedure_revision": "rev-1",
  "base_material_side_a_condition_id": "base-a",
  "base_material_side_b_condition_id": "base-b",
  "joint_configuration_id": "joint-1",
  "welding_process_id": "process-1",
  "production_variables": [
    {
      "record_id": "record-1",
      "variable_id": "heat-input",
      "variable_kind": "numeric",
      "unit_token": "J/m",
      "numeric_value": 1000000.0,
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored production variable"
        }
      ]
    },
    {
      "record_id": "record-2",
      "variable_id": "transfer-mode",
      "variable_kind": "categorical",
      "unit_token": "1",
      "categorical_value_token": "spray",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored production variable"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "qualified_procedure_id": "wps-1",
      "qualified_procedure_revision": "rev-1",
      "base_material_side_a_condition_id": "base-a",
      "base_material_side_b_condition_id": "base-b",
      "joint_configuration_id": "joint-1",
      "welding_process_id": "process-1",
      "essential_variables": [
        {
          "variable_id": "heat-input",
          "variable_kind": "numeric",
          "unit_token": "J/m",
          "minimum_value": 800000.0,
          "maximum_value": 1200000.0,
          "applicability_basis": "authored qualification"
        },
        {
          "variable_id": "transfer-mode",
          "variable_kind": "categorical",
          "unit_token": "1",
          "supported_value_tokens": [
            "spray",
            "globular"
          ],
          "applicability_basis": "authored qualification"
        }
      ],
      "test_evidence": [
        {
          "evidence_record_id": "evidence-1",
          "qualification_test_id": "test-1",
          "physical_specimen_id": "specimen-1",
          "source_group_id": "source-group-1",
          "provider_id": "provider-1",
          "provider_revision": "1",
          "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
          "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
          "supported_variable_ids": [
            "heat-input",
            "transfer-mode"
          ],
          "record_valid": true,
          "supports_declared_envelope": true,
          "evidence": [
            {
              "source_id": "authored-example",
              "origin": "synthetic",
              "citation": "authored qualification evidence"
            }
          ]
        }
      ],
      "declaration_basis": "authored caller-owned qualification"
    }
  ],
  "production_procedure_identity_reviewed": true,
  "material_and_joint_identity_reviewed": true,
  "variable_records_reviewed": true,
  "qualification_specimen_identity_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "qualification_envelope_authority_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/wps_qualification.py#L187)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

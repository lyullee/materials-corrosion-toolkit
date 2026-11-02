# `inspection.pressure_test_eligibility`

**목적:** Test method, medium, pressure basis and component/material identities are caller-reviewed.

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
| `component_type_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `test_method_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `test_medium_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_basis` | 예 | `{"enum": ["absolute", "gauge", "differential"], "type": "string"}` | 계약·필드 설명 참조 |
| `proposed_test_pressure_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `minimum_test_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `maximum_test_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `stored_energy_value` | 아니오 | `{"anyOf": [{"minimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `stored_energy_unit_token` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `boundary_and_isolation_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `requirement_records` | 예 | `{"items": {"$ref": "#/$defs/PressureTestRequirementRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/DeclaredPressureTestEligibilityEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `component_material_and_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `test_method_medium_and_pressure_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pressure_and_temperature_plan_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `boundary_isolation_and_stored_energy_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `requirement_records_and_source_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `eligibility_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PressureTestEligibilityAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `physical_scope_id` | `1` |
| `selected_envelope_id` | `1` |
| `declared_eligibility_outcome` | `1` |
| `outside_support_reasons` | `1` |
| `unsatisfied_requirement_ids` | `1` |
| `requirement_comparisons` | `mixed` |
| `stored_energy_comparison` | `mixed` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Test method, medium, pressure basis and component/material identities are caller-reviewed.
- Pressure, temperature, stored-energy and prerequisite limits are caller-owned and not extrapolated.
- Requirement dispositions retain physical source-group and provider lineage.

## 구현 근거·독립 설명

- `reviewed_pressure_test_eligibility_envelope`: Compare exact component and material condition, test method, medium, pressure basis, planned pressure and temperature, stored-energy definition and complete prerequisite records with a caller-owned eligibility envelope. Preserve unsatisfied requirements as a computed outcome; do not supply code test pressures, structural capacity, fracture or leak risk, service fitness or regulatory acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.pressure_test_eligibility"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.pressure_test_eligibility"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-pressure-test",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "scope-1",
  "component_type_id": "vessel",
  "material_condition_id": "condition-1",
  "test_method_id": "hydro-method-1",
  "test_medium_id": "water-1",
  "pressure_basis": "gauge",
  "proposed_test_pressure_Pa": 1500000.0,
  "minimum_test_temperature_K": 290.0,
  "maximum_test_temperature_K": 300.0,
  "stored_energy_value": 12.0,
  "stored_energy_unit_token": "caller-energy-unit",
  "boundary_and_isolation_definition": "authored boundary and isolation",
  "requirement_records": [
    {
      "requirement_id": "boundary",
      "requirement_definition": "authored boundary requirement",
      "disposition": "satisfied",
      "physical_source_group_id": "source-boundary",
      "method_id": "review-method-1",
      "provider_id": "provider-1",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "disposition_basis": "authored review",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored requirement"
        }
      ]
    },
    {
      "requirement_id": "instrumentation",
      "requirement_definition": "authored instrumentation requirement",
      "disposition": "satisfied",
      "physical_source_group_id": "source-instrumentation",
      "method_id": "review-method-1",
      "provider_id": "provider-1",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "disposition_basis": "authored review",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored requirement"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "component_type_id": "vessel",
      "supported_material_condition_ids": [
        "condition-1"
      ],
      "test_method_id": "hydro-method-1",
      "supported_test_medium_ids": [
        "water-1"
      ],
      "pressure_basis": "gauge",
      "minimum_test_pressure_Pa": 1000000.0,
      "maximum_test_pressure_Pa": 2000000.0,
      "minimum_test_temperature_K": 280.0,
      "maximum_test_temperature_K": 320.0,
      "maximum_stored_energy_value": 20.0,
      "stored_energy_unit_token": "caller-energy-unit",
      "required_requirement_ids": [
        "boundary",
        "instrumentation"
      ],
      "provider_id": "envelope-provider",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "authority_basis": "authored eligibility plan",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored pressure-test envelope"
        }
      ]
    }
  ],
  "component_material_and_scope_reviewed": true,
  "test_method_medium_and_pressure_basis_reviewed": true,
  "pressure_and_temperature_plan_reviewed": true,
  "boundary_isolation_and_stored_energy_reviewed": true,
  "requirement_records_and_source_groups_reviewed": true,
  "provider_lineage_and_digests_reviewed": true,
  "eligibility_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored pressure-test assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/pressure_test_eligibility.py#L116)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

# `materials.brittle_applicability_evidence`

**목적:** Material, product form, condition, thickness, orientation and service descriptors are reviewed caller identities.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_specification_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `product_form_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `governing_thickness_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `governing_orientation_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `minimum_service_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `loading_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `loading_rate_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `test_records` | 예 | `{"items": {"$ref": "#/$defs/BrittleTestEvidenceRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/BrittleApplicabilityEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `material_specification_and_condition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `product_form_thickness_and_orientation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `service_temperature_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `loading_and_rate_descriptors_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_and_source_group_partitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `method_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_and_digest_lineage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `applicability_envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/BrittleApplicabilityEvidenceAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `selected_envelope_id` | `1` |
| `test_evidence_summary` | `mixed` |
| `evidence_requirement_summary` | `mixed` |
| `source_and_independence_group_partitions` | `mixed` |
| `unused_test_record_ids` | `1` |
| `missing_evidence_requirement_ids` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Material, product form, condition, thickness, orientation and service descriptors are reviewed caller identities.
- Every test value carries an exact unit token, expanded uncertainty and immutable provider lineage.

## 구현 근거·독립 설명

- `reviewed_brittle_test_applicability_evidence`: Preserve material, product form, condition, thickness, orientation, minimum service temperature, loading descriptors and partitioned impact or toughness evidence, then compare only with a caller-owned applicability envelope. Do not bundle exemption curves, convert reference temperatures, infer fracture, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "materials.brittle_applicability_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["materials.brittle_applicability_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-brittle",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "material_id": "heat-1",
  "material_specification_id": "spec-1",
  "product_form_id": "plate",
  "material_condition_id": "condition-1",
  "governing_thickness_m": 0.02,
  "governing_orientation_id": "transverse",
  "minimum_service_temperature_K": 240.0,
  "loading_descriptor": "membrane-plus-bending",
  "loading_rate_descriptor": "quasi-static",
  "test_records": [
    {
      "record_id": "record-1",
      "physical_specimen_id": "specimen-1",
      "source_group_id": "source-a",
      "independence_group_id": "source-a",
      "test_kind": "impact",
      "result_name": "absorbed_energy",
      "result_value": 35.0,
      "result_unit_token": "J",
      "expanded_uncertainty": 1.5,
      "uncertainty_coverage_factor": 2.0,
      "test_temperature_K": 250.0,
      "specimen_orientation_id": "transverse",
      "specimen_thickness_m": 0.01,
      "method_id": "caller-impact-method",
      "provider_id": "caller-laboratory",
      "provider_version": "2",
      "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "1111111111111111111111111111111111111111111111111111111111111111",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored brittle record"
        }
      ]
    },
    {
      "record_id": "record-2",
      "physical_specimen_id": "specimen-2",
      "source_group_id": "source-b",
      "independence_group_id": "source-b",
      "test_kind": "impact",
      "result_name": "absorbed_energy",
      "result_value": 40.0,
      "result_unit_token": "J",
      "expanded_uncertainty": 1.5,
      "uncertainty_coverage_factor": 2.0,
      "test_temperature_K": 250.0,
      "specimen_orientation_id": "transverse",
      "specimen_thickness_m": 0.01,
      "method_id": "caller-impact-method",
      "provider_id": "caller-laboratory",
      "provider_version": "2",
      "configuration_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "data_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "result_digest": "2222222222222222222222222222222222222222222222222222222222222222",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored brittle record"
        }
      ]
    }
  ],
  "candidate_envelopes": [
    {
      "envelope_id": "brittle-envelope-1",
      "material_specification_id": "spec-1",
      "product_form_id": "plate",
      "material_condition_id": "condition-1",
      "minimum_thickness_m": 0.005,
      "maximum_thickness_m": 0.05,
      "minimum_supported_service_temperature_K": 220.0,
      "maximum_supported_service_temperature_K": 300.0,
      "applicable_orientation_ids": [
        "transverse"
      ],
      "loading_descriptors": [
        "membrane-plus-bending"
      ],
      "loading_rate_descriptors": [
        "quasi-static"
      ],
      "evidence_requirements": [
        {
          "requirement_id": "impact-evidence",
          "test_kind": "impact",
          "result_name": "absorbed_energy",
          "result_unit_token": "J",
          "applicable_orientation_ids": [
            "transverse"
          ],
          "minimum_test_temperature_K": 240.0,
          "maximum_test_temperature_K": 260.0,
          "minimum_record_count": 2,
          "requirement_basis": "authored evidence plan"
        }
      ],
      "provider_id": "caller-envelope-provider",
      "provider_version": "1",
      "configuration_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "data_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "result_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "applicability_basis": "authored material program",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored brittle envelope"
        }
      ]
    }
  ],
  "material_specification_and_condition_reviewed": true,
  "product_form_thickness_and_orientation_reviewed": true,
  "service_temperature_reviewed": true,
  "loading_and_rate_descriptors_reviewed": true,
  "specimen_and_source_group_partitions_reviewed": true,
  "method_and_units_reviewed": true,
  "uncertainty_basis_reviewed": true,
  "provider_and_digest_lineage_reviewed": true,
  "applicability_envelope_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored brittle assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/brittle_applicability.py#L171)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

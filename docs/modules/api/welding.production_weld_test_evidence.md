# `welding.production_weld_test_evidence`

**목적:** Production-weld, procedure, material-lot and consumable-lot identities are caller-reviewed.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `production_weld_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `procedure_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `consumable_lot_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_lot_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `specimens` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/ProductionTestSpecimen"}, "type": "array"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/ProductionTestObservation"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `requirements` | 예 | `{"items": {"$ref": "#/$defs/CallerProductionTestRequirement"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `weld_procedure_and_lot_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `specimen_source_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `test_method_and_location_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `metric_definitions_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `uncertainty_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_identity_and_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `result_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `missingness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_requirement_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ProductionWeldTestEvidenceAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `production_weld_id` | `1` |
| `procedure_id` | `1` |
| `procedure_revision` | `1` |
| `consumable_lot_id` | `1` |
| `material_lot_id` | `1` |
| `specimen_count` | `1` |
| `invalid_specimen_source_mapping_ids` | `1` |
| `observation_count` | `1` |
| `unavailable_observation_ids` | `1` |
| `unknown_requirement_observation_ids` | `1` |
| `definition_mismatch_observation_ids` | `1` |
| `requirement_coverage` | `mixed` |
| `insufficient_requirement_ids` | `1` |
| `caller_requirement_comparisons` | `mixed` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Production-weld, procedure, material-lot and consumable-lot identities are caller-reviewed.
- Each destructive observation retains a physical specimen and source-group mapping.
- Requirements and dispositions are supplied by the caller and are not bundled code rules.

## 구현 근거·독립 설명

- `reviewed_production_weld_test_evidence`: Account for destructive and nondestructive production-weld observations with exact specimen, source-group, procedure, lot, method, metric, unit, uncertainty and provider lineage against caller-owned requirements. Do not declare acceptance or infer defects, fracture, life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "welding.production_weld_test_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["welding.production_weld_test_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-production-test",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "production_weld_id": "weld-1",
  "procedure_id": "procedure-1",
  "procedure_revision": "1",
  "consumable_lot_id": "consumable-lot-1",
  "material_lot_id": "material-lot-1",
  "specimens": [
    {
      "specimen_id": "specimen-1",
      "physical_source_group_id": "coupon-1",
      "extraction_location": "extension coupon",
      "orientation_definition": "caller longitudinal",
      "specimen_preparation_id": "prep-1",
      "source_mapping_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored production specimen"
        }
      ]
    }
  ],
  "observations": [
    {
      "observation_id": "observation-1",
      "requirement_id": "requirement-1",
      "test_kind": "destructive",
      "test_method_id": "method-1",
      "physical_source_group_id": "coupon-1",
      "specimen_id": "specimen-1",
      "examination_location": "gauge section",
      "metric_definition": "caller reported proof stress",
      "unit": "Pa",
      "observed_value": 320000000.0,
      "expanded_uncertainty": 5000000.0,
      "coverage_factor": 2.0,
      "uncertainty_basis": "authored uncertainty",
      "provider_id": "laboratory-1",
      "provider_version": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "result_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_available": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored production test"
        }
      ]
    }
  ],
  "requirements": [
    {
      "requirement_id": "requirement-1",
      "test_kind": "destructive",
      "test_method_id": "method-1",
      "metric_definition": "caller reported proof stress",
      "unit": "Pa",
      "minimum_value": 300000000.0,
      "maximum_expanded_uncertainty": 10000000.0,
      "minimum_available_record_count": 1,
      "minimum_distinct_physical_source_groups": 1,
      "requirement_basis": "authored caller plan",
      "disposition_id_if_outside": "engineering-review",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored production requirement"
        }
      ]
    }
  ],
  "weld_procedure_and_lot_identity_reviewed": true,
  "specimen_source_mapping_reviewed": true,
  "test_method_and_location_reviewed": true,
  "metric_definitions_and_units_reviewed": true,
  "uncertainty_records_reviewed": true,
  "provider_identity_and_state_reviewed": true,
  "result_digests_reviewed": true,
  "missingness_reviewed": true,
  "caller_requirement_authority_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored production-weld assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/welding_production_test.py#L149)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

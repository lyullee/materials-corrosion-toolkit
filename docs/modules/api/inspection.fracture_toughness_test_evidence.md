# `inspection.fracture_toughness_test_evidence`

**목적:** Every record preserves material condition, specimen/source identity, geometry/orientation, test conditions, endpoint, unit and caller-supplied validity evidence.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `evidence_collection_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `records` | 예 | `{"items": {"$ref": "#/$defs/FractureToughnessTestRecord"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `required_partitions` | 예 | `{"items": {"enum": ["calibration", "holdout", "application"], "type": "string"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `material_and_condition_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_specimen_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `source_group_and_partition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `geometry_and_orientation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_rate_and_environment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `endpoint_units_and_uncertainty_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `caller_validity_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_lineage_and_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FractureToughnessEvidenceAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `evidence_collection_id` | `1` |
| `record_count` | `count` |
| `material_ids` | `1` |
| `material_condition_ids` | `1` |
| `specimen_geometry_ids` | `1` |
| `notch_orientation_ids` | `1` |
| `crack_orientation_ids` | `1` |
| `environment_ids` | `1` |
| `required_partitions` | `1` |
| `missing_required_partitions` | `1` |
| `partition_summaries` | `mixed` |
| `invalid_record_ids` | `1` |
| `unsupported_endpoint_record_ids` | `1` |
| `missing_value_record_ids` | `1` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Every record preserves material condition, specimen/source identity, geometry/orientation, test conditions, endpoint, unit and caller-supplied validity evidence.
- Provider revision and state/configuration/input/result digests are immutable lineage fields, not physical qualification.
- Partitions are caller-declared and no independence beyond enforced specimen and source-group separation is inferred.

## 구현 근거·독립 설명

- `partitioned_fracture_toughness_test_evidence_accounting`: Preserve material, physical specimen, geometry, orientation, test condition, endpoint, raw unit, uncertainty, caller validity evidence and provider digests in separate calibration, holdout and application partitions. Do not apply standards validity tables, convert endpoints, create FAD inputs, life, probability or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.fracture_toughness_test_evidence"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.fracture_toughness_test_evidence"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "evidence_collection_id": "authored-toughness-evidence",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "records": [
    {
      "record_id": "record-1",
      "physical_specimen_id": "specimen-1",
      "source_group_id": "source-1",
      "partition": "calibration",
      "material_id": "material-1",
      "material_condition_id": "condition-1",
      "specimen_geometry_id": "geometry-1",
      "specimen_geometry_descriptor": "authored geometry",
      "notch_orientation_id": "notch-L",
      "crack_orientation_id": "crack-T",
      "temperature_K": 293.15,
      "load_rate_value": 1.0,
      "load_rate_unit_token": "custom-rate",
      "environment_id": "laboratory-air",
      "endpoint_kind": "initiation",
      "endpoint_definition_id": "caller-initiation",
      "reported_value": 101.0,
      "reported_unit_token": "custom-toughness",
      "expanded_uncertainty": 5.0,
      "uncertainty_basis": "authored uncertainty",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "caller_validity_record_id": "validity-1",
      "record_valid": true,
      "supports_declared_endpoint": true,
      "validity_evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored validity evidence"
        }
      ]
    },
    {
      "record_id": "record-2",
      "physical_specimen_id": "specimen-2",
      "source_group_id": "source-2",
      "partition": "holdout",
      "material_id": "material-1",
      "material_condition_id": "condition-1",
      "specimen_geometry_id": "geometry-1",
      "specimen_geometry_descriptor": "authored geometry",
      "notch_orientation_id": "notch-L",
      "crack_orientation_id": "crack-T",
      "temperature_K": 293.15,
      "load_rate_value": 1.0,
      "load_rate_unit_token": "custom-rate",
      "environment_id": "laboratory-air",
      "endpoint_kind": "initiation",
      "endpoint_definition_id": "caller-initiation",
      "reported_value": 102.0,
      "reported_unit_token": "custom-toughness",
      "expanded_uncertainty": 5.0,
      "uncertainty_basis": "authored uncertainty",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "caller_validity_record_id": "validity-2",
      "record_valid": true,
      "supports_declared_endpoint": true,
      "validity_evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored validity evidence"
        }
      ]
    },
    {
      "record_id": "record-3",
      "physical_specimen_id": "specimen-3",
      "source_group_id": "source-3",
      "partition": "application",
      "material_id": "material-1",
      "material_condition_id": "condition-1",
      "specimen_geometry_id": "geometry-1",
      "specimen_geometry_descriptor": "authored geometry",
      "notch_orientation_id": "notch-L",
      "crack_orientation_id": "crack-T",
      "temperature_K": 293.15,
      "load_rate_value": 1.0,
      "load_rate_unit_token": "custom-rate",
      "environment_id": "laboratory-air",
      "endpoint_kind": "initiation",
      "endpoint_definition_id": "caller-initiation",
      "reported_value": 103.0,
      "reported_unit_token": "custom-toughness",
      "expanded_uncertainty": 5.0,
      "uncertainty_basis": "authored uncertainty",
      "provider_id": "provider-1",
      "provider_revision": "1",
      "provider_state_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "provider_configuration_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "input_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "result_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "caller_validity_record_id": "validity-3",
      "record_valid": true,
      "supports_declared_endpoint": true,
      "validity_evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored validity evidence"
        }
      ]
    }
  ],
  "required_partitions": [
    "calibration",
    "holdout",
    "application"
  ],
  "material_and_condition_identity_reviewed": true,
  "physical_specimen_identity_reviewed": true,
  "source_group_and_partition_reviewed": true,
  "geometry_and_orientation_reviewed": true,
  "temperature_rate_and_environment_reviewed": true,
  "endpoint_units_and_uncertainty_reviewed": true,
  "caller_validity_evidence_reviewed": true,
  "provider_lineage_and_digests_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fracture_toughness_evidence.py#L113)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

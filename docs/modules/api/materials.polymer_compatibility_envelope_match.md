# `materials.polymer_compatibility_envelope_match`

**목적:** Material, media, unit and loading identifiers are compared exactly without aliases or hidden conversions.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `polymer_grade_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `polymer_lot_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `polymer_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `media_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `media_composition_description` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `concentration` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `concentration_unit_token` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `pressure_Pa_abs` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `exposure_duration_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `mechanical_loading_descriptor` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `candidate_envelopes` | 예 | `{"items": {"$ref": "#/$defs/PolymerCompatibilityEnvelope"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `material_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `media_identity_and_concentration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_pressure_duration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `mechanical_loading_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `envelope_authority_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `lot_transfer_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PolymerCompatibilityAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `polymer_grade_id` | `1` |
| `polymer_lot_id` | `1` |
| `polymer_condition_id` | `1` |
| `media_id` | `1` |
| `selected_envelope_id` | `1` |
| `identity_matching_envelope_ids` | `1` |
| `fully_matching_envelope_ids` | `1` |
| `candidate_diagnostics` | `mixed` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Material, media, unit and loading identifiers are compared exactly without aliases or hidden conversions.
- Temperature, absolute pressure, concentration and exposure duration are checked only against caller-qualified ranges.
- Grade-level transfer across lots requires an explicit reviewed declaration.

## 구현 근거·독립 설명

- `declared_polymer_compatibility_envelope`: Match reviewed polymer grade, lot or explicitly authorized grade-level transfer, condition, medium, concentration-unit convention and loading descriptor to caller-owned compatibility envelopes, then compare temperature, absolute pressure, concentration and duration support. Do not infer swelling, permeation, degradation rate, lifetime, mixture effects or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "materials.polymer_compatibility_envelope_match"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["materials.polymer_compatibility_envelope_match"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "assessment_id": "authored-polymer-example",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "polymer_grade_id": "polymer-grade-a",
  "polymer_lot_id": "lot-1",
  "polymer_condition_id": "as-molded",
  "media_id": "authored-medium",
  "media_composition_description": "authored single medium",
  "concentration": 10.0,
  "concentration_unit_token": "mass_percent",
  "temperature_K": 320.0,
  "pressure_Pa_abs": 200000.0,
  "exposure_duration_s": 100000.0,
  "mechanical_loading_descriptor": "static-seal-compression",
  "candidate_envelopes": [
    {
      "envelope_id": "envelope-1",
      "polymer_grade_id": "polymer-grade-a",
      "polymer_condition_id": "as-molded",
      "lot_applicability": "exact_lots",
      "applicable_lot_ids": [
        "lot-1"
      ],
      "media_id": "authored-medium",
      "concentration_min": 5.0,
      "concentration_max": 15.0,
      "concentration_unit_token": "mass_percent",
      "temperature_min_K": 280.0,
      "temperature_max_K": 350.0,
      "pressure_min_Pa_abs": 90000.0,
      "pressure_max_Pa_abs": 500000.0,
      "maximum_exposure_duration_s": 1000000.0,
      "applicable_mechanical_loading_descriptors": [
        "static-seal-compression"
      ],
      "qualification_source_id": "authored-source",
      "applicability_basis": "caller-owned envelope",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored polymer envelope"
        }
      ]
    }
  ],
  "material_identity_reviewed": true,
  "media_identity_and_concentration_reviewed": true,
  "temperature_pressure_duration_reviewed": true,
  "mechanical_loading_reviewed": true,
  "envelope_authority_reviewed": true,
  "lot_transfer_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored polymer assessment"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/polymer_compatibility.py#L113)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

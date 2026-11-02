# `degradation.under_insulation_exposure_history`

**목적:** Surface temperature, wetness and insulation condition are piecewise-constant reviewed observations over explicit intervals.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `record_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_model_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `source_result_digest` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `wetness_state_semantics` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `horizon_start_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `horizon_end_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `intervals` | 예 | `{"items": {"$ref": "#/$defs/InsulationExposureInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `exposure_definition` | 예 | `{"$ref": "#/$defs/DeclaredUnderInsulationExposure"}` | 계약·필드 설명 참조 |
| `clock_and_coverage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `temperature_measurement_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `wetness_state_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `insulation_condition_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `exposure_definition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/UnderInsulationExposureHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `record_id` | `1` |
| `definition_id` | `1` |
| `horizon_duration_s` | `s` |
| `represented_interval_duration_s` | `s` |
| `invalid_interval_duration_s` | `s` |
| `uncovered_interval_duration_s` | `s` |
| `missing_interval_duration_s` | `s` |
| `classified_exposure_duration_s` | `s` |
| `maximum_continuous_classified_exposure_s` | `s` |
| `classified_exposure_interval_ids` | `1` |
| `interval_rows` | `mixed` |
| `missing_reviews` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Surface temperature, wetness and insulation condition are piecewise-constant reviewed observations over explicit intervals.
- The exposure definition and every included state identifier are supplied by the caller.

## 구현 근거·독립 설명

- `declared_under_insulation_exposure_accounting`: Classify explicit reviewed insulation intervals only when surface temperature, wetness state and insulation-condition state fall inside a caller-owned exposure definition. Preserve invalid and uncovered time without predicting corrosion rate, metal loss, cracking, remaining life or failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.under_insulation_exposure_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.under_insulation_exposure_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "record_id": "authored-cui-example",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "clock_id": "authored-exposure-clock",
  "horizon_start_s": 0.0,
  "horizon_end_s": 300.0,
  "intervals": [
    {
      "interval_id": "i1",
      "start_time_s": 0.0,
      "end_time_s": 150.0,
      "record_valid": true,
      "surface_temperature_K": 330.0,
      "wetness_state_id": "wet",
      "insulation_condition_id": "damaged",
      "missing_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored insulation interval"
        }
      ]
    },
    {
      "interval_id": "i2",
      "start_time_s": 150.0,
      "end_time_s": 300.0,
      "record_valid": true,
      "surface_temperature_K": 330.0,
      "wetness_state_id": "dry",
      "insulation_condition_id": "damaged",
      "missing_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored insulation interval"
        }
      ]
    }
  ],
  "exposure_definition": {
    "definition_id": "definition-1",
    "minimum_surface_temperature_K": 300.0,
    "maximum_surface_temperature_K": 360.0,
    "included_wetness_state_ids": [
      "wet"
    ],
    "included_insulation_condition_ids": [
      "damaged"
    ],
    "definition_basis": "caller-owned exposure definition",
    "evidence": [
      {
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "authored CUI definition"
      }
    ]
  },
  "clock_and_coverage_reviewed": true,
  "temperature_measurement_reviewed": true,
  "wetness_state_mapping_reviewed": true,
  "insulation_condition_mapping_reviewed": true,
  "exposure_definition_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/under_insulation.py#L95)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

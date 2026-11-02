# `fabrication.storage_preservation_history`

**목적:** Piecewise-constant environment observations remain separate from caller-declared temperature, humidity, preservation-state and inspection-spacing limits.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `record_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `horizon_start_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `horizon_end_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `environment_intervals` | 예 | `{"items": {"$ref": "#/$defs/PreservationEnvironmentInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `inspections` | 아니오 | `{"items": {"$ref": "#/$defs/PreservationInspection"}, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_allowed_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `maximum_allowed_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `minimum_allowed_relative_humidity_fraction` | 예 | `{"maximum": 1, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_allowed_relative_humidity_fraction` | 예 | `{"maximum": 1, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `allowed_preservation_state_ids` | 예 | `{"items": {"type": "string"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_inspection_interval_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `clock_and_coverage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `environment_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `preservation_state_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `declared_limits_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `inspection_records_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/StoragePreservationHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `horizon_duration_s` | `s` |
| `represented_environment_duration_s` | `s` |
| `valid_environment_duration_s` | `s` |
| `invalid_environment_duration_s` | `s` |
| `uncovered_environment_duration_s` | `s` |
| `missing_environment_duration_s` | `s` |
| `temperature_outside_duration_s` | `s` |
| `humidity_outside_duration_s` | `s` |
| `preservation_state_outside_duration_s` | `s` |
| `any_declared_limit_outside_duration_s` | `s` |
| `maximum_continuous_temperature_outside_s` | `s` |
| `maximum_continuous_humidity_outside_s` | `s` |
| `maximum_continuous_preservation_state_outside_s` | `s` |
| `maximum_continuous_any_declared_limit_outside_s` | `s` |
| `inspection_gap_s` | `s` |
| `inspection_overdue_duration_s` | `s` |
| `total_inspection_overdue_duration_s` | `s` |
| `maximum_inspection_overdue_duration_s` | `s` |
| `inspection_interval_exceeded` | `1` |
| `environment_timeline` | `structured_record` |
| `inspection_schedule` | `structured_record` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Piecewise-constant environment observations remain separate from caller-declared temperature, humidity, preservation-state and inspection-spacing limits.
- Uncovered or invalid intervals stop a complete-history result and are not replaced, interpolated or classified as acceptable exposure.
- Timeline rows partition the declared horizon; uncovered spans remain explicit and are not imputed.

## 구현 근거·독립 설명

- `storage_preservation_interval_accounting`: Partition the full preservation horizon at ordered environment-record and inspection boundaries, retain source interval and inspection IDs with observed, invalid and uncovered spans, and report caller-declared temperature, humidity, preservation-state excursions and inspection-spacing overrun. Use a single forward sweep over sorted interval boundaries. Do not bridge missing intervals or supply preservation requirements, damage rates, remaining life or acceptance decisions.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.storage_preservation_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.storage_preservation_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "record_id": "authored-storage-example",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "clock_id": "authored-storage-clock",
  "horizon_start_s": 0.0,
  "horizon_end_s": 300.0,
  "environment_intervals": [
    {
      "interval_id": "interval-1",
      "start_time_s": 0.0,
      "end_time_s": 300.0,
      "record_valid": true,
      "temperature_K": 290.0,
      "relative_humidity_fraction": 0.4,
      "preservation_state_id": "intact",
      "missing_basis": null,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored storage interval"
        }
      ]
    }
  ],
  "inspections": [
    {
      "inspection_id": "inspection-1",
      "inspection_time_s": 150.0,
      "reported_disposition": "authored intact disposition",
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored inspection"
        }
      ]
    }
  ],
  "minimum_allowed_temperature_K": 280.0,
  "maximum_allowed_temperature_K": 300.0,
  "minimum_allowed_relative_humidity_fraction": 0.2,
  "maximum_allowed_relative_humidity_fraction": 0.6,
  "allowed_preservation_state_ids": [
    "intact"
  ],
  "maximum_inspection_interval_s": 200.0,
  "clock_and_coverage_reviewed": true,
  "environment_units_reviewed": true,
  "preservation_state_mapping_reviewed": true,
  "declared_limits_reviewed": true,
  "inspection_records_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored preservation history"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/storage_preservation.py#L120)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

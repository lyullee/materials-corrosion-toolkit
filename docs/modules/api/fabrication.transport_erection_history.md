# `fabrication.transport_erection_history`

**목적:** Ordered handling, transport and erection activity intervals remain separate from metric observations, inspections and caller-owned limits.

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
| `activity_intervals` | 예 | `{"items": {"$ref": "#/$defs/HandlingActivityInterval"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `metric_observations` | 아니오 | `{"items": {"$ref": "#/$defs/TransportMetricObservation"}, "type": "array"}` | 계약·필드 설명 참조 |
| `metric_limits` | 아니오 | `{"items": {"$ref": "#/$defs/TransportMetricLimit"}, "type": "array"}` | 계약·필드 설명 참조 |
| `inspections` | 아니오 | `{"items": {"$ref": "#/$defs/HandlingInspection"}, "type": "array"}` | 계약·필드 설명 참조 |
| `required_inspection_stage_ids` | 아니오 | `{"items": {"type": "string"}, "type": "array"}` | 계약·필드 설명 참조 |
| `clock_and_activity_coverage_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `metric_identity_and_units_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `metric_limits_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `inspection_stage_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `disposition_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/TransportErectionHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `horizon_duration_s` | `s` |
| `represented_activity_duration_s` | `s` |
| `invalid_activity_duration_s` | `s` |
| `uncovered_activity_duration_s` | `s` |
| `missing_activity_duration_s` | `s` |
| `metric_observation_count` | `count` |
| `outside_declared_limit_count` | `count` |
| `inspection_count` | `count` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Ordered handling, transport and erection activity intervals remain separate from metric observations, inspections and caller-owned limits.
- Missing coverage, invalid records, unmatched metrics, unit conflicts and absent caller-required inspection stages prevent a complete-history result.

## 구현 근거·독립 설명

- `transport_erection_record_accounting`: Account for explicit handling, transport and erection intervals, metric observations, caller-owned limits and required inspection stages. Preserve activity gaps, invalid records, unmatched metrics, unit conflicts and caller dispositions without inferring damage, remaining life or acceptance.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.transport_erection_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fabrication.transport_erection_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "record_id": "authored-transport-example",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "clock_id": "authored-transport-clock",
  "horizon_start_s": 0.0,
  "horizon_end_s": 200.0,
  "activity_intervals": [
    {
      "interval_id": "road",
      "activity_id": "road-leg-1",
      "activity_kind": "transport",
      "start_time_s": 0.0,
      "end_time_s": 100.0,
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored transport interval"
        }
      ]
    },
    {
      "interval_id": "erection",
      "activity_id": "lift-1",
      "activity_kind": "lifting_and_erection",
      "start_time_s": 100.0,
      "end_time_s": 200.0,
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored erection interval"
        }
      ]
    }
  ],
  "metric_observations": [
    {
      "observation_id": "shock-1",
      "interval_id": "road",
      "observation_time_s": 50.0,
      "metric_id": "peak_acceleration",
      "value": 4.0,
      "unit": "m/s^2",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored transport metric"
        }
      ]
    }
  ],
  "metric_limits": [
    {
      "metric_id": "peak_acceleration",
      "metric_definition": "authored sensor-axis peak",
      "unit": "m/s^2",
      "minimum_value": null,
      "maximum_value": 5.0,
      "limit_basis": "caller plan",
      "caller_disposition_id_if_outside": "review-shock"
    }
  ],
  "inspections": [
    {
      "inspection_id": "pre",
      "stage_id": "pre_lift",
      "inspection_time_s": 100.0,
      "inspection_type": "authored visual check",
      "reported_finding": "authored no change",
      "caller_disposition_id": null,
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored inspection"
        }
      ]
    },
    {
      "inspection_id": "post",
      "stage_id": "post_erection",
      "inspection_time_s": 200.0,
      "inspection_type": "authored visual check",
      "reported_finding": "authored no change",
      "caller_disposition_id": "next-stage",
      "record_valid": true,
      "evidence": [
        {
          "source_id": "authored-example",
          "origin": "synthetic",
          "citation": "authored inspection"
        }
      ]
    }
  ],
  "required_inspection_stage_ids": [
    "pre_lift",
    "post_erection"
  ],
  "clock_and_activity_coverage_reviewed": true,
  "metric_identity_and_units_reviewed": true,
  "metric_limits_reviewed": true,
  "inspection_stage_mapping_reviewed": true,
  "disposition_mapping_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-example",
      "origin": "synthetic",
      "citation": "authored transport history"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/transport_erection.py#L311)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

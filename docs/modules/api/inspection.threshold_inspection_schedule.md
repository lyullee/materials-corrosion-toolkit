# `inspection.threshold_inspection_schedule`

**목적:** Caller-reviewed cumulative first-crossing probabilities on strictly ordered candidate times; select the latest supplied candidate within notice and deferral limits that satisfies a user-approved probability criterion without interpolation or consequence optimization.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.threshold_inspection_schedule.v1", "default": "matintegrity.threshold_inspection_schedule.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `schedule_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `conditioning` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_probability_meaning` | 예 | `{"const": "conditional_first_failure_in_period", "type": "string"}` | 계약·필드 설명 참조 |
| `forecast_model_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `forecast_model_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `forecast_input_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `forecast_points` | 예 | `{"items": {"$ref": "#/$defs/InspectionForecastPoint"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `probability_basis` | 예 | `{"enum": ["estimate", "upper_bound"], "type": "string"}` | 계약·필드 설명 참조 |
| `maximum_probability_before_inspection` | 예 | `{"exclusiveMaximum": 1.0, "exclusiveMinimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |
| `minimum_notice_s` | 아니오 | `{"default": 0.0, "minimum": 0, "type": "number"}` | s |
| `maximum_deferral_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `forecast_identity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `event_scope_and_conditioning_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `cumulative_probability_curve_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `scheduling_criterion_user_approved` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ThresholdInspectionSchedule.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `assessment_time_s` | `s` |
| `maximum_probability_before_inspection` | `1` |
| `candidate_window_start_s` | `s` |
| `candidate_window_end_s` | `s` |
| `earliest_candidate_time_s` | `s` |
| `earliest_candidate_probability` | `1` |
| `selected_inspection_time_s` | `s` |
| `selected_time_from_assessment_s` | `s` |
| `selected_probability_given_survival` | `1` |
| `selected_probability_estimate` | `1` |
| `selected_probability_upper_bound` | `1` |
| `probability_margin_to_criterion` | `1` |
| `next_noncompliant_candidate_time_s` | `s` |
| `next_noncompliant_candidate_probability` | `1` |
| `forecast_support_end_s` | `s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-reviewed cumulative first-crossing probabilities on strictly ordered candidate times; select the latest supplied candidate within notice and deferral limits that satisfies a user-approved probability criterion without interpolation or consequence optimization.

## 구현 근거·독립 설명

- `threshold_inspection_schedule_definition`: Preserve one reviewed cumulative first-crossing probability curve, event definition, physical scope, survival conditioning, forecast model revision and input digest. Inside caller-declared notice and maximum-deferral limits, select the latest supplied candidate whose estimate or supplied upper bound satisfies a user-approved probability criterion. Refuse mixed or nonmonotone probability curves, incomplete upper bounds and missing review gates. Do not interpolate between times, extrapolate beyond forecast support, optimize consequence, infer inspection effectiveness or convert a point-in-time state probability into a first-crossing probability.

확률 의미: `{"earliest_candidate_probability": "conditional_first_failure_in_period", "selected_probability_given_survival": "conditional_first_failure_in_period", "selected_probability_estimate": "conditional_first_failure_in_period", "selected_probability_upper_bound": "conditional_first_failure_in_period", "next_noncompliant_candidate_probability": "conditional_first_failure_in_period"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.threshold_inspection_schedule"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.threshold_inspection_schedule"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schedule_id": "synthetic-threshold-schedule",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "synthetic-wall-location",
  "event_id": "synthetic-first-threshold-crossing",
  "event_definition": "first crossing of an independently authored synthetic limit",
  "assessment_time_s": 0.0,
  "conditioning": "synthetic asset has not crossed the declared limit at assessment time",
  "event_probability_meaning": "conditional_first_failure_in_period",
  "forecast_model_id": "synthetic.forecast",
  "forecast_model_revision": "1",
  "forecast_input_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "forecast_points": [
    {
      "forecast_point_id": "year-1",
      "horizon_end_s": 31557600.0,
      "cumulative_probability_given_survival": 0.01,
      "cumulative_probability_upper_bound": 0.02
    },
    {
      "forecast_point_id": "year-2",
      "horizon_end_s": 63115200.0,
      "cumulative_probability_given_survival": 0.03,
      "cumulative_probability_upper_bound": 0.05
    },
    {
      "forecast_point_id": "year-3",
      "horizon_end_s": 94672800.0,
      "cumulative_probability_given_survival": 0.07,
      "cumulative_probability_upper_bound": 0.09
    }
  ],
  "probability_basis": "upper_bound",
  "maximum_probability_before_inspection": 0.06,
  "minimum_notice_s": 0.0,
  "maximum_deferral_s": 94672800.0,
  "forecast_identity_reviewed": true,
  "event_scope_and_conditioning_reviewed": true,
  "cumulative_probability_curve_reviewed": true,
  "scheduling_criterion_user_approved": true,
  "evidence": [
    {
      "source_id": "authored-schedule-example",
      "origin": "synthetic",
      "citation": "independently authored monotone probability example"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/inspection.py#L857)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

# `inspection.finite_policy_probability_calibration`

**목적:** Reviewed finite physical-state truth, inspection labels and action-conditioned longitudinal transitions with immutable, sequence- and source-group-disjoint calibration/holdout partitions; weighted empirical frequencies and an explicit symmetric pseudocount only.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.finite_policy_probability_calibration.v1", "default": "matintegrity.finite_policy_probability_calibration.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `states` | 예 | `{"items": {"$ref": "#/$defs/FinitePolicyState"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `observation_labels` | 예 | `{"items": {"$ref": "#/$defs/PolicyObservationLabel"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `actions` | 예 | `{"items": {"$ref": "#/$defs/PolicyCalibrationAction"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `observation_records` | 예 | `{"items": {"$ref": "#/$defs/PolicyObservationCalibrationRecord"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `transition_records` | 예 | `{"items": {"$ref": "#/$defs/PolicyTransitionCalibrationRecord"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `symmetric_pseudocount` | 아니오 | `{"default": 0.0, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `state_definitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_state_truth_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_labels_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `action_assignments_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calibration_holdout_partition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `smoothing_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FinitePolicyProbabilityCalibration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `probability_given_state` | `1` |
| `probability_given_state_and_action` | `1` |
| `mean_negative_log_likelihood` | `1` |
| `multiclass_brier_score` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Reviewed finite physical-state truth, inspection labels and action-conditioned longitudinal transitions with immutable, sequence- and source-group-disjoint calibration/holdout partitions; weighted empirical frequencies and an explicit symmetric pseudocount only.

## 구현 근거·독립 설명

- `finite_policy_probability_calibration_definition`: Estimate finite state-conditional observation probabilities and action-conditioned state-transition probabilities from caller-reviewed weighted records. Require explicit physical-state truth, inspection labels, action assignments, ordered transition intervals and immutable calibration or holdout membership. Reject any sequence or source group crossing between partitions. Apply only a caller-declared symmetric pseudocount, report unsupported conditioning rows instead of inventing them, and score untouched holdout records with multiclass Brier score and negative log likelihood. Preserve exactly zero holdout probabilities as a diagnostic rather than clipping them. Do not infer record independence, confidence intervals, state definitions, labels, actions, feature matching, physical truth, transition causality or field applicability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.finite_policy_probability_calibration"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.finite_policy_probability_calibration"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.finite_policy_probability_calibration.v1",
  "calibration_id": "synthetic-reviewed-policy-calibration",
  "states": [
    {
      "state_id": "healthy",
      "state_definition": "reviewed synthetic healthy state",
      "is_failure_state": false
    },
    {
      "state_id": "degraded",
      "state_definition": "reviewed synthetic degraded state",
      "is_failure_state": false
    },
    {
      "state_id": "failure",
      "state_definition": "reviewed synthetic failure state",
      "is_failure_state": true
    }
  ],
  "observation_labels": [
    {
      "observation_id": "clear",
      "observation_definition": "reviewed synthetic clear label"
    },
    {
      "observation_id": "alert",
      "observation_definition": "reviewed synthetic alert label"
    }
  ],
  "actions": [
    {
      "action_id": "monitor",
      "action_definition": "reviewed synthetic monitoring action"
    },
    {
      "action_id": "repair",
      "action_definition": "reviewed synthetic repair action"
    }
  ],
  "observation_records": [
    {
      "record_id": "o1",
      "sequence_id": "fit-oh",
      "source_group_id": "fit-oh",
      "partition": "calibration",
      "observation_time_s": 1.0,
      "true_state_id": "healthy",
      "observed_label_id": "clear",
      "weight": 3.0
    },
    {
      "record_id": "o2",
      "sequence_id": "fit-oh",
      "source_group_id": "fit-oh",
      "partition": "calibration",
      "observation_time_s": 1.0,
      "true_state_id": "healthy",
      "observed_label_id": "alert",
      "weight": 1.0
    },
    {
      "record_id": "o3",
      "sequence_id": "fit-od",
      "source_group_id": "fit-od",
      "partition": "calibration",
      "observation_time_s": 1.0,
      "true_state_id": "degraded",
      "observed_label_id": "clear",
      "weight": 1.0
    },
    {
      "record_id": "o4",
      "sequence_id": "fit-od",
      "source_group_id": "fit-od",
      "partition": "calibration",
      "observation_time_s": 1.0,
      "true_state_id": "degraded",
      "observed_label_id": "alert",
      "weight": 3.0
    },
    {
      "record_id": "oh1",
      "sequence_id": "hold-oh",
      "source_group_id": "hold-oh",
      "partition": "holdout",
      "observation_time_s": 2.0,
      "true_state_id": "healthy",
      "observed_label_id": "clear",
      "weight": 1.0
    },
    {
      "record_id": "oh2",
      "sequence_id": "hold-od",
      "source_group_id": "hold-od",
      "partition": "holdout",
      "observation_time_s": 2.0,
      "true_state_id": "degraded",
      "observed_label_id": "alert",
      "weight": 1.0
    }
  ],
  "transition_records": [
    {
      "record_id": "t1",
      "sequence_id": "fit-hm",
      "source_group_id": "fit-hm",
      "partition": "calibration",
      "interval_start_s": 1.0,
      "interval_end_s": 2.0,
      "from_state_id": "healthy",
      "action_id": "monitor",
      "to_state_id": "healthy",
      "weight": 4.0
    },
    {
      "record_id": "t2",
      "sequence_id": "fit-hm",
      "source_group_id": "fit-hm",
      "partition": "calibration",
      "interval_start_s": 1.0,
      "interval_end_s": 2.0,
      "from_state_id": "healthy",
      "action_id": "monitor",
      "to_state_id": "failure",
      "weight": 1.0
    },
    {
      "record_id": "t3",
      "sequence_id": "fit-hr",
      "source_group_id": "fit-hr",
      "partition": "calibration",
      "interval_start_s": 1.0,
      "interval_end_s": 2.0,
      "from_state_id": "healthy",
      "action_id": "repair",
      "to_state_id": "healthy",
      "weight": 1.0
    },
    {
      "record_id": "t4",
      "sequence_id": "fit-dm",
      "source_group_id": "fit-dm",
      "partition": "calibration",
      "interval_start_s": 1.0,
      "interval_end_s": 2.0,
      "from_state_id": "degraded",
      "action_id": "monitor",
      "to_state_id": "degraded",
      "weight": 3.0
    },
    {
      "record_id": "t5",
      "sequence_id": "fit-dm",
      "source_group_id": "fit-dm",
      "partition": "calibration",
      "interval_start_s": 1.0,
      "interval_end_s": 2.0,
      "from_state_id": "degraded",
      "action_id": "monitor",
      "to_state_id": "failure",
      "weight": 2.0
    },
    {
      "record_id": "t6",
      "sequence_id": "fit-dr",
      "source_group_id": "fit-dr",
      "partition": "calibration",
      "interval_start_s": 1.0,
      "interval_end_s": 2.0,
      "from_state_id": "degraded",
      "action_id": "repair",
      "to_state_id": "healthy",
      "weight": 1.0
    },
    {
      "record_id": "th1",
      "sequence_id": "hold-h",
      "source_group_id": "hold-h",
      "partition": "holdout",
      "interval_start_s": 2.0,
      "interval_end_s": 3.0,
      "from_state_id": "healthy",
      "action_id": "monitor",
      "to_state_id": "healthy",
      "weight": 1.0
    },
    {
      "record_id": "th2",
      "sequence_id": "hold-d",
      "source_group_id": "hold-d",
      "partition": "holdout",
      "interval_start_s": 2.0,
      "interval_end_s": 3.0,
      "from_state_id": "degraded",
      "action_id": "monitor",
      "to_state_id": "failure",
      "weight": 1.0
    }
  ],
  "symmetric_pseudocount": 0.0,
  "state_definitions_reviewed": true,
  "physical_state_truth_reviewed": true,
  "observation_labels_reviewed": true,
  "action_assignments_reviewed": true,
  "calibration_holdout_partition_reviewed": true,
  "smoothing_basis_reviewed": true,
  "evidence": [
    {
      "source_id": "authored-policy-calibration-example",
      "origin": "synthetic",
      "citation": "independently authored weighted-count example"
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/inspection.py#L1551)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

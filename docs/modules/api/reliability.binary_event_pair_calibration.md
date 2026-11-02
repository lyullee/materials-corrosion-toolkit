# `reliability.binary_event_pair_calibration`

**목적:** Calibration and holdout physical sequences, source groups and independence groups are disjoint.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `calibration_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observation_clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_a_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_a_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_b_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_b_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `observations` | 예 | `{"items": {"$ref": "#/$defs/BinaryEventPairObservation"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `symmetric_cell_pseudocount` | 아니오 | `{"anyOf": [{"minimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `pseudocount_basis` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `minimum_calibration_record_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_record_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_calibration_sequence_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_sequence_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_calibration_source_group_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_source_group_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `minimum_holdout_independence_group_count` | 예 | `{"minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `event_definitions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `observation_clock_and_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `partition_assignments_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_sequence_source_and_independence_groups_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `sample_weights_and_missingness_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `pseudocount_choice_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `record_digests_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/BinaryEventPairCalibration.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `calibration_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `physical_scope_id` | `1` |
| `observation_clock_id` | `1` |
| `event_ids` | `1` |
| `cell_order` | `1` |
| `calibration_raw_record_counts` | `1` |
| `calibration_weighted_cell_totals` | `weight` |
| `calibration_cell_probabilities` | `1` |
| `calibration_event_a_probability` | `1` |
| `calibration_event_b_probability` | `1` |
| `calibration_joint_probability` | `1` |
| `calibration_covariance` | `1` |
| `calibration_phi` | `1` |
| `symmetric_cell_pseudocount` | `weight` |
| `holdout_raw_record_counts` | `1` |
| `holdout_weighted_cell_totals` | `weight` |
| `holdout_empirical_cell_probabilities` | `1` |
| `holdout_mean_negative_log_score` | `1` |
| `holdout_zero_probability_observation_weight` | `weight` |
| `holdout_multiclass_brier_score` | `1` |
| `calibration_sequence_ids` | `1` |
| `holdout_sequence_ids` | `1` |
| `calibration_source_group_ids` | `1` |
| `holdout_source_group_ids` | `1` |
| `holdout_independence_group_ids` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Calibration and holdout physical sequences, source groups and independence groups are disjoint.
- Weights and any symmetric cell pseudocount are explicit caller-reviewed inputs.
- Empirical pair probabilities are observation-distribution diagnostics, not FTA or future risk.

## 구현 근거·독립 설명

- `reviewed_binary_event_pair_calibration_holdout_observations`: Form a weighted binary 2-by-2 event table from explicitly partitioned calibration observations and report marginals, joint frequency, covariance, phi and holdout category scores. Preserve physical sequence and independence groups; do not claim causality, independence, future-period probability or automatic FTA suitability.

확률 의미: `{"calibration_event_a_probability": "unscoped_event_probability", "calibration_event_b_probability": "unscoped_event_probability", "calibration_joint_probability": "unscoped_event_probability"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "reliability.binary_event_pair_calibration"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["reliability.binary_event_pair_calibration"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "calibration_id": "calibration-1",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "scope-1",
  "observation_clock_id": "clock-1",
  "time_basis": "observation-clock",
  "event_a_id": "event-a",
  "event_a_definition": "caller observed event A in one observation interval",
  "event_b_id": "event-b",
  "event_b_definition": "caller observed event B in one observation interval",
  "observations": [
    {
      "observation_id": "a-cal-00",
      "physical_sequence_id": "sequence-a",
      "source_group_id": "source-a",
      "independence_group_id": "independence-a",
      "partition": "calibration",
      "observation_start_s": 0.0,
      "observation_end_s": 10.0,
      "event_a_occurs": false,
      "event_b_occurs": false,
      "sample_weight": 1.0,
      "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored observation"
        }
      ]
    },
    {
      "observation_id": "b-cal-11",
      "physical_sequence_id": "sequence-b",
      "source_group_id": "source-b",
      "independence_group_id": "independence-b",
      "partition": "calibration",
      "observation_start_s": 0.0,
      "observation_end_s": 10.0,
      "event_a_occurs": true,
      "event_b_occurs": true,
      "sample_weight": 1.0,
      "record_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored observation"
        }
      ]
    },
    {
      "observation_id": "c-hold-00",
      "physical_sequence_id": "sequence-c",
      "source_group_id": "source-c",
      "independence_group_id": "independence-c",
      "partition": "holdout",
      "observation_start_s": 0.0,
      "observation_end_s": 10.0,
      "event_a_occurs": false,
      "event_b_occurs": false,
      "sample_weight": 1.0,
      "record_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored observation"
        }
      ]
    },
    {
      "observation_id": "d-hold-11",
      "physical_sequence_id": "sequence-d",
      "source_group_id": "source-d",
      "independence_group_id": "independence-d",
      "partition": "holdout",
      "observation_start_s": 0.0,
      "observation_end_s": 10.0,
      "event_a_occurs": true,
      "event_b_occurs": true,
      "sample_weight": 1.0,
      "record_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "record_valid": true,
      "invalid_or_missing_basis": null,
      "evidence": [
        {
          "source_id": "authored",
          "origin": "synthetic",
          "citation": "authored observation"
        }
      ]
    }
  ],
  "symmetric_cell_pseudocount": 1.0,
  "pseudocount_basis": "caller-authored symmetric smoothing",
  "minimum_calibration_record_count": 1,
  "minimum_holdout_record_count": 1,
  "minimum_calibration_sequence_count": 1,
  "minimum_holdout_sequence_count": 1,
  "minimum_calibration_source_group_count": 1,
  "minimum_holdout_source_group_count": 1,
  "minimum_holdout_independence_group_count": 1,
  "event_definitions_reviewed": true,
  "observation_clock_and_scope_reviewed": true,
  "partition_assignments_reviewed": true,
  "physical_sequence_source_and_independence_groups_reviewed": true,
  "sample_weights_and_missingness_reviewed": true,
  "pseudocount_choice_reviewed": true,
  "record_digests_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/binary_event_pair_calibration.py#L109)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

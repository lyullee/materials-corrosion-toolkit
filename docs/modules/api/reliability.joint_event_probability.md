# `reliability.joint_event_probability`

**목적:** Caller-reviewed exhaustive joint distribution over binary events sharing one physical scope, horizon and conditioning basis.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `distribution_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `horizon_start_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `horizon_end_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `conditioning` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `top_event_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `top_event_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `event_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 12, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `event_definitions` | 예 | `{"items": {"type": "string"}, "type": "array"}` | 계약·필드 설명 참조 |
| `states` | 예 | `{"items": {"$ref": "#/$defs/JointEventState"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `dependence_basis` | 예 | `{"enum": ["empirical_joint_distribution", "user_supplied_scenario_weights", "model_prediction"], "type": "string"}` | 계약·필드 설명 참조 |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_version` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_content_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `common_cause_group_ids` | 아니오 | `{"items": {"type": "string"}, "type": "array"}` | 계약·필드 설명 참조 |
| `state_space_complete_declared` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `distribution_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `normalization_tolerance` | 예 | `{"exclusiveMinimum": 0, "maximum": 1e-06, "type": "number"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/JointEventDistribution.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `probability_given_survival` | `1` |
| `state_probability_sum` | `1` |
| `event_marginal_probabilities` | `1` |
| `pairwise_joint_probabilities` | `1` |
| `pairwise_covariances` | `1` |
| `pairwise_phi_coefficients` | `1` |
| `independent_reference_probability` | `1` |
| `dependence_probability_delta` | `1` |
| `zero_probability_state_count` | `count` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-reviewed exhaustive joint distribution over binary events sharing one physical scope, horizon and conditioning basis.
- The top-event truth value is supplied for every state; no independence or causal common-cause structure is inferred.

## 구현 근거·독립 설명

- `finite_joint_probability_space`: Sum caller-reviewed probabilities over an exhaustive finite binary state space. Marginals, pairwise moments and an independence reference follow from the same declared truth table; they do not identify causal common causes or justify a new dependence model.

확률 의미: `{"probability_given_survival": "conditional_first_failure_in_period"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "reliability.joint_event_probability"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["reliability.joint_event_probability"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "distribution_id": "synthetic-joint-two-event",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "physical_scope_id": "synthetic-system",
  "time_basis": "API contract check",
  "horizon_start_s": 0.0,
  "horizon_end_s": 31557600.0,
  "conditioning": "system intact at the start of the declared interval",
  "top_event_id": "either-component-fails",
  "top_event_definition": "A or B occurs during the declared interval",
  "event_ids": [
    "component-a-failure",
    "component-b-failure"
  ],
  "event_definitions": [
    "first failure of component A in the interval",
    "first failure of component B in the interval"
  ],
  "states": [
    {
      "event_occurs": [
        false,
        false
      ],
      "probability": 0.75,
      "top_event_occurs": false
    },
    {
      "event_occurs": [
        true,
        false
      ],
      "probability": 0.05,
      "top_event_occurs": true
    },
    {
      "event_occurs": [
        false,
        true
      ],
      "probability": 0.15,
      "top_event_occurs": true
    },
    {
      "event_occurs": [
        true,
        true
      ],
      "probability": 0.05,
      "top_event_occurs": true
    }
  ],
  "dependence_basis": "user_supplied_scenario_weights",
  "provider_id": "synthetic-example",
  "provider_version": "1",
  "source_content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "common_cause_group_ids": [
    "shared-environment"
  ],
  "state_space_complete_declared": true,
  "distribution_reviewed": true,
  "normalization_tolerance": 1e-12
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/reliability.py#L336)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

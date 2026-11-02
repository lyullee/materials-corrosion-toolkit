# `integration.adaptive_cycle_block_damage`

**목적:** The caller supplies a deterministic provider whose identity, revision and configuration digest match the request.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `analysis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `cycle_count_basis_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `calibration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `state_variable_ids` | 예 | `{"items": {"type": "string"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `state_units` | 예 | `{"items": {"type": "string"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `initial_state` | 예 | `{"items": {"type": "number"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `minimum_state` | 예 | `{"items": {"type": "number"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_state` | 예 | `{"items": {"type": "number"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `initial_damage` | 아니오 | `{"default": 0.0, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `damage_event_threshold` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `blocks` | 예 | `{"items": {"$ref": "#/$defs/IntegerCycleDamageBlock"}, "maxItems": 10000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `initial_step_cycles` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `minimum_step_cycles` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_step_cycles` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `state_absolute_tolerance` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `state_relative_tolerance` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `damage_absolute_tolerance` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `damage_relative_tolerance` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_function_evaluations` | 아니오 | `{"default": 100000, "maximum": 10000000, "minimum": 12, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_rejected_steps` | 아니오 | `{"default": 10000, "maximum": 1000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `ordered_integer_blocks_and_cycle_count_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `state_law_and_nonnegative_damage_rate_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `initialization_bounds_and_event_meaning_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `deterministic_repeat_evaluation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `adaptive_controls_and_local_error_meaning_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `material_calibration_and_usage_rights_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/AdaptiveCycleBlockDamageRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `completed_integer_cycle_count` | `1` |
| `final_damage` | `1` |
| `accepted_damage` | `1` |
| `maximum_accepted_scaled_local_error` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- The caller supplies a deterministic provider whose identity, revision and configuration digest match the request.
- State derivatives and nonnegative damage rate are defined per cycle in the ordered caller state basis.
- Adaptive RK4 step-doubling controls only local numerical error for the declared ODE and does not establish physical validity or global error bounds.
- Integer cycle blocks are caller-provided accounting partitions; the solver does not count cycles or infer a material failure law.

## 구현 근거·독립 설명

- `caller_adaptive_cycle_block_state_damage_ode`: Integrate a caller-defined bounded state derivative and nonnegative damage rate per cycle across ordered integer cycle blocks using RK4 step doubling, componentwise local error controls and a finite function-evaluation/rejection budget. Carry only accepted state, commit completed blocks, and retain an accepted prefix when a state boundary, unresolved event, provider mismatch or numerical limit stops the path. Bind provider/calibration/configuration digests and ordered state units. This is numerical integration of the caller's model, not an inferred fatigue law, cycle counter, life estimate, probability or material qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.adaptive_cycle_block_damage"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
# 아래 이름의 실제 Python provider를 준비한 뒤 runtime_dependencies로 전달한다.
# JSON만으로 외부 callable을 직렬화하거나 실행하지 않는다.
providers = {'provider': ...}
result = registry.run_json(model_id, payload, context, runtime_dependencies=providers)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/adaptive_cycle_block_damage.py#L261)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

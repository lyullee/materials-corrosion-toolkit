# `fabrication.gasket_contact_transition_refinement`

**목적:** Refine one caller-selected contact-state bracket only with exact provider midpoint evaluations, matching provider identity/revision/configuration and Evidence-bound response digests.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.gasket_contact_transition_refinement.v1", "default": "matintegrity.gasket_contact_transition_refinement.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `initial_bracket_result` | 예 | `{"$ref": "#/$defs/AssessmentResult"}` | 계약·필드 설명 참조 |
| `initial_bracket_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `contact_history_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `node_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `from_state` | 예 | `{"enum": ["open", "closed"], "type": "string"}` | 계약·필드 설명 참조 |
| `to_state` | 예 | `{"enum": ["open", "closed"], "type": "string"}` | 계약·필드 설명 참조 |
| `lower_time_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `upper_time_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `time_tolerance_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `maximum_evaluations` | 예 | `{"maximum": 100000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `monotonic_single_transition_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `provider_identity_and_configuration_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_scope_and_time_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GasketContactTransitionRefinement.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `lower_time_s` | `s` |
| `upper_time_s` | `s` |
| `time_tolerance_s` | `s` |
| `refined_bracket_lower_time_s` | `s` |
| `refined_bracket_upper_time_s` | `s` |
| `refined_bracket_width_s` | `s` |
| `evaluation_prefix[].query_time_s` | `s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Refine one caller-selected contact-state bracket only with exact provider midpoint evaluations, matching provider identity/revision/configuration and Evidence-bound response digests.
- A reviewed monotonic single transition in the starting bracket is required. The result is a bounded bracket, not an exact event time or local FE qualification.

## 구현 근거·독립 설명

- `caller_external_flange_contact_state_provider`: Refine one digest-bound observed flange contact-state transition bracket only through a caller-supplied external contact-state provider with matching identity, revision, configuration, source context, midpoint time, Evidence and response digest. Require a caller-reviewed monotonic single transition, time tolerance and bounded evaluation budget. Return a narrower bracket only; do not provide an FE solver or claim exact event time, hidden transition discovery, sealing acceptance, leakage, stress, probability or qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.gasket_contact_transition_refinement"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
# 아래 이름의 실제 Python provider를 준비한 뒤 runtime_dependencies로 전달한다.
# JSON만으로 외부 callable을 직렬화하거나 실행하지 않는다.
providers = {'contact_state_provider': ...}
result = registry.run_json(model_id, payload, context, runtime_dependencies=providers)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/models/gasket_contact_transition_refinement.py#L222)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

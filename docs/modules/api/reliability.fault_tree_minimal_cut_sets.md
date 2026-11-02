# `reliability.fault_tree_minimal_cut_sets`

**목적:** Caller-declared minimal cut sets; AND within each cut, OR across cuts; exact inclusion-exclusion under reviewed independent basic events.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.fault_tree_assessment.v1", "default": "matintegrity.fault_tree_assessment.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `top_event_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `basic_events` | 예 | `{"items": {"$ref": "#/$defs/FaultTreeBasicEvent"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `minimal_cut_sets` | 예 | `{"items": {"items": {"type": "string"}, "type": "array"}, "maxItems": 4096, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `independence_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `common_cause_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `cut_set_overlap_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `event_scope_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/FaultTreeAssessment.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `top_event_probability` | `1` |
| `minimal_cut_set_probabilities` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-declared minimal cut sets; AND within each cut, OR across cuts; exact inclusion-exclusion under reviewed independent basic events.

## 구현 근거·독립 설명

- `independent_basic_event_minimal_cut_sets`: Represent caller-declared minimal cut sets as AND gates and the top event as their OR. For reviewed independent basic events, compute each intersection probability as the product over the union of event IDs in the selected cut sets and combine intersections by exact inclusion-exclusion; report exact Birnbaum and probability-weighted basic-event importance. Bound the exact calculation to 16 cut sets; require a shared probability meaning and scope ID across events, retain conditioning and evidence digest, and optionally reconcile the existing integrity-event exchange contract including clock/horizon. Do not infer event probabilities, compatible horizons, independence, common causes, repair, initiating frequency or acceptance.

확률 의미: `{"top_event_probability": "fault_tree_top_event_probability"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "reliability.fault_tree_minimal_cut_sets"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["reliability.fault_tree_minimal_cut_sets"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "schema_version": "matintegrity.fault_tree_assessment.v1",
  "top_event_id": "synthetic-top-event",
  "basic_events": [
    {
      "event_id": "synthetic-A",
      "probability": 0.01,
      "probability_meaning": "unscoped_event_probability",
      "conditioning": "synthetic common horizon",
      "evidence_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "probability_scope_id": "synthetic-shared-horizon-v1"
    },
    {
      "event_id": "synthetic-B",
      "probability": 0.02,
      "probability_meaning": "unscoped_event_probability",
      "conditioning": "synthetic common horizon",
      "evidence_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "probability_scope_id": "synthetic-shared-horizon-v1"
    },
    {
      "event_id": "synthetic-C",
      "probability": 0.03,
      "probability_meaning": "unscoped_event_probability",
      "conditioning": "synthetic common horizon",
      "evidence_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "probability_scope_id": "synthetic-shared-horizon-v1"
    }
  ],
  "minimal_cut_sets": [
    [
      "synthetic-A",
      "synthetic-B"
    ],
    [
      "synthetic-B",
      "synthetic-C"
    ]
  ],
  "independence_reviewed": true,
  "common_cause_reviewed": true,
  "cut_set_overlap_reviewed": true,
  "event_scope_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fault_tree.py#L87)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

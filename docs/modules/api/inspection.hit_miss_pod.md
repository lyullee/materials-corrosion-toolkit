# `inspection.hit_miss_pod`

**목적:** Increasing logistic POD in log flaw size, independent hit/miss observations and profile-likelihood confidence inference.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `specimen_ids` | 예 | `{"items": {"type": "string"}, "minItems": 6, "type": "array"}` | 계약·필드 설명 참조 |
| `flaw_size_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "minItems": 6, "type": "array"}` | m |
| `detected` | 예 | `{"items": {"type": "boolean"}, "minItems": 6, "type": "array"}` | 계약·필드 설명 참조 |
| `query_sizes_m` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 100, "minItems": 1, "type": "array"}` | m |
| `target_probability` | 예 | `{"exclusiveMaximum": 1, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `confidence_level` | 예 | `{"exclusiveMaximum": 1, "exclusiveMinimum": 0.5, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_threshold_size_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `independent_trials_declared` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/HitMissPOD.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `target_size_estimate_m` | `m` |
| `target_size_upper_confidence_m` | `m` |
| `logistic_midpoint_size_m` | `m` |
| `logistic_log_size_scale` | `1` |
| `probability_of_detection` | `1` |
| `pointwise_lower_probability_of_detection` | `1` |
| `confidence_level` | `1` |
| `likelihood_ratio_cutoff` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Increasing logistic POD in log flaw size, independent hit/miss observations and profile-likelihood confidence inference.

## 구현 근거·독립 설명

- [FHWA report on inspection probability of detection](https://rosap.ntl.bts.gov/view/dot/53616/dot_53616_DS1.pdf) · `nde_pod`
- [POD method author discussion of likelihood confidence inference](https://statistical-engineering.com/mh1823-workshop/) · `profile_likelihood_inference`

확률 의미: `{"probability_of_detection": "detection_given_flaw_and_procedure"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "inspection.hit_miss_pod"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["inspection.hit_miss_pod"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "specimen_ids": [
    "pod-1",
    "pod-2",
    "pod-3",
    "pod-4",
    "pod-5",
    "pod-6"
  ],
  "flaw_size_m": [
    0.0005,
    0.0007,
    0.001,
    0.0014,
    0.002,
    0.003
  ],
  "detected": [
    false,
    true,
    false,
    true,
    false,
    true
  ],
  "query_sizes_m": [
    0.0007,
    0.0014,
    0.002
  ],
  "target_probability": 0.9,
  "confidence_level": 0.95,
  "maximum_threshold_size_m": 0.1,
  "independent_trials_declared": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/pod.py#L39)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

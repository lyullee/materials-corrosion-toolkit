# `fatigue.cyclic_response_relative_error`

**목적:** Caller-supplied observed/predicted mean and amplitude arrays share strict cycle alignment, explicit positive normalization and a predeclared experiment set.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `series` | 예 | `{"items": {"$ref": "#/$defs/CyclicResponseSeries"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `mean_weight` | 아니오 | `{"default": 0.6, "maximum": 1.0, "minimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |
| `amplitude_weight` | 아니오 | `{"default": 0.4, "maximum": 1.0, "minimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CyclicResponseRelativeError.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `experiment_count` | `1` |
| `mean_weight` | `1` |
| `amplitude_weight` | `1` |
| `aggregate_weighted_relative_error` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-supplied observed/predicted mean and amplitude arrays share strict cycle alignment, explicit positive normalization and a predeclared experiment set.
- The default 0.6/0.4 balance is configurable and experiment-level averaging prevents unequal trace lengths from changing experiment weights.

## 구현 근거·독립 설명

- [FABEST in LCF official rules and task description](https://faber-cost.eu/wp-content/uploads/2026/05/Assignment_FABEST_LCF_FINAL.pdf) · `fabest_lcf_rules_2026`
- `normalized_absolute_error`: For each predeclared experiment, divide aligned absolute mean and amplitude residuals by separate caller-supplied positive scales, combine them with nonnegative weights summing to one, average over that experiment's supplied cycles and then average experiments equally. Never infer a possibly zero normalizer, resample cycle histories or treat the score as model validity.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.cyclic_response_relative_error"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.cyclic_response_relative_error"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "series": [
    {
      "experiment_id": "synthetic-lcf-1",
      "cycle": [
        1,
        10
      ],
      "observed_mean": [
        10000000.0,
        9000000.0
      ],
      "predicted_mean": [
        11000000.0,
        8500000.0
      ],
      "observed_amplitude": [
        200000000.0,
        180000000.0
      ],
      "predicted_amplitude": [
        190000000.0,
        170000000.0
      ],
      "mean_normalizer": 10000000.0,
      "amplitude_normalizer": 200000000.0
    }
  ],
  "mean_weight": 0.6,
  "amplitude_weight": 0.4
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fatigue_benchmark.py#L61)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

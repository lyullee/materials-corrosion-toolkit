# `corrosion.material_rate_contrast`

**목적:** Input rates and condition groups are supplied by the caller; matched methodology and exposure conditions require source review.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `comparison_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `numerator_material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `reference_material_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `numerator_rate_m_s` | 예 | `{"minimum": 0, "type": "number"}` | m/s |
| `reference_rate_m_s` | 예 | `{"minimum": 0, "type": "number"}` | m/s |
| `condition_signature` | 예 | `{"additionalProperties": {"anyOf": [{"type": "string"}, {"type": "number"}, {"type": "integer"}, {"type": "boolean"}]}, "type": "object"}` | 계약·필드 설명 참조 |
| `condition_group_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_group_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `measurement_method` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/MaterialCorrosionRateContrast.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `numerator_rate_m_s` | `m/s` |
| `reference_rate_m_s` | `m/s` |
| `rate_difference_m_s` | `m/s` |
| `rate_ratio` | `1` |
| `log_rate_ratio` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Input rates and condition groups are supplied by the caller; matched methodology and exposure conditions require source review.
- A ratio describes only the supplied comparison and does not transfer to another material, process, or environment.

## 구현 근거·독립 설명

- `material_corrosion_rate_contrast`: Arithmetic difference, ratio, and log-ratio for two nonnegative caller-supplied uniform corrosion rates with distinct material identities and an explicit condition/source group; undefined ratios remain explicit when the reference rate is zero.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.material_rate_contrast"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["corrosion.material_rate_contrast"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "comparison_id": "synthetic-weld-base-contrast",
  "numerator_material_id": "grade-A-weld-metal",
  "reference_material_id": "grade-A-base-metal",
  "numerator_rate_m_s": 2.1e-08,
  "reference_rate_m_s": 1.4e-08,
  "condition_signature": {
    "temperature_K": 333.15,
    "co2_partial_pressure_Pa": 300000.0,
    "exposure_s": 345600.0
  },
  "condition_group_id": "synthetic-autoclave-condition-01",
  "source_group_id": "synthetic-example-source",
  "measurement_method": "weight_loss"
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/corrosion.py#L374)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

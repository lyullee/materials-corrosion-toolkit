# `corrosion.chronoamperometry_window_summary`

**목적:** Time and current units, strict sample order, current sign and source trace digest are explicitly reviewed.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.chronoamperometry_window_summary.v1", "default": "matintegrity.chronoamperometry_window_summary.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `trace_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_specimen_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_group_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_trace_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `source_archive_sha256` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `source_member_sha256` | 아니오 | `{"anyOf": [{"pattern": "^[a-f0-9]{64}$", "type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"items": {"type": "number"}, "maxItems": 200000, "minItems": 2, "type": "array"}` | s |
| `current_A` | 예 | `{"items": {"type": "number"}, "maxItems": 200000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `analysis_window_s` | 예 | `{"items": {"type": "number"}, "maxItems": 2, "minItems": 2, "type": "array"}` | s |
| `baseline_window_s` | 아니오 | `{"anyOf": [{"items": {"type": "number"}, "maxItems": 2, "minItems": 2, "type": "array"}, {"type": "null"}], "default": null}` | s |
| `boundary_policy` | 아니오 | `{"default": "piecewise_linear", "enum": ["exact_samples", "piecewise_linear"], "type": "string"}` | 계약·필드 설명 참조 |
| `sample_order_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `time_unit_reviewed_as_seconds` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `current_unit_reviewed_as_amperes` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `current_sign_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `current_sign_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/ChronoamperometryWindowSummary.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `analysis_window_s` | `s` |
| `analysis_duration_s` | `s` |
| `signed_charge_C` | `C` |
| `absolute_charge_C` | `C` |
| `positive_polarity_charge_C` | `C` |
| `negative_polarity_charge_C` | `C` |
| `time_mean_current_A` | `A` |
| `minimum_current_A` | `A` |
| `minimum_time_first_s` | `s` |
| `minimum_time_last_s` | `s` |
| `maximum_current_A` | `A` |
| `maximum_time_first_s` | `s` |
| `maximum_time_last_s` | `s` |
| `baseline_window_s` | `s` |
| `baseline_signed_charge_C` | `C` |
| `baseline_time_mean_current_A` | `A` |
| `minimum_minus_baseline_A` | `A` |
| `maximum_minus_baseline_A` | `A` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Time and current units, strict sample order, current sign and source trace digest are explicitly reviewed.
- Trapezoidal integration represents the supplied trace as piecewise linear; requested boundaries are exact samples or explicit linear interpolants.
- Raw signal summaries do not classify corrosion events, infer metal loss or pit dimensions, or establish probability, POD, life or acceptance.

## 구현 근거·독립 설명

- `authored_chronoamperometry_window_contract`: Independently summarize one provenance-bound, strictly time-ordered current trace over caller-declared analysis and optional baseline windows. Preserve the reviewed seconds, amperes, current sign, physical specimen, source group and source digest. Use either exact observed endpoints or explicit piecewise-linear boundary interpolation; integrate signed current and absolute piecewise-linear magnitude while retaining extrema plateaus. Do not filter, classify events, infer metal loss or pit dimensions, pool map points as specimens, or produce POD, life, acceptance or failure probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "corrosion.chronoamperometry_window_summary"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["corrosion.chronoamperometry_window_summary"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "trace_id": "authored-ca-trace",
  "physical_specimen_id": "authored-specimen",
  "source_group_id": "authored-ca-program",
  "source_trace_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "time_s": [
    0.0,
    1.0,
    2.0,
    3.0
  ],
  "current_A": [
    -2e-09,
    0.0,
    2e-09,
    4e-09
  ],
  "analysis_window_s": [
    0.5,
    2.5
  ],
  "baseline_window_s": [
    0.0,
    1.0
  ],
  "boundary_policy": "piecewise_linear",
  "sample_order_reviewed": true,
  "time_unit_reviewed_as_seconds": true,
  "current_unit_reviewed_as_amperes": true,
  "current_sign_basis": "authored signed instrument-current convention",
  "current_sign_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/electrochemistry.py#L209)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

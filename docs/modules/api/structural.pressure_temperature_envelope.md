# `structural.pressure_temperature_envelope`

**목적:** Caller-reviewed positive pressure limit at strictly increasing absolute-temperature knots; piecewise-linear interpolation is restricted to supplied support.

**모델 버전:** `1.0.1` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `envelope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `applicability_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `source_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `knots` | 예 | `{"items": {"$ref": "#/$defs/PressureTemperatureEnvelopeKnot"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `operating_points` | 예 | `{"items": {"$ref": "#/$defs/PressureTemperatureOperatingPoint"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `interpolation` | 아니오 | `{"const": "piecewise_linear", "default": "piecewise_linear", "type": "string"}` | 계약·필드 설명 참조 |
| `applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `operating_points_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/PressureTemperatureEnvelope.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `point_ids` | `1` |
| `allowable_pressures_Pa` | `Pa` |
| `pressure_margins_Pa` | `Pa` |
| `utilization_ratios` | `1` |
| `within_supplied_envelope` | `1` |
| `all_within_supplied_envelope` | `1` |
| `minimum_pressure_margin_Pa` | `Pa` |
| `minimum_margin_point_id` | `1` |
| `maximum_utilization_ratio` | `1` |
| `maximum_utilization_point_id` | `1` |
| `outside_support_point_ids` | `1` |
| `support_temperature_min_K` | `K` |
| `support_temperature_max_K` | `K` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-reviewed positive pressure limit at strictly increasing absolute-temperature knots; piecewise-linear interpolation is restricted to supplied support.
- No design-code table, load combination, transient reconstruction, uncertainty factor, extrapolation or acceptance decision is inferred.

## 구현 근거·독립 설명

- `user_supplied_pressure_temperature_envelope`: Interpolate pressure limits only between strictly increasing absolute-temperature knots supplied and reviewed by the caller. Preserve the applicability basis and content digest, compare identified operating points without extrapolation, and report pressure margin and utilization separately. No design-code table, service-category rule, load combination, uncertainty factor or acceptance decision is bundled.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "structural.pressure_temperature_envelope"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["structural.pressure_temperature_envelope"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "envelope_id": "authored-demo-pressure-temperature-envelope",
  "applicability_basis": "synthetic curve for API execution only",
  "source_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "knots": [
    {
      "temperature_K": 250.0,
      "allowable_pressure_Pa": 12000000.0
    },
    {
      "temperature_K": 300.0,
      "allowable_pressure_Pa": 10000000.0
    },
    {
      "temperature_K": 400.0,
      "allowable_pressure_Pa": 8000000.0
    }
  ],
  "operating_points": [
    {
      "point_id": "demo-cold",
      "temperature_K": 275.0,
      "pressure_Pa": 9000000.0
    },
    {
      "point_id": "demo-hot",
      "temperature_K": 350.0,
      "pressure_Pa": 8500000.0
    }
  ],
  "interpolation": "piecewise_linear",
  "applicability_reviewed": true,
  "operating_points_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/mechanics.py#L167)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

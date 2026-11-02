# `thermo.co2_mixture_fugacity_history`

**목적:** Evaluate ordered caller-specified gas-mixture CO2 component fugacity at exact PT time knots with CoolProp.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.mixture_co2_fugacity_history.v1", "default": "matintegrity.mixture_co2_fugacity_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "maxItems": 20000, "minItems": 1, "type": "array"}` | s |
| `requests` | 예 | `{"items": {"$ref": "#/$defs/CoolPropCo2MixtureFugacityRequest"}, "maxItems": 20000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `history_clock_and_state_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `maximum_point_evaluations` | 아니오 | `{"default": 20000, "maximum": 20000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/MixtureCo2FugacityHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `history_id` | `1` |
| `asset_id` | `1` |
| `location_id` | `1` |
| `time_basis` | `1` |
| `time_s[]` | `s` |
| `temperature_K_history[]` | `K` |
| `total_pressure_Pa_history[]` | `Pa` |
| `co2_partial_pressure_Pa_history[]` | `Pa` |
| `fugacity_coefficient_history[]` | `1` |
| `co2_fugacity_Pa_history[]` | `Pa` |
| `point_count` | `count` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Evaluate ordered caller-specified gas-mixture CO2 component fugacity at exact PT time knots with CoolProp.
- Component identity/order and backend are fixed; mole fractions may vary at each knot and the provider state object is reused.
- No ideal-mixture fallback, temporal interpolation, aqueous equilibrium, Henry coefficient or corrosion response is inferred.

## 구현 근거·독립 설명

- [CoolProp AbstractState low-level API, mixture mole fractions and component fugacity coefficient](https://coolprop.org/coolprop/LowLevelAPI.html) · `coolprop_low_level_fugacity`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "thermo.co2_mixture_fugacity_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["thermo.co2_mixture_fugacity_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "synthetic-mixture-co2-fugacity-history",
  "asset_id": "synthetic-loop",
  "location_id": "synthetic-gas-tap",
  "time_basis": "elapsed_seconds_from_declared_origin",
  "time_s": [
    0.0,
    30.0
  ],
  "requests": [
    {
      "assessment_id": "synthetic-mixture-co2-history-point-1",
      "temperature_K": 333.15,
      "total_pressure_Pa": 200000.0,
      "components": [
        "CarbonDioxide",
        "Nitrogen"
      ],
      "mole_fractions": [
        0.15,
        0.85
      ],
      "backend": "HEOS",
      "mixture_composition_reviewed": true,
      "mixture_eos_applicability_reviewed": true,
      "single_phase_gas_or_supercritical_reviewed": true,
      "review_id": "synthetic-review-only",
      "evidence": [
        {
          "origin": "synthetic",
          "citation": "Synthetic API example; not experimental data",
          "sha256": null,
          "license_id": null,
          "source_id": "authored-example"
        }
      ]
    },
    {
      "assessment_id": "synthetic-mixture-co2-history-point-2",
      "temperature_K": 350.0,
      "total_pressure_Pa": 250000.0,
      "components": [
        "CarbonDioxide",
        "Nitrogen"
      ],
      "mole_fractions": [
        0.25,
        0.75
      ],
      "backend": "HEOS",
      "mixture_composition_reviewed": true,
      "mixture_eos_applicability_reviewed": true,
      "single_phase_gas_or_supercritical_reviewed": true,
      "review_id": "synthetic-review-only",
      "evidence": [
        {
          "origin": "synthetic",
          "citation": "Synthetic API example; not experimental data",
          "sha256": null,
          "license_id": null,
          "source_id": "authored-example"
        }
      ]
    }
  ],
  "history_clock_and_state_alignment_reviewed": true,
  "maximum_point_evaluations": 100
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/co2_fugacity.py#L370)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

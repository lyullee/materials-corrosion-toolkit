# `degradation.cavitation_history`

**목적:** Aligned reviewed absolute local-pressure and equilibrium liquid-property samples with piecewise-linear crossings; duration and pressure deficit are not damage.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `history_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `history_origin` | 예 | `{"enum": ["measured", "model_prediction", "user_declared", "synthetic"], "type": "string"}` | 계약·필드 설명 참조 |
| `hydraulic_source_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `fluid_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `pressure_basis` | 아니오 | `{"const": "absolute", "default": "absolute", "type": "string"}` | 계약·필드 설명 참조 |
| `sample_ids` | 예 | `{"items": {"type": "string"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"items": {"minimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | s |
| `local_static_pressure_Pa` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | Pa |
| `temperature_K` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | K |
| `vapor_pressure_Pa` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | Pa |
| `liquid_density_kg_m3` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | kg/m³ |
| `characteristic_velocity_m_s` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "minItems": 2, "type": "array"}` | m/s |
| `sample_valid` | 예 | `{"items": {"type": "boolean"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `property_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `property_provider_version` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `property_state_digests` | 예 | `{"items": {"type": "string"}, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `property_history_digest` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `local_pressure_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `velocity_definition` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `interpolation` | 아니오 | `{"const": "linear", "default": "linear", "type": "string"}` | 계약·필드 설명 참조 |
| `absolute_pressure_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `thermodynamic_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CavitationHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `static_pressure_margin_Pa` | `Pa` |
| `characteristic_dynamic_pressure_Pa` | `Pa` |
| `local_cavitation_number` | `1` |
| `minimum_static_pressure_margin_Pa` | `Pa` |
| `minimum_margin_sample_id` | `1` |
| `minimum_margin_time_s` | `s` |
| `thermodynamic_possible_intervals_s` | `s` |
| `total_thermodynamic_possible_duration_s` | `s` |
| `observed_duration_s` | `s` |
| `thermodynamic_possible_time_fraction` | `1` |
| `pressure_deficit_exposure_Pa_s` | `Pa*s` |
| `any_thermodynamic_cavitation_possible` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Aligned reviewed absolute local-pressure and equilibrium liquid-property samples with piecewise-linear crossings; duration and pressure deficit are not damage.

## 구현 근거·독립 설명

- `cavitation_history_definition`: For each aligned reviewed sample subtract equilibrium vapor pressure from local absolute static pressure. On every declared linear time segment, locate zero-margin crossings exactly, union contiguous nonpositive-margin intervals and integrate the clipped negative linear margin as pressure-deficit exposure. Duration and pressure deficit are sampling-dependent screening descriptors, not nuclei, inception, collapse energy, erosion damage, life or probability.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "degradation.cavitation_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["degradation.cavitation_history"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "history_id": "synthetic-pressure-dip",
  "asset_id": "synthetic",
  "location_id": "synthetic",
  "clock_id": "synthetic-clock",
  "history_origin": "synthetic",
  "hydraulic_source_digest": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
  "fluid_id": "synthetic-liquid",
  "pressure_basis": "absolute",
  "sample_ids": [
    "t0",
    "t1",
    "t2"
  ],
  "time_s": [
    0.0,
    1.0,
    2.0
  ],
  "local_static_pressure_Pa": [
    5000.0,
    3000.0,
    5000.0
  ],
  "temperature_K": [
    300.0,
    300.0,
    300.0
  ],
  "vapor_pressure_Pa": [
    4000.0,
    4000.0,
    4000.0
  ],
  "liquid_density_kg_m3": [
    997.0,
    997.0,
    997.0
  ],
  "characteristic_velocity_m_s": [
    10.0,
    10.0,
    10.0
  ],
  "sample_valid": [
    true,
    true,
    true
  ],
  "property_provider_id": "synthetic-provider",
  "property_provider_version": "1.0",
  "property_state_digests": [
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
  ],
  "property_history_digest": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "local_pressure_definition": "synthetic local absolute static pressure",
  "velocity_definition": "synthetic section mean velocity",
  "interpolation": "linear",
  "absolute_pressure_reviewed": true,
  "thermodynamic_state_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/degradation.py#L275)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

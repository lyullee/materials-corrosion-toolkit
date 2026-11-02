# `fracture.sequence_zone_memory`

**목적:** Caller-calibrated opening ratio and plastic-zone memory with explicit whole-cycle stepping, state checkpoints, and distinct fracture/depth/support termination.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `growth` | 예 | `{"$ref": "#/$defs/VariableParis"}` | 계약·필드 설명 참조 |
| `yield_strength_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa |
| `plastic_zone_coefficient` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `retardation_exponent` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `opening_K_fraction_of_maximum` | 예 | `{"exclusiveMaximum": 1, "minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_depth_increment_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `maximum_cycle_steps` | 예 | `{"maximum": 2000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `calibrated_sequence_law_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `sequence_and_closure_law_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `initial_state` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/SequenceGrowthState"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/SequenceCrackGrowth.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `completed_cycles` | `cycle` |
| `completed_cycles_this_run` | `cycle` |
| `final_depth_m` | `m` |
| `plastic_zone_tip_m` | `m` |
| `limiting_depth_m` | `m` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller-calibrated opening ratio and plastic-zone memory with explicit whole-cycle stepping, state checkpoints, and distinct fracture/depth/support termination.

## 구현 근거·독립 설명

- `sequence_zone_memory_and_partial_dissolution`: Step ordered whole cycles with an explicit caller-calibrated opening ratio and plastic-zone extent memory, preserving integration-resolution and calibration boundaries. Separately integrate identified nonnegative partial anodic dissolution-current histories by trapezoids and Faraday stoichiometry with caller efficiency, molar mass and density. Net mixed-potential current is never substituted for dissolution current.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fracture.sequence_zone_memory"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fracture.sequence_zone_memory"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "growth": {
    "initial_depth_m": 0.001,
    "terminal_depth_m": 0.005,
    "geometry_depth_m": [
      0.0005,
      0.005
    ],
    "geometry_factor": [
      1.12,
      1.12
    ],
    "blocks": [
      {
        "minimum_stress_Pa": 0.0,
        "maximum_stress_Pa": 100000000.0,
        "cycles": 10000.0
      }
    ],
    "coefficient_m_cycle_per_Pa_sqrt_m_power": 1e-28,
    "exponent": 3.0,
    "threshold_delta_K_Pa_sqrt_m": 0.0,
    "minimum_calibrated_delta_K_Pa_sqrt_m": 1000.0,
    "maximum_calibrated_delta_K_Pa_sqrt_m": 1000000000.0,
    "minimum_calibrated_stress_ratio": 0.0,
    "maximum_calibrated_stress_ratio": 0.999999,
    "fracture_toughness_Pa_sqrt_m": 50000000.0,
    "relative_integration_tolerance": 1e-08,
    "absolute_cycle_tolerance": 1e-06,
    "absolute_depth_tolerance_m": 1e-12
  },
  "yield_strength_Pa": 300000000.0,
  "plastic_zone_coefficient": 0.15915494309189535,
  "retardation_exponent": 1.5,
  "opening_K_fraction_of_maximum": 0.1,
  "maximum_depth_increment_m": 1e-06,
  "maximum_cycle_steps": 20000,
  "calibrated_sequence_law_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "sequence_and_closure_law_reviewed": true
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/sequence_numeric.py#L64)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

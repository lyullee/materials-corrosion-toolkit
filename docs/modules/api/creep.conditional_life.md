# `creep.conditional_life`

**목적:** Condition-bounded lognormal population under unchanged conditions from a fresh-material age origin.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `model` | 예 | `{"$ref": "#/$defs/CreepLifeModel"}` | 계약·필드 설명 참조 |
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `stress_basis` | 예 | `{"enum": ["initial_nominal_constant_load", "constant_true_stress"], "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_basis` | 예 | `{"enum": ["nominal_specified", "measured_representative"], "type": "string"}` | 계약·필드 설명 참조 |
| `initial_stress_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa |
| `temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `current_age_s` | 예 | `{"minimum": 0, "type": "number"}` | s |
| `horizon_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `maximum_time_extrapolation_factor` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `constant_conditions_since_fresh_material_confirmed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `applicability_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreepLifePrediction.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `median_life_s` | `s` |
| `probability_given_survival` | `1` |
| `declared_time_bound_s` | `s` |
| `log_life_sigma` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Condition-bounded lognormal population under unchanged conditions from a fresh-material age origin.

## 구현 근거·독립 설명

- [NIST lognormal lifetime distribution](https://www.itl.nist.gov/div898/handbook/apr/section1/apr164.htm) · `nist_lognormal`
- `creep_aft_likelihood`: Natural log lifetime has a stress-power/optional reciprocal-temperature mean and common Gaussian scatter. Sum failure log densities plus right-censored log survivals; use scaled full-rank features and observed information. Conditional failure is one minus the survival ratio, evaluated using stable normal-tail functions or the integrated Mills ratio for short intervals.

확률 의미: `{"probability_given_survival": "conditional_first_failure_in_period"}`. 손상량을 확률로 재명명하지 않는다.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "creep.conditional_life"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["creep.conditional_life"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "model": {
    "schema_version": "matintegrity.creep_life.v1",
    "family": "stress_only",
    "material_condition_id": "synthetic-material-state",
    "stress_basis": "constant_true_stress",
    "temperature_basis": "nominal_specified",
    "reference_stress_Pa": 165487545.98234388,
    "reference_temperature_K": 1000.0,
    "log_reference_median_time_s": 13.422467971905787,
    "stress_exponent": 3.9999999999997438,
    "activation_energy_J_mol": null,
    "log_life_sigma": 0.1498332406372431,
    "temperature_tolerance_K": 0.0,
    "support_stress_Pa": [
      100000000.0,
      150000000.0,
      200000000.0,
      250000000.0
    ],
    "support_temperature_K": [
      1000.0,
      1000.0,
      1000.0,
      1000.0
    ],
    "longest_observed_failure_time_s": 6183351.463185861,
    "training_digest": "d4f9b3b9e942d09b4c82fc1b7babee4b40e131c42366dd21e224053c5222249f",
    "observations": 16,
    "failures": 16,
    "evidence": [
      {
        "source_id": "synthetic",
        "origin": "synthetic",
        "citation": "Analytical synthetic power-law specimens",
        "license_id": "MIT",
        "sha256": null
      }
    ]
  },
  "material_condition_id": "synthetic-material-state",
  "stress_basis": "constant_true_stress",
  "initial_stress_Pa": 150000000.0,
  "temperature_K": 1000.0,
  "current_age_s": 100000.0,
  "horizon_s": 900000.0,
  "maximum_time_extrapolation_factor": 1.0,
  "constant_conditions_since_fresh_material_confirmed": true,
  "applicability_reviewed": true,
  "temperature_basis": "nominal_specified"
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/creep.py#L276)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

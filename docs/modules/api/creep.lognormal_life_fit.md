# `creep.lognormal_life_fit`

**목적:** Independent constant-condition specimens with explicit right-censoring and one common rupture mechanism.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `material_condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `stress_basis` | 예 | `{"enum": ["initial_nominal_constant_load", "constant_true_stress"], "type": "string"}` | 계약·필드 설명 참조 |
| `temperature_basis` | 예 | `{"enum": ["nominal_specified", "measured_representative"], "type": "string"}` | 계약·필드 설명 참조 |
| `family` | 예 | `{"enum": ["stress_only", "arrhenius_stress"], "type": "string"}` | 계약·필드 설명 참조 |
| `specimen_id` | 예 | `{"items": {"type": "string"}, "maxItems": 100000, "minItems": 8, "type": "array"}` | 계약·필드 설명 참조 |
| `initial_stress_Pa` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}` | Pa |
| `temperature_K` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}` | K |
| `endpoint_time_s` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}` | s |
| `right_censored` | 예 | `{"items": {"type": "boolean"}, "type": "array"}` | 계약·필드 설명 참조 |
| `temperature_tolerance_K` | 예 | `{"minimum": 0, "type": "number"}` | K |
| `independent_specimens_confirmed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `common_mechanism_and_condition_confirmed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreepLifeFit.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `negative_log_likelihood_seconds` | `1` |
| `information_condition_number` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Independent constant-condition specimens with explicit right-censoring and one common rupture mechanism.

## 구현 근거·독립 설명

- [NIST lognormal lifetime distribution](https://www.itl.nist.gov/div898/handbook/apr/section1/apr164.htm) · `nist_lognormal`
- [NIST accelerated lifetime likelihood estimation](https://www.itl.nist.gov/div898/handbook/apr/section4/apr422.htm) · `nist_accelerated_mle`
- [SciPy constrained minimization API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html) · `scipy_minimize`
- `creep_aft_likelihood`: Natural log lifetime has a stress-power/optional reciprocal-temperature mean and common Gaussian scatter. Sum failure log densities plus right-censored log survivals; use scaled full-rank features and observed information. Conditional failure is one minus the survival ratio, evaluated using stable normal-tail functions or the integrated Mills ratio for short intervals.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "creep.lognormal_life_fit"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["creep.lognormal_life_fit"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "material_condition_id": "synthetic-material-state",
  "stress_basis": "constant_true_stress",
  "temperature_basis": "nominal_specified",
  "family": "stress_only",
  "specimen_id": [
    "synthetic-0",
    "synthetic-1",
    "synthetic-2",
    "synthetic-3",
    "synthetic-4",
    "synthetic-5",
    "synthetic-6",
    "synthetic-7",
    "synthetic-8",
    "synthetic-9",
    "synthetic-10",
    "synthetic-11",
    "synthetic-12",
    "synthetic-13",
    "synthetic-14",
    "synthetic-15"
  ],
  "initial_stress_Pa": [
    100000000.0,
    100000000.0,
    100000000.0,
    100000000.0,
    150000000.0,
    150000000.0,
    150000000.0,
    150000000.0,
    200000000.0,
    200000000.0,
    200000000.0,
    200000000.0,
    250000000.0,
    250000000.0,
    250000000.0,
    250000000.0
  ],
  "temperature_K": [
    1000.0,
    1000.0,
    1000.0,
    1000.0,
    1000.0,
    1000.0,
    1000.0,
    1000.0,
    1000.0,
    1000.0,
    1000.0,
    1000.0,
    1000.0,
    1000.0,
    1000.0,
    1000.0
  ],
  "endpoint_time_s": [
    4144824.437457284,
    4720243.713273864,
    5429572.667599472,
    6183351.463185861,
    818730.7530779819,
    932393.8199059482,
    1072508.1812542165,
    1221402.75816017,
    259051.52734108025,
    295015.2320796165,
    339348.291724967,
    386459.4664491163,
    106107.50559890641,
    120838.23905981088,
    138997.06029054642,
    158293.797457558
  ],
  "right_censored": [
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false
  ],
  "temperature_tolerance_K": 0.0,
  "independent_specimens_confirmed": true,
  "common_mechanism_and_condition_confirmed": true,
  "evidence": [
    {
      "source_id": "synthetic",
      "origin": "synthetic",
      "citation": "Analytical synthetic power-law specimens",
      "license_id": "MIT",
      "sha256": null
    }
  ]
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/creep.py#L149)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

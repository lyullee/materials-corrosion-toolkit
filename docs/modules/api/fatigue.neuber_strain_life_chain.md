# `fatigue.neuber_strain_life_chain`

**목적:** Runs the reviewed scalar stabilized notch-root estimate first, then evaluates the local strain amplitude with caller-supplied strain-life coefficients and cycle support.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `notch` | 예 | `{"$ref": "#/$defs/NeuberNotchStrainAmplitude"}` | 계약·필드 설명 참조 |
| `fatigue_strength_coefficient_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa |
| `fatigue_strength_exponent` | 예 | `{"exclusiveMaximum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `fatigue_ductility_coefficient` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `fatigue_ductility_exponent` | 예 | `{"exclusiveMaximum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `minimum_valid_cycles` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_valid_cycles` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/NeuberStrainLifeChain.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `local_stress_amplitude_Pa` | `Pa` |
| `local_strain_amplitude` | `1` |
| `elastic_strain_amplitude` | `1` |
| `plastic_strain_amplitude` | `1` |
| `relative_neuber_residual` | `1` |
| `neuber_iterations` | `1` |
| `neuber_converged` | `1` |
| `neuber_status` | `1` |
| `notch_reason` | `1` |
| `strain_life_status` | `1` |
| `cycles_to_failure` | `cycle` |
| `reversals_to_failure` | `reversal` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Runs the reviewed scalar stabilized notch-root estimate first, then evaluates the local strain amplitude with caller-supplied strain-life coefficients and cycle support.
- The strain-life stage is skipped unless the notch stage has a computed, converged result; neither stage establishes code acceptance or experimental qualification.

## 구현 근거·독립 설명

- `neuber_local_strain_compatibility`: For a caller-reviewed scalar elastic stress concentration factor Kt and nominal stress amplitude S, solve sigma times epsilon = Kt squared times S squared divided by E. The local stabilized cyclic strain is sigma/E plus (sigma/K-prime) raised to 1/n-prime. The implementation brackets the positive root and applies deterministic bisection; it does not infer Kt, material calibration or fatigue life.
- `ramberg_osgood_cyclic_relation`: Use the caller-supplied stabilized cyclic strength coefficient K-prime, exponent n-prime and elastic modulus to partition local strain amplitude into elastic and plastic components. This relation alone does not establish material applicability, transient history, multiaxial response or life.
- [COMSOL documented strain-life relations](https://doc.comsol.com/6.4/doc/com.comsol.help.fatigue/fatigue_ug_sme.4.21.html) · `comsol_strain_life`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fatigue.neuber_strain_life_chain"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 키: `examples/model_inputs.json` → `models["fatigue.neuber_strain_life_chain"]`. 합성값이며 물성·허용값·실측값이 아니다.

```json
{
  "notch": {
    "nominal_stress_amplitude_Pa": 100000000.0,
    "elastic_stress_concentration_factor": 2.0,
    "elastic_modulus_Pa": 200000000000.0,
    "cyclic_strength_coefficient_Pa": 1000000000.0,
    "cyclic_strain_hardening_exponent": 0.2,
    "all_inputs_reviewed": true
  },
  "fatigue_strength_coefficient_Pa": 1000000000.0,
  "fatigue_strength_exponent": -0.1,
  "fatigue_ductility_coefficient": 0.5,
  "fatigue_ductility_exponent": -0.5,
  "minimum_valid_cycles": 1.0,
  "maximum_valid_cycles": 1000000000.0
}
```

[계산 구현과 주석 확인](../../../src/matintegrity/models/fatigue.py#L103)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

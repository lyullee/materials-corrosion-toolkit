# `fabrication.gasket_prony_temperature_shift_history`

**목적:** A caller-calibrated, thermorheologically simple time-temperature shift modifies the Prony relaxation clock while other material parameters remain at the reference condition.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.gasket_prony_temperature_shift_history.v1", "default": "matintegrity.gasket_prony_temperature_shift_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `base_history` | 예 | `{"$ref": "#/$defs/GasketViscoelasticHistoryRequest"}` | 계약·필드 설명 참조 |
| `shift_law` | 예 | `{"$ref": "#/$defs/GasketPronyTemperatureShiftLaw"}` | 계약·필드 설명 참조 |
| `interval_temperature_K` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "minItems": 1, "type": "array"}` | K |
| `interval_temperature_piecewise_constant_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/GasketTemperatureShiftedPronyHistory.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `reference_temperature_K` | `K` |
| `interval_temperature_K[]` | `K` |
| `reduced_time_s[]` | `s` |
| `temperature_shift_history[].shift_factor` | `1` |
| `temperature_shift_history[].reduced_interval_time_s` | `s` |
| `constitutive_response_history[].total_compressive_stress_Pa` | `Pa` |
| `constitutive_response_history[].compressive_force_N` | `N` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- A caller-calibrated, thermorheologically simple time-temperature shift modifies the Prony relaxation clock while other material parameters remain at the reference condition.
- The existing exact piecewise-linear strain/generalized-Maxwell solver is reused in reduced time; actual interval temperatures are piecewise constant caller inputs.
- This is an isothermal-equivalent constitutive screening history, not a thermally coupled joint or seal qualification model.

## 구현 근거·독립 설명

- `caller_gasket_prony_time_temperature_shift_parameters`: Use caller-evidenced Arrhenius or WLF parameters to compute a time-temperature shift factor for an existing generalized-Maxwell Prony response within explicit review and temperature support. No parameters are inferred or transferred between formulations.
- `caller_gasket_prony_constitutive_response`: Integrate caller-authorized generalized Maxwell branch stresses over a piecewise-linear compressive-strain history using the closed-form update for each declared relaxation time. Preserve initial internal stresses, material condition, specimen, temperature, provider revision and source/configuration digests. Do not fit or transfer coefficients, model tensile contact loss, flange flexibility, leakage or acceptance.
- `arrhenius_reduced_time_prony_shift`: Scale elapsed Prony time by an Arrhenius shift factor from caller activation energy and reference temperature, then pass reduced-time increments to the existing linear viscoelastic generalized-Maxwell solver. This does not shift modulus, solve heat transfer, or imply contact or leakage performance.
- `wlf_reduced_time_prony_shift`: Scale elapsed Prony time by a caller WLF shift factor using caller constants and reference temperature, then reuse the existing generalized-Maxwell solver. The implementation enforces supplied support and does not establish a universal shift law or material qualification.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "fabrication.gasket_prony_temperature_shift_history"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/models/gasket_temperature_shifted_prony_history.py#L92)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

# `integration.wet_co2_transient_gas_carbonate_alkalinity_equilibrium`

**목적:** Only the ideal carbonate-only system is equilibrated using caller conditional K1, K2 and Kw values with explicit pH support.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `initial_liquid_volume_m3` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `initial_gas_fugacity_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `gas_molar_capacity_mol_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `wall_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `initial_total_inorganic_carbon_mol_m3` | 예 | `{"minimum": 0, "type": "number"}` | mol/m³ |
| `initial_total_alkalinity_mol_m3` | 예 | `{"type": "number"}` | mol/m³ |
| `intervals` | 예 | `{"items": {"$ref": "#/$defs/WetCo2TransientCarbonateInterval"}, "maxItems": 10000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `absolute_tolerance_mol` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_tolerance_fugacity_Pa` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0, "type": "number"}` | Pa |
| `relative_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMaximum": 1.0, "exclusiveMinimum": 0.0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_step_s` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | s |
| `initial_state_evidence` | 예 | `{"$ref": "#/$defs/Evidence"}` | 계약·필드 설명 참조 |
| `initial_state_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `initial_state_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `initial_state_record_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `equilibrium_model_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `ideal_carbonate_only_activity_assumption_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `finite_gas_and_well_mixed_liquid_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `intervalwise_constant_input_and_operator_split_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `physical_scope_and_clock_match_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WetCo2TransientCarbonateHistoryRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_s` | `s` |
| `temperature_K` | `K` |
| `gas_fugacity_Pa` | `Pa` |
| `gas_inventory_mol` | `mol` |
| `total_inorganic_carbon_mol_m3` | `mol/m3` |
| `total_alkalinity_mol_m3` | `mol/m3 as charge equivalents` |
| `species_mol_m3.*` | `mol/m3` |
| `carbon_balance_residual_mol` | `mol` |
| `alkalinity_balance_residual_mol_eq` | `mol as charge equivalents` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Only the ideal carbonate-only system is equilibrated using caller conditional K1, K2 and Kw values with explicit pH support.
- Finite gas exchange is coupled to dissolved CO2-star; total carbon and alkalinity inventories receive caller wall and waterborne fluxes.
- The model requires SciPy DOP853 at runtime and performs no interpolation across exact caller interval knots.

## 구현 근거·독립 설명

- `caller_wet_co2_conditional_carbonate_equilibrium_parameters`: Resolve ideal carbonate-only species fractions at each transient integration evaluation from caller-provided, temperature-matched conditional equilibrium constants and current DIC and alkalinity. Preserve reviewed source and solvent lineage; do not imply nonideal activity or complete electrolyte speciation.
- `caller_wet_co2_wall_carbon_and_alkalinity_flux_schedule`: Apply signed caller-declared carbon and alkalinity-equivalent flux schedules over exact transient intervals, with explicit physical basis and evidence lineage. Fluxes are exogenous and do not imply corrosion kinetics or electrochemical coupling.
- `caller_finite_gas_carbonate_transfer_and_variable_liquid`: Integrate finite gas CO2 inventory, dissolved inorganic carbon, total alkalinity, and variable well-mixed liquid volume using caller-supplied transfer, gas-volume, Henry, initial-state and inflow/outflow parameters. Couple to ideal carbonate-only conditional equilibrium; no external chemistry, activity model, or corrosion law is inferred.
- [SciPy scipy.integrate.solve_ivp API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html) · `scipy_integrate_solve_ivp`
- [SciPy DOP853 solver documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.DOP853.html) · `scipy_integrate_dop853`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.wet_co2_transient_gas_carbonate_alkalinity_equilibrium"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
# 아래 이름의 실제 Python provider를 준비한 뒤 runtime_dependencies로 전달한다.
# JSON만으로 외부 callable을 직렬화하거나 실행하지 않는다.
providers = {'scipy': ...}
result = registry.run_json(model_id, payload, context, runtime_dependencies=providers)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/wet_co2_transient_carbonate_gas_equilibrium.py#L165)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

# `integration.wet_co2_lumped_wall_thermal_condensation_history`

**목적:** A single wall temperature is governed by a lumped areal heat capacity and caller heat boundary terms.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.wet_co2_lumped_wall_thermal_condensation_history.v1", "default": "matintegrity.wet_co2_lumped_wall_thermal_condensation_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `wall_patch_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `initial_wall_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `initial_gas_water_vapor_moles` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `initial_wall_water_areal_inventory_kg_m2` | 예 | `{"minimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `wall_areal_heat_capacity_J_m2_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `saturation_fugacity_table` | 예 | `{"items": {"$ref": "#/$defs/WallWaterSaturationPoint"}, "maxItems": 10000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `saturation_table_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `saturation_table_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `saturation_table_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `saturation_table_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 64, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `intervals` | 예 | `{"items": {"$ref": "#/$defs/LumpedWallCondensationInterval"}, "maxItems": 20000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `rtol` | 예 | `{"exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `atol_temperature_K` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | K |
| `atol_gas_moles` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `atol_liquid_kg_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `atol_energy_J_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `max_step_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `lumped_wall_temperature_and_fixed_patch_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `energy_boundary_and_latent_heat_sign_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `finite_gas_ideal_component_pressure_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `saturation_table_basis_and_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `no_wall_phase_change_or_spatial_gradient_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calculation_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WetCo2LumpedWallThermalCondensationRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `final_wall_temperature_K` | `K` |
| `final_gas_water_vapor_moles` | `mol` |
| `final_wall_water_areal_inventory_kg_m2` | `kg/m^2` |
| `state_history[].cumulative_external_heat_J_m2` | `J/m^2` |
| `state_history[].cumulative_sensible_heat_J_m2` | `J/m^2` |
| `state_history[].cumulative_latent_heat_J_m2` | `J/m^2` |
| `interval_ledger[].wall_energy_balance_residual_J_m2` | `J/m^2` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- A single wall temperature is governed by a lumped areal heat capacity and caller heat boundary terms.
- Finite gas water transfer uses the gas-fugacity to wall-saturation-fugacity driving force with caller transfer coefficient.
- Wall water vapor saturation fugacity is linearly interpolated within the caller's strictly increasing tabulated support.
- Latent heat is added to the wall for condensation and removed for evaporation; liquid depletion blocks further evaporation.

## 구현 근거·독립 설명

- `caller_temperature_tabulated_wall_water_saturation_fugacity`: Supply an evidence-linked finite wall-temperature/saturation-fugacity table and an explicit interpolation review. Requests outside tabulated support are rejected; no water activity, extrapolation or thermodynamic property is inferred.
- `caller_lumped_wall_heat_capacity_and_boundary_flux`: Specify caller wall-patch areal heat capacity and interval-constant external heat flux, gas-side heat-transfer coefficient and boundary orientation. These inputs do not constitute a validated conjugate heat-transfer model.
- `caller_finite_gas_water_film_transfer_parameters`: Specify caller gas-film transfer coefficient, finite-gas state and patch area for a coupled wall-energy and vapor-inventory balance. No hydrodynamic correlation is selected automatically.
- `lumped_wall_energy_and_finite_gas_water_mass_balance`: Co-integrate wall temperature, finite ideal-gas water inventory, condensate areal inventory and external/sensible/latent energy terms using the caller tabulated saturation fugacity and SciPy DOP853. Stop outside saturation-table support and preserve mass/energy residuals; no saline activity or corrosion law is inferred.
- [SciPy scipy.integrate.solve_ivp API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html) · `scipy_integrate_solve_ivp`
- [SciPy DOP853 solver documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.DOP853.html) · `scipy_integrate_dop853`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.wet_co2_lumped_wall_thermal_condensation_history"
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

[계산 구현과 주석 확인](../../../src/matintegrity/wet_co2_wall_thermal_condensation.py#L156)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

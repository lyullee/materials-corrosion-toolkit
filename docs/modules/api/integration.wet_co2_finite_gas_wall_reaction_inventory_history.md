# `integration.wet_co2_finite_gas_wall_reaction_inventory_history`

**목적:** Finite gas inventory, Henry coefficient, film coefficients, volume flux, incoming dissolved CO2*, initial state and solver tolerances are caller-owned and Evidence-linked.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.wet_co2_wall_reaction_coupled_history.v1", "default": "matintegrity.wet_co2_wall_reaction_coupled_history.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `location_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `wall_patch_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `condition_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_basis` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `wall_patch_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `initial_liquid_volume_per_area_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `initial_liquid_co2star_mol_m3` | 예 | `{"minimum": 0, "type": "number"}` | mol/m³ |
| `initial_gas_co2_fugacity_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `finite_gas_inventory_capacity_mol_m2_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `initial_state_provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `initial_state_provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `initial_state_configuration_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `initial_state_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `initial_state_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 64, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `intervals` | 예 | `{"items": {"$ref": "#/$defs/WetCo2FiniteGasVariableLiquidInterval"}, "maxItems": 2000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `electrochemical_metal_loss_result` | 예 | `{"$ref": "#/$defs/AssessmentResult"}` | 계약·필드 설명 참조 |
| `electrochemical_metal_loss_result_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `co2star_wall_consumption_mappings` | 예 | `{"items": {"$ref": "#/$defs/Co2starWallConsumptionMapping"}, "maxItems": 32, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `relative_tolerance` | 아니오 | `{"default": 1e-09, "maximum": 0.001, "minimum": 1e-12, "type": "number"}` | 계약·필드 설명 참조 |
| `liquid_concentration_absolute_tolerance_mol_m3` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | mol/m³ |
| `gas_fugacity_absolute_tolerance_Pa` | 아니오 | `{"default": 0.001, "exclusiveMinimum": 0, "type": "number"}` | Pa |
| `areal_mole_absolute_tolerance_mol_m2` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_step_s` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | s |
| `fixed_area_and_gas_capacity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `positive_volume_flux_is_condensate_inflow_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `negative_volume_flux_is_well_mixed_liquid_outflow_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `no_dryout_within_simulated_history_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `incoming_co2star_convention_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `electrochemical_source_applicability_for_patch_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `metal_loss_and_transfer_clock_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `co2star_consumption_stoichiometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `area_and_volume_loss_additivity_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `solver_tolerances_and_use_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `calculation_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WetCo2WallReactionCoupledHistoryRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `state_history[].time_s` | `s` |
| `state_history[].liquid_co2star_mol_m3` | `mol/m3` |
| `state_history[].gas_co2_fugacity_Pa` | `Pa` |
| `state_history[].liquid_co2star_areal_inventory_mol_m2` | `mol/m2` |
| `state_history[].gas_co2_areal_inventory_mol_m2` | `mol/m2` |
| `state_history[].cumulative_wall_reaction_co2star_consumed_mol_m2` | `mol/m2` |
| `state_history[].cumulative_anodic_wall_metal_loss_kg` | `kg` |
| `state_history[].cumulative_area_average_anodic_recession_m` | `m` |
| `interval_ledger[].combined_inventory_balance_residual_mol_m2` | `mol/m2` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Finite gas inventory, Henry coefficient, film coefficients, volume flux, incoming dissolved CO2*, initial state and solver tolerances are caller-owned and Evidence-linked.
- A separately computed, digest-pinned anodic metal-loss history supplies piecewise-constant wall-source demand over exactly aligned intervals and the same physical wall area.
- CO2* consumption per removed-metal mole is an independent caller stoichiometric mapping with source Evidence and atom/carbon-balance review; it is never inferred from the metal-loss result.
- The coupled balance solves CO2* transfer and depletion with externally forced wall loss; it does not feed changing CO2 state back into electrochemical kinetics and does not solve full aqueous speciation, scale growth or corrosion qualification.
- Anodic area-average recession uses caller-mapped alloy molar masses, densities and uniform/additive-volume review; it is not a localized corrosion depth or remaining-wall assessment.

## 구현 근거·독립 설명

- `caller_wet_co2_electrochemical_co2star_sink_mapping`: Couple externally supplied CO2* consumption per anodically removed-metal mole with a computed digest-pinned partial-current metal-loss history. Keep reaction mapping, review, alloy density and molar mass as caller inputs; do not infer electrochemical kinetics or local penetration.
- `caller_finite_gas_variable_liquid_two_film_balance`: Integrate caller-specified finite gas CO2 fugacity inventory, variable well-mixed liquid volume and CO2star concentration with piecewise-constant two-film transfer, signed condensate volume flux, and caller-specified inflow CO2star composition. Use a caller-pinned numerical IVP solver and record the per-area gas/liquid inventory ledger and closure residual. No EOS, gas capacity, correlations, water chemistry, reaction, spatial gradient or corrosion law is inferred.
- `electrochemical_partial_current_to_metal_loss`: Require a computed digest-pinned mixed-potential history and caller-reviewed metal-dissolution mapping for each selected reaction. Integrate each upstream reference-area current-density branch with the exact trapezoid integral under a declared piecewise-linear between-knot reconstruction. Divide charge by the upstream reaction electron number and Faraday constant, apply the caller metal-atom stoichiometric factor and evidence-linked molar mass, then divide signed mass change by caller density and actual mapped branch area for a uniform area-average recession. Report anodic and cathodic equivalents separately from signed net transfer. This implements Faraday charge-to-reaction accounting only; it does not validate current kinetics, alloy selectivity, completeness of selected dissolution reactions, local attack, evolving geometry or corrosion qualification.
- [SciPy scipy.integrate.solve_ivp API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html) · `scipy_integrate_solve_ivp`
- [SciPy DOP853 solver documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.DOP853.html) · `scipy_integrate_dop853`

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.wet_co2_finite_gas_wall_reaction_inventory_history"
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

[계산 구현과 주석 확인](../../../src/matintegrity/wet_co2_wall_reaction_coupled_history.py#L220)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

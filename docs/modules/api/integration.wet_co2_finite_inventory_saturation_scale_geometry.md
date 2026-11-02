# `integration.wet_co2_finite_inventory_saturation_scale_geometry`

**목적:** Wall activities use molarity standard state, caller activity coefficients and a caller log10 Ksp at each exact time knot.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.wet_co2_finite_inventory_saturation_scale_geometry.v1", "default": "matintegrity.wet_co2_finite_inventory_saturation_scale_geometry.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `solid_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `geometry_seed` | 예 | `{"$ref": "#/$defs/WetCo2CylindricalScaleGeometryHistory"}` | 계약·필드 설명 참조 |
| `geometry_result` | 예 | `{"$ref": "#/$defs/Calculation"}` | 계약·필드 설명 참조 |
| `finite_liquid_inventory_results` | 예 | `{"additionalProperties": {"$ref": "#/$defs/Calculation"}, "maxProperties": 64, "minProperties": 1, "type": "object"}` | 계약·필드 설명 참조 |
| `aqueous_species` | 예 | `{"items": {"$ref": "#/$defs/WetCo2TransientSpecies"}, "maxItems": 64, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `solid_elemental_composition` | 예 | `{"additionalProperties": {"exclusiveMinimum": 0, "type": "number"}, "type": "object"}` | 계약·필드 설명 참조 |
| `activity_product_terms` | 예 | `{"items": {"$ref": "#/$defs/WetCo2CylindricalActivityProductTerm"}, "maxItems": 32, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `phase_activity_history` | 예 | `{"items": {"$ref": "#/$defs/WetCo2CylindricalPhaseActivityKnot"}, "maxItems": 5000, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `kinetics_template` | 예 | `{"$ref": "#/$defs/CallerSurfaceScaleKinetics"}` | 계약·필드 설명 참조 |
| `nonreaction_wall_exchanges` | 예 | `{"items": {"$ref": "#/$defs/WetCo2FiniteLiquidWallExchange"}, "maxItems": 32000, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `layer_order_steel_to_bore` | 예 | `{"items": {"type": "string"}, "maxItems": 1, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `concentration_inventory_abs_tolerance_mol` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `concentration_inventory_relative_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `geometry_kinetic_inventory_abs_tolerance_mol` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `geometry_kinetic_inventory_relative_tolerance` | 아니오 | `{"default": 1e-06, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `precipitation_area_basis_and_reaction_closure_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `wall_activity_standard_state_and_phase_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `saturation_interpolation_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `geometry_layer_and_segment_area_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WetCo2FiniteInventorySaturationScaleGeometry.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `saturation_history[].wall_concentration_mol_m3_by_species.*` | `mol/m^3` |
| `saturation_history[].saturation_ratio` | `1` |
| `finite_liquid_phase_exchange_closure[].selected_phase_area_m2` | `m^2` |
| `finite_liquid_phase_exchange_closure[].kinetic_net_phase_change_mol` | `mol` |
| `finite_liquid_phase_exchange_closure[].geometry_phase_change_mol` | `mol` |
| `finite_liquid_phase_exchange_closure[].wall_liquid_species_closure.*.closure_residual_mol` | `mol` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Wall activities use molarity standard state, caller activity coefficients and a caller log10 Ksp at each exact time knot.
- One caller-selected neutral solid and its explicit aqueous dissolution-product stoichiometry are used.
- Caller finite-liquid inventory results include both nonreaction wall exchange and the selected solid's reaction exchange; this module verifies the decomposition.
- Scale kinetics are mapped to a single dense annular phase and checked against exact cylindrical phase inventory changes.

## 구현 근거·독립 설명

- `caller_cylindrical_finite_liquid_inventory_results`: Require exact, computed finite-compartment liquid concentration/inventory histories for the selected transported aqueous species; no liquid states are reconstructed from gas data.
- `caller_finite_inventory_wall_activity_and_ksp_records`: Caller supplies digest-pinned wall activity coefficients, activity-product species terms and temperature-supported solubility-product records for one explicitly selected solid phase.
- `caller_surface_scale_kinetics_configuration`: Use the caller's existing surface-scale kinetic parameterization only after exact saturation ratio and wall state mapping; no kinetic coefficient is inferred or fitted.
- `caller_cylindrical_scale_geometry_seed`: Start from a caller-pinned cylindrical geometry state and preserve layer order, selected phase identity and axial segment basis through the scale update.
- `finite_liquid_to_solid_reaction_stoichiometric_closure`: Bridge a single selected solid's caller saturation and kinetic increments to finite aqueous wall-species inventory changes using balanced stoichiometry, then update cylindrical layer inventory and geometry; fail closed on concentration/solid balance residuals or depletion. This is a bounded operator-split bridge, not full multiphase equilibrium, nucleation or a qualified corrosion model.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.wet_co2_finite_inventory_saturation_scale_geometry"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/wet_co2_finite_inventory_saturation_scale_geometry.py#L176)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

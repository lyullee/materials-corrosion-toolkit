# `integration.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback`

**목적:** Caller supplies a complete finite aqueous mass-action network, activity and equilibrium provider lineage, reaction formulae, natural-log Ksp and kinetic parameters with bound Evidence.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback.v1", "default": "matintegrity.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `spatial_request` | 예 | `{"$ref": "#/$defs/WetCo2CylindricalSpatialMixedPotential"}` | 계약·필드 설명 참조 |
| `mass_action_system_template` | 예 | `{"$ref": "#/$defs/AqueousMassActionSystem"}` | 계약·필드 설명 참조 |
| `phases` | 예 | `{"items": {"$ref": "#/$defs/WetCo2FiniteGasStageSpeciationKineticPhase"}, "maxItems": 32, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_feedback_iterations` | 아니오 | `{"default": 20, "maximum": 60, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `relaxation_factor` | 아니오 | `{"default": 0.5, "exclusiveMinimum": 0, "maximum": 1, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_radius_tolerance_m` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "type": "number"}` | m |
| `relative_radius_tolerance` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_inventory_tolerance_mol_m` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `relative_inventory_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_work_units` | 아니오 | `{"default": 30000000, "maximum": 300000000, "minimum": 10000, "type": "integer"}` | 계약·필드 설명 참조 |
| `mass_action_network_and_standard_state_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `phase_identity_and_balanced_reaction_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `cylindrical_supply_map_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `exact_knot_left_hold_and_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `no_qualification_claim_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `gas_transfer_species_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `initial_gas_co2_fugacity_Pa` | 예 | `{"minimum": 0, "type": "number"}` | Pa |
| `gas_inventory_capacity_mol_per_axial_metre_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | Pa |
| `gas_liquid_interfacial_area_m_per_axial_metre` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `henry_concentration_over_fugacity_mol_m3_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `gas_film_coefficient_mol_m2_s_Pa` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `liquid_film_coefficient_m_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m/s |
| `transfer_parameter_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `transfer_provider_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `transfer_provider_revision` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `transfer_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 64, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `initial_gas_state_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `initial_gas_state_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 64, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `finite_gas_and_fixed_transfer_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WetCo2CylindricalFiniteGasStageSpeciationFeedback.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_s[]` | `s` |
| `geometry_history[].bore_radius_m` | `m` |
| `geometry_history[].steel_inner_radius_m` | `m` |
| `history[].phase_inventory_mol_m_by_phase.*` | `mol/m` |
| `interval_ledger[].time_averaged_scale_flux_mol_m2_s_by_phase.*` | `mol/m^2/s` |
| `interval_ledger[].aqueous_inventory_residual_mol_m_by_species.*` | `mol/m` |
| `history[].gas_co2_fugacity_Pa` | `Pa` |
| `history[].finite_gas_inventory_mol_m` | `mol/m` |
| `interval_ledger[].gas_to_liquid_transfer_mol_m` | `mol/m` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller supplies a complete finite aqueous mass-action network, activity and equilibrium provider lineage, reaction formulae, natural-log Ksp and kinetic parameters with bound Evidence.
- Mass-action component constraints are rebuilt from stage wall concentrations and solved in log-activity coordinates at every BDF evaluation.
- The caller power law uses the current stage activities; radial supply, phase inventory and common geometry are bounded and updated in the coupled calculation.
- A caller fixed-capacity gas reservoir exchanges one declared neutral carbon-bearing aqueous species through caller-supplied Henry and two-film data at the outer radial cell.

## 구현 근거·독립 설명

- `caller_mass_action_activities_for_stage_scale_kinetics`: Uses the caller's fixed, evidence-bound aqueous reaction network and standard states to provide activities to the selected scale kinetic law.
- `multireactant_cylindrical_supply_and_inventory_limiter_at_bdf_stages`: Shared cylindrical reactant-supply and live-solid-inventory limiter reevaluated at each BDF stage.
- `aqueous_mass_action_recomputed_from_stage_wall_composition`: Rebuilds caller linear component totals from each BDF-stage wall-cell molar composition and re-solves the declared log-activity mass-action system; no species or reaction topology is inferred.
- `caller_finite_gas_cylindrical_two_film_transfer_and_inventory`: Uses caller-evidenced fixed-capacity gas inventory, Henry relation, interfacial area and two-film coefficients for cylindrical stage coupling.
- `finite_gas_aqueous_bv_scale_element_balance`: Balances finite gas, aqueous species, scale phases, wall release and external radial exchange by element at each interval.
- `caller_finite_gas_inventory_initial_state`: Pins the initial finite-gas fugacity and capacity to caller-provided licensed evidence.
- `finite_gas_and_outer_liquid_stage_inventory_flux_limit`: Limits each BDF-stage two-film transfer rate by available finite gas or outer radial-cell liquid inventory over the interval remainder.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/wet_co2_cylindrical_finite_gas_stage_speciation_feedback.py#L598)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

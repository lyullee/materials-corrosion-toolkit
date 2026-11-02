# `transport.crevice_spatial_activity_solid_nernst_planck_1d`

**목적:** Each interval uses the existing conservative variable-volume finite-volume Nernst-Planck BDF solver, including caller face areas, velocity, ionic diffusivity, zero-current closure and blind-tip no-flux boundary.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_spatial_chemistry_transport.v1", "default": "matintegrity.crevice_spatial_chemistry_transport.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `transport` | 예 | `{"$ref": "#/$defs/VariableAreaCreviceActivityReactiveTransportRequest"}` | 계약·필드 설명 참조 |
| `chemistry_by_knot` | 예 | `{"items": {"$ref": "#/$defs/CreviceChemistryKnot"}, "maxItems": 500, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `maximum_cell_chemistry_iterations` | 아니오 | `{"default": 50, "maximum": 1000, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_transport_function_evaluations` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 100, "type": "integer"}` | 계약·필드 설명 참조 |
| `fixed_point_concentration_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `fixed_point_solid_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `fixed_point_constraint_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `chemistry_damping_fraction` | 아니오 | `{"default": 0.5, "exclusiveMinimum": 0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `chemistry_transport_species_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `conserved_linear_constraint_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `zero_current_and_electroneutrality_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `knotwise_instantaneous_chemistry_operator_split_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `geometry_and_cell_order_alignment_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceSpatialChemistryTransportRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `state_history[].time_s` | `s` |
| `state_history[].aqueous_concentration_mol_m3_by_species_and_cell.*[]` | `mol/m^3` |
| `state_history[].solid_inventory_mol_m3_by_cell.*` | `mol/m^3_solution` |
| `element_inventory_closure_history[].total_moles_by_element.*` | `mol` |
| `element_inventory_closure_history[].external_inflow_moles_by_element.*` | `mol` |
| `element_inventory_closure_history[].closure_residual_moles_by_element.*` | `mol` |
| `total_transport_function_evaluations` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Each interval uses the existing conservative variable-volume finite-volume Nernst-Planck BDF solver, including caller face areas, velocity, ionic diffusivity, zero-current closure and blind-tip no-flux boundary.
- At each exact knot, caller mass-action/Davies and finite competing-solid equilibria are solved; aqueous and solid states are carried into the next interval.
- The left-knot chemistry activity coefficients are held constant within each BDF interval; chemistry is not solved at internal integrator stages.
- Every caller linear chemistry constraint must span each declared aqueous elemental inventory; kinetic and phase discovery are not automatic.

## 구현 근거·독립 설명

- `caller_cellwise_aqueous_and_solid_equilibrium_by_knot`: At each exact transport knot and mapped cell, consume caller-declared aqueous species/reactions/linear inventory constraints, temperature-specific activity inputs, finite solid candidates and equilibrium records. Preserve input/result digests and record the provider's species order, cell identity and geometry knot. No automatic species or phase discovery is performed.
- `sequential_variable_volume_nernst_planck_and_local_chemistry_operator_split`: For each adjacent exact time-knot pair, run the existing BDF variable-volume finite-volume Nernst-Planck transport with caller face areas, flow, diffusivity, mouth boundary and balanced kinetic reaction rates. Hold each cell activity coefficient at its left-knot equilibrium value within that interval; at the right knot, re-solve caller Davies/mass-action speciation and finite competing-solid equilibrium, then carry aqueous concentrations and phase inventories into the next interval. Check per-interval species inventory, local charge and zero-current residuals, per-knot aqueous-plus-solid elemental inventory against integrated mouth/reaction sources, bounded solver evaluations, and full interval/knot digests. This is sequential operator splitting, not a monolithic within-step chemistry/transport solve; no kinetic precipitation, electrochemical source, aperture feedback or integrity qualification is inferred.
- `caller_crevice_variable_area_history`: Caller-provided exact-knot cell and face cross-sectional area histories, bound to geometry identity, provider revision, configuration digest, usage license and exact solver clock.
- `caller_crevice_activity_corrected_transport_species`: Caller declares ionic species charge, constant diffusivity and initial cell concentration for a reaction-free transport interval; no property table is bundled.
- `caller_activity_based_crevice_reaction_network`: Caller supplies exact-knot forward/reverse rate and dimensionless equilibrium-constant schedules on an activity basis, balanced reaction stoichiometry, per-record digests and a digest-pinned network manifest. No kinetic calibration or chemical mechanism is bundled.
- `aqueous_solid_inventory_feedback_fixed_point`: Alternate a computed aqueous activity/speciation state with the finite competing-solid inventory transfer, update the declared linear aqueous conservation targets by the stoichiometric concentration change, and damp/re-solve until aqueous, solid-inventory and constraint residuals meet caller tolerances. Cell calculations are independent at one fixed geometry knot; convergence is numerical and does not establish global thermodynamic stability or physical qualification.
- `scipy_integrate_bdf`: Integrate the declared stiff initial-value transport system with SciPy's variable-order backward differentiation formula implementation using caller-selected tolerances and ordered output times; numerical solver choice does not establish physical validation.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "transport.crevice_spatial_activity_solid_nernst_planck_1d"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_spatial_chemistry_transport.py#L340)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

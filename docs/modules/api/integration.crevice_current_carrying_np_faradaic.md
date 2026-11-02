# `integration.crevice_current_carrying_np_faradaic`

**목적:** Cell 0 is the potential gauge at each exact knot; mouth and blind tip have zero ionic current.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_current_carrying_np_faradaic.v1", "default": "matintegrity.crevice_current_carrying_np_faradaic.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `faradaic_coupling` | 예 | `{"$ref": "#/$defs/CreviceFaradaicSpatialChemistryRequest"}` | 계약·필드 설명 참조 |
| `maximum_interval_fixed_point_iterations` | 아니오 | `{"default": 30, "maximum": 1000, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_transport_function_evaluations` | 아니오 | `{"default": 5000000, "maximum": 20000000, "minimum": 100, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_mixed_potential_function_evaluations` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 100, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_bdot_stage_activity_evaluations` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 100, "type": "integer"}` | 계약·필드 설명 참조 |
| `absolute_face_current_closure_tolerance_A` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `relative_face_current_closure_tolerance` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_potential_fixed_point_tolerance_V` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "type": "number"}` | V |
| `relative_potential_fixed_point_tolerance` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_branch_current_fixed_point_tolerance_A_m2` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "type": "number"}` | A/m² |
| `relative_branch_current_fixed_point_tolerance` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `relative_chemistry_fixed_point_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_charge_inventory_tolerance_mol_eq` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `relative_charge_inventory_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `relaxation_fraction` | 아니오 | `{"default": 0.5, "exclusiveMinimum": 0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `potential_gauge_cell_index` | 아니오 | `{"const": 0, "default": 0, "type": "integer"}` | 계약·필드 설명 참조 |
| `mouth_electrical_boundary` | 아니오 | `{"const": "insulated_zero_current", "default": "insulated_zero_current", "type": "string"}` | 계약·필드 설명 참조 |
| `blind_tip_electrical_boundary` | 아니오 | `{"const": "insulated_zero_current", "default": "insulated_zero_current", "type": "string"}` | 계약·필드 설명 참조 |
| `np_current_matches_mixed_potential_sign_convention_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `local_charge_storage_excluded_and_faradaic_source_closes_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `potential_gauge_and_insulated_end_conditions_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `face_area_current_density_and_mixed_potential_mesh_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computation_scope_and_solver_budgets_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `faradaic_source_integration_mode` | 아니오 | `{"default": "endpoint_trapezoid", "enum": ["endpoint_trapezoid", "bdf_stage_linear_current", "bdf_stage_spatial_mixed_potential"], "type": "string"}` | 계약·필드 설명 참조 |
| `bdf_stage_linear_current_source_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `bdf_stage_spatial_mixed_potential_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `bdf_stage_bdot_activity_by_interval` | 아니오 | `{"anyOf": [{"items": {"$ref": "#/$defs/AqueousBdotIteration"}, "type": "array"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `bdf_stage_bdot_activity_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceCurrentCarryingNernstPlanckRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `accepted_intervals[].start_time_s` | `s` |
| `accepted_intervals[].end_time_s` | `s` |
| `accepted_intervals[].ionic_face_current_A_by_boundary[]` | `A` |
| `accepted_intervals[].wall_faradaic_current_A_by_cell[]` | `A` |
| `exact_knot_current_time_s[]` | `s` |
| `exact_knot_ionic_face_current_A_by_boundary[][]` | `A` |
| `exact_knot_branch_current_density_A_m2_by_branch_and_cell.*[][]` | `A/m^2` |
| `accepted_intervals[].faradaic_extent_mol_by_branch_and_cell.*[]` | `mol` |
| `accepted_intervals[].faradaic_aqueous_source_mol_by_species.*[]` | `mol` |
| `accepted_intervals[].endpoint_aqueous_concentration_mol_m3_by_species_and_cell.*[]` | `mol/m^3` |
| `accepted_intervals[].endpoint_solid_inventory_mol_m3_by_cell.*` | `mol/m^3_solution` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Cell 0 is the potential gauge at each exact knot; mouth and blind tip have zero ionic current.
- The caller mixed-potential face current is coupled to Nernst-Planck migration and must match the constitutive ionic flux.
- The legacy mode uses endpoint trapezoid splitting; opt-in bdf_stage_linear_current uses endpoint-linear branch-current interpolation and integrates cellwise sources/extents inside BDF stages. Signed charge stoichiometry must satisfy sum(z nu)=+n.
- Potential and equilibrium chemistry are solved at exact knots in legacy and linear-current modes. The opt-in spatial mixed-potential stage mode re-solves the quasi-steady ohmic/Butler-Volmer balance within each BDF RHS evaluation using fixed caller reaction topology and trial concentrations; that algebraic solve is not part of the BDF Newton Jacobian, and double-layer storage and phase discovery are not modeled.
- Optional B-dot stage activity refresh is caller-evidence-bound and coefficient-only; it is evaluated once per BDF RHS from mouth-plus-cell trial concentrations and feeds NP activity gradients, homogeneous activity-based kinetic rates, and stage Nernst/BV. It does not solve speciation or phase equilibrium; exact-knot/end-point chemistry remains on its existing activity model path.
- The caller provides all chemistry, kinetics, conductivity, geometry, reservoir and applicability inputs; no automatic discovery or qualification is included.

## 구현 근거·독립 설명

- `finite_volume_current_carrying_activity_nernst_planck_with_faradaic_wall_balance`: Integrate variable-volume species inventories with activity-gradient, advection, diffusion and migration fluxes. Interior migration uses the caller mixed-potential voltage gradient; boundary electrical currents are insulated. Faradaic wall reaction is a distinct endpoint-trapezoid species source. Iteration commits only when face-current, potential, branch-current, chemistry, charge and element ledgers close within declared tolerances; this does not include double-layer storage or within-step equilibrium.
- `mixed_potential_face_current_to_ionic_nernst_planck_flux_closure`: Compare the ionic current reconstructed from signed species face fluxes and caller face areas against the spatial mixed-potential current at each internal face. Reject constitutively incompatible conductivity and mobility mappings instead of adjusting transport fluxes to force agreement.
- `scipy_integrate_bdf`: Integrate the declared stiff initial-value transport system with SciPy's variable-order backward differentiation formula implementation using caller-selected tolerances and ordered output times; numerical solver choice does not establish physical validation.
- `endpoint_trapezoid_faradaic_inventory_split`: Apply caller-mapped Faradaic species sources and branch extents after each transport interval using endpoint trapezoidal integration; preserve this legacy operator-split method as the default and do not infer intra-interval kinetics.
- `endpoint_linear_branch_current_bdf_stage_inventory_source`: Interpolate caller-computed Faradaic branch-current densities linearly between exact-knot mixed-potential solutions, then integrate branch extents and mapped aqueous species sources inside the transport BDF stages. The mixed-potential/equilibrium solves remain endpoint-coupled; this method is not a fully coupled electrochemical DAE or a qualified corrosion law.
- `bdf_stage_spatial_ohmic_mixed_potential_and_faradaic_source`: At each BDF right-hand-side evaluation, solve the existing caller-parameterized spatial quasi-steady ohmic/Butler-Volmer mixed-potential problem from trial aqueous concentrations and stage geometry/conductivity records, then integrate its Faradaic branch sources and extents with transport. No double-layer storage, chemistry-phase discovery, or qualified corrosion kinetics are inferred.
- `caller_evidence_bound_bdot_activity_refresh_at_bdf_stages`: At every BDF RHS evaluation in the reviewed spatial mixed-potential mode, recompute caller-parameterized B-dot activity coefficients from the trial aqueous state and use the same coefficients in Nernst-Planck activity gradients, homogeneous activity-based kinetics and stage Nernst/Butler-Volmer calculations. Bind interval parameter request digests and bound total callback evaluations. This does not solve mass-action speciation, solid equilibrium or activity parameter qualification.
- `finite_volume_current_carrying_activity_nernst_planck_with_faradaic_wall_balance`: Integrate variable-volume species inventories with activity-gradient, advection, diffusion and migration fluxes. Interior migration uses the caller mixed-potential voltage gradient; boundary electrical currents are insulated. Faradaic wall reaction is a distinct endpoint-trapezoid species source. Iteration commits only when face-current, potential, branch-current, chemistry, charge and element ledgers close within declared tolerances; this does not include double-layer storage or within-step equilibrium.
- `mixed_potential_face_current_to_ionic_nernst_planck_flux_closure`: Compare the ionic current reconstructed from signed species face fluxes and caller face areas against the spatial mixed-potential current at each internal face. Reject constitutively incompatible conductivity and mobility mappings instead of adjusting transport fluxes to force agreement.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_current_carrying_np_faradaic"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_current_carrying_np_faradaic.py#L635)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

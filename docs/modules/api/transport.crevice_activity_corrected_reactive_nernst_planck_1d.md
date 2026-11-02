# `transport.crevice_activity_corrected_reactive_nernst_planck_1d`

**목적:** Caller activity-coefficient cell/time fields drive both the activity-gradient flux term and reversible local mass-action rates.

**모델 버전:** `1.0.0` · **구현 분류:** `engineering_screening` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `asset_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `physical_scope_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `clock_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `provider_revision` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `length_m` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | m |
| `cross_section_area_m2` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `cell_count` | 예 | `{"maximum": 300, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `output_time_s` | 예 | `{"items": {"type": "number"}, "maxItems": 500, "minItems": 2, "type": "array"}` | s |
| `concentration_standard_state_mol_m3` | 아니오 | `{"default": 1000.0, "exclusiveMinimum": 0, "type": "number"}` | mol/m³ |
| `species` | 예 | `{"items": {"$ref": "#/$defs/CreviceActivityReactiveSpecies"}, "maxItems": 40, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `mouth_boundary_concentration_mol_m3_by_species` | 예 | `{"additionalProperties": {"items": {"exclusiveMinimum": 0, "type": "number"}, "type": "array"}, "maxProperties": 40, "minProperties": 2, "type": "object"}` | 계약·필드 설명 참조 |
| `cell_face_axial_velocity_m_s_by_knot` | 예 | `{"items": {"items": {"type": "number"}, "type": "array"}, "maxItems": 301, "minItems": 3, "type": "array"}` | 계약·필드 설명 참조 |
| `relative_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_tolerance_mol_m3` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | mol/m³ |
| `maximum_step_s` | 예 | `{"exclusiveMinimum": 0, "type": "number"}` | s |
| `maximum_function_evaluations` | 아니오 | `{"default": 300000, "maximum": 10000000, "minimum": 100, "type": "integer"}` | 계약·필드 설명 참조 |
| `provider_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `rights_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 64, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `fixed_geometry_and_cell_order_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `activity_standard_state_single_ion_convention_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `activity_fields_and_time_interpolation_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `diffusivity_and_temperature_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `face_velocity_sign_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `local_electroneutrality_and_zero_current_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `mouth_boundary_and_blind_tip_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reaction_free_single_liquid_interval_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `schema_version` | 아니오 | `{"const": "matintegrity.crevice_activity_corrected_reactive_transport.v1", "default": "matintegrity.crevice_activity_corrected_reactive_transport.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `reactions` | 예 | `{"items": {"$ref": "#/$defs/CreviceActivityReactiveReaction"}, "maxItems": 100, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `temperature_K_by_knot` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 500, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `reaction_network_sha256` | 예 | `{"pattern": "^[a-f0-9]{64}$", "type": "string"}` | 계약·필드 설명 참조 |
| `reaction_network_evidence` | 예 | `{"items": {"$ref": "#/$defs/Evidence"}, "maxItems": 128, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `activity_mass_action_network_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reaction_charge_element_balance_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `kinetic_parameter_temperature_support_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceActivityReactiveTransportRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `state_history[].time_s` | `s` |
| `state_history[].species_concentration_mol_m3_by_id.*[]` | `mol/m^3` |
| `state_history[].species_inventory_mol_by_id.*` | `mol` |
| `state_history[].reaction_extent_rate_mol_m3_s_by_id_and_cell.*.net_extent_rate_mol_m3_s_by_cell[]` | `mol/(m^3*s)` |
| `state_history[].net_reaction_source_mol_m3_s_by_species_and_cell.*[]` | `mol/(m^3*s)` |
| `finite_volume_inventory_balance_residual_mol_by_species.*[]` | `mol` |
| `peak_zero_current_residual_mol_eq_m2_s` | `mol_eq/(m^2*s)` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller activity-coefficient cell/time fields drive both the activity-gradient flux term and reversible local mass-action rates.
- Reaction rates use caller parameter schedules on dimensionless activities; positive rate constants are interpolated in log space and co-integrated with finite-volume transport in one BDF system.
- Every reaction is charge- and element-balanced; equilibrium-constant and forward/reverse rate schedules are caller supplied and detailed-balance checked.
- No automatic speciation, phase transition, wall reaction, metal loss or corrosion rate is inferred.

## 구현 근거·독립 설명

- `caller_crevice_activity_corrected_transport_species`: Caller declares ionic species charge, constant diffusivity and initial cell concentration for a reaction-free transport interval; no property table is bundled.
- `caller_crevice_activity_coefficient_cell_time_fields`: Caller provides species-specific positive activity coefficients at every declared cell and time knot, plus a mouth coefficient history. Provider, standard state, single-ion convention and applicability are caller reviewed; no activity law or coefficient data are included.
- `caller_crevice_activity_corrected_mouth_boundary_history`: Caller supplies an electroneutral mouth concentration history and signed axial face-velocity schedule aligned to exact output time knots, with a no-flow blind tip.
- `caller_activity_based_crevice_reaction_network`: Caller supplies exact-knot forward/reverse rate and dimensionless equilibrium-constant schedules on an activity basis, balanced reaction stoichiometry, per-record digests and a digest-pinned network manifest. No kinetic calibration or chemical mechanism is bundled.
- `caller_crevice_activity_rate_reaction_records`: Caller supplies element/charge-balanced reversible reaction stoichiometry, positive forward/reverse volumetric rate constants, dimensionless equilibrium constants, record IDs/digests and licensed Evidence. The implementation does not fit or temperature-transfer kinetic parameters.
- `finite_volume_activity_nernst_planck_with_local_mass_action`: Co-integrate activity-corrected Nernst–Planck finite-volume transport with caller reversible mass-action sources in one stiff BDF system. Couple per-cell gamma fields to both the chemical-potential transport gradient and dimensionless reaction activities, retain mouth/no-flux-tip boundaries and track cumulative reaction inventory to close species balances. This is not full speciation, phase equilibrium, wall reaction or a qualified corrosion model.
- `scipy_integrate_bdf`: Integrate the declared stiff initial-value transport system with SciPy's variable-order backward differentiation formula implementation using caller-selected tolerances and ordered output times; numerical solver choice does not establish physical validation.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "transport.crevice_activity_corrected_reactive_nernst_planck_1d"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_activity_corrected_transport.py#L525)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

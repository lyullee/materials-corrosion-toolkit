# `integration.wet_co2_cylindrical_scale_recession_feedback`

**목적:** Every outer iteration recalculates spatial BV transport, phase saturation and wall kinetics, multilayer cylindrical diffusion supply, phase inventory and common wall geometry.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"const": "matintegrity.wet_co2_cylindrical_scale_recession_feedback.v1", "default": "matintegrity.wet_co2_cylindrical_scale_recession_feedback.v1", "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `spatial_request` | 예 | `{"$ref": "#/$defs/WetCo2CylindricalSpatialMixedPotential"}` | 계약·필드 설명 참조 |
| `phase_saturation_kinetics_requests` | 예 | `{"additionalProperties": {"$ref": "#/$defs/WetCo2CylindricalWallSaturationScaleKinetics"}, "maxProperties": 32, "minProperties": 1, "type": "object"}` | 계약·필드 설명 참조 |
| `multilayer_transport_request` | 예 | `{"$ref": "#/$defs/WetCo2CylindricalMultilayerTransportResistance"}` | 계약·필드 설명 참조 |
| `phase_growth_campaigns` | 예 | `{"additionalProperties": {"$ref": "#/$defs/WetCo2CylindricalPhaseGrowthCampaign"}, "maxProperties": 32, "minProperties": 1, "type": "object"}` | 계약·필드 설명 참조 |
| `maximum_feedback_iterations` | 아니오 | `{"default": 20, "maximum": 60, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `relaxation_factor` | 아니오 | `{"default": 0.5, "exclusiveMinimum": 0.0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_radius_tolerance_m` | 아니오 | `{"default": 1e-09, "exclusiveMinimum": 0, "type": "number"}` | m |
| `relative_radius_tolerance` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0.0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_phase_inventory_tolerance_mol_m` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `relative_phase_inventory_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0.0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_wall_element_tolerance_mol_m` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `relative_wall_element_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0.0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_feedback_work_units` | 아니오 | `{"default": 30000000, "maximum": 300000000, "minimum": 10000, "type": "integer"}` | 계약·필드 설명 참조 |
| `scale_kinetics_and_transport_are_separate_reviewed_paths` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `saturation_standard_state_and_phase_selection_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `diffusion_limited_reactant_supply_mapping_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `reaction_stoichiometry_and_phase_formula_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `alloy_release_and_scale_volume_geometry_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `no_unmodeled_aqueous_precipitation_sink_claim_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `no_inter_knot_or_qualification_claim_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WetCo2CylindricalScaleRecessionFeedback.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_s[]` | `s` |
| `final_geometry_history[].bore_radius_m` | `m` |
| `final_phase_inventory_mol_m_by_phase.*[]` | `mol/m` |
| `final_phase_inventory_fixed_point_residual_mol_m_by_phase.*[]` | `mol/m` |
| `final_steel_radius_fixed_point_residual_m` | `m` |
| `geometry_volume_closure_residual_m2_by_knot[]` | `m^2` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Every outer iteration recalculates spatial BV transport, phase saturation and wall kinetics, multilayer cylindrical diffusion supply, phase inventory and common wall geometry.
- Phase kinetic and diffusion paths use caller-declared, independently reviewed transport inputs on identical exact geometry knots.
- Precipitation/dissolution inventory uses left-held flux and the corresponding left-knot cylinder area; scale inventory is not added as an aqueous reaction sink in the BV transport solve.
- The outer relaxed iteration is bounded and followed by a final strict metal wall geometry closure solve; no contraction or uniqueness guarantee is claimed.
- All phase selection, activity, solubility, kinetic coefficients, reactant supply mapping, alloy composition and cylindrical assumptions are caller supplied.

## 구현 근거·독립 설명

- `bounded_feedback_of_caller_scale_kinetics_diffusion_supply_and_bv_recession`: Iterate the registered cylindrical spatial BV/recession solver with caller wall-saturation kinetics, exact annular multilayer diffusion supply, phase inventory updates and cylindrical geometry. Saturation kinetics/transport and BV transport remain separate caller calculations; scale precipitation is not inserted as an aqueous sink in the BV ODE.
- `independent_transient_cylindrical_finite_volume_electrochemical_inventory`: Independently assemble a radial finite-volume transient species inventory over exact caller geometry knots, couple reviewed caller Butler–Volmer branches through a shared zero-current potential, and remap inventories across moving cylindrical geometry with explicit species, aqueous element/charge, wall-element and circuit closure ledgers. No reaction kinetics, thermodynamic property table, calibration or corrosion qualification is bundled.
- `caller_cylindrical_transient_species_history_for_wall_saturation`: Caller-paired transient cylindrical wall-adjacent concentration history at exact chemistry knots.
- `caller_wet_co2_wall_saturation_scale_kinetics_result`: Caller-provided digest-bound saturation and scale-kinetics result at aligned cylindrical geometry knots.
- `caller_cylindrical_phase_solution_diffusivity_records`: Caller-supplied per-phase and solution-film diffusivity values with evidence and exact species mapping.
- `cylindrical_multilayer_radial_diffusion_resistance`: Independent sum of exact logarithmic radial Fick resistances across caller annular layers and solution film.
- `independent_cylindrical_annular_scale_inventory_volume_closure`: Map exact-knot caller-selected solid line inventory through its evidence-bound molar volume into the cylindrical annular volume used by radial transport and steel-recession geometry.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.wet_co2_cylindrical_scale_recession_feedback"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/wet_co2_cylindrical_scale_recession_feedback.py#L349)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

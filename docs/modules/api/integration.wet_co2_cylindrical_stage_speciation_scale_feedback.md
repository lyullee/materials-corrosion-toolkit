# `integration.wet_co2_cylindrical_stage_speciation_scale_feedback`

**목적:** Caller supplies a complete finite aqueous mass-action network, activity and equilibrium provider lineage, reaction formulae, natural-log Ksp and kinetic parameters with bound Evidence.

**모델 버전:** `1.0.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"default": "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v2", "enum": ["matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v1", "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v2", "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v3", "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v4", "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v5"], "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"maxLength": 160, "minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `spatial_request` | 예 | `{"$ref": "#/$defs/WetCo2CylindricalSpatialMixedPotential"}` | 계약·필드 설명 참조 |
| `mass_action_system_template` | 예 | `{"$ref": "#/$defs/AqueousMassActionSystem"}` | 계약·필드 설명 참조 |
| `davies_activity` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/WetCo2StageDaviesActivity"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `sit_activity` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/AqueousSITIteration"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `bdot_activity` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/AqueousBdotIteration"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `shear_removal` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/WetCo2StageShearRemoval"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `phases` | 예 | `{"items": {"$ref": "#/$defs/WetCo2StageSpeciationKineticPhase"}, "maxItems": 32, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
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

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/WetCo2CylindricalStageSpeciationScaleFeedback.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_s[]` | `s` |
| `geometry_history[].bore_radius_m` | `m` |
| `geometry_history[].steel_inner_radius_m` | `m` |
| `history[].phase_inventory_mol_m_by_phase.*` | `mol/m` |
| `interval_ledger[].detached_solid_inventory_export_mol_m_by_phase.*` | `mol/m` |
| `interval_ledger[].detached_solid_element_export_mol_m_by_element.*` | `mol/m` |
| `interval_ledger[].wall_shear_stress_Pa` | `Pa` |
| `interval_ledger[].requested_shear_detachment_flux_mol_m2_s_by_phase.*` | `mol/m^2/s` |
| `interval_ledger[].time_averaged_scale_flux_mol_m2_s_by_phase.*` | `mol/m^2/s` |
| `interval_ledger[].aqueous_inventory_residual_mol_m_by_species.*` | `mol/m` |
| `interval_ledger[].last_stage_activity_diagnostics.ionic_strength_mol_kg` | `mol/kg` |
| `interval_ledger[].last_stage_activity_diagnostics.maximum_log_gamma_fixed_point_residual` | `1` |
| `interval_ledger[].first_stage_activity_diagnostics.concentrations_mol_L_by_species.*` | `mol/L` |
| `interval_ledger[].last_stage_activity_diagnostics.concentrations_mol_L_by_species.*` | `mol/L` |
| `interval_ledger[].first_stage_activity_diagnostics.activity_coefficients_by_species.*` | `1` |
| `interval_ledger[].last_stage_activity_diagnostics.activity_coefficients_by_species.*` | `1` |
| `shear_removal.shear_history[].time_s` | `s` |
| `shear_removal.shear_history[].wall_shear_stress_Pa` | `Pa` |
| `shear_removal.phase_laws[].critical_shear_stress_Pa` | `Pa` |
| `shear_removal.phase_laws[].detachment_velocity_scale_m_s` | `m/s` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- Caller supplies a complete finite aqueous mass-action network, activity and equilibrium provider lineage, reaction formulae, natural-log Ksp and kinetic parameters with bound Evidence.
- Optionally, a caller-supplied, evidence-bound Davies A parameter and water-mass conversion are iterated self-consistently with each BDF-stage wall-composition mass-action solve; Davies support and single-liquid limits are enforced.
- Alternatively, a caller-supplied, evidence-bound SIT parameter/interaction set can be iterated at each BDF stage; its embedded aqueous template must exactly match the fixed stage-speciation template and only one optional activity model may be selected.
- Schema v4 or v5 enables caller-supplied, evidence-bound B-dot parameters at each BDF stage; the embedded aqueous template must exactly match, and activity modes are mutually exclusive.
- Schema v5 optionally applies exact-knot caller shear and per-phase evidence-bound threshold detachment within the BDF phase-inventory state; detached solid is recorded as an element export, not returned to the aqueous solution.
- Mass-action component constraints are rebuilt from stage wall concentrations and solved in log-activity coordinates at every BDF evaluation.
- The caller power law uses the current stage activities; radial supply, phase inventory and common geometry are bounded and updated in the coupled calculation.

## 구현 근거·독립 설명

- `caller_mass_action_activities_for_stage_scale_kinetics`: Uses the caller's fixed, evidence-bound aqueous reaction network and standard states to provide activities to the selected scale kinetic law.
- `multireactant_cylindrical_supply_and_inventory_limiter_at_bdf_stages`: Shared cylindrical reactant-supply and live-solid-inventory limiter reevaluated at each BDF stage.
- `aqueous_mass_action_recomputed_from_stage_wall_composition`: Rebuilds caller linear component totals from each BDF-stage wall-cell molar composition and re-solves the declared log-activity mass-action system; no species or reaction topology is inferred.
- `caller_general_aqueous_mass_action_speciation`: Solve a caller-defined square single-phase aqueous network in natural-log dimensionless activities. Use caller-supplied fixed activity coefficients and temperature-matched log10 equilibrium constants; solve caller-provided linear species amount and/or charge constraints after normalization by declared positive scales. A damped Newton method with finite-range checks and line search returns species activities, concentrations, balance closure, reaction residuals and full input/provider digests only within the declared tolerance. At a computed root, solve the converged Jacobian for implicit local derivatives of log activities and concentrations with respect to each log10(K), constraint target and fixed ln(gamma), without finite differencing. If explicitly reviewed, propagate a finite symmetric positive-semidefinite caller parameter covariance through those derivatives using first-order JΣJᵀ; condition and finite checks can make sensitivities unavailable while preserving the equilibrium result. No automatic electroneutrality, ionic-strength iteration, water balance, gas/solid phase, precipitation, kinetics, corrosion, or acceptance is inferred.
- [USGS PHREEQC 3 documentation: Davies activity-coefficient model](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-50.htm) · `usgs_phreeqc_davies_activity_coefficients`
- [USGS WSP 2254: Davies approximation for aqueous activity coefficients](https://pubs.usgs.gov/wsp/wsp2254/pdf/wsp2254a.pdf) · `usgs_davies_ionic_strength_approximation`
- `molality_to_molarity_activity_standard_state_bridge`: Map a molality-standard-state coefficient to a molarity-standard-state coefficient by equating the same dimensionless activity: gamma_c*c/(1 mol/L) = gamma_m*m/(1 mol/kg-water), with m=c/w and caller-supplied w in kg-water/L-solution, giving gamma_c=gamma_m/w. Require review of the water-mass conversion and standard-state mapping, preserve both coefficients, and fail closed outside finite numeric range. This algebraic basis does not infer solution water content or validate an activity model.
- [OECD Nuclear Energy Agency Thermochemical Database Project: SIT method](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/tdb2_2020-09-02_11-51-54_735.pdf) · `nea_thermochemical_database_sit_method`
- [USGS PHREEQC 3 documentation: SIT aqueous model data block](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-46.htm) · `usgs_phreeqc_sit_model_documentation`
- [USGS PHREEQC 3 documentation: LLNL extended Debye-Huckel B-dot activity model](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-26.htm) · `usgs_phreeqc_llnl_bdot_activity`
- `caller_wall_shear_history`: Caller supplies licensed, digest-pinned wall-shear stress values at exact cylindrical geometry time knots.
- `caller_calibrated_shear_scale_detachment_law`: Caller supplies a digest-pinned threshold power law for scale detachment velocity; the implementation does not infer adhesion or detachment parameters.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.wet_co2_cylindrical_stage_speciation_scale_feedback"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/wet_co2_cylindrical_stage_speciation_scale_feedback.py#L787)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

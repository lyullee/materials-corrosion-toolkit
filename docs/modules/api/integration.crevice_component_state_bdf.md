# `integration.crevice_component_state_bdf`

**목적:** BDF state variables are component moles, and each aqueous reaction conserves every transported component map.

**모델 버전:** `1.7.0` · **구현 분류:** `user_model` · **배포 버전:** `0.1.0a1`

[README로 돌아가기](../../../README.md) · [전체 모듈 목록](../../MODULE_DIRECTORY_KO.md)

## 입력 파라미터

각 행은 최상위 입력 필드다. 객체·배열 안의 필수 필드, enum, 상호 의존 조건은 아래 전체 JSON Schema와 구현 검사를 함께 적용한다. 일반 숫자를 문자열로 자동 보정하지 않는다.

| 이름 | 필수 | 타입·허용값·기본값 | 단위 또는 의미 |
|---|---|---|---|
| `schema_version` | 아니오 | `{"default": "matintegrity.crevice_component_state_bdf.v1", "enum": ["matintegrity.crevice_component_state_bdf.v1", "matintegrity.crevice_component_state_bdf.v2", "matintegrity.crevice_component_state_bdf.v3", "matintegrity.crevice_component_state_bdf.v4", "matintegrity.crevice_component_state_bdf.v5", "matintegrity.crevice_component_state_bdf.v6", "matintegrity.crevice_component_state_bdf.v7"], "type": "string"}` | 계약·필드 설명 참조 |
| `assessment_id` | 예 | `{"minLength": 1, "type": "string"}` | 계약·필드 설명 참조 |
| `time_s` | 예 | `{"items": {"type": "number"}, "maxItems": 500, "minItems": 2, "type": "array"}` | s |
| `cells` | 예 | `{"items": {"$ref": "#/$defs/CellAqueousEquilibriumTemplate"}, "maxItems": 300, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `initial_component_inventory` | 예 | `{"items": {"$ref": "#/$defs/ComponentInventoryByCell"}, "maxItems": 100, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `solid_equilibrium_mode` | 아니오 | `{"default": "aqueous_only", "enum": ["aqueous_only", "instantaneous_solid_equilibrium"], "type": "string"}` | 계약·필드 설명 참조 |
| `solid_phase_sets_by_cell` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/CellSolidPhaseSet"}, "maxItems": 300, "type": "array"}` | 계약·필드 설명 참조 |
| `kinetic_phase_sets_by_cell` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/CreviceBDFKineticPhaseSet"}, "maxItems": 300, "type": "array"}` | 계약·필드 설명 참조 |
| `kinetic_phase_mode_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `kinetic_rate_evaluation_budget` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_phase_event_count` | 아니오 | `{"default": 100000, "maximum": 2000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `absolute_solid_inventory_tolerance_mol` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `solid_phase_set_clock_id` | 아니오 | `{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `total_component_inventory_includes_solid_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `instantaneous_equilibrium_no_nucleation_barrier_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `solid_phase_set_applicability_and_completeness_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `moving_geometry_mode` | 아니오 | `{"default": "fixed_volume", "enum": ["fixed_volume", "instantaneous_solid_aperture_feedback"], "type": "string"}` | 계약·필드 설명 참조 |
| `dynamic_solid_geometry_by_cell` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/CellDynamicSolidGeometry"}, "maxItems": 300, "type": "array"}` | 계약·필드 설명 참조 |
| `moving_geometry_stage_feedback_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `dynamic_geometry_relative_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `dynamic_geometry_relaxation_factor` | 아니오 | `{"default": 0.5, "exclusiveMinimum": 0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_dynamic_geometry_iterations_per_cell_stage` | 아니오 | `{"default": 30, "maximum": 500, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_dynamic_geometry_iterations` | 아니오 | `{"default": 1000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `electrochemical_sources` | 아니오 | `{"default": [], "items": {"$ref": "#/$defs/ElectrochemicalSourceExtentSchedule"}, "maxItems": 100, "type": "array"}` | 계약·필드 설명 참조 |
| `ionic_face_current_schedule` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/IonicFaceCurrentSchedule"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `capacitive_current_schedule` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/CapacitiveCellCurrentSchedule"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `hydraulic_component_advection` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/CreviceHydraulicComponentAdvection"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `dynamic_hydraulic_component_advection` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/CreviceDynamicHydraulicAdvection"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `faradaic_stage_coupling` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/CreviceFaradaicSpatialChemistryRequest"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `dynamic_double_layer` | 아니오 | `{"anyOf": [{"$ref": "#/$defs/CreviceBDFDoubleLayerCapacitance"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `interior_face_area_m2` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 299, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `center_distance_m_by_interior_face` | 예 | `{"items": {"exclusiveMinimum": 0, "type": "number"}, "maxItems": 299, "minItems": 1, "type": "array"}` | 계약·필드 설명 참조 |
| `species_face_diffusivity` | 예 | `{"items": {"$ref": "#/$defs/SpeciesFaceDiffusivity"}, "maxItems": 100, "minItems": 2, "type": "array"}` | 계약·필드 설명 참조 |
| `relative_tolerance` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_component_inventory_tolerance_mol` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_component_closure_tolerance_mol` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `relative_component_closure_tolerance` | 아니오 | `{"default": 1e-07, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `solid_equilibrium_log_saturation_tolerance` | 아니오 | `{"default": 1e-08, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_face_current_closure_tolerance_A` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `relative_face_current_closure_tolerance` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "maximum": 0.001, "type": "number"}` | 계약·필드 설명 참조 |
| `absolute_double_layer_charge_tolerance_C` | 아니오 | `{"default": 1e-10, "exclusiveMinimum": 0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_absolute_source_extent_rate_mol_s` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `maximum_step_s` | 아니오 | `{"default": 1000000.0, "exclusiveMinimum": 0, "maximum": 1000000000000.0, "type": "number"}` | s |
| `maximum_total_rhs_evaluations` | 아니오 | `{"default": 100000, "maximum": 2000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_stage_equilibrium_calls` | 아니오 | `{"default": 1000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_nested_equilibrium_iteration_work` | 아니오 | `{"default": 20000000, "maximum": 2000000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_solid_partition_evaluations` | 아니오 | `{"default": 1000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_solid_active_set_sweeps` | 아니오 | `{"default": 2000000, "maximum": 200000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_solid_bisection_iterations` | 아니오 | `{"default": 20000000, "maximum": 2000000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_source_projection_operations` | 아니오 | `{"default": 2000000, "maximum": 200000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_ionic_current_face_evaluations` | 아니오 | `{"default": 2000000, "maximum": 200000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_total_stage_mixed_potential_function_evaluations` | 아니오 | `{"default": 2000000, "maximum": 20000000, "minimum": 100, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_absolute_stage_faradaic_extent_rate_mol_s` | 아니오 | `{"anyOf": [{"exclusiveMinimum": 0, "type": "number"}, {"type": "null"}], "default": null}` | 계약·필드 설명 참조 |
| `maximum_output_species_values` | 아니오 | `{"default": 1000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `maximum_output_solid_phase_values` | 아니오 | `{"default": 1000000, "maximum": 20000000, "minimum": 1, "type": "integer"}` | 계약·필드 설명 참조 |
| `component_state_and_flux_basis_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `cell_equilibrium_templates_and_evidence_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `fixed_volume_and_boundary_scope_reviewed` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |
| `electrochemical_source_stoichiometry_and_reservoir_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `ionic_face_current_schedule_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `capacitive_current_schedule_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `hydraulic_component_advection_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `dynamic_hydraulic_component_advection_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `dynamic_volume_and_boundary_scope_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `dynamic_hydraulic_fixed_point_relative_tolerance` | 아니오 | `{"default": 1e-05, "exclusiveMinimum": 0, "maximum": 0.01, "type": "number"}` | 계약·필드 설명 참조 |
| `dynamic_hydraulic_fixed_point_relaxation` | 아니오 | `{"default": 0.5, "exclusiveMinimum": 0, "maximum": 1.0, "type": "number"}` | 계약·필드 설명 참조 |
| `maximum_dynamic_hydraulic_fixed_point_iterations` | 아니오 | `{"default": 8, "maximum": 100, "minimum": 2, "type": "integer"}` | 계약·필드 설명 참조 |
| `absolute_flow_tolerance_m3_s` | 아니오 | `{"default": 1e-12, "exclusiveMinimum": 0, "type": "number"}` | m³/s |
| `component_state_faradaic_stage_coupling_reviewed` | 아니오 | `{"default": false, "type": "boolean"}` | 계약·필드 설명 참조 |
| `computational_use_authorized` | 예 | `{"type": "boolean"}` | 계약·필드 설명 참조 |

[중첩 정의까지 포함한 전체 입력 스키마](../../schemas/CreviceComponentStateBDFRequest.json)

## 출력 파라미터

공통 반환 형식은 `AssessmentResult`다. 계산 값은 `values`, 단위는 `units`에 들어간다. 아래는 registry가 선언한 출력량이며, 조건부 분기의 모든 내부 키를 정형화한 출력 스키마는 아니다. `needs_data`·`out_of_scope`에서는 값이 비거나 진단만 반환될 수 있다.

| `values` 내 선언 경로 | 단위 |
|---|---|
| `time_s[]` | `s` |
| `cells[].solution_volume_L` | `L` |
| `initial_component_inventory[].inventory_mol_by_cell[]` | `mol` |
| `electrochemical_sources[].extent_rate_mol_s_by_knot_and_cell[][]` | `mol/s` |
| `electrochemical_source_ledgers[].extent_mol_by_cell[]` | `mol` |
| `ionic_face_current_schedule_A_by_knot_and_face[][]` | `A` |
| `capacitive_current_schedule.current_A_by_knot_and_cell[][]` | `A` |
| `hydraulic_component_advection.left_boundary_species_concentration_mol_m3_by_knot[][]` | `mol/m^3` |
| `hydraulic_component_advection.right_boundary_species_concentration_mol_m3_by_knot[][]` | `mol/m^3` |
| `dynamic_hydraulic_component_advection.signed_pressure_drop_Pa_by_knot[]` | `Pa` |
| `dynamic_hydraulic_component_advection.left_boundary_species_concentration_mol_m3_by_knot[][]` | `mol/m^3` |
| `dynamic_hydraulic_component_advection.right_boundary_species_concentration_mol_m3_by_knot[][]` | `mol/m^3` |
| `dynamic_hydraulic_component_advection.transverse_width_m` | `m` |
| `dynamic_hydraulic_component_advection.density_kg_m3` | `kg/m^3` |
| `dynamic_hydraulic_component_advection.dynamic_viscosity_Pa_s` | `Pa*s` |
| `dynamic_hydraulic_component_advection.maximum_abs_flow_m3_s` | `m^3/s` |
| `dynamic_hydraulic_component_advection.initial_signed_volumetric_flow_m3_s` | `m^3/s` |
| `dynamic_hydraulic_fixed_point_relative_tolerance` | `1` |
| `dynamic_hydraulic_fixed_point_relaxation` | `1` |
| `absolute_flow_tolerance_m3_s` | `m^3/s` |
| `dynamic_inlet_flow_m3_s_by_time[]` | `m^3/s` |
| `dynamic_hydraulic_fixed_point_work.maximum_normalized_volume_rate_residual` | `1` |
| `dynamic_hydraulic_fixed_point_work.relative_tolerance` | `1` |
| `dynamic_hydraulic_iterations` | `1` |
| `maximum_dynamic_hydraulic_fixed_point_residual` | `1` |
| `dynamic_hydraulic_fixed_point_iteration_budget` | `1` |
| `hydraulic_boundary_exchange_component_change_mol_by_side_and_time[][]` | `mol` |
| `hydraulic_boundary_exchange_element_change_mol_by_side_and_time[][]` | `mol` |
| `hydraulic_boundary_exchange_charge_change_mol_eq_by_side_and_time[][]` | `mol_eq` |
| `integrated_capacitive_charge_C_by_cell_and_time[][]` | `C` |
| `dynamic_double_layer.initial_interfacial_potential_V_by_cell[]` | `V` |
| `dynamic_double_layer.reference_interfacial_potential_V_by_cell[]` | `V` |
| `dynamic_double_layer.differential_capacitance_potential_axis_V[]` | `V` |
| `dynamic_double_layer.differential_capacitance_F_m2[]` | `F/m^2` |
| `absolute_double_layer_charge_tolerance_C` | `C` |
| `dynamic_double_layer_charge_C_by_cell_and_time[][]` | `C` |
| `dynamic_double_layer_interfacial_potential_V_by_time_and_cell[][]` | `V` |
| `dynamic_double_layer_solution_potential_V_by_time_and_cell_relative_to_metal_gauge[][]` | `V` |
| `exact_knot_ionic_face_current_A_by_boundary[][]` | `A` |
| `exact_knot_branch_current_density_A_m2_by_branch_and_cell.*[][]` | `A/m^2` |
| `exact_knot_current_time_s[]` | `s` |
| `stage_mixed_potential_function_evaluations` | `1` |
| `integrated_ionic_charge_C_by_face_and_time[][]` | `C` |
| `electrochemical_source_ledgers[].external_reservoir_element_change_mol.*[]` | `mol` |
| `electrochemical_source_ledgers[].external_reservoir_component_change_mol_by_cell.*[]` | `mol` |
| `electrochemical_source_ledgers[].external_reservoir_charge_change_mol_eq` | `mol_eq` |
| `aqueous_component_inventory_mol_by_component_time_cell.*[][]` | `mol` |
| `solid_component_inventory_mol_by_component_time_cell.*[][]` | `mol` |
| `solid_phase_inventory_mol_by_cell_phase_time.*.*[]` | `mol` |
| `kinetic_phase_sets_by_cell[].initial_solid_moles_by_phase.*` | `mol` |
| `kinetic_phase_rate_evaluations` | `1` |
| `maximum_absolute_kinetic_phase_rate_mol_s` | `mol/s` |
| `kinetic_event_policy.event_count` | `1` |
| `element_ledgers[].total_inventory_mol_by_time_and_cell[][]` | `mol` |
| `element_ledgers[].integrated_face_transfer_mol_by_time_and_face[][]` | `mol` |
| `element_ledgers[].integrated_aqueous_source_change_mol_by_cell[]` | `mol` |
| `element_ledgers[].integrated_external_reservoir_change_mol_by_cell[]` | `mol` |
| `solid_partition_evaluations` | `1` |
| `solid_active_set_sweeps` | `1` |
| `solid_bisection_iterations` | `1` |
| `dynamic_geometry_iterations` | `1` |
| `maximum_dynamic_geometry_relative_volume_residual` | `1` |
| `dynamic_geometry_relative_tolerance` | `1` |
| `dynamic_geometry_iteration_budget` | `1` |
| `dynamic_solid_geometry_by_cell[].cell_length_m` | `m` |
| `dynamic_solid_geometry_by_cell[].transverse_width_m` | `m` |
| `dynamic_solid_geometry_by_cell[].initial_aperture_m` | `m` |
| `dynamic_solid_geometry_by_cell[].minimum_aperture_m` | `m` |
| `dynamic_solid_geometry_by_cell[].phase_geometry[].molar_volume_m3_mol` | `m^3/mol` |
| `exact_knot_dynamic_geometry_by_cell[][].solution_volume_L` | `L` |
| `exact_knot_dynamic_geometry_by_cell[][].aperture_m` | `m` |
| `exact_knot_dynamic_geometry_by_cell[][].cross_section_area_m2` | `m^2` |
| `exact_knot_dynamic_geometry_by_cell[][].normalized_fixed_point_residual` | `1` |
| `reserved_nested_equilibrium_iteration_work_bound` | `1` |
| `maximum_normalized_component_closure_residual` | `1` |
| `maximum_normalized_hydraulic_boundary_closure_residual` | `1` |
| `interior_face_area_m2[]` | `m^2` |
| `center_distance_m_by_interior_face[]` | `m` |
| `species_face_diffusivity[].diffusivity_m2_s_by_interior_face[]` | `m^2/s` |
| `component_ledgers[].inventory_mol_by_time_and_cell[][]` | `mol` |
| `component_ledgers[].integrated_face_transfer_mol_by_time_and_face[][]` | `mol` |
| `species_concentration_mol_m3_by_species_time_cell.*[][]` | `mol/m^3` |
| `activity_coefficient_by_species_time_cell.*[][]` | `1` |
| `maximum_face_current_residual_A` | `A` |
| `maximum_face_current_scale_A` | `A` |
| `ionic_current_face_evaluations` | `1` |
| `source_projection_operations` | `1` |

공통 메타데이터: `model_id`, `model_version`, `status`, `inputs`, `values`, `units`, `assumptions`, `notes`, `context`, `input_digest`, `source_ids`, `qualification`, `runtime`, `probability_semantics`.

## 모델 가정·주의 사항

- BDF state variables are component moles, and each aqueous reaction conserves every transported component map.
- Each trial state is projected to local caller-evidenced single-liquid Davies/mass-action equilibrium before the RHS is formed; volume is fixed by default, while the opt-in solid-occupancy geometry mode iterates equilibrium at the derived trial volume.
- Interior species Nernst-Planck diffusion uses caller-supplied face diffusivity/geometry; a per-face algebraic migration field enforces the requested ionic current.
- Optional fixed-geometry hydraulic advection uses digest-bound transient slit flow and electroneutral reservoir compositions with upwind stage concentrations.
- Optional moving-geometry hydraulic transport uses an explicit signed pressure and electroneutral boundary-composition schedule, trial solid-equilibrium aperture, directional finite-difference liquid-volume rate, slit momentum, upwind component flux and integrated reservoir ledgers in a damped fixed point. It has not been physically verified; Faradaic area coupling is rejected.
- The default aqueous-only mode excludes solid transfer; the opt-in total-component solid-equilibrium mode is separate. Caller source schedules and reviewed spatial Ohmic/Butler-Volmer stage coupling remain mutually exclusive.
- The stage electrochemical path rejects conflicting caller extent/current schedules, enforces a caller branch-rate bound and a total stage-work budget, and records branch/evidence digests and knot lineage.
- Schema v7 optionally appends per-cell integrated double-layer charge to the BDF state. At every trial, the caller Cdl curve is inverted without extrapolation, trial chemistry refreshes Nernst equilibrium potentials and conductivity, spatial Ohmic face current is reconstructed, and branch Faradaic current plus charge continuity provide same-stage chemical source and charge derivatives. This mode requires fixed geometry and insulated ionic boundaries; moving hydraulic coupling and external circuit forcing are not represented.
- Opt-in dynamic geometry is restricted to aqueous plus instantaneous-solid equilibrium. At each BDF RHS and exact output knot, a damped fixed-point iteration maps caller-mapped gap-occupying solid moles through caller-reviewed molar volumes to aperture and solution volume, repeats equilibrium at that volume, and uses the resulting interpolated cell cross-section for NP face conductance. This is a bounded operator-split stage solve, not a monolithic coupled geometry/chemistry Newton solve; deposition mechanics, porosity, particle packing, fracture, and unlisted phases are outside scope.
- Dynamic geometry fails closed when the aperture reaches its caller minimum, the relative volume fixed-point residual exceeds tolerance, or the per-cell-stage or aggregate geometry iteration budget is exhausted. Fixed-volume v1-v3 behavior and the default mode are retained.
- Opt-in solid equilibrium mode treats the BDF conserved-component state as liquid-plus-candidate-solid total inventory and invokes a digest-bound, cell-specific instantaneous phase partition at every trial before NP/Faradaic flux evaluation; aqueous-only mode remains the default.
- Opt-in kinetic phase mode evolves total component inventory together with explicit per-phase solid moles. Every trial is equilibrated against the derived dissolved inventory, evaluates dimensionless ion activities and saturation ratios, then applies caller-pinned nucleation/growth laws in the same BDF stage; seed and depletion crossings restart at accepted event boundaries. Kinetic moving geometry maps explicit solid moles to gap occupancy. This user model is not independently verified or qualified.
- Solid mode requires the component basis to reconstruct every declared element, closes cellwise total-component and element balances plus external reservoir and current/charge ledgers, and aggregates partition, active-set, bisection and nested-equilibrium work across RHS and knot snapshots.
- Solid phase candidate identities and thermochemical records are stationary across the exact request clock/horizon and caller reviewed. Candidate amounts may change through instantaneous equilibrium and, in the opt-in geometry mode, change aperture and liquid volume. Phase kinetics, nucleation, global Gibbs minimization, discovery of unlisted phases and qualification are not calculated.
- Optional fixed-geometry hydraulic advection applies the exact interval inertance flow with signed upwind stage species concentrations and explicit neutral left/right reservoir states; its boundary component/element/charge amounts are separately integrated into the ODE ledger.
- Optional capacitive current is supplied as an exact-knot per-cell schedule, enters charge continuity with the declared sign convention, and is linearly interpolated with the matching ionic face-current schedule. It is forcing-only and cannot be interpreted as a solved potential/charge state or a Cdl constitutive relation.
- Capacitive-current schedules are forcing-only; schema-v7 same-stage dynamic double-layer owns its capacitive charge and ionic current and rejects caller capacitive/ionic schedules.

## 구현 근거·독립 설명

- `finite_volume_conserved_component_inventory_bdf_state`: Integrate per-cell conserved aqueous component moles as the BDF state on a fixed-volume mesh with closed external boundaries; species concentrations are equilibrium reconstructions and reaction-invariant component maps provide the transported inventory basis.
- `caller_evidenced_cellwise_davies_mass_action_at_bdf_stages`: At every BDF trial stage, derive cellwise analytical component targets from the trial conserved inventories and solve the caller-evidenced Davies mass-action equilibrium; enforce explicit single-liquid, fixed-volume and bounded nested-work assumptions.
- `electroneutral_nernst_planck_species_flux_projected_to_components`: Calculate species diffusion and activity-gradient fluxes on interior faces using caller diffusivities, solve an algebraic migration field for zero ionic current, and project species fluxes through reaction-conserved component maps into the finite-volume BDF state.
- `caller_evidenced_component_source_extent_schedule`: Apply caller-supplied, digest-bound per-cell reaction-extent-rate schedules at exact knots with piecewise-linear interpolation, project aqueous stoichiometry into conserved-component BDF states, and separately account for external reservoir component, element and charge changes. Charged extent schedules require the paired prescribed-current schedule and knotwise continuity; source rates are not derived from Butler-Volmer or mixed-potential kinetics.
- `caller_evidenced_ionic_face_current_schedule`: Use review-gated caller-supplied exact-knot ionic currents on all faces, zero external boundary currents, and matching source-schedule times. Check each cell charge balance against Faraday-scaled reaction extents, solve the Nernst-Planck migration gradient to reproduce the requested interior current, and report ampere residuals and integrated charge; currents are not inferred from mixed-potential or Butler-Volmer kinetics.
- `caller_evidenced_double_layer_capacitive_current_schedule`: Apply a caller-provided exact-knot, per-cell capacitive-current history to the component-state BDF charge-continuity ledger. Bind the complete schedule digest and licensed Evidence, require exact clock and cell ordering plus review, interpolate within intervals, and integrate signed charge on the same BDF state. This is prescribed-current forcing; it does not solve electrode potential, derive capacitance, or couple to the stage mixed-potential kernel.
- `component_state_bdf_stage_spatial_ohmic_butler_volmer_faradaic_coupling`: At each conserved-component BDF trial, reconstruct caller-evidenced aqueous Davies/mass-action equilibrium, re-solve the existing spatial quasi-steady ohmic/Butler-Volmer mixed-potential branches from that trial chemistry, and project the branch extents plus matching electrolyte face current into the same RHS. Require exact chemistry/species/cell/clock alignment, fixed cell and face areas, consistent cell volumes/face areas/center distances, a reviewed branch map and caller extent-rate and solver-work bounds. This bounded mode has no moving-boundary dynamics, double-layer storage, automatic chemistry/phase discovery or material qualification.
- `component_state_bdf_stage_total_component_solid_equilibrium_partition`: Opt-in conserved-component BDF mode treats each cell state as total aqueous-plus-solid component inventory and invokes the bounded solid-partition solver at every trial stage; Nernst-Planck and Faradaic terms use reconstructed aqueous species while knot outputs retain liquid/solid inventories and component/element/charge ledgers. Exact caller phase sets and solver-work budgets are required. This mode excludes kinetic nucleation/precipitation, automatic phase discovery, moving-boundary dynamics, a global Gibbs-minimum claim and qualification.
- `caller_evidenced_solid_molar_volume_gap_occupancy_fixed_point_geometry`: Map caller-evidenced solid inventories to occupied gap volume with phase molar volumes, then update cell aperture, liquid volume and transport face area through a bounded damped stage fixed point. Geometry and occupancy are caller inputs; no mechanics, packing, porosity or kinetic phase evolution is inferred.
- `bound_crevice_current_carrying_result_to_component_state_schedules`: Bind a fully committed, digest-matched exact-knot CREVICE current-carrying result into a conserved-component BDF request. Preserve cell order, match initial component inventories, convert caller branch current densities to signed per-cell extent-rate schedules using the declared electron number and reactive area, carry ionic face currents, and require review of the sequential reconstruction. Reject stage-re-solved mixed-potential results because endpoint knots cannot reproduce their within-stage current history.
- `caller_general_aqueous_mass_action_speciation`: Solve a caller-defined square single-phase aqueous network in natural-log dimensionless activities. Use caller-supplied fixed activity coefficients and temperature-matched log10 equilibrium constants; solve caller-provided linear species amount and/or charge constraints after normalization by declared positive scales. A damped Newton method with finite-range checks and line search returns species activities, concentrations, balance closure, reaction residuals and full input/provider digests only within the declared tolerance. At a computed root, solve the converged Jacobian for implicit local derivatives of log activities and concentrations with respect to each log10(K), constraint target and fixed ln(gamma), without finite differencing. If explicitly reviewed, propagate a finite symmetric positive-semidefinite caller parameter covariance through those derivatives using first-order JΣJᵀ; condition and finite checks can make sensitivities unavailable while preserving the equilibrium result. No automatic electroneutrality, ionic-strength iteration, water balance, gas/solid phase, precipitation, kinetics, corrosion, or acceptance is inferred.
- `nist_codata_faraday_constant_2022`: CODATA Faraday constant used as an exact conversion constant; no source data table or prose is reproduced.
- `caller_lumped_slit_inertance_resistance`: Evaluate the caller-reviewed reduced planar-slit momentum law with the declared resistance and inertance correction factors; factors default to unity and non-unity values require exact fit-result Evidence and an applicability review.
- `caller_digest_bound_planar_slit_inertance_upwind_component_advection`: Bind a committed exact-clock planar-slit inertance history and Evidence-pinned electroneutral inlet/outlet compositions to a fixed-volume component-state BDF mesh. At every BDF RHS state, evaluate signed inertance flow, select upwind aqueous stage concentrations, project species advection to conserved components, and integrate separate left/right component, elemental and charge reservoir exchanges. Requires fixed aperture and caller-reviewed geometry; it does not solve moving boundaries or general momentum flow.
- `caller_reviewed_dynamic_slit_pressure_and_boundary_composition_schedule`: Bind a reviewed, digest-fixed pressure-drop and electroneutral reservoir-composition history to a moving-volume slit-transport calculation. The reduced Newtonian laminar slit model uses caller-declared fluid properties, correction factors and support limits; directional volume-rate estimation and physical validation remain explicit limitations.
- `caller_evidenced_dynamic_double_layer_and_faradaic_polarization_curves`: Integrate independent lumped electrode-cell potentials from an exact-knot total-current history, caller-supplied signed polarization tables and a differential-capacitance curve using I_total = I_F + dQ/dt. Interpolate only within declared supports, preserve Evidence digests and fail closed on solver/support/work limits. This does not solve electrolyte ohmic coupling, ionic transport, active-area evolution, or procedure qualification.
- `caller_evidenced_initial_crevice_double_layer_interfacial_state`: Pin the ordered cell identities, initial and reference interfacial potentials, and the exact differential-capacitance curve digest used to derive initial stored charge. The record is caller-supplied state evidence; it is not inferred from an independently solved voltage history.
- `same_stage_component_bdf_dynamic_double_layer_spatial_ohmic_faradaic_feedback`: Append one integrated double-layer charge state per fixed-geometry cell to the component BDF. At each trial, invert the caller differential-capacitance charge relation, refresh Nernst potentials and electrolyte conductivity from trial chemistry, reconstruct spatial ohmic face current, evaluate local Butler-Volmer branches, and project Faradaic extents plus charge continuity into the same RHS. The present scope has insulated ionic ends and excludes moving hydraulic boundaries and external circuit-current forcing.
- `same_stage_activity_based_competing_solid_kinetics_with_seed_depletion_events`: At each spatial component-BDF trial, reconstruct dissolved components from total component inventory and explicit per-phase solid moles, solve local activity-corrected aqueous chemistry, derive phase saturation and evaluate caller-pinned nucleation/growth laws. Integrate solid moles alongside transport/source/hydraulic ledgers and restart at located seed/depletion events. Kinetic parameter values, phase-set completeness, numerical verification and physical qualification remain caller/research responsibilities.

## 실행 방법

```python
import json
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext

registry = default_registry()
model_id = "integration.crevice_component_state_bdf"
# inputs.json을 위 계약과 실제 평가 조건에 맞게 작성한다.
payload = open("inputs.json", encoding="utf-8").read()
context = RunContext(asset_id="your-asset", location_id="your-location", time_basis="elapsed seconds")
result = registry.run_json(model_id, payload, context)
print(result.status)
print(result.values)
```

위 코드는 호출 구조다. `inputs.json`, context, provider의 실제 준비가 필요하며 그대로 실행되는 재료 추천 예제가 아니다.

주 JSON 예제 파일에는 이 API의 독립 예제가 없다. 연결 API는 선행 계산의 실제 `AssessmentResult`가 필요할 수 있고 데이터 API는 별도로 확보한 파일·권한이 필요하다. 단위·계약·증거를 임의로 채워 실행 성공을 만들지 않는다.

[계산 구현과 주석 확인](../../../src/matintegrity/crevice_component_state_bdf.py#L1015)

## 검증과 연구 재개

등록·스키마 제공은 모든 분기·실험·현장 적용성 검증 완료를 뜻하지 않는다. [검증 기록](../../CORE_EXECUTION_VERIFICATION_KO.md), [물리 검토](../../PHYSICAL_REVIEW_KO.md), [공개 전 검사](../../PREPUBLISH_CHECKS_KO.md)를 모델 ID와 대조한다.

해당 입력과 결과의 JSON·단위·설비/위치/시간 기준·재료 상태·provider revision·Evidence·해시를 함께 저장한다. 보정과 holdout 자료를 분리하고, 기능 수정 시 단순 비교값과 보존법칙을 먼저 재검사한다.

# Wet-CO₂ 원통형 BDF-stage 수용액 speciation과 scale 반응 피드백

## API

- Model ID: `integration.wet_co2_cylindrical_stage_speciation_scale_feedback`
- Schema: v1 fixed-activity legacy; v2 Davies (default); v3 SIT; v4 B-dot; v5 optional stage-coupled shear removal
- 요청: `WetCo2CylindricalStageSpeciationScaleFeedback`
- Caller aqueous network: `AqueousMassActionSystem`
- Caller 상 kinetic law: `WetCo2StageKineticPhase`
- Activity-product term: `WetCo2StageActivityProductTerm`
- Optional stage configurations: activity modes `WetCo2StageDaviesActivity`, `sit_activity: AqueousSITIteration`, `bdot_activity: AqueousBdotIteration`; schema v5 also requires `shear_removal: WetCo2StageShearRemoval`
- 계산 함수: `evaluate_wet_co2_cylindrical_stage_speciation_scale_feedback`
- provenance source IDs: `caller_mass_action_activities_for_stage_scale_kinetics`, `multireactant_cylindrical_supply_and_inventory_limiter_at_bdf_stages`, `aqueous_mass_action_recomputed_from_stage_wall_composition`; optional shear mode also cites `caller_wall_shear_history` and `caller_calibrated_shear_scale_detachment_law`. Davies mode additionally cites `usgs_phreeqc_davies_activity_coefficients`, `usgs_davies_ionic_strength_approximation`, `molality_to_molarity_activity_standard_state_bridge`; SIT mode cites `nea_thermochemical_database_sit_method` and `usgs_phreeqc_sit_model_documentation`; B-dot mode cites `usgs_phreeqc_llnl_bdot_activity` and the standard-state bridge

## 계산 흐름

이 모델은 이전 단계의 exact-knot 고정 activity schedule을 쓰지 않는다. BDF가 각 내부 stage에서 방사 유한체적의 wall-adjacent 농도 벡터를 전달하면, caller `AqueousMassActionSystem`의 반응식·선형 보존식·표준상태·평형상수는 유지하고 보존식 target만 해당 stage 수용액 조성으로 다시 계산한다. transport 농도 `mol/m³`를 mass-action의 `mol/L` 입력으로 바꾸고, 각 보존식의 caller 계수로 성분 총량 target을 구성한다. 기본 모드에서는 template 활동도계수를 그대로 사용하고 `aqueous_mass_action_speciation`을 호출한다. 선택형 `davies_activity`를 제공하면 기존 `aqueous_davies_self_consistent_speciation`을 stage마다 호출하여 caller의 온도별 Davies A와 물 질량 환산으로 이온강도–활동도계수를 반복 수렴시킨다. 그 결과에서 species별 무차원 활동도를 얻는다.

선택형 B-dot 경로는 `AqueousBdotIteration`의 caller 제공 온도별 계수, species parameter 및 Evidence를 사용해 각 stage에서 이온강도와 활동도 계수를 자기일관 반복 계산한다. 요청 schema v4에서만 켤 수 있다. 재평형 결과의 activities를 caller phase의 activity-product term에 적용한다. Caller natural-log `ln(Ksp)`, phase 반응 화학량론·고체 formula, precipitation/dissolution rate constants, 반응차수와 유한 flux cap은 Evidence 및 digest에 결속한다. `ln(Q/Ksp)>0`일 때 caller power law가 침전을, `ln(Q/Ksp)<0`일 때 reverse-direction power law가 용해를 산출한다. 해당 flux는 같은 BDF stage에서 BV species source/sink와 함께 aqueous finite-volume RHS에 추가된다.

각 stage의 precipitation은 모든 상이 공통으로 소비하는 각 reactant에 대해 cylindrical radial diffusion 공급량을 함께 계산해 제한한다. 용해 속도는 stage phase inventory 및 interval 잔여시간으로 제한한다. 제한된 RHS 평가 예산과 mass-action solver의 caller Newton iteration/line-search 상한을 결합해 질량작용 solve 호출 비용을 bounded work estimate로 제한한다. 각 exact knot 이후 phase inventory·BV wall release·반경을 annular geometry 식으로 갱신하고, bounded Picard 반복에서 geometry residual을 수렴시킨다.

## 선택형 BDF-stage 전단 제거 (schema v5)

기존 `integration.wet_co2_cylindrical_shear_limited_scale_removal`은 성장 ledger를 받은 뒤 적용하는 operator-split 후처리다. 여기서는 제거를 BDF phase-inventory 상태와 같은 RHS에 넣는다. `shear_removal.shear_history`는 BV/geometry knot과 정확히 같은 시간점의 wall shear 응력(Pa)을 제공하고, `phase_laws`는 각 scale phase에 대해 임계 응력, detachment velocity scale, stress exponent 및 그 전체 설정을 묶는 digest/Evidence를 제공한다. 활성 구간에서는

`v_det = v_scale × max(τ/τ_critical − 1, 0)^n`, `J_det = v_det / V_m`

을 사용하며, 각 구간 안에서 shear는 왼쪽 knot 값으로 고정한다. 물리 화학 성장·용해 flux와 shear detachment는 동일한 phase inventory derivative에 합산하지만, detachment 양은 남은 phase inventory와 같은 구간의 chemical dissolution을 고려해 제한한다. 분리된 고체는 aqueous species로 되돌리지 않는다. 별도의 BDF export state에 적분해 phase별 detached inventory와 고체 원소 export를 기록하고 element closure에 포함한다. 따라서 제거는 geometry/phase inventory feedback에 영향을 주면서 수용액 화학 질량수지와 분리물 export를 구분한다.

schema v5는 명시적 opt-in이다. 기존 v1–v4 및 v2 기본값은 그대로 두고, v5에서는 `shear_removal`이 필수다. 모든 transport knot의 shear record, 모든 kinetic phase와 정확히 일치하는 law 집합, knot left-hold·inner area·분리물 export·law 적용성 review flag가 필요하다. v5에서 Davies, SIT 또는 B-dot 중 하나의 활동도 모드를 함께 선택할 수 있으며 세 활동도 모드는 서로 배타적이다.

```python
payload = request.model_dump(mode="python")
payload["schema_version"] = "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v5"
payload["shear_removal"] = WetCo2StageShearRemoval(
    shear_history=caller_digest_bound_shear_knots,
    phase_laws=caller_digest_bound_phase_laws,
    exact_knot_left_hold_reviewed=True,
    detached_solid_export_and_inner_area_reviewed=True,
    phase_law_applicability_reviewed=True,
).model_dump(mode="python")
request = WetCo2CylindricalStageSpeciationScaleFeedback.model_validate(payload)
```

각 knot/law digest는 각각 시간·전단응력과 phase·임계응력·속도계수·지수를 canonical payload로 묶어 계산하고, 동일 digest를 포함한 license 선언 Evidence를 제공한다. BDF 상태와 inventory accounting이 달라지는 기능이므로 `model_copy(update=...)` 대신 `model_validate`로 v5 계약을 검증한다.

## 입력 경계와 lineage

- 모든 mass-action species ID, charge 및 정수 원소식은 BV transport species와 일치해야 한다.
- Mass-action constraint species는 모두 transported species여야 하며, stage component totals는 caller constraint coefficient를 그대로 사용한다.
- `molarity_1_mol_L` 표준상태만 지원하며 mass-action template temperature는 모든 BV reaction knot과 일치해야 한다. Interval의 first/last stage diagnostics에는 solver가 해당 값을 제공할 때 `concentrations_mol_L_by_species` (mol/L)와 `activity_coefficients_by_species` (무차원)를 함께 보존한다. 이는 해당 BDF stage의 계산 결과이며 knot 입력이나 새 평형 해석으로 대체하지 않는다.
- `davies_activity` 모드에서는 온도별 Davies A, provider/record digest, 물 질량 환산, 최대 이온강도(0.5 mol/kg 이하), 전하 잔차 한계, 감쇠·수렴 설정 및 Evidence가 추가로 필요하다. 입력 온도는 질량작용 네트워크 온도 지원과 caller 허용오차 내에서 일치해야 한다. 이 모드는 Davies 근사의 선언 범위에서만 활동도 계수를 계산한다.
- `bdot_activity`는 schema v4 또는 shear를 더한 v5에서 사용할 수 있다. 내장 `AqueousMassActionSystem`의 canonical digest가 최상위 template와 정확히 같아야 하며, parameter temperature는 mass-action temperature와 허용오차 내에서 일치해야 한다. 기존 B-dot 계약에 따라 물 질량 환산, Debye–Hückel A/B, ordered species ion-size parameters, provider/configuration/record digests, 최대 이온강도, 수렴·전하 설정, 완전한 Evidence와 review flags를 caller가 제공한다. stage diagnostics에는 activity model/provider, ionic strength, outer iterations, normalized solver residual 및 최대 log-gamma fixed-point residual을 기록한다. B-dot outer iteration 상한은 work estimate에 곱해진다.
- schema v5의 `shear_removal` 응력·계수는 caller가 공급하며, 각 `WetCo2StageShearKnot` 및 `WetCo2StageShearDetachmentLaw` digest는 license가 명시된 Evidence에 연결되어야 한다. law들은 scale phase마다 하나씩 필요하다. BDF 구간 내 응력 보간을 수행하지 않으며 왼쪽 knot 응력만 적용한다.
- 상 침전 반응의 양의 aqueous stoichiometric coefficient는 소비 reactant이고 음수는 생성 species다. `Q` term ID와 exponent는 양의 반응물 계수와 일치해야 한다. Reaction charge·element balance와 solid element formula를 검증한다.
- 각 stage에서 만들어지는 보존식 target에는 외부 Evidence를 꾸미지 않는다. 대신 input digest, 계산된 stage wall-composition digest, stage mass-action result digest를 interval별 first/last diagnostics와 함께 기록한다. Caller의 equilibrium/activity provider lineage 및 kinetic-law Evidence는 최종 결과에 보존한다.
- Mass-action stage fail, budget 초과, 비수렴, 음수 aqueous/solid inventory, 보존 잔차 및 geometry 실패는 완료 interval prefix와 digest lineage를 담아 `out_of_scope`로 닫힌다.

## 선택형 Davies 설정

`davies_activity=None`이면 기존 고정 활동도계수 경로를 사용한다. 자기일관 Davies 경로를 사용할 때는 `WetCo2StageDaviesActivity`를 전달한다.

| 입력 | 단위/계약 | 용도 |
|---|---|---|
| `water_mass_per_solution_volume_kg_L` | kg/L | 몰농도에서 물 기준 몰랄농도로 옮길 때 사용하는 caller 환산 |
| `davies_A_at_temperature`, `parameter_temperature_K` | 1, K | Evidence로 식별한 온도별 A와 해당 온도 |
| `davies_A_provider_id/revision`, `davies_A_configuration_digest`, `davies_A_record_digest`, `evidence` | 식별자/digest/Evidence | 파라미터 lineage; record digest는 같은 source ID의 Evidence에 있어야 함 |
| `ionic_strength_limit_mol_kg` | mol/kg, 최대 0.5 | Davies 근사 사용 범위의 caller 상한 |
| `charge_balance_tolerance_mol_kg` | mol/kg | stage 평형의 독립 전하 잔차 한계 |
| `maximum_outer_iterations`, `log_gamma_tolerance`, `damping_fraction` | 횟수/1/1 | 활동도계수–이온강도 고정점 제어; 최대 반복은 BDF 작업 예산에도 반영 |
| review flags | bool | 물 환산, A 온도·용매 기준, 표준상태 연결, 완전 종 재고/전하범위, 반복 설정, 단일 액상/무침전 가정을 각각 검토했는지 선언 |

예시 구성은 기존 `request`의 mass-action template에서 종·반응·제약식을 그대로 쓰고, 다음 형태의 설정만 추가한다. 실제 숫자·Evidence는 사용자가 선택한 parameter source와 해당 scope에서 제공해야 한다.

```python
request = request.model_copy(update={"davies_activity": WetCo2StageDaviesActivity(
    water_mass_per_solution_volume_kg_L=water_kg_per_litre,
    davies_A_at_temperature=davies_A,
    parameter_temperature_K=temperature_K,
    davies_A_provider_id=provider_id,
    davies_A_provider_revision=provider_revision,
    davies_A_configuration_digest=configuration_sha256,
    davies_A_record_digest=record_sha256,
    ionic_strength_limit_mol_kg=ionic_strength_limit,
    charge_balance_tolerance_mol_kg=charge_tolerance,
    evidence=parameter_evidence,
    water_mass_conversion_reviewed=True,
    Davies_A_temperature_solvent_basis_reviewed=True,
    molarity_to_molality_standard_state_mapping_reviewed=True,
    complete_inventory_and_charge_scope_reviewed=True,
    fixed_point_solver_settings_reviewed=True,
    single_liquid_no_precipitation_scope_reviewed=True,
)})
```

## 선택형 SIT 설정

`davies_activity`와 `sit_activity`는 동시에 지정할 수 없다. SIT 모드는 요청 schema v3에서만 허용한다. Caller는 기존 `AqueousSITIteration` 계약에 따라 물 질량 환산, 온도별 Debye–Hückel A, directional SIT 상호작용 계수, parameter/provider identity·digest, 완전한 Evidence 및 review flags를 제공한다. 포함된 `AqueousMassActionSystem`은 최상위 `mass_action_system_template`과 canonical digest가 정확히 같아야 한다. 계산 중에는 각 BDF stage 농도에서 만든 보존식 target을 가진 stage system으로 교체한 뒤 기존 `aqueous_sit_self_consistent_speciation`을 호출한다. SIT의 외부 provider 계수는 caller가 고른 조성·온도·단일 액상 범위에만 적용되며 자동 parameter fit이나 이온 상호작용 보간은 하지 않는다.

SIT 결과에는 activity model/provider lineage, ionic strength, outer iteration 및 fixed-point residual이 stage diagnostics로 남는다. 외부 parameter set의 적합성, 온도·용매 기준 및 parameter coverage는 caller 책임이다.

```python
payload = request.model_dump(mode="python")
payload["schema_version"] = "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v3"
payload["davies_activity"] = None
payload["sit_activity"] = caller_sit_iteration.model_dump(mode="python")
request = WetCo2CylindricalStageSpeciationScaleFeedback.model_validate(payload)
```

`caller_sit_iteration.system`은 `request.mass_action_system_template`와 digest가 정확히 같아야 한다. `model_validate`를 이용해 schema-version, 상호배제 및 digest 조건을 다시 적용한다.

## 선택형 B-dot 설정

`davies_activity`, `sit_activity`, `bdot_activity` 가운데 하나만 지정할 수 있다. B-dot은 명시적으로 schema v4를 선택해야 하며 기본 schema v2는 그대로 유지된다. `AqueousBdotIteration`은 최상위 `mass_action_system_template`과 같은 system을 포함해야 하고 digest 일치 검사를 통과해야 한다. stage마다 system의 conservation target만 현재 wall composition으로 바꾼 복사본을 solver에 전달한다. provider identity/revision 및 parameter configuration/record digest는 결과의 `mass_action_lineage`에 남고, stage 결과에도 provider, iteration 및 fixed-point/solver residual이 남는다. 물성 데이터나 조성 범위를 보간·외삽하지 않는다.

```python
payload = request.model_dump(mode="python")
payload["schema_version"] = "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v4"
payload["davies_activity"] = None
payload["sit_activity"] = None
payload["bdot_activity"] = caller_bdot_iteration.model_dump(mode="python")
request = WetCo2CylindricalStageSpeciationScaleFeedback.model_validate(payload)
```

## 보존 장부 및 제한

Interval ledger는 stage mass-action solver 횟수·잔차·first/last stage digest, (solver 출력에 있을 때) first/last stage species별 농도·활동도계수·활동도, time-averaged 상 flux, endpoint saturation ratio, aqueous species/charge/element 잔차, BV electronic charge 잔차, aqueous–solid 원소 increment 잔차, moving-grid sweep, phase inventory를 기록한다. v5 shear mode에서는 interval별 입력 wall shear, 요청 detachment flux, phase별 detached solid export와 고체 원소 export도 기록한다. Exact-knot geometry에는 bore/steel radius, phase 및 solid element inventory, wall alloy release residual을 남긴다.

평형 provider는 caller가 선언한 한 액상 단일상 반응망만 푼다. 반응 topology, 농도 보존식 선택, activity model, coefficient, 표준상태, log K, 온도 및 Evidence의 적용성은 caller 책임이다. 선택형 activity 설정이 모두 없으면 template의 고정 활동도계수를 사용한다. Davies/SIT/B-dot 모드는 반응식·종·기체 평형·고체 안정성을 자동 생성하지 않으며, 해당 단일 액상 수용액 평형의 전하/재고 범위와 activity model의 이온강도 support를 넘으면 계산을 닫는다. gas equilibrium, complex 생성, 침전상 탐색, metastability, 핵생성, scale 내부확산, 상 경쟁 또는 수명 qualification은 하지 않는다. v5 shear 기록은 호출자가 제공한 exact-knot 응력을 왼쪽 고정으로 적용하며, geometry iteration마다 유동장·전단응력을 재계산하지 않는다. detachment law는 경험적 caller 입력이며 부착력이나 박리의 보편법칙을 대체하지 않는다. 모델은 BDF stage마다 algebraic aqueous equilibrium을 재계산하지만, equilibrium solver의 미분 DAE Jacobian을 BDF에 제공하지 않는다. Mass-action 계산 실패 또는 stage 호출 한도 초과는 되돌려 대체 활동도로 계속하지 않는다.

이 증분은 신규 코드이며 테스트, benchmark, package build 또는 HPC 계산으로 검증되지 않았다.

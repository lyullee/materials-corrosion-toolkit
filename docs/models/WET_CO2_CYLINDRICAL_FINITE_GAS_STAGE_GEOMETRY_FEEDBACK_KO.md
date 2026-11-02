# 원통 반경이 stage마다 갱신되는 유한 기체 wet-CO₂ 연성 계산

## API

- Model ID: `integration.wet_co2_cylindrical_finite_gas_stage_geometry_feedback`
- Schema: v1 legacy; v2 opt-in stage-coupled scale shear removal
- 요청: `WetCo2CylindricalFiniteGasStageGeometryFeedback`
- 계산 함수: `evaluate_wet_co2_cylindrical_finite_gas_stage_geometry_feedback`
- 기반 계산 입력: `WetCo2CylindricalFiniteGasStageSpeciationFeedback`
- 추가 source IDs: `same_stage_cylindrical_radius_from_wall_and_scale_inventories`, `lagrangian_radial_mesh_conserved_cell_inventory_transport`; v2 shear mode also cites `caller_wall_shear_history`, `caller_calibrated_shear_scale_detachment_law`

## 계산 계약

기존 finite-gas stage API는 BDF interval 동안 bore/steel 반경을 고정하고, interval 끝에서 geometry Picard 반복을 수행한다. 이 증분은 각 BDF RHS에서 현재 phase inventory와 누적 wall alloy release로 반경을 다시 계산한다. Caller가 준 초기 geometry와 동일한 원통 보존식을 사용한다.

```text
r_steel² = r_steel,0² + released_wall_mass / (ρ π)
r_bore²  = r_steel² − Σ(n_phase V_phase) / π
```

현재 반경과 caller의 film thickness로 각 stage radial finite-volume edge 및 cell volume을 재계산한다. 상태변수는 농도가 아니라 각 radial cell의 종별 molar inventory다. BDF RHS는 현재 geometry에서 BV 혼합전위/반응, 확산, 외측 boundary 또는 유한 gas 전달, 동적 mass-action activity, scale precipitation/dissolution을 풀어 species molar source와 상/wall 재고를 동시에 적분한다. 반경은 이 wall/phase 상태에서 대수적으로 얻어지므로 별도의 interval-end geometry fixed point를 사용하지 않는다.

각 exact knot에서 geometry가 달라지는 경우 이전 radial grid와 새 interval grid의 overlap을 통해 농도 프로필을 재배치한다. 추가·제거된 경계 재고는 species별 signed exchange ledger에 남는다. BDF interval별 species·charge·전자전하·aqueous-solid 원소·gas 재고·global gas/liquid/solid/wall 원소 잔차와 stage radius digest를 출력한다. 계산 예산 초과, 비양수 반경, 고갈, 비수렴 또는 수지 실패는 완료 interval prefix와 실패 사유를 반환한다.

## 선택형 BDF-stage 전단 제거 (schema v2)

v1은 그대로 유지된다. v2에서는 `shear_removal: WetCo2StageShearRemoval`을 제공해야 한다. 이 공용 요청은 모든 transport knot과 일치하는 digest/Evidence 결속 wall shear record와, 모든 scale phase에 하나씩 대응하는 caller detachment law를 포함한다. 각 구간에서 shear는 왼쪽 knot 값으로 유지되며 `v_det = v_scale × max(τ/τ_critical − 1, 0)^n`, `J_det = v_det/V_m`를 사용한다.

전단 제거 flux는 scale inventory BDF 상태에 적용되어 같은 RHS에서 bore radius와 liquid radial mesh가 바뀐다. 화학 precipitation/dissolution flux만 aqueous source/sink ledger에 반영하고, detached solid은 수용액 생성종으로 돌리지 않는다. detached phase inventory를 별도 BDF export state로 적분하고, aqueous-scale-phase 원소 폐합 및 전체 gas/liquid/solid/wall 원소 ledger에 export 항을 포함한다. Interval ledger에는 shear stress, phase별 detached inventory와 원소 export가 기록된다.

```python
payload = geometry_request.model_dump(mode="python")
payload["schema_version"] = "matintegrity.wet_co2_cylindrical_finite_gas_stage_geometry_feedback.v2"
payload["shear_removal"] = caller_digest_bound_stage_shear_removal.model_dump(mode="python")
request = WetCo2CylindricalFiniteGasStageGeometryFeedback.model_validate(payload)
```

## caller가 승인할 가정 및 제한

- 액상 radial mesh는 Lagrangian으로 움직여 cell 몰수 상태를 보존한다. 별도 수력 solver나 임의의 radial fluid velocity를 추론하지 않는다. Caller는 mesh motion과 적용 조건을 검토하고 두 review gate를 설정해야 한다.
- outer radius는 해당 interval 시작 bore radius와 caller film thickness로 정해진다. inner bore가 이 경계에 닿으면 해당 interval은 out of scope로 닫힌다.
- scale chemistry/phase law, BV 반응망, aqueous network와 activity/equilibrium providers, alloy, Henry law 및 film coefficient는 nested caller contract 그대로 사용한다. 자동 종/반응/상 발견은 하지 않는다.
- 기체 capacity, 접촉면적, Henry 계수와 2막 계수는 fixed-capacity finite gas 모델의 제한을 따른다. 유동, 압력 vessel EOS, 다성분 기체, 온도 변화 및 외부 공정망은 포함하지 않는다.
- v1은 scale removal을 수행하지 않는다. v2 shear 경로도 hydraulic shear를 계산하거나 geometry 반복 중 응력을 다시 산정하지 않으며, caller가 제공한 exact-knot 응력과 경험적 law만 사용한다. Scale 보호효율, 분리 고체의 재부착·이동·화학 fate를 추론하지 않는다.
- 계산 구현을 추가했으며 수치 검증, 실험 검증 또는 설계 qualification을 주장하지 않는다. 본 변경에서 테스트, package build, HPC 작업은 수행하지 않았다.

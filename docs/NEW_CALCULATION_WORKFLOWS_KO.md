# 추가 계산 API 구성 안내

`examples/structural_assembly_workflow.py`는 tube geometry, tube inventory, elastic joint, FAD curve 및 FS life API의 독립 synthetic 호출을 모아 놓았다. 예제는 작성만 했으며 실행·검증하지 않았다. 모든 값은 설명용이고 재료·규격 권장값이 아니다.

## 입력과 적용 경계

- Tube layout: m 단위 outer/inner diameter와 pitch, regular square/triangular lattice. Void fraction은 무한 격자 단위셀 기준이며 실제 shell/baffle flow area가 아니다.
- Tube inventory: 물리 tube ID별 measured/reference wall과 plugging 상태. Active bore area는 기하 집계이며 열교환 성능·내압·누설을 판정하지 않는다.
- Elastic joint: N, N/m, m 단위 caller preload/stiffness/load/expansion. Contact loss는 out_of_scope로 반환하며 비선형 gasket 거동을 보간하지 않는다.
- FAD: caller curve의 Lr/Kr 좌표와 동일 material/geometry/load basis를 요구한다. 표준 curve·reference stress·fracture resistance를 자동 공급하지 않는다.
- FS life: engineering shear factor와 shear fatigue 계수 및 cycle support를 사용한다. Tensor shear와 engineering shear는 호출자가 일치시켜야 한다.

`API_KO.md`와 공개 계약 schema가 필드 정의를 제공한다. `IMPLEMENTATION_BACKLOG_KO.md`와 machine-readable scope audit는 전체 분야 범위와 이 bounded 계산을 구분한다. 테스트·독립 자격화는 후속 단계다.


## 후속 연성 및 비선형 API

`examples/model_inputs.json`의 `models` 아래에 다음 합성 요청을 제공한다. 계산은 실행하지 않았다.

| 모델 ID | 입력/결과 범위 |
|---|---|
| corrosion.explicit_co2_campaign | carbonate boundary, explicit reaction/transport/surface configuration, selected-tip dissolution, optional wall reaction and signed-ledger metal loss. `examples/build_co2_campaign_input.py`의 `build_request(include_wall_loss=True)`는 입력 생성 전용이며 solver는 호출하지 않는다. |
| corrosion.planar_slit_geometry | constant aperture, transverse width, axial cell widths, selected broad-face area and wall area density. |
| fabrication.nonlinear_gasket_contact | authorized reversible compression-force curve, initial compression, elastic bolt, separating force and bolt free-length change. Contact gap과 unsupported compression을 구분한다. |
| fatigue.multiaxial_life_campaign | closed local tensor cycle, directional/chord/circle plane factor, material-matched FS/SWT calibration and cycle support. FS k와 normalization stress도 calibration과 일치해야 한다. |
| degradation.calibrated_damage_history | identified microbial/cavitation provider rate intervals and support review. Total overflow와 unsupported interval에서 값을 보류한다. |
| thermal.fire_flux_response | declared net absorbed fire-face history plus explicit transient multilayer conduction. Input net boundary는 reradiation/cooling 해석을 사용자가 포함해야 한다. |

## 틈새 수송의 callback 경계

`solve_restricted_transport`는 nonuniform `cell_widths_m`을 사용할 수 있다. 입구 농도는 상수 또는 검토된 piecewise-linear history이며 끝단 surface flux와 측벽 distributed flux는 서로 다르다. 측벽 callback은 species×cell의 mol/m2/s를 반환하며 explicit wall area/solution volume과 곱한다. 누적량 원장은 axial cross-sectional m2 기준이다. 실제 총 mol은 일정 axial cross-section area를 곱해야 한다.

Activity callback은 species×(mouth+cell) 양수 gamma를 반환한다. SG drift에 `log(gamma_right)-log(gamma_left)`와 electrical potential term을 합산한다. Diffusivity는 해당 chemical-potential formulation의 tracer/mobility basis 검토가 필요하다. Gamma provider를 붙여도 homogeneous concentration mass-action constants가 activity equilibrium constants로 자동 변환되지 않는다. Poisson은 같은 비균일 cell volume/face distance를 사용하며 mouth Dirichlet 및 tip zero-field 경계다.

Python `solve_electrochemical_transport` 및 `evaluate_co2_corrosion_campaign`에 `wall_surface_flux=`와 `activity_coefficients=`를 전달할 수 있다. Callable을 JSON에 포함하지 않는다. Config digest가 요청과 다르면 거절하며, 함수가 없으면 needs_data다. CO2 selected-tip metal loss는 wall-wide mass loss를 합산하지 않는다. 결과의 `metal_loss_scope`와 transport의 별도 wall ledger를 보존한다.


## 보정된 조건→손실률→손실 이력

`degradation.calibrated_condition_loss_rate`는 명시적 경험식 `log(rate) = log(reference_rate) + sum(beta_i*z_i) + sum(b_ij*z_i*z_j)`를 계산한다. `z_i=(value_i-reference_i)/scale_i`이며 모든 feature ID, 원래 단위 token, reference/scale, support bounds, 계수와 calibration SHA-256을 호출자가 공급한다. 동일 feature의 자기 interaction은 quadratic term이다. 대칭 중복 interaction을 거절하며 기준 속도는 m/s 단위다. 모든 계수와 예제 수치는 프로젝트가 작성한 합성값이고 실제 미생물/캐비테이션 보정값이 아니다.

`degradation.calibrated_condition_loss_history`는 같은 material/mechanism law를 contiguous piecewise-constant conditions에 적용하고 구간 길이와 속도를 곱해 손실을 적분한다. 단위 자동 변환, 범위 밖 외삽, 누락 구간 제거, 지표 개수→보편 부식률 추론은 없다. 어느 구간이라도 계산 불가이면 총합을 보류한다. calibration rights와 feature/measurement applicability review를 별도로 요구한다.

## 단일 고체 침전·재용해 평형

`chemistry.single_solid_precipitation_equilibrium`는 한 종류 중성 pure solid의 반응 진행량 x를 구한다. 용존 성분은 `c_i=c_i0-nu_i*x`, 고체 inventory는 `s=s0+x`다. 모든 원소와 전하의 반응량 보존을 입력에서 확인하며 활동도는 명시한 `gamma_i*c_i/c_ref_i`다. 모든 reference concentration은 mol/m3이고 Ksp는 이 표준상태의 무차원 값이다. 온도와 Ksp 출처 digest, fixed-volume/constant-gamma approximation review가 필요하다.

과포화이면 용존 성분으로 제한되는 precipitation extent 안에서 log(Q)=log(Ksp)를 풀고, 불포화이면 기존 고체의 전량 소진 또는 포화에 도달할 때까지만 재용해한다. 원소·species extent balance 및 log saturation residual을 기록하며 주어진 수치 tolerance를 충족하지 못하면 out_of_scope다. 다른 acid/base speciation, 경쟁 고체, nucleation/precipitation kinetics, 피막 보호효과는 이 계산에 포함되지 않는다. FeCO3 이름의 합성 예제는 실제 상수 추천이 아니다.

## 수송과 국부 고체 평형의 연결

`EquilibriumReactiveTransport`는 고정 geometry에서 초기 phase projection, 각 interval의 transport, 그 뒤 cell-local equilibrium 순서로 진행한다. 기존 solver의 reaction/tip/wall callbacks를 받으며 interval 재시작 시 callback time을 전체 clock으로 되돌린다. `output_times_s`가 operator-splitting 경계다. 각 셀의 immobile solid inventory를 유지하고 phase 전환 source와 mouth/tip/homogeneous/wall exchange 원장을 따로 적분한다. reference axial area와 실제 local tip area를 구분한다. 첫 output은 초기 phase projection 뒤 상태이며 `initial_aqueous_inventory_before_phase_mol_m2`가 입력 전 inventory를 보존한다.

활동도를 쓰려면 underlying transport request의 `activity_provider_id`, `activity_configuration_sha256`, chemical-potential/tracer-diffusivity review를 함께 선언하고 `solve_equilibrium_reactive_transport(..., activity_coefficients=callback)`에 Python callback을 전달한다. Callback 입력은 절대 elapsed time과 species × (mouth + cell) concentration 배열이며 출력은 같은 shape의 유한 양수 gamma 배열이다. 같은 설정이 split transport 구간과 phase projection에서 호출된다. 각 phase cell의 초기 activity coefficient는 초기 callback 값과 일치해야 한다. 모델은 caller의 gamma를 적용할 뿐, activity law/상수의 자격, speciation 또는 다상 경쟁을 계산하지 않는다.

현재 split 경로는 모든 셀에서 하나의 고정 solid law를 공유한다. 기본은 ideal activity이며, 선택적으로 transport request의 provider ID/configuration digest에 고정된 Python activity callback을 transport drift와 각 phase projection 상태에 함께 적용한다. Phase 기록은 초기 각 셀 gamma를 callback과 대조하고, 후속 시각에서는 그때의 gamma로 고정 activity 계수 평형을 계산한다. 이 경로는 명시 single-solid operator split이지 simultaneous multiphase/speciation solver가 아니다. 반응 중 종분화·다상 경쟁, kinetic deposition, evolving aperture, splitting-error qualification은 별도 미구현 범위다.

`Co2CorrosionCampaign.phase_transport`를 선택하면 동일한 transport request와 원소 조성을 가진 phase split을 전극/용액 반응과 연결한다. phase input digest도 결과에 남고 출력 농도·전위·current diagnostics는 phase projection 뒤 상태에 맞춘다. Tip 용출량은 선택한 tip reaction 기준이다. 추가로 `wall_metal_loss_selection`을 전달하면 완료된 wall inward species ledger를 caller가 지정한 금속 종·몰질량·밀도·참조 단면·반응면적으로 변환한다. 결과의 `metal_loss_results`는 tip reaction 결과와 signed wall ledger 변환 결과를 분리 보존하며, 선택된 wall conversion이 미완료면 campaign status도 그 상태를 따른다. `examples/build_co2_campaign_input.py`의 `build_request(include_wall_loss=True)`는 합성 wall reaction, 일정 벽면적 밀도, 참조 단면 및 변환 선택을 한 번에 연결한다. 플래그는 입력을 만들 뿐 solver를 실행하지 않으며 합성 계수는 보정 자료가 아니다. 침전량을 부식 억제율로 환산하지 않는다. 사용 가능한 합성 입력은 `examples/model_variants/co2_single_solid_campaign.json`; 단일 고체 입력 생성은 `build_request(include_single_solid_phase=True)`다. 수치 테스트는 요청에 따라 보류했다.

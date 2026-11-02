# 잔여 구현 작업표

기준일: 2026-11-01

2026-11-01 추가 연결: component-state Crevice BDF에 검토된 caller current schedule을 반응 extent와 함께 적용한다. knot/cell 전하 연속, face-current migration 복원, A 단위 잔차, 적분 전하 장부가 포함된다. 이는 prescribed-current child API이며 BV/mixed-potential 기반 생성 전류, 고체상·대류·개구 연성은 여전히 상위 잔여 범위다. Wet-CO₂ 통합 finite-gas cylindrical BDF 경로는 코드 존재 근거와 함께 `implemented_unverified`로 추적되며, independent numerical/experimental validation은 남는다. bounded-code 추적 100/101 (99.0%)이며 코드 미완성 parent는 Crevice 1개다.

2026-11-01 새 sequential connection: `integration.crevice_component_state_faradaic_schedule_binding`는 current-carrying producer 결과를 component-state BDF의 caller current/extent schedules로 바인딩한다. Exact knot, input/result digests, species order, cell mapping, initial inventory, external component/element/charge ledgers를 검증하고 endpoint current density로 rate를 산출한다. Stage-resolved mixed potential은 거절하며, 압력/aperture, solids 및 intrastage BV feedback은 parent code residual로 남는다.

2026-11-01 실제 코드 증분: `chemistry.crevice_closed_batch_aqueous_equilibrium`는 초기 몰수로부터 보존 성분 목표를 만들어 caller Davies 평형 solver를 호출하고 닫힌 batch inventory 잔차를 확인한다. 이는 기존 BDF와 독립된 자식 경로다. `integration.wet_co2_cylindrical_stage_speciation_scale_feedback` v5는 caller 전단/상별 임계 탈락 법칙을 BDF 고체 재고에서 제한 차감하고, 탈락 고체를 별도 원소 export로 닫는다. 두 증분은 부모 모델 전체를 완료하지 않으므로 2개 `code_incomplete` 분류와 bounded-code 추적 99/101은 유지한다.

2026-11-01 component-state 후속: `integration.crevice_component_state_bdf`는 species-state solver를 변형하는 대신 보존 성분 몰수를 직접 적분하는 고정 부피·닫힌 경계 child solver를 추가했다. 각 stage Davies 평형, activity-gradient Nernst–Planck flux, 대수적 0 이온전류와 component face-transfer closure를 계산한다. Faradaic source, mixed-potential current, solid transfer, advection, hydraulic/moving aperture와의 동시 연성은 여전히 부모 residual이다. `integration.wet_co2_cylindrical_finite_gas_stage_geometry_feedback` schema v2는 별도 finite-gas branch에서 stage shear export를 live geometry와 global element closure에 묶는다.

이 문서는 `data/catalogs/implementation_scope_audit.json`에서 코드 경로 미완성으로 분류한 Crevice parent 1개의 잔여 계산 범위를 작업 단위로 추적한다. 분류가 data-validation-pending인 Wet-CO₂ parent는 별도 정적 구현 근거가 연결되어 있다. 이 표의 작업이 끝나도 해당 기술 영역 전체가 자동으로 완성되는 것은 아니다. 완료율이나 검증 통과를 뜻하지 않는다. 사용자 지시대로 현재는 신규 계산 테스트와 패키징을 실행하지 않는다.

2026-10-31 bounded increments: `integration.wet_co2_cylindrical_geometry_coupled_history` now repeatedly solves spatial transient radial transport/BV response against cylindrical wall recession while holding caller scale inventory fixed; remaining wet-CO₂ code gap is scale chemistry/kinetics and tighter direct coupling to evolving phase inventory. `chemistry.crevice_spatial_activity_solid_fixed_point` now couples per-cell Davies speciation with finite competing-solid transfers through linear aqueous inventory constraints at one fixed geometry knot; intercell transport/Faradaic coupling and dynamic aperture remain outside this child model. These child APIs do not change the two parent classifications or the 47/101 implemented-code-row count. No tests, packaging, or HPC run was performed.

## 실행 순서와 작업

추가 bounded 연동: `integration.electrochemical_metal_loss_wall_thickness_history`는 WCO2-1 metal-loss result를 digest-bound wall baseline에 연결하는 제한된 후속 경로다. 입력 반응 전부를 포함한다는 선언, 공통 면적의 branch별 적합성, Evidence-linked effective density와 anodic-only 두께 projection review가 필요하다. 이 경로는 잔여 구현 항목 분류 수를 바꾸지 않으며 임의 면적 분포·국부부식·남은수명 외삽·FTA 확률 생성은 하지 않는다. 상세는 `ELECTROCHEMICAL_WALL_THICKNESS_KO.md`.

추가 bounded 시나리오 집계: `integration.electrochemical_wall_thickness_scenario_envelope`는 이력 계산 결과 여러 개를 같은 물리/재료 범위·측정 baseline·required-thickness 이력·정확한 시간 절점에 맞춰 비교한다. 전체 manifest와 각 결과의 digest를 보존하고 pointwise thickness/margin minima/maxima와 witness 시나리오 ID를 반환한다. 시나리오 간 의존성과 전체 집합 review는 호출자 책임이며 결과는 finite-set extrema이지 확률, continuous bound 또는 remaining life가 아니다.

### CO2 수용액·전기화학 부식

**WCO2-1 — 부분 반응 전류에서 금속 손실 장부로 변환 (코드 연결 완료, 회귀/수치 검증 대기)**

- 목표: 현재 Nernst/Butler–Volmer 반응별 signed partial current 결과와 caller 지정 반응 화학량론·전자수·금속 원자수·몰질량·밀도·실제 노출면적을 입력으로 받아, 반응별 금속 용출 몰수·질량·면적 평균 두께 변화를 시간 구간별로 산출한다.
- 구현: `AssessmentResult` 출처 해시와 시각·자산·위치·전극 기준·전류 부호 convention을 고정하는 typed binding API를 만든다. 산화/환원 branch의 부호를 보존하고 각 branch와 합계 장부를 나눈다. 입력 반응 목록 누락, 비일치 시계, 단위 불일치, 비유한 적분 또는 금속 원자 balance 불일치는 결과를 `needs_data`/`out_of_scope`로 닫는다.
- 선행 입력: caller가 검토한 반응 화학량론, 전자수, 전극에서 실제로 용출되는 금속 종, 표면적과 재료 밀도. 이 값들을 문헌에서 자동 추론하지 않는다.
- 완료 증거: 독립 계산 API, JSON Schema, API/방법 문서, 합성 배선 예제, 코드 회귀 명세, `integration.*` catalog 연결 및 lineage 출력. 합성 회귀·보존식 검증과 실제 부식 검증은 별도 상태로 기록한다.

구현 상태: `integration.electrochemical_partial_current_metal_loss`가 등록되었고 upstream digest·반응전자수·reference area·branch exposed area를 고정해 anodic/cathodic charge, 금속 몰수·질량 및 signed 평균 recession을 반환한다. 실제 혼합전위 history 검증, material mapping 회귀, 부호·질량 balance 검증은 뒤의 일괄 검증에 남아 있다.

**WCO2-2 — activity/speciation/transport 단방향 composition 경계 감사 및 확장**

- 목표: 기존 caller activity provider, aqueous mass-action, restricted transport 및 반응 ledger가 공유하는 종 ID·표준상태·온도·용매·digest 경계를 목록화하고, 불일치 시 앞 단계 결과가 후속 손실 결과로 승격되지 않도록 binding을 보강한다.
- 선행 입력: 사용자 지정 종·반응 및 Evidence 매핑. 자동 수용액 네트워크 생성이나 보편적 activity law로 해석하지 않는다.
- 완료 증거: adapter별 명시 계약, 완전한 input/result digest 연결, 분리된 mismatch finding, schema/예제/회귀 명세.

구현 상태: `integration.electrochemical_chemistry_boundary_audit`가 각 stage의 computed AssessmentResult/input/context digest와 caller가 선언한 안전한 result path를 고정한다. asset/location/clock, exact knots·temperature, material condition, solvent와 activity standard state의 연속성을 검사하고, 모든 upstream species를 evidence-backed mapping/rename/reaction-transform/exclusion으로 처분하도록 요구한다. 이 경로는 감사 API이며 chemistry conversion이나 balance/solver 계산은 하지 않는다. 합성 계산·테스트·실제 chemistry 결과 audit는 보류한다.

추가 연결: `ElectrochemicalTransport`는 별도 review gate와 digest-matched `activity_coefficients` callback을 받은 경우 homogeneous reaction source에도 `gamma × concentration` 유효농도 보정을 적용할 수 있다. rate constants 및 농도 단위는 원 calibration을 유지하고, 해당 보정은 caller kinetics와 activity model의 적합성을 검증하지 않는다. 표준상태 변환, automatic reaction discovery, complete multiphase or chemistry-derived kinetics는 계속 미완성이다.

추가 연결: `chemistry.layered_scale_history_stack_transport`는 별도 단일상 scale-thickness AssessmentResults를 ordered multilayer diffusion request에 결합한다. 모든 layer는 distinct result digest와 정확히 일치하는 공통 output time을 요구한다. 두께 histories는 보간하지 않으며 phase discovery, 상간 반응, 동시 scale/electrode coupling, 물성 qualification은 계속 미완성이다.

추가 stage 연성: `integration.wet_co2_cylindrical_stage_speciation_scale_feedback`는 고정 gamma 외에 review-gated Davies v2/SIT v3/B-dot v4 자기일관 수용액 반복을 BDF stage마다 지원한다. 실제 stage species concentration·activity-coefficient 표본은 first/last diagnostics에 저장해 다음 모듈이 같은 BDF 상태를 추적할 수 있다. 이 옵션은 단일 액상 caller 정의 질량작용망만 풀며 automatic phase discovery, gas–liquid equilibrium, scale internal transport/adhesion/protective effects, corrosion-law qualification은 잔여 범위다.

### Crevice·틈새 부식

**CREV-1 — 전기화학 금속 ledger와 구간별 간극 recession 연결 (코드 wiring 완료, 계산·회귀 검증 대기)**

- 목표: WCO2-1의 금속 용출 ledger를 기존 crevice cell/face geometry에 매핑하고, caller 반응 면적·셀 벽 면적·밀도와 연결해 구간 종료 시 aperture 변화를 계산한다.
- 선행 입력: WCO2-1 결과, 금속 반응 분배와 전극 표면 위치를 crevice 셀/벽에 대응시키는 명시 mapping review. 틈새 내 전류 분포를 임의 균등화하지 않는다.
- 경계: 현 cellwise recession feedback은 restricted-transport 금속 ledger에 한정된다. 선택적으로 검토된 선형 aperture와 endpoint steady slit-flow 속도 경로를 함께 반복할 수 있지만, transient momentum·완전 동시 유동/화학/형상 연성 및 전기화학 원천 history의 재계산은 지원하지 않는다.
- 완료 증거: 검토된 공간 mapping 계약, 금속 재고↔aperture 체적 balance, sequential operator-split 경로, 실패 구간·성공 prefix·입력 digest의 분리, schema/API 문서·합성 예제·회귀 명세.

구현 상태: `integration.electrochemical_metal_loss_to_crevice_geometry`가 digest-pinned 금속손실 결과를 반응별 signed 체적으로 변환하고, caller가 모든 반응/시간 knot에 제공한 셀 분율을 적용한다. review gates, clock 연속성, fraction sum, finite mass, input lineage와 volume closure를 확인한 뒤 기존 sequential slit aperture remap을 호출한다. 첫 source 시각을 elapsed time 0에 매핑하며 nonzero origin에는 초기 형상 기준 clock shift review를 요구하고 대응을 보존한다. 지원 범위 이탈 시 마지막 허용 geometry state와 최초 실패 interval을 반환한다. 별도 transport-derived `solve_crevice_transport_recession_feedback`에는 deterministic callback review와 budget을 둔 aperture-change 기반 적응 분할·재계산이 있다. 이 함수는 선택적으로 bounded within-segment aperture fixed-point를 사용하며, 추가 review와 piecewise-linear pressure 표본이 있으면 endpoint steady slit-flow 사이의 선형 face-velocity path도 transport 반복에 연결한다. 이는 고정 upstream electrochemical history를 재계산하지 않고 transient momentum이나 완전 동시 유동·화학·형상 연성을 풀지 않는다. 따라서 electrochemical current/chemistry/geometry 완전 연성과 관련 data provider는 여전히 미완성이다.

추가 current-carrying handoff: `integration.crevice_current_carrying_extent_to_metal_loss`는 최신 current-carrying Faradaic 결과의 이미 적분된 reaction extent를 digest-pinned caller metal mapping으로 셀별 몰수·질량·부피·감육에 연결한다. 모든 branch는 dissolution 매핑 또는 명시적 비-dissolution 제외로 처분해야 하며, geometry adapter는 정확한 source cell ID/order와 volume closure를 확인해 셀별 부피 장부를 직접 소비한다. 전류를 다시 적분하지 않고, 구간 내 부호 반전이나 aperture-to-current 재계산을 제공하지 않아 CREV-1의 완전 연성 잔여 범위는 유지된다.

추가 BDF activity 연성: `integration.crevice_current_carrying_np_faradaic`는 `bdf_stage_spatial_mixed_potential`에서 interval별 caller-evidence-bound `AqueousBdotIteration`을 선택 입력으로 받아 BDF RHS마다 B-dot gamma를 다시 계산할 수 있다. 같은 stage gamma가 Nernst–Planck activity gradient, homogeneous reaction activity와 Nernst/BV mixed-potential에 전달되고, 별도 callback budget 및 request digest를 남긴다. 이 경로는 coefficient refresh이지 stage mass-action speciation이나 solid equilibrium이 아니며 정확 절점의 기존 Davies chemistry와 등가로 보장하지 않는다.

**CREV-2 — 외부 유동·질량전달 solver 교환 계약 (provider-neutral 코드 wiring 완료, provider 및 consumer 검증 대기)**

- 목표: 한강/외부 CFD solver가 계산한 pressure, face velocity, geometry revision을 기존 slit-flow/transport 요청에 재현 가능하게 교환한다.
- 선행 입력: 외부 solver별 단위·좌표계·mesh-face 방향·시간 기준 어댑터. 파일이나 결과가 아직 없는 solver는 provider 의존으로 남긴다.
- 완료 증거: provider-neutral typed receipt와 최소 한 consumer 교환 실행 기록. consumer를 실행하지 않은 schema 배선은 end-to-end 통합으로 표시하지 않는다.

구현 상태: `integration.external_crevice_solver_receipt` 및 `ExternalCreviceVelocityProvider`가 receipt metadata, digest, mesh/geometry/time/face mapping과 SI 단위를 확인하고 기존 `solve_restricted_transport` callable 경계로 보간 velocity를 노출한다. provider 전용 parser 및 실제 consumer 실행 증거가 없으므로 CREV-2 end-to-end는 미완료다.

추가 API: `bind_external_crevice_velocity()`가 transport 요청의 셀 폭·길이·출력 시간 범위를 solver receipt와 대조하고 provider/configuration/source digest를 검증된 요청 사본에 연결한다. 사용자가 사전에 설정한 time-varying advection 및 flow-continuity 검토 플래그는 필수다. 시각 원점 정합, CFD/수송 물리 일치, 실제 consumer 실행은 자동으로 가정하지 않는다.

추가 계산 경로: `degradation.crevice_lumped_exchange_reaction_history`는 caller가 선택한 고정 체적 well-mixed 단일 종의 piecewise-constant bulk concentration, exchange flow, first-order sink 식을 폐형식으로 전파하고 구간별 inventory/exchange/sink closure를 보고한다. 이 경로는 spatial transport나 multicomponent speciation을 닫지 않으며, transient momentum·상세화학·벽 반응률 자격검증은 남아 있다.

### 다축·비비례 피로

**FAT-1 — supplied material law plugin의 검증·적용범위 계약**

- 목표: 기존 sampled-plane/tensor path 및 memoryless/stateful damage callback에 material law 식별자·revision·calibration curve digest·재료 상태·응력/변형률 정의·주기 범위·검토 Evidence를 함께 전달하는 typed provider profile을 정리한다.
- 경계: 임의 재료의 보편 비비례 피로 법칙은 코드만으로 결정할 수 없다. 특정 law는 합법적으로 사용할 수 있는 caller 데이터와 적용성 확인이 있어야 한다.
- 완료 증거: 입력 검증과 lineage 연결, 지원범위 밖 데이터 fail-closed 동작, 예제용 합성법칙 및 독립 출처의 benchmark 비교 명세. calibration·holdout 분리와 물리 qualification은 실제 자료 확보 후 별도 수행한다.

구현 상태: `MultiaxialFatigueLawProfile`/`bind_caller_multiaxial_material_law()`가 memoryless 및 stateful callback 양쪽에 material/calibration/provider identity, tensor/stress/strain basis, componentwise support, cycle count/duration/repetition 및 reconstruction applicability를 연결한다. callback 매 표본에서 실제 재구성 stress/strain을 fail-closed로 확인하고 profile digest를 결과 lineage에 보존한다. 합성 예제와 schema/catalog/API note를 연결했으며 benchmark·수치검증은 보류한다. 이로써 profile wiring 코드는 추가됐지만 broad multiaxial capability는 calibration transfer·상태법칙 및 validation 공백 때문에 미완료로 유지한다.

**FAT-2 — 주기 분할·순서 의존 상태 전달의 교환 규약**

- 목표: 외부 solver가 산출한 tensor cycle block을 시간축·순서·반복 횟수·초기/최종 material state identity와 함께 기존 callback API로 넘기는 교환 계약을 제공한다.
- 선행 입력: provider가 보존하는 실제 cycle order 및 state semantics. 순서가 없는 집계 cycle counts만으로 순서 의존 law를 계산하지 않는다.
- 완료 증거: typed request/receipt, 누락 순서·state 불연속 거절, digest-bound 재구성 정책, API/schema·합성 예제.

구현 상태: `MultiaxialCycleBlockReceipt`와 `bind_ordered_multiaxial_cycle_blocks()`가 block/cycle digest, 원본 stress/strain digest, zero-based ordering, integer repetition, block 간 source material-state identity 연속성을 확인한다. request cycle payload가 receipt의 flatten 순서와 완전히 같을 때만 바인딩하고 receipt digest/provider ID·revision·run ID·result digest/block order/clock/state endpoint를 최종 stateful damage 결과에 전달한다. 실제 provider parser·consumer 실행과 sequence-state 실험은 대기 중이다.

추가 구현: `fatigue.critical_plane_findley_calibrated_life`는 기존 유한 sampled-plane Findley 파라미터를 caller의 digest-bound 단조 parameter-life curve에 연결한다. log(parameter)-log(life) 선형 보간은 curve support 안에서만 허용하고 외삽은 거절한다. calibration transfer, 독립 holdout 검증, 비비례 재료 law, code acceptance 및 qualification은 남아 있다.

### Gasket joint·flange

**GASK-1 — 외부 구조 solver compliance/stiffness 결과 adapter**

- 목표: 이미 있는 compliance reduction API를 외부 FE solver의 자유도·경계조건·기준점·단위·mesh revision receipt와 연결한다. solver 원본 출력과 축약 operator의 digest를 모두 보존한다.
- 선행 입력: FE solver별 명시된 DOF/sign/constraint 매핑 및 실제 구조 응답. 공개 상용/표준 허용 기준을 내장하지 않는다.
- 완료 증거: provider별 fixture를 통한 교환 실행 receipt, stiffness↔compliance 정합성 및 좌표/DOF mapping 기록, 빠진 구속/불안정 행렬의 fail-closed 결과.

**GASK-2 — 불확실성 입력을 포함한 누설 envelope**

- 목표: 현재 단일시점 독립 node pressure interval envelope와 calibration table에 caller가 제공한 보정계수/면적 공분산을 연결할 수 있는 별도 불확실성 전파 API를 설계한다.
- 선행 입력: 교정 자료가 제공하는 joint covariance 또는 명시된 bounded uncertainty set. 독립성 가정이나 확률분포를 자동 부여하지 않는다.
- 완료 증거: 확률/결정론적 구간 의미를 분리한 typed input, correlation-preserving 계산, 독립 해석 예제와 numerical convergence 회귀 명세. calibration 불확실성과 노드 상관 자료가 없으면 구현 경로가 있어도 `needs_data`로 표시한다.

구현 추가: `fabrication.gasket_leakage_covariance_propagation`는 caller 제공의 단일 joint-state 공분산을 정해진 변수 순서로 받아 bilinear 누설 map의 내부 셀에서 국소 1차 delta-method 분산을 계산한다. calibration knot/support boundary 입력은 거절하며 calibration/scenario/covariance/라이선스 Evidence를 고정한다. nonlinear uncertainty, 구간 보증, provider covariance 추정 및 수치 검증은 남아 있으므로 GASK-2 전체 완료로 표시하지 않는다.

추가 구현: `fabrication.gasket_leakage_box_envelope`는 caller가 정의한 independent rectangular set에서 각 node의 contact pressure/area 구간, 공통 differential-pressure 구간, entrywise calibration flux bounds를 평가한다. Piecewise-bilinear 표에서 pressure endpoints와 내부 table knots를 후보로 잡고 common differential-pressure endpoints/knots에 걸쳐 node contributions를 합산해 exact extrema 및 witness를 돌려준다. 이 보장은 선언된 box와 interpolation law에만 유효하며 joint correlations, covariance uncertainty, seal acceptance/qualification은 남는다. GASK-2 전체는 미완료다.

추가 구현: `fabrication.gasket_leakage_weighted_scenario_moments`는 digest로 고정한 완전한 joint leakage scenario와 동일 순서의 양의 caller 가중치를 결합해 유한 집합의 가중 평균·모집단 분산·표준편차 및 extrema를 계산한다. 가중치 합은 입력에서 1이어야 하며 의미와 권리 근거를 명시한다. 확률/신뢰구간이나 연속 bound로 해석하지 않는다. 연속 비선형 불확실성, 공분산 추정·제공자 검증, 독립 검증 사례 및 물리 qualification은 남는다.

추가 screen: `fabrication.gasket_contact_pressure_screen`는 계산된 static/exact-knot contact-pressure field의 각 node를 caller의 digest-bound 압력 창과 비교한다. 결과는 node margin과 controlling screening margin이며, sealing acceptance·leakage·qualification은 아니다. 물리·기준의 적용성 및 rights 검토가 필요하다.

## 한강 CPU 검증 준비 경계

- 현재 공유 SSH 연결 확인: `HPC_LOGIN_NODE`, 사용자 `HPC_USER` (2026-10-30). 이 확인은 계산 제출이나 저장소 전달이 아니다.
- 다음 준비물은 기존 `hpc/manifest.json` 중 미실행 항목을 현재 소스 snapshot에 맞춰 고정하고, wall-time·메모리·출력 경로·작업 수를 검토하는 것이다.
- 사용자가 별도로 제출을 요청하기 전에는 scheduler에 계산을 제출하지 않는다. 누리온에만 가능한 이전 manifest 작업은 한강 CPU에서 실행 가능 여부를 확인한 뒤 미지원 dependency를 분리한다.

## 순서 요약

1. CREV-1 전기화학 recession binding
2. WCO2-2 종·상태·digest composition 경계
3. FAT-1/FAT-2 provider law 및 cycle exchange 계약
4. GASK-1 외부 FE receipt 및 GASK-2 확률/상관 자료와 비선형 불확실성 확장
5. 데이터·권리·독립 benchmark를 확보한 범위만 사용자 승인 검증 계획에 올린다.


2026-10-30 CREV-2 정적 등록 결과: capability 373 calculators·157 interfaces·101 partial (631 total), public schemas 802, implementation bases 423. 101-row scope audit는 253 paths·365 components, 누락 경로·AST 실패·stale/unmapped symbol·unmapped component 0. 이는 정적 연결 상태만 말하며 solver round-trip/consumer 실행은 증명하지 않는다.

구현 상태: `integration.external_flange_compliance_receipt`가 digest-검증 provider receipt의 FE kind, load-case/boundary, mesh/frame, stiffness field ID/shape/unit/raw-array digest, node/component DOF map, contact normal/sign 및 basis-transform lineage를 검사한 뒤 기존 compliance reducer를 호출한다. 이는 이미 변환된 translational N/m tangent matrix를 소비하며 solver parser/FE assembly, provider별 교환 실행·independent benchmark는 아직 없다.

추가 구현: `integration.external_flange_compliance_history`는 시간 절점별 단일 receipt binding을 받아 기존 compliance history reducer에 연결한다. provider/model revision, 자산 범위, frame/DOF/contact mapping을 고정하고 절점별 mesh·load case·matrix digest와 receipt lineage를 반환한다. receipt 자체가 물리 시각을 제공하지 않으므로 caller가 `receipt_times_reviewed`를 승인하기 전에는 계산하지 않는다. provider parser, 실제 provider round-trip 및 구조/실링 qualification은 여전히 남는다. 정적 생성 결과는 389 models·159 interfaces·101 partial (649 capabilities)·821 schemas·447 source bases이며, 101-row audit 265 paths·380 components에서 누락·AST·stale·unmapped 오류가 없다.

구현 상태: `fabrication.gasket_correlated_scenario_envelope`가 complete caller joint scenario 안의 node pressure, shared differential pressure, node area와 scenario-specific calibration grid를 함께 계산해 유한 scenario set의 extrema/witness를 보존한다. 확률을 가정하지 않으며 연속 uncertainty set bound가 아니다. 실측 joint covariance/scenario provider, convergence 및 독립 leakage 비교는 자료·검증 대기다.

네 broad code gap(WCO2, crevice, multiaxial fatigue, gasket)의 일부 명시 코드 경로는 registry/API/schema/catalog까지 연결했지만 자동 완전 반응망·연성, 실제 provider parser/consumer, calibration/holdout 및 물리 validation이 남아 capability 전체 완료는 아니다. 최신 정적 결과는 continuation의 2026-10-30 갱신 기록을 참조한다.

## 병렬 증분 모듈 — broad scope 미완료

- CREV-3: `integration.crevice_aperture_history_refinement`는 기존 geometry history에 caller 한도와 digest를 적용해 선형 보간 구간을 구성한다. 삽입점은 물리 solver가 계산한 state가 아니며 metal-loss나 transport를 재실행하지 않는다. 한도 초과 시 연속 prefix와 실패 interval을 남긴다. Geometry가 `AssessmentResult`에서 온 경우 원본 result와 context digest도 검증한다. 최대 구간 설정에서도 리스트 재배치의 이차 비용을 피하도록 양끝 큐로 순차 분할한다.
- WCO2-3: `integration.wet_co2_elemental_phase_handoff`는 이미 계산된 aqueous/solid history에 caller 원소식과 solution volume을 적용한다. 경계 flux, 누락 상, 반응 extent는 추론하지 않는다. provider-specific 정규화, 완전 종/상 목록, 외부 경계 flux closure 및 물성/부식 데이터 validation은 남아 있다.
- WCO2-4: `integration.aqueous_candidate_network_workflow`는 기존 bounded balanced-candidate enumeration, Evidence-backed manual equilibrium-data binding, strict mass-action assembly를 한 digest-pinned 흐름으로 구성한다. 자동 reaction/phase discovery를 제공하지 않으며 thermodynamic feasibility·rates·corrosion validity는 사용자 데이터와 별도 solve/검증에 남는다.
- GASK-3: `integration.gasket_leakage_scenario_exposure` composes a computed finite correlated leakage-rate result with an explicitly reviewed constant-state exposure duration. This gives downstream modules an amount basis in mol, but it does not model time-varying gasket relaxation or pressure. Transient history and material/seal qualification remain open.
- 최신 정적 생성: 817 schemas; 380 registered calculation models, 159 interfaces, 101 partial rows (640 entries); 434 implementation bases. Audit 101 rows·262 source paths·375 components; missing/AST/stale/unmapped=0. 정적 성공은 실행/수치/물리 검증을 뜻하지 않는다.

## 최신 병렬 산출물 및 진행률 (2026-10-30)

- WCO2-4 `integration.aqueous_candidate_network_workflow`: candidate balance→manual Evidence-backed reaction/logK binding→mass-action assembly를 digest로 묶는다. 자동 선택/speciation solve는 별개다.
- FAT cycle receipt: provider ID/revision/run/result digest가 stateful request와 output에 보존된다.
- GASK-3 `integration.gasket_leakage_scenario_exposure`: finite correlated scenario rate에 caller 검토 constant-state duration을 곱해 mol량과 witness를 제공한다. 시간 변화 및 event probability를 추론하지 않는다.
- 전체 scope completion flag: 47/101 = 46.5%. 분류 상세는 47 data-validation-pending 행이 code implementation complete, 4 data-validation-pending 행이 추가 코드도 필요, 4 code-incomplete, 46 provider-dependent다. 따라서 나머지 54행은 아직 전체 완료 기준을 충족하지 않는다.
- 정적 산출물: 817 schemas, 380 models, 159 interfaces, 101 partial entries, 434 source bases; audit 262 source paths·375 components, missing/AST/stale/unmapped 0. 이는 테스트나 물리검증 통과를 나타내지 않는다.

- WCO2-5 `integration.aqueous_candidate_network_speciation`: computed candidate workflow result plus complete digest is checked before invoking the existing aqueous mass-action solver on the exact assembled system. The output preserves workflow/enumeration/binding/assembly/system/solve lineage and registry context. The solver remains fixed-gamma, caller-parameterized and single-phase; automatic reaction discovery, phase equilibrium, precipitation, kinetics and physical corrosion validation are not provided.

- GASK-4 `integration.gasket_leakage_scenario_rate_interval`: 두 시점의 computed correlated leak envelopes를 scenario ID와 calibration realization digest로 대응하고, caller가 승인한 piecewise-linear total leak-rate 재구성에 대해 scenario별 exact trapezoid mol amount를 계산한다. 평가하지 않은 중간 압력/접촉·완화 상태, transient extrema, 확률 및 acceptance는 추론하지 않는다. 후속 time-resolved provider와 validation은 외부 확장 과제다.

Multiaxial scenario extension: `fatigue.multiaxial_life_scenario_envelope` now reports finite-set extrema across digest-pinned computed critical-plane life campaign results. It preserves whole scenarios and validates common calibration/material/cycle support; it neither generates the scenario distribution nor produces confidence/probability or continuous parameter bounds. Caller law-provider scenario generation, correlation/coverage evidence, calibration/holdout and independent fatigue validation remain open.

## 최신 정적 스냅샷 (2026-10-30, 이후 라운드)

- WCO2-5 `integration.aqueous_candidate_network_speciation`: Evidence-backed candidate workflow의 정확한 assembled mass-action system을 digest/온도/표준상태/context 검증 후 기존 aqueous speciation solver에 연결한다. 종·상 발견/kinetics는 제공하지 않는다.
- FAT-3 `fatigue.multiaxial_life_scenario_envelope`: 동일 calibration/material/cycle support/context의 computed life campaign을 완전한 correlated finite scenario로 묶고 extrema/witness를 제공한다. 확률/신뢰구간/연속 bound는 아니다.
- GASK-4 `integration.gasket_leakage_scenario_rate_interval`: matched correlated scenario endpoints의 총 누설률을 caller-reviewed 선형 시간 재구성으로 trapezoid 적분한다. sampled endpoints 외 transient extrema 및 probability는 추론하지 않는다.
- 현재 카탈로그(2026-10-30 최신 정적 생성): 821 schemas, 390 models, 159 interfaces, 101 partial rows (650 total), 452 source bases. Audit: 101 rows, 265 paths, 380 components; path/AST/stale/unmapped 오류 0. 최신 추가 API는 Evidence 연계 aqueous reaction-cycle audit/mass-action adapter, receipt-bound flange compliance history, 그리고 caller 반응 엔탈피/선택적 constant ΔCp로 온도별 mass-action 평형을 재계산하는 van't Hoff history다. 계산 테스트·수치/물리 검증·패키징·HPC 실행 결과는 아니다.
- 엄격한 scope completion은 47/101 = 46.5%로 유지. 남은 코드는 broad WCO2/crevice/fatigue/gasket scope의 unresolved parts이며 data/provider/validation도 대기 중이다. 테스트·패키징·HPC 실행은 하지 않았다.

## 2026-10-30 WCO2 reaction-cycle consistency increment

`chemistry.aqueous_thermodynamic_cycle_audit` closes one bounded WCO2 gap: it verifies caller-declared elemental/charge balance and checks whether `log10(K)` lies in the stoichiometric right-null-space complement. It uses a caller-reviewed SVD relative rank tolerance and log-constant closure tolerance, pins reaction source records to Evidence file hashes, and returns the orthonormal cycle basis and residual. This remains an audit utility; it does not discover reactions/phases, solve speciation, supply equilibrium constants, or validate a corrosion mechanism. The WCO2 capability remains code-incomplete overall.

`integration.aqueous_mass_action_cycle_audit` now reuses the existing `AqueousMassActionSystem` contract and accepts exact per-reaction source bindings. It verifies complete reaction coverage and source-file hashes, requires existing elemental formulas instead of inventing them, and delegates to the same cycle evaluator. This closes a duplicate-input integration gap only; no equilibrium or corrosion validation is claimed.





추가 구현: `integration.aqueous_mass_action_vant_hoff_history`는 기준 온도의 caller 질량작용 system과 reaction ID별 Evidence-bound reference enthalpy를 사용해, 선언 범위 안의 온도 절점마다 van 't Hoff 관계로 log10(K)를 갱신한 뒤 기존 single-liquid mass-action solver를 다시 호출한다. reaction enthalpy 일정 근사, 표준상태 일치, fixed-gamma 온도 적용성, source/license 및 시간·온도 대응 review가 없으면 계산하지 않는다. activity gamma의 온도 의존, Cp 보정, phase discovery/precipitation, kinetics, corrosion rate 및 범위 밖 외삽은 하지 않는다. IDAES method, IUPAC standard K 및 NIST CODATA R 참조를 기록했다. 새 registry 합성 입력은 synthetic only다.


van 't Hoff history 확장: `activity_coefficients_by_knot`에 절점별 활동도계수 배열을 넣으면 기준 system과 같은 종 순서로 적용하고 각 source-record/Evidence/license 및 provider ID/revision/configuration digest를 결과에 보존하며 이 history 안에서 provider configuration이 일치해야 한다. 자료 배열을 제공하면 temperature-history review gate가 필수이며, 미제공 시에만 기존 reference gamma 고정경로를 별도 review로 쓸 수 있다. 행간 보간이나 활동도 모델 추정은 없다.


van 't Hoff 열화학 확장: 각 reaction record는 `delta_cp_reference_J_mol_K`를 선택적으로 제공할 수 있다. ΔCp가 입력된 행은 constant-ΔCp review가 추가로 필요하고 ΔH(T)=ΔHref+ΔCp(T−Tref)를 적분한 `ln K` 보정을 사용한다. ΔCp를 생략하면 기존 constant-ΔH 형태를 유지한다. 고차 Cp 모델·추정은 포함하지 않는다.


현재 데이터 검토 메모: catalog는 63개 dataset record와 276개 asset record를 갖고, 48개 ID의 다운로드 완료 4.29 GB 원본이 local `data/raw`에 있으나 모두가 재배포나 물리 calibration에 적합한 것은 아니다. 예: NORSOK M-506는 CC BY 시뮬레이션 grid라 같은 계통의 코드 비교용으로만 검토하며, 이질적 wet-CO2 compilation의 unresolved rows는 출처/권리 mapping 전 fitting에 넣지 않는다. TUDOdata mean ionic gamma는 metadata-only 및 underlying-literature provenance pending이고 종별 gamma vector에 직접 사용할 수 없다. 상세 결정은 `docs/DATA_KO.md`와 `data/catalogs/datasets.json`에 기록했다.

## 2026-10-30 van 't Hoff 선형 열용량 모델 구현

수용액 van 't Hoff 이력 API에 caller가 제공하는 `delta_cp_slope_J_mol_K2`를 추가했다. `delta_cp_reference_J_mol_K`가 반드시 함께 있어야 하며 ΔCp(T)=ΔCp_ref+slope·(T−Tref)를 분석적으로 적분한다. 이 옵션은 `temperature_dependent_reaction_heat_capacity_reviewed` gate, 정량 단위, reaction별 입력 lineage와 method formula에 연결된다. 기존 constant-ΔCp gate는 slope 없는 record에만 적용한다. 공식의 열화학 기반은 OECD NEA TDB temperature correction 문서에 연결하며 coefficient 값은 추정하지 않는다. registry synthetic example 한 반응에만 가상 기울기를 넣어 input wiring을 기록했다.

정적 API·registry·schema/catalog 생성과 source-path audit만 갱신할 예정이며 계산 실행, 테스트, 패키징은 하지 않는다. 전체 scope completion은 47/101(46.5%)으로 유지한다. WCO₂ 모델 전체에는 자동 chemistry/phase discovery, 비이상 혼합물 물성·kinetics, 자료 적합 및 독립 물리 qualification 공백이 남는다.

2026-10-30 정적 생성 기록: van't Hoff history–포화도 연계 API를 default registry에 등록하고 3개 public contract를 JSON schema로 내보냈다. regenerated catalog: 391 models·159 interfaces·101 partial rows (651 capabilities)·452 source bases·827 schemas. 101-row AST/path/component audit: 266 source paths, 381 components, missing paths/AST errors/stale symbols/unmapped components 0. Public source-boundary audit returned `passed` with restricted local roots excluded; this is not legal clearance. The API count does not change the strict 47/101 implementation classification because wet-CO2 remains broad-scope incomplete. No calculations, tests, packaging or HPC jobs were run.

추가 구현: `fabrication.gasket_leakage_box_envelope`는 caller 독립 직사각형 입력 구간 내에서 node 압력/면적, 공통 차압, 보정 flux grid 구간의 정확한 total leak-rate extrema를 bilinear table 아래 산출한다. 이는 비확률 box bound이며 상관 집합·물리 qualification은 대체하지 않는다.

## 2026-10-31 — 추가 CREV/WCO2 코드 경로

- `integration.electrochemical_wall_flux_schedule`은 digest-pinned metal-loss assessment의 anodic metal amount를 interval duration과 reviewed common area로 나눈 wall-flux callback을 제공한다. Cellwise uniformity, branch area compatibility, time-origin rebasing은 caller review가 필요하다. Moving-boundary flux integration may differ from the upstream total.
- `integration.wco2_species_transfer_audit`는 workflow stage 사이 caller-declared species identity/name-change/stoichiometric transforms를 검사한다. Upstream exclusions 및 downstream coverage를 명시하고, declared composition에 대한 charge/element closure를 요구한다. Mechanism·equilibrium·kinetics 추론은 없다.
- 두 API 모두 registry/schema/catalog에 연결됐고 Python installed catalog가 동기화됐다. 부모 scope 분류는 변경하지 않는다.

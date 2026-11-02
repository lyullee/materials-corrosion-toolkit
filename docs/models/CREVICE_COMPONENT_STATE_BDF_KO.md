# Crevice 보존 성분 상태 BDF 선행 solver

`integration.crevice_component_state_bdf`는 종 농도 대신 caller가 명시한 보존 성분 몰수를 각 셀의 BDF 상태로 적분하는 격리형 child solver다. 매 BDF RHS 평가에서 각 셀의 trial 성분 몰수와 고정 부피로 수용액 constraint 목표를 다시 만들고, caller 증거가 연결된 기존 Davies–mass-action solver로 국소 종 평형을 계산한다. 최종 knot에는 종 농도 출력을 포함한다.

## 입력과 수지

요청 모델은 `CreviceComponentStateBDFRequest`, 셀 화학 템플릿은 `CellAqueousEquilibriumTemplate`, 평가 함수는 `solve_crevice_component_state_bdf`, ModelSpec은 `specifications()`다. 각 셀은 `AqueousDaviesIteration`, 완전한 제약 역할 분할, 성분별 species 계수 맵을 제공한다. 각 성분 사상은 대응 제약 행과 일치하고 각 선언 반응에서 보존되어야 한다. 전하 제약 행은 종 전하수와 정확히 일치하는 0 target이어야 한다. 셀별 volume은 적분 중 고정된다.

수송에는 호출자가 제공한 내부 면 면적·셀 중심 거리·종별 확산계수를 사용한다. 매 RHS에서 평형 종 농도와 활동도계수로 Nernst–Planck 확산 플럭스를 계산하고, 내부 각 면의 migration 전위 구배를 대수적으로 풀어 이온 전류 0을 강제한다. `absolute_face_current_closure_tolerance_A`와 `relative_face_current_closure_tolerance`가 전류 잔차 상한을 지정한다. 종 플럭스는 보존 성분 계수 맵으로 투영해 성분 면 전달률을 만든다. 외부 양 끝 면은 무유량이며, 별도 대류·source·reservoir는 포함하지 않는다. 상태 미분은 `dN_k/dt = J_left - J_right`이다. 내부 성분 면 전달은 별도 적분 상태로 누적하여 셀별 수지 잔차를 확인한다. 총 성분 몰수는 폐쇄 경계에서 보존되어야 한다.

기본값은 여전히 source가 없는 경로다. 선택형 `electrochemical_sources`에는 반응마다 정확한 수송 시간 knot별·셀별 signed extent rate, 수용액 종량론, 원소별 외부 reservoir 변화, 성분별 reservoir 변화, 전하 ledger와 evidence를 넣는다. 외부 reservoir change는 저장량 증가를 양수로 두며, aqueous 변화와 reservoir 변화의 합이 0이어야 한다. 이 모드를 쓰려면 명시적 `electrochemical_source_stoichiometry_and_reservoir_reviewed`와 caller가 정한 `maximum_absolute_source_extent_rate_mol_s`도 지정한다. 입력 검증은 수용액 종 전하와 reservoir 전하, 원소 변화, 성분 변화가 각각 닫히는지 확인한다. extent는 정확 knot 사이에서 선형 보간해 BDF 보조 상태로 적분되고, 보존 성분 RHS에 투영되며, 출력에서 reservoir ledger와 함께 대조한다. 별도 `maximum_total_source_projection_operations` budget이 RHS에서 이 작업량을 제한한다.

기본값에서는 내부 이온 전류를 0으로 둔다. 순전하 source는 caller 전류 schedule과 charge continuity가 닫힐 때만 허용한다. schedule knot는 transport/source knot와 정확히 일치하고 각 knot에서 `ncell+1` signed 면 전류(A)를 제공하며 Evidence와 `ionic_face_current_schedule_reviewed`를 요구한다. 외부 경계 전류는 0으로 고정한다. 매 knot·cell에서 `I_right - I_left = F Σ(z_i ν_i r)`를 검사한다. 두 schedule을 같은 시간 선형 보간으로 stage에 적용하고 NP migration 구배가 caller 전류를 재현하는지 A 단위 잔차로 확인한다. 이 전류는 caller supplied이며 BV/mixed-potential solver에서 유도하지 않는다. 적분 전하(C), 전류와 source digests가 결과에 포함된다.

기본 caller-schedule 모드에서는 외부 경계 전류가 0이므로 source charge의 셀 합도 0이어야 한다. 이 경로는 caller가 제시한 current와 extent를 수송식에 맞추며, 벽 kinetics를 계산하지 않는다.

### 선택형 BDF-stage 혼합전위 결합

별도의 review-gated 경로에서는 `faradaic_stage_coupling`에 기존 공간 Ohmic/Butler–Volmer/Faradaic 요청을 넣고 `component_state_faradaic_stage_coupling_reviewed=True` 및 `maximum_absolute_stage_faradaic_extent_rate_mol_s`를 지정한다. 이 선택 모드는 각 BDF trial의 국소 평형 종 농도와 활동도계수를 mixed-potential stage solver에 전달한다. 그 stage의 branch signed current density를 caller가 선언한 반응 면적으로 전류(A)로 바꾸고 `nF`로 나눈 extent rate를 같은 보존 성분 상태 RHS에 투영한다. 동일 stage의 electrolyte face current는 NP 이동항 목표로 사용한다. 따라서 branch extent와 전류는 독립된 사후 schedule이 아니라 동일 trial chemistry에서 나온 값이다. component-state BDF의 고정 부피 가정에 맞춰 모든 geometry knot의 cell/face area가 일정해야 하며, 각 셀의 litre 부피, NP face area와 cell-center 간격은 혼합전위 형상과 일치해야 한다. 이동 경계·가변 aperture는 이 모드에서 아직 지원하지 않는다.

이 경로는 입력의 시간 knot, 셀 ID와 순서, 종 ID와 순서, 전하수, uniform mesh, 온도 조건이 양쪽 계약에서 정확히 맞아야 한다. 현재 local Davies stage chemistry의 지정 온도와 Faradaic interval 온도도 일치해야 한다. 별도 `electrochemical_sources` 또는 `ionic_face_current_schedule`와의 혼용은 거부한다. 내부 각 셀에서 `I_right - I_left = F Σ(z_i ν_i r_i)`를 확인하고, 전류 solver의 A 단위 폐합 오차 및 component inventory/reservoir ledger가 닫히지 않으면 결과를 commit하지 않는다. 양 끝 면은 절연 경계여야 한다. source rate 및 총 mixed-potential solver work에는 caller 상한이 적용된다. 결과에는 exact-knot 전류·branch current density, source/evidence digest, stage solver work, 그리고 mixed-potential lineage가 포함된다.

이는 계산 결합 경로의 구현이며 물리 검증·재료별 kinetic parameter 승인·자격 검증을 뜻하지 않는다. Faradaic 입력의 Nernst/BV 계수, 전도도, branch 화학양론, 반응 면적과 evidence는 caller 책임이다. 검토된 기존 spatial mixed-potential contract가 보장하는 branch 부호 규칙에 맞지 않거나 charge/component closure가 실패하면 fail-closed 한다. 기존 species-state Crevice BDF를 바꾸지 않으며, 고체상 전달·유동·가변 부피·double-layer 저장을 추가하지 않는다.

### 선택형 총성분–고체상 평형 stage 결합

이 모드는 `schema_version="matintegrity.crevice_component_state_bdf.v2"`를 명시해야 한다. 기존 v1 요청은 aqueous-only 기본 동작을 유지한다.

`solid_equilibrium_mode="instantaneous_solid_equilibrium"`를 선택하면 기존 기본값 `aqueous_only`와 의미가 분리된다. 이 모드의 BDF 상태는 각 셀의 **액상 + 후보 고체상 총 성분 몰수**다. `CellSolidPhaseSet`은 셀별 phase 후보를 material condition, metallurgy, environment, asset/location/scope, clock, 정확한 전체 `time_s` knot, 온도 및 `dimensionless_molarity_1_mol_L` 활동도 표준상태에 묶는 digest receipt다. `phase_set_sha256`는 receipt 자체와 `phase_set_evidence`를 제외한 필드에서 계산하고, 그 digest를 pin하는 Evidence가 필요하다. 모든 후보 상은 기존 Evidence/Ksp digest를 유지하고 zero seed inventory를 써야 한다. phase set completeness, 총량에 고체 포함, 순간평형·무핵생성장벽 가정과 computation use를 별도 review한다. Faradaic mode와 함께 쓰면 phase receipt의 assessment/asset/location/scope/clock/cell/time/temperature가 Faradaic context와 정확히 일치해야 한다.

각 BDF trial마다 셀별 `chemistry.crevice_component_solid_partition`을 호출해 total component 상태를 aqueous totals와 고체 inventory로 분배한다. 그 trial의 aqueous species와 activity coefficient만 NP/Faradaic 계산에 제공한다. 내부 분배에는 net source를 더하지 않는다. BDF state derivative는 기존 aqueous NP/Faradaic flux가 component map으로 투영된 총성분 변화량이며, 고체 반응은 aqueous와 solid 사이의 내부 이동이다. exact knot마다 aqueous component, phase별 고체 몰수, solid component, total component 및 element ledger를 기록한다. Solid mode는 모든 species element formula와 독립 component basis를 요구해 component-to-element map을 재구성하며, 성립하지 않으면 요청을 거부한다. 외부 source element/reservoir, Faradaic/ionic face-current charge continuity와 integrated current ledger도 같은 결과에서 폐합한다.

`maximum_total_solid_partition_evaluations`, `maximum_total_solid_active_set_sweeps`, `maximum_total_solid_bisection_iterations`, `maximum_total_stage_equilibrium_calls`, `maximum_total_nested_equilibrium_iteration_work`는 RHS 호출과 exact-knot 재계산을 통틀어 집계된다. Output solid history에도 `maximum_output_solid_phase_values` 상한이 적용된다. aqueous-only mode의 기본 계약/계산은 그대로 유지된다. Instantaneous solid-equilibrium branch는 finite caller phase set의 순차 active-set 해이며 global Gibbs minimum/유일성을 증명하지 않는다. 아래 v6 kinetic branch는 별도 모드로 nucleation·finite growth를 적분하지만 phase discovery, 준안정성, scale morphology, 재료별 물리 검증과 material qualification은 포함하지 않는다.

### schema v6 same-stage kinetic phase state

schema v6의 opt-in `kinetic_phase_sets_by_cell`는 셀별 phase 후보, 초기 solid mol, nucleation threshold/rate, saturation-growth law, exact clock 및 temperature record를 digest로 묶는다. 모든 시간점에서 BDF 상태는 total conserved component mol과 phase별 solid mol을 함께 유지한다. 각 trial마다 total 성분에서 현재 고체량을 빼 aqueous total을 만들고, local Davies equilibrium으로 활동도·포화도를 구한 뒤 caller kinetic law를 평가한다. 내부 precipitation/dissolution은 total-component derivative에 net source를 추가하지 않고 액상과 고체상 사이에서만 양을 옮긴다. seed threshold와 solid depletion은 event root에서 BDF를 재시작한다. 고체 점유율 geometry를 선택하면 같은 trial의 aperture/volume과 dynamic hydraulic RHS가 연결될 수 있다.

2026-11-02의 2-cell synthetic NaCl 예제는 schema-v6 request validation부터 BDF 실행까지 수행했다. Davies stage equilibrium, 동시 seed event, 고체 history와 component closure를 확인했고 관련 kinetics/event/BDF/double-layer test suite 30건이 통과했다. 이 시험은 synthetic input만 사용하며 kinetic parameter qualification을 뜻하지 않는다. 별도 moving-hydraulic kinetic 조합과 depletion/reappearance 극한의 추가 검증은 남아 있다.

### schema v7 동적 이중층–공간 Faradaic same-stage 연성

schema v7의 선택 입력 `dynamic_double_layer: CreviceBDFDoubleLayerCapacitance`는 셀별 초기 계면전위·기준전위, caller가 제공한 양의 미분용량 곡선, 순서가 고정된 cell ID, curve/state digest 및 사용 허가 Evidence를 받는다. 계산은 각 셀의 적분 전하를 BDF 상태에 추가하고, 곡선 구간 내에서 전하를 계면전위로 역산한다. 곡선 외 extrapolation은 허용하지 않는다. 고정 반응면적은 mixed-potential geometry로부터 셀 길이×슬릿 폭×반응면 수로 구성한다.

각 trial RHS에서는 trial 화학에서 Nernst 평형전위와 전해질 전도도를 다시 만들고, 공간 Ohmic face current와 reviewed Butler–Volmer branch를 결합한다. 전극 금속 기준전위는 0으로 두고 계면전위에서 용액 전위를 재구성한다. 셀별 전하율은 인접 ionic face-current 발산과 Faradaic current 차로 정하며, 그 charge continuity와 보존 성분 투영을 같은 RHS에서 확인한다. 출력에는 셀별 전하·계면전위·금속 기준 상대 용액전위·전류/화학 lineage가 담긴다.

현재 경계는 양 끝 절연, 고정 geometry, caller가 선언한 반응 면적·Cdl·kinetics다. hydraulic advection, 이동 geometry, caller current/source schedule과 혼용하지 않는다. 실제 물질의 Cdl·BV·전도도 적용성이나 실험 적합성을 계산기가 보증하지 않는다. 이 계약은 구현 범위이며 현장 물리 검증 완료를 의미하지 않는다. 요청 예시는 `examples/`의 BDF/Cdl 관련 예제 인덱스를 참조하고, 정확한 입력 필드와 출력 키는 등록된 v7 JSON Schema 및 Python contract를 기준으로 한다.

## 계산 한도와 실패

`maximum_total_rhs_evaluations`는 BDF RHS 호출 수, `maximum_total_stage_equilibrium_calls`는 셀별 평형 호출 수를 제한한다. `maximum_total_nested_equilibrium_iteration_work`는 각 셀 설정의 최대 outer × inner 질량작용 반복 수를 매 호출마다 보수적으로 예약해 제한한다. 선택 source projection에도 별도 상한을 둔다. 초과 시 계산을 중단한다. 내부 Davies/mass-action 평형 실패, 종 결과 ID/순서 불일치, 비양수 종 농도, 전류 폐합 실패, BDF 실패 또는 성분/reservoir ledger 잔차 초과는 미커밋 `needs_data` 결과가 된다. 요청, source/evidence, 내부 평형 호출은 digest 및 lineage chain으로 기록한다.

## 한계와 연결 방향

이 계산의 면 플럭스는 caller 확산계수/기하를 쓰며 기본 zero-current, 검토된 exact-knot caller-current schedule, 또는 review-gated stage mixed-potential 경로를 사용한다. 고체상 stage mode는 고정 부피/단일 액상/equilibrium 후보의 독립 계산 경로다. 유동/개구·가변 부피는 포함하지 않는다. 결과는 모델 한정 계산이며 재료 건전성 판단이나 자격 검증이 아니다.

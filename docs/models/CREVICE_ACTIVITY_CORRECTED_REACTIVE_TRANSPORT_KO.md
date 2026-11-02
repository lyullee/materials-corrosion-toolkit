# 활동도 보정 간극 반응-수송 이력

## 목적

`transport.crevice_activity_corrected_reactive_nernst_planck_1d`는 고정 격자 간극에서 caller 제공 활동도계수 장과 가역 반응 parameter를 사용해 다종 이온의 확산·전기이동·대류·반응을 함께 적분한다. 이전 activity-corrected API의 무반응 수송에 caller kinetic network를 더한 별도 모델이다.

## 계산 구조

각 species의 반응용 무차원 활동도는 (a_i=\gamma_i c_i/c^\circ)로 계산하고 반응 (j)의 국소 순 속도는

\[
r_j=k_{f,j}\prod_{i\in R_j} a_i^{\nu_{ij}}
-k_{r,j}\prod_{i\in P_j} a_i^{\nu_{ij}}.
\]

이 속도에 signed stoichiometry를 곱해 셀별 source 항을 만들고, 그 항을 유한체적 물질수지에 더한다. 활동도계수 시간 장은 로그 공간에서 knot 사이 보간한다. 수송 플럭스는 농도 기울기와 `ln(gamma)` 기울기 및 전위 기울기를 포함하며, 각 면 전류합은 국부 영전류식으로 닫는다. 셀 농도와 입구 이력은 시간 knot 사이 선형 보간하고 양의 rate coefficient는 로그 공간에서 보간한다. 이 보간은 knot별 detailed-balance rate ratio를 시간 구간에서도 보존하도록 한다. BDF solver는 수송과 반응을 하나의 상태계에서 함께 적분한다.

## 입력 계약 및 계보

`CreviceActivityReactiveTransportRequest`는 `CreviceActivityReactiveSpecies`, `CreviceActivityReactiveReaction`, `CreviceActivityReactiveTerm`을 사용한다. 종별 charge, 원소 조성, 초기 농도, 셀/시간별 gamma, 입구 gamma 및 diffusivity를 제공한다. 각 반응은 양의 forward/reverse rate schedule과 무차원 평형상수 schedule을 정확한 transport knot 순서로 갖고, 전체 reaction network digest는 정렬된 reaction records를 묶어야 한다. 개별 record는 ID/SHA와 허가 Evidence로 결합한다.

생성기 validator는 각 반응의 charge·원소 보존, (k_f/k_r=K) 관계, 시작 셀/입구 국부 전기중성, provider configuration digest, activity standard state 및 review flags를 확인한다. 모델 계산은 종별 inventory balance에 transport 입구 공급 및 시간 적분한 반응 source를 포함하고, 계산 허용오차를 벗어나면 `needs_data`로 닫는다.

## 한국어 Python 호출

```python
from matintegrity.crevice_activity_corrected_transport import (
    CreviceActivityReactiveTransportRequest,
    CreviceActivityReactiveSpecies,
    CreviceActivityReactiveTerm,
    CreviceActivityReactiveReaction,
    solve_crevice_activity_corrected_reactive_transport,
)

request = CreviceActivityReactiveTransportRequest(
    # geometry, aligned transport and chemistry histories, evidence and reviews
    ...
)
result = solve_crevice_activity_corrected_reactive_transport(request)
```

결과 이력은 종별 농도와 재고, 셀 전하 잔차, 각 반응의 gross-forward/gross-reverse/net rate, 종별 net reaction source, 재고수지 잔차 및 peak zero-current 잔차를 포함한다.

## 가정과 제한

- 간극 형상과 면적은 고정이며 하나의 액상만 존재한다고 caller가 지정한다. 유동장은 caller가 제공한 면속도이며 운동량식에서 만들지 않는다.
- gamma, 확산계수, equilibrium constants, kinetic coefficients는 모두 caller 공급 입력이다. 프로젝트는 전해질 parameter database나 실험 kinetic law를 포함하지 않는다.
- (k_f/k_r=K) 조건은 상세평형의 caller-record 대수 일관성 검사다. 이는 parameter의 실험 적합, 표준상태 정확성, 재료/온도 전이 또는 물리 qualification을 검증하지 않는다.
- 모델은 mass-action state integration이며 자동 산염기/착물 speciation, activity coefficient self-consistency, 수용액 후보 반응 탐색, 고체상 경쟁·침전/용해, nucleation, 표면 반응, 금속 손실 및 부식 susceptibility는 수행하지 않는다.
- 반응은 종 조성의 대수적 charge/element 보존을 요구하지만 실제 reaction mechanism 선택은 사용자 책임이다.
- solver가 0 이온 이동도에서 current closure를 만들 수 없거나 음수/비유한 농도, 비유한 kinetics, 과도한 current/charge 또는 inventory 잔차를 만나면 computed 결과를 내지 않는다.

## 출처와 검증 상태

Source IDs: `caller_crevice_activity_corrected_transport_species`, `caller_crevice_activity_coefficient_cell_time_fields`, `caller_crevice_activity_corrected_mouth_boundary_history`, `caller_activity_based_crevice_reaction_network`, `caller_crevice_activity_rate_reaction_records`, `finite_volume_activity_nernst_planck_with_local_mass_action`, `scipy_integrate_bdf`. 원자료와 kinetics parameter는 사용자가 권리·출처·적용범위를 확인해 제공한다. 이 구현은 독립적인 공개 method relationship을 코드화하며 문헌 문장이나 restricted parameter table을 복사하지 않는다.

테스트, 계산 실행, 실험 검증, packaging, HPC validation은 수행하지 않았다. 후속 검증은 gamma=1 dilute limit과 비교, detailed-balance stationary state, signed convection, reaction mass/charge closure, inventory cumulative source, face zero-current, overflow/negativity fail-closed 및 schedule/digest 변경으로 구성한다.

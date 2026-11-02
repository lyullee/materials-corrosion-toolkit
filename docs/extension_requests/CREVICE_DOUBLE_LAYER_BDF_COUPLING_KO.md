# 확장 요청: Crevice component-state BDF의 이중층 전하 연성

## 현재 경계

`integration.crevice_double_layer_charge_history`는 caller가 준 전위·활성면적 이력과 미분용량 표에서 저장전하 및 구간 평균 전류를 구한다. `integration.crevice_component_state_bdf`의 stage mixed-potential 모드는 보존 수용액 성분 상태를 적분하고, 매 trial에서 대수적 혼합전위를 다시 풀어 Faradaic branch 전류와 이온 이동전류만으로 charge balance를 닫는다. BDF 상태에는 계면전하/전극전위가 없으므로 두 결과를 schedule로 덧붙이면 일관된 전기화학 상태가 되지 않는다.

## 다음 계산 모델이 만족해야 할 요구사항

1. 각 반응면/cell에 계면 저장전하 `Q_dl` 또는 동등한 전위 상태를 명시한다. 미분용량 곡선 `C_dl(E)`를 쓰면 `Q_dl(E)=A_active ∫ C_dl(E) dE`와 기준전위·부호 convention을 계약으로 고정한다.
2. 전극전위, 계면전하, 수용액 전위와 Faradaic branch extent를 같은 BDF stage에서 함께 결정한다. caller가 지정한 외부 전위 이력은 별도의 potentiostatic mode로 둔다; 이를 혼합전위 unknown과 조용히 혼용하지 않는다.
3. 전류수지에는 확정된 sign convention을 적용해 내부 전류발산, Faradaic electron transfer, `dQ_dl/dt`를 모두 포함한다. 용액 성분/전하/원소수지와 전극·저장소 전하 장부를 각각 검산하고 같은 전하를 중복 계상하지 않는다.
4. 미분용량/전극 표는 고유 재료·환경·전위 기준, 단위, 면적 기준, 시험법, Evidence, license와 digests를 갖는다. Support 밖 전위는 extrapolate하지 않는다.
5. 가변 활성면적이나 움직이는 aperture를 포함하려면 면적 변화가 계면 저장전하에 미치는 효과와 geometry/volume update 순서를 같은 implicit state에 정의한다. 고정 geometry request에서 이를 추측하지 않는다.
6. solver-work, Newton/BDF RHS, chemistry projection 및 ledger budget을 명시한다. 수렴 실패나 balance 초과 시 interval을 부분 commit하지 않는다. Result에는 stage 전위·저장전하·capacitive/Faradaic/ionic currents, residuals, source/model revision과 input/result digests를 남긴다.
7. 먼저 분석해를 갖는 합성 capacitor와 독립 전하보존식을 사용한 소프트웨어 검증을 한다. 이어서야 material/environment matched 공개·승인 자료와 비교한다. Pt(111) DFT/electrolyte 후보를 carbon/alloy crevice의 parameter로 직접 전이하지 않는다.

## 기대 산출물

- 신규 versioned request/result 계약과 schema; 기존 fixed-geometry BDF caller의 명시적 backward-compatible mode 선택
- coupled RHS/DAE solver와 charge/element/component closure receipt
- 합성 analytical reference·solver refinement·budget exhaustion 사례 및 이후의 독립 데이터 qualification plan
- 사용자 안내서와 기존 separate-history API에서 coupled calculation으로 넘어가는 provenance-preserving adapter

이 요청은 계산 완료나 물리적 qualification을 뜻하지 않는다. 별도 계면 상태와 수지식이 구현·검증되기 전까지 구간 평균 용량전류를 Faradaic-only BDF request에 넣지 않는다.


## Implemented bridge and remaining request

MatIntegrity now has an opt-in, digest-bound caller schedule for exact-knot per-cell capacitive-current forcing in `integration.crevice_component_state_bdf`. It checks the ionic/Faradaic/capacitive charge balance and accumulates charge, but does not solve electrode potential or infer current from capacitance. Downstream consumers needing a monolithic BDF electrical state must still provide or co-develop a prescribed-potential Butler–Volmer kernel with charge-state derivatives, area evolution, and a reviewed implicit charge/current closure.

# 간극 용액의 경쟁 고체 평형 선별

## 목적

`chemistry.crevice_competing_solid_equilibrium`은 하나의 고정 부피 액상 상태와 caller가 열거한 중성 순수 고체 후보 집합을 대상으로, 각 상의 용해도곱에 맞는 평형 조성을 계산한다. 상은 하나씩 현재 공유 액상 상태와 평형화하고 이를 순환 반복한다. 요청된 모든 상에서 수렴과 상 존재/부재 보완조건을 확인할 때만 결과를 `computed`로 반환한다.

## 계산 관계

각 고체 반응은 caller가 제공한 양의 aqueous reactant stoichiometry를 사용한다. 고체 1 mol의 생성 진행량을 \(\xi_s\)라 하면 aqueous 종 재고는

\[
c_i^{new}=c_i^{old}-\nu_{is}\xi_s,\qquad n_s^{new}=n_s^{old}+\xi_s.
\]

각 후보 상의 무차원 이온 활동도곱은

\[
Q_s=\prod_i\left(\gamma_i c_i/c_i^\circ\right)^{\nu_{is}},
\]

이며, 고체가 존재하면 \(\ln(Q_s/K_s)\)가 지정 오차 안에 있어야 한다. 상이 없으면 용액은 해당 상에 대해 과포화되지 않아야 한다. 각 scalar phase update에서 침전 extent는 가장 먼저 고갈되는 reactant까지 제한하고, 용해 extent는 현재 고체 inventory까지만 허용한다. caller가 준 상 목록 순서대로 반복 sweep하며, 입력 순서는 digest에 고정된다. 반복 후 상태변화, phase 보완조건, 전하 및 aqueous/solid extent 재고 폐쇄가 모두 허용오차 안에 있어야 결과를 commit한다.

## 입력과 추적성

- 모든 수용액 종의 초기 농도, 전하, 원소 구성, 기준농도, 고정 활동도계수 및 digest-bound record를 입력한다.
- 각 상에는 원소 균형 반응식, 초기 상 몰농도, 무차원 \(K_s\), 온도/표준상태에 적용되는 상수 record ID·SHA와 Evidence를 제공한다.
- 모든 후보 반응은 중성 순수 고체를 만들며 원소와 전하가 보존되어야 한다. 초기 액상 전하 잔차도 입력 허용오차 이내여야 한다.
- 모든 활성 phase 및 공유 용액의 완전성, 순간 평형 가정과 계산 사용권을 caller가 검토해야 한다.
- 전체 입력의 canonical digest와 상별 상수/record digest가 결과 lineage에 포함된다.

## 한계와 실패 조건

- 계산 대상은 caller가 선언한 유한 상 목록뿐이다. 목록 밖 상의 자동 발견, 수용액 종/speciation 생성, pH·이온강도 반복 및 활동도계수 모델링은 하지 않는다.
- 고정 온도·부피·활동도계수·표준상태를 사용한다. 열역학 데이터의 출처, 적용 범위와 상수의 단위 없는 표준 상태는 caller 책임이다.
- 순차 active-set 반복은 global Gibbs-energy 최소화나 전역 상 안정성 증명이 아니다. 반복 한도 내 수렴 실패, 존재 상의 포화도 잔차 초과, 부재 상의 과포화, 음수 inventory 또는 전하 불균형이면 결과를 commit하지 않는다.
- 핵생성 지연, 준안정상, 유한 반응 속도, 기체상, 흡착, 다공성 침전, 벽 위치, 수송, 금속 용해, 간극 변화, 부식률 및 안전 수용은 계산하지 않는다.

이 모델은 기존 단일 고체 평형 해석을 다상 후보가 공유하는 용액 상태로 확장하는 제한된 계산이다. 다상 열역학·speciation·kinetics 실험 검증을 대신하지 않는다.

## Python API

```python
from matintegrity.crevice_competing_solid_equilibrium import (
    CreviceEquilibriumAqueousSpecies,
    CreviceCompetingSolidPhase,
    CreviceCompetingSolidEquilibriumRequest,
    evaluate_crevice_competing_solid_equilibrium,
)
```

Source IDs: `caller_competing_solid_aqueous_state`, `caller_competing_solid_equilibrium_constants`, `bounded_sequential_active_set_multi_solid_equilibrium`. 마지막 ID는 코드가 수행하는 수치 절차의 설명이며 외부 과학적 권위나 독립 실험 근거가 아니다.

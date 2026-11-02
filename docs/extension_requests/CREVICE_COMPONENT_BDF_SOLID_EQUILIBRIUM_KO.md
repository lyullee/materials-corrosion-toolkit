# Crevice component-state BDF의 고체상 평형 연성 요청

## 구현 상태 — bounded opt-in API 추가, 검증 대기

`CreviceComponentStateBDFRequest.solid_equilibrium_mode="instantaneous_solid_equilibrium"` 경로가 구현됐다. 기존 aqueous-only mode가 default이며 별도 의미로 유지된다. 새 mode는 cell/material/metallurgy/environment/time/clock/T가 digest-bound된 per-cell phase set과 고체를 포함하는 total component state를 받아 각 BDF trial에서 standalone partition API를 호출한다. Aqueous concentrations만 NP/Faradaic flux 계산에 쓰고, total component state를 적분한다. Exact-knot solid/aqueous histories와 component/element/current ledgers, RHS 전체에 걸친 partition/active-set/bisection/nested equilibrium budgets를 출력한다. 이 경로는 계산 코드이며 시험·물리 검증·qualification 증거가 아니다.

## 목적

현재 `integration.crevice_component_state_bdf`는 고정 부피 cell의 보존 성분 재고를 적분하고, 매 BDF stage에서 그 재고를 전부 수용액 성분 제약으로 사용해 Davies/mass-action speciation을 계산한다. 기존 `chemistry.crevice_competing_solid_equilibrium`은 주어진 수용액 농도와 활동도에서 고체 평형을 계산하지만, 그 결과를 성분 재고 BDF의 stage RHS에 포함하지 않는다. 두 계산을 순차 호출하는 것으로는 intrastage 연성이 되지 않는다.

## 권장 상태/방정식

새 opt-in 모드는 BDF가 `total_component_inventory`를 보존 상태로 적분하도록 한다. 이 총량은 액상과 선택된 고체상에 배분된 합계다. 각 trial stage에서 액상 성분 목표는

`n_aq,i = n_total,i - Σ_j ν_component,i,j * n_solid,j`

로 구성한다. 농도 표준상태와 액량 변환을 명시한 뒤 이 액상 총량으로 기존 mass-action/Davies 계산을 수행한다. 고체상 j가 존재하면 caller 제공 활동도 곱 `Q_j`가 해당 온도·매질의 `K_j`에 맞아야 하고, 부재상은 과포화되지 않아야 한다. active-set 해는 `n_solid,j >= 0`, `log(Q_j/K_j) <= tolerance`, 존재상 포화 잔차 이내 조건을 동시에 만족해야 한다. 음수 액상 성분을 clip하거나 수렴 실패 때 부분 결과를 반환하면 안 된다.

NP flux는 평형 분배로 얻은 액상 species 농도에서 계산하지만, 그 flux를 적분해 총 성분 재고를 갱신한다. 그러므로 각 cell에서 `liquid component + solid component` 보존량을 추적해야 한다. Faradaic source도 액상/고체 분배 후 총 성분 방정식에 한 번만 적용하고, 외부 reservoir 원소·전하 ledger는 기존 검사를 유지한다.

## 요청 입력

- caller가 지정한 전체 반응/고체 후보 집합과 상별 용해도식, 고체 조성, 액상 반응물 계수
- 온도, 활동도 표준상태, 수용액 부피와 모든 provider record의 revision/digest/Evidence
- BDF 시작점의 총 성분 재고(고체 포함 여부를 schema version에 고정)
- 후보 집합 완전성, 평형 가정, kinetic barrier 무시, provider 적용성에 대한 별도 review flags
- stage RHS/phase 수/active-set iteration/inner chemistry 호출을 위한 총 계산 예산
- active-set 순서와 초기 추정치가 다른 경우의 수렴/유일성 판단 기준

기존 `initial_component_inventory`는 aqueous-only 의미를 보존한다. 총량 해석은 새 schema version 또는 명시적인 별도 입력으로 제공해야 하며 기존 결과의 의미를 조용히 바꾸면 안 된다.

## 구현 경계

이 모드는 caller가 제공한 유한 후보상에 대한 국부 순간평형이다. 핵생성, 유도시간, meta-stability, scale adhesion, moving boundary, 다공성상 확산, 열방출 및 균열/벽면 반응은 별도 모델이다. `crevice_competing_solid_equilibrium`의 concentration-level helper를 그대로 BDF에 호출하는 것은 허용되지 않는다. 먼저 component-to-species stoichiometric map이 모든 상에서 성분·원소·전하를 보존하는지 증명하고, 결과에 stage별 고체량, aqueous species, 포화 잔차, 보존 ledger, solver work 및 input/result digest를 남겨야 한다.

## 필요한 검증 단계

1. 이상용액의 단일 1:1 염에서 닫힌형 해와 평형분배 비교
2. 초기 액상/고체량이 다른 동일 총량 입력의 동일 평형상태 수렴 확인
3. 경쟁상 두 개에서 상 활성/비활성 전환과 물질수지 확인
4. 용해도곱을 높이거나 낮춘 단조성 및 과포화 부재 확인
5. BDF 수송 없이 총량 보존, NP 수송 포함 시 경계/면 전달 폐합
6. active-set 순서 변경, 계산량 한도 도달, 표준상태 불일치, 미포함 성분에서 fail-closed 확인
7. 독립 공개 자료의 재료·온도·매질 적용성이 확인된 뒤에만 물리 비교 및 calibration 검토

별도 one-cell computational API `chemistry.crevice_component_solid_partition`가 total component inventory를 액상과 유한 caller phase 후보 사이에 분배한다. 이 API는 기존 Davies/mass-action solver를 phase 재분배마다 호출하고 component closure와 active/absent complementarity를 검사한다. Caller phase order에 따른 sequential active-set이며 global Gibbs-energy minimum이나 해 유일성을 증명하지 않는다. 이를 `integration.crevice_component_state_bdf`의 opt-in stage RHS에 연결했으나, 수치 시험과 독립 검증은 아직 수행하지 않았다.

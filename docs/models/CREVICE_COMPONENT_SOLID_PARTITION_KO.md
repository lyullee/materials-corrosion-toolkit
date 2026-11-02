# Crevice 총성분–고체상 평형 분배 API

## 목적과 API

`chemistry.crevice_component_solid_partition`는 한 고정 부피 셀의 총 보존성분 몰수를 caller가 지정한 수용액 조성 및 유한 고체상 후보 집합으로 분배한다. 전체 입력은 aqueous + solid 합계이며, 기존 `CellAqueousEquilibriumTemplate`의 Davies/mass-action 계산을 각 상 재분배 후 다시 호출한다.

```python
from matintegrity.crevice_component_solid_partition import (
    CreviceComponentSolidPartitionRequest,
    solve_crevice_component_solid_partition,
)

result = solve_crevice_component_solid_partition(
    CreviceComponentSolidPartitionRequest(
        assessment_id="unit-17-equilibrium-snapshot",
        cell=cell_template,
        total_component_inventory=component_totals_including_solid,
        phase_candidates=reviewed_phase_records_with_zero_seed_inventory,
        total_inventory_includes_all_candidate_solids_reviewed=True,
        candidate_phase_set_complete_for_declared_scope_reviewed=True,
        equilibrium_constants_and_activity_basis_applicable_reviewed=True,
        instantaneous_equilibrium_and_no_nucleation_barrier_reviewed=True,
        computational_use_authorized=True,
    )
)
```

`phase_candidates`는 기존 `CreviceCompetingSolidPhase` typed record를 사용한다. 해당 record의 Ksp·조성·반응식 digest/Evidence는 유지하며, 초기 고체량은 0이어야 한다. API는 dimensionless activity의 `dimensionless_molarity_1_mol_L` standard state만 받는다. 총성분 inventory가 고체를 포함하므로 API가 phase amount를 active-set 해로 결정한다. 성분/상 후보의 순서, 반응계수, Ksp 및 solver budget은 request digest에 포함된다.

## 계산 절차와 수지

각 상 후보에서 수용액 반응물 계수와 `ConservedAqueousComponent` 매핑을 곱해 상 1 mol당 소모 성분 계수 (A_{ij})를 구성한다. 상 반응의 원소·전하 폐합이 확인되지 않거나 선언된 성분 기저에 매핑되지 않으면 실패한다. 액상 성분 목표는

`n_aq,i = n_total,i - Σ_j A_ij n_solid,j`

로 계산한 뒤 solution volume으로 나눠 Davies/mass-action solver에 넣는다. 각 고체상에서 `Q = Π a_i^ν_i`를 계산한다. 존재상은 `log(Q/Ksp) = 0` 허용오차 안에, 부재상은 `Q/Ksp <= 1`이어야 한다. 상별 재분배는 caller가 선언한 상 순서대로 bounded bisection으로 수행하고, 경쟁상 active-set sweep, aqueous solver 호출, nested equilibrium iteration work에 각각 명시 상한을 둔다. 이는 유한 후보상의 active-set 해이지 global Gibbs energy minimum 탐색은 아니다. 다중 가능한 상 조합에서 상 순서 민감성이 남으면 결과를 독립 검토해야 한다. 예산 초과, 비양수 액상 성분, 상 미수렴 또는 closure 실패 시 `needs_data`를 반환하고 partial 결과는 commit하지 않는다.

최종 출력은 액상 및 고체 분배, 전체 총량과의 component residual, 액상 species, 상별 포화비/상태, active-set sweep 수와 equilibrium 호출 및 누적 nested-work 상한을 기록한다. `committed=True`는 선언된 계산 경계 안에서 수지가 닫혔다는 뜻이며, global thermodynamic stability, 상 후보 완전성이나 실제 재료의 Ksp 적용성을 독립 검증했다는 뜻은 아니다.

## 범위 한계

- 고정 부피·단일 액상·caller 정의 고체상 후보에 대한 순간평형만 계산한다.
- 핵생성 장벽, 준안정상, 반응속도, 부착/탈락, 다공성 scale 내부 전달 및 이동경계는 포함하지 않는다.
- 단독 API와 component-state BDF opt-in hook이 연결되어 있다. BDF 모드에서 total component 상태가 각 trial에 이 API를 호출하고 aqueous NP/Faradaic flux와 solid/element ledger를 만든다. 기본 aqueous-only mode는 별도 경로로 보존한다.
- 물리 검증·qualification·수치 테스트는 후속 검증 계획에 남는다.
- Sequential phase ordering may select one admissible local active set; no global Gibbs-energy minimization or proof of uniqueness is provided.

## 후속 BDF 연성 검증

구현/확장 상태는 [CREVICE_COMPONENT_BDF_SOLID_EQUILIBRIUM_KO.md](../extension_requests/CREVICE_COMPONENT_BDF_SOLID_EQUILIBRIUM_KO.md)에 기록했다. 1:1 이상 용해도 곡선의 해석해, 초기 상태 불변성, 경쟁상 전환, active-set 순서, 수송 포함 total/component/element/current ledger는 후속 검증 대상이며 현재 검증하지 않았다.

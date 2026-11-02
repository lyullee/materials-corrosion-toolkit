# Crevice 밀폐 수용액 batch 평형 API

`chemistry.crevice_closed_batch_aqueous_equilibrium`은 초기 종별 몰 inventory와 고정 용액 부피로부터 caller가 지정한 보존 성분 목표를 계산하고, 기존 Davies–mass-action 반복 solver로 단일 액상 수용액 평형을 구한다. 명시적 성분 ledger 매핑을 실제 닫힌 batch 계산에 사용하는 독립 API다.

## 입력과 보존 규약

요청 모델은 `CreviceClosedBatchAqueousEquilibriumRequest`, 평가 함수는 `evaluate_crevice_closed_batch_aqueous_equilibrium`, ModelSpec은 `specifications()`로 제공한다. 각 species의 초기 몰수와 용액 부피를 입력한다. `conserved_component` constraint 목표는 성분 사상 계수와 초기 종 inventory의 곱을 합산해 mol/L로 만들고, `fixed_target` 목표는 입력값을 보존한다. `charge_neutrality`는 종 전하수와 정확히 일치하는 0 목표 행이어야 하며, 초기 전체 전하 inventory도 caller 허용오차 안에서 0이어야 한다.

모든 constraint ID를 정확히 한 번 역할에 배정해야 한다. 각 conserved component 사상은 대응 constraint 행과 일치하고 선언된 모든 반응에서 보존되어야 한다. 기존 Davies 요청의 증거, 활동도 표준상태, 온도, 단일 액상 범위 검토를 그대로 요구하며, nested outer/inner 반복 상한의 곱을 별도 `maximum_total_equilibrium_iterations` 상한으로 제한한다.

## 결과와 실패

요청 digest, 재구성된 평형 입력 digest, inner 결과 digest, 최종 species 평형, 성분별 초기/최종 inventory와 폐합 잔차를 기록한다. 보존 성분 목표가 양수가 아니거나 초기 전하가 불일치하거나 내부 평형 solver가 계산 완료를 반환하지 않거나 최종 성분 잔차가 허용치를 초과하면 결과를 커밋하지 않는다.

## 한계

계산 범위는 caller 지정 수용액 종·반응·Davies 계수와 고정 부피의 닫힌 batch다. 고체 전이/침전, 기체 교환, reservoir, 열역학 온도 변경, 수송, Crevice BDF 결합, 부식 속도 또는 재료 수용 판정은 포함하지 않는다. ModelSpec은 중앙 registry에 연결했으며 공유 생성 catalog/API 문서는 이 증분에서 건드리지 않았다.

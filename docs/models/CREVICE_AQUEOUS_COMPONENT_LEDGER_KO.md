# Crevice 수용액 보존 성분 ledger 선행 API

`integration.crevice_aqueous_component_ledger`는 수용액 종 기준의 구간 inventory, 면 전달량 및 source를 사용자가 정의한 보존 성분 기준 ledger로 투영한다. 보존 성분을 운반하는 상태 API를 향후 설계할 때 기존 종 inventory를 손실 없이 연결하는 독립 계산 계약이다.

## 범위

- 입력된 시작/종료 종 몰수, 셀 경계별 signed 면 전달량, 셀별 source 몰수를 선형 사상으로 보존 성분 몰수·전달량·source로 바꾼다.
- 각 보존 성분과 셀에서 `종료-시작 = 왼쪽 면 전달-오른쪽 면 전달+source`를 확인하고, 성분별 경계 순전달과 전체 구간 잔차를 기록한다.
- 제약 역할을 완전하게 지정해야 한다. 모든 수용액 질량작용 제약은 정확히 하나의 `conserved_component`, `fixed_target`, `charge_neutrality` 역할을 가져야 한다.
- 보존 성분 제약 행의 계수는 성분-종 사상과 정확히 같아야 한다. 그 사상은 선언된 모든 수용액 반응에서 보존되어야 한다.
- `charge_neutrality` 행 하나를 필수로 두며, 종 전하수와 정확히 일치하고 목표가 0이어야 한다.

## 입력과 검토

주요 계약과 함수는 `CreviceAqueousComponentLedgerRequest`, `evaluate_crevice_aqueous_component_ledger`, `specifications()`이다. 종별 ledger 배열은 질량작용 시스템의 종 ID를 각각 정확히 한 번 포함한다. 시작/종료 inventory는 비음수이고, 면 전달량은 왼쪽에서 오른쪽으로 양수이며, source 전달량은 수용액으로 들어오는 방향이 양수다.

호출자는 제약 역할, charge scope, 성분 사상 및 반응 보존성, 면 방향/source 부호, 계산 사용 권한을 명시적으로 검토해야 한다. `maximum_projection_operations`는 성분 계수와 셀/면 수로 산정한 상한을 검사한다. 반복 계산은 없다.

## 결과와 실패

요청 및 질량작용 시스템 digest, 역할표, 각 성분의 시작/종료 inventory, face transfer, source, 셀 잔차, 허용 잔차와 global 잔차를 반환한다. 어느 성분/셀이라도 `absolute_component_closure_tolerance_mol + relative_component_closure_tolerance × scale` 범위를 벗어나면 `needs_data`이며 `committed=false`다. 계약의 종 식별자·배열 차원·역할 분할·전하 행·성분 계수·반응 보존 검증이 맞지 않으면 입력을 거부한다.

## API 한계

이 모듈은 평형·종분화·활동도·고체 전달을 풀지 않고, 기존 Crevice BDF solver의 상태나 방정식을 바꾸지도 않는다. 입력 ledger의 수치 수지를 투영하고 확인하는 독립 API다. 결과는 계산 스크리닝이며 검증이나 건전성 판정이 아니다. 모델 식별자는 `integration.crevice_aqueous_component_ledger`, 계약은 `matintegrity.crevice_aqueous_component_ledger.v1`이다.

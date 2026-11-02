# 크리비스 국소 종분화 공간 재고 원장

## 용도

`integration.crevice_local_speciation_volume_ledger`는 이미 계산된 크리비스 수송 상태와, 각 셀·시각·기하 경계별로 별도 실행한 수용액 질량작용 결과를 하나의 공간 보존 원장으로 묶습니다. 이 API는 수송이나 종분화를 다시 계산하지 않습니다. 셀을 평균 내지 않고 모든 셀 농도와 체적을 유지하면서, 각 종의 몰 수와 전하 당량 및 원소 수지를 산출합니다.

## 입력 순서

1. `CreviceTransportCompositionBridge`에 캠페인 요청과 계산된 campaign result를 고정하고 `summarize_crevice_transport_composition`을 실행합니다.
2. 결과의 각 `knot_summaries` 항목을 시간과 `geometry_side`별 종분화 작업 단위로 취급합니다. 형상 변경 시 `left_pre_remap`과 `right_post_remap`은 별개 상태입니다.
3. 각 작업 단위의 셀마다 독립적으로 `AqueousMassActionSystem`을 구성하고 이미 계산된 결과를 전달합니다. 수송 농도에서 질량작용 선형 제약으로 가는 화학량론 변환은 사용자 검토와 책임 범위입니다.
4. 셀 결합 다이제스트는 다음 헬퍼로 계산해 레코드에 넣습니다.

```python
from matintegrity.crevice_local_speciation_ledger import (
    transport_cell_context_digest,
)

cell_digest = transport_cell_context_digest(knot_summary, cell_index=0)
```

5. `CreviceLocalSpeciationLedgerRequest`에 transport summary result와 전체 셀별 결과를 넣고 `assemble_crevice_local_speciation_ledger`를 호출합니다.

## 집계 관계

질량작용 결과가 내는 종 농도가 `mol/L`, 크리비스 셀 용액 체적이 `m3`일 때, 원장은 다음 관계로 셀별 재고를 계산합니다.

\[
n_{i,c}=C_{i,c}\,V_c\,1000
\]

여기서 1000은 `m3`를 `L`로 바꾸는 계수입니다. 전하 당량은 `Σ(z_i n_i)`, 원소 원자 몰수는 `Σ(a_{e,i} n_i)`로 단순 집계합니다. 이 결과는 각 셀 내부 종분화 계산의 집계 정보이며, 셀 간 혼합이나 전하 중성 조건을 새로 적용하지 않습니다.

## 경계와 실패 처리

- transport result와 mass-action result는 각각 입력 다이제스트로 원 요청에 결합되어야 합니다.
- 각 mass-action 입력/결과 쌍은 셀 상태 다이제스트에 대응되어야 하며, 이 대응은 호출자가 검토하고 표시합니다.
- 각 knot에 모든 셀 결과가 있어야 해당 시각을 기록합니다. 첫 계산 누락·실패 이후에는 앞서 완료된 전체 knot만 반환합니다.
- 기하 변경 직전·직후, 서로 다른 시각, 다른 셀은 별도 행입니다. 시간을 따라 재고를 누적 합산하지 않습니다.
- 부피는 용액 부피로 해석되며 공극률, 용매 질량, 물 수지, 침전·용해, 계면 반응은 추론하지 않습니다.
- 자동 입력 변환, 시간 보간, 상평형·반응속도 결합, 감육률, 수용성 판정 및 위험 확률을 제공하지 않습니다.

## 인터페이스 메타데이터

- Model ID: `integration.crevice_local_speciation_volume_ledger`
- Source ID: `caller_crevice_local_speciation_volume_ledger`
- Schema version: `matintegrity.crevice_local_speciation_ledger.v1`
- 계산 성격: caller가 제공한 국소 종분화 결과의 결정론적 집계
- 적합성: `user_model`; 현장 정확도 또는 재료 건전성 자격을 뜻하지 않음

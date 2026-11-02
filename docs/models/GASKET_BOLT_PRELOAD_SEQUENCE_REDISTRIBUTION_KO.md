# 가스켓 조인트 볼트 체결 순서에 따른 탄성 하중 재분배

## 목적

`fabrication.gasket_bolt_preload_sequence_redistribution`은 caller가 제공한 joint-specific 탄성 상호작용 계수 행렬과 순서화된 단일 볼트 체결 작업으로 각 작업 후 볼트별 축방향 preload 벡터를 계산합니다. 단일 작업에서 직접 조이는 볼트의 preload 증가량을 입력하고, 행렬의 해당 열이 다른 볼트에 전달되는 하중 변화를 정의합니다.

볼트 순서는 `ordered_bolt_ids`와 행렬의 행·열 순서가 동일해야 합니다. 각 작업은 고유 operation ID, pass ID, 조이는 볼트 ID 및 양의 `applied_preload_increment_N`를 가집니다. 초기 preload는 해당 조립 순서의 시작 상태입니다. 반복 pass는 같은 bolt ID를 다시 지정해 표현할 수 있습니다.

## 계산 관계

입력 행렬의 계수 `H[i,j]`는 bolt `j`를 직접 조일 때 bolt `i`의 축력 변화가 직접 적용 증가량에 비례하는 정도를 나타냅니다. 직접 조이는 bolt의 대각값은 1이어야 합니다. 각 단일 볼트 작업에서 아래 벡터 업데이트를 순서대로 수행합니다.

```text
delta_F_i = H[i, j] * applied_increment_j
F_i_after = F_i_before + delta_F_i
```

초기 상태와 모든 작업 뒤의 preload 이력을 반환하고, 마지막 상태의 산술평균, 모집단 표준편차, 변동계수, 최소·최대 및 범위를 요약합니다. 이는 결정론적인 preload 재분배 계산이며 공분산 또는 통계적 신뢰구간을 계산하지 않습니다.

## 데이터와 적용 절차

1. 현재 flange/gasket/bolt 구성, contact regime, 체결 방법 및 모델 지원 범위에 맞는 상호작용 행렬을 FE 해석 또는 시험 provider에서 확보합니다. 이 API는 계수 행렬을 계산하거나 다른 joint로 전이하지 않습니다.
2. 행렬 데이터는 provider ID, revision, record ID와 함께 canonical digest를 만듭니다. digest 입력에는 joint ID, bolt 순서, provider identity/revision 및 전체 행렬이 포함되어야 합니다.
3. 각 작업의 적용 preload 증가량은 공구 토크를 이 API에서 변환하지 않고 caller가 정량화해 입력합니다. target force와 실제 적용 증가량의 차이는 별도 측정/불확실도 자료에서 관리해야 합니다.
4. 부호 convention, bolt order, matrix applicability, 동일 configuration에서의 선형 중첩, target increment 근거, 계산 사용권 검토를 완료해야 계산됩니다. 누락된 검토는 `needs_data`입니다.
5. 업데이트된 bolt preload 중 하나라도 음수가 되거나 수치 결과가 유한하지 않으면 `out_of_scope`입니다. 결과를 실제 gasket seating stress, flange stress 또는 leakage 상태로 해석하지 않습니다.

## 핵심 적용 한계

- 동일 상호작용 행렬을 각 pass와 작업에 고정 적용하며, 단일 볼트의 양의 preload increment만 입력받습니다. 여러 볼트를 동시 조이는 작업은 현재 계약에 없습니다.
- 선형 탄성 중첩과 동일 contact/configuration 조건을 전제로 합니다. 접촉 영역 변화, gasket 비선형성, seating/relaxation, flange plasticity, flange 회전, bolt bending 또는 각 작업 후 geometry update는 반영하지 않습니다.
- 행렬은 caller 공급 결과이며 이 모듈의 결과가 아닙니다. geometry·경계조건·mesh·재료·gasket 상태·실제 조임 방법에 맞는 provider 검증이 필요합니다.
- 토크와 preload의 상관·분산, 공구 교정, bolt 마찰, 작업자 편차, 확률분포, 신뢰구간 및 failure probability는 생성하지 않습니다.
- 최종 preload vector는 기존 joint equilibrium solver에 넘길 초기 상태 후보일 수 있으나, 그 연결만으로 초기 gasket reaction과 force balance가 보장되지 않습니다.
- 이 계산은 seal acceptance, 설계코드 적합성, fatigue life, flange local stress 또는 재료 qualification 판정이 아닙니다.

## 독립 참고자료

- L. Zhu, A.-H. Bouzid, and J. Hong, “Numerical and Experimental Study of Elastic Interaction in Bolted Flange Joints,” *Journal of Pressure Vessel Technology*, 139(2), 2017. 탄성 상호작용 계수와 flange/gasket assembly의 수치·시험 검토 맥락만 참고합니다. [DOI: 10.1115/1.4035316](https://doi.org/10.1115/1.4035316)
- I. Coria, M. Abasolo, J. Aguirrebeitia, and I. Heras, “Study of bolt load scatter due to tightening sequence,” *International Journal of Pressure Vessels and Piping*, 182, article 104054, 2020. tightening 순서에 따라 하중 산포가 변할 수 있다는 계산 배경만 참고합니다. [DOI: 10.1016/j.ijpvp.2020.104054](https://doi.org/10.1016/j.ijpvp.2020.104054)
- M. Abid and Y. M. Khan, “The effect of bolt tightening methods and sequence on the performance of gasketed bolted flange joint assembly,” *Structural Engineering and Mechanics*, 46(6), 843–852, 2013. 가스켓 조인트의 체결 전략과 상호작용 맥락을 참고합니다. [공개 저널 페이지](https://www.techno-press.com/papers/15078)

참고자료에서 계수, 표, 예제 수치 또는 문장을 복사하지 않았습니다. 입력 matrix와 작업 증가량은 사용자 소유 또는 사용 허가가 확인된 공급자 자료여야 합니다.

## API 계약

- 모듈: `matintegrity.models.gasket_bolt_preload_sequence_redistribution`
- 모델 ID: `fabrication.gasket_bolt_preload_sequence_redistribution`
- 스키마: `matintegrity.gasket_bolt_preload_sequence_redistribution.v1`
- 입력: `GasketBoltPreloadSequenceRedistribution`
- 작업 입력: `GasketBoltTighteningOperation`
- 평가기: `evaluate_gasket_bolt_preload_sequence_redistribution(request)`
- 모델 메타데이터: `specifications()`
- source ID: `caller_joint_specific_elastic_interaction_matrix`, `caller_ordered_bolt_tightening_operations_and_preload_increments`, `sequential_linear_superposition_of_elastic_bolt_load_transfer`
- 런타임 외부 라이브러리 의존성 없음. 수치·물리 검증과 패키지 작업은 아직 실행하지 않았습니다.

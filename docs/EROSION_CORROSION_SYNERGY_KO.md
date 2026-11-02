# 침식·부식 손실 성분 장부

`degradation.erosion_corrosion_synergy_decomposition`는 동일 재료·유체·형상·물리 범위에서 caller가 제공한 순수 침식, 순수 부식, 결합 환경의 두께 손실률을 시간구간별로 맞춰 기록한다. 기본 결과의 상호작용 잔차는 아래 프로젝트 정의를 따른다.

`S_residual = R_combined - R_erosion,pure - R_corrosion,pure`

잔차는 signed 값으로 보존한다. 음수는 상쇄 관측을 뜻할 수 있으므로 0으로 자르지 않는다. 별도의 `corrosion_during_erosion` 측정값을 제공하면 결합 손실 중 기계 성분을 `R_combined - R_corrosion,during`으로 두고, 순수 기준 대비 침식 가속 부식 및 부식 가속 침식 성분도 계산한다. 이 분해는 정해진 측정량 장부이며 특정 파괴 기구를 판정하지 않는다. 한 실험 연구는 전위·유속 조건에 따라 순수 침식과 강화된 부식의 합으로 관측값이 설명되는 구간과 침식 상호작용이 나타나는 구간이 달라질 수 있음을 보고한다. [Zhou, Stack & Newman (1996), DOI 10.5006/1.3292087](https://doi.org/10.5006/1.3292087).

## 입력 계약

- 모든 component rate는 같은 caller 지정 두께손실률 basis와 `m/s`를 사용한다.
- 각 provider record의 시작·종료 시간이 상위 구간과 정확히 일치해야 한다.
- 각 rate record는 provider/revision, record ID, SHA-256 및 일치하는 Evidence를 포함한다.
- rate record의 재료조건·유체조건·형상·물리범위·위치는 assessment 전체에서 같아야 한다.
- 구간은 순서가 있고 겹치지 않아야 한다. 빈 시간대는 보간하지 않는다.
- `corrosion_during_erosion`이 일부 구간에만 있으면 해당 구간별 분해 결과는 제공하지만, 전체 구간 분해 가능 플래그는 false다.
- 모든 구간 rate를 상수로 보고 duration을 곱해 loss를 적분한다. 실제 시간 변화는 더 잘게 나눈 관측 구간으로 caller가 표현한다.
- 각 rate record에 하한·상한을 함께 넣고 `deterministic_rate_bounds_reviewed=True`로 검토하면 보수적 구간 산술로 loss 및 residual synergy 범위를 전파한다. 입력한 성분별 범위 사이 상관관계는 가정하지 않으므로 결과는 통계적 confidence interval이나 확률이 아니다. 어느 구간에서든 핵심 성분 범위가 누락되거나 review가 열려 있으면 집계 범위는 제공되지 않는다. 침식 중 부식률이 별도로 제공되고 네 성분 모두 bounds를 갖는 경우 interaction component bounds도 구간별로 출력된다.

## 한계와 사용

rate의 데이터 정합성, 측정 방법, 반복시험 불확실성, 순수 시험과 결합 시험 간 동등조건은 caller가 검토한다. 모델은 실험자료를 보정하거나 누락 성분을 추정하지 않는다. CFD wall shear, 입자 궤적, 보호막·재료 제거 기구, 확률, 잔여수명, 허용기준 및 재료 자격화도 계산하지 않는다. 합성 예제의 수치는 wiring을 위한 임의 값이며 재료 데이터가 아니다.

선택적으로 digest-linked 초기 벽두께, 기준 시각, 위치 및 caller 요구 최소두께를 입력하면 모든 손실 구간이 기준 시각부터 빈 구간 없이 이어지는지 확인하고, 구간별 결정론적 thickness margin을 출력한다. rate bounds가 완전하면 margin bounds도 함께 계산해 한계 위/아래/교차를 구별한다. 첫 point·가능·확정 교차는 공급된 interval bracket으로만 반환하고 구간 내 root를 보간하지 않는다. 이는 FTA나 신뢰성 모듈에 전달할 수 있는 결정론적 한계상태 자료이며, 그 자체로 사건확률이나 failure probability를 만들지 않는다. 연속 clock, 위치·재료·형상 mismatch 또는 열려 있는 review gate에서는 limit-state adapter만 `needs_data` 상태가 된다.

기준 시점의 실측 두께가 이미 요구 최소두께 이하인 경우도 별도로 표시한다. `initial_remaining_thickness_limit_state_margin_m`은 손실 누적 전의 `measured - required`이며, `initial_state_at_or_below_required_thickness`가 true면 최초 관측 상태부터 한계 아래 또는 한계와 같다. 이 초기 상태 표시와 이후 interval crossing bracket을 혼동하지 않는다.

레지스트리 호출은 `ModelRegistry.run("degradation.erosion_corrosion_synergy_decomposition", request, context)` 또는 JSON의 `run_json()`을 사용한다. 전체 schema와 입력 필드는 모델 참조에 포함된다.

# 틈 개구 변화의 체적변위 유량 ledger

## 목적

`matintegrity.crevice_aperture_displacement_flow.v1`은 digest로 고정한 기존 planar-slit aperture history를 입력으로 받아, 인접 geometry 절점 사이에서 셀 체적이 변할 때 비압축성 액체가 만족해야 하는 1차원 연속방정식상의 단면 유량을 계산한다.

이 계산은 벽면 소모량에서 개구를 새로 추정하지 않는다. 이미 계산된 cell aperture/volume history를 읽고 그 결과를 질량보존 형태의 부피 유량으로 변환한다. 일반 pressure-driven hydraulic flow, transient momentum solver 또는 moving-boundary transport solver와는 다른 계산이다.

## API

```python
from matintegrity.crevice_aperture_displacement_flow import (
    CreviceApertureDisplacementFlowRequest,
    evaluate_crevice_aperture_displacement_flow,
)
```

요청은 다음을 포함한다.

- `geometry_history_result`와 `geometry_history_result_sha256`: 완전한 computed `PlanarSlitApertureHistory` 결과 또는 그 결과를 담은 JSON envelope
- `geometry_id`, 자산·위치·시간 기준 식별자
- blind end/single mouth, 비압축성 액체, 1차원 셀 연속성, 절점 사이 선형 체적 변화, displacement-only 결과 해석에 대한 별도 리뷰

geometry 결과의 SHA-256이 정확히 맞아야 한다. 원 geometry result는 computed여야 하고, 모든 상태의 cell aperture/volume/face area가 유한 양수여야 한다. history는 `t=0`에서 시작해 caller가 준 순서로 엄격히 증가해야 한다. ledger 크기는 `interval 수 × cell 수 ≤ 1,000,000`으로 제한한다.

## 계산

입구에서 막힌 끝을 향하는 축을 양수로 정의한다. 셀 `j`의 단위시간당 부피 변화율을 `dV_j/dt`, 셀 `j`의 왼쪽·오른쪽 단면 유량을 `Q_j`, `Q_(j+1)`로 두면 비압축 연속식은 다음과 같다.

```text
Q_j − Q_(j+1) = dV_j/dt
Q_N = 0                         (sealed blind tip)
Q_j = Σ[k=j..N−1] dV_k/dt
```

각 interval에서는 인접 geometry 절점의 cell volume 차이를 실제 interval 시간으로 나누어 평균 `dV_j/dt`를 산출한다. 절점 사이 체적이 선형이라는 caller review를 요구한다. cell별 잔차, mouth 유량, blind-tip 유량 및 각 상태 digest를 결과에 담는다. 양의 mouth 유량은 액체가 틈 안으로 들어오는 방향, 음수는 밖으로 나오는 방향이다.

## 계약·계보

- `input_sha256`: 전체 caller 요청 digest
- `geometry_history_result_sha256`: pinned 원 geometry 결과 digest
- 각 interval의 시작/끝 geometry 상태 digest와 interval input digest
- 연속식 실패 시 완전히 계산된 앞선 interval만 `committed_prefix`에 저장하고, 실패 interval은 추가하지 않는다.
- `specifications()`는 Model ID `degradation.crevice_aperture_displacement_flow`, typed request/evaluator, 단위, 가정, context validator와 고유 Source ID를 제공한다.

## 제한

- 정확한 압력, 점도, 마찰, Reynolds 수, 속도분포, 관성 또는 벽 전단은 계산하지 않는다.
- 내부 cell face의 유량은 부피변화 연속성으로 정한 값이며, 운동량 방정식과 함께 풀린 유동해가 아니다.
- 연속체 해석에 사용할 시간 의존 면속도를 만들지 않는다. cross-section 변화 중 속도 변환/보간은 별도 review와 모델이 필요하다.
- 용질 수송, 전기화학, 반응, 침전, 부식률, 금속손실 또는 wall kinetics를 계산하지 않는다.
- 일정한 절점 사이 평균 유량과 작은 연속 잔차는 transient 물리모델의 검증이나 moving-boundary 적합성을 보증하지 않는다.

이 모듈은 사용자가 선언한 기하 history와 해석 가정으로 계산하는 caller-parameterized continuity ledger다. 테스트·실제 계산·패키징·중앙 registry/catalog/schema 연결은 포함하지 않았다.

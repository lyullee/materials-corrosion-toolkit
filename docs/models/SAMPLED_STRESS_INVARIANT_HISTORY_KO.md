# 표본 응력 불변량 이력 요약

## 목적

`matintegrity.multiaxial_stress_invariant_history`는 검토된 닫힌 주기의 caller 제공 응력 텐서 표본만 사용해 최대 정수압 응력과 편차응력 표본집합의 유한 거리 지표를 계산한다. 외부에서 보정한 피로 기준이나 후속 분석에 연결할 수 있는 수치 요약이다. 이 API 자체는 피로 기준, 수명, 손상, 안전 판정이 아니다.

## 입력 계약

- 6개 성분 순서는 `[xx, yy, zz, xy, yz, zx]`이며 응력 단위는 Pa다. 전단 성분은 대칭 응력 텐서의 실제 성분으로 해석한다.
- `sample_ids`와 텐서 표본을 입력 순서대로 일대일 연결한다. 샘플 식별자는 중복할 수 없다.
- 닫힌 주기는 첫 표본과 마지막 응력 텐서가 성분별로 정확히 같아야 한다. 별도의 sample ID는 각각 지정한다.
- `source_id`와 caller가 확인한 원본 SHA-256을 보존한다. 입력 전체의 canonical digest도 결과에 포함한다.
- `closed_cycle_and_sample_order_reviewed`와 `stress_tensor_basis_reviewed`가 모두 참이어야 계산한다. 검토가 없으면 `needs_data`를 돌려준다.
- 표본 수가 pair-work 상한을 넘으면 `out_of_scope`와 필요한 비교 횟수를 반환한다. 상한은 `maximum_pair_evaluations`로 조정할 수 있다.

## 계산

각 표본 (i)의 평균 정수압 응력은 다음과 같다.

\[
\sigma_{H,i}=(\sigma_{xx,i}+\sigma_{yy,i}+\sigma_{zz,i})/3
\]

각 응력 텐서에서 대각 성분의 평균을 빼 편차 텐서를 구성한다. 두 편차 텐서 사이의 거리에는 대칭 텐서 내적의 전단 중복도를 반영한다.

\[
d_{J2}(i,j)=\sqrt{\tfrac12[\Delta s_{xx}^2+\Delta s_{yy}^2+\Delta s_{zz}^2+2(\Delta s_{xy}^2+\Delta s_{yz}^2+\Delta s_{zx}^2)]}
\]

제공된 이산 표본들 사이에서 `d_J2`의 최댓값과 그 표본 ID를 반환한다. 그 절반은 **유한 표본 J2 거리의 반경 지표**다. 응력 경로가 한 직선 위에 놓인 경우에만 통상적인 진폭 해석과 일치한다. 비비례 경로에서 최소 외접 구의 반경, 연속 시간 극값 또는 표준 피로 진폭으로 해석하지 않는다.

## 사용 예

```python
from matintegrity.multiaxial_stress_invariant_history import (
    SampledStressInvariantHistory,
    evaluate_sampled_stress_invariant_history,
)

request = SampledStressInvariantHistory(
    analysis_id="case-001",
    material_condition_id="steel-condition-a",
    location_id="point-17",
    source_id="caller-reviewed-stress-history",
    source_sha256="a" * 64,
    sample_ids=["s0", "s1", "s2"],
    stress_tensor_components_Pa=[
        [0, 0, 0, 0, 0, 0],
        [100e6, 0, 0, 20e6, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ],
    closed_cycle_and_sample_order_reviewed=True,
    stress_tensor_basis_reviewed=True,
)
result = evaluate_sampled_stress_invariant_history(request)
```

예시는 호출 구조만 보여준다. 임의 숫자는 재료 상수나 검증 자료가 아니다.

## 범위와 주의점

이 구현은 표본 간 보간, cycle counting, 누락 데이터 보완, 비례/비비례 경로 판정, 재료 보정, 피로 수명, 누적 손상, 불확실성, 고장확률, 기준 적합성 및 자격 검증을 수행하지 않는다. 시간 벡터나 반복 하중의 수를 입력받지 않으므로 주파수·속도·수명으로 환산할 수 없다. 이 요약값을 후속 피로 모델에서 사용하려면 별도의 방법 정의, 재료/조건별 보정 및 적용성 검토가 필요하다.

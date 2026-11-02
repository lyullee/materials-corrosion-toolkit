# 유한 표본 전단 변형률 경로 면적

## 목적

`fatigue.multiaxial_sampled_shear_path_area`는 사용자가 선택한 재료면의 두 전단 변형률 좌표를 시간 순서대로 연결한 닫힌 다각형의 부호 면적을 계산한다. 비비례 하중에서 load path의 형상과 둘러싸인 면적이 하중 경로 효과를 구별하는 데 쓰여 온 기술적 동기를 참고한 독립적인 기하 descriptor다.

## 근거 및 범위

Deng 등은 비비례 하중 하의 다축 피로에서 load-path 민감성을 논하고, 일반화된 평면의 비비례 정도를 별도 지표로 구성한다. 이 모듈은 해당 연구의 수명 모델이나 계수를 구현하지 않는다. 입력 표본으로 다각형 면적을 직접 합산하는 자체 유한 표본 정의만 제공한다.

- Deng, Q. et al. (2023), “Load path sensitivity and multiaxial fatigue life prediction of metals under non-proportional loadings,” *International Journal of Fatigue*, 166, 107281. [DOI: 10.1016/j.ijfatigue.2022.107281](https://doi.org/10.1016/j.ijfatigue.2022.107281)
- 출처 식별자: `caller_finite_shear_path_polygon_area_nonproportional_loading_descriptor`

## 계산 정의

입력 좌표를 `(γ_a[i], γ_b[i])`라 할 때, 시간 순서를 유지한 각 연속 표본 쌍과 마지막 표본에서 첫 표본으로 돌아가는 닫힘 변을 포함하여 다음 값을 구한다.

`A = 1/2 Σ_i (γ_a[i] γ_b[i+1] − γ_a[i+1] γ_b[i])`, 인덱스는 순환한다.

출력에는 부호 면적, 절대 면적, 입력 끝점 사이 간격을 기록한다. 축 방향 순서를 바꾸면 부호가 바뀔 수 있다. 축 교환·회전 불변성을 보장하지 않는다.

## 입력 검토와 제약

- 두 좌표열과 sample ID는 같은 길이이며 ID는 고유해야 한다.
- 두 좌표는 사용자가 명시적으로 선택한 재료면의 engineering shear strain 좌표여야 한다. 모델은 텐서 이력으로부터 좌표를 투영하지 않는다.
- 닫힌 경로 검토, 성분 규약 및 축 방향 검토가 필요하다. 끝점 간격은 caller가 선언한 `closure_tolerance` 이하여야 한다.
- 계산은 표본 다각형에 한정된다. 보간, 평활화, 샘플 누락 보정, 주기 분해 및 연속시간 극값 추정은 하지 않는다.
- 면적은 정규화된 비비례 계수도 피로 손상식도 아니다. 시험 데이터와 재료별 검증 없이 수명이나 설계 판단에 연결하지 않는다.

## Python API

```python
from matintegrity.multiaxial_shear_path_area import (
    SampledShearPathArea,
    evaluate_sampled_shear_path_area,
    specifications,
)

model_spec = specifications()[0]
request = SampledShearPathArea(...)
result = evaluate_sampled_shear_path_area(request)
```

이 모듈은 독립 제공된다. 프로젝트 중앙 registry, catalog, schema에는 자동 등록하지 않는다.

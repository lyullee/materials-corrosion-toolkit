# 최대 주응력 축 회전 descriptor

## 목적과 기존 모듈과의 구분

`fatigue.multiaxial_principal_stress_axis_rotation`은 순서가 지정된 대칭 응력 텐서 표본마다 최대 대수적 주응력의 축을 구하고, 인접 표본 사이의 축 각도 변화를 합산한다. 이 API는 주응력 크기나 J2 경로 범위 대신 **방향이 이력 중 얼마나 변했는지**를 별도 기하 정보로 제공한다. 기존 피로 screen, cycle pairing, tensor work 또는 strain-plane polygon area를 대체하지 않는다.

## 공개 근거

다축 비비례 하중과 관련한 문헌은 주응력 방향의 시간 변화/회전을 하중 경로 특성의 한 표현으로 다룬다. 본 구현은 특정 문헌의 비비례 계수, 손상식 또는 수명식을 옮기지 않는다. 대칭 3×3 응력 텐서의 최대 고유벡터를 표본별로 구하고, 이를 무방향 축으로 취급해 유한 표본 회전 descriptor를 계산한다.

- Deng, Q. et al. (2023), “Load path sensitivity and multiaxial fatigue life prediction of metals under non-proportional loadings,” *International Journal of Fatigue*, 166, 107281. [DOI: 10.1016/j.ijfatigue.2022.107281](https://doi.org/10.1016/j.ijfatigue.2022.107281)
- 출처 식별자: `caller_finite_sample_principal_stress_axis_rotation_descriptor_nonproportional_loading`

## 입력과 출력

- 응력 성분 순서는 `[xx, yy, zz, xy, yz, zx]`이며 전단 성분은 대칭 텐서의 tensor shear 성분이다.
- caller가 시간/경로 순서가 보존된 표본 ID와 텐서 이력을 제공한다.
- cycle 폐합, 좌표계/성분 순서를 검토하고, `minimum_relative_principal_gap` 허용 기준을 선택한다.
- 샘플마다 최대 고유값과 두 번째 고유값 간격을 `max(|λ_i|, 1 Pa)`로 정규화한다. 이 gap이 caller 기준 이하인 표본이 있으면 방향이 민감하다고 보고 계산을 거부한다.
- 두 단위 고유축 `u_i`, `u_(i+1)` 간 거리는 `acos(|u_i · u_(i+1)|)`로 계산한다. 절댓값은 고유벡터의 임의 부호 반전을 제거한다.

출력은 인접 표본 각도의 누계, 최대 한 구간 각도, 그 구간의 표본 ID, 최소 관측 상대 고유값 간격이다. 첫·마지막 응력 텐서는 정확히 같아야 하며, 기록된 마지막 샘플로 폐합을 포함한다.

## 한계

고유축이 표본 사이에서 어떻게 움직였는지는 입력에 없으므로 중간 회전은 복원하지 않는다. 최대 고유값이 반복되거나 거의 반복되는 구간은 축 선택이 불안정하므로 제외한다. 누적 축 회전은 유한 표본 기하 descriptor일 뿐, 비비례 피로 손상계수, 추가 경화, 수명, 확률, 코드 판정 또는 재료 qualification 결과가 아니다.

## Python API

```python
from matintegrity.principal_stress_axis_rotation import (
    PrincipalStressAxisRotation,
    evaluate_principal_stress_axis_rotation,
    specifications,
)

spec = specifications()[0]
request = PrincipalStressAxisRotation(...)
result = evaluate_principal_stress_axis_rotation(request)
```

이 모듈은 standalone이며 중앙 registry/catalog/schema에 자동 등록되지 않는다.

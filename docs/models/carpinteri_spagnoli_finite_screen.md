# Carpinteri–Spagnoli 유한 평면 피로한도 screen

## 목적과 계산 범위

`fatigue.carpinteri_spagnoli_finite_limit_screen`은 caller가 정의한 각 재료면에서 최대 법선응력과 전단응력 벡터 진폭을 quadratic equivalent parameter로 결합하고, 완전반전 축방향 fatigue limit과 비교한다. Findley의 선형 합과 달리 제곱합 구조를 사용한다. 기존 Carpinteri–Spagnoli 임계면 방향 결정법 전체를 재현한다고 주장하지 않으며, 주어진 유한 plane 후보에서 최대값만 계산한다.

## 기술 근거

Carpinteri–Spagnoli 계열 고주기 기준은 critical plane의 최대 법선응력과 전단응력 진폭을 비선형 결합한다. hard-metal, 완전반전 축방향·비틀림 endurance limit의 비율을 통해 전단 가중치를 구성할 수 있다. 본 API는 caller 유한 후보면과 표본 이력에 해당 결합식을 적용하는 독립 finite-set screen이다.

- Carpinteri, A. & Spagnoli, A. (2001), “Multiaxial high-cycle fatigue criterion for hard metals,” *International Journal of Fatigue*, 23, 135–145. [DOI: 10.1016/S0142-1123(00)00075-X](https://doi.org/10.1016/S0142-1123(00)00075-X)
- 별도 검토용 공개 문헌: [Carpinteri–Spagnoli 식과 재료계수 요약](https://doi.org/10.3390/ma12142310)
- source ID: `carpinteri_spagnoli_2001_hard_metal_high_cycle_fatigue_criterion`

## 구현 정의

`k = σ_-1 / τ_-1`에서 `σ_-1`과 `τ_-1`은 같은 재료·시험조건의 fully reversed axial 및 torsional endurance limits다. 각 caller plane에서 tensor stress를 법선/두 접선 방향으로 투영한다. 전단응력 벡터의 finite-sample half diameter를 `τ_a`로 정의하고, cycle 최대 법선응력을 `σ_n,max`로 둔다.

`σ_eq = sqrt(σ_n,max² + k² τ_a²)`

표본 순서의 모든 전단 벡터 쌍을 비교하므로 shear amplitude는 유한표본 값이다. 최대값과 witness 표본 ID를 반환하며, `σ_eq`를 `σ_-1`과 비교한다. 응력 tensor 성분 순서는 `[xx, yy, zz, xy, yz, zx]`다.

## 검토 요건 및 한계

- history는 정확히 닫힌 cycle이어야 하며, 유한 candidate plane basis는 caller가 검토한다.
- 두 endurance limits는 동일 조건 및 smooth-specimen R = −1 basis에서 왔는지 caller가 확인한다.
- 원래 Carpinteri–Spagnoli plane direction rule은 평균 주응력 방향과 재료비에 의존할 수 있다. 여기서는 그 방향을 도출하거나 연속 plane 최적화를 하지 않는다. 따라서 결과는 caller plane 집합 조건부 screen이다.
- `σ_n,max`는 부호를 유지한 뒤 제곱된다. 압축 영향 별도 보정이나 clipping은 넣지 않는다.
- 이 API는 hard-metal HCF 제한 모델이며 finite-life curve, cycle damage, 비비례 추가 경화, 확률, acceptance 또는 qualification 결과를 산출하지 않는다.
- 시간표본 사이 extrema, plane quadrature 오차, endurance-limit 산포 및 재료조건 전이는 평가하지 않는다.

## Python API

```python
from matintegrity.carpinteri_spagnoli_finite_screen import (
    CarpinteriSpagnoliFiniteScreen,
    CarpinteriSpagnoliPlane,
    evaluate_carpinteri_spagnoli_finite_screen,
    specifications,
)

spec = specifications()[0]
request = CarpinteriSpagnoliFiniteScreen(...)
result = evaluate_carpinteri_spagnoli_finite_screen(request)
```

모듈은 standalone이며 중앙 registry/catalog/schema에 자동 등록되지 않는다.

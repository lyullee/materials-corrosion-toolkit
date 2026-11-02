# Papadopoulos P1 유한 방향 적분 피로한도 screen

## 목적

`fatigue.papadopoulos_p1_finite_integral_screen`은 caller가 제공한 대표 응력 cycle에서 많은 방향의 resolved shear 응력 amplitude를 caller quadrature로 평균하고, 최대 표본 hydrostatic stress와 함께 P1 형태의 고주기 피로한도 parameter를 계산한다. 이미 존재하는 P2 finite-plane screen의 방향별 최댓값과 달리, P1 integral 접근을 유한한 caller quadrature로 근사한다.

## 기술 근거

Papadopoulos의 고주기 다축 피로 criterion은 가능한 slip 방향들에서 구한 resolved shear amplitude의 방향 평균 계열 항과 최대 hydrostatic stress를 결합한다. 구현은 그 P1 계열 계산 개념에 해당한다. 발표 논문의 표·문장·상수 표를 포함하지 않고, 방향 적분은 사용자가 제출하는 유한 방향 표본 및 가중치로 독립 계산한다.

- Papadopoulos, I. V. (1995), “A high-cycle fatigue criterion applied in biaxial and triaxial out-of-phase stress conditions,” *Fatigue & Fracture of Engineering Materials & Structures*, 18, 79–91. [DOI: 10.1111/j.1460-2695.1995.tb00143.x](https://doi.org/10.1111/j.1460-2695.1995.tb00143.x)
- 출처 식별자: `papadopoulos_1995_high_cycle_integral_multiaxial_criterion`

## 유한 방향 계산

사용자는 방향계 `j`마다 단위 평면 법선 `n_j`, 단위 평면내 전단 방향 `m_j` (`m_j · n_j = 0`), 그리고 정규화 가중치 `w_j`를 제출한다. 가중치 합은 1이어야 한다. 각 방향에서 응력 tensor `σ(t)`의 `m_j · σ(t) · n_j` 투영 이력을 구성하고, cycle 표본 반범위 `τ_a,j = (max_t τ_j − min_t τ_j)/2`를 구한다.

유한 quadrature general shear 항은 `sqrt(5 Σ_j w_j τ_a,j²)`이며, screening parameter는 여기에 caller `a_C`와 최대 표본 hydrostatic 응력의 곱을 더한다. 결과를 caller가 제공한 fully reversed torsional fatigue limit과 비교한다. 모델은 가중치를 생성하거나 보정계수/한도를 추정하지 않는다.

## 입력과 검토 요건

- 같은 재료 조건의 대칭 Cauchy stress tensor 표본, 표본 ID, 물성/한도 Evidence 및 SHA-256 lineage가 필요하다.
- tensor 성분 순서는 `[xx, yy, zz, xy, yz, zx]`; 전단 성분은 tensor stress 성분이다.
- 첫·마지막 tensor 표본이 정확히 일치하는 대표 cycle을 입력한다.
- 방향 표본의 measure, covering/가중치 구성 및 대표성은 caller가 검토한다. 법선과 전단 방향은 각각 단위벡터이며 서로 직교해야 한다.
- hydrostatic coefficient `a_C`와 fully reversed torsional fatigue limit은 caller의 같은 재료·조건 교정값이어야 한다. API는 단순 finite-support limit comparison만 수행한다.

## 한계

유한 quadrature는 연속 구면 적분의 정확성이나 오차 상한을 보장하지 않는다. 시간 영역도 입력 표본에 한정되므로 표본 사이 극값과 임의 cycle 분해를 추정하지 않는다. 이 API는 고주기 fatigue limit screen으로 제한되며, finite-life 곡선, cycle damage 누적, 비비례 추가 경화, load-sequence 효과, 코드 acceptance 또는 재료 qualification을 제공하지 않는다. 넓은 방향 coverage를 원하면 별도 quadrature 수렴/독립 검증을 해야 한다.

## Python API

```python
from matintegrity.papadopoulos_p1_finite_integral_screen import (
    PapadopoulosP1FiniteIntegralScreen,
    PapadopoulosP1ShearSystem,
    evaluate_papadopoulos_p1_finite_integral_screen,
    specifications,
)

spec = specifications()[0]
request = PapadopoulosP1FiniteIntegralScreen(...)
result = evaluate_papadopoulos_p1_finite_integral_screen(request)
```

모듈은 standalone이다. 중앙 registry/catalog/schema에는 자동 연결하지 않는다.

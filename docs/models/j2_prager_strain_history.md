# 소변형률 J2–Prager 변형률 이력 계산기

## 목적

`fatigue.j2_prager_strain_history`는 caller가 제공한 3차원 총 변형률 표본 경로에서 응력, 소성변형률, 이동경화 backstress 및 누적 등가소성변형률을 순차적으로 계산한다. 평면 방향 screen이나 cycle-life curve와는 다른 구성방정식 계산 API다. 후속 재료 피로 모델에 경로 의존 응력·소성변형률을 공급할 수 있지만, 그 자체로 피로 수명을 산출하지 않는다.

## 기술 근거

모델은 소변형률 등방탄성, von Mises/J2 항복면, 연관 유동법칙, 선형 등방경화 및 선형 Prager 이동경화를 조합한다. 탄성 predictor 뒤에 등가응력 방향으로 복귀하는 radial-return 갱신을 사용한다. 구현은 공개된 소성 이론을 독립적으로 코드화한 것이며, 특정 상용 솔버의 구현이나 검증 결과를 복제하지 않는다.

- Prager, W. (1949), “Recent Developments in the Mathematical Theory of Plasticity,” *Journal of Applied Physics*, 20(3), 235–241. [DOI: 10.1063/1.1698348](https://doi.org/10.1063/1.1698348)
- J2 소성 및 계산 구현 문맥: Chiumenti et al. (2004), “A stabilized formulation for incompressible plasticity using linear triangles and tetrahedra,” *International Journal of Plasticity*, 20, 1487–1504. [DOI: 10.1016/j.ijplas.2003.11.009](https://doi.org/10.1016/j.ijplas.2003.11.009)
- 출처 식별자: `small_strain_j2_associative_return_mapping_with_linear_prager_kinematic_and_isotropic_hardening`

## 구성식과 한 구간 갱신

응력/변형률 6성분 순서는 `[xx, yy, zz, xy, yz, zx]`다. 변형률의 전단 성분은 tensor shear로 입력한다. 응력 내적의 전단 성분에는 대칭 텐서 내적에 맞춰 가중치 2가 적용된다.

각 표본 구간에서 현재 응력에 등방 탄성 증분을 적용해 trial stress를 만든다. 편차응력에서 backstress를 뺀 값으로 von Mises 등가응력을 계산한다. 항복면 안에 있으면 elastic predictor를 수용하고, 바깥이면 scalar plastic multiplier를 다음 선형 hardening modulus로 나눈 radial correction을 적용한다.

`3G + H_iso + C_Prager`

여기서 `G`는 전단탄성계수, `H_iso`는 누적 등가소성변형률에 대한 항복응력 증가 계수, `C_Prager`는 `dα = (2/3) C_Prager dεp` 규약의 이동경화 상수다. 응답 ledger에는 매 knot 응력, 소성변형률, backstress, 누적 등가소성변형률과 항복잔차를 남긴다.

## 입력 조건과 사용 제한

- 단일 재료 조건의 ordered total-strain tensor history, 초기 응력/소성변형률/backstress/누적 등가소성변형률 상태, 탄성계수, 초기 항복응력 및 두 선형 경화 계수를 모두 caller가 제공한다.
- 재료 모델, 단위, 기준 좌표, 성분 순서, 첫 표본의 초기 상태, 소변형률·준정적 적용성을 별도 검토해야 한다. 초기 상태는 첫 입력 변형률 knot에 해당한다고 가정한다.
- 해석은 등온·준정적·소변형률·등방탄성으로 제한된다. 속도 효과, 온도 의존성, 다중 backstress, 비선형/포화 경화, cyclic softening, 비비례 추가 경화, 대변형률, damage 및 균열은 구현하지 않는다.
- 각 입력 knot 사이에 한 번의 backward-Euler radial-return를 적용한다. 적응형 substepping은 하지 않으므로 입력 시간/변형률 간격의 적절성은 caller가 검토해야 한다.
- 출력의 knot 응력 기반 signed stress–strain work는 단순 사다리꼴 적분값이다. 이를 비가역 소산에너지로 간주하지 않는다.
- 결과는 구성 응답이며 피로 cycle counting, damage, life, probability, acceptance, code compliance 또는 재료 qualification을 대신하지 않는다.

## Python API

```python
from matintegrity.j2_prager_strain_history import (
    J2PragerStrainHistory,
    evaluate_j2_prager_strain_history,
    specifications,
)

spec = specifications()[0]
request = J2PragerStrainHistory(...)
result = evaluate_j2_prager_strain_history(request)
```

모듈은 standalone으로 제공되며 중앙 registry/catalog/schema에 자동 등록되지 않는다.

# Carpinteri–Spagnoli 수명 의존 계수와 caller S–N 곡선 수명

## 목적

`fatigue.carpinteri_spagnoli_life_dependent_curve`는 caller가 제공한 동일 조건의 축방향 및 비틀림 S–N 곡선을 함께 사용해 Carpinteri–Spagnoli 계열 수명 의존 재료비를 계산하고, finite candidate planes에서 수명을 구한다. 고정 axial/torsion endurance ratio로 한 번만 계산하는 screen과 달리, 두 곡선의 강도비가 수명 좌표에 따라 변하는 경우를 각 root iteration에서 반영한다.

## 문헌 근거와 계산

Carpinteri–Spagnoli 고주기 계열의 plane-normal stress 및 shear amplitude 결합을 사용한다. caller 수명 곡선에서 `σ_f(N)`과 `τ_f(N)`을 평가해 `k_CS(N)=σ_f(N)/τ_f(N)`로 둔다. plane별 등가식의 정규화된 형태는 다음과 같다.

`(σ_n,max / σ_f(N))² + (τ_a / τ_f(N))² = 1`

이 식은 strength 비가 수명과 함께 달라지는 경우에도 각 수명 후보의 utilization을 비교할 수 있게 한다. 두 S–N 곡선은 양의 강도값, 증가하는 수명축, 감소하는 강도축을 가져야 한다. log–log 선형 보간 후 공통 life support 내에서 bisection으로 root를 구한다. 강도가 엄격히 감소하므로 양의 곡선과 고정 stress feature에 대해 utilization은 비감소한다.

- Carpinteri, A. & Spagnoli, A. (2001), “Multiaxial high-cycle fatigue criterion for hard metals,” *International Journal of Fatigue*, 23, 135–145. [DOI: 10.1016/S0142-1123(00)00075-X](https://doi.org/10.1016/S0142-1123(00)00075-X)
- 수명 의존 parameter 사용 사례: [Application of Life-Dependent Material Parameters to Fatigue Life Prediction under Multiaxial and Non-Zero Mean Loading](https://doi.org/10.3390/ma13071587)
- 모델 ID: `fatigue.carpinteri_spagnoli_life_dependent_curve`

## 이력 특성

각 candidate plane에서 normal 응력은 표본 중 최대값을 사용한다. 전단 응력은 두 직교 tangent 축으로 투영된 2D vector 이력에서 최대 pairwise 거리의 절반을 취한다. 이 정의는 입력 표본으로 계산 가능한 finite amplitude이며 연속시간 또는 표본 사이 극값을 복원하지 않는다. 각 plane에서 수명을 계산한 후 caller의 finite plane 집합에서 가장 짧은 수명을 governing 결과로 반환한다.

## 입력 검토 및 보호 조건

- history는 정확히 닫힌 응력 cycle이어야 하며 tensor 순서는 `[xx, yy, zz, xy, yz, zx]`다.
- 축·비틀림 곡선은 같은 재료 condition, 시험 기준, fully reversed smooth specimen 및 동일 units이어야 한다. Material matching, 하드메탈 HCF 적용성, curve 권리/engineering use와 plane 집합을 caller가 검토한다.
- 수명 root는 두 curve life support의 교집합에서만 찾는다. 계산 근이 support에 없으면 외삽하지 않고 `out_of_scope`를 반환한다.
- 유한 plane pair work와 curve-root work budget을 적용한다. root tolerance 및 iteration 수는 caller 계약에 명시된다.

## 한계

이 API는 원 Carpinteri–Spagnoli 평균 주응력 방향에 따른 연속 critical-plane 선정법을 구현하지 않는다. caller finite 후보면 중에서 가장 짧은 life를 선택한다. 표본 간 stress history, life scatter, curve fitting, 재료 간 transfer, variable-amplitude cycle 분해/누적, sequence effect, mean-stress relaxation, failure probability, code acceptance 및 재료 qualification은 처리하지 않는다. 결과는 caller 곡선과 finite plane 집합에 조건부다.

## Python API

```python
from matintegrity.carpinteri_spagnoli_life import (
    CarpinteriSpagnoliLife,
    evaluate_carpinteri_spagnoli_life,
    specifications,
)

spec = specifications()[0]
request = CarpinteriSpagnoliLife(...)
result = evaluate_carpinteri_spagnoli_life(request)
```

모듈은 standalone이고 중앙 registry/catalog/schema에 자동 등록되지 않는다.

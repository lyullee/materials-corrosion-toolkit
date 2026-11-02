# 다축 stress/strain 주기의 Fourier 재구성

## 목적

`fatigue.periodic_tensor_fourier_reconstruction`은 균등 위상 간격으로 주어진 단일 폐주기 stress/strain tensor 표본에서 실수 삼각다항식 보간 함수를 만들고, caller가 고른 위상에서 tensor 값을 평가한다. 이는 기존 선형·Hermite·PCHIP·주기 cubic-spline과 별개의 대체 시간 재구성 family다. API는 재구성 결과만 제공하며 work, 피로계수, damage 또는 life를 계산하지 않는다.

## 수학적 정의

폐주기 끝점이 중복된 마지막 tensor knot을 제외하고 `N`개의 균등 표본을 사용한다. 각 tensor component별로 이산 Fourier 계수를 계산하고, 짝수 표본수일 때 Nyquist harmonic을 별도 cos 항으로 포함해 유일한 실수 trigonometric interpolant를 구성한다. 따라서 고정된 표본에 대해 평가점에서 다항식 interpolation 값이 만들어지며, smoothing이나 harmonic 절삭을 하지 않는다.

이 절차는 균등 주기 격자에서 trigonometric interpolation을 쓰는 표준 Fourier spectral 접근에 기반한다.

- Trefethen, L. N. (2000), *Spectral Methods in MATLAB*, SIAM, Philadelphia. [DOI: 10.1137/1.9780898719598](https://doi.org/10.1137/1.9780898719598)
- 참고 장: [Polynomial Interpolation and Clustered Grids](https://doi.org/10.1137/1.9780898719598.ch5)
- source ID: `caller_uniform_periodic_real_trigonometric_tensor_interpolation`

## 입력 규약

- Stress/strain component 순서는 `[xx, yy, zz, xy, yz, zx]`다. Strain의 전단 규약은 tensor 또는 engineering으로 명시하며, API는 입력 component 값을 그대로 보간한다.
- 첫/마지막 stress 및 strain tensor는 정확히 일치하는 중복 cycle endpoint여야 한다.
- 첫 knot부터 endpoint 직전까지 표본이 `2π/N` 간격의 균등 periodic grid를 이룬다는 것을 caller가 확인한다. 시간값을 받지 않으므로 불균등한 실제 시간축을 보정하지 않는다.
- Caller는 주기성, 단위, 좌표축, 성분 순서, 표본 순서, Fourier 적합성, aliasing review를 제공한다.
- `evaluation_phase_rad`는 [0, 2π] 범위에서 오름차순이어야 한다. 각 평가점의 입력 ID, phase와 재구성 tensor 값을 결과에 보존한다.

## 한계와 적용 시 주의

균등 표본의 전체 band를 그대로 보간하므로 aliasing을 제거하거나 노이즈를 줄이지 않는다. 급격한 전이/불연속이 있는 신호는 Gibbs형 진동을 만들 수 있으며, 현 API는 이를 진단·필터링하거나 오차를 제한하지 않는다. 표본 사이 최대값은 존재할 수 있으므로 후속 극값/피로 계산에는 별도 sampling convergence와 적합성 검토가 필요하다. 이 모듈은 재구성된 경로의 정확성, 물성 적합성, 피로 수명, 확률, 설계 acceptance 또는 qualification을 보증하지 않는다.

## Python API

```python
from matintegrity.multiaxial_periodic_fourier_reconstruction import (
    PeriodicTensorFourierReconstruction,
    evaluate_periodic_tensor_fourier_reconstruction,
    specifications,
)

spec = specifications()[0]
request = PeriodicTensorFourierReconstruction(...)
result = evaluate_periodic_tensor_fourier_reconstruction(request)
```

모듈은 standalone이며 중앙 registry/catalog/schema에 자동 등록되지 않는다.

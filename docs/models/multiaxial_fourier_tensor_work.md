# Fourier 보간 tensor cycle의 stress–strain 일 적분

## 목적

`fatigue.periodic_fourier_tensor_work`는 균등 위상 간격의 폐주기 stress/strain tensor 표본으로 full-bandwidth real trigonometric interpolant를 만들고, 그 보간 경로에서 한 주기 signed tensor work를 해석적으로 계산한다. 앞서 분리된 Fourier 재구성 API를 응력–변형률 경로 적분까지 연결하는 계산기다.

## 계산 원리

각 tensor 성분의 주기 Fourier 계수를 계산한 뒤, 같은 harmonic의 stress cosine/sine 성분과 strain cosine/sine 성분의 cross-term만 합산한다. 서로 다른 harmonic은 한 주기 적분에서 직교하고 평균항의 폐주기 미분 적분은 0이므로 결과는 Fourier 계수 곱의 유한 합으로 정확히 주어진다.

Stress 및 strain은 `[xx, yy, zz, xy, yz, zx]` 순서다. Strain이 tensor shear라면 stress:strain contraction의 전단 성분을 2배 가중하고, engineering shear라면 해당 입력이 이미 work-conjugate `gamma` 성분이므로 1배 가중한다. 출력은 각 성분 기여와 signed total work density다.

## 공개 기술 근거

균등 주기점에서 trigonometric interpolation과 Fourier 급수의 직교성을 사용한다. 특정 피로 수명식을 복제하거나 유도하는 모듈은 아니다.

- Trefethen, L. N. (2000), *Spectral Methods in MATLAB*, SIAM. [DOI: 10.1137/1.9780898719598](https://doi.org/10.1137/1.9780898719598)
- 구현 ID: `fatigue.periodic_fourier_tensor_work`
- source ID: `caller_exact_closed_tensor_work_fourier_orthogonality_integral`

## 입력 조건

- 동일 sample ID, source digest 및 시간 순서의 closed stress/strain tensor 이력이 필요하다.
- 첫·마지막 tensor sample은 정확히 같아야 한다. endpoint를 제거한 내부 표본이 균등 위상 간격이라는 점은 caller가 확인한다.
- tensor basis, 성분 순서, 응력–변형률 conjugacy 및 strain shear convention을 review해야 한다.
- Fourier interpolation은 전체 표본이 허용하는 harmonics를 모두 사용한다. 주기 재구성 적합성과 aliasing review를 caller가 명시한다.

## 한계

적분값은 오직 입력점과 그 full-bandwidth trigonometric interpolant에 대해 정확하다. 표본화된 physical history의 미관측 구간을 보증하지 않으며, 급격한 경계 변화나 노이즈는 전역 Fourier 진동을 만들 수 있다. signed closed-loop work는 비가역 소산에너지와 동일시하지 않는다. 비균등 시간점, smoothing, alias rejection, work-life curve, cycle counting, damage, life, probability, code acceptance 또는 재료 qualification은 포함하지 않는다.

## Python API

```python
from matintegrity.multiaxial_fourier_tensor_work import (
    PeriodicFourierTensorWork,
    evaluate_periodic_fourier_tensor_work,
    specifications,
)

spec = specifications()[0]
request = PeriodicFourierTensorWork(...)
result = evaluate_periodic_fourier_tensor_work(request)
```

모듈은 standalone이며 중앙 registry/catalog/schema에 자동 등록되지 않는다.

# 주기 tensor 이력의 Fourier 시간 미분

## 목적

`fatigue.periodic_tensor_fourier_rates`는 닫힌 주기 응력·변형률 tensor 이력에서 유한 Fourier 보간함수를 구성하고, 사용자가 지정한 위상에서 그 함수의 해석적 시간 미분을 반환한다. 시간 미분 입력을 요구하는 후속 구성방정식이나 사용자 모델에 연결하기 위한 운동학 API다.

## 입력과 단위

- tensor 성분 순서는 `[xx, yy, zz, xy, yz, zx]`이다.
- 응력은 Pa, 변형률은 무차원이며 주기는 초 단위다.
- 변형률 전단 convention을 `tensor` 또는 `engineering`으로 명시해 원자료 의미를 보존한다. 미분값 자체는 입력 convention을 그대로 따른다.
- 마지막 행은 첫 행과 정확히 같은 폐곡선 종점이어야 한다. 앞의 행들은 균일 간격의 독립 위상 표본으로 취급한다.
- 질의 위상은 라디안 `[0, 2π]` 범위에서 오름차순으로 입력한다.
- Evidence의 source ID와 SHA-256은 요청 메타데이터와 일치해야 한다.

## 계산 정의

각 tensor 성분의 독립 표본에 대해 실수 Fourier 급수를 유한 표본 수의 Nyquist 규칙에 맞게 구성한다. `a_k cos(kθ) + b_k sin(kθ)` 항의 위상 미분은 `k(-a_k sin(kθ) + b_k cos(kθ))`이고, 시간 미분은 `dθ/dt = 2π/T`를 곱한다. 짝수 표본의 Nyquist 성분은 cosine 항만 존재하므로 그 미분도 해당 항의 미분으로 계산한다.

모델 식과 Fourier spectral differentiation의 공개 기초 문헌은 Lloyd N. Trefethen, *Spectral Methods in MATLAB*, SIAM, 2000, DOI: [10.1137/1.9780898719598](https://doi.org/10.1137/1.9780898719598)이다. 구현은 이 문헌의 주기 Fourier 미분 원리를 유한 실수 급수에 적용하며, 책의 문장이나 표를 재수록하지 않는다.

## 상태와 한계

누락된 검토 선언은 `needs_data`, 계산량 상한 초과 또는 비유한 결과는 `out_of_scope`로 남긴다. 균일 표본, 경로 순서, 주기 및 Fourier aliasing 적합성은 호출자가 검토해야 한다. 고주파 잡음과 aliasing을 억제하거나 오차 범위를 추정하지 않는다. 따라서 반환값은 보간함수의 도함수이며 실험에서 직접 측정한 rate와 동일하다고 보장하지 않는다.

이 모듈은 응력률·변형률률만 계산한다. 구성방정식, 소성 상태 업데이트, 피로 손상, 수명, 허용성 판단 또는 재료 자격을 계산하지 않는다. 그 물리적 해석은 별도 모델, 재료별 파라미터, 적용성 검토 및 검증이 필요하다.

## API 연결

```python
from matintegrity.multiaxial_periodic_fourier_rates import (
    PeriodicTensorFourierRates,
    evaluate_periodic_tensor_fourier_rates,
)

request = PeriodicTensorFourierRates(...)
result = evaluate_periodic_tensor_fourier_rates(request)
```

`specifications()`는 모델 식별자, 요청 타입, evaluator, 출력 단위, 전제 및 source ID를 제공한다. 중앙 registry 등록은 별도 통합 변경으로 수행한다.

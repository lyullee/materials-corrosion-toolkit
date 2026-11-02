# Fourier tensor work–life와 Miner block 연결

## 목적

`fatigue.periodic_fourier_tensor_work_life`는 각 caller cycle의 closed stress–strain path에서 Fourier interpolant signed work를 정확히 적분하고, 절대 work 값을 같은 재료 조건 caller work–life curve에 제한 보간한 뒤 명시된 cycle repetitions로 선형 Miner damage를 누적한다. Fourier 재구성과 work integration을 수명·block ledger에 연결하는 standalone bridge다.

## 계산 흐름

1. 각 cycle에 균등 표본 stress/strain tensor, 닫힌 endpoint, shear convention과 source lineage를 입력한다.
2. Fourier tensor work 모듈로 `σ:dε`의 closed-cycle signed 적분을 계산한다.
3. 절대 signed work를 양의 caller work–life curve 안에서 log–log 선형 보간하여 `N_i`를 얻는다. curve 외부는 외삽하지 않는다.
4. caller cycle count equivalents `n_i`로 `D_i=n_i/N_i`를 계산하고 선형합을 구한다.

## 근거와 caller 선언

주기 Fourier 보간은 균등점에서의 삼각다항식 보간에 근거하며, 응력–변형률 work는 같은 harmonic들의 직교 적분으로 계산한다. 수명 mapping은 외부에서 제공하는 재료별 실험 curve만 이용한다. Miner 합은 계산기에서 숨겨진 기본값이 아니라 caller가 명시적으로 검토해야 하는 가정이다.

- Trigonometric interpolation reference: Trefethen, L. N. (2000), *Spectral Methods in MATLAB*. [DOI: 10.1137/1.9780898719598](https://doi.org/10.1137/1.9780898719598)
- 모델 ID: `fatigue.periodic_fourier_tensor_work_life`
- Calibration source ID/digest와 curve 값은 모든 ledger row에서 digest lineage로 보존된다.

## 한계

작업량·보간·수명은 caller가 제출한 유한표본 Fourier interpolant에만 정확/조건부다. absolute signed work를 calibration x축으로 쓰는 선택, 실제 가역/비가역 에너지의 물리적 의미, cycle 개수, 경로 분해, Miner 상호작용 무시와 누적 임계값은 별도 검토가 필요하다. 한 주기 work가 0이거나 curve support 밖이면 수명 외삽하지 않는다. Material transfer, loading sequence, scatter/probability, nonproportional hardening, 코드 acceptance와 qualification은 평가하지 않는다.

## Python API

```python
from matintegrity.multiaxial_fourier_work_life import (
    FourierWorkLifeCycle,
    FourierTensorWorkLife,
    evaluate_fourier_tensor_work_life,
    specifications,
)

spec = specifications()[0]
request = FourierTensorWorkLife(...)
result = evaluate_fourier_tensor_work_life(request)
```

모듈은 standalone이며 중앙 registry/catalog/schema에 자동 등록하지 않는다.

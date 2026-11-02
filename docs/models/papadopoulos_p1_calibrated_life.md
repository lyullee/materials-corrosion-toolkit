# Papadopoulos P1 caller 곡선 기반 수명 계산

## 목적

`fatigue.papadopoulos_p1_calibrated_life`는 유한 orientation quadrature P1 screen으로 계산한 stress parameter를 같은 재료 조건의 caller 제공 `P1 parameter ↔ cycles to failure` 곡선에 연결한다. P1 한도 screen을 finite-life 계산에 이어 붙이는 별도 API이며, 수명 곡선 자체를 생성하거나 시험 데이터를 fitting하지 않는다.

## 계산 흐름

1. 중첩 `PapadopoulosP1FiniteIntegralScreen` 요청이 caller 검토 조건을 충족하면 P1 equivalent stress parameter를 계산한다.
2. caller 곡선의 P1 값은 양수·엄격 증가, failure cycle 값은 양수·엄격 감소여야 한다.
3. 계산 parameter가 곡선 내부에 있으면 `log(P1)`과 `log(Nf)` 사이를 선형 보간한다. 곡선 knot과 정확히 같으면 해당 수명을 직접 사용한다.
4. parameter가 곡선 밖에 있으면 `out_of_scope`이며 외삽하지 않는다.

## 근거와 계수

P1 parameter는 Papadopoulos의 integral high-cycle fatigue criterion에 근거한 finite quadrature screen을 재사용한다. 수명 매핑은 재료별로 시험해 제공한 caller curve에 한정한다. 논문의 식이나 수명표를 본 문서에 복사하지 않는다.

- Papadopoulos, I. V. (1995), “A high-cycle fatigue criterion applied in biaxial and triaxial out-of-phase stress conditions,” *Fatigue & Fracture of Engineering Materials & Structures*, 18, 79–91. [DOI: 10.1111/j.1460-2695.1995.tb00143.x](https://doi.org/10.1111/j.1460-2695.1995.tb00143.x)
- 구현 ID: `fatigue.papadopoulos_p1_calibrated_life`
- 수명 곡선 source ID: caller가 선언하며, Evidence·SHA-256과 정규화된 곡선 digest가 응답에 보존된다.

## 한계

이 수명은 caller 곡선의 시험 재료·조건·표본·한도 정의에 전적으로 조건부다. finite quadrature 방향오차, 시험 산포, confidence interval, 데이터 transfer, 평균응력 영향 보정, 주기 분해, variable-amplitude Miner 누적, 코드 acceptance, 수명 확률 및 재료 qualification은 처리하지 않는다. R비, 표면 상태, 환경, 온도, 형상 notch 조건 등이 다른 curve를 섞지 말고 별도 재료 조건으로 관리한다.

## Python API

```python
from matintegrity.papadopoulos_p1_calibrated_life import (
    PapadopoulosP1CalibratedLife,
    evaluate_papadopoulos_p1_calibrated_life,
    specifications,
)

spec = specifications()[0]
request = PapadopoulosP1CalibratedLife(...)
result = evaluate_papadopoulos_p1_calibrated_life(request)
```

이 모듈은 standalone이며 중앙 registry/catalog/schema에 자동 등록되지 않는다.

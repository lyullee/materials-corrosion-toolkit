# Papadopoulos P1 계수 시험치 계산

## 목적

`fatigue.papadopoulos_p1_calibration`은 같은 재료 조건의 완전반전 축방향 endurance limit `σ_-1`과 비틀림 endurance limit `τ_-1`으로 P1 hydrostatic 계수 `a_C`를 계산한다. 결과의 `use_handoff` 필드는 직전 P1 finite-integral screen에 넘길 계수와 비틀림 한도를 함께 보존한다.

## 근거 및 정의

완전반전 smooth-specimen 시험 한계로 Papadopoulos 계수를 구성하는 관계를 사용한다.

`a_C = 3 τ_-1 / σ_-1 − √3`

축방향과 비틀림 한계가 같은 열처리, 표면, 환경, 온도 및 재료 condition에 해당하고 둘 다 동일한 R = −1 endurance-limit 정의일 때만 계산을 허용한다. 발표 논문 문장이나 표는 이 문서에 복사하지 않는다.

- Papadopoulos, I. V. (1995), “A high-cycle fatigue criterion applied in biaxial and triaxial out-of-phase stress conditions,” *Fatigue & Fracture of Engineering Materials & Structures*, 18, 79–91. [DOI: 10.1111/j.1460-2695.1995.tb00143.x](https://doi.org/10.1111/j.1460-2695.1995.tb00143.x)
- 적용식과 endurance-limit 매개변수 관계를 확인할 수 있는 공개 기술 자료: [Palin-Luc et al. PDF, Appendix A](https://sam.ensam.eu/bitstream/handle/10985/7414/DUMAS_ijfatigue_2013_palin-luc.pdf?isAllowed=y&sequence=3)
- source ID: `papadopoulos_1995_p1_endurance_limit_parameter_relation`

## 계약과 결과

입력은 axial/torsion limit 값과 각각의 Evidence, 원자료 SHA-256, 동일 재료·조건 검토, R = −1 검토, smooth-specimen 기반 검토 및 계수 사용 검토를 요구한다. 계산된 `a_C`는 무차원이며 `fully_reversed_torsional_limit_Pa`는 대응 P1 screen의 오른쪽 한계값으로 보존한다.

`a_C < 0`이면 현재 P1 screen의 nonnegative 계수 contract 적용 범위와 맞지 않으므로 `out_of_scope`로 응답한다. 입력값을 clipping하거나 계수를 0으로 대체하지 않는다.

## 한계

이 API는 두 축방향/비틀림 endurance limit 사이의 계수 산출만 수행한다. 특정 부품/노치, 용접부, 평균응력, 다른 R비, 고온·부식 환경 또는 다른 재료 condition으로 시험치를 전이하지 않는다. 시험 산포, confidence interval, 곡선 피팅, 수명, 손상 누적, 설계 acceptability 및 재료 qualification은 계산하지 않는다. Evidence의 권리와 수치 사용 허가는 데이터 소유자가 별도 확인해야 한다.

## Python API

```python
from matintegrity.papadopoulos_p1_calibration import (
    PapadopoulosP1Calibration,
    derive_papadopoulos_p1_calibration,
    specifications,
)

spec = specifications()[0]
request = PapadopoulosP1Calibration(...)
result = derive_papadopoulos_p1_calibration(request)
```

모듈은 standalone으로 제공되며 중앙 registry/catalog/schema에 자동 등록하지 않는다.

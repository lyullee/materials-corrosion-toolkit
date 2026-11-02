# 캐비테이션 열역학 선별

## 범위

`degradation.cavitation_margin`은 검토된 한 국부 액체 상태에서 절대 정압과 평형 증기압의
차이를 계산한다. 이 계산은 증기상 형성이 열역학적으로 가능한지를 선별하는 하위 기능이다.
기포핵, 비정상 압력파, inception 지연, 기포 붕괴, 표면 충격, 침식률, 재료 손상, 수명,
고장확률 또는 합격 판정은 계산하지 않는다.

압력은 모두 절대압이어야 한다. 입력은 유체와 온도, 국부 정압, 증기압, 액체 밀도,
특성속도, 물성 공급자 판본과 상태 digest, 압력·속도의 물리적 정의를 보존한다. 정압 또는
열역학 상태가 검토되지 않았으면 `needs_data`로 중지한다. 게이지압은 입력 계약에서 거절한다.

## 계산

정압 여유, 정수두 여유, 특성 동압과 국부 캐비테이션 수는 다음처럼 정의한다.

```text
delta_p = p_local,absolute - p_vapor
h_static = delta_p / (rho g0)
q = rho V^2 / 2
sigma_local = delta_p / q
```

여기서 `g0=9.80665 m/s²`이며 `V`는 호출자가 정의한 양의 특성속도다. `delta_p <= 0`이면
해당 입력 상태에서 열역학적 증기상 형성이 가능하다고 표시한다. 양의 여유가 실제 설비에서
캐비테이션이 없음을 보증하지 않으며, 국부 순간압력이 입력 정압보다 낮아질 수 있다.

## CoolProp 조합

`thermo.cavitation_inputs_from_coolprop`은 지정 온도의 포화액 상태에서 평형 증기압과 포화액
밀도를 구해 계산기 입력을 만든다. backend·유체·온도·quality, CoolProp 버전·리비전과 반환
물성으로 상태 digest를 만든다. 배관 해석이나 측정에서 얻은 국부 절대 정압과 특성속도는
호출자가 별도로 공급해야 한다. CoolProp은 기포핵이나 금속의 침식 저항을 공급하지 않는다.

`degradation.cavitation_history`는 정렬된 국부 절대압·온도·증기압·액체 밀도·속도 이력을
받는다. 각 표본의 정압 여유와 캐비테이션 수, 최소 여유의 표본 identity를 보존한다. 선언된
선형 구간에서 여유 0의 교차 시각을 구해 연속된 비양수 여유 구간을 합치고, 그 구간의
`max(-delta_p, 0)`을 적분해 `Pa·s` 압력부족 노출량을 계산한다. 무효 표본은 삭제하거나
보간하지 않고 `needs_data`로 중지한다. 한 표본에서 0에 접하고 다시 양수가 되면 가능 상태는
기록하되 지속시간과 압력부족은 0으로 유지한다.

`cavitation_history_inputs_from_coolprop`은 각 온도 표본의 포화액 물성을 별도로 계산하고 표본별
상태 digest와 전체 물성 이력 digest를 만든다. 이 계산의 지속시간과 압력부족은 표본 사이를
선형으로 가정한 수치이며, 미표본 순간압력이나 기포 붕괴 에너지를 나타내지 않는다.

`adapters.cavitation_history_inputs_from_operating_history`는 `OperatingHistory`의 자산·부위·시계,
측정/예측 기원과 원본 digest를 유지한 채 위 CoolProp 조합기로 연결한다. 공정 압력 채널이
해당 위치의 절대 정압이라는 검토 선언과 같은 시계의 양의 특성속도 이력이 모두 필요하다.
용기 대표압, 정체압, 게이지압 또는 위치가 다른 압력을 국부 정압으로 자동 해석하지 않는다.
공개 교환 계약은 `docs/schemas/CavitationHistory.json`이다.

```python
from matintegrity.thermo import cavitation_inputs_from_coolprop

inputs = cavitation_inputs_from_coolprop(
    fluid="Water",
    temperature_K=300.0,
    local_static_pressure_Pa=80_000.0,
    characteristic_velocity_m_s=12.0,
    local_pressure_definition="reviewed CFD cell absolute static pressure",
    velocity_definition="reviewed throat area-average velocity",
)
```

정상상태와 이력의 전체 실행 예는 `examples/cavitation_margin.py`다. 수식과 CoolProp 조합의 재현 기록은
`scripts/validate_cavitation.py`와 `validation/cavitation_math.json`에 있다.

## 남은 검증

- 실제 압력 센서·CFD의 시간 해상도와 최소 국부압력 검토
- 용존가스·기포핵·표면 거칠기·유체 오염에 따른 inception 자료
- 기포 붕괴 강도와 재료별 incubation·침식률 보정
- 펌프 NPSH나 터보기계 공급자 정의와의 별도 계약
- 독립 장치·재료·운전 조건의 보류 실험 비교

따라서 이 기능은 `degradation.cavitation` 전체 중 열역학 선별 하위 기능으로만 기록한다.

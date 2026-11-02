# Wet-CO₂ 기–액 2막 물질전달 계산

## 목적

`matintegrity.wet_co2_two_film_transfer.v1`은 한 상태에서 caller가 제공한 CO₂ fugacity, 용존 `CO2*` 농도, Henry 계수, 기상막 계수, 액상막 계수로 기–액 경계의 정상상태 물질전달 플럭스를 계산한다. Henry 관계는 다음 농도/압력 convention으로 고정한다.

```text
H = C* / f_CO2
```

즉 `H`의 단위는 `mol/(m^3 Pa)`이다. 가스 fugacity는 CoolProp 또는 다른 승인된 공급자에서 계산해 caller가 명시적으로 전달할 수 있다. 이 모듈은 어떤 물성 공급자도 자동 호출하지 않는다.

## API

```python
from matintegrity.wet_co2_two_film_transfer import (
    WetCo2TwoFilmTransferRequest,
    evaluate_wet_co2_two_film_transfer,
)
```

요청에 제공하는 값은 다음과 같다.

- `co2_fugacity_Pa`: 해당 기상 조성·온도·압력에서의 CO₂ 성분 fugacity
- `bulk_co2star_mol_m3`: 액상 벌크의 중성 용존 CO₂* 농도
- `henry_concentration_over_fugacity_mol_m3_Pa`: 선택한 용매·온도 기준의 Henry 데이터
- `gas_film_coefficient_mol_m2_s_Pa`: fugacity 차 기준 가스막 전달계수
- `liquid_film_coefficient_m_s`: 농도 차 기준 액막 전달계수
- `temperature_K`, 시간·자산·위치·조건 식별자, Henry/fugacity 공급자 식별자, 용매 조성 digest, `Evidence`
- 기–액 상과 면적 기준, fugacity/Henry convention, 온도·용매 일치 및 막 계수 적용성을 확인하는 네 검토 플래그

## 계산식

기막 flux와 액막 flux를 같은 정상상태 계면에서 같다고 둔다.

```text
J_g = k_g (f_b − f_i)
J_l = k_l (H f_i − C_b)
J_g = J_l = J
```

여기서 `f_b`, `C_b`는 벌크 기체 fugacity와 액상 `CO2*` 농도이고, `f_i`는 계면 fugacity다. 이에 따른 액상 기준 종합 전달속도와 플럭스는 다음과 같다.

```text
K_L = 1 / [1/k_l + 1/(k_g H)]
J = K_L (H f_b − C_b)
```

`J > 0`이면 기체에서 액체 방향, `J < 0`이면 액체에서 기체 방향이다. 부호를 절댓값으로 바꾸지 않는다. 출력에는 계면 fugacity/농도와 양쪽 막에서 계산한 플럭스 및 상대 수지 잔차가 포함된다. 계수 조합은 로그 공간에서 계산해 역수·저항 비의 오버플로를 피한다. 결과를 유한 부동소수점으로 표현할 수 없으면 `out_of_scope`로 반환한다.

## 한계와 사용 주의

- Henry 기록은 정확히 `CO2* concentration / CO2 fugacity` convention이어야 한다. 다른 Henry 상수 convention을 암묵 변환하지 않는다.
- fugacity, Henry 데이터, 벌크 액상 농도와 두 막 계수는 같은 조건·면적 기준에 적용 가능하다는 근거가 caller 책임이다.
- 한 개의 정상상태 경계만 계산한다. 압력/조성 변화, 기포, 계면적 변화, 유동장, 시간 적분은 포함하지 않는다.
- `CO2*`의 bulk speciation, 탄산 평형, 활동도, 산도, 수화 반응은 계산하지 않는다.
- 반응속도나 scale transport와 결합하지 않으며, 부식률·금속손실·벽두께·수명·위험확률을 추론하지 않는다.
- 계산상 양쪽 막의 수지가 맞더라도 계수의 실험 적합성이나 물리적 모델의 유효성이 확인된 것은 아니다.

## 상태

독립 모듈과 본 문서만 추가했다. 중앙 registry·schema·catalog 연결, 테스트, 실제 계산 및 패키징은 수행하지 않았다.

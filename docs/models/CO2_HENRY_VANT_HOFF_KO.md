# CO₂ Henry 용해도 온도 보정

`chemistry.co2_henry_vant_hoff_temperature_correction`은 사용자가 출처를 고정한 CO₂* 농도/기상 fugacity 계수와 용해 엔탈피를 기준 온도에서 목표 온도로 옮깁니다. 엔탈피 부호는 흡열 용해에 양수입니다. 입력 계수의 관례는 `mol/L/Pa`이며, 분모는 부분압력이 아니라 fugacity입니다.

## 입력과 계산

`Co2HenryTemperatureReference`는 기준 Henry 계수, 기준 온도, 용해 엔탈피, 선택적인 일정 용해 열용량 변화, 적용 온도 범위, 용매 조성 digest, provider revision/configuration, source-record digest 및 일치하는 `Evidence`를 포함합니다. `Co2HenryTemperatureCorrectionRequest`는 목표 온도와 계수 관례·용매 조성·열화학 범위에 대한 검토를 전달합니다. 출처 데이터나 계수 표는 코드에 내장되지 않습니다.

엔탈피가 일정하다고 가정할 때:

`ln(H(T)/H(Tref)) = ΔH/R × (1/Tref - 1/T)`

일정한 `ΔCp`를 제공하면 다음 항을 더합니다:

`ΔCp/R × (ln(T/Tref) + Tref/T - 1)`

이 식은 van't Hoff 관계를 지정한 물질 전이의 열역학 데이터로 적분한 형태입니다. 계산 결과는 `H(T)`와 적용 범위 안의 보정계수, 기준 기록 및 파라미터 계보 digest를 포함합니다. 고정 fugacity carbonate equilibrium API의 Henry record를 만들 때, 파생값/온도/출처와 이 API의 result digest를 명시해 별도 `Co2HenrySolubilityRecord`로 구성해야 합니다.

## 적용 한계

- 목표 온도는 기준 열화학 기록의 선언된 범위 안에 있어야 합니다. 범위 밖에서는 외삽하지 않습니다.
- 엔탈피·열용량 변화·용매 조성은 caller가 제공하고 근거를 연결합니다. 모델은 표준염수 자료나 salting-out parameter를 제공하지 않습니다.
- 일정 용해열용량 항을 제공하면 caller가 해당 근사의 사용을 검토해야 합니다. 열용량 데이터의 온도 의존성은 계산하지 않습니다.
- 활동도, mixed-solvent fugacity, 기상 EOS, carbonate pH, 전달속도, scale, 부식률과 재료 응답은 여기서 계산하지 않습니다.

## 기술 근거와 재사용

온도별 평형상수의 van't Hoff 형태는 [IDAES equilibrium constant documentation](https://idaes-pse.readthedocs.io/en/2.13.0/explanations/components/property_package/general_reactions/equil_constant.html)에 근거해 직접 구현합니다. 보편 기체상수 값은 [NIST CODATA](https://physics.nist.gov/cgi-bin/cuu/Value?r%7Csearch_for=R)와 연결합니다. 문장, 표, 매개변수 값 또는 실행코드를 복제하지 않았습니다. 사용자는 자신의 Henry 상수와 열화학 데이터의 라이선스·조건 적합성을 별도로 확인해야 합니다.

# 비등온 산화와 단열 결로노출

## 비등온 포물선 산화

`degradation.nonisothermal_parabolic_oxidation`은 caller-owned `m²/s` 포물선 속도계수 표와 순서 있는 온도 이력을 받는다. 각 선형 온도 구간을 표의 온도 knot에서 분할하고 선형 보간된 `k(T)`를 정확히 적분해 `x²-x₀²`를 계산한다. 표 밖 외삽은 금지한다.

재료상태·표면상태·환경, provider 판본과 네 digest, calibration/holdout 시편·source group을 보존한다. 포물선 scale 유지가 검토되지 않으면 중지한다. Spallation, breakaway, 금속소모, 합격, 잔여수명과 확률은 포함하지 않는다.

## 단열 외표면 결로노출

`fabrication.insulation_condensation_exposure`는 외표면 온도, ambient dew point와 weather-barrier 상태가 명시된 구간만 계수한다. 표면온도-이슬점 margin과 두 온도 불확도를 보수적으로 뺀 margin을 함께 반환한다. 기록 공백·무효 구간은 정상상태로 보간하지 않는다.

`thermo.insulation_condensation_inputs_from_coolprop`는 dry-bulb K, 상대습도 fraction과 절대압 Pa에서 CoolProp `HAPropsSI` 이슬점을 생성한다. CoolProp 판본·리비전과 상태 digest를 입력에 남긴다. 이슬점 계산은 물 유입, 단열재 습윤, 건조, CUI 부식률, coating failure, 합격, 수명 또는 고장확률 모델이 아니다.

# 크리비스 wall-sink rate parameter 불확도 전달

## 목적

보정된 Arrhenius wall-transfer velocity와 그 exact-knot rate history를 입력으로 받아, calibration이 제공한 `(ln(k_ref), E_a)` parameter covariance를 온도별 `k_w(T)`의 국소 표준불확도로 1차 전달한다. fitting 결과와 적용 history의 digest를 모두 확인해 동일 calibration 결과의 parameter uncertainty만 사용한다.

모듈은 시간/위치별 rate를 새로 산출하지 않는다. 이미 계산된 exact knot의 속도에 대해 다음 sensitivity를 이용한다.

`g(T) = [1, -(1/R) * (1/T - 1/T_ref)]`

`Var[ln k(T)] = g(T) @ Cov(ln k_ref, E_a) @ g(T).T`

반환하는 `linearized_velocity_standard_uncertainty_m_s`는 `k(T) * sqrt(Var[ln k(T)])`이다. 이는 1차 delta-method 결과다.

## 입력과 lineage

- Python 모듈: `matintegrity.crevice_wall_sink_rate_uncertainty`
- 입력: `CreviceWallSinkRateUncertaintyRequest`
- 계산: `propagate_crevice_wall_sink_rate_uncertainty()`
- ModelSpec: `specifications()`
- 모델 ID: `integration.crevice_wall_sink_rate_parameter_uncertainty`
- source ID: `caller_crevice_wall_sink_arrhenius_parameter_covariance_propagation`

요청은 원 `CreviceWallSinkArrheniusCalibrationRequest`, 전체 calibration Calculation과 canonical SHA, `crevice_calibrated_wall_sink_history`의 전체 계산결과와 SHA를 포함한다. Evaluator는 calibration을 원 관측으로 재계산해 result digest를 확인하고, rate history의 calibration fit digest 및 nested result digest도 검사한다. covariance 행렬은 유한하고 대칭이며 양의 준정부호여야 한다.

세 review gate는 parameter covariance 적용, 1차 선형화 방식, 결과가 확률이 아니라는 해석을 명시적으로 확인한다.

## 출력 해석과 한계

각 exact-knot 결과는 온도, 시간, wall-transfer velocity, `ln(k)` parameter standard uncertainty, 그리고 이를 속도 단위로 선형화한 표준불확도를 포함한다. covariance는 calibration fit에 기록된 calibration row 및 가중치 해석만 반영한다.

정규분포/로그정규분포는 가정하지 않는다. 신뢰구간, 확률, acceptance, qualification, 모델 불일치, 외부 condition-transfer, systematic bias, Ksp/speciation 불확도 또는 반응기작 불확도를 포함하지 않는다. 해당 보정 parameter의 불확도가 완전하다는 뜻도 아니다. 추가 오차항이나 분포가 필요하면 별도의 caller 근거와 모델을 마련해야 한다.

요청/결과 digest 또는 fit lineage가 맞지 않거나, covariance가 비대칭·비유한·PSD 위반이면 계산을 닫는다. 계산 중 수치 범위를 벗어나도 해당 knot의 prefix까지만 반환한다.

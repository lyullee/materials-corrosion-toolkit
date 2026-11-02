# 크리비스 유효 벽면 sink 속도 Arrhenius 보정

## 목적

관측 또는 별도로 산출되어 caller가 이미 유효 벽면 전달속도로 해석한 `k_w` 자료를 받아 Arrhenius 온도 의존 파라미터를 보정한다. 여기서 속도는 `m/s`이며 기존 1차 벽면 sink API의 유효 전달속도와 같은 단위를 쓴다.

이 모듈은 아래 한 개 법칙을 가정한다.

`k_w(T) = k_ref * exp[-E_a/R * (1/T - 1/T_ref)]`

활성화에너지는 비음수로 제한한다. `T_ref`는 calibration 온도 범위 안에 지정한다. 피팅은 `ln(k_w)`를 `1/T - 1/T_ref`에 대해 weighted least squares로 수행한다.

## 입력 계약과 lineage

Python 모듈 `matintegrity.crevice_wall_sink_arrhenius_calibration`의 typed 입력은 `CreviceWallSinkArrheniusCalibrationRequest`이며 evaluator는 `fit_crevice_wall_sink_arrhenius()`다. `specifications()`가 ModelSpec을 반환한다.

모든 observation에는 고유 `observation_id`, `source_group_id`, calibration/holdout partition, 온도(K), 양의 벽면 속도(m/s)가 필요하다. 최대 5,000행을 지원한다. calibration/holdout source group은 서로 겹치지 않아야 한다. calibration에는 세 개 이상의 서로 다른 온도와 caller가 선언한 최소 온도 폭이 필요하며, 최소 한 개 holdout을 요구한다. holdout 온도는 calibration 범위 안에 있어야 하며 fit에는 전혀 사용하지 않는다.

optional `log_velocity_standard_uncertainty`는 각 행의 `ln(k_w)` 표준 불확도다. 입력되면 역분산을 weight로 사용한다. 미입력 시 unweighted residual scatter로 parameter covariance를 산출한다. Evidence와 review gate는 측정치가 유효 벽면 속도로 매핑된 근거, 공통 표면/유체 조건, 온도 적용범위, 사전 분할, Arrhenius 가정 및 데이터 사용권한을 caller가 확인했음을 기록한다.

## 결과

성공 결과는 `reference_wall_transfer_velocity_m_s`, `reference_temperature_K`, `activation_energy_J_mol`, parameter covariance, calibration/holdout 로그속도 RMSE, 온도 support 및 행별 measured/predicted residual을 포함한다. `holdout_used_in_fit=False`, `prediction_extrapolation_performed=False`로 holdout과 예측 경계도 기록한다.

최소 표본/온도 폭이 부족하면 `needs_data`를, 온도 extrapolation이나 음의 fitted activation energy처럼 계약 범위와 맞지 않는 경우 `out_of_scope`를 반환한다. holdout이 calibration source group과 겹치면 누수로 보고 닫는다.

## 사용 연결

성공한 `reference_wall_transfer_velocity_m_s`, `reference_temperature_K`, `activation_energy_J_mol`은 후속으로 별도 review한 뒤 `crevice_wall_sink_rate_history` 입력에 옮길 수 있다. Fit 결과가 자동으로 downstream calculation에 연결되거나 검증되지는 않는다. 각 단계에서 사용자는 동일 표면 상태, 유체 조성, 표준상태, 반응 기작 및 온도 지원범위가 맞는지 확인해야 한다.

## 제한

자료는 단순히 `m/s` 차원을 가진다는 이유만으로 벽면 전달속도 입력으로 적합해지지 않는다. 침투율, 금속손실률, 전류, 용해 flux에서 `k_w`를 만드는 물질수지/표면농도 mapping은 이 모듈 범위 밖이며 별도 근거가 필요하다. 단일 Arrhenius law는 해당 specimen, surface state, fluid chemistry 및 보정 온도 구간에 대한 effective fit일 뿐이다.

이 코드는 보정 자료 바깥의 예측, 벽면 반응 기작, 다성분 경쟁반응, 표면 진화, 부식률, protective-scale 성능, acceptance, 실패확률 또는 engineering qualification을 주장하지 않는다. residual이나 holdout 적합도가 좋더라도 그 자체로 모델 자격을 입증하지 않는다.

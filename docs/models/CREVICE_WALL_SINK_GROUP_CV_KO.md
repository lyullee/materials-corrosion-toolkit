# 크리비스 wall-sink Arrhenius source-group 안정성 진단

## 목적

기존 Arrhenius calibration에서 `calibration`으로 사전 지정된 독립 source group을 하나씩 제외하고, 제외 group을 out-of-fold 관측으로 사용하는 leave-one-group-out 진단을 수행한다. 이 계산은 calibration 결과가 하나의 batch나 특정 source group에 과도하게 좌우되는지 확인하기 위한 것이다.

원래 `holdout`으로 지정한 관측은 모든 fold 계산에서 제외한다. 이 데이터는 기존 calibration 결과의 독립 holdout 성능으로만 보존된다.

## API

- 모듈: `matintegrity.crevice_wall_sink_group_cv`
- 입력: `CreviceWallSinkGroupCVRequest`
- 계산: `evaluate_crevice_wall_sink_group_cv()`
- ModelSpec: `specifications()`
- 모델 ID: `validation.crevice_wall_sink_source_group_stability`
- source ID: `caller_crevice_wall_sink_leave_one_group_out_diagnostic`

요청에는 원 `CreviceWallSinkArrheniusCalibrationRequest`, 그 계산 결과 전체와 SHA-256, 그리고 세 review gate가 필요하다. 입력 결과의 digest와 원 입력 digest를 확인하고 calibration 계산을 재현해 같은 결과인지 다시 대조한다.

모든 source group은 실제로 독립된 측정/캠페인 단위라는 caller review가 필요하다. 최대 100개 calibration group을 처리하며 최소 4개 group을 요구한다. Fold마다 빠진 그룹을 holdout으로, 나머지 predeclared calibration row를 fit set으로 설정한다. 기존 독립 holdout 데이터는 selection에서도 제외된다.

## 계산과 결과

각 fold는 원 calibration과 동일한 wall transfer velocity Arrhenius 모델, Tref, 온도 폭, Evidence 및 uncertainty weights를 사용해 `fit_crevice_wall_sink_arrhenius`를 다시 계산한다. 각 fold는 다음 결과를 보존한다.

- 제외한 source-group ID 및 observation 수
- fold별 참조 wall transfer velocity 및 활성화에너지
- out-of-fold 로그 속도 RMSE와 최대 절대 잔차
- 제외 group의 각 관측 잔차와 재계산 결과 digest

전체 fold를 마치면 out-of-fold 오차 합계와 fold 간 `ln(k_ref)`/`E_a` sample standard deviation을 계산한다. 어느 fold든 충분한 온도 지원, 참조온도 support 또는 full-rank fit을 갖지 못하면 그 이전 fold를 보존하고 `needs_data`로 닫는다.

## 해석 제한

이 diagnostic은 supplied calibration groups 안에서의 group deletion 민감도와 internal out-of-fold error만 측정한다. 독립 외부 데이터 검증, confidence interval, probability, 모델 qualification 또는 다른 재료·표면·유체 조건으로의 전이를 입증하지 않는다. Fold 분할 자체가 적절하려면 group ID의 의미와 독립성이 caller가 확인한 실제 데이터 provenance와 일치해야 한다.

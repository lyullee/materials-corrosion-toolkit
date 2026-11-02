# 크리비스 slit hydraulic parameter fit

## 목적과 범위

`calibration.crevice_slit_hydraulic_law_parameters`는 넓은 평행 slit의 reduced lumped inertance/resistance 모델에 대해 positive global correction multiplier 두 개를 적합한다. caller가 제공한 압력·aperture·유체밀도·점도·기하·초기 유량은 그대로 두고, 기존 예측식을 각각 `R_fit = m_R R_base`, `I_fit = m_I I_base`로 조정한다. fitted 값은 user-model parameter이지 보편 법칙이나 코드 자격이 아니다.

적합은 run별 측정 signed volumetric-flow knot과 caller standard uncertainty를 이용한 weighted least squares다. 적어도 두 개의 독립 calibration group이 필요하다. holdout group은 calibration group과 겹치지 않고 objective에 들어가지 않으며, 계산 후 별도 예측으로 출력된다. 식별 Jacobian rank가 2가 아니거나 optimizer가 수렴하지 않으면 parameter 결과를 만들지 않는다.

## 입력 구성

각 `HydraulicFlowObservationRun`은 하나의 전체 실험 run, 독립성 group, calibration/holdout partition, 기존 `PlanarSlitTransientHydraulicHistory` 요청, 해당 요청의 exact time knots에 정렬된 signed observed flow와 standard uncertainty를 담는다. 관측 payload의 canonical SHA-256을 계산해 `observation_record_sha256`에 넣고, 동일 digest의 source Evidence를 첨부한다. Calibration과 holdout은 통계적 독립성을 사전 검토해야 한다.

모든 run은 같은 material-state/physical-scope ID, time basis, provider IDs/revisions, ordered axial cell grid를 공유해야 한다. Fit support는 calibration partition만으로 계산하며 aperture·pressure drop·density·viscosity·initial flow·interval duration·전체 시간 span의 관측 범위로 기록된다. Holdout 측정값은 parameter fit이나 지원범위 산출에 사용하지 않는다. `apply_hydraulic_parameter_fit`은 target 요청의 물리/provider identity와 고정 grid를 대조하고, 이 support 밖의 압력·간극·유체상태·clock 요청을 extrapolation으로 거절한다.

## 사용 흐름

1. 원시 유량 기록과 각 계측 uncertainty를 단위·부호 convention 검토 후 run record로 고정한다.
2. 시편/run 단위가 아니라 독립 시험 또는 source group 단위로 calibration과 holdout을 나눈다. 같은 group의 반복 측정은 양 partition에 걸쳐 분리하지 않는다.
3. bounds와 적용 가능한 reduced law 범위를 설정해 fit request를 평가한다.
4. 결과 전체의 canonical digest를 계산하고 source ID `calibration.crevice_slit_hydraulic_law_parameters`인 Evidence에 묶는다.
5. `apply_hydraulic_parameter_fit`으로 target hydraulic request에 fitted multipliers를 전달한다. transfer review와 exact result Evidence가 없으면 기존 모델은 non-default parameter를 거부한다.
6. 수정된 `PlanarSlitTransientHydraulicHistory`를 기존 transient slit solver에 넣는다. 해당 request digest는 fitted multipliers와 fit result digest를 포함한다.

## 반환값과 해석

결과에는 `resistance_multiplier`, `inertance_multiplier`, log-parameter의 local covariance, weighted calibration RMS, run별 calibration/holdout prediction과 standardized residual, optimizer 상태, 적용 가능한 calibration support가 포함된다. Covariance는 선택된 모델·가중치·측정 조건에 조건부인 국소 선형 근사다. Holdout이 있어도 전체 모집단, 다른 provider, 다른 geometry family로의 transfer를 보증하지 않는다.

## 제한

이 모델은 Navier–Stokes, 난류, 압축성, entrance/roughness, moving aperture, 반응·부식·열역학, 파손수명 또는 failure probability를 다루지 않는다. Model selection, parameter uncertainty 밖의 model-form error, measurement covariance, group-level hierarchical variation도 자동 추정하지 않는다. calibration support 밖 적용은 금지하며, caller는 목적별 근거·권리와 applicability를 검토해야 한다.

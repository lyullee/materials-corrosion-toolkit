# 소성·POD·CTMC 보정 심화

## 순환 Ramberg–Osgood

`materials.cyclic_ramberg_osgood_fit`은 안정화된 응력진폭과 양의 소성변형률진폭을 자연로그 공간에서 가중 적합한다. `K′`와 `n′`은 calibration 자료만 결정하며 holdout은 log-stress bias와 RMSE에만 사용한다. 소성변형률을 `total-strain minus stress/E`로 만들 때 응력과 탄성계수의 unit token은 정확히 같아야 한다.

Calibration과 holdout의 물리 시편, source group, independence group은 겹칠 수 없다. Holdout이 calibration 소성변형률 범위를 벗어나면 외삽하지 않는다. 결과는 안정화 단축 진폭관계이며 이력 구성모델, 다축 소성, 피로수명, 합격 또는 확률이 아니다.

## Signal-response POD

`inspection.signal_response_pod_calibration`은 고정된 caller threshold와 `signal = β₀ + β₁ ln(size) + normal residual`을 사용한다. Uncensored calibration 관측만 적합하며 censored/missing 관측은 ID와 근거를 남기고 대체하지 않는다. Holdout에서 detection classification, log score, Brier score와 표준화 잔차를 계산한다.

POD query와 target-POD size는 caller qualification support 안에서만 제공한다. `detection_given_flaw_and_procedure` 의미는 독립 현장 검증, 규격 합격이나 일반 검사 확률을 뜻하지 않는다.

## CTMC generator calibration

`reliability.ctmc_generator_calibration`은 각 origin state의 weighted exposure와 directed transition count로 calibration rate를 계산한다. Generator의 대각원소는 행합이 0이 되도록 구성한다. Holdout count는 Poisson negative log likelihood와 deviance로 평가하며 calibration rate가 0인데 holdout 양의 count가 있으면 clipping하지 않고 점수를 보류한다.

이 모델은 generator를 미래로 전파하지 않는다. Stationarity, 독립성, 인과, repair policy, 미래 신뢰도 또는 FTA 확률도 생성하지 않는다. 전파는 자격화 이후 기존 CTMC 모델에 별도 입력해야 한다.

# 관측 기반 가스켓 누설 표면 적합

`GasketLeakageMapFit`와 `fit_gasket_leakage_map()`는 caller가 검토한 관측 누설 flux로 비음수 bilinear knot table을 적합한다. 접촉압력과 차압 축은 0에서 시작하고 엄격히 증가한다. 모든 관측은 두 축의 지원범위 안에 있어야 하며 외삽하지 않는다. 원 관측의 flux 단위는 mol/s/m²이고 원 자료 SHA-256, 물리 시편, source group과 observation ID를 보존한다. 원 누설률에서 면적을 추정하거나 자동 환산하지 않는다.

각 관측의 네 bilinear 보간 가중치가 design matrix 행을 구성한다. Calibration 행의 `(예측-관측)/residual_scale` 제곱합을 최소화하며 모든 knot flux를 0 이상으로 제한한다. 잔차 scale은 caller의 양수 가중 척도이며 측정 표준편차라는 의미를 자동 부여하지 않는다. NumPy와 SciPy가 실행 시 필요하고 `scipy.optimize.lsq_linear`를 사용한다. 계산기는 모델식과 보간 기저를 독립 작성하며 제3자 데이터·표·계수를 포함하지 않는다.

모든 knot 계수를 식별할 수 있는 calibration design rank가 필요하다. Rank 부족은 needs_data이며 map을 반환하지 않는다. 동일 물리 시편 또는 source group이 calibration과 holdout에 걸치면 입력을 거부한다. Holdout은 적합에 들어가지 않고 같은 지지범위에서 예측과 signed residual만 기록한다. 시편당 반복 관측이 독립 실험 개수를 늘리는 것으로 해석하지 않는다. 각 partition은 사전에 선언되고 caller가 근거를 검토해야 한다. Holdout 행이 없어도 계산은 가능하지만 독립 평가 근거가 생기지는 않는다.

결과 `calibration_map`은 기존 `GasketLeakageCalibrationMap` 형태이며 map content digest를 함께 반환한다. Provider/조건/면적/압력 방향이 실제 적용 joint와 일치하는지는 기존 leakage API에 넘기기 전에 별도 검토한다. 비음수 제한은 단조성, 영 차압에서 영 flux, 물리 메커니즘, constitutive transfer, 신뢰구간, 밀봉 acceptance 또는 qualification을 부여하지 않는다. Solver 미완료와 비유한 수치 결과는 out_of_scope이며 미완성 map을 공개하지 않는다.

개발 상태: 계산 코드와 registry·source catalog·capability·schema 연결이 완료됐다. Solver의 rank 진단 또는 제한 최소제곱 계산이 수치 오류로 종료되면 map을 반환하지 않도록 한다. 테스트, 수치 실행, 공개 데이터 적합, 실험 검증, 패키징은 수행하지 않았다. 이후 검증에서는 정확한 합성 knot recovery, rank 부족, boundary nonnegative fit, calibration/holdout 누출 거부, 지원범위 및 수치 극단값을 다룬다.

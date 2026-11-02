# Gasket 누설 correlated scenario uncertainty

`GasketLeakageCorrelatedScenarioEnvelope`와 `evaluate_gasket_leakage_correlated_scenarios()`는 기존 gasket leakage calibration table 및 node별 leakage flux 경로에 완전한 joint scenario를 적용한다.

각 `GasketLeakageCorrelatedScenario`는 하나의 시나리오 ID 아래 모든 순서 node의 contact pressure·contact area, 공통 differential pressure, 전체 contact-pressure×differential-pressure calibration flux grid를 함께 가진다. 각 시나리오의 누설률은 해당 scenario-specific calibration 표를 기존 bilinear interpolator로 평가하고 node area를 곱해 합산한다. 최솟값·최댓값과 witness scenario를 돌려준다. 시나리오 입력 전체는 canonical SHA-256 및 provider Evidence에 결속하고, 원 calibration record digest와 사용권 Evidence도 별도로 보존한다.

## 명시적 가중치를 가진 유한 시나리오 집합

`GasketLeakageWeightedScenarioMoments`와 `evaluate_gasket_leakage_weighted_scenario_moments()`는 위의 완전한 joint scenario 묶음에 순서가 고정된 양의 가중치를 연결한다. 가중치는 이미 합이 1이어야 하며 자동 재정규화하지 않는다. 가중치의 의미(`empirical_frequency`, `quadrature_weight`, `user_declared_weight`), 공급자 revision, 레코드 digest, 사용권 근거를 별도로 제공하고 검토 플래그를 모두 통과해야 한다.

각 시나리오의 기존 leakage 계산 결과를 `qᵢ`, 입력 가중치를 `wᵢ`라 할 때 평균은 `Σwᵢqᵢ`, 모집단 분산은 `Σwᵢ(qᵢ−μ)²`로 계산한다. 출력은 표준편차와 유한 집합에서의 최소·최대 및 witness도 보존한다. 이는 제출된 유한 가중 집합의 기술통계이며, 고장확률·신뢰구간·연속 불확실성 보증을 뜻하지 않는다. 자료에 없는 확률 해석이나 꼬리 외삽을 만들지 않는다.

```python
from matintegrity.gasket_correlated_uncertainty import (
    GasketLeakageCorrelatedScenarioEnvelope,
    evaluate_gasket_leakage_correlated_scenarios,
)

request = GasketLeakageCorrelatedScenarioEnvelope.model_validate(payload)
result = evaluate_gasket_leakage_correlated_scenarios(request)
```

결과 경계는 **입력한 유한 scenario 집합 안의 exact extrema**다. 같은 scenario 안의 pressure, calibration 변화 및 node area 간 상관관계는 그대로 보존되지만, scenario 간 확률가중치나 확률을 부여하지 않는다. Scenario가 가능한 joint set을 충분히 덮는지는 caller 책임이며, 누락된 영역의 연속 bound나 confidence interval은 계산하지 않는다. calibration axes 바깥은 기존과 같이 거절한다. 시간 적분, contact mechanics, 누설 허용값 및 설계 qualification은 범위 밖이다.

이 API는 사용권 판단을 대신하지 않는다. calibration과 scenario 원자료의 source/license Evidence를 공급하고 공개 사용 권리를 별도로 확인해야 한다. 코드에는 calibration table이나 사용자 원자료를 포함하지 않는다.


## 독립 직사각형 불확실성 집합의 정확 envelope

`GasketLeakageBoxEnvelope` (`fabrication.gasket_leakage_box_envelope`)은 각 contact node의 pressure/area 구간, 하나의 공통 differential-pressure 구간, calibration flux grid의 entrywise lower/upper bound를 입력으로 받아 total molar leak rate의 최솟값·최댓값과 witness를 계산한다. 모든 nominal calibration flux cell은 해당 lower/upper 구간 안에 있어야 하며 source Evidence, usage-rights Evidence, 단위/물리 mapping, box의 의미·coverage 및 계산 승인이 필요하다. 지원 밖 압력 구간은 외삽하지 않고 `out_of_scope`다.

계산은 caller가 선언한 독립 box에 한정한다. 접촉압력은 node마다 독립 범위 안에서 움직이고 차압은 모든 node가 공유한다. 보정표 flux cell 구간은 서로 독립인 entrywise box이며 모든 interpolation weight가 비음수이므로 extrema는 lower grid 또는 upper grid에서 얻는다. 압력축별 bilinear 표는 각 contact-pressure cell 안에서 p에 선형이며, 공통 차압축 cell 안에서 최적화된 lower envelope는 concave, upper envelope는 convex이므로 node 구간 끝점·내부 calibration knots 및 공통 차압 끝점·내부 knots의 조합으로 extrema를 찾는다. Witness는 node별 선택 pressure/area와 공통 차압, 보간 cell을 기록한다.

이 `exact` 표시는 명시한 rectangular input set과 piecewise-bilinear table에 대한 결정론적 최적화다. 압력·면적·보정계수의 상관관계, 표 밖 오차, 공간 접촉 mechanics, 확률분포, 신뢰구간, 장치 누설 acceptance 또는 qualification은 포함하지 않는다. correlated scenario API와 covariance delta method는 서로 다른 입력 의미를 계속 유지한다.

# 확장 요청: 다축 피로 finite scenario API와 law provider 연결

## 구현된 경계

`fatigue.multiaxial_life_scenario_envelope`는 기존 `fatigue.multiaxial_life_campaign`의 computed results를 완전한 finite scenario로 묶고, result/calibration/factor/context digest 및 material/cycle-support consistency를 검사해 finite-set cycle-life extrema를 반환한다. 확률이나 continuous uncertainty bound는 만들지 않는다.

## 후속 세션의 확장

1. 재료별 law/provider profile을 each scenario run에 결속해 callback-based fatigue result도 envelope 입력으로 받을 수 있게 한다. Law revision, configuration digest, calibration/holdout ID, usage license와 material applicability digest를 요구한다.
2. caller가 제공한 full joint scenario generator 또는 measured multiaxial load-history distribution을 읽는 별도 adapter를 추가한다. dependence structure와 scenario weights가 있으면 정의 의미를 분리해 보존한다. Probability output은 별도 calibrated statistical API 없이는 산출하지 않는다.
3. scenario coverage 또는 interval bound를 만들 때 monotonicity/proof가 있는 구간에 한정하고, sampled grid extrema를 continuous bound처럼 보고하지 않는다.
4. independent nonproportional fatigue benchmark와 calibration/holdout 분리 자료를 확보해 scenario-wise prediction error와 support exceedance를 평가한다. 현 core에서 numerical validation은 수행하지 않았다.
5. downstream inspection/risk/FTA 연결에서는 cycle-life amount/range를 event probability로 자동 환산하지 말고, threshold, mission time, demand and action assumptions를 explicit input으로 받는다.

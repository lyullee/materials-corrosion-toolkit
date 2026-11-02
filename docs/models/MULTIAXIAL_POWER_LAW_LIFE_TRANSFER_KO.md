# 다축 피로 참조 수명 곡선의 paired-data 이전

## 목적

`fatigue.multiaxial_power_law_life_transfer`는 계산 완료된 `fatigue.multiaxial_calibration_transfer_audit` 결과와 참조 재료의 caller 수명곡선을 조합해, 참조/대상 재료 조건 사이에서 한정된 empirical life-transfer curve를 생성합니다. 선행 audit는 동일 fatigue parameter knot에서 짝지은 두 조건 수명을 요약하고, 이 API는 그 완전한 paired data를 사용해 별도 log-linear 이전 관계를 적합합니다.

이 계산은 특정 caller의 paired 실험 데이터를 요약하여 대상 곡선의 후보를 만드는 도구입니다. 보편적인 재료 전이 법칙, code design curve 또는 새 재료의 qualification을 제공하지 않습니다.

## 입력 및 추적성

- computed paired calibration-transfer `AssessmentResult`와 전체 result SHA-256
- exact parameter knot별 positive reference/target cycles와 audit에 이미 보존된 caller weight
- reference material condition, target material condition, parameter 정의/단위 및 두 시험 context ID
- source/revision/record/digest/Evidence/license가 연결된 reference life curve
- paired reference 관측과 reference curve 수명 사이 최대 허용 절대 log 잔차
- curve/paired knot 정합성, parameter 동일 의미, transfer 함수형, 두 재료 조건 사이 적용성, 권리 및 computational-use 검토

reference curve knot 수와 paired observation 수는 같아야 하며 각 parameter 값이 정확히 일치해야 합니다. 참조 curve의 모든 knot은 짝지은 data에서 관측돼야 합니다. 누락 parameter knot을 interpolation하거나 지원 범위 밖을 extrapolation하지 않습니다.

## 계산

짝지은 관측에서 `N_r`는 참조 조건 수명, `N_t`는 대상 조건 수명, `w`는 audit에 고정된 양의 normalized weight입니다. 두 조건 사이에 아래 단일 log-linear 구조를 caller가 승인하면, weighted least squares로 절편 `a`와 지수 `b`를 계산합니다.

```text
log(N_t) = a + b log(N_r)
N_t,transferred = exp(a) × N_r,reference^b
```

모델은 `b > 0`이고 유한한 경우만 적용합니다. 이 관계를 reference curve의 각 정확한 life knot에 적용해 transferred target curve를 만듭니다. 참조 곡선과 paired reference observation의 차이는 `abs(log(N_r,observed) - log(N_r,curve))`로 구하고, caller 한도를 초과하면 계산하지 않습니다. 두 수명 변수의 log fit residual과 curve/pair 일치 residual은 별도 출력합니다.

## 결과 사용

`transferred_target_curve`의 각 행은 기존 fatigue parameter 값, 참조 cycle 수 및 추정된 target cycle 수를 표시합니다. `target_life_power_exponent`, `log_target_life_intercept`, weighted log RMSE와 pair별 residual은 적합 상태를 검토하는 용도입니다. 대상 곡선은 오직 paired parameter 범위의 참조 곡선 knot에서만 나옵니다.

## 적용 한계

- 정확한 같은 parameter 정의/단위와 동일 physical scope/location에 있는 paired life 관측만 사용합니다. reference와 target 조건이 다른 이유/시험 프로토콜 차이를 자동 보정하지 않습니다.
- 이 API는 caller가 지정한 두-parameter power relation만 적합합니다. 잔차가 작아도 power law가 실제 물리법칙임을 증명하지 않으며, 다른 parameter 범위나 재료로 일반화할 수 없습니다.
- weights는 caller가 제공한 normalized descriptive weights입니다. uncertainty, confidence/prediction interval 또는 failure probability를 계산하지 않습니다.
- 입력 audit의 paired parameter knots와 reference curve knots가 완전히 같아야 합니다. knot 보간, 시험자료 밖 parameter 범위 및 life extrapolation은 없습니다.
- 참조 curve와 paired reference values의 일치 기준은 caller가 고릅니다. 이 기준을 통과해도 target model 독립 holdout validation을 대체하지 않습니다.
- Miner damage, cycle counting, mean-stress correction, fatigue acceptance, design-code compliance 및 material qualification을 산출하지 않습니다.

## 독립 방법 참고자료

- NIST/SEMATECH, *e-Handbook of Statistical Methods*, “Weighted Least Squares Regression.” WLS가 caller 제공 observation weights를 이용하는 회귀 목적과 weighting 해석을 참고합니다. [NIST 공식 문서](https://itl.nist.gov/div898/handbook/pmd/section1/pmd143.htm)
- NIST/SEMATECH, *e-Handbook of Statistical Methods*, “Weighted Least Squares.” 일반 weighted least-squares objective를 설명하는 회귀 방법 자료입니다. [NIST 공식 문서](https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd432.htm)

이 자료는 일반 회귀 방법을 설명하는 배경으로만 참고했습니다. fatigue material data, curve, coefficient, threshold 또는 문장을 복사하지 않았습니다. 실제 paired data 및 사용권은 caller가 별도 확보해야 합니다.

## API 계약

- 모듈: `matintegrity.multiaxial_power_law_life_transfer`
- 모델 ID: `fatigue.multiaxial_power_law_life_transfer`
- 스키마: `matintegrity.multiaxial_power_law_life_transfer.v1`
- 입력: `MultiaxialPowerLawLifeTransfer`
- 참조 곡선 knot: `ReferenceMultiaxialLifeCurvePoint`
- 평가기: `evaluate_multiaxial_power_law_life_transfer(request)`
- 메타데이터 함수: `specifications()`
- source ID: `computed_digest_pinned_multiaxial_paired_life_audit`, `caller_reference_condition_multiaxial_parameter_life_curve`, `weighted_log_linear_paired_life_transfer`
- 실행 검증 및 패키징은 별도 작업입니다.

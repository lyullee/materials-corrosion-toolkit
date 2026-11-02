# 수명 적합·민감도 안정성·실가스 압력감쇠

이 문서는 사용자가 소유하고 적용성을 검토한 자료를 세 보정 계산기와 하나의 CoolProp 조합기에 연결하는 계약을 정의한다. 패키지는 규격표·재료상수·현장 합격기준을 내장하지 않는다. 예제 입력은 계약 검사용 합성값이며 설계·수명 판정 근거가 아니다.

## Strain–life 계수 적합

`materials.strain_life_coefficient_calibration`은 calibration failure의 분리된 탄성·소성 변형률 amplitude만으로 Coffin–Manson–Basquin 계수를 두 단계 가중 log-linear 회귀로 적합한다. 주기수는 식의 `2N`으로 변환되므로 cycles/reversals 정의를 반드시 검토한다. 탄성계수와 호출자의 탄성계수가 같은 stress unit을 쓴다.

- calibration/holdout 간 specimen, source group, independence group 재사용을 금지한다.
- runout과 censored record는 보존하지만 failure로 대체하거나 계수 적합에 쓰지 않는다.
- holdout failure는 calibration cycle support 안에서만 log bias와 RMSE를 산출한다.
- 결과는 수명 합격, 파괴확률, 피로 한도 또는 외삽을 제공하지 않는다.

## 검열 크리프 파단 적합

`creep.accelerated_lognormal_rupture_fit`은 log rupture time을 log inverse stress와 reciprocal temperature의 고정 선형식으로 나타내고, rupture density와 right-censor survival likelihood를 함께 최적화한다. 응력 정의, load control, 재료 상태가 모든 record에서 일치해야 한다.

- calibration과 holdout은 물리 시편·출처·독립성 그룹을 공유하지 않는다.
- 응력–온도 효과가 식별되지 않거나 최적화가 수렴하지 않으면 계수를 반환하지 않는다.
- holdout은 calibration stress–temperature convex hull 안에서만 평가한다.
- 단일 mechanism 가정을 넘는 외삽, 서비스 수명, design allowable과 규격 판정은 제공하지 않는다.

계산기 ID는 상위 능력 ID `structural.creep_rupture_fit`과 의도적으로 분리했다. 하나의 제한된 적합기가 있다는 이유로 크리프 파단 기술 전체를 완료로 표시하지 않기 위해서다.

## Sobol replicate 안정성

`reliability.sobol_replicate_stability`는 외부에서 계산된 first-order·total-order Sobol index의 독립 replicate를 축약한다. output, parameter distribution, dependence assumption, design family, evaluator revision/configuration digest가 같은 replicate만 합친다. 매개변수별 평균·표본표준편차·범위, 보고된 estimator uncertainty와 replicate 간 순위 안정성을 사용자 허용값과 비교한다.

이 계산기는 Sobol index를 새로 추정하지 않고 수렴을 증명하지 않는다. 의존 입력의 인과효과, 모델 부정확성, 기초사건 확률은 별도 평가 대상이다.

## CoolProp 실가스 압력감쇠 조합

`thermo.gas_pressure_decay_inputs_from_coolprop(...)`는 초기·최종·기준 상태의 절대압 Pa와 온도 K를 CoolProp `PropsSI`/`PhaseSI`에 넘겨 compressibility factor `Z`와 phase를 얻는다. 음수 `Z`, 미정 phase, two-phase 상태를 거절하고 provider version·revision·backend·fluid와 canonical state digest를 `inspection.gas_pressure_decay`의 입력에 보존한다.

이 경로는 검토된 용기부피에서 실가스 재고량 변화를 압력·온도 변화와 구분하기 위한 수지다. 누설 경로, 유출계수, 오리피스 유량, 탐지확률, 합격기준 또는 파괴확률을 만들지 않는다.

## 재현과 후속 검증

각 모델의 strict JSON 예제는 `examples/model_inputs.json`에 있다. 현재 자료는 소프트웨어 계약과 수학적 거절 경계를 검사하는 합성 자료다. 누리온에서는 전체 registry/example 재생, 선택 의존성 환경, Slurm 분할 검사와 집계를 완료한 뒤 배포물을 다시 만든다. 실제 시편에 대해서는 calibration/holdout 분리, 시험조건·검열의 자격화, 독립 반복을 추가해야 한다.

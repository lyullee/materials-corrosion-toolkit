# 검사 두께의 Bayesian 선형 갱신

## 목적

`reliability.bayesian_linear_thickness_update`는 한 물리 위치의 반복 두께 관측으로 기준시점
잔여두께와 일정 두께손실률의 Gaussian 사후분포를 계산한다. 검사 결과를 이후 구조·신뢰도
모듈에 전달하기 위한 제한된 첫 경로다. 일반적인 부식성장, 균열성장, 비선형 상태공간 모형
전체를 구현했다는 뜻은 아니다.

상태는 기준시점 두께 `T_ref`와 손실률 `r`이며 관측식은 다음과 같다.

```text
T(t) = T_ref - r (t - t_ref) + measurement error
```

양의 `r`은 두께 손실을 뜻한다. prior 평균·표준편차·상관은 사용자가 근거와 함께 공급한다.
측정오차는 각 관측의 표준편차와 독립 선언을 사용하거나, 보정 partition 행 순서에 맞춘
검토된 양의 정부호 전체 공분산을 사용한다. 두 방식을 동시에 입력할 수 없다.

## 관측과 분할

각 `ThicknessObservation`은 관측 ID, campaign, 물리 위치, 경과시간, 잔여두께, 측정
표준편차, 측정법, 교정 ID, source group, 원본 SHA-256과 `update`/`holdout` partition을 보존한다. 모든 관측은
같은 물리 위치여야 하며 ID가 중복되면 거절한다. `update` 행만 사후분포에 들어가고 `holdout`
값은 잔차와 표준화 잔차에만 쓰인다.

보류 source group이 보정 source group과 겹치면 결과는
`not_independent_source_group_overlap`으로 남는다. 겹치지 않더라도 호출자가 독립성을
검토하지 않았으면 `unreviewed_source_group_independence`다. 이는 값을 버리거나 독립 검증으로
자동 승격하지 않기 위한 계약이다.

## 출력과 확률 의미

출력은 두 상태의 사후 평균·공분산·표준편차·상관, 손실률이 양수일 사후 모수확률, 지정한
시각의 두께 평균·표준편차·신용구간을 포함한다. 검토된 요구두께를 공급하면 각 지정 시각에서
`P(T(t) < T_required | supplied model and data)`를 계산한다.

이 확률은 `point_in_time_state_probability`다. 기간 중 처음 요구두께를 통과할 확률, FTA
기본사건 확률, 검사주기 내 고장확률 또는 관측된 빈도가 아니다. 그런 변환에는 시간경로,
과정잡음, 개입·수리, 모델형식과 관련 고장모드의 별도 계약이 필요하다. 손실률 양수 확률은
`posterior_parameter_probability`이며 역시 고장확률이 아니다.

## 검토 게이트와 한계

prior 근거 ID와 원본 SHA-256, 선형모델·측정오차·예측지원 ID, 일정 선형모델, 관측 identity,
측정오차모델과 예측시간 지원을 모두 검토해야 한다.
요구두께가 있으면 그 근거도 검토해야 한다. 하나라도 없거나 시험 유효성이 미검토이면
`needs_data`다. 공분산은 대칭·대각 정합·양의 정부호를 검사한다.

## 과정잡음 포함 순차 상태공간 갱신

`reliability.linear_thickness_state_space_update`는 같은 두 상태를 시간순으로 갱신하지만, 검사 사이
각 구간에 사용자가 검토한 2×2 과정잡음 공분산률을 경과시간만큼 누적한다. 상태전이는
`T_next = T_now - r Δt`, `r_next = r_now`이고, 두께와 손실률의 과정 공분산도 보존한다. 각 update
관측에는 scalar Kalman 갱신과 Joseph 공분산 식을 적용한다. holdout 행은 해당 시각까지 상태를
전파해 one-step-ahead 잔차를 계산하지만 상태를 갱신하지 않는다.

관측은 한 물리 위치에서 엄격히 증가하는 시간순서여야 한다. 현재 계약은 독립 측정오차만 지원하며,
과정잡음 공분산률은 외부에서 공급·검토한다. 필터가 이를 자료에서 추정하지 않는다. 출력은 분석
종료시점의 상태 posterior와 미래시각별 평균·표준편차·신용구간·특정시점 임계두께 미달확률이다.
후자는 여전히 최초도달확률이 아니다.

`gaussian_thickness_posterior_sample_inputs`는 이 상태공간 posterior도 아래 공동표본 계약으로
연결한다. 현재 구현에는 smoother, EM/MLE 과정잡음 적합, 시간가변·비선형 전이, 다중 위치 공간상관,
개입·수리와 POD가 없다.

## Gaussian posterior 공동 표본

`reliability.gaussian_thickness_posterior_sample_design`은 검토된 2변량 Gaussian posterior의
기준시점 두께와 부호 있는 일정 손실률을 공동으로 표본화한다. 두께-손실률 공분산을 Cholesky
변환으로 보존하고, 평가시점의 잔여두께가 요구두께보다 크며 손실률이 비음수인 행만 받아들인다.
이는 값을 본 뒤 임의로 행을 버리는 것이 아니라 입력 계약에 선언한 조건부분포의 rejection
sampling이다. 고정된 후보 추출 예산에서 요청 표본 수를 채우지 못하면 부분 표본을 반환하지 않는다.

재현성은 라이브러리의 정규분포 함수에 맡기지 않는다. `splitmix64_box_muller_cholesky_rejection_v1`
알고리즘이 64비트 seed, SplitMix64 정수열, 53비트 개구간 균등수, Box–Muller와 2차원 Cholesky의
순서를 고정한다. 입력·posterior 결과·표본설계와 실제 표본 digest를 각각 보존한다. Python 어댑터
`gaussian_thickness_posterior_sample_inputs`는 계산된 Bayesian 결과를 표본 계약으로,
`sampled_linear_thickness_first_passage_inputs`는 완성 표본을 최초도달 계약으로 연결한다.

조건화는 Gaussian posterior와 일정 선형 경로를 그대로 전제로 한다. 과정잡음, 비선형 성장,
개입, 모델형식 불확실성 또는 현장 타당성을 추가하지 않으며, 비음수 손실률 조건의 적절성도 사용자가
검토해야 한다.

## 표본 기반 최초 임계도달 경로

`reliability.sampled_linear_thickness_first_passage`는 별도의 입력 계약이다. 평가시점에 임계두께
위에 남아 있는 동일 위치의 `잔여두께-비음수 손실률` 공동 표본과 정규화 가중치를 받아, 각 표본의
선형 임계도달 시각을 직접 계산한다. 손실률이 0이면 유한 도달시각이 없으며, 양의 손실률이면
`(잔여두께 - 요구두께) / 손실률`을 평가시점에 더한다. 지정 후보시각까지 도달한 표본의 가중치
합이 누적 최초도달 확률이다.

이 경로는 Gaussian 평균·공분산만으로 최초통과를 근사하지 않는다. 표본은 평가시점 생존을 조건으로
한 공동분포여야 하며, 이미 요구두께 이하인 행이 하나라도 있으면 그 행을 삭제하거나 재조건화하지
않고 `needs_data`로 중지한다. 명목 가중치 합이 허용오차 안이면 정규화 계수를 명시해 사용한다.
분포·표본설계 ID, 공동 표본 SHA-256, 사건·물리 범위·시간기준과 입력 digest를 보존한다.

출력의 `forecast_points`는 점추정 기준으로 `inspection.threshold_inspection_schedule`에 직접
전달할 수 있다. 다만 신뢰상한은 계산하지 않으므로 `upper_bound` 일정에는 그대로 사용할 수 없다.
이 변환은 공급된 표본분포의 push-forward일 뿐이다. 위 Gaussian 표본 생성기와 연결할 수 있지만
그 연결도 과정잡음·비선형 성장·개입을 보완하지 않는다.

현재 모델에는 다음이 없다.

- 비선형·시간가변 성장률과 과정잡음 모수의 자료기반 적합
- 온도·유체·운전조건 공변량 및 공간 상관
- 일반부식과 공식·균열의 혼합 또는 결함 생성
- POD, 누락 결함, 검사 편향, 측정 교정 모수 불확실성
- 모델형식 선택·평균화, 개입·수리, Gaussian posterior의 자격 있는 공동 표본 생성
- 실제 공개 검사자료에 대한 보정이나 독립 현장 검증

합성 재현은 `scripts/validate_bayesian_thickness_update.py`가 독립 정보형 해와 사후 평균·
공분산을 대조하고 `validation/bayesian_thickness_update_math.json`에 기록한다. 전용 단위검사는
batch/sequential 동치, 보류값 불개입, 상관 측정오차, review gate, identity와 확률 의미를
검사한다. 이는 수학·소프트웨어 검증이며 실제 부식성장이나 UT 성능의 검증이 아니다.

`scripts/validate_thickness_first_passage.py`는 세 개의 작성 표본에서 정확 도달시각, 누적확률,
최종 후보 이후 질량과 무한 도달 질량을 직접 합산하고 검사시점 선택까지 합성한다. 결과는
`validation/sampled_linear_thickness_first_passage_math.json`에 기록한다. 다음 단계는 같은 CML의
자격 있는 반복 두께자료와 환경·운전 이력을 확보해 source-group 분할을 고정하고, 과정잡음이 있는
상태공간 모형 및 비선형 성장 후보를 보류 비교하는 것이다. 그 뒤에 구조한계상태, 검사효과,
결과·검사비용을 결합한 위험기반 검사계획으로 확장한다.

`scripts/validate_gaussian_thickness_sampling.py`는 독립 작성한 SplitMix64·Box–Muller·Cholesky·
rejection 순회를 등록 계산과 표본 단위로 정확히 대조한다. 결과는
`validation/gaussian_thickness_posterior_sampling_math.json`에 기록한다.

`scripts/validate_thickness_state_space.py`는 과정잡음 0에서 순차 필터를 독립 batch 정보형 해와
대조하고, 과정잡음이 있을 때 직접 전이한 미래 공분산과 holdout 비개입을 검사한다. 결과는
`validation/linear_thickness_state_space_math.json`에 기록한다.

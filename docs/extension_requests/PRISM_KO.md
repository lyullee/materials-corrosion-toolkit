# PRISM 확장 요청

검토한 기준 소스는 `884b0553341beb2d51d1d3c563f86982f378e160`이다. `FrequencyEvent.basis`는 문헌 분류 두 가지만 허용하고 `precomputed_events`도 같은 타입을 받는다. MatIntegrity는 기존 문헌 출처를 위장한 사건 객체를 만들지 않는다.

## 요청하는 동작

`creep.conditional_life`의 확률도 송신할 수 있으나 재료·기구·일정 조건·fresh-material 나이 원점·지원 온도/응력·시간 범위와 `parameter_uncertainty_included=False`를 보존한다. 송신 사건 시각은 원 모델 나이·기간과 같아야 한다. 크리프 파단 메커니즘 하나의 모집단 확률을 전체 누출빈도로 바꾸거나 문헌 전체 빈도와 중복 합산하지 않는다.

`matintegrity.event_probability.v1`을 받는 독립 수신 경로를 추가한다. 기존 `FrequencyEvent`의 필드만 느슨하게 하는 방식보다 사건의 의미를 구분한 입력이 적합하다. 필요한 정보는 `event_id`, `asset_id`, `physical_scope_id`, `failure_mode`, `horizon_start_s`, `horizon_end_s`, `probability_given_survival`, `conditioning`, `model_result_digest`, `common_cause_groups`다.

연간 반복사건 빈도, 최초고장 확률, 시간 의존 위험률, 일정 위험률 근사는 서로 다른 종류로 보존한다. 분포·상관·생존 조건과 근거를 같이 받는다. 등가 위험률을 허용할 때도 근사 선택을 명시하고 문헌 통계로 표시하지 않는다.

`AssessmentResult.probability_semantics`를 수신 시 확인한다. `conditional_first_failure_in_period`만 기간 사건의 후보이며 공간 크기 초과·POD·unscoped·의미 미선언은 직접 수신하지 않는다. Gumbel 면적 초과확률은 같은 노출의 공간 분포이므로 별도 성장·검사·구조 한계상태 연결이 필요하다. Weibull 전달 시각은 원 나이 시계·기간과 일치시킨다.

`reliability.joint_event_probability` 결과를 받을 때는 원 공동분포의 자산·물리 범위·기간·생존
조건, 사건/상위사건 정의, 공급자 판본·source digest와 `common_cause_groups`를 유지한다.
독립 비교값은 민감도 진단이므로 기존 독립 FTA 결과나 새 근거로 저장하지 않는다. 동일 원인의
주변사건과 공동 상위사건을 동시에 더하지 않도록 distribution ID와 result digest로 중복을
검사한다. 실제 공동분포 원문은 `JointEventDistribution` JSON Schema로 교환할 수 있다.

`reliability.continuous_time_markov_chain`에서는 `probability_given_survival`만 기간 중 최초
상위사건 상태 진입확률이다. `top_event_state_occupancy_probability`는 종료시각 점유확률이고,
`expected_transition_counts`는 모델 기대 횟수이므로 기존 `FrequencyEvent`로 보내지 않는다.
상태·생성행렬·초기조건·기간·공급자 digest가 필요한 수신자는
`ContinuousTimeMarkovChain` Schema를 별도 보존한다.

`reliability.piecewise_continuous_time_markov_chain`도 송신 가능한 값은 전체 구간의
`probability_given_survival`뿐이다. 수신 측은 원 구간 순서·경계, 구간별 전이율 근거 ID·공급자
리비전·source digest와 전체 계약 digest를 함께 보존한다. 종료 점유, 경계별 확률, 구간별 기대
전이횟수를 기간 최초고장이나 관측 빈도로 변환하지 않는다. 소비자가 원 동적 모델을 감사해야
하면 `PiecewiseContinuousTimeMarkovChain` Schema를 별도 수신한다.

같은 물리 범위에 대해 문헌 전체 누출빈도와 원인별 모델을 동시에 사용할 경우 대체·분할·조건부 보정 중 어느 방식인지 선언하게 한다. 누출 개구·형태·재고·차단은 검증된 사고 방출 공급자가 담당하며 확률 입력에서 임의 추론하지 않는다.

`reliability.bayesian_linear_thickness_update`의
`probability_below_required_thickness`는 각 예측시점의 상태확률이고
`probability_loss_rate_positive`는 사후 모수확률이다. 둘 다 기간 최초고장확률 계약이 아니므로
현재 `EventProbability`나 PRISM 기본사건 빈도로 직접 수신하지 않는다. PRISM 쪽 확장이
필요하면 자산·물리 위치·요구두께·시각·posterior digest를 보존하는 별도 상태분포 계약과,
최초통과를 계산하는 시간경로 모델을 먼저 정의해야 한다.

## 인수 확인

1. 기존 문헌 경로의 계산과 분류가 유지된다.
2. 기간과 생존 조건이 다른 확률을 혼합하지 않는다.
3. 0과 1의 확률, 기간 누락, 물리 범위 중복을 검사한다.
4. 대체 원인 모델과 기존 전체 누출빈도의 중복 계상을 거절하거나 명시적으로 조정한다.
5. 외부 모델의 미확정·범위 밖 상태가 승인된 시설 위험 결과로 승격되지 않는다.

송신 측은 `probability_event`와 `equivalent_stationary_hazard`에서 확인할 수 있다. 현재 등가 위험률 결과의 `prism_frequency_event_compatible`은 `false`다.
## 중요도 샘플링 확률 수신

`reliability.gaussian_mean_shift_importance_sampling`의 `probability_given_survival`은 입력 사건이
동일 자산·범위·기간·생존조건의 최초사건으로 검토됐을 때만 PRISM 기간 사건 후보로 수신한다.
원 결과의 event ID/definition, design·latent mapping·evaluator identity/digest, 표본 수,
제안 사건 수, 가중치 평균, 전체/사건 ESS, 최대 정규화 가중치와 표준오차를 함께 저장한다.
자기정규화 진단을 주 확률로 대체하거나 0사건 결과를 0위험으로 확정하지 않는다. 가중치 ESS와
정규근사 구간은 입력분포·한계상태·공통원인·결과 불확실성을 포함하지 않으므로 FTA 기본사건의
신뢰상한이나 허용위험 판정값으로 이름을 바꾸지 않는다.

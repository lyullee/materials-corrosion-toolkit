# 결정론적 성능함수 기반 희귀사건 subset simulation

`matintegrity.reliability_sampling.run_subset_simulation(limit_state, request)`는 임의의 결정론적 Python callback을 통해 `P[g(Z) <= 0]`를 추정한다. `Z`는 선언 순서대로 정규화된 독립 표준정규 latent 좌표다. 재료·운전변수의 물리분포·상관구조와 limit state 구성은 호출자가 별도로 검토해 callback에서 매핑한다.

초기 population은 NumPy `PCG64`와 기록된 seed로 생성한다. 다음 단계들은 pCN proposal `Z' = sqrt(1-beta^2) Z + beta U`를 현재 limit-state 임계값 안에서 rejection 방식으로 제한한다. pCN은 표준정규 기준측도에 대해 reversible이므로 복잡한 latent 차원에서 prior density를 별도로 평가하지 않아도 된다. 각 population에서 caller의 conditional fraction을 empirical threshold에 맞춰 선택하고, 단계별 empirical fraction 곱으로 목표 사건 확률을 계산한다.

```python
from matintegrity.reliability_sampling import SubsetSimulationRequest, run_subset_simulation

result = run_subset_simulation(lambda z: reviewed_limit_state(z), reviewed_request)
```

요청은 사건 정의·물리 범위·기간·생존 조건, latent ID 순서, callback revision/configuration digest, seed, 표본 수, 조건부 확률 목표, pCN 계수, 단계 상한과 review flags를 고정한다. 결과는 각 단계 임계값·조건부 비율·seed 수·제안 수락률·누적 추정값과 함께 최종/부분 로그확률을 기록한다. 요청한 단계 안에 event를 관측하지 못하거나 threshold가 정체하면 결과를 `needs_data`로 두며 부분값은 최종 확률로 제공하지 않는다.

완료 결과는 `subset_simulation_event_probability(result)`를 거쳐야 중립 `EventProbability` 계약으로 전달할 수 있다. 이 adapter는 별도의 `event_is_first_failure_in_period_reviewed`가 참이어야 작동하므로 시점 상태확률을 기간 최초고장확률로 자동 승격하지 않는다.

조건부 pCN 체인의 표본은 상관돼 있다. 현재 구현은 iid binomial 오차막대, 신뢰구간, 수렴 인증, 분포 보정, 물리모델 불확도 또는 자격판정을 만들지 않는다. 수락률·임계값 진행·seed·표본 수는 진단이지 정확도 보증이 아니다. `uncertainty_status`는 항상 `not_estimated`다. 다중 callback 병렬 평가, 사용자 표본 함수, importance-weighted 결합도 자동 수행하지 않는다.

사용 예는 `examples/subset_simulation.py`; 합성 회귀는 `tests/test_reliability_sampling.py` 및 HPC batch110에 등록된다. 테스트는 실행하지 않았다. 이 API는 `reliability.rare_event_sampling`의 subset-simulation 경로를 추가하지만 검증·자격화가 요구되는 estimator model 전체를 완료한 것으로 표시하지 않는다.


## 독립 반복의 병렬 작업 API

`build_subset_replicate_tasks(request)`는 sampling 없이 seed별 task를 만든다. `run_subset_replicate_task(limit_state, task)`를 독립 worker에서 호출한 뒤 `reduce_subset_replicate_tasks(parent, results)`에 결과를 모은다. Parent/input/result digest, 정확한 task 집합, evaluator/event/sampling identity 및 공통 NumPy version을 확인하며 입력 순서로 재배열한다. 누락·중복·다른 요청 결과는 거절하고 실패 반복은 통계에서 버리지 않는다. probability/log probability의 일관성도 확인한다.

예제 `examples/subset_replicate_tasks.py`의 prepare는 JSON만 생성하고 run은 한 task, reduce는 집계만 수행한다. 실제 제한상태 함수는 사용자가 자기 worker에 명시적으로 연결해야 한다. 예제 worker는 자기 합성 manifest만 허용한다. 스케줄러 제출, SSH 연결, 누리온 실행은 수행하지 않았다. 독립 반복 분산/표준오차는 estimator bias나 모델 불확도, 신뢰구간 또는 물리적 검증을 대신하지 않는다. 이 API와 예제의 수치 실행은 후속 검증 단계에 남아 있다.

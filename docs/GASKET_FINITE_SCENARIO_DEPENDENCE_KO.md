# 유한 gasket 시나리오의 입력·응답 상관 요약

`GasketFiniteScenarioDependence`와 `gasket_finite_scenario_dependence()`는 이미 제공된 joint scenario와 양의 가중치에서 입력·응답 사이의 기술적 의존성을 계산한다. 기존 finite correlated leakage evaluator와 weight/rights 계약을 재사용한다. 확률분포나 공분산만 보고 새로운 시나리오를 생성하지 않는다. 기존 first-order covariance propagation이나 weighted scalar leakage moments를 대체하지 않는다.

변수 순서는 공통 차압(Pa), 전체 선언 접촉 면적(m²), 전체 몰 누설률(mol/s), 그리고 caller가 선택한 각 node의 접촉압·면적·몰 누설 기여량이다. 선택 node 순서를 유지한다. 전체 면적·누설률은 선택 node의 부분 합이 아니라 원 envelope의 전체 joint 값이다. 시나리오별 calibration realization의 영향은 계산된 누설응답에 보존하지만 calibration grid 자체를 covariance 변수로 펼치지는 않는다.

각 시나리오의 pressure/area/calibration/rate를 동일한 row로 유지한다. 독립 marginal 재추출, sorting을 통한 row 재매칭, 실패 시나리오 제거, 가중치 재정규화를 하지 않는다. 기존 weight 계약은 합 1의 수치 허용범위 1e-12를 적용한다. 이 모듈은 raw caller weights를 그대로 사용한다. 정확히 동일한 상수 열은 그 값을 평균으로 직접 보존하여 단순 가중 곱 반올림으로 인공 분산이 생기지 않도록 한다.

평균은 `mu_i=sum(w_s*x_si)`이며 centered second moment는 `C_ij=sum(w_s*(x_si-mu_i)*(x_sj-mu_j))`다. Unbiased sample covariance의 자유도 보정을 하지 않는다. 각 entry의 단위는 변수 i 단위와 변수 j 단위의 곱이다. Correlation은 centered 열을 각 열의 최대 절대 편차로 나눈 뒤 구한다. 상수 열과 관련한 correlation은 null이며 0으로 대체하지 않는다. 수치 overflow/underflow로 비영 covariance가 표현되지 않거나 correlation이 [-1,1]을 벗어나면 clipping하지 않고 out_of_scope로 반환한다.

선택 node는 최대 16개이고 시나리오 수 × 고유 variable pair 수 예산을 입력에서 제한한다. 동일한 variable vector의 완전한 matrix를 반환한다. Weight 기록, 원 scenario·응답·upstream 결과·새 입력 해시와 physical scope를 남긴다. 원 source/rights review를 유지하되 이용조건 ID가 있다는 사실만으로 공개 관측 데이터 재배포권을 인정하지 않는다. 합성 예제에는 실제 관측값이나 표준 표를 넣지 않았다.

결과는 선언한 유한 시나리오와 가중치의 기술 통계다. 모집단 covariance 추정, stochastic independence, causal sensitivity, 연속 uncertainty set의 상·하한, confidence interval, 외삽, seal acceptance, 잔여수명, 실패확률 또는 재료 qualification을 제공하지 않는다. 상관이 높다고 어떤 입력이 물리적 원인이라는 결론을 내리지 않는다. 유한 시나리오 공분산을 보고 원 분포의 copula나 tail dependence를 복원하지 않는다.

구현 후 테스트·예제 실행·계산·패키징·HPC는 수행하지 않았다. 후속 검증은 hand-computed 2/3-row matrix, 동일 상수 열의 null correlation, 완전 양/음 상관, 독립적으로 구성한 직교 열, node 선택 순서, scenario 순서와 weights의 공동 재배열 불변성, 누락/중복 ID, 실패 upstream의 상태 보존, 큰 단위 scale/미소 covariance, pair budget와 weight provenance를 포함해야 한다.

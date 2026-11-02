# 가스켓 Prony 완화 스펙트럼 적합

`fabrication.gasket_prony_relaxation_spectrum_fit`은 caller가 제공한 등온 일정 압축변형률 유지시험의 응력 완화 자료에 유한 generalized-Maxwell 스펙트럼을 적합한다. 각 branch의 modulus와 relaxation time, 평형 modulus를 bounded nonlinear least-squares로 추정하고, 관측값별 caller 표준불확도로 잔차를 정규화한다.

적합식은 선언한 step strain `epsilon_0`에서 다음으로 둔다.

`sigma(t) = epsilon_0 [E_inf + sum_i E_i exp(-t/tau_i)]`

`E_inf`와 `E_i`는 0과 caller 최대 modulus 사이, `tau_i`는 caller가 제공한 유한 양의 시간 지지구간에 제한된다. Branch 수와 modulus 상한 역시 caller가 결정한다. Branch 순서는 계산 안정성/식별용 label switching에 의해 정해지는 물리 순서가 아니므로 결과 branch를 relaxation time 오름차순으로 정렬해 돌려준다.

## 입력과 적합 조건

- 하나 이상의 시험별 입력을 받는다. 각 시험에는 test ID, physical specimen, source group, 일정 압축 step strain, 정확한 시험온도, strict-order 시간–응력 관측과 관측 표준불확도가 있어야 한다.
- 모든 시험은 요청의 정확히 같은 재료조건과 온도여야 한다. 측정 근거 파일의 SHA-256을 Evidence와 연결한다.
- caller는 step-strain protocol/sign, 자료의 동일 재료조건, 등온 선형 점탄성 적용성, 이용권리를 확인해야 한다.
- 모델은 scipy `least_squares` trust-region reflective solver, 선형 제곱 잔차, caller가 정한 function-evaluation budget을 사용한다. 자동 branch 수 결정, robust-loss 선택, 이상치 삭제, 온도 전이 및 서로 다른 재료 사이 매핑은 하지 않는다.

## 결과 해석과 경계

출력은 평형 modulus, finite Prony branch 계수, weighted residual, Jacobian rank 진단, 파라미터 bound 접촉과 solver 종료 상태를 포함한다. rank가 낮거나 파라미터가 경계에 닿으면 branch spectrum이 식별되지 않을 수 있으므로 계수를 그대로 승인된 재료상수로 사용해서는 안 된다.

이 API는 caller 자료 안의 보정 결과만 제공한다. 같은 적합자료의 잔차는 독립 실험 검증이 아니다. runout/파손 기준, 기하학적 구속, 온도 의존성, 시간–온도 이동, 비선형 strain dependence, Mullins effect, 재료 전이, local gasket stress, joint contact equilibrium, leakage, seal acceptance 또는 자격 수명은 산출하지 않는다. branch 개수와 시간 지지구간을 바꾸면 서로 다른 적합 문제가 되므로 요청 digest를 고정해야 한다.

계산식과 설명은 공개 가능한 형태로 새로 작성했다. 현재 구현에 대한 수치 회귀시험 및 독립 시험자료 검증은 남아 있다.

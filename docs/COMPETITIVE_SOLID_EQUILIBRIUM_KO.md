# 경쟁 중성 고체상 평형 API

`chemistry.competitive_solid_equilibrium`은 caller가 닫힌 종목록과 둘 이상의 경쟁 고체상, 반응식, 초기 농도/고체량, 표준상태, 고정 활동도 계수와 각 용해도곱을 제공했을 때 고정 부피 단일 액상 평형 후보를 계산한다. 입력 contract는 `CompetitiveSolidEquilibrium`이며 `ModelRegistry.run()`에서 실행한다.

## 풀이 개념

고체상 j의 침전 extent를 `xi_j`라 두면 최종 수용액 농도는 `c_i = c_i0 - sum_j(nu_ij xi_j)`이고 최종 고체량은 `s_j = s_j0 + xi_j`이다. 허용 조건은 모든 최종 농도와 고체량이 음수가 아니어야 한다는 것이다. 각 선언 반응은 전하 및 원소 수지를 만족해야 한다.

계산기는 고정 활동도 `a_i = gamma_i c_i / c_i_ref`에 대해 aqueous mixing term과 caller `Ksp`의 solid term을 결합한 dimensionless Gibbs potential을 최소화한다. 고체가 존재하면 `log(Q_j/Ksp_j)=0`; 고체가 사라진 후보상은 `Q_j/Ksp_j <= 1`이어야 한다. 최종 상태에서 포화 조건, 상 complementarity와 농도 extent balances가 각각 허용오차 안인지 확인한다. 최적화 성공만으로 평형을 인정하지 않는다.

## 필요한 입력과 검토

- 공통 액상에서 공유되는 각 종 ID, 초기 `mol/m3` 농도, dimensionless activity coefficient, 참조 농도, 전하 및 원소 조성
- 각 고체상 ID, 침전 반응에서 소비되는 종별 양론계수, 중성 고체 원소 조성, 초기 고체량, 무차원 `Ksp` 및 출처 SHA-256
- 하나의 온도와 표준상태
- 후보 고체상 집합의 완전성, 고정 활동도/표준상태, Ksp 온도·계산 사용, 단일 액상·고정 부피·중성 순수고체 가정에 대한 명시 검토

## 범위 경계

이 API는 계산기술 모듈이며 자동 산/염기 speciation, 전하/원소 총량에서의 종 생성, 활동도 반복, 수화물·고용체·기체상·다른 액상, 핵생성 장벽, 침전 속도, 공간 수송, 표면 보호율 또는 부식률을 만들지 않는다. 호출자가 고체상 후보목록을 빠뜨리거나 Ksp 적용 조건을 잘못 선언한 경우 이를 보완할 수 없다. 공급자 상수의 정확도와 화학적 적용성은 별도 검증 대상이다. SLSQP 최적화기 종료는 독립 화학 검증을 의미하지 않으며, 포화·보존 잔차 조건을 만족하지 못하면 결과는 `out_of_scope`로 닫힌다.

합성 입력 구조는 `examples/competitive_solid_equilibrium.py`에 있다. 해당 값은 문헌 상수나 권장값이 아니다.

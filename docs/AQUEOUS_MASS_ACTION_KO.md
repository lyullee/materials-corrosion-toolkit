# 사용자 정의 수용액 질량작용 평형

`chemistry.aqueous_mass_action_speciation`은 사용자가 정의한 하나의 수용액 액상 종 목록, 평형반응, 고정 활동도계수 및 선형 농도 제약을 풀어 각 종의 활동도와 농도를 계산한다. 탄산계 전용 코드를 수정하지 않고 반응종·상수·분석 총량·전하 제약을 바꿔 재사용할 수 있는 독립 확장 API다.

## 방정식 계약

각 종의 무차원 활동도 `a_i`를 미지수로 사용한다. 선언한 평형반응마다 `sum(nu_i * ln(a_i)) = ln(K)`을 구성하며, 입력의 `log10_equilibrium_constant`는 natural-log 잔차로 변환한다. K는 선택한 표준상태와 반응식 기준에 맞는 dimensionless equilibrium constant여야 한다. 명시 종 목록 밖의 용매 활동도는 계산하지 않으므로, 용매를 암묵적으로 일정하다고 둘 때 그 전제는 K에 이미 반영되어 있어야 한다. 활동도와 농도는 `a_i = gamma_i * c_i / (1 mol/L)` 관계를 사용하므로 이 계약은 `molarity_1_mol_L` 표준상태만 허용한다. 활동도계수 `gamma_i`는 양수인 caller 상수이며 풀이 중 갱신하지 않는다.

반응식 계수는 반응물에 음수, 생성물에 양수를 쓰는 signed stoichiometric convention이다. 각 평형반응의 전하수지는 계약 생성 시 항상 확인한다. 종마다 원소 조성을 입력하면 전체 종에 조성이 있어야 하며, 모든 반응의 원소수지도 함께 확인한다. 원소 조성을 제공하는 요청은 별도 `elemental_formula_and_reaction_balance_reviewed` 검토 플래그를 요구한다. 용매를 종 목록에서 뺀 축약 반응식은 축약 계수로 원자수가 보존되지 않을 수 있으므로 이 경우 원소 조성을 생략하고, 축약 평형상수와 용매 표준상태의 책임을 caller가 검토해야 한다.

각 선형 제약은 `sum(b_ki * c_i) = target_k` 꼴이다. 분석 성분 총량에는 계수 1을 사용하고, 전기중성도에는 종 전하수를 계수로 넣어 `target=0`인 별도 제약을 선언할 수 있다. 모델은 제약의 물리적 의미를 추정하지 않으며, 질량수지와 전하수지를 자동 추가하지 않는다. 미지수 수와 제약 방정식 수가 정확히 같아야 한다. 과잉/부족 제약은 거절한다.

입력에는 각 종 활동도의 초기 추정값이 필요하다. damped Newton 방식으로 로그 활동도 공간에서 제약 잔차를 caller 규모로 정규화해 풀이한다. 계산 전에 row-normalized equation basis의 rank를 검사하고, 각 iteration에서 Jacobian rank·condition number를 caller가 정한 상한과 비교한다. Rank 부족, condition limit, singular factorization, 비유한 step, line-search 실패와 iteration 소진은 서로 다른 종료 사유로 `out_of_scope`에 남긴다. 종 농도를 clip하거나 기본값·다른 열역학 모델로 대체하지 않는다. 결과에는 반응 잔차, 제약별 농도 closure, iteration/accepted damping 기록, rank/condition 진단, provider revision/configuration/record digest와 전체 입력 digest를 기록한다.

수렴한 상태에서는 같은 잔차 Jacobian을 이용한 암시적 미분을 계산한다. 결과의 `local_sensitivities.parameter_order`는 반응별 `log10(K)`, 제약별 target 농도, 종별 `ln(gamma)` 순서다. 종마다 로그 활동도·로그 농도 및 농도의 각 입력에 대한 국소 편미분을 반환한다. 고정 gamma 모델에서 농도 민감도는 활동도계수의 직접 변화와 평형 재조정을 함께 반영한다. 이는 계산점 주변의 1차 국소 기울기다.

선택적으로 `local_parameter_covariance`에 위 parameter 순서와 일치하는 공분산행렬을 넣고 `local_parameter_covariance_reviewed=True`를 설정하면 `J Σ Jᵀ`를 통해 로그 활동도, 로그 농도 및 농도의 1차 공분산과 농도 표준편차를 계산한다. 입력 공분산은 유한·대칭·양의 준정부호여야 하며 매개변수가 혼합 단위이므로 각 원소 단위를 위 parameter 정의에서 유도해 caller가 확인해야 한다. 이는 계산점 주변의 선형화 결과이며 입력분포 전파, 비선형/전역 불확실성, 꼬리확률 또는 민감도 순위가 아니다. Jacobian이 caller 조건수 상한을 넘거나 특이하면 평형 계산 결과는 보존하고 민감도 및 그 공분산만 사용할 수 없다고 표시한다. [`examples/aqueous_mass_action_local_sensitivities.py`](../examples/aqueous_mass_action_local_sensitivities.py)는 합성 대각 공분산을 설정하는 배선 예시다.

## 사용자 검토와 한계

종 목록의 완전성, 반응식의 방향·계수·상수, 제공한 원소식의 적용 범위, 제약식 및 전하 범위, 활동도 표준상태와 계수, 온도·provider 계보, 초기 추정값·수렴 허용치, 액상 단일상 가정을 모두 검토해야 한다. 예제는 synthetic이며 이 검토 플래그가 참이라고 해서 실제 재료계가 검증된 것은 아니다.

이 API는 액상 하나의 평형 수치 solver다. 이온세기 변화에 따른 gamma iteration, Davies/Pitzer 선택, 물 자동수지, 기체 퓨가시티와 액상 연계, 고체 침전·복수상 평형, 전극 kinetics, 부식률·보호막·moving boundary 또는 acceptance를 계산하지 않는다. 기존 `chemistry.carbonate_alkalinity_speciation`은 별도 carbonate-only 계약으로 남는다.

`examples/model_inputs.json`의 `chemistry.aqueous_mass_action_speciation`은 용매 활동도를 1로 취급해 `Kw`에 접어 넣은 두 단계 해리산과 물 이온화의 합성 예다. `examples/aqueous_elemental_balance.py`는 용매를 제외해 원소 보존이 성립하도록 명시한 1단계 해리계에 전하·원소 검사를 연결하는 합성 예다. 실제 계산에는 적법하게 사용할 수 있는 종·상수·활동도 자료를 입력한다.

## 균형 반응식 후보 열거

`chemistry.aqueous_reaction_candidate_enumeration`은 닫힌 후보 종 목록, 종별 완전한 원소식과 전하를 받아 사용자가 지정한 총 화학양론 차수까지 원자수·전하가 맞는 원시 정수 반응식을 열거한다. 최대 종 수·차수·측면 조합 수·동일 보존 벡터 쌍 검사 수·후보 수를 입력 계약에서 제한하며, 예산을 넘으면 부분 후보 목록을 성공 결과로 반환하지 않는다. 결과에는 입력 digest와 수식/전하 검토 게이트가 포함된다.

이 기능은 계산망 작성을 보조하는 **stoichiometric screen**이다. 균형이 맞는다는 사실만으로 반응의 화학적 가능성, 액상/기상/고상 여부, 반응방향, 평형상수, 속도상수 또는 망의 완전성이 결정되지 않는다. 선택·검토된 반응만 별도 근거를 붙여 평형 또는 속도 계산 API에 전달해야 한다. 이 기능은 기존 매스액션 계산을 자동으로 채우거나 부식률을 추정하지 않는다. 합성 배선 예는 `examples/aqueous_reaction_candidates.py`에 있다.

고농도 단일 전해질의 mean ionic activity와 solvent activity가 필요하면 별도 계산기 [`chemistry.pitzer_single_salt_activity`](PITZER_SINGLE_SALT_KO.md)를 사용한다. 이 API는 하나의 pure salt에 한정되며 기존 여러 이온/혼합 반응망에 single-ion gamma를 임의 배정하지 않는다.

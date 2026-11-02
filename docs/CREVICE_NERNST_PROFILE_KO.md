# Caller activity 기반 crevice redox potential profile

`degradation.crevice_nernst_potential_history`는 입력된 각 시각에서 한 개의 caller 지정 환원 반응에 대한 반쪽전지 평형전위를 계산한다. 시간별 dimensionless activity, 표준전위 및 온도는 caller가 제공한다. `standard_potential_reference_id`는 표준전위의 전극 기준을 지정하며 후속 electrode kinetics 연결 시 같은 기준 ID가 요구된다. 계산식은

\[
E(t)=E^0(t)-\frac{RT(t)}{nF}\ln Q(t),\qquad
\ln Q(t)=\sum_i \nu_i\ln a_i(t)
\]

이다. `reaction_quotient_stoichiometry`에서 생성물 계수는 양수, 반응물 계수는 음수이며 전자는 reaction quotient에 넣지 않는다. 반응 방향과 전자 수를 caller가 확정해야 한다.

## inventory API와 연결

`build_crevice_nernst_request_from_inventory()`는 `degradation.crevice_species_inventory_history`의 `computed` 결과를 입력받아 inventory concentration history 및 온도 knot를 Nernst 요청으로 연결한다. 용액 activity는 caller가 제공한 `gamma_i`와 기준농도 `c°_i`로 `a_i=gamma_i c_i/c°_i`를 계산한다. 동일한 시간축에서 모든 반응 종의 concentration, gamma, 양의 activity, standard concentration 및 standard-potential 값이 필요하다. activity provider와 standard-potential provider는 별도 configuration/record digests와 revision으로 기록되고 각각 선언 Evidence에 연결되어야 하며, 원 inventory result digest도 결과 계보에 보존된다.

inventory result만으로 gamma, 표준상태, 종 변환, 반응 표준전위 또는 해당 local environment에서의 적용성을 알 수 없다. 이 항목은 전부 caller의 책임이다. 0 농도/활동도는 로그가 정의되지 않으므로 자동 epsilon 대체 없이 요청 생성 단계에서 거절한다.

## 경계와 사용

이 결과는 한 반쪽전지의 Nernst 전위 profile이다. 혼합전위, 부식전류, 반응 속도, 국부 pH, 포화·침전, 균열 민감도, 수명, 위험 확률 또는 acceptance를 계산하지 않는다. 여러 반응을 혼합하거나 상호작용시키지 않는다. 위험성 평가/FTA에는 별도 모델에서 caller가 정의한 event mapping을 사용한다.

`examples/crevice_nernst_profile.py`는 Fe³⁺/Fe²⁺ 반응에 대한 synthetic 배선만 보여준다. 숫자는 교육용 입력이며 실험 자료, 재료 권고치, 검증 데이터 또는 공개 서비스 한계가 아니다. 계산 테스트와 실험적 자격화는 별도 과제다.

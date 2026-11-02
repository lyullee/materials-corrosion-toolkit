# 공간 비선형 점탄성 gasket 접촉 이력

`fabrication.flange_nonlinear_viscoelastic_contact_history`는 caller가 제공한 평형 응력–변형률 backbone과 generalized-Maxwell branch별 단조 비선형 backbone을 node별 gasket 면적·두께 및 구조 provider의 상대 flange compliance에 결합한다. 입력에는 시간별 gasket 반력 제외 자유 닫힘량, material/condition/source digest, 구조 provider configuration/result digest와 계산·재료 검토 gate가 포함된다.

첫 시간점은 검토된 영변형률 branch 기준에서 순간적으로 하중이 가해지는 경우로 정의한다. 이후 각 시간 구간은 endpoint compressive strain 사이 선형 경로로 해석하며, 각 Maxwell branch는 그 경로가 통과하는 backbone knot에서 분할한 뒤 지수형 내부 응력 update를 적용한다. 매 시간 knot에서 비음수 접촉력과 비음수 간극의 상보 조건을 만족시키도록 caller flange operator와 비선형 gasket 반력을 결합해 active-set Newton solve를 수행한다. 접촉 node 국부 응답의 접선은 수치 미분으로 평가하고, 허용 변형률 범위 안의 양의 접선과 잔차 감소를 line search로 확인한다.

## 입력 경계와 실패 조건

합성 fixture는 `examples/model_inputs.json`의 `fabrication.flange_nonlinear_viscoelastic_contact_history` 항목이다. 재료에는 `NonlinearGasketViscoelasticMaterial`의 평형 backbone, branch별 시간상수/응력 backbone, initial branch state와 source/condition digest를 넣는다. 별도 `initial_branch_stress_by_node_Pa`를 제공하면 이를 node별 초기 상태로 사용하며, 생략하면 material 입력의 초기 branch 응력을 모든 node에 복제한다.

Flange compliance는 caller가 공급하는 유한 대칭 양의 준정부호 행렬이어야 한다. bolt·압력·경계하중 조성과 시간 이력도 caller가 명시한다. 비양의 국부 접선, strain 범위 초과, 유한 support 내 양의 gasket traction 부재, Newton/active-set 미수렴 또는 계산 예산 초과 때 해당 시간점은 `out_of_scope`로 끝나고 실패 이후 결과를 계산 완료로 승격하지 않는다.

모델은 지정 knot 사이의 개방·재접촉 시각을 풀지 않으며 구조해석이나 flange FE 응답을 생성하지 않는다. Node 평균압력은 contact force/area로만 정의하며 local peak stress, leakage, seal performance, 절차 적합성 또는 규격 합격 판정이 아니다. Nonlinear branch fitting, condition transfer와 실제 시편 자격화도 caller/provider 책임이다. 이 공개 계산 경로의 합성 예제는 물리 검증 자료가 아니다.

## caller 검토 시간 샘플링과 전이 구간

`maximum_contact_transition_step_s`를 주면 각 원래 시간 구간을 그 최대 간격 이하의 균일한 하위 구간으로 나누어 접촉 계산을 반복한다. 각 node의 gasket 제외 자유 닫힘량은 원래 입력 knot 사이에서 선형 보간한다. 이 보간이 실제 하중 이력을 표현하는지 caller가 먼저 판단해야 하며, 입력의 `contact_transition_time_sampling_reviewed`를 `true`로 설정해야만 사용할 수 있다. 생성 knot와 보간 closure는 계산 전에 원래 계약으로 다시 검증된다. 전체 knot 수는 10,000개로 제한된다.

인접 계산점에서 한 node의 `contact_state`가 달라지면 `sampled_contact_transition_brackets`에 하한·상한 시각과 폭을 기록한다. 기본 동작은 이 bracket을 샘플 최대 간격까지만 제한한다. 더 좁은 폭이 필요하면 `contact_transition_time_tolerance_s`를 지정하고 `single_contact_transition_per_refined_interval_reviewed=true`를 함께 제출한다. 이때 계산기는 중간 시각을 삽입해 앞선 입력 이력부터 접촉/branch-state 계산을 재생하고, 대상 node의 상태가 하한 상태와 같은지에 따라 이분 탐색한다. 각 관찰 전이 bracket을 선언 tolerance 이하로 좁히며 결과에 `transition_refinement_complete`, refinement 방법, solve 수, replay work unit, 시도한 `transition_refinement_midpoint_times_s` 및 대응 재생 입력 digest를 남긴다. solve·work·10,000-knot budget을 넘거나 midpoint가 부동소수점으로 표현되지 않거나 중간 재생이 실패하면 결과는 `out_of_scope`이며 미세 bracket을 계산 완료로 보고하지 않는다.

각 bracket은 하한·상한의 접촉력, 평균압력, gasket 압축량·변형률·구성 응력 및 간극을 `sampled_bracket_endpoint_results`에 보존한다. 모든 이분 재생 midpoint의 동일 응답량과 실제 적용한 `flange_compliance_operator_sha256`, 해당 시도의 `replay_request_sha256`는 `refinement_observations`에 기록한다. 시간변화 행렬은 caller가 검토한 성분별 선형 보간으로 재생되며, 이 lineage로 각 bracket 관찰을 시간별 구조 compliance 입력과 대조할 수 있다. 응답량은 접촉 상태의 추적 자료이며, 별도의 root residual 정의가 없는 한 이벤트 근의 평가값으로 해석하지 않는다.

이 방법은 caller가 각 refined interval에 node당 전이가 하나 이하라고 검토한 경우에만 유효하다. 최대 sampled step은 초기 전이 탐지 해상도이며, 그보다 짧은 비관찰 개폐 사건은 찾아내지 않는다. 반환값은 tolerance 폭의 구간이지 수학적으로 exact root가 아니다. 재료 이력은 보간된 입력 시간점에서 순차 적분되므로 보간과 해상도는 모델 가정이며, 전이시각 자격화나 누설 판단으로 사용하지 않는다.

`examples/flange_contact_transition_sampling.py`는 synthetic 입력에 caller 검토 표시와 최대 간격을 추가하는 API wiring 예제다. 실제 계산·시험 결과로 간주하지 않는다.

## 시간변화 flange compliance 입력

기본 입력은 기존 단일 `flange_relative_compliance_matrix_m_N`를 모든 계산 시각에 사용한다. 시간에 따라 구조 응답이 변하는 경우 `flange_relative_compliance_history_m_N`에 각 `times_s` knot별 정방·대칭 행렬을 제공할 수 있다. `compliance_history_interpolation_reviewed=true`를 명시해야 하며, 하위 시간점(전이 샘플링/이분 재생 포함)에는 행렬 성분별 선형 보간을 쓴다. 각 실제 평가 행렬은 양의 준정부호 조건을 만족해야 하고, 벗어나면 해당 시점에서 `out_of_scope`로 중지한다. 이는 caller가 준비한 구조 compliance 이력의 결합이지 flange FE 응답 생성이나 비선형 구조재료 해석이 아니다.

시간별 응답 행에는 해당 knot에서 실제 사용된 compliance 행렬의 SHA-256과 최소 고유값을 기록한다. 집계 최소 고유값은 전체 평가 이력 중 최솟값이다. 따라서 보간/재생 경로에서도 시점별 적용 구조 compliance를 계산 결과와 대조할 수 있다.

Compliance 입력 허용오차 내 작은 비대칭은 계산에 그대로 쓰지 않는다. 검증을 통과한 단일 행렬 또는 시간별 행렬을 `(C + Cᵀ)/2`로 대칭화한 뒤 접촉 연산자에 적용한다. 시간 이력 각 응답에는 대칭화된 실제 적용 행렬 digest와 해당 행렬의 최소 고유값이 기록된다.

`examples/flange_time_varying_compliance.py`는 기존 synthetic fixture의 고정 compliance matrix를 선언된 시간 knot마다 양의 scalar로 배율화해 입력하는 배선 예제다. 계수는 예제 데이터이며 재료/설비 보정값이 아니다. 파일은 API 호출 방법을 보여줄 뿐 실행·수치 검증을 주장하지 않는다.

비균일 접촉 탐색에는 additional_contact_sampling_times_s를 사용한다. 이 시각들은 원 times_s의 양 끝 안쪽에서 엄격히 증가해야 하며, maximum_contact_transition_step_s와 contact_transition_time_sampling_reviewed가 필요하다. 최대 간격으로 만든 격자와 추가 시각의 합집합을 정렬하고 정확히 같은 시각만 중복 제거한다. 최종 격자는 10,000개 이하이며 원 closure 및 선택적 compliance history를 기존 선형 방식으로 재구성한다. 추가 시각은 하중 관측값을 추가한 것이 아니라 같은 선언 경로의 계산 위치다.

결과의 additional_contact_sampling_times_s는 요청된 추가 시각이고 planned_evaluation_time_knots_s/sha256는 전체 계획 격자와 해시다. evaluation_time_knots_s와 computed prefix는 실제 완료 범위를 나타낸다. 실패 시 계획 격자를 완료 이력으로 해석하지 않는다. 추가 시각을 이용해 관심 구간을 더 촘촘히 탐색할 수 있지만 미관측 다중 전이나 정확한 전이 시각을 보증하지 않는다. Bisection은 기존 단일 전이 가정과 예산을 유지한다.

원 시각 보존: 각 source 구간의 마지막 시각은 보간 산술로 재생성하지 않고 원 end 값을 직접 사용한다. source_time_knots_preserved_exactly는 모든 원 knot가 계획 격자에 정확히 포함되는지 기록한다. 이는 시간축 구성의 무결성 설명이며 전이 검출이나 구성법칙의 정확성 증거가 아니다.

시간 격자 보간은 component별 전체 시각 벡터를 np.interp에 전달한다. Scalar time별 Python 호출을 줄이며 원 node/matrix 축 순서를 보존한다. 보간 결과 배열을 임시 저장하므로 계산 준비 메모리가 추가로 필요하다. 성능 측정과 수치 동등성 테스트는 별도 검증 과제다.

전이 refinement replay는 base 경로의 기존 closure/compliance 행을 그대로 유지하고 새 midpoint의 행만 보간·삽입한다. 전체 구성법칙/접촉 이력은 다시 계산하므로 상태 이력을 건너뛰지 않는다. 보간 준비의 중복 연산만 줄이며 exact event나 물리적 qualification을 추가하지 않는다.

# 공간 점탄성 gasket 접촉 이력

`fabrication.flange_viscoelastic_contact_history`는 각 접촉 node의 caller 제공 선형 generalized-Maxwell 재료와 구조 provider의 상대 flange compliance를 결합해 선언 시간 knot별 압축 전용 접촉력을 계산한다. 입력에는 node별 면적·두께·평형 탄성률·Prony branch, 초기 branch 응력, gasket 반력을 제외한 자유 닫힘량 이력, compliance 행렬, 구조 결과 lineage와 검토 gate가 포함된다.

각 구간에서 압축 변형률은 knot 사이 선형이라고 해석한다. branch `i`의 시간상수 `tau_i`, 탄성률 `E_i`, 구간 `dt`에 대해 `a_i = exp(-dt/tau_i)`, `r_i = tau_i(1-a_i)/dt`를 사용해 내부 응력을 `s_i,new = a_i s_i,old + E_i r_i (epsilon_new-epsilon_old)`로 갱신한다. 이 관계를 현재 변형률의 affine 항으로 써서 compliance와 함께 접촉 active-set 선형계를 푼다. 비접촉 node는 접촉력이 0이고 간극이 음수가 아니어야 한다.

첫 knot는 검토된 영압축 기준 상태에서 순간적으로 하중을 가하는 것으로 정의한다. 따라서 첫 knot에서 Maxwell branch는 순간 탄성 응답을 보이고 해당 branch 응력은 초기 변형률에 맞춰 설정된다. 이후 branch 업데이트는 구간의 선형 strain 경로에 대한 닫힌형 지수 갱신이다. 결과는 각 knot의 힘·평균압력·압축량·변형률·응력·간극 및 branch 상태와 구조 provider configuration/result digest를 보존한다. 계산 실패 시 성공한 시간 prefix와 실패 시각을 제공하고 전체 이력 완료로 표시하지 않는다.

## 입력 및 사용 경계

합성 예제는 `examples/model_inputs.json`의 `fabrication.flange_viscoelastic_contact_history` 항목이다. 실제 적용 시 Prony 보정의 재료 상태·온도·압축 범위·시간 범위와 초기 branch 상태를 caller가 확인해야 한다. compliance는 유한 대칭 양의 준정부호여야 하며 자유 닫힘량에는 bolt, 압력, 경계하중의 조성이 반영되어야 한다. Calculator API는 `matintegrity.models.flange_contact_field.FlangeViscoelasticContactHistoryRequest` 입력 계약과 등록 evaluator를 통해 직접 사용할 수 있다.

이 계산은 caller가 준 compliance operator를 사용하며 flange 해석을 생성하지 않는다. 접촉은 knot에서 준정적으로만 푼다. knot 사이 개방/재접촉 시각, 비선형 gasket 가지, 비선형 회복·손상, 국부 FE 응력, 누설, sealing 기준과 code acceptance는 계산하지 않는다. 평균압력은 node 접촉력/면적이다. 별도 교차검증과 물리 자격화가 완료될 때까지 이는 caller 모델 기반 계산이며 설계 판정이 아니다.

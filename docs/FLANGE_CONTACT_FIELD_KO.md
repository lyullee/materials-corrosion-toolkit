# 외부 compliance 기반 flange/gasket 접촉장

`fabrication.flange_contact_field`는 다른 구조해석기에서 계산해 전달한 상대 flange compliance operator를 사용해 circumferential gasket node별 접촉력·평균압력·압축량·간극을 계산한다. compliance operator, 볼트/내압/외력 합성 및 무 gasket free-closure 벡터는 입력 시스템 책임이며 이 API가 FE를 대신하지 않는다.

## 계산식과 해법

노드별 gasket force vector `q`는 비음수이고, 무 gasket 상태에서 닫힘 방향 free displacement를 `u0`, flange response matrix를 `C`, node gasket tangent stiffness를 `k`라 한다. 선형 gasket compliance를 `diag(1/k)`로 두고

`M = C + diag(1/k)`, `g = M q - u0`

의 선형 complementarity system `q >= 0`, `g >= 0`, `q_i g_i = 0`를 푼다. Deterministic active-set solver는 현재 접촉 node만 선형계로 풀고 음의 force node를 제거하거나 음의 gap node를 추가한다. 접촉 행렬의 유한성·대칭성·positive semidefinite support를 확인하며, active-set caller가 정한 iteration/work budget 내에 수렴하지 않으면 결과장을 반환하지 않는다.

평균 접촉압력은 각 node force를 caller 공급 접촉면적으로 나눈 값이다. 이는 면적 평균으로 local stress peak와 다르다. 결과에 source/configuration/result digest를 보존하므로 FE 응답 결과와 calculator 입력을 추적할 수 있다.

## 적용 범위 및 검토

caller는 node 순서와 좌표계, compliance의 부호/단위 및 상대 변위 정의, FE 경계조건·bolt load·내압·외력 포함 여부, gasket 접촉 면적과 접선 stiffness 범위를 검토해야 한다. compliance 행렬은 상대 closure에 대한 gasket nodal force의 영향 연산자로 정의되어야 하며, 다른 부호 convention의 구조 결과는 호출자가 명시 변환 후 제출해야 한다. 이 모델은 linearized local gasket springs와 caller compliance의 결합이다.

본 API는 flange mesh나 stiffness를 생성하지 않고, gasket 비선형/점탄성 법칙을 추정하지 않으며, flange element stress, 실제 국부 접촉응력, 누설률, seal 성능, code acceptance 또는 qualification을 계산하지 않는다. 예제는 synthetic fixture다. 수치 검증은 미실행이며 compliance를 제공하는 외부 solver와의 실제 검증이 필요하다.

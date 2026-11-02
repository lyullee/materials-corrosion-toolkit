# 외부 구조 강성에서 가스켓 접촉 유연도 추출

선형 Prony 공간 접촉 이력에는 기존 FlangeViscoelasticContactHistoryRequest의 정적 첫 행렬을 flange_relative_compliance_matrix_m_N에 두고, 전체 축약 결과와 canonical SHA-256을 flange_compliance_history_result 및 flange_compliance_history_sha256에 함께 제공한다. 요청 times_s와 node_ids는 축약 이력의 시각 및 접촉 node 순서와 정확히 일치해야 한다. 계산기는 각 시간 knot에서 대응하는 compliance operator를 사용한다.

`fabrication.flange_contact_compliance_reduction`은 구조 solver가 제공한 선형 증분 강성행렬을 받아 고정 지지 DOF를 반영하고, 선택한 접촉점 법선 병진 DOF의 상대 유연도 행렬을 계산한다. 출력의 `flange_relative_compliance_matrix_m_N`은 기존 공간 가스켓 접촉 요청의 동명 입력에 전달할 수 있다.

운전점/시간별 tangent 강성행렬이 있으면 `fabrication.flange_contact_compliance_reduction_history`를 사용한다. 이 API는 한 시간 배열, 같은 길이의 행렬·출처 SHA-256 배열, 고정된 contact node/DOF/sign 매핑을 요구한다. 각 절점 행렬을 독립 축약하며, 모든 결과와 solver lineage를 시간순으로 반환한다. 각 응답 행을 같은 시각의 가스켓 접촉 요청에 연결할 수 있다.

각 시간 절점의 강성행렬을 외부 FE 결과 receipt와 함께 전달할 때는 `integration.external_flange_compliance_history`를 쓴다. 입력 `bindings`에는 단일 receipt API의 binding을 절점마다 하나씩 둔다. `times_s` 길이와 정확히 맞춰야 하며, provider/model ID·revision, 자산·위치·물리 범위, 전역 translational DOF 순서, 지지 DOF, 접촉 node/normal/sign은 모든 receipt에서 고정한다. mesh revision 및 load case는 절점별로 바뀔 수 있지만 각 receipt 안의 field/mesh/boundary digest 연결은 단일 receipt 계약에 따라 검증된다.

구조 receipt 계약 자체에 canonical 물리 시각이 없으므로 caller는 시간 배열과 receipt의 대응을 외부 해석 기록에 근거해 검토하고 `receipt_times_reviewed=True`로 표시해야 한다. 이 review가 없으면 행렬 축약을 수행하지 않고 `needs_data`를 돌려준다. 계산 결과에는 시간별 compliance와 receipt/result field/mesh/DOF 변환 lineage가 함께 남는다. 시각 라벨은 입력자의 선언이며, solver 시간 이력을 자동 복원하거나 receipt 사이 응답을 보간하지 않는다.

## 수학적 정의

전체 구조 행렬 `K`에서 고정 증분 DOF를 제거해 자유 DOF 행렬 `K_ff`를 만든다. `S`는 contact normal DOF를 선택하는 행렬이며 `D`는 각 접촉점의 caller 부호 convention을 대각성분으로 담는다. 다음 선형 계를 풀어 상대 컴플라이언스를 만든다.

```text
K_ff X = S^T D
C_contact = D S X
```

이 방식은 `K_ff` 역행렬 전체를 구성하지 않고 선택한 접촉 방향에 대한 열만 푼다. 입력 강성이 평형 기준 주위의 증분 선형 모델이어야 하며, fixed DOF 값은 0 증분으로 해석한다. 외부 구조 해석에서 계산한 열팽창/압력/볼트 등의 baseline 자유 폐합은 별도 `free_closure_without_gasket_m` 입력에 연결한다.

## 입력 규약과 검토

- 입력 행렬은 같은 단위의 병진 자유도만 남긴 `N/m` 강성행렬이어야 한다. 회전 또는 이종 단위 DOF는 공급 구조 solver에서 먼저 응축한다.
- fixed DOF와 각 가스켓 접촉 node의 법선 DOF 인덱스를 명시한다. DOF 순서, 지지 경계, 실제 접촉점 매핑, 법선 폐합 부호와 물리적 범위를 caller가 검토한다.
- upstream solver ID/revision과 stiffness source SHA-256을 보존한다. 이 도구는 solver 출력 파일 해시를 스스로 확인하지 않으며 전달된 행렬 전체를 input digest에 포함한다.
- 지지 DOF 제거 후 행렬이 대칭 양정치이며 허용 condition number 안에 있어야 한다. 계산된 접촉 연산자는 대칭 양의 준정부호 조건을 만족해야 결과를 `computed`로 준다.

## 한계

Prony 접촉 history에서 compliance가 시간 절점 사이 어떻게 변하는지는 계산하지 않는다. Branch strain 경로는 caller가 선언한 인접 closure knot 사이의 piecewise-linear 이력이고, 접촉 전이의 정확한 시각은 별도 계산하지 않는다.

이 API는 메쉬 생성, 요소 강성 조립, 재료모델·볼트/압력/온도 하중 생성, 초기 변위 계산, 절점 사이 tangent 보간, 비선형 접촉, gasket 특성 추정, 국부 응력, 누설·sealing 성능 또는 설계 승인 판단을 수행하지 않는다. 외부 선형 solver에서 나온 운영점 증분 강성 연산자를 계약에 맞게 축약한다. 고유값과 조건수 검사는 행렬 수치 구조 확인이며 외부 해석 자체의 검증, mesh 수렴, 실험 검증이나 물리 자격화를 의미하지 않는다.

합성 입력은 [`examples/flange_compliance_reduction.py`](../examples/flange_compliance_reduction.py)에 있다. 이 예시는 사용법만 보여주며 실제 플랜지 물성이나 구조 강성을 나타내지 않는다.

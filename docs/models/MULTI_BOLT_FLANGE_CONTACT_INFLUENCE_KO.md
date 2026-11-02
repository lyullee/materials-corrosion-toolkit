# 다중 볼트 하중을 절점별 가스켓 접촉 입력으로 연결

## 역할

`integration.multi_bolt_joint_to_flange_contact_request`는 계산된 `fabrication.gasket_multi_bolt_sector_equilibrium` 결과의 한 하중 knot에서 볼트별 장력을 꺼내, caller 제공 볼트-절점 폐합 영향행렬로 절점별 자유 폐합량을 만들고 기존 `fabrication.flange_contact_field`에 넣을 typed request를 반환한다.

이 모듈은 flange finite-element 해석이나 unilateral 접촉 해석을 자체 구현하지 않는다. 새로운 가스켓 법칙을 적합하지 않으며 기존 접촉 solver를 다시 구현하지 않는다. 결과로 받은 `contact_request`를 `FlangeContactFieldRequest`로 복원해 기존 contact-field API에 전달한다.

## 관계와 순서

선택한 시각 knot에서 볼트 `j`의 장력을 `Fⱼ`, 접촉 절점 `i`의 비볼트 자유 폐합을 `uᵢ⁰`, caller 제공 변위 영향행렬을 `Hᵢⱼ`라 두면

`uᵢ = uᵢ⁰ + Σⱼ Hᵢⱼ Fⱼ`

이다. 행은 `contact_template.node_ids`, 열은 명시된 `bolt_ids` 순서와 맞아야 한다. Adapter는 이 `uᵢ`를 `free_closure_without_gasket_m`으로 갖는 `FlangeContactFieldRequest`를 만든다. downstream solver는 caller의 flange compliance matrix와 local gasket stiffness로 unilateral 접촉 평형을 푼다.

권장 호출 흐름은 다음과 같다.

1. 다중 볼트·sector 조립체 solver에서 digest-bound `AssessmentResult`를 얻는다.
2. 영향행렬 제공자·revision·configuration·절점/볼트 순서·matrix bytes의 digest와 Evidence/license를 제공한다.
3. `integration.multi_bolt_joint_to_flange_contact_request`로 typed 접촉 요청을 만든다.
4. 반환된 `contact_request`를 `fabrication.flange_contact_field`로 전달해 접촉력을 구한다.

`contact_template.free_closure_without_gasket_m`에는 영향행렬에 포함한 볼트의 변위 기여를 넣지 않아야 한다. 이 adapter가 그 볼트 기여를 한 번만 합산한다.

## 검토와 fail-closed 조건

- 상류 결과는 모델 ID `fabrication.gasket_multi_bolt_sector_equilibrium`, 상태 `computed`, 전체 `AssessmentResult` digest, 선택된 단계 ID, joint ID와 physical scope가 일치해야 한다.
- 영향행렬은 유한하고 절점/볼트 배열 크기·순서가 맞아야 한다. 행렬의 공급자, revision, configuration digest, 배열 순서, 수치 내용으로 계산한 canonical digest가 provider Evidence의 SHA-256과 일치해야 하며 Evidence에는 사용권리 ID가 있어야 한다.
- 절점/볼트 axis mapping, 선형 중첩, 비볼트 free-closure 배제와 계산 사용권한을 검토해야 한다. 합성 폐합 또는 힘이 유한 범위를 벗어나면 `out_of_scope`다.
- flange relative compliance는 기존 `FlangeContactFieldRequest`를 그대로 사용한다. 대칭·유한 검사는 그 계약에서 수행되고, 양의 준정부호 support와 접촉 complementarity는 downstream contact solver가 확인한다.

영향행렬은 rectangular bolt-to-node map이므로 대칭행렬이나 양의 정부호성을 자체 요구하지 않는다. 물리적 부호·좌표계·경계조건·선형범위·FE reduction 검토는 공급자와 caller 책임이다. 행렬 밖의 접촉 support 또는 matrix regularization을 추론하지 않는다.

## 해석 한계

정적 adapter는 선택된 knot만 다룬다. 상류 load knots 사이의 볼트 변화나 contact event를 재구성하지 않는다. 출력은 downstream contact request이지, 접촉이 계산됐다는 증거가 아니다. 이 API는 FE response를 만들지 않고, local stress, leakage, seal acceptance, 확률 또는 qualification을 제공하지 않는다. 사용자 데이터·영향계수의 권리 및 해당 물리 조건에서의 유효성은 별도로 확인해야 한다.

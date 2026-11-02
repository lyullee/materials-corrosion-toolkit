# Evidence·온도 지원구간이 고정된 가스켓 Prony 이력

## 목적과 기존 계산 재사용

`fabrication.gasket_evidence_bound_prony_history`는 기존 `gasket_relaxation.py` generalized-Maxwell strain-history 계산에 Evidence, 이용권리, 온도 support 계약을 덧붙이는 공개 API다. branch 응답 방정식을 복제하거나 새로 적합하지 않는다. 계산 본체는 기존 `evaluate_gasket_viscoelastic_history`에 위임한다. 구버전 `GasketViscoelasticHistoryRequest` 및 기존 registry API 사용자는 변경 없이 계속 사용할 수 있다.

모델 입력은 `EvidenceBoundGasketViscoelasticHistoryRequest`, 재료와 Prony parameter는 `EvidenceBoundGasketViscoelasticMaterial`, 결과 객체는 표준 `Calculation`이다. registry 통합 시 `specifications()`에서 `ModelSpec`을 가져온다.

## 새 provenance/support 계약

신규 contract는 기존 재료·시편·source group·condition hash·source hash·provider revision·온도와 branch 입력을 그대로 유지하면서 다음을 요구한다.

- `temperature_support_min_K` / `temperature_support_max_K`: 지원 온도 경계가 유한하고 순서가 맞아야 한다. 단일 입력 온도 `temperature_K`가 이 구간 밖이면 `out_of_scope`이며 온도 보간은 하지 않는다.
- `temperature_support_reviewed`: 실제 재료 상태의 데이터 support라는 검토가 필요하다.
- `evidence`: provider source hash와 material condition hash 각각을 고정하는 `Evidence`가 있어야 한다. 원자료 Evidence는 caller가 선언한 `usage_license_id`와 계산 사용권한을 함께 보유한다.
- `source_and_condition_lineage_reviewed`, `license_and_computational_use_reviewed`: `False`면 결과는 `needs_data`다.

license 식별자는 데이터의 권리 상태를 정직하게 나타내는 caller 제공 값이어야 한다. 프로젝트가 parameter data를 소유하거나 배포 권한을 갖는다는 뜻은 아니다. 데이터의 원 출처/인용은 Evidence에 남기고 재료 조건 digest와 원 파일 digest를 구분한다.

## 계산 본체와 branch 제한

각 구간의 strain은 양 끝 입력 knot를 잇는 선형 경로로 취급한다. 기존 계산기는 각 branch 상태를 닫힌형 업데이트로 구하고 총 압축응력을 equilibrium modulus와 branch stress의 합으로 계산한다. 압축력은 총응력에 caller 지정 면적을 곱한다.

branch modulus와 relaxation time은 양수 typed field다. contract는 NaN/무한대를 거부하고, 기존 solver는 branch state/총응력/힘의 유한성을 추가 확인한다. 압축 전용 입력과 tensile total stress의 out-of-scope 처리도 기존 evaluator의 동작을 따른다. branch 내부 응력은 strain 감소 경로에서 부호를 가질 수 있으므로 내부상태를 인위적으로 0 이상으로 clipping하지 않는다.

## 다중 볼트 평형으로의 연결 경계

출력 history는 `elapsed_time_s`, `compressive_strain`, equilibrium/branch/total stress, `compressive_force_N`을 보존하고 source·condition·provider·license·temperature·request digest를 함께 남긴다. 이 constitutive history는 단일 재료/면적 조건에서 주어진 strain path에 대한 응답이다. 미지 변형률과 gasket force를 공동으로 풀어야 하는 joint problem에는 기존 `fabrication.gasket_prony_joint_history`를 사용한다. 다중 볼트·다중 sector coupling은 별도 평형 계산과 각 위치의 branch state 연결이 필요하다. 본 wrapper가 그 coupling을 대신하거나 단일 aggregate force를 개별 gasket sector로 분배하지 않는다.

시간 knot 사이를 제외한 열이력, 온도별 parameter 전이, 재료 간 보정 전이, nonlinear viscoelasticity, flange bending, unilateral spatial contact, leakage, seal acceptance, code qualification과 lifetime은 추론하지 않는다. 계산 결과는 외부 실험/solver 검증을 대체하지 않는다.

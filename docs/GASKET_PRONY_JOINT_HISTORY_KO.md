# Prony 가스켓과 볼트의 시간별 접촉 평형

`fabrication.gasket_prony_joint_history`는 caller-authorized generalized Maxwell(Prony) 가스켓 재료와 선형 탄성 볼트를 하나의 시간 이력 계산으로 결합한다. 입력은 gasket 면적·압축 높이, bolt 강성, 초기 압축변형률, 시간별 외력과 bolt free-length 변화, 그리고 동일 조건의 가스켓 Prony 계수·초기 내부응력이다.

각 시간 구간에서는 변형률이 양 끝 knot 사이에서 선형으로 변한다고 가정한다. 이 가정 아래 Maxwell branch 내부응력은 구간 끝에서 닫힌형식으로 갱신된다. 갱신식과 bolt 힘의 평형은 endpoint 변형률에 대해 affine이므로, 모델은 각 시점의 압축 변형률을 식으로 풀어 응력·가스켓 힘·볼트 힘·평형 잔차와 branch 응력을 반환한다. 임의 nonlinear root solver를 가정하지 않는다.

처음 시간점은 `t=0`이어야 하며 첫 bolt free-length 변화는 0이어야 한다. 초기 branch 응력에서 계산한 gasket force와 첫 외력 합으로 기준 bolt preload를 정의한다. 모든 입력 이력은 길이와 시간 순서가 일치해야 한다. 최대 압축변형률은 caller가 선언한 유효 지원 한계다. 입력 근거 SHA-256, 재료 조건·시편·provider revision, 전체 입력 digest를 결과에 보존한다.

검토 gate는 joint 형상·힘 평형, 구간 내 선형 strain update, 재료/계수 적용성, 초기 branch state와 계산 사용권한을 포함한다. 계산은 closed contact 구간만 다룬다. 분리 접촉, 인장 gasket 응력, 음의 bolt force, 선언 압축 support 초과가 생기면 부분 결과를 `out_of_scope`로 반환하고 그 시점 이후를 계산하지 않는다.

이 모델은 1자유도 균일 압축·선형 bolt·선형 점탄성이라는 caller 지정 모델 조합이다. Prony 계수 fitting·조건 전이, gasket의 nonlinear hysteresis, 플랜지 공간 유연성/회전, 비균일 접촉, 열전달, 누설률, sealing acceptance 또는 규격 판정은 제공하지 않는다. 합성 예제는 API 구조 확인용이며 검증 근거가 아니다. `examples/model_inputs.json`의 `fabrication.gasket_prony_joint_history`를 참고한다.

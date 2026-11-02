# Crevice cell별 외부 활동도 종분화 투영

`integration.crevice_local_external_activity_projection`는 digest-bound crevice transport campaign의 각 exact time knot와 cell에서 이동된 조성으로 명시된 선형 제약 목표만 재구성하고, 해당 cell의 수용액 질량작용식을 caller 소유 활동도 공급자와 반복 결합한다. 출력은 기존 crevice local speciation volume ledger 형식으로 집계되며, 공급자·내부 질량작용 입력 digest와 molarity standard-state 활동도계수 벡터를 셀별로 보존한다. 외부 공급자 반복 횟수, 최종 고정점 잔차, 마지막 provider 응답 digest 및 전체 iteration transcript digest도 기록해 후속 saturation/열역학 모듈이 계수를 추적할 수 있게 한다.

## 입력과 실행

- 기본 transport binding, cell system template, exact cell context digest, 조성 유도 constraint ID, 완전 knot commit 규칙은 `integration.crevice_local_mass_action_projection` 계약을 사용한다.
- 추가 `activity_iteration_template`은 공급자 ID/revision, 설정·parameter digest, 용매 질량 환산, 표준상태, 단일 이온 convention, 수렴 한도와 적용성 review를 선언한다. 그 template의 species/reaction/constraint topology는 모든 cell template과 같아야 한다.
- Registry 호출은 `runtime_dependencies={"activity_provider": callback}`을 요구한다. callback 요청·응답 형식은 [외부 활동도 공급자 계약](../AQUEOUS_EXTERNAL_ACTIVITY_PROVIDER_KO.md)을 따른다.
- 각 cell에서 기존 damped fixed-point routine이 caller molality activity provider와 mass-action solver를 반복한다. 한 cell이 실패하면 현재 knot는 저장하지 않고 앞서 완성한 knot prefix만 반환한다.

## 경계

종·반응식·평형상수·온도·용매와 표준상태 적용성은 caller가 완전히 제공한다. 이 모델은 후보 phase 검색, 침전/용해, 핵생성 장벽, cell 간 평형, knot 사이 kinetics, 재수송, wall sink, 금속손실 또는 부식률을 계산하지 않는다. Activity provider 구현과 parameter set도 이 package에 포함되거나 자격화되지 않는다. 따라서 외부 모델과 경험 자료의 독립 검토가 필요하고, 현재 API 구현은 수치·실험 검증 전 상태다.

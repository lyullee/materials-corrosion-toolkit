# 다축 stateful damage provider 적분

`evaluate_caller_stateful_multiaxial_damage()`는 caller가 정의한 다축 경로 상태 미분과 순간 손상률을 지정 cycle 순서 및 정수 반복 횟수대로 적분한다. 상태방정식·손상법칙·보정의 물리적 의미는 모두 provider 소유이며 이 어댑터는 계산 적분기만 제공한다.

## 적분 방법

기본 `integration_method="fixed_step_rk4"`는 기존 고정 최대 시간간격 classical RK4 경로를 유지한다. 선택형 `adaptive_step_doubling_rk4`는 각 시도 구간에 대해 한 번의 전체 RK4 단계와 두 번의 반 단계 계산을 비교한다. 4차 RK법 오차 추정치는 두 결과 차이의 1/15로 두고, caller가 제공한 state/damage absolute 및 relative tolerance로 무차원화한다. 허용 오차 이하일 때 두 반 단계 결과를 채택하고, 초과하면 단계 크기를 줄인다. 시간 단계는 선언한 최대/최소 범위, provider 평가 budget 및 interval별 rejection budget으로 제한한다.

적응형 방법은 같은 시각·상태 입력의 provider 호출을 여러 번 수행할 수 있다. 따라서 `adaptive_integration_controls_reviewed=true`와 `provider_repeat_evaluation_is_deterministic_reviewed=true`를 명시해야 한다. provider callback은 외부 상태를 변경하지 않는 결정론적 함수여야 한다. 최소 단계에서도 허용 오차를 만족하지 못하거나 상태 경계, provider budget 또는 rejection 제한을 넘으면 미완료 aggregate를 `out_of_scope`로 반환한다.

결과에는 method ID, 선언 tolerance, 최대/최소 단계, accepted/rejected 단계 수, 최대 관찰 error ratio와 provider 평가 수가 포함된다. 같은 단계·평가·error 통계는 계산된 각 cycle 결과에도 별도 집계되어 cycle별 수렴 행동을 비교할 수 있다. 각 sample interval의 끝점은 reconstruction endpoint에 정확히 맞춘다. 적응형 거절 시도마다 cycle/repetition/interval ID, 전역 sequence 시각, 시도/후속 단계 크기, error ratio와 거절 사유를 기록하고 전체 history digest를 반환한다. 각 cycle 결과에는 해당 cycle에 속하는 거절 이력의 원본 전역 인덱스 범위, cycle-local 이력과 별도 digest도 저장한다. 따라서 반복 cycle에서도 sequence 전체 장부를 검색하지 않고 해당 cycle의 거절 시도를 확인할 수 있다. `maximum_rejection_history_records` 한도를 넘으면 결과는 `out_of_scope`이며, 기록을 잘라내 계산 완료로 처리하지 않는다. 이 local integration error indicator는 모델/재료 불확도, provider 보정오차, path reconstruction 오차 또는 실제 피로 손상 정확도의 추정치가 아니다.

수치 적분이 시작된 뒤 발생하는 상태 경계, callback/provider, rejection-history, 시간 누적, damage aggregate 또는 provider identity 실패에는 동일한 integration diagnostics와 거절 이력/digest를 포함한다. 따라서 실패 응답도 재현·감사에 필요한 적분 설정과 provider 평가 accounting을 보존한다.

## 계약 예제와 범위

예제 `examples/stateful_multiaxial_damage.py`에는 stateful PCHIP request variant가 추가됐고, `examples/multiaxial_damage_provider.py`에는 memoryless PCHIP variant가 있다. 예제 closure 허용치는 합성 경로용으로 넉넉하게 설정해 rate discontinuity를 드러내며, 실제 주기 하중의 허용 기준으로 재사용하면 안 된다.

시간 경로는 caller가 선택한 piecewise-linear, 명시 미분 cubic-Hermite, 표본 기반 PCHIP 또는 SciPy 기반 periodic cubic spline으로 전달된다. PCHIP·주기 spline은 명시 미분 입력을 거절하며, 주기 spline은 정확히 닫힌 응력·변형률 표본과 `periodic_spline_reviewed=true` 확인을 요구한다. 이 cubic 재구성의 계산된 시작·끝 기울기 차이를 caller의 응력률·변형률률 허용치와 대조한다. 이 검사는 주기 경계의 수치 연속성 조건일 뿐 재료 경로나 provider law의 물리적 타당성을 입증하지 않는다.

`examples/stateful_multiaxial_damage.py`는 같은 synthetic cycle/provider 입력에 고정 및 adaptive 적분 요청을 각각 구성한다. 입력 law와 tolerance는 wiring 예시일 뿐 실험값·재료 권고값·검증 결과가 아니다. 이 구현은 caller rate/evolution law의 타당성, 상태변수 설계, cycle extraction, calibration transfer, 물리 qualification, code acceptance를 제공하지 않는다. 수치 검증은 별도 승인된 검증 단계에서 수행한다.

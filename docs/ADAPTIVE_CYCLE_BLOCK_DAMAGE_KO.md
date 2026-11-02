# 정수 cycle block의 적응형 상태·손상 ODE

`AdaptiveCycleBlockDamageRequest`와 `evaluate_adaptive_cycle_block_damage(request, provider)`는 사용자 정의 상태식 `dz/dN=f(N,z,block)`과 비음 손상률 `dD/dN=g(N,z,block)`를 계산한다. N은 각 block 안의 cycle-count 좌표다. 각 block의 총 cycle_count는 양의 정수이고 전체 합은 2^53 이하로 제한한다. 정수 개수의 물리적 의미와 순서, population과 source digest는 caller가 선언한다. 수치 solver의 내부 분할 N은 비정수일 수 있다. 관측 cycle을 분할하거나 새로운 cycle을 검출한 것이 아니다.

기존 `multiaxial_damage_provider.py`에는 이미 tensor-cycle 시간 경로의 adaptive RK4가 있다. 이 모듈은 그 기능의 대체 구현이 아니다. 시간 내 stress/strain 보간 없이 ordered integer block의 cycle-count 영역에서 사용자 state law를 적분하는 별도 API다. 재료의 비비례 피로법칙, 하중 상호작용 또는 calibration transfer를 제공하지 않는다.

Callback은 `(local_cycle_coordinate, state_tuple, block)`을 받아 `state_derivative_per_cycle` 배열과 비음 scalar `damage_rate_per_cycle`을 반환한다. State 배열은 선언된 ID/단위 순서를 따른다. Block parameters는 이름·값·단위의 immutable tuple이다. Provider는 provider_id, revision, configuration_sha256 속성을 요청과 일치시켜야 하며 매 호출 전후에 대조한다. Calibration digest와 이용조건 식별자가 있는 Evidence를 요구한다. 이러한 기록이나 review가 독립 qualification을 뜻하지 않는다.

RK4 한 전구간 step과 RK4 두 반구간 step을 별도로 계산하므로 trial 하나는 정상적으로 callback 12회를 사용한다. 상태와 누적 손상을 함께 적분하며, 성분별 `abs(fine-whole)/15/(atol+rtol*max(abs(old),abs(fine)))` 최대값이 1 이하인 trial의 fine 결과를 수락한다. Richardson 외삽은 하지 않는다. h 조정은 5차 국소 오차 추정의 지수 1/5를 사용한다. 이 추정값은 global error나 결정론·물리 타당성 보장이 아니다. 음의 손상률·비유한 반환·차원 불일치·provider 변경은 실패로 처리한다. 오차 scale overflow도 passing step으로 취급하지 않는다.

모든 RK stage와 최종 trial state에 선언 bounds를 적용하며 clipping하지 않는다. Bound 밖의 trial은 축소 재시도한다. 최소 step 또는 rejection budget에 도달하면 마지막 수락 상태를 유지하고 후보 N bracket을 반환한다. 이 bracket은 수치 stage가 범위를 벗어났다는 설명이며 실제 bound crossing이나 정확한 event root를 입증하지 않는다. Stage에서만 overshoot한 가능성을 남긴다.

선택적 damage_event_threshold에 수락 가능한 trial의 손상이 도달하면 그 trial은 commit하지 않고 마지막 수락 상태와 trial 결과 및 bracket을 반환한다. 정확한 event 위치 또는 수명 예측이 아니다. 현재 구현은 event bracket의 별도 root refinement를 하지 않는다. 같은 이유로 이 결과는 out_of_scope이며 full_requested_history_completed=false다. Bounds와 threshold를 재료 failure criterion으로 자동 해석하지 않는다.

Function-evaluation budget는 성공/실패/거절 trial의 실제 callback 호출을 모두 센다. 처음부터 12회가 남지 않으면 다음 trial을 시작하지 않는다. 완료 block 결과는 completed_blocks에만 기록하고, 중단 block은 accepted_local_cycle_coordinate/accepted_state/accepted_damage로 별도 기록한다. 완료되지 않은 block을 정수 cycle 완료량에 더하지 않는다. 마지막 짧은 remainder는 min step보다 작을 수 있으나 재시도가 필요하면 중단한다. Block 끝마다 다음 block의 local N=0으로 재시작하며 상태와 손상은 유지한다.

예제 `examples/adaptive_cycle_block_damage.py`는 합성 요청과 callback만 정의하고 계산을 실행하지 않는다. 실제 실행 시 요청의 물리·재료·이용조건·초기화·bounds·numerical control review를 독립적으로 작성해야 한다. 현재 테스트·수치 실행·패키징은 수행하지 않았다.

정적 재검토 보강: callback은 calibration_sha256, state_variable_ids, state_units, cycle_count_basis_id, damage_unit 속성도 노출해야 한다. 마지막 값은 무차원 손상을 뜻하는 문자열 `1`이고 나머지는 요청과 정확히 일치해야 한다. 모든 호출 전후에 이 metadata를 함께 대조한다. 상태 단위의 빈 문자열·공백만 있는 값은 입력 오류다. Callback 결과는 두 derivative/damage key만 허용한다. 예를 들어 status=out_of_scope나 다른 실패 표시가 포함된 결과를 무시한 채 수치값만 적분하지 않는다. 필요한 상태·지원범위 실패는 callback 예외 또는 유효하지 않은 결과로 명시하고 마지막 수락 prefix를 보존한다.

검증 예정: 일정 derivative/damage의 닫힌 해, 지수 상태식, block 순서에 민감한 law, 연속 같은 law의 block 분할, 허용오차 축소 수렴, 최대 12회 trial budget 및 rejected-call accounting, state bound의 내부 stage 초과, damage threshold bracket, 최소 step·시간 표현 한계, provider metadata 변경, 음·NaN·무한 rate/차원 오류, error-scale overflow, 매우 큰 정수 cycle과 작은 fractional step. 독립 law calibration과 물리 validation은 수학/소프트웨어 검증과 별도로 필요하다.

추가 검증은 올바른 state 수치지만 잘못된 단위/ID 순서/calibration digest인 callback, 실행 중 단위 metadata 변경, 빈 state unit, 실패 status와 수치를 함께 반환하는 callback, extra key, 마지막 짧은 remainder에서의 rejection을 포함한다. 정적 검토는 실제 실행 검증이 아니다.

Block 입력의 parameter ID/단위와 block/population/loading-state ID는 공백뿐인 문자열도 거부한다. 값을 trim하거나 다른 ID로 바꾸지 않는다. Parameter 값은 유한 float이며 cycle_count는 strict integer다. 공통 Contract의 기존 allow_inf_nan=false/strict=true 제한을 이 두 필드에도 명시했다. NaN·무한 parameter와 boolean cycle count는 유효 입력이 아니다. 관련 malformed 입력은 후속 실행 검증 대상이다.

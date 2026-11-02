# 유한표본 Sines parameter 기반 피로수명

`fatigue.multiaxial_sines_parameter_life`는 기존의 caller 계수 기반 유한표본 Sines형 한계 screen을 실행한 뒤, 산출된 양의 parameter를 동일 재료조건의 caller 정진폭 피로수명 곡선에 연결한다. API는 연구자가 curve points, Evidence, 해시, source record ID, 재료조건 및 보간·권리 검토를 입력하도록 설계되어 있다.

## 계산 순서

1. 중첩 screen이 응력 이력 해시, 시각 정렬, 재료조건과 계수 Evidence를 확인한다.
2. finite sampled deviatoric half-diameter와 piecewise-linear time-average hydrostatic stress를 caller 계수로 결합한다.
3. screen parameter가 양수이고 curve 검토가 완료된 경우, parameter가 caller 점 사이에 있을 때만 로그-로그 직선 보간으로 수명을 계산한다.
4. 계산 결과에는 screen 결과, 입력·곡선 digest와 보간 bracket의 source record ID를 보존한다.

## 적용 경계

- curve parameter는 cycle 수 증가에 따라 엄격히 감소하는 유한 곡선으로 입력한다. 곡선 밖 값은 외삽하지 않고 `out_of_scope`로 반환한다.
- Sines형 계수, 한계, 시간가중 평균 및 곡선은 모두 caller가 정하고 적합성을 검토한다. 여기서 특정한 보편 계수나 재료곡선을 제공하지 않는다.
- 중첩 screen의 유한표본 half-diameter는 표본 간 최댓값 거리 descriptor다. 이를 연속 경로 진폭이나 원 논문의 별도 convention으로 확대 해석하지 않는다.
- 결과는 caller 곡선에 조건부인 수명 추정치다. cycle counting, 가변진폭 손상 누적, 하중 순서 효과, 고장확률, 규격 합격 및 재료 qualification은 산출하지 않는다.
- 권리 검토나 동일 재료조건 검토가 미완료면 `needs_data`를 반환한다.

## 입력 교환

`MultiaxialSinesParameterLife.screen`에는 `MultiaxialSinesMeanLimitScreen` 계약을 넣는다. `life_curve_points`는 `(screening_parameter_Pa, cycles_to_failure, source_record_id)` 순서의 고유 관측점이며 `life_curve_sha256`은 정렬된 point 계약 배열의 canonical digest다. `life_curve_evidence`는 caller source ID와 동일 SHA-256을 담아야 한다.

## 독립 검증 과제

수치 검증 시에는 곡선 knot 재현, 양 끝점 지원, 내부 로그-로그 보간, curve 밖 거부, 재료조건 불일치 및 digest 변조 사례를 분리한다. 물리 검증은 동일 합금·온도·환경·시편 방향·수명 끝점에 대해 보정에 사용하지 않은 독립 시편의 검토 자료를 필요로 한다. 기존 한계 screen의 통과만으로 수명 모델을 검증했다고 보지 않는다.

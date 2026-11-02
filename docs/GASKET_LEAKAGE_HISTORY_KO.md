# 보정 gasket 누설 이력 적분

## 계산 경로

`fabrication.gasket_calibrated_leakage_history`는 gasket 접촉면의 caller 보정 누설 flux table을 시간별 평균 접촉압과 차압에 적용한다. 두 압력 방향 모두 표의 support 안에서만 bilinear interpolation하며 각 접촉 node flux에 선언된 접촉 면적을 곱해 joint molar leakage rate를 합산한다.

`gasket_leakage_request_from_flange_contact_history()`는 등록된 spatial linear/nonlinear viscoelastic flange-contact AssessmentResult의 material-independent 접촉 압력장을 누설 요청에 연결한다. node 순서, joint/physical scope, 접촉면적, 시간 범위와 upstream assessment input digest를 일치시킨다. contact result의 내부 refinement knots가 원 요청 knots와 다르면 사용자가 차압의 선형 시간 재구성을 명시적으로 검토해야 한다.

## 시간 적분

연속 요청 시간 knots 사이에서 접촉압과 차압은 선형으로 재구성된다고 둔다. 보정 flux가 각 격자 셀에서 압력 두 축에 대해 bilinear이므로 이 경로를 따라 flux는 시간의 2차 이하 다항식이다. 계산기는 각 node 접촉압 또는 차압이 보정 축의 내부 knot를 통과하는 시각에 분할한다. 각 작은 구간에서 Simpson 3점 적분을 사용하므로 선언된 piecewise-linear pressure path와 bilinear table의 조합에 대해 구간 누설량을 정확 적분한다(부동소수점 반올림 제외). 반환값은 split fractions와 각 구간 수를 포함한다. table cell은 2,000,000 이하, 전체 campaign의 적분 subinterval 수는 요청의 `maximum_time_integration_subintervals` 이하여야 한다.

## 필요한 근거와 제한

- 보정 표의 `calibration_record_sha256`, provider revision/configuration, Evidence와 calibration/joint match review를 유지한다.
- node 면적이 실제 접촉영역의 완전한 분할인지 검토한다.
- 차압 방향·단위와 차압 부호가 보정 표의 정의와 일치해야 한다.
- 계산은 표 밖으로 보간/외삽하지 않는다. 점 사이 압력 경로는 caller가 수락한 선형 재구성이다.
- 접촉역학을 생성하거나 보정곡선을 다른 gasket/joint에 전이하지 않는다. 유체 통로 해석, leak-tightness 기준, seal acceptance 또는 자격화된 설계 판단을 제공하지 않는다.

테스트와 독립 누설 자료에 대한 자격화는 별도 검증 작업에서 수행한다.

`examples/gasket_leakage_exact_interval.py`는 `examples/model_inputs.json`의 합성 요청만 사용해 결과 구조를 출력하는 배선 예다. 실행하지 않은 예제이며 값은 보정 데이터가 아니다.

# 공정 모니터링 연동 요청

검토한 기준 소스는 `79b4cf52a0acd0d0cbd3addbe82c3d98d6385e5a`이다. 기존 신호 품질·시계·측정/예측 구분과 어댑터 구조를 유지하면서 재료·검사 특징을 추가한다.

## 요청 항목

- 두께·결함 깊이·균열 길이·부식속도·누적 사이클·손상 지수의 물리량 및 단위 매핑을 추가한다.
- 저빈도 검사와 초 단위 센서의 신선도 정책을 분리한다. 검사 시각과 다음 검사까지 유효하다는 판단은 다른 정보다.
- `matintegrity.monitoring_context.v1`의 자산·부위·모델·상태·단위·시간 기준·해시를 보존한다.
- 송신 기준은 `MonitoringAssessmentRecord`와 `docs/schemas/MonitoringAssessmentRecord.json`이다.
  `source_digest`를 완전한 assessment snapshot의 canonical SHA-256으로 재계산하고 불일치 레코드를
  거절한다. 과거 필드명과 달리 이를 원 데이터 파일 hash로 해석하지 않는다.
- 통계 이상 점수와 물리적 손상 여유를 별도 채널로 유지한다. 결측·범위 밖 평가를 정상 값으로 채우지 않는다.
- 외부 프로세스가 실행하는 계산 특징을 별도 공급자 경로로 연결하며 이 라이브러리에 MatIntegrity 구현을 복사하지 않는다.
- 성분·경도·방식 예산의 계산 상태와 요구조건 결과를 별도로 보존한다. `computed`를 정상/합격으로 매핑하지 않는다. `outcome` 또는 `declared_budget_outcome`, 절차의 `policy_gate`와 요구조건 출처를 유지한다.
- 새 모니터링 스냅샷의 모델 판본·입력·문맥·출처 ID·`probability_semantics`를 보존한다. 공간 초과·POD·기간 확률을 같은 risk score 열로 합치지 않는다.
- WILLOW 연동은 합성/실제 영역, 반복 시편 ID, 개별 특징 누락과 처리 실패를 보존한다. 미확정 시간대·sample clock·장치 gain/filter 변경 및 긴 기록 공백을 명시하며 초기 pit 치수를 시계열 참값으로 학습하지 않는다.
- 열 이력은 관측과 모델 예측을 분리하고 시간·셀/위치·재료·형상 ID, K 단위, 경계 열의 부호, 모델 버전·입력 해시와 에너지 잔차를 수신한다. 열응력은 평면 조건·합력/변형 제어·단면 합력·평가 위치·탄성 한계 상태를 보존한다. 계산 온도를 센서 관측으로, 탄성 선별값을 허용응력·고장확률로 이름 바꾸지 않는다.
- FAD 수신은 point/load case/location/material condition과 K/reference-stress/toughness solution ID, curve ID·basis·digest·지원 Lr를 보존한다. `declared_boundary_outcome`을 실제 균열 검출, 규격 합격, 잔여수명이나 PoF로 이름 바꾸지 않는다. Crack-arrest raw machine channel은 계산된 toughness 및 현장 균열 크기와 별도 관측 종류로 유지한다.

인수 시험은 단위 차원 불일치, 시간 기준 불일치, 오래된 관측, 계산 결과의 미확정 상태, 측정과 모델 예측 구분을 포함한다. 통계 경보 개수로 연간 고장빈도를 학습하는 기능은 이 요청에 포함하지 않는다.

현재 검토 revision에는 `process-monitoring.detection.v1` 송신 계약은 있으나
`matintegrity.monitoring_context.v1` 수신 validator가 없다. 상대 저장소 구현 시 두 계약을 별도
객체로 유지하고, `computed`를 normal/alarm으로 바꾸지 않으며 `needs_data`·`out_of_scope` 레코드도
삭제하지 않는 음성대조 시험을 추가한다. MatIntegrity 측 송신·변조 검증은
`validation/monitoring_exchange_contract.json`에 있다.

`declared_model_pressure_difference_capacity_Pa`와 `pressure_basis=internal_minus_external`를 정적 차압 용량으로 수신한다. 절대 내압과 바로 비교하거나 MAWP·파열 확률로 이름을 바꾸지 않는다. 기준/형상 공급자 ID·해시·적용성을 보존한다.

민감도는 별도 `SobolReport` 스키마로 수신한다. 원 응답의 물리 단위와 지수의 단위 1을 구분하고, 평가자 판본·분포/설계/평가 digest·자산/시간 문맥·`precision_status`를 보존한다. 분포가 바뀐 분석의 중요도 변화를 자동 열화 추세로 사용하지 않는다. 기간 PoF·공간 초과·POD와 합산하지 않으며 수치 기준 미충족·미계산·비재현·분산 미확정을 경보나 정상 상태로 채우지 않는 수신 검사를 추가한다.

분극 결과 `corrosion.mixed_potential`은 전위 기준 ID와 V, 전극별 부호 있는 순전류 A, 면적과 곡선·점 근거를 수신한다. 다중/평탄 평형과 수치 미해상을 보존하고 대표 전위가 비어 있으면 정상 값으로 채우지 않는다. 순전류를 금속 용출 전류·부식 속도·기간 PoF로 이름 변경하지 않는다. 수신 검사는 전위 기준 불일치, 미검토 스캔/저항 조건, 여러 평형점, 지지 구간 끝점과 동적 안정성의 미확정을 포함한다. 상세 계약은 `../ELECTROCHEMISTRY_KO.md`와 `../schemas/PolarizationCurve.json`, `../schemas/MixedPotentialEquilibrium.json`을 따른다.

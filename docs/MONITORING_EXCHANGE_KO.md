# 공정 모니터링 교환계약

## 역할

`monitoring_record(AssessmentResult)`는 계산 결과를
`matintegrity.monitoring_context.v1` JSON으로 내보낸다. 공개 Pydantic 계약은
`MonitoringAssessmentRecord`이며 스키마는 `docs/schemas/MonitoringAssessmentRecord.json`에 있다.
통계 모니터링 프로젝트가 재료·부식 계산값을 특징으로 사용할 때 모델·입력·문맥·단위와 상태를
잃지 않게 하는 교환 경계다.

계약은 자산·부위·시간 기준, 모델 ID·버전, 입력과 입력 digest, 값·단위, 가정·주석, 근거 ID,
실행환경, 자격 수준과 확률 의미를 보존한다. `source_digest`는 이름의 과거 호환성을 유지하지만
원 데이터 파일 hash가 아니라 완전한 `AssessmentResult` 스냅샷의 canonical SHA-256이다. 수신자가
값·모델 버전·확률 의미 등 스냅샷 필드를 바꾸고 digest를 그대로 두면 검증이 실패한다.

## 상태와 확률 경계

`computed`는 계산을 수행했다는 뜻이며 정상·합격·무경보가 아니다. `needs_data`와 `out_of_scope`도
그대로 전송되며 0, 정상값 또는 false alarm으로 대체하지 않는다. `probability_semantics`는 공간
크기초과, POD, 특정시점 상태확률, 기간 최초고장확률 등을 구분한다. 서로 다른 의미를 하나의 risk
score로 합치거나 통계 alarm 빈도를 고장빈도로 바꾸는 기능은 이 계약에 없다.

공정 모니터링의 `process-monitoring.detection.v1`은 시간별 score·threshold·alarm·valid를 나타내는
별도 계약이다. 두 레코드는 자산·센서·시간 identity를 외부에서 검토한 뒤 나란히 보존해야 하며,
한쪽을 다른 쪽으로 이름만 바꾸면 안 된다.

## 검증과 현재 통합 상태

`tests/test_monitoring_exchange.py`는 JSON 왕복, context 일치, 값·버전·확률 의미 변조 차단,
`needs_data` 보존을 검사한다. `scripts/validate_monitoring_exchange.py`는 작성한 P–T 결과의 왕복과
변조 음성대조를 수행해 `validation/monitoring_exchange_contract.json`을 만든다.

`process-monitoring-toolkit`의 검토 기준 commit은
`79b4cf52a0acd0d0cbd3addbe82c3d98d6385e5a`다. 해당 revision은 아직 이 스키마의 수신 validator를
구현하지 않았으므로 현재 증거는 송신 계약 검증이지 live end-to-end 통합이 아니다. 필요한 상대
저장소 변경은 [공정 모니터링 확장 요청](extension_requests/MONITORING_KO.md)에 기록한다.

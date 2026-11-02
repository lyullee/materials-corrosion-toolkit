# human-reliability-toolkit 확장 요청

검토 기준은 공개 저장소 `human-reliability-toolkit`의 `d2754bbea16e12d00240e88d13cb4badbe672ac3`다. 현재 `AssessmentEngine.assess`는 `human_reliability.assessment.v1` 결과와 `Estimate` JSON을 만들지만 MatIntegrity용 versioned exporter는 없다. 저장소의 MIT 라이선스와 기존 엄격 계약을 유지하면서 아래 송신·수신 경계를 해당 저장소의 별도 세션에서 구현한다.

## 송신기

`matintegrity.human_reliability_estimate.v1` JSON Schema에 맞춘 순수 adapter를 추가한다. 선택한 `HumanFailureEvent`와 대응 `Estimate` 전체를 그대로 포함하고 공급자 package version·정확한 Git revision, assessment input digest, task/procedure/context identity를 채운다. event ID, conditioning, opportunity definition, evidence ID, method status, recovery/timing/dependency 포함범위를 재해석하지 않는다.

확률 의미는 `failure_probability_per_defined_opportunity`로 고정한다. demands/year, 기간 최초고장, 장비 고장빈도 또는 개인 특성으로 이름을 바꾸지 않는다. assessment의 `empirical_plant_validation_claim=false`를 유지하며, `assumed`, `research`, `method_estimate`, `empirical` 상태를 모두 같은 자격으로 합치지 않는다.

송신시험은 event–estimate ID/conditioning 불일치, recovery/timing 중복, evidence 누락, payload 변조, 0과 1 확률을 포함한다. MatIntegrity 공개 Schema 검증과 JSON 왕복 후 원 event/estimate의 canonical digest가 같아야 한다.

## MatIntegrity 문맥 수신기

`matintegrity.monitoring_context.v1` 수신 adapter를 추가해 재료·검사 평가를 HRA의 `Evidence`와 `ContextValue` 후보로 보존한다. `status`, model/version, asset/location/time basis, values/units, assumptions/notes, qualification, source digest를 유지한다. `computed`를 정상으로, `needs_data`를 실패로, margin·anomaly score를 HEP로 자동 변환하지 않는다. 어떤 값이 cue, procedure precondition 또는 작업 맥락인지 인간 검토가 먼저 필요하다.

수신기는 원 MatIntegrity assessment digest를 검증하고 HRA task/context와 asset·location·clock 매핑을 별도 근거로 요구한다. 같은 모니터링 결과를 cue와 실패결과에 중복 사용하거나 자동·수동 방호의 공통 센서 의존성을 삭제하지 않는다.

## 완료 조건

1. 고정 revision의 실제 `AssessmentEngine` 예제가 송신 Schema를 생성한다.
2. MatIntegrity가 JSON을 수신하고 원 event·estimate digest를 재구성한다.
3. MatIntegrity의 `computed`, `needs_data`, `out_of_scope` 예제를 HRA가 의미 변경 없이 수신한다.
4. 작업 기회당 확률이 기간 확률·연간 빈도로 자동 변환되지 않는 음성대조를 둔다.
5. 공통 cue, 자동 방호, 작업 반복과 재료고장 사이의 의존성은 별도 위험 모델 없이는 독립으로 처리하지 않는다.

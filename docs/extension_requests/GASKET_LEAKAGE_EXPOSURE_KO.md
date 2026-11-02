# 확장 요청: gasket leakage exposure downstream adapter

## 구현된 core 경계

`integration.gasket_leakage_scenario_exposure`는 digest-pinned finite correlated gasket leakage scenario result에서 각 scenario의 `mol/s` rate에 caller-reviewed constant-state duration을 곱해 `mol` amount와 finite-set extrema witness를 낸다. 이 결과는 누설량 basis이지 failure event probability가 아니다.

## 외부 세션 요청

1. consequence module에 해당 mol amount를 source term 또는 released inventory로 전달하는 typed adapter를 추가한다. 물질 조성, 유체 상태, 분출/flash rate와 독성·가연성 consequence는 별도의 Evidence-backed provider 입력으로 요구한다.
2. FTA/reliability 사용 시 별도 event definition을 만들고 gasket leak amount threshold, 시간창, detection/isolation action, demand frequency를 caller가 명시하도록 한다. 연속량을 Bernoulli probability로 임의 변환하지 않는다.
3. time-varying exposure가 필요하면 bolt load/contact/pressure history를 동기화해 시간 적분하는 별도 consumer를 구현한다. constant-state adapter의 amount를 transient 결과로 재사용하지 않는다.
4. downstream adapter 모두 source AssessmentResult digest, asset/location/time basis와 scenario IDs를 보존한다.
5. 공개 계산 예제는 합성 데이터로 작성하고, 독립 consequence/FTA benchmark는 출처·사용권을 기록한 뒤 수행한다.

## 한계

현재 core는 유한 scenario 집합과 일정 누설 상태를 가정한다. 시나리오확률, seal acceptance, 운영 위험 또는 consequence를 계산하지 않는다.

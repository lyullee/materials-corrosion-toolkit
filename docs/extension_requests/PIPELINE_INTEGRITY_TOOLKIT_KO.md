# pipeline-integrity-toolkit 확장 요청

검토한 로컬 소스는 `pipeline-integrity-toolkit` 0.1.0.dev0이며 Git 저장소에는 아직 commit이 없다. 검토 시점의 `pyproject.toml`과 `src/**/*.py` 111개 파일의 결정론적 소스 트리 SHA-256은 `446ffe69d10dbcc57427dcc45a37eef39da0e9b92bf7ce0c04a2d29230bb37c0`이다. 이 값은 commit ID가 아니며 이후 변경 시 반드시 다시 계산해야 한다.

별도 세션에서 다음 송신 adapter를 구현한다.

1. `pipeline_integrity.contracts.AssessmentResult` 전체를 `matintegrity.pipeline_assessment.v1` JSON Schema에 맞춰 내보낸다.
2. package version과 결정론적 source-tree SHA-256·파일 수를 넣는다. 첫 정식 commit 이후에는 commit ID도 별도 필드로 제공하되 source hash를 대체하지 않는다.
3. 모델 ID·버전·status, 입력·출력 단위, asset/scenario/clock/origin, evidence, runtime, qualification을 바꾸지 않는다.
4. `computed`를 정상상태, 합격, 현장 적합 또는 설계 승인으로 바꾸지 않는다.
5. 수신 측의 `PipelineAssessmentRecord` JSON 왕복과 digest 검사를 상대 저장소 집중시험에 추가한다.

기존 `MaterialJob`/`MaterialReceipt`는 반대 방향의 MatIntegrity 호출을 이미 엄격하게 검증하므로 유지한다. 운전 압력·온도 이력은 `matintegrity.operating_history.v1`, 국부 응력·변형률은 `matintegrity.local_tensor_history.v1`를 재사용하고 새 중복 schema를 만들지 않는다. 배관 결과를 부식률·수명·FTA 기초사건으로 자동 변환하는 기능은 이 요청 범위가 아니다.


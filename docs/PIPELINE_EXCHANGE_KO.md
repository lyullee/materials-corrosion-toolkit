# 배관 평가 결과 교환 계약

`PipelineAssessmentRecord`는 외부 배관 해석기가 만든 공통 평가 결과를 재료·부식 워크플로로 가져오는 수신 계약이다. 계산식을 복제하거나 배관 결과를 재료 열화 결과로 재해석하지 않는다.

```python
from matintegrity.pipeline_exchange import pipeline_assessment_record

record = pipeline_assessment_record(
    provider_id="pipeline-integrity-toolkit",
    provider_package_version="0.1.0.dev0",
    provider_source_tree_sha256="...",
    provider_source_file_count=111,
    source_result=pipeline_result,
    limitations=["Software exchange only; not field or design acceptance."],
)
```

계약은 원 `pipeline_integrity.result.v1` 전체, 모델 ID·버전, 계산 상태, 입력·출력 단위, 자산·시나리오·clock·origin, evidence, runtime, qualification을 보존한다. 평탄화한 필드와 원 payload가 다르거나 원 결과·전체 receipt digest가 바뀌면 검증에 실패한다. `computed`는 계산 실행 성공이며 현장 적합, 설계규격 충족 또는 사용 승인과 같지 않다. 이 때문에 `field_or_design_acceptance_claim`은 v1에서 항상 `false`다.

검토 당시 상대 소스 트리에는 Git commit이 없었다. 따라서 존재하지 않는 revision을 만들지 않고 `pyproject.toml`과 `src/**/*.py`의 상대경로·바이트를 정렬해 만든 SHA-256과 파일 수를 기록한다. 상대 저장소가 정식 commit을 만들면 송신 측은 commit과 동일한 tree identity를 함께 내보내는 후속 버전을 검토해야 한다.

`scripts/validate_pipeline_exchange.py --provider-root <checkout>`는 실제 `geometry.pipe` 예제를 실행하고 JSON 왕복, clock 변조 거절, 설계승인 재명명 거절을 확인한다. 이는 교환 소프트웨어 검증일 뿐 유압·구조·부식 물리, 설계규격 또는 시스템 위험의 독립 검증이 아니다.


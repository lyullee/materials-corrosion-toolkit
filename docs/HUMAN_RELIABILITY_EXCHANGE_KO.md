# 인적신뢰도 추정값 교환

`HumanReliabilityEstimateRecord`는 독립 인적신뢰도 공급자가 계산한 한 작업 기회당 실패확률을 작업·절차·사건 정의와 함께 보존한다. 검토한 `human-reliability-toolkit`의 `HumanFailureEvent`와 `Estimate` 전체 JSON, 공급자 Git revision, assessment input digest, context와 procedure identity를 함께 저장하고 각 원 레코드와 전체 payload에 SHA-256을 적용한다.

확률 의미는 `failure_probability_per_defined_opportunity`로 고정된다. `failure_definition`, `opportunity_definition`, `conditioning`, 관련 task step, initiating/latent/response 역할, dependency group, recovery·timing·dependency 포함범위, 방법·상태·근거 ID·불확실성·trace를 버리지 않는다. 원 event와 estimate의 사건 ID·conditioning·포함범위가 다르면 수신을 거절한다.

```python
from matintegrity.human_reliability_exchange import human_reliability_estimate_record

record = human_reliability_estimate_record(
    provider_id="human-reliability-toolkit",
    provider_revision="reviewed-git-revision",
    assessment_input_digest="0" * 64,
    procedure_version="procedure-revision",
    context_id="operating-context",
    source_event=event_json,
    source_estimate=estimate_json,
    limitations=["Task-specific estimate; no period-risk conversion."],
)
```

이 값은 사람의 속성이나 개인 실패확률이 아니다. 정의된 작업 기회와 조건에 속한다. 요구 횟수, 기간, 작업 간 의존성, 공통 cue·팀·절차·장비 의존구조 없이 MatIntegrity의 `conditional_first_failure_in_period`, 연간 빈도 또는 FTA 기초사건으로 변환하지 않는다. 물리 설비의 재료 열화확률과 인적 대응실패확률도 독립이라고 가정해 단순 곱하지 않는다.

`empirical_plant_validation_claim`은 이 v1 계약에서 항상 false다. 실제 현장 자격을 주장하려면 독립적인 표본 모집단, 기회 분모, 검열·누락, 작업·절차·설비 전이가능성, calibration/holdout과 의존성 검증을 갖춘 새 계약이 필요하다.

`scripts/validate_human_reliability_exchange.py`는 작성 음성대조와 선택적인 고정 공급자 checkout 실행을 지원한다. 공급자 실행 성공은 소프트웨어 end-to-end 확인일 뿐 인간 수행도나 현장 위험 검증이 아니다.

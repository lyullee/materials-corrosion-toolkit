# 전기화학 벽두께 유한 시나리오 envelope

`integration.electrochemical_wall_thickness_scenario_envelope`는 이미 계산된 `integration.electrochemical_metal_loss_wall_thickness_history` 결과를 완전한 시나리오 행으로 받아, 공급한 각 시간 절점에서 잔여두께와 required-thickness margin의 최솟값·최댓값 및 각각의 witness scenario ID를 계산한다.

## 입력과 lineage

- 각 행은 고유 `scenario_id`, 계산된 `AssessmentResult`, 전체 결과 JSON의 SHA-256을 포함한다.
- 순서가 있는 전체 시나리오 행 목록의 `canonical_digest`를 `scenarios_sha256`으로 고정한다. `scenario_provider_id`와 동일 source ID 및 manifest digest의 `Evidence`가 필요하다.
- 모든 결과는 asset·location·time basis, physical scope, material condition, baseline ID/hash, required-thickness history 및 정확히 같은 ordered time knots를 공유해야 한다.
- 시나리오 간 면적·밀도·전기화학 결과와 같이 불확실성을 표현하는 값은 각 완전 결과에 남겨둔다. 이 집계기는 서로 다른 입력을 독립 조합하거나 시나리오 간 값을 보간하지 않는다.
- 권리 검토 자료에는 `usage_license_id`가 있어야 한다. review flags로 전체 시나리오 집합의 범위·의존성, 공통 기준선/범위, 권리 및 계산 사용 허용을 선언한다.

```python
from matintegrity.contracts import canonical_digest
from matintegrity.models.electrochemical_wall_thickness_scenario_envelope import (
    ElectrochemicalWallThicknessScenario,
    ElectrochemicalWallThicknessScenarioEnvelope,
)

rows = tuple(
    ElectrochemicalWallThicknessScenario(
        scenario_id=scenario_id,
        wall_result=wall_result,
        wall_result_sha256=canonical_digest(wall_result.model_dump(mode="json")),
    )
    for scenario_id, wall_result in computed_wall_results
)
manifest_sha256 = canonical_digest([row.model_dump(mode="json") for row in rows])
request = ElectrochemicalWallThicknessScenarioEnvelope(
    assessment_id="asset-17-corrosion-scenario-envelope",
    asset_id="asset-17",
    location_id="cml-4",
    time_basis="campaign-relative-seconds",
    physical_scope_id="pipe-spool-17",
    material_condition_id="heat-treatment-record-17",
    baseline_id="ut-baseline-2026-01",
    baseline_record_sha256="<64-character-baseline-sha256>",
    scenario_provider_id="caller-scenario-manifest",
    scenario_provider_revision="rev-1",
    scenarios_sha256=manifest_sha256,
    scenarios=rows,
    scenario_evidence=(scenario_manifest_evidence,),
    usage_rights_evidence=(rights_evidence,),
    usage_license_id="caller-confirmed-computational-use",
    complete_scenario_set_reviewed=True,
    joint_scenario_dependence_reviewed=True,
    baseline_and_scope_match_reviewed=True,
    usage_rights_reviewed=True,
    computational_use_authorized=True,
)
```

등록된 evaluator에는 `ModelRegistry.run()`으로 호출하고 envelope와 같은 asset·location·time basis를 가진 `RunContext`를 준다. 입력 manifest의 순서와 그 digest를 그대로 유지한다.

## 결과 의미와 제한

각 시각의 최솟값·최댓값은 **그 절점에서만** 계산된 유한 시나리오 집합의 pointwise extrema다. 서로 다른 시각의 극값은 다른 witness scenario에서 나올 수 있으므로 출력들을 이어 새로운 physical trajectory로 해석하지 않는다. 시나리오 개수와 각 upstream result/input/projection digest를 함께 보존한다.

시나리오 확률이나 가중치, 연속 입력범위 보증, confidence interval, first-passage probability, remaining-life forecast, corrosion-rate qualification, code acceptance 및 fitness-for-service 판정을 만들지 않는다. 시나리오가 완전 집합이라는 선언과 공급 범위의 타당성은 호출자가 책임진다.

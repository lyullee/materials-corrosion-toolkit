# 외부 접촉 solver 상태 격자 탐색

## 목적

이 모듈은 caller가 선택한 여러 시각에 외부 contact/FE solver를 호출해 node 하나의 접촉 상태열을 받습니다. 인접한 시각의 상태가 다르면 그 시간 구간을 관측 전이 bracket으로 보고합니다. 단일 bracket의 이분 축소를 수행하는 `gasket_contact_transition_refinement`과 달리, 이 API는 caller grid 전 구간에서 복수의 관측 전이를 요약합니다.

패키지는 FE/contact solver를 제공하지 않습니다. callback provider의 실행, 입력 구성, 해석 재시작 및 수렴 검토는 caller가 담당합니다.

## Python API

- 요청 계약: `GasketContactStateGridSweep`
- callback query: `ExternalContactStateGridQuery`
- callback response: `ExternalContactStateGridResponse`
- 평가 함수: `evaluate_gasket_contact_state_grid_sweep`
- registry 연결용 사양: `specifications()`
- model ID: `fabrication.gasket_contact_state_grid_sweep`
- runtime dependency key: `contact_state_provider`

## 시간 격자와 source 계보

입력 source는 다음 모델의 계산된 contact-history `AssessmentResult`입니다.

- `fabrication.flange_viscoelastic_contact_history`
- `fabrication.flange_nonlinear_viscoelastic_contact_history`

요청은 source 결과 SHA-256, input/context digest, physical scope, node ID, `time_history[].time_s` 단위와 node 상태를 확인합니다. caller는 엄격히 증가하는 `probe_times_s`를 주고 첫·마지막 시각을 source history의 정확한 지원 끝점과 일치시켜야 합니다. 각 시간 간격은 caller가 검토한 `maximum_probe_gap_s` 이하이어야 하며, grid 크기는 최대 callback 횟수를 넘을 수 없습니다.

provider 식별자, revision과 구성 digest는 요청에 고정됩니다. 각 질의 digest는 source history, 물리 범위, 자산·위치·시간기준, node, 시각, provider 구성을 묶습니다. 응답은 이 query digest와 같은 source/context/node/provider/time을 반환하고, provider를 식별하는 `Evidence` 및 응답 payload의 canonical SHA-256을 포함해야 합니다. 불일치가 발생하면 계산은 중단되고 성공한 응답 prefix와 첫 오류가 보존됩니다.

## 사용 예

```python
from matintegrity.contracts import canonical_digest
from matintegrity.models.gasket_contact_state_grid_sweep import (
    GasketContactStateGridSweep,
    evaluate_gasket_contact_state_grid_sweep,
)

request = GasketContactStateGridSweep(
    assessment_id="joint-state-grid-01",
    physical_scope_id="joint-scope-01",
    source_contact_history=contact_history_result,
    source_contact_history_sha256=canonical_digest(
        contact_history_result.model_dump(mode="json")
    ),
    node_id="gasket-node-004",
    probe_times_s=(0.0, 0.25, 0.5, 0.75, 1.0),
    maximum_probe_gap_s=0.25,
    physical_scope_and_time_basis_reviewed=True,
    provider_identity_and_configuration_reviewed=True,
    probe_grid_resolution_reviewed=True,
    computational_use_authorized=True,
    provider_id="caller-fe-contact-solver",
    provider_revision="reviewed-revision",
    provider_configuration_sha256="0" * 64,
)
calculation = evaluate_gasket_contact_state_grid_sweep(
    request,
    contact_state_provider=caller_owned_solver_callback,
)
```

callback은 각 `ExternalContactStateGridQuery`에 대해 `ExternalContactStateGridResponse` 또는 그 JSON dictionary를 반환합니다. 응답 payload digest는 `result_sha256`를 제외한 response contract의 `model_dump(mode="json")`에 `canonical_digest`를 적용해 계산합니다.

## 결과 해석과 한계

- 각 bracket은 바로 인접한 probe 시각의 provider 상태가 다르다는 뜻입니다. bracket 내부의 전이 시각을 보간하거나 root solve하지 않습니다.
- 같은 상태가 양 끝에 반환되어도 중간에 발생했다 되돌아온 전이는 빠질 수 있습니다. 최대 probe 간격은 해상도 선택일 뿐 숨은 전이의 오차 한계가 아닙니다.
- `multiple_transitions_observed`는 grid에서 복수 변화가 관측됐는지 나타냅니다. 전체 시간영역의 완전한 접촉 전이 목록을 보증하지 않습니다.
- 결과는 접촉 상태 자료 요약입니다. seal acceptance, 누설, 국부 응력, FE 적합성, 구조 안전 또는 failure probability를 계산하지 않습니다.
- response 실패 시 `needs_data`와 함께 이전 검증 sample prefix 및 첫 실패를 반환합니다. 미완료 sweep의 일부를 완료 이력처럼 합산하지 않습니다.
- 본 모듈은 독립 계산 경로입니다. 중앙 registry/schema/catalog 연결, provider 실행, 테스트 및 패키지 검증은 후속 작업입니다.

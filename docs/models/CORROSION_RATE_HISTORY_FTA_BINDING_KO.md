# 부식률 이력과 FTA 기본사건 연결

## 식별자와 범위

- Adapter model ID: `adapter.corrosion_rate_history_to_fault_tree_basic_event`
- Adapter version: `1`
- Upstream corrosion model ID: `corrosion.piecewise_linear_rate_thickness_history`
- Selected condition: `required_thickness_crossing_within_history_support`
- Output contracts: `FaultTreeBasicEvent`, `IntegrityEventBasis`, `Calculation`

이 어댑터는 계산된 부식률 이력의 감육량이나 required-thickness crossing으로 확률을 계산하지 않는다. FTA에 넣을 이벤트 확률, 의미, conditioning 문장, 확률 scope ID 및 그 근거는 모두 호출자가 별도로 제공해야 한다. 해당 입력이 빠졌으면 `needs_data` 결과만 반환한다.

Registry 경로의 `RunContext` asset, location 및 time basis는 원 부식률 이력 요청과 일치해야 한다. 불일치는 ModelSpec context validator에서 거부된다.

## 연결되는 조건

호출자는 이벤트가 의미하는 두께 조건을 `condition_id`와 `condition_statement`로 명시하고 조건 종류를 `required_thickness_crossing_within_history_support`로 고른다. 이 선택은 요청에 이미 정의된 `required_thickness_m` 기준의 교차 조건이며, 어댑터는 다음의 자산, 위치, 물리 범위, 시간 기준, 유한 이력 구간과 기준두께를 확인한다.

- asset 및 location ID
- physical scope ID와 elapsed-time clock ID
- 이력 시작·종료 시각
- required thickness
- 입력 요청 digest와 부식 계산 결과 digest

부식 계산의 deterministic crossing은 관측값으로 결과에 그대로 기록한다. 이 값은 확률 입력을 보정하거나 대체하지 않는다. caller가 전달한 확률과 deterministic crossing이 다르게 보일 수 있으므로, 이벤트 정의와 불확실성 해석의 적합성은 FTA 담당자가 별도로 검토해야 한다.

## 확률과 근거

`CorrosionFaultTreeProbabilityInput`은 이벤트 ID, 고장모드, 조건 ID/문장, 확률, probability semantics, conditioning, 공통 FTA scope ID, 확률 Evidence, 권리 경계를 요구한다. 이 adapter의 조건은 finite history 기간 안의 요구두께 최초 통과이므로 probability semantics는 `conditional_first_failure_in_period`만 허용한다. 시점 상태확률, 공간 크기 초과, 검출확률, 범위 미지정 확률은 이 이벤트에 연결할 수 없다. probability는 [0, 1]의 caller 입력이며, 어떤 기본값도 없다. 각 Evidence의 citation, license token, source ID, digest는 JSON 결과와 typed binding에 보존한다.

`rights_boundary="local_only"`는 이 입력을 로컬 검토 범위에 한정한다. `caller_authorized_open_distribution`을 선택하려면 호출자가 관리하는 권한 근거 digest를 함께 제시해야 한다. 이 플래그나 digest는 권리의 법적 유효성을 판정하거나 라이선스 조건을 대신하지 않는다. 공개 권한이 확인되지 않으면 로컬 전용 경계를 사용한다.

## Python API

```python
from matintegrity.corrosion_fta_binding import (
    CorrosionFaultTreeProbabilityInput,
    bind_corrosion_history_probability_to_fta,
)
from matintegrity.contracts import Evidence

probability_input = CorrosionFaultTreeProbabilityInput(
    event_id="asset-17-wall-limit-crossing",
    failure_mode="caller-defined loss-of-required-thickness condition",
    condition_id="minimum-wall-limit-v1",
    condition_statement="Required thickness is crossed during the supplied elapsed-time support.",
    condition_basis="required_thickness_crossing_within_history_support",
    probability=0.08,  # independently supplied; never calculated from wall loss
    probability_meaning="conditional_first_failure_in_period",
    conditioning="Caller states the conditioning population and operating state here.",
    probability_scope_id="asset-17-scope-period-2026",
    probability_evidence=(Evidence(
        source_id="caller_probability_assessment",
        origin="user_declared",
        citation="Caller-maintained probability assessment identifier",
        license_id=None,
        sha256=None,
    ),),
    rights_boundary="local_only",
)

bound = bind_corrosion_history_probability_to_fta(
    request=corrosion_request,
    corrosion_result=corrosion_calculation,
    probability_input=probability_input,
)
if hasattr(bound, "basic_event"):
    fta_basic_event = bound.basic_event  # already a validated FaultTreeBasicEvent
    exchange_basis = bound.integrity_event_basis
    provenance_calculation = bound.calculation
else:
    # A Calculation with status needs_data or out_of_scope; do not add it to an FTA.
    provenance_calculation = bound
```

`bound.basic_event` is a validated `FaultTreeBasicEvent`, so it can be included in a `FaultTreeAssessment`. Its embedded `IntegrityEventBasis` has the same event ID, probability, semantics, conditioning and binding result digest as the basic event. Its `clock_id` and horizon match the corrosion history's elapsed-time basis and finite support. A basic event is still not sufficient to quantify an FTA: independence, common-cause treatment, cut sets and event scope remain separate caller review responsibilities.

## Digest and status behavior

The binding preserves the canonical corrosion request digest, complete `Calculation` digest, explicit event input digest, evidence records and a digest for the bound event result. `FaultTreeBasicEvent.evidence_digest` equals `IntegrityEventBasis.integrity_result_digest`, satisfying the existing FTA contract. The integrity result digest denotes this caller-probability/event binding with its upstream references; it is not a model-derived probability result.

- Missing/unfinished corrosion result: `needs_data`.
- Missing probability input: `needs_data`; no event payload is emitted.
- Model ID, request digest, asset/location/scope/time/threshold mismatch: `out_of_scope`.
- Valid inputs: typed `CorrosionFaultTreeEventBinding`, containing the FTA contracts and a `Calculation` lineage record.

This interface does not infer failure probability, conditioning, dependence, acceptance, remaining life, rights, or authorization. The caller-supplied probability must explicitly mean first crossing of the required thickness within the finite period; the deterministic thickness model is not declared to be a probabilistic model.

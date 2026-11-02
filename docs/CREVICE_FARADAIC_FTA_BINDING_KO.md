# Crevice/Faradaic 결과에서 FTA 기본 사건으로 연결

## 목적

`adapter.crevice_faradaic_to_fault_tree_basic_event`는 계산 완료된 Crevice/Faradaic 결과를 기존 `FaultTreeBasicEvent` 계약에 연결한다. adapter가 확률을 만들지는 않는다. 이벤트 확률과 의미, 조건부 기준, 확률 범위, 확률 Evidence를 호출자가 모두 제공해야 한다.

이 연결만으로 확률의 과학적 타당성, 사건 독립성, 공통 원인, FTA cut set의 적절성 또는 안전 적격성이 입증되지는 않는다. FTA 평가는 별도의 `FaultTreeAssessment` 입력에서 이루어진다.

## Fail-closed 조건

결과 `Calculation`의 모델 ID가 `integration.crevice_faradaic_spatial_chemistry_coupling`과 정확히 같아야 한다. `input_sha256`는 동봉한 원 요청의 canonical digest와 같아야 한다. 또한 결과의 assessment ID, committed interval 수, 모든 인접 구간 시각과 `committed` 상태가 요청의 exact clock knots에 일치해야 한다.

일치하지 않는 결과는 `out_of_scope`, 계산 상태가 `computed`가 아닌 결과는 `needs_data`로 반환하며 FTA 기본 사건을 만들지 않는다. 계산 Evidence는 `origin="model_prediction"`, source ID는 Crevice/Faradaic 모델 ID, SHA-256은 전체 source Calculation digest와 일치해야 한다.

Asset ID, location ID, physical scope ID, clock ID 및 사건 horizon은 입력으로 제공된 동일한 Crevice/Faradaic 요청에서 전달한다. 확률은 caller 값 그대로만 사용하며 Faradaic current, reaction extent, 또는 deterministic model outputs에서 추정하지 않는다.

## Python API

```python
from matintegrity.crevice_faradaic_fta_binding import (
    CreviceFaradaicFaultTreeBindingRequest,
    CreviceFaradaicFaultTreeProbabilityInput,
    bind_crevice_faradaic_probability_to_fta,
)
from matintegrity.contracts import Evidence

caller_reviewed_probability = ...  # analyst-owned value with its own evidence and scope
probability_input = CreviceFaradaicFaultTreeProbabilityInput(
    event_id="caller-event-id",
    failure_mode="caller-defined failure mode",
    condition_id="caller-condition-revision",
    condition_statement="Caller-defined event statement and threshold.",
    probability=caller_reviewed_probability,
    probability_meaning="conditional_first_failure_in_period",
    conditioning="Explicit conditioning statement supplied by the analyst.",
    probability_scope_id="caller-probability-scope",
    probability_evidence=(Evidence(
        source_id="caller-probability-source",
        origin="user_declared",
        citation="Caller-supplied probability basis and revision.",
        sha256="<64 lowercase hex digits>",
    ),),
    rights_boundary="local_only",
    rights_authorization_digest=None,
)

calculation_evidence = Evidence(
    source_id="integration.crevice_faradaic_spatial_chemistry_coupling",
    origin="model_prediction",
    citation="Exact upstream Calculation result digest and model revision.",
    sha256="<64 lowercase hex digits matching the whole Calculation digest>",
)

binding = bind_crevice_faradaic_probability_to_fta(
    CreviceFaradaicFaultTreeBindingRequest(
        integrity_request=crevice_request,
        integrity_result=crevice_result,
        calculation_evidence=calculation_evidence,
        probability_input=probability_input,
    )
)
```

실제 호출에서는 placeholder digest를 제공하지 말고, 검토된 probability record와 source Calculation에서 산출한 정확한 digest를 넣는다. 성공 결과에는 기존 `FaultTreeBasicEvent`, `IntegrityEventBasis`, source request/result digest와 binding digest가 포함된다. Registry의 `Calculation.values`에는 calculation 및 probability Evidence 전체와 rights boundary/authorization digest도 보존된다. 공개 배포가 승인된 경우에만 `rights_boundary="caller_authorized_open_distribution"`와 검토된 authorization digest를 제공한다.

## 경계 및 한계

- 본 adapter는 external risk toolkit이나 FTA 계산기의 연결이 아니다. 패키지 안의 기존 typed FTA 계약을 만드는 로컬 adapter다.
- 기본 사건을 tree에 삽입하거나 top-event probability를 계산하지 않는다.
- 동일한 probability meaning, conditioning, probability scope는 FTA 평가 전체에서 맞춰야 한다.
- 물리 scope 또는 clock이 다른 result를 임의로 변환하지 않는다.
- Adapter는 caller probability source와 계산 결과 Evidence를 digest로 묶지만 두 출처의 과학적 적합성이나 권리 상태를 판정하지 않는다.

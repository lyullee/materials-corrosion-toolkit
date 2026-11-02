# 다층 스케일 두께 이력의 절점별 확산 한계

## 목적

`chemistry.layered_scale_history_series_transport`는 각 수송층에 대해 별도 계산된 caller 제공 단일상 스케일 두께 이력을 연결하고, 모든 이력이 공유하는 정확한 시간 절점에서 기존 다층 확산 한계 계산을 다시 평가합니다.

## 입력 연결

- 기준 `LayeredScaleDiffusionLimit`은 각 확산층의 기하, 물성, 경계조건, 재료 및 용액 상태를 제공합니다.
- 각 층에는 서로 다른 `chemistry.caller_surface_scale_kinetics` AssessmentResult 하나를 `ScaleLayerHistoryBinding`으로 연결합니다.
- 결과·입력 digest, 물리 범위, 기질/용액 상태, 스케일 상 식별자 및 자산·위치·시간 기준을 확인합니다.
- 모든 상 이력은 동일한 엄격 증가 시간 절점을 제공해야 하며, 결과와 요청 사이의 층 순서/상 mapping을 명시적으로 검토합니다.

## 계산 의미

각 공유 절점에서 caller 이력의 스케일 두께를 해당 확산층에 대입하고, 기존의 층상 정상 확산 한계를 독립적으로 계산합니다. 이전 이력 절점 사이를 보간하지 않고, 절점별 결과만 순서대로 기록합니다. 첫 계산이 실패하면 이미 완료된 절점 접두부와 실패 결과를 보존합니다.

이 API는 절점 순간별 quasi-steady 확산 한계를 정리합니다. 시간의존 수송 방정식, 스케일 상의 생성·용해, 상 간 반응, 보간된 중간 상태, 부식률, 금속 손실, 잔여두께, 수용 기준 또는 고장확률을 계산하지 않습니다. 따라서 계산된 확산 한계를 실제 부식률이나 보호효과로 해석하지 않습니다.

## 필수 검토

- 층 순서와 각 상 history의 층 대응
- 공통 물리 범위 및 정확한 절점 정렬
- 절점별 독립 quasi-steady 해석의 적용성
- 입력 자료의 계산 이용 권한

검토가 빠지면 계산 없이 `needs_data`를 반환합니다.

## Python 사용 형태

```python
from matintegrity.scale_layer_stack_series_transport import (
    LayeredScaleHistorySeriesTransport,
    evaluate_layered_scale_history_series_transport,
)

request = LayeredScaleHistorySeriesTransport(
    transport_request=layered_diffusion_request,
    layer_bindings=(scale_phase_a_binding, scale_phase_b_binding),
    layer_history_order_and_phase_mapping_reviewed=True,
    common_scope_time_and_knot_alignment_reviewed=True,
    independent_quasi_steady_knot_interpretation_reviewed=True,
    computational_use_authorized=True,
)
result = evaluate_layered_scale_history_series_transport(request)
```

코드 예시의 변수는 호출자가 준비한 계약 객체를 뜻합니다. 서로 다른 절점 집합을 자동으로 맞추거나, 계수 및 적용성을 추정하지 않습니다.

# 보정된 wall-sink를 restricted transport 경계 callback으로 연결

## 목적

검토된 equilibrium surface concentration과 온도별 보정 wall-transfer velocity를 사용해 기존 restricted transport solver의 wall flux callback을 생성한다. 이 API가 계산하는 국소 경계 flux는 inward-positive 부호로 다음 식을 사용한다.

`J_in = k_w(T) * (C_surface - C_bulk)`

`C_bulk`는 solver가 매 callback 호출 때 전달하는 현재 종별/셀별 농도다. `C_surface`와 `k_w`는 caller가 제공한 정확한 동일 knot들을 가진다. 이에 따라 유체에서 벽으로 이동하는 sink는 음의 inward flux로 표현된다. 수송 solver가 geometry의 `wall_area_per_volume`를 곱해 체적항으로 반영하므로 callback은 벽면 flux 단위(`mol/(m2 s)`)만 반환한다.

이 경로는 wall-transfer parameter와 시변 geometry를 실제 restricted transport callback으로 구성하는 계산 기능이다. 수송 적분 자체는 기존 solver가 수행한다.

## API 및 입력

- 모듈: `matintegrity.crevice_calibrated_wall_flux_callback`
- 입력 계약: `CreviceCalibratedWallFluxRequest`
- callable 생성: `build_crevice_calibrated_wall_flux_callback(request)`
- 직렬화 가능한 구성 manifest: `evaluate_crevice_calibrated_wall_flux_callback(request)`
- ModelSpec 목록: `specifications()`
- 모델 ID: `integration.crevice_calibrated_wall_flux_callback`
- source ID: `caller_crevice_calibrated_wall_flux_boundary`

입력은 computed exact-knot calibrated wall-rate history 전체 결과와 SHA-256, geometry history 전체 결과와 SHA-256, 단일 species/condition/geometry ID, 각 knot 및 셀의 equilibrium wall concentration(`mol/m3`), Evidence, 다섯 review gate다. 온도 rate knots와 geometry knots의 시간 및 순서가 exact하게 일치해야 한다. geometry에서 셀 수, 각 knot의 `wall_area_per_volume_m2_m3` 크기와 양수 여부를 확인한다.

History에는 적어도 2개 knot와 2개 셀이 필요하다. 노출되는 호출 시간은 knot 구간 안에 있어야 하며 범위 밖은 예외로 거부한다. 요청에는 모든 적용 상태/부호/시간 재구성 review가 필요하다. callback은 `numpy.ndarray` 형태 `(1, cell_count)` 입력을 받고 같은 shape의 inward flux를 돌려준다.

## 실행에 연결

```python
provider = build_crevice_calibrated_wall_flux_callback(request)

# RestrictedTransportRequest에는 동일 identity/digest가 들어 있어야 한다.
restricted_request = restricted_request.model_copy(update={
    "wall_surface_provider_id": provider.provider_id,
    "wall_surface_configuration_sha256": provider.configuration_sha256,
    "wall_surface_flux_basis_reviewed": True,
})

# Direct transport call example
result = solve_restricted_transport(
    restricted_request,
    reaction=reaction_callback,
    wall_surface_flux=provider,
)
```

geometry campaign에 전달할 때는 기존 campaign이 callback의 global time mapping을 처리한다. 직접 `solve_restricted_transport`를 부르면 callback 시간은 wall-rate 및 geometry 결과와 동일한 elapsed-time origin을 사용해야 한다.

## 적용 경계

callback의 `C_surface`는 wall에서의 equilibrium 또는 effective boundary concentration이다. 별도 surface speciation solver는 포함되어 있지 않으므로 caller가 제공하고 evidence/review해야 한다. 모든 시간과 위치에서 동일한 scalar `k_w`를 사용하는 선형 Robin-like boundary law만 지원한다. 하나의 species만 처리한다.

구간 사이 `k_w`와 `C_surface`는 piecewise linear하게 보간하며 extrapolation하지 않는다. 시간 이력에 이 보간 가정을 적용하지 않으면 사용하지 않는다. `wall_area_per_volume`는 geometry 및 solver가 적용하므로 callback에서 별도로 곱하지 않아 이중 적용을 방지한다.

API는 다성분 경쟁반응, 전기화학 potential 효과, wall concentration을 도출하는 surface chemistry, turbulent/film resistance 분리, 재료 손실·부식률, transient geometry 자체, 자동 callback qualification 또는 위험성 확률을 추론하지 않는다. first-order parameter가 검토된 재료/유체/표면상태와 geometry에만 적용된다.

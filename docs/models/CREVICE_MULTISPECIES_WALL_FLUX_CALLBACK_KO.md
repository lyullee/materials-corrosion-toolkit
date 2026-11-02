# 크리비스 다성분 wall-transfer callback

## 목적과 범위

다성분 restricted transport가 요구하는 `(종, 셀)` flux 배열을 만들기 위해, 각 종에 대해 digest-pinned Arrhenius wall-transfer history와 caller 제공 평형 surface concentration 이력을 연결한다. 이 callback은 종별 선형 경계식

`J_i,in = k_i(T) * (C_surface,i - C_bulk,i)`

을 독립 적용하고 inward-positive molar flux를 반환한다. `C_bulk`는 수송 solver가 현재 상태로 넘긴다. geometry의 wall area/volume은 수송 solver에서 한 번 적용되므로 여기서 다시 곱하지 않는다.

이것은 여러 단일 종 transfer laws의 독립 벡터화다. 종 간 반응이나 site competition을 구현하지 않는다.

## API

- 모듈: `matintegrity.crevice_multispecies_wall_flux_callback`
- 입력: `CreviceMultispeciesWallFluxRequest`
- 계산 callback 생성: `build_crevice_multispecies_wall_flux_callback()`
- serializable manifest: `evaluate_crevice_multispecies_wall_flux_callback()`
- ModelSpec: `specifications()`
- 모델 ID: `integration.crevice_multispecies_wall_flux_callback`
- source ID: `caller_crevice_multispecies_calibrated_wall_flux_boundary`

요청은 ordered `transport_species_order` 목록과 그와 동일한 순서의 종별 rate-history 기록을 갖는다. 각 기록에는 종 ID, condition ID, 전체 computed rate history result + SHA-256, exact knot별/셀별 surface concentration, Evidence가 있다. geometry history와 SHA-256도 포함하고 rate/geometry history의 knot 개수·시각·geometry ID 및 각 surface 배열 셀 개수를 대조한다.

최대값은 종 100, 셀 2,000, knot 5,000이며 `종×knot×셀` surface profile 총량은 2,000,000 이하로 제한된다. 시간 이력은 0에서 시작해 증가해야 하며 모든 종과 geometry가 정확히 같은 knot grid를 사용한다. callback 요청 시각은 범위 안이어야 하고 밖으로 extrapolation하지 않는다.

## 수송 solver 연결

```python
wall_flux = build_crevice_multispecies_wall_flux_callback(request)

restricted_request = restricted_request.model_copy(update={
    "wall_surface_provider_id": wall_flux.provider_id,
    "wall_surface_configuration_sha256": wall_flux.configuration_sha256,
    "wall_surface_flux_basis_reviewed": True,
})

result = solve_restricted_transport(
    restricted_request,
    reaction=reaction_callback,
    wall_surface_flux=wall_flux,
)
```

Transport species order는 request의 정확한 tuple 순서와 같아야 한다. geometry campaign이 callback을 segment별로 감쌀 때 global time mapping을 적용한다. 단일 transport 요청과 직접 호출에서는 시간 기준점을 history와 맞춘다.

## 해석 제한

종별 속도·surface 상태는 knot 사이 선형 재구성만 사용한다. `C_surface`는 caller가 제공한 유효 wall-equilibrium 농도이며 이 API가 표면 평형을 풀거나 온도·전위로부터 계산하지 않는다. 각 종은 다른 종과 독립적인 1차 이동 law를 따른다고 review해야 한다.

이 callback은 surface reaction stoichiometry, multi-species competitive adsorption, 전기화학 charge transfer, pH/speciation feedback, precipitation, metal loss, corrosion rate 또는 qualification을 제공하지 않는다. 그런 효과가 중요한 계에는 독립 flux를 합성한 결과를 적용하지 말고 적합한 반응 모델을 사용해야 한다.

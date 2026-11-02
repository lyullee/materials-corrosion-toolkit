# Wet CO₂ 탄산염 경계 조성의 exact-knot 이력 전달

`integration.wet_co2_carbonate_transport_boundary_history`는 완전히 계산된 carbonate history의 각 지점을 caller가 제공하고 근거를 고정한 CO₂* hydration partition과 water concentration으로 transport boundary 기록에 옮깁니다. 지원 입력은 `chemistry.fixed_fugacity_carbonate_history`와 `integration.co2_henry_temperature_to_fixed_fugacity_carbonate_history` 결과입니다.

## 입력과 계보

`WetCo2CarbonateTransportBoundaryHistoryRequest`는 원본 `AssessmentResult`와 그 전체 JSON의 SHA-256, 점별 `CarbonateBoundaryPartitionUse`, 그리고 history/경계 선택 검토를 받습니다. 각 partition 입력은 기존 `CarbonateBoundarySelection`의 CO₂* 중 탄산으로 수화한 분율, 물 농도, partition-provider digest 및 검토 flag와 provider ID/revision, source record ID, digest 일치 `Evidence`를 보유합니다.

각 결과 지점은 원본 history의 `sample_results`와 동일한 순번·시간에 있어야 하며 계산 성공 상태여야 합니다. Henry history인 경우 중첩된 point result의 온도·용매 digest·보정 Henry record digest를 보존합니다. 원본 history 전체 digest와 각 point JSON digest가 모두 boundary row에 연결됩니다. partition provider digest는 Evidence SHA-256과 일치해야 합니다.

## 계산과 시간 경계

각 정확한 time knot에서 `CO2*` 농도를 mol/L에서 mol/m³로 환산하고 caller 분율 `f`에 따라 `CO2_aq = (1-f) CO2*`, `H2CO3 = f CO2*`로 나눕니다. caller의 물 농도와 원 carbonate result의 `H+`, `HCO3-`, `CO3--`, `OH-`도 mol/m³로 전달합니다. 이 mapping은 고정된 1000 L/m³ 단위 환산과 명시된 caller partition만 사용합니다.

History 시간이 엄격히 증가하고 경계 선택이 모두 검토되어야 합니다. 한 knot당 정확히 한 mapping을 수행하며 knot 사이 온도·용매·농도를 보간하거나 외삽하지 않습니다. 모든 지점이 유효할 때에만 전체 boundary history를 반환합니다. 한 지점이 유효하지 않으면 성공 prefix와 최초 실패 index/reason만 반환하고 history 전체를 완료로 표시하지 않습니다.

## 해석 한계

이 API는 이미 계산된 탄산염 부분계의 농도를 수송 경계 형식으로 옮길 뿐, 수송 PDE/ODE나 반응 네트워크를 풀지 않습니다. `CO2*` hydration fraction과 물 농도는 caller가 공급합니다. 나트륨/염화물 등 미제공 이온, 전기중성, 완전한 용액 조성, 활동도, 전극 반응, 부식률, scale 생성, 수명 및 acceptance는 추론하지 않습니다. 결과는 transport boundary 입력이며 자체로 적합성·안전성을 보증하지 않습니다.

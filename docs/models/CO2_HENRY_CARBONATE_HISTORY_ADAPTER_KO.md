# CO₂ Henry 보정에서 탄산염 평형 exact-knot history로 연결

`integration.co2_henry_temperature_to_fixed_fugacity_carbonate_history`는 시간 이력의 각 knot에 대해 `chemistry.co2_henry_vant_hoff_temperature_correction`의 계산 결과를 검증한 다음, 기존 carbonate-only fixed-fugacity 계산을 호출합니다. 단일 시점 연결은 [단일 carbonate adapter](CO2_HENRY_CARBONATE_ADAPTER_KO.md)를 반복 호출합니다.

## 점별 입력과 계보 검증

각 `Co2HenryCarbonateAdapterRequest`는 Henry 보정 요청과 계산된 `AssessmentResult`, 그리고 Henry 입력 없이 작성한 carbonate-equilibrium template을 묶습니다. 점마다 보정 결과의 model ID/status, 원 입력 JSON, AssessmentResult input digest, 보정 result digest, Henry 단위(`mol/L/Pa`), 농도/fugacity 관례, provider 설정과 revision, 기준 기록 digest, 목표 온도, 용매 조성 digest를 검사합니다. carbonate request의 온도는 정확한 보정 목표 온도와 일치하고 용매 digest도 같아야 합니다. 보정 AssessmentResult context의 asset/location/time basis도 history scope와 일치해야 합니다.

온도 또는 용매 조성이 knot마다 달라질 수 있지만 각각 그 knot의 caller-provided correction request와 증거를 사용합니다. 모델은 서로 다른 점을 보간하거나 한 점의 값을 다른 점으로 전이하지 않습니다. Sample·assessment ID는 history 안에서 유일해야 합니다.

## 시간 처리와 실패 규칙

Caller가 엄격히 증가하는 `time_s`와 같은 길이의 점별 request를 전달합니다. clock/sample 정렬 검토를 명시해야 하며, 실행은 선언된 순서의 각 knot에서 정확히 한 번의 bounded carbonate evaluation을 수행합니다. 시간 구간의 중간값, 온도, 조성 또는 Henry 계수는 계산하지 않습니다.

모든 점이 성공했을 때만 aggregate history를 반환합니다. 첫 번째 비계산 결과가 나오면 해당 지점과 앞선 성공 prefix까지만 반환하고 이후 점은 평가하지 않습니다. 이때 history-level status는 실패한 지점의 상태를 그대로 따릅니다.

## 계산 범위와 제한

기존 fixed-fugacity 모델은 gas fugacity와 보정된 Henry 계수로 CO₂*를 정하고, carbonate equilibrium constants 및 total alkalinity로 `CO₂*`, `HCO₃⁻`, `CO₃²⁻`, `H⁺`, `OH⁻`의 탄산염 부분계를 계산합니다. **전체 용액 조성이나 전 이온의 charge-balanced speciation은 계산하지 않습니다.** 수소/염류/다른 산-염기 종, 일반 반응망, 기상 재고, 부식률, scale, 재료 응답 및 수명은 추론하지 않습니다.

이 어댑터는 caller가 제공한 Henry/열역학 기록을 소비합니다. 자료·매개변수를 넣거나 외삽하지 않으며, 계산 성공은 실험 검증이나 물리 qualification을 뜻하지 않습니다.

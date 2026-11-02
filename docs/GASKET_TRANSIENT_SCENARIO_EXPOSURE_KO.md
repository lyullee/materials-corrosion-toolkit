# GASK correlated-scenario transient exposure interval

`integration.gasket_leakage_scenario_rate_interval` integrates caller-matched scenario-specific molar leak rates over one interval bounded by two computed `fabrication.gasket_correlated_scenario_envelope` results.

## Inputs and gating

Pass complete start/end `AssessmentResult` records and their canonical result SHA-256 values. Each endpoint must have a valid model input/context digest and a valid scenario-row digest. The pair must agree on asset, joint, physical scope, scenario provider/revision, calibration provider/revision/record/map, license, and ordered node identity. Both endpoint scenario ID sets and per-scenario calibration-flux realization digests must match. The caller explicitly reviews scenario identity continuity, the time basis/window, the rate reconstruction, and computational use.

Endpoint snapshots must have finite strictly increasing time coordinates. Each scenario row must have a nonnegative finite molar leak rate and ordered node responses. Endpoint scenario results may be listed in different orders; matching uses their explicit scenario IDs.

## Calculation meaning

For each scenario separately, the API applies piecewise-linear reconstruction to the total molar leak rate between the two endpoint rates and integrates it exactly with a trapezoid:

`amount = (rate_start + rate_end) × (time_end - time_start) / 2`

The output retains both complete result digests, both result input digests, both scenario-row-set digests, individual endpoint scenario-row digests, the amount for each scenario and the finite-set minimum/maximum witness IDs.

## Limits

- Scenario continuity and appropriateness of the endpoint pairing are caller responsibilities; explicit review is required.
- Only the sampled endpoint rates are integrated. The API does not recover the evolution of pressure, contact pressure, gasket force, relaxation, leakage path, area or calibration response between endpoints.
- The trapezoid is exact only for the declared linear-in-time total-rate reconstruction. No interpolation of node state is performed.
- Reported extrema are over the finite matched scenario set. They are not probabilities, confidence bounds or extrema over unsampled transient states.
- No FTA probability, seal acceptance or consequence is inferred.

No tests, independent validation or HPC calculation were run for this interface.

선택적 기술 통계 기준값은 descriptive_rate_threshold_mol_s와 descriptive_threshold_basis를 함께 입력한다. 입력하지 않으면 기존 누설량 적분만 반환한다. 기준값을 입력하면 각 시나리오의 선형 누설률 경로에서 q(t)>기준값인 시간과 max(q(t)-기준값,0)의 시간 적분을 폐형식으로 계산한다. 각각 strictly_above_threshold_duration_s와 integrated_positive_rate_excess_mol이다. above_threshold_interval_start_s/end_s는 초과 구간의 경계 시각이며 교차점 자체가 strict 초과 집합에 포함된다는 의미는 아니다. 초과 구간이 없으면 두 경계는 null이다. 기준값과 같은 평탄 경로의 초과 시간은 0이다. 이 값은 규격 허용치, 안전 판정, 실패확률 또는 선형 재구성 밖의 transient 상한이 아니다. 기존 시나리오·교정·시간 경계와 입력 해시를 그대로 보존한다.

수치 지원범위: 개별 endpoint 시각이 유한해도 시간 차가 overflow이면 입력을 거부한다. 평균률은 q0/2+q1/2로 계산하여 중간 q0+q1 overflow를 줄인다. 실제 누설량 적분이 유한 범위를 넘으면 out_of_scope이며 완료 결과로 간주하지 않는다. Underflow나 반올림 오차에 대한 고정밀 보증은 제공하지 않는다.

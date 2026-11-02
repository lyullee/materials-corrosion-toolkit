# Wet-CO₂ spatial model의 고정점 trial 결과

`wet_co2_cylindrical_spatial_mixed_potential` 요청에 `geometry_trial_mode=True`를 지정하면, 한 번의 caller 반경 경로 계산에서 aqueous species·charge·nonalloy-element 수지를 계속 엄격히 검사하면서 wall element 방출량과 그에 대응하는 target bore radius를 반환한다. 이 옵션은 아직 형상 고정점이 닫히지 않은 iteration 안에서만 쓰며, 명시적인 `trial_geometry_closure_exemption_reviewed=True` 검토와 `fixed_point_input_sha256`가 필요하다. 기본값은 꺼져 있어 기존 strict geometry closure 동작을 유지한다.

## trial 출력 계약

결과 `values`에는 아래 값이 있다.

- `model_id`: 기존 `integration.wet_co2_cylindrical_spatial_mixed_potential`
- `fixed_point_input_sha256`: 상위 controller가 넘긴 현재 반경 벡터·solver revision·asset/location/time grid의 호출 digest
- `time_s`: 계산된 exact-knot 시각
- `input_bore_radius_m_by_knot`: geometry evaluator가 실제 계산에 사용한 입력 bore 반경
- `target_bore_radius_m_by_knot`: 적분된 wall-element release에서 재구성한 일관 후보 bore 반경
- `wall_element_balance_residual_mol_m_by_element`: 각 element별 각 knot의 `initial wall inventory - trial geometry wall inventory - cumulative released element inventory`
- `wall_element_inventory_scale_mol_m`: 각 element별 초기 벽 원소 재고를 반복 controller 상대 허용오차에 사용할 scale 배열로 제공
- `trial_result_only`: trial 계산인지 식별하는 표식

후보 반경은 각 knot에서 caller alloy 조성의 원소별 누적 몰수 방출을 원소 몰질량과 곱해 누적 방출 질량으로 만든 뒤, 고정 외경·밀도와 caller scale phase 부피를 사용해 계산한다.

```text
steel_inner_radius_target^2 = initial_steel_inner_radius^2
                              + released_alloy_mass_per_length / (pi * density)
target_bore_radius^2 = steel_inner_radius_target^2 - scale_volume_per_length / pi
```

trial mode에서도 각 반응 branch의 BV 지원범위, 혼합전위 bracket, 반응 방향, nonnegative 유한 농도, species inventory, aqueous charge, aqueous element, signed wall release 및 실현 가능한 target geometry 검사는 유지된다. 건너뛰는 검사는 오직 trial geometry와 계산된 cumulative wall release 간의 일치 gate다. 그 잔차는 폐기하지 않고 위 배열과 history에 전부 남겨 최종 고정점 controller가 별도 tolerance로 판정할 수 있다.

## callback 연결

`wet_co2_geometry_fixed_point.py`의 `candidate_solver`는 현재 반경 벡터에 맞춰 새 geometry history를 만든 뒤 trial 모드 spatial request를 구성하고, controller가 전달한 `fixed_point_input_sha256`를 request에 넣어 평가해야 한다. 결과가 `computed`여도 이는 **trial 성공**일 뿐이며 수렴한 corrosion geometry를 뜻하지 않는다. 상위 controller가 반경 고정점 residual과 각 element의 전체 시간 재고 residual을 모두 통과시켜야 한다. 제한된 반복 횟수 안에 닫히지 않으면 미수렴 진단 결과만 남긴다.

Trial mode는 일반 사용자 최종 계산 설정으로 쓰면 안 된다. 실제 chemistry/transport/electrode coupling, 사용 데이터·계수의 적합성, temporal support, 계측 근거 및 독립 검증은 별도 책임이다. Scale phase history는 현재 요청에서 caller가 고정 제공하며, scale 생성·용해 법칙의 반복 결합은 이 trial adapter에 포함되지 않는다. 동일한 BV 반응계가 새 geometry에서 다시 계산된다는 caller solver contract가 반드시 성립해야 한다.

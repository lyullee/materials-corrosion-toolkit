# 두께 프로파일 부식 시나리오와 압력차 용량

`structural.profile_capacity_corrosion_scenario`는 검토된 축방향 잔여두께 프로파일에서 출발해 호출자가 지정한 균일 부식률과 고정 예측기간을 적용한 뒤, 동일한 참조 압력·벌징 계수 provider로 국부 프로파일 용량을 다시 계산한다.

## 입력과 결과

`examples/model_inputs.json`의 `structural.profile_capacity_corrosion_scenario` 항목은 전체 입력 예다. `profile`에는 `structural.profile_capacity`와 동일한 geometry, 재료상태, 측정 위치·두께, reference capacity, bulging table 및 적용성 확인이 필요하다. `uniform_loss_rate_m_s`와 `forecast_horizon_s`는 각각 m/s, s이며 손실량은 둘의 곱이다. 결과는 기준/예측 압력차 용량, 변화량, 기준 용량 대비 손실률, 예측 최소두께와 예측 지배 window를 제공한다.

모델은 모든 노드에서 동일한 두께 손실을 빼는 결정론적 시나리오다. 위치별 속도장 추정, 부식률 보정, 불확실성, 부식 pit 성장, acceptance, 잔여수명, 안전계수 또는 파손확률을 계산하지 않는다. 0 ligament 도달, 기준 profile 부적합 또는 provider 범위 이탈 시 예측 용량을 만들지 않고 상태를 전달한다. 입력 rate, 기간과 공간 균일성은 사용자가 정하고 근거를 관리해야 한다.

이 API의 수식/코드 검증은 batch53 `tests/test_local_capacity_corrosion_scenario.py`에서 실행하도록 HPC manifest에 등록했다. 이 환경에서는 테스트를 실행하지 않았다. 합성 예제는 입력·API 연동용이며 실험 검증이나 설비 적용 자격을 의미하지 않는다.

## 축방향·시간 변화율 입력

`structural.profile_capacity_rate_field_scenario`는 각 `profile.axial_position_m` 노드에 대응하는 속도 행렬을 받는다. `time_s`는 0초부터 strictly increasing이어야 하며, 행렬의 각 행은 시간 knot마다 한 부식률(m/s)을 둔다. `forecast_horizon_s`는 마지막 제공 시각 이하여야 한다. 구간 내 속도는 선형으로 연결하고 예측기간 끝점에서 필요하면 끝점 속도를 보간한 뒤 사다리꼴 적분한다. 노드별 누적 손실을 기존 잔여두께에서 빼고, 기존 profile capacity evaluator에 전달한다. 노드간 속도장을 만들거나 속도 이력을 외삽하지 않는다.

이 방법은 입력 격자의 결정론적 적분기다. 격자 보간 가정·측정 오차·속도 추정·공간 연속성은 별도 책임이다. 입력 예제는 `examples/model_inputs.json`의 `structural.profile_capacity_rate_field_scenario`에 있고, 계산 회귀는 batch54에 추가했다.

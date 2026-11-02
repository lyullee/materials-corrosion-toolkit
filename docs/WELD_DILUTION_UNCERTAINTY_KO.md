# 용접 희석 조성의 provenance 및 불확실성 전파

`welding.dilution_with_uncertainty`는 caller가 식별한 base metal, filler 및 이전 layer의 용융 질량과 원소 질량분율로 단순 완전혼합 조성을 계산한다. 각 조성 레코드는 source ID와 SHA-256 digest를 함께 보존한다. 각 constituent의 총 조성표는 1 이하일 수 있으며 requested element 부분집합만 계산한다.

## 질량 혼합

constituent `i`의 용융 질량을 `m_i`, requested element `e`의 질량분율을 `c_(i,e)`라 하면 혼합 조성은

`c_mix,e = sum_i (m_i / sum_j m_j) * c_(i,e)`

이다. 질량은 정확한 caller 입력으로 취급한다. 각 원소 입력이 하나라도 누락되면 해당 혼합 조성을 `null`로 반환하고 계산 상태를 `needs_data`로 둔다. 누락값을 0 또는 검출한계로 치환하지 않는다.

## 공분산 전파

선택적으로 모든 constituent의 모든 requested element를 flatten한 joint covariance `C`를 입력한다. 변수 순서는 `covariance_variable_order`에서 constituent 입력 순서, requested element 순서의 중첩 순으로 정확히 선언해야 한다. 출력 element 벡터의 Jacobian `J`는 각 constituent-element 위치에 해당 용융 질량가중치를 배치하며, 계산은 `C_mix = J C J^T`로 선형 전파한다. 결과에는 mass-fraction squared 단위의 공분산과 caller coverage factor에 따른 주변 expanded uncertainty를 함께 둔다. PSD 및 대칭 조건을 확인한다. 변수 순서와 공분산 정의·단위는 caller가 검토해야 한다.

불확실성 계산은 full joint covariance를 직접 받으므로 constituent별 독립성을 자동 가정하지 않는다. 공분산이 없으면 중심 혼합 조성만 계산하고 uncertainty는 반환하지 않는다. 용융 질량 불확실성은 포함하지 않는다.

## 적용 경계

계산은 지정된 용융 질량 비율로 완전히 혼합된 조성의 선형 질량수지다. 원소 burnoff/transfer loss, segregation, solidification phase partition, layer별 국부 조성, dilution measurement 자체의 보정, weldability, hot cracking, 부식 저항, 코드 허용치 또는 합격 판정은 만들지 않는다. 적용 입력은 `examples/model_inputs.json`의 `welding.dilution_with_uncertainty` synthetic example이다.

# 다축 편차응력 경로 변동량

## 목적

`fatigue.multiaxial_deviatoric_stress_path_variation`은 사용자가 제공한 닫힌 다축 응력 텐서 표본을 순서대로 따라가며 편차응력 및 정수압응력의 총 변동량을 계산한다. 이 값은 경로의 기하학적 크기를 요약하여 다른 분석에 전달하기 위한 기술량이다. 피로 손상식이나 수명식으로 해석하지 않는다.

기존 응력 불변량 요약이 표본 전체의 최대 이격거리를 계산하는 것과 달리, 이 계산은 인접 표본 사이의 변화를 누적한다. 따라서 샘플 순서와 표본 밀도를 보존하며, 같은 물리 이력이라도 표본화가 다르면 값이 달라질 수 있다.

## 입력

- `SampledStressInvariantHistory`와 nested history의 canonical SHA-256 digest
- 정확한 표본 순서 및 응력 텐서 기저를 검토했다는 확인
- 표본 사이 이력을 추정하지 않고 원래 표본 프로토콜 범위에서만 결과를 쓴다는 확인
- 최대 선분 계산 개수 `maximum_increment_evaluations`

응력 텐서 성분 순서는 `[xx, yy, zz, xy, yz, zx]`이며 단위는 Pa다. history contract의 첫/마지막 응력은 정확히 같아 닫힌 주기여야 한다. 재료 조건, 위치, 원천 자료 ID와 SHA-256은 입력 history에 보존된다.

## 계산 정의

각 표본의 편차응력은 `s = σ - tr(σ)/3 I`, 정수압 응력은 `p = tr(σ)/3`로 둔다. 인접 표본 `i`, `i+1` 간 편차 증분은

`Δq_i = sqrt( 1/2 (Δs_xx² + Δs_yy² + Δs_zz²) + Δs_xy² + Δs_yz² + Δs_zx² )`

로 계산한다. 이는 `sqrt(J2)` 텐서 거리이며 대칭 전단 성분의 중복을 반영한다. 전체 편차 경로 변동량은 `Σ Δq_i`, 정수압 변동량은 `Σ |p_(i+1) - p_i|`다. 별도로 각 항목의 최대 단일 선분 증분과 선분별 값을 남긴다.

## 상태 및 한계

- `computed`: 리뷰된 입력에 대해 모든 인접 표본 증분을 계산했다.
- `needs_data`: 닫힌 주기, 기저 또는 표본 범위 검토가 누락됐다.
- `out_of_scope`: 선분 예산 초과 또는 비유한 산술 결과가 발생했다.

선분 계산은 주어진 이웃 표본만 잇는 수치적 표현이다. 별도 입력된 시각이 없으므로 속도나 빈도는 계산하지 않는다. 표본 사이 극값, 순환 주기 분할, rainflow, 피로 법칙 적용, 수명, 확률, 코드 합격 및 재료 적격을 추정하지 않는다. 서로 다른 좌표계·단위·표본 프로토콜의 결과는 검토된 조화 없이 직접 비교하지 않는다.

## 식별자 및 연결

- Model ID: `fatigue.multiaxial_deviatoric_stress_path_variation`
- 입력 계약: `MultiaxialDeviatoricStressPathVariation`
- 계산 함수: `evaluate_multiaxial_deviatoric_stress_path_variation(request)`
- 계산 정의 source ID: `caller_finite_tensor_stress_path_variation`

이 값은 downstream fatigue law에 연결할 수 있는 geometry descriptor다. downstream 모델은 별도 material calibration 및 applicability review를 요구해야 한다. Registry, catalog, schema, API index, source derivation 및 scope audit 연결은 중앙 통합에서 수행한다.

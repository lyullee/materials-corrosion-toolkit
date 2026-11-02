# 다축 피로 수명 유한 시나리오 가중 모멘트

`fatigue.multiaxial_weighted_life_scenario_moments`는 기존 `fatigue.multiaxial_life_scenario_envelope`와 같이 완전히 계산된 다축 수명 scenario들을 입력받아 caller가 명시한 순서 가중치로 기술통계를 계산한다. 각 입력 scenario에는 개별 계산 결과, 재료·보정 계보, asset/location/time basis 및 결과 digest가 이미 고정되어 있어야 한다.

## 입력·계보 조건

- `scenario_weights[i]`는 `scenario_envelope.scenarios[i]`에 대응하는 엄격한 양수다. scenario ID를 재정렬하거나 상관 scenario를 요소별로 조합하지 않는다.
- 가중치 벡터의 canonical SHA-256은 `weight_record_sha256`에 제공하고, 같은 provider ID와 digest를 가진 `weight_evidence`를 연결한다. 가중치 사용권 Evidence와 `usage_license_id`도 별도 제공한다.
- 가중치는 자동 정규화하지 않는다. 입력 합계가 1과 절대 오차 `1e-12` 이내가 아니면 계약 검증이 거부한다.
- weight/scenario 정렬, 가중치 의미, 권리, 계산 승인을 검토해야 계산한다. 기존 envelope에도 scenario dependence, coverage, result lineage 및 rights 검토가 필요하다.
- `weight_semantics`는 `empirical_frequency`, `quadrature_weight`, `user_declared_weight` 중 하나로 원래 의미를 기록한다. 이름만으로 실증적 대표성이나 확률 의미를 승인하지 않는다.

## 선택형 가중 분위수와 수명 기준 요약

`weighted_quantile_levels`에는 0과 1 사이의 고유한 q를 넣을 수 있다. `weighted_distribution_summaries_reviewed=true` 검토가 필요하며, 출력은 수명을 오름차순으로 정렬한 뒤 누적 가중치가 q 이상이 되는 첫 scenario를 고르는 left-continuous weighted inverse ECDF다.  동일 수명은 scenario ID 순으로 안정 정렬한다. 정렬 후 가중치 및 가중수명 prefix를 한 번 계산해 분위수·lower-tail 질의는 이진 탐색으로 처리하며 threshold output은 개수와 가중 몫을 제공한다. 개별 ID는 공통 `scenario_lives` 목록과 그 digest에서 확인한다.

`lower_tail_mass_levels`에는 0보다 크고 1 이하인 weighted mass fraction을 지정할 수 있다. `weighted_distribution_summaries_reviewed=true`가 필요하며, 가장 짧은 수명부터 해당 질량이 찰 때까지의 가중 수명 평균을 계산한다. 경계 시나리오의 필요한 가중치 일부만 포함해 지정 질량을 맞춘다. 출력은 이 유한 가중 시나리오의 lower-tail 평균이며 probability·confidence·연속분포의 CVaR 자격을 뜻하지 않는다.

`cycle_life_thresholds`는 caller가 검토한 수명 경계다. `cycle_life_threshold_definitions_reviewed=true`를 요구하며, 각 경계 이하의 시나리오 가중치 합과 해당 ID를 보고한다. 이 값은 선언된 finite manifest에서 경계 이하인 시나리오의 가중 몫이며 failure probability, 생존확률, 안전도 또는 신뢰구간이 아니다.

## 계산과 해석 한계

scenario별 수명을 `Nᵢ`, 명시 가중치를 `wᵢ`라 하면 출력 평균은 `Σ wᵢNᵢ`, 모집단 분산은 `Σ wᵢ(Nᵢ−μ)²`, 표준편차는 그 제곱근이다. Bessel 보정은 적용하지 않는다. 최솟값과 최댓값에는 실제 scenario witness를 함께 기록한다.

출력은 제공된 유한 scenario 집합의 가중 기술통계다. `empirical_frequency`를 포함해 어떤 가중치 의미도 사건확률·생존확률·신뢰구간으로 자동 변환하지 않는다. scenario 집합 밖의 연속 범위, 수명 분포 꼬리, 모델 보정 이전성, code acceptance 또는 재료 qualification을 보증하지 않는다. 이 API는 기존 scenario envelope와 별도 ModelSpec으로 등록된다.

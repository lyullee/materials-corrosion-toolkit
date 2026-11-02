# Itoh 비비례 변형률 기반 caller 수명 곡선 연결

`fatigue.itoh_nonproportional_strain_life`는 `fatigue.itoh_nonproportional_strain_parameter` 계산을 같은 재료 조건의 caller strain-range/life 곡선에 연결한다. 신규 피로법칙을 추정하지 않고, 이미 검토·교정된 데이터를 명시적 정의로 적용하는 인터페이스다.

## 입력 계약

- 중첩 `parameter_request`가 strain tensor 이력, 시계, α 교정, 주기 폐합과 Evidence/digest를 모두 보존한다.
- `curve_material_condition_id`는 nested parameter의 `material_condition_id`와 정확히 같아야 한다.
- `curve_strain_definition_id`는 `itoh_1995_adjusted_nonproportional_principal_strain_range.v1`로 고정한다. 다른 정의·scale·범위로 만들어진 곡선은 이 API에서 사용할 수 없다.
- curve provider ID/SHA-256/Evidence, 명시 license/use-basis ID와 curve-condition descriptor SHA-256으로 자료와 조건표현을 고정한다. strain-range와 cycle-to-failure 배열도 정규화 digest에 포함한다.
- curve는 양의 값만 허용하며 strain range가 strict 증가, cycles to failure가 strict 감소해야 한다. 재료조건·시험 기초, 원자료 사용 권리, log-log 해석을 caller가 확인해야 한다.

## 계산 및 범위

실제 Itoh 파라미터는 하위 계산기로 재계산한 뒤, 같은 material condition과 strain definition의 curve 안에서만 조회한다. 정확한 보정점이면 그대로 반환하고, 중간점은 `log(strain range)` 대 `log(cycles)`의 선형 보간을 사용한다. 입력값이 곡선 support 밖이면 `out_of_scope`로 반환한다. 곡선의 끝점 밖 외삽, 다른 재료·열처리·환경으로의 이전, scatter/불확도 추정은 하지 않는다.

출력 life는 사용자가 준 curve와 상수 진폭 parameter가 주어졌다는 조건의 cycle-count 값이다. 주기를 분해하거나 variable-amplitude damage를 합산하지 않는다. 결과는 설계 허용, 수명 인증, acceptance 또는 failure probability가 아니다.

## 근거

방법 배경은 Itoh, Sakane, Ohnami, Socie의 비비례 저주기 피로 기준을 따른다: [원 논문 DOI](https://doi.org/10.1115/1.2804541). 변형률 정의의 공개 설명은 [저자 연구의 multiaxial fatigue paper](https://doi.org/10.1299/jmmp.5.230)를 참조한다. 프로젝트는 독립 작성 코드와 caller 소유 자료만 사용하며 논문 표·실험값·문장을 포함하지 않는다.

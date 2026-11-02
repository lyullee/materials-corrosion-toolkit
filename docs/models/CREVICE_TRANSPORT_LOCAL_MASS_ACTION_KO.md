# 간극 수송장 기반 셀별 aqueous mass-action 연결

`integration.crevice_transport_to_local_mass_action`는 digest-pinned 고정형상 수송 결과의 exact output knot와 셀 농도장을, caller가 제공한 셀별 `AqueousMassActionSystem`의 명시적 선형 제약 목표에 연결하고 각 액상 평형 시스템을 독립적으로 푼다.

## 입력과 계산

- 현재 지원 upstream은 중성종 반응-확산 또는 희석 전해질 electroneutral transport의 완료된 `AssessmentResult`이다. 원본 input digest와 전체 result SHA-256을 재확인한다.
- transport species 하나를 mass-action constraint 하나에 연결하는 caller 매핑을 요구한다. 수송 결과 농도는 mol/m³, aqueous constraint target은 mol/L이므로 `target = concentration × caller scale / 1000` 변환을 사용한다.
- 각 시간 knot와 셀마다 caller가 전체 aqueous species, 반응, 활동도 계수, 평형상수, 온도, Evidence가 포함된 시스템을 지정한다. 이 시스템의 constraint target만 재구성하고 나머지 화학 설정은 유지한다.
- 셀별 activity와 concentration 및 Evidence에 연결한 caller 셀부피를 사용해 종별 액상 몰 재고를 반환한다. 계산은 최초 실패 지점에서 멈추고 완료된 prefix와 실패 정보를 보존한다.

## 해석 경계

- 수송성분 ID가 전체 성분·분석농도·부족 성분과 어떤 관계인지, 각 `constraint_id`의 총량 의미, 단위 scale, 셀 순서와 부피는 caller가 검토하고 Evidence에 연결한다. 자동 화학 mapping은 수행하지 않는다.
- 각 셀/시간에 독립적으로 caller 네트워크를 계산한다. 수송으로부터 평형상태를 피드백하지 않으며 반응-확산 동시해석, 활동도 모델 자동 선택, 상 선택, 침전, 벽 반응, 재료 손실 및 자격 판정을 하지 않는다.
- aqueous solver가 반환한 단일 액상 mass-action 결과를 집계한다. 숫자적 계산 성공은 열역학/공정 적용성 검증을 뜻하지 않는다.

## 후속 중앙 연결

공개 API로 사용하려면 Registry 등록, input schema export, source rationale와 implementation scope path 등록, API/model reference 및 generated package catalog 동기화가 필요하다. 계산 및 물리 검증은 별도 배치로 수행한다.

# 사용자 기준에 따른 손상기구 선별

`degradation.damage_mechanism_screening`은 여러 손상기구에 대해 호출자가 제공한 사실과 규칙을 비교한다. 내장된 재료·환경별 감수성 표나 자동 진단기는 아니다. 입력은 `DamageMechanismScreening`, 사실은 `DamageMechanismFact`, 기구별 기준은 `DamageMechanismProfile`이다.

사실의 영역은 재료·환경·응력·형상·유동·열이력·검사·공정 중 하나다. 값은 숫자·정확한 문자열·불리언이며, 알려짐·미상·무효 상태를 구분한다. 원자료 기록 ID·출처 그룹·해시와 근거를 보존한다. 수치 조건은 단위 토큰이 정확히 같아야 하며 단위·농도 기준·전위 기준·흐름의 부호를 자동 변환하지 않는다.

각 프로필은 기구 ID·정의, 제공자·개정, 필수 사실 ID 목록, 규칙, 미상 정책과 권한·규칙 완전성 검토를 제공한다. 조건은 기존 `SCCRuleCondition`, 규칙은 `SCCScreeningRule`의 비교 형식을 재사용한다. 조건 안에서는 AND, 규칙 사이에서는 OR로 결합한다. 실제 감수성·온도·유속 등의 기준은 호출자가 적용 근거와 사용 권한을 확인해 제공해야 한다.

프로필 전체의 기본값을 정규화한 SHA-256은 `profile_sha256`에 넣고, 같은 해시와 라이선스 식별자가 있는 근거를 제공한다. 입력 전체는 상속된 `basis`에 다시 결합된다. 사실·프로필·기구 ID는 요청 안에서 유일해야 한다. 입력 자산·위치는 실행 문맥과 같아야 하며 물리 범위·재료 상태는 별도로 명시한다.

필수 사실의 누락·미상·단위/값 종류 불일치가 있으면 해당 기구는 `needs_data`다. `unknown_policy=indeterminate`이면 판정도 미정으로 남긴다. `screen_in`이면 보수적으로 `potentially_applicable`에 포함하지만 데이터 부족 상태는 유지한다. 같은 규칙의 다른 조건이 거짓이어도 미상을 숨겨 `not_indicated`로 만들지 않는다. 무효 기록이나 검토 누락은 정책과 관계없이 미정이다.

필수 사실과 검토가 모두 갖춰진 경우 규칙이 하나라도 성립하면 `potentially_applicable`, 그렇지 않으면 `not_indicated`다. 후자는 선택한 사용자 규칙에 대한 결과이며 손상 부재나 안전의 증거가 아니다. 선택하지 않은 기구는 평가하지 않는다. 한 기구가 미정이어도 다른 기구 결과를 버리지 않고 각각의 상태를 유지하며, 전체 상태는 `needs_data`다.

`maximum_condition_evaluations`로 전체 조건 수를 제한한다. 식 문자열을 실행하거나 규칙을 자동 수집하지 않는다. 출력 `mechanism_findings`는 위험성 평가의 근거 자료로 전달할 수 있지만 고장확률·고장률·수명·FTA 기본사건 확률로 자동 변환하면 안 된다. 해당 전환에는 별도의 적용 모델과 관측·보정·검증이 필요하다.

검증: `tests/test_damage_mechanism_screening.py`와 기존 SCC 회귀, 합계 17개 사례. 기록은 `artifacts/validation/damage_mechanism_screening_contract.xml`이다. 선별 조건·미상·단위·다중 기구·근거 해시·계산 예산·Python/JSON 교환을 확인하며 실제 손상기구의 과학적 식별 성능은 검증하지 않는다.

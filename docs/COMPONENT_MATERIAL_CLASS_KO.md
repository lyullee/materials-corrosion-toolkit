# 부품 재료 클래스 비교 API

`materials.component_material_class_assessment`는 사용자가 작성한 재료 프로필을 실제 부품 기록과 비교한다. 펌프·밸브를 포함한 조립체의 부품 역할, 허용 재료 상태 식별자, 제품 형태·열처리·판본 등의 속성, 역할별 최소·최대 개수를 명시할 수 있다. 규격 표나 재료 선정 기준은 제공하지 않는다.

입력 계약은 `ComponentMaterialClassAssessment`, 역할 규칙은 `ComponentMaterialRequirement`, 관측 기록은 `MaterialClassComponentRecord`이다. 부품마다 원자료 식별자와 SHA-256을 보존한다. 모든 부품의 물리 범위는 조립체 범위와 같아야 하며 실행 문맥의 자산·위치도 입력과 일치해야 한다. 전체 입력은 상속된 `basis`의 정규화 해시와 사용 권한·적용성 검토에 결합된다.

재료와 속성은 정확한 문자열로 비교한다. 주조·단조·용접 제품, 열처리 상태, 과거·현행 판본을 자동으로 동등하게 취급하지 않는다. 명시적 동등성 처리가 필요하면 호출자가 검토한 별도 식별자 매핑을 먼저 적용해야 한다.

누락된 재료·필수 속성·역할 규칙과 최소 개수 부족은 `needs_data`이다. 명시된 다른 재료·속성 또는 최대 개수 초과는 `not_satisfied`이다. 누락과 불일치가 함께 있으면 계산 상태는 `needs_data`, 알려진 프로필 결과는 `not_satisfied`로 각각 유지한다. 최소 개수 0은 선택 역할을 표현한다. 알려지지 않은 추가 역할은 자동 통과하지 않는다.

허용 서비스 밖의 요청은 `out_of_scope`, 프로필 권한·부품 대응 검토가 없는 요청은 `needs_data`이다. 프로필 일치는 압력 용량, 내식성, 갤링, 누설, 회전체 간극, 인증 또는 생산 수락을 뜻하지 않는다. 경도 차 계산과도 별도 API다.

배관 클래스 API와 재료·속성 비교 함수를 공유하지만 압력 곡선·등급·부식 여유 입력을 강제하지 않는다. 실제 압력 검토가 필요하면 별도 압력 API에 적합한 입력을 제공해야 한다. 자동 0 부식 여유나 가상 압력 데이터는 생성하지 않는다.

검증 기록: `tests/test_component_material_class.py`, 기존 배관 회귀 `tests/test_piping_class.py`, 결과 `artifacts/validation/scope_reset_component_material_class.xml`. 합계 20개 사례는 계약·누락 처리·개수·식별자·Python/JSON 교환과 기존 동작을 확인하며 물리적 재료 적합성의 실험 검증은 아니다.

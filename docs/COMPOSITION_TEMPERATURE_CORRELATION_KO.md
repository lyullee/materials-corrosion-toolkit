# 조성 기반 온도 상관식 API

`materials.composition_temperature_correlation`는 사용자가 검토한 조성 다항식으로 온도를 계산하고, 명시한 조성 적용 범위와 온도 단위를 확인한다. 변태 시작·종료 등의 상관식을 입력할 수 있지만 특정 합금의 고정 계수나 등급별 식은 내장하지 않는다.

입력 계약은 `CompositionTemperatureCorrelation`이다. 기본 조성식의 `chemistry`, 입력·식 질량 기준, `terms`, `constant_offset`, 근거 `basis`를 재사용한다. `output_unit`은 `K`, `degC`, `degF` 중 하나다. 상수와 항의 계수는 해당 단위의 온도를 산출하도록 제공해야 한다. 몰 분율을 질량 분율로 자동 해석하지 않는다.

재료 상태, 온도의 물리적 의미, 보정 모집단과 상관식 개정을 각각 `material_condition_id`, `temperature_quantity_id`, `calibration_population_id`, `correlation_revision_id`로 보존한다. 예측값과 실제 측정값은 구분하며, ID만으로 보정 자료의 독립성이나 적용성을 입증하지 않는다.

`composition_support`의 각 `CompositionSupportRange`는 원소 ID 목록과 합계의 최솟값·최댓값을 지정한다. 경계는 `recipe_mass_basis` 단위다. 원소 하나의 구간이나 여러 원소 합계의 구간을 정의할 수 있다. 모든 식의 원소는 적어도 한 적용 범위에 포함돼야 하며, 지원 조건에 필요한 원소도 실제 입력돼야 한다. 누락된 질소·잔량 철 등을 추정하지 않는다. 범위 밖이면 `out_of_scope`로 예측값을 보류한다.

상관식·조성 범위 검토가 없으면 `needs_data`다. 계산은 기존 조성 다항식의 정확 산술을 재사용하고, 온도 원점과 척도를 명시적으로 변환한다. 최종 Kelvin 값이 양수가 아니거나 필수 수치가 표현 불가능하면 `out_of_scope`다. 기본 조성식의 원소별 기여량과 변환 조성도 함께 반환한다.

주요 출력은 `predicted_temperature_K`, `recipe_temperature_value`, `recipe_temperature_unit`이다. 예측 온도는 관측 변태 온도, 변태 분율, 가열·냉각 경로, 석출·경도·인성 변화, 불확도 구간 또는 재료 수락의 보증이 아니다. 공정·용체화 상태·보정 모집단이 다른 자료의 적용은 호출자가 별도로 검토해야 한다.

검증은 `tests/test_composition_temperature.py`와 기존 조성식 회귀를 포함해 40개 사례로 수행했다. 기록은 `artifacts/validation/composition_temperature.xml`이다. 합성 계수·조성으로 질량 기준 변환, 합계 경계, 외삽 거부, 온도 원점, 누락·해시 및 Python/JSON 교환을 확인했으며 실제 합금의 독립 실험 검증은 별도다.

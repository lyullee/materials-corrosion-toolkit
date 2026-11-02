# 조성 하한을 적용하는 지수 계산

`materials.floored_composition_index_recipe`는 측정 조성을 레시피 질량 기준으로 변환한 후 지정 성분에 `max(측정값, 하한)`을 적용하고 다항식을 계산한다. 기존 `materials.composition_index_recipe`의 계약과 입력 해시는 변경하지 않는다.

입력 계약은 `FlooredCompositionIndexRecipe`다. `constituent_floors`의 단위는 `recipe_mass_basis`이며 입력 분석값의 단위와 다를 수 있다. 하한은 실제 측정됐고 식에 사용되는 성분에만 지정할 수 있다. 누락 성분을 하한으로 채우지 않는다. 계수·상수항·하한·단위·전체 입력은 `CorrelationBasis`의 권한·적용성 검토와 해시에 연결된다.

결과의 `converted_assay`는 변환한 원래 분석값, `effective_constituents`는 계산에 사용한 값이다. `floor_applied_elements`는 실제로 값이 높아진 성분 목록이다. `term_contributions`는 항별 기여도다. 유효값은 대수식용 입력으로 취급하며 합계가 실제 합금 조성이 되도록 재정규화하지 않는다.

가령 측정값 A=0.02, B=0.3에 A 하한 0.1을 사용하고 `2*A**2*B-1`을 계산하면 -0.994다. 이는 직접 작성한 수학 예제이며 실제 합금의 균열 판정식이 아니다.

용접 응고균열 관련 일부 경험식에는 특정 성분의 유효 하한을 두는 형태가 있다. 독립적인 기술적 배경은 [TWI의 응고균열 설명](https://www.twi-global.com/technical-knowledge/job-knowledge/defects-solidification-cracking-044)에서 확인했다. 이 API는 경험계수·표·적용 범위·위험 등급을 내장하지 않는다. 실제 지수 적용에는 공정, 분석 대상, 조성 범위, 형상 및 사용 권한 검토가 별도로 필요하다. 계산된 지수를 균열 확률이나 승인으로 해석하지 않는다.

`tests/test_floored_composition_recipe.py`와 기존 조성 지수 테스트에서 질량 기준 변환, 하한 아래·경계·위, 원래 분석값 보존, 누락 성분, 해시 변조와 기본 레지스트리 Python/JSON 교환을 확인했다. 합계 26개 테스트가 통과했으며 독립 실험에 의한 균열 예측 검증을 의미하지 않는다.

## 0.1.1 수치 범위 보완

질량 기준 변환·거듭제곱·교차항·계수·상수 합산을 입력 부동소수점 값의 정확 유리수로 계산한 뒤 반환값으로 변환한다. 작은 인자의 거듭제곱이 중간에 0이 되더라도 큰 계수와 결합한 최종 항이 표현 가능하면 보존한다. 비영 변환 조성·항·최종 지수가 표현 불가능하면 `out_of_scope`이며, 정확히 0인 계수는 그대로 0이다. 하한 적용식도 같은 계산 함수를 사용하며 원래 조성을 재정규화하지 않는다. 경계 사례와 기존 교환·회귀 합계 32개를 확인했다(`artifacts/validation/composition_recipe_numeric_range.xml`). 이 확인은 조성 지수 산술에 관한 것이며 페라이트 예측·균열·재료 수락 검증이 아니다.

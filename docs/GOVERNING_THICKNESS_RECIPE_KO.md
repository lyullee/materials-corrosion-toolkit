# 지배두께 계산식 API

`fabrication.governing_thickness_recipe`은 사용자가 선택한 형상·용도별 식을 실행한다. 동일 이름의 두께라도 열처리, 시험 면제, 재료 제한 등의 용도가 다를 수 있으므로 `purpose_id`, `selected_geometry_case_id`, `joint_geometry_id`, `material_condition_id`를 구분한다. 재료나 이음 이름만으로 규격의 계산식·면제 조건을 선택하지 않는다.

`ThicknessDimension`은 치수 ID, 양의 m 값, 치수 정의, 기록 해시와 근거를 가진다. `ThicknessExpression`은 앞서 정의한 치수나 식에 `minimum`, `maximum`, `sum`을 적용한다. 최종 출력은 `output_reference_id`로 선택한다. 식 없이 입력 치수 하나를 바로 선택할 수도 있다. 최대·최소 동률은 모든 지배 참조 ID를 보존하며, 합의 반복 참조는 실제 반복 항으로 처리한다.

입력은 `matintegrity.models.engineering_correlations.GoverningThicknessRecipe`다. 기존 상관식 API와 같은 `CorrelationBasis`가 적용된다. 중첩 치수·식 계약을 먼저 정규화한 뒤 전체 요청의 `basis` 제외 JSON 표현을 `canonical_digest`로 해시한다. 이 해시와 동일한 사용 권한·근거를 `basis`에 넣어 요청을 검증한다. 해시는 원시 JSON 문자열이 아닌 기본값까지 포함한 계약의 정규화 값에 대해 계산한다. 모든 치수·선택식·용도·형상 ID가 묶이므로 변경 시 다시 검토하고 해시를 갱신해야 한다.

기본 레지스트리의 `run` 또는 `run_json`으로 실행한다. 출력에는 지배두께(m), 용도·형상·재료 상태 식별자, 요청 해시와 각 식의 연산·참조·선택 경로가 포함된다. 후속 모델의 입력 두께로 전달할 때도 같은 용도와 물리 위치인지 확인해야 한다. 후속 모델의 규격 적용성 검토나 시험 면제·열처리 판단을 대체하지 않는다. 불확실성을 자동 전파하지 않으며 계산값을 보수적 경계로 해석하지 않는다.

검증: 중첩 최소·최대, 합의 반복 항, 동률, 단일 치수 선택, 수치 범위 초과, 잘못된 의존 그래프, 선택 형상 변경 시 해시 거부, Python/JSON 동일성을 확인한다. 공개 코드에 규격 표나 형상별 선택표·면제 상수는 포함하지 않는다.

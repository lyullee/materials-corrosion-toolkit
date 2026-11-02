# 충격 시험 지표의 관측 교차 온도

`inspection.impact_metric_crossings`는 선언한 목표값을 관측 곡선이 지나는 모든 온도를 계산한다. 흡수 에너지(`J`), 전단 파면 비율(`1`), 횡팽창량(`m`)을 별도 지표로 받는다. 전단 파면 비율은 0~1의 값이어야 하며 백분율을 자동 환산하지 않는다.

입력은 같은 재료 상태·시험편 형상·방향의 한 시리즈다. 각 점의 observation/source-group ID와 전체 시리즈의 관측 단위·통계량 기준을 명시한다. 온도는 K로 엄격하게 증가해야 한다. 같은 온도의 반복 측정은 사용자가 명시한 통계량으로 먼저 처리해야 하며, API가 임의로 평균하거나 행을 정렬하지 않는다. 통계량·관측값·적용 조건과 단위 검토를 전체 입력 해시에 연결한다.

계산은 관측점 사이의 구간별 선형 보간이다. 목표값과 정확하게 같은 점, 서로 다른 여러 교차점, 목표값이 유지되는 평탄 온도 구간을 각각 보존한다. 고유한 점 하나일 때만 `unique_crossing_temperature_K`를 제공한다. 여러 교차점이나 평탄 구간은 `needs_data`, 관측 범위 안에 교차점이 없으면 `out_of_scope`다. 외삽·평활화·반복 시험 독립성·통계적 신뢰구간을 추정하지 않는다.

이 결과는 선택한 지표·목표·보간법에 따른 관측 서술값이다. 목표 온도를 DBTT/FATT, 설계 최저 온도 또는 규격 합격으로 자동 승인하지 않는다. 흡수 에너지 로지스틱 곡선은 기존 `materials.impact_transition`에서 별도로 계산한다.

지표 구분의 독립 근거는 [NIST 충격 시험 연구](https://www.nist.gov/publications/impact-characterization-4340-and-t200-steels-means-standard-sub-size-and-miniaturized)다. 표준의 판정표·환산표·합격값은 포함하지 않는다.

`inspection.impact_testing_campaign` 1.0.1은 동일한 물리 시험편을 여러 시험 ID로 등록해 반복 수를 부풀리는 입력을 거부한다. 한 시험의 여러 지표는 하나의 test record에 함께 기록한다. 입력 필드 변경은 없다.

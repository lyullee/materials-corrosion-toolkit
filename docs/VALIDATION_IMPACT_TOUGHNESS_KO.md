# 충격·인성 계산과 자료 연결 확인

2026-11-01 로컬 검토 기록이다. 기존 구현을 재사용하고 실제 시험편 중복 집계 문제 및 지원되지 않던 관측 교차점 계산을 보완했다.

| 범위 | 확인 내용 |
|---|---|
| 에너지 전이 곡선 | 합성 선반값·폭·관측 내 목표 온도 복원, 자료 범위와 이상치 처리 |
| 계장화 충격 신호 | 부호 있는 힘–변위 적분, 최대 힘 평탄부, 유효 구간·교정·자료 누락 |
| 충격 캠페인 | 사용자 기준, 물리 시험편 중복 거부, 반복 수와 독립 그룹 |
| 인성 캠페인·증거 | 시험법·단위·형상·끝점·유효성·자료 분할·기준 및 해시 |
| 지표 교차 온도 | 에너지/전단 파면 비율/횡팽창량 단위, 모든 교차점·평탄 구간, 외삽 거부 및 관측 ID |
| API 연결 | 신규 교차점 API와 기존 5개 API의 Python/JSON 결과·단위·맥락 일치 |

이번 묶음의 고유 테스트 사례 40개가 통과했다. 새 교차점 파일의 재실행과 통합 교환 실행에 포함된 같은 사례는 중복 집계하지 않았다. 재검토 범위의 누적 관련 테스트는 298개이며 전체 저장소 테스트 수나 물리적으로 검증한 모델 수가 아니다.

`inspection.impact_testing_campaign` 1.0.1은 동일 시험편이 다른 시험 ID나 독립 그룹 이름으로 반복 집계되는 입력을 거부한다. 여러 지표는 한 시험 record에 함께 기록한다. `inspection.impact_metric_crossings`는 측정 지표별 교차점을 구분하고 고유한 점을 선택할 수 없는 데이터를 보류한다.

실행 파일은 `tests/test_impact_transition.py`, `tests/test_instrumented_impact_signal.py`, `tests/test_impact_testing_campaign.py`, `tests/test_fracture_toughness_testing.py`, `tests/test_fracture_toughness_evidence.py`, `tests/test_impact_metric_crossings.py`, `tests/test_toughness_api_exchange.py`다. 새 API의 합성 예제는 `examples/impact_metric_crossings.py`다.

본 결과는 실제 인성 시험의 규격 유효성, 시험편 독립성의 외부 확인, 실제 재료의 천이 온도 qualification, K/J/CTOD 환산 및 설계 최저 온도나 합격 판정을 대체하지 않는다.

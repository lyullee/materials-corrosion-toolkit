# 환경 적용성·등가 노출·조성 지표 검토

2026-11-01 로컬 확인 기록이다. 합성 입력에 대한 수학·자료 연결 확인과 실제 재료 검증을 구분한다.

| 묶음 | 통과 사례 | 범위 |
|---|---:|---|
| 열화 등가 노출·산화 | 11 | 가중 시간 합, 관측 공백, 시계 이동, 온도 의존 적분, 경로 반전, 보간 범위 및 자료 분리 |
| 황화·침탄·질화·선택 용출 | 21 | 선언된 환경·단위·기준·재료·시험 기록과 적용 범위 연결 |
| 저온·액체금속·습윤 황화수소 적용성 | 13 | 재료 상태·시험 분할·누락·범위 밖 및 식별자 검사 |
| 조성 지표 계산 | 18 | 질량 기준 변환, 다항식, J/X/RCS/K 구조, 누락 원소·잘못된 계수·변조·overflow, Python/JSON 교환 |
| 환경 모델 API 교환 | 9 | 동일 입력·결과·단위·맥락·해시를 Python/JSON 경로에서 보존 |

이번 72개를 포함한 재검토 범위의 누적 관련 테스트는 258개다. 전체 저장소 테스트 수나 검증한 물리 모델 수가 아니다. 재실행한 같은 사례는 추가 집계하지 않는다.

등가 노출 API 1.0.1은 관측 구간 사이의 누락 시간을 노출 0으로 취급하던 문제를 수정했다. 누락 구간을 출력하고 `needs_data`로 처리하며 한계 이내 여부를 보류한다. 산화 적분의 작은 제곱 길이 값은 절대 허용오차가 결과를 가리지 않도록 상대 오차 기준으로 확인했다.

환경 적용성 API는 제공된 사용자 시험·범위와의 연결을 확인한다. 공급자 시험의 물리적 유효성, 보편적인 취화·균열·금속 손실 법칙, 독립 실험 비교 및 규격 합격을 이 결과로 완료 처리하지 않는다. 조성 지표의 계수와 한계는 포함하지 않으며 사용자가 검토한 값을 입력한다.

실행 파일은 `tests/test_metallurgical_aging.py`, `tests/test_nonisothermal_oxidation.py`, `tests/test_sulfidation.py`, `tests/test_carburization.py`, `tests/test_nitriding_degradation.py`, `tests/test_selective_leaching.py`, `tests/test_brittle_applicability.py`, `tests/test_liquid_metal_embrittlement.py`, `tests/test_sour_environment.py`, `tests/test_composition_index_recipe.py`, `tests/test_environment_model_api_exchange.py`다.

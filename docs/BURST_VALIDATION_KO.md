# 배관 파열압 예측 비교

## 목적과 경계

`structural.burst_pressure_comparison`은 사용자가 공급한 파열압 예측과 자격화한 실제 시험
종료압을 같은 압력 기준에서 비교한다. 특정 규격식, 유동응력식, bulging factor, 안전계수,
합격 한계 또는 재료 표는 내장하지 않는다. 따라서 상용 해석기, 사용자 식, 별도 저장소 모델과
동일한 계약으로 조합할 수 있다.

입력의 `observed_burst_pressure_Pa`는 검토된 실제 시험 종료압이고
`predicted_failure_pressure_Pa`는 고정된 공급자 모델의 예측이다. 두 값은
`internal_minus_external`, `gauge_internal` 또는 `absolute_internal` 중 동일한 기준이어야 한다.
기준이 `unresolved`이거나 서로 다르면 비교하지 않는다.

## 필요한 정체성과 검토

각 행은 다음을 보존한다.

- 관측·물리 시편·원 자료 그룹·분할 ID
- 재료 상태·형상·하중 case
- 관측과 예측의 압력 기준
- 원 관측 파일 SHA-256과 예측 입력 digest
- 관측 이용 권한, 실제 시험 끝점, 형상·재료와 압력 기준의 검토 상태

한 물리 시편은 한 행에만 나타날 수 있다. 물리 시편 독립성을 검토했다고 선언하려면 모든
행에 시편 ID가 있어야 한다. 같은 source group을 calibration과 holdout 또는
external-validation으로 나누는 행위는 거절한다. 예측 설정은 평가 관측을 보기 전에 고정했다고
선언해야 한다. 이 선언은 코드가 외부 연구 절차를 독립적으로 확인했다는 뜻이 아니라, 잘못된
비교를 무심코 통과시키지 않기 위한 계약이다.

## 출력

행마다 예측/관측 압력비와 그 자연로그를 반환한다. calibration, holdout,
external-validation을 합치지 않고 각각 다음 기술통계를 계산한다.

- 관측 수와 source group 목록
- 산술평균·중앙값·최소·최대 예측/관측비
- 평균 로그비와 로그오차 RMS
- 평균 절대 상대오차

이 값은 신뢰구간, 모집단 포괄률, 규격 합격, 안전계수, 잔여수명 또는 고장확률이 아니다.
자료 선택과 모델 동결이 적절하더라도 적용영역 밖 재료·형상·하중에 대한 타당성을 자동으로
확장하지 않는다.

## 현재 공개 편집본의 적용 상태

`compiled-pipe-burst`는 시험 파열압 102행과 FEM 실패압 351행을 구분하지만 주 표에서
내경/외경과 절대압/게이지압/차압 기준을 확정할 수 없다. 전 행의 물리 시편 ID와 원 관측 권리도
자격화되지 않았고 `Ma13Otros` 23행의 원 문헌은 미해결이다. 따라서 이 편집본을 새 비교기에
자동 투입하거나 102행을 독립 검증 표본이라고 선언하지 않는다.

[편집본 제공자 페이지](https://doi.org/10.17632/77t4k43y7g.1)의 CC0 선언은 편집본에 대한
표시이며 각 원 문헌 관측의 재배포 허가로 확대하지 않는다. Ma 논문의
[출판사 페이지](https://doi.org/10.1016/j.engfailanal.2013.03.015)는 79개 수집 시험의 서지·의미
검토에만 사용한다. 원 논문 표나 점별 관측은 공개 패키지에 복사하지 않는다.

## 재현

```powershell
.\.venv\Scripts\python.exe examples/burst_prediction_comparison.py
.\.venv\Scripts\python.exe scripts/validate_burst_prediction_comparison.py
.\.venv\Scripts\python.exe -m pytest tests/test_burst_prediction_comparison.py -q
```

`validation/burst_prediction_comparison_math.json`은 합성 압력비 1.0, 0.8, 1.25의 분할과
산술 항등식을 검사한다. 실제 파열시험이나 특정 압력모델의 정확도 검증은 아니다.

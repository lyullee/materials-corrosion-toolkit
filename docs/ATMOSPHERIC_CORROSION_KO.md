# 탄소강 1년 대기부식 자료와 제한적 예측

## 구현 범위

`read_atmospheric_corrosion_observations`는 고정 SHA-256의 공개 ZIP에서 프로그램 자료와 독립
연구 자료를 읽는다. 원 출처 행, 프로그램·연구 source group, 위치, 제공자 품질등급과
표·그림 추출 구분을 보존한다. 물리 시편 ID가 제공되지 않으므로 행 번호에서 시편을 만들지
않는다. 제공자가 조화한 ERA5/Open-Meteo 기후량은 시편과 동시에 측정한 환경값으로 부르지 않는다.

`corrosion.atmospheric_first_year_fit`은 양의 1년 평균 두께손실을 자연로그로 바꾸고, 다음의
독립적으로 정의한 고정 특징에 조건부 최소제곱을 적용한다.

- 절편
- 288.15 K를 중심으로 10 K 단위화한 온도
- 상대습도 0.75를 중심으로 0.1 단위화한 값
- 염화물 침적량의 `log1p`
- 이산화황 침적량의 `log1p`

보정과 보류 source group은 겹칠 수 없다. 호출자는 보류 log-RMSE, 절대 log-bias와 보정 지원
범위 이탈 비율의 최대값을 적합 전에 선언한다. 반환 모델은 이 기준과 실제 결과를 함께 보존한다.
보류 그룹별 observation count, log-RMSE, absolute log-bias와 보정 지원 이탈률도 별도로 집계한다.
전체 행 가중 결과가 좋아도 어느 한 source group이 RMSE 또는 bias 한계를 넘으면 전이 gate는 실패한다.
이는 각 source group을 독립 검증 단위로 취급해 큰 그룹이 작은 그룹의 오차를 가리는 것을 제한한다.
모델은 calibration과 holdout 입력 각각의 canonical digest를 보존한다. Holdout digest는 전이 gate의
보류자료 revision을 고정하지만 점별 관측값을 공개 결과에 포함하지 않는다.

회귀 모델에 포함되는 5×5 계수 공분산 행렬은 유한·대칭뿐 아니라 양의 준정부호여야 한다. 이는 예측분산을 음수로 만드는 잘못된 사용자 모델을 입력 단계에서 차단한다. 특이하지만 양의 준정부호인 행렬은 허용한다. 예측구간은 고정 공변량·선택 모델형식 조건부이며 공변량, 출처, 모델형식, 모집단 불확실성은 포함하지 않는다.

`corrosion.atmospheric_first_year_prediction`은 정확히 한 해의 평균 손실만 계산한다. 행 집계와
모든 source-group 집계 기준을 함께 만족하지 못한 모델은 기본적으로 `needs_data`이고, 제한된 전이성을
알고도 사용하는 별도 검토가 있어야만 계산한다. 새 group 진단이 없는 legacy model은 자동 통과로
간주하지 않는다. 보정 범위를 벗어난 공변량도 별도 외삽 검토가 없으면 중지한다.

## 공개 자료와 권리 경계

고정 자료는 Mendeley Data의 *Harmonised first-year atmospheric corrosion database for carbon
steel with ERA5 covariates*, DOI `10.17632/ysr7wy3y7z.1`이다. 자료 페이지는 편집물에 CC BY 4.0을
표시한다. 프로그램 617행, 독립 연구 106행과 별도 베트남 3행을 포함한다. 원 관측은 여러
프로그램·논문에서 왔으므로 편집물 라이선스, 원 출처 인용과 점별 관측 재배포 권리를 같은 것으로
취급하지 않는다. 공개 배포에는 원 ZIP이나 점별 예측을 넣지 않고 취득 주소·해시·집계 검증만 둔다.

## 현재 검증 결과

`scripts/validate_atmospheric_corrosion.py`는 프로그램 617행을 보정에, 독립 연구의 A/B 등급
83행을 보류에 사용한다. C 등급 및 침적량이 부족한 23행은 적합 전에 제외한다. 직접 NumPy
최소제곱과 구현 계수의 최대 절대차는 0이다.

기존 자료 검토에서 사용한 행 집계 사전 기준은 보류 log-RMSE `log(2)`, 절대 log-bias `log(1.5)`,
지원범위 이탈 비율 0.1이다. source-group 최대 RMSE와 bias도 각각 같은 RMSE/bias 상한을 사용해
각 그룹이 모두 통과해야 하도록 gate를 강화했다. group-wise 재계산 결과는 batch94를 누리온에서
실행한 후 별도 기록한다. 아래 기존 aggregate 수치는 새 group-wise gate를 검증한 값이 아니다.
실제 보류 log-RMSE는 약 1.20494, 절대 log-bias는 약 0.36009, 범위 이탈은 33/83 약 0.39759다.
따라서 전이 기준은 충족하지 않는다. 이는 수학 구현 실패가 아니라 외부 source group 전이가
부족하다는 검증 결과이며, 현재 모델은 운전 예측 자격이 없다.

## 포함하지 않는 주장

`degradation.atmospheric_multi_year_loss_history`는 별도로 자격화된 1년 손실 anchor와 사용자 공급 시간지수만 사용해 지원기간 안의 다년 누적손실 이력을 만든다. 재료·표면·노출구역·climate/pollutant descriptor와 provider digest, 독립 calibration/holdout 시편·source group이 정확히 일치해야 한다. 현재 공개 1년 회귀가 자동으로 이 전이모델의 자격을 얻는 것은 아니다.

이 경로는 습식 CO2 내부부식, 공식 깊이, 국부 최대 침투, 잔여수명, 구조용량,
합격판정 또는 고장확률 모델이 아니다. 조건부 회귀구간은 기후 공변량 오차, 출처 차이,
모델형식 및 모집단 불확실성을 포함하지 않는다. 실제 적용에는 지역·재료상태별 독립 자료,
시간 외삽 모델과 별도의 한계상태·불확실성 모델이 필요하다.

## 재현

```powershell
.venv\Scripts\python.exe scripts\fetch_data.py atmospheric-carbon-steel-first-year
.venv\Scripts\python.exe scripts\validate_atmospheric_corrosion.py
.venv\Scripts\python.exe -m pytest tests\test_atmospheric_corrosion.py -q
```

집계 결과는 `validation/atmospheric_corrosion_first_year.json`에 기록한다.

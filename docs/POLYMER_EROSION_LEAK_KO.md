# 고분자 시간–온도·충식부식·기준누설 보정

## 고분자 Arrhenius 시간 이동계수

`materials.polymer_arrhenius_shift_calibration`은 동일 polymer formulation, physical state,
endpoint의 자연로그 시간 이동계수를 `(1/T - 1/Tref)`에 가중 적합한다. 유효한
calibration record만 계수를 만들고 holdout은 사후 log bias/RMSE에만 쓴다. specimen,
source group, independence group은 partition을 건너지 않는다. 양의 기울기와 서로 다른
calibration 온도가 식별되어야 한다. 지정 온도 support 밖은 외삽하지 않는다.

이 계산기는 time–temperature shift 관계만 적합한다. 약품·유체 호환성, swelling,
장기 파괴, 합격이나 고장확률을 판정하지 않는다. 가정은 glass transition을 통과하는 범위에
자동 적용하지 않는다.

## 충식–부식 power-law 보정

`degradation.erosion_corrosion_power_law_calibration`은 한 개의 검토된 material/fluid/geometry/
mechanism regime에서 측정된 결합 손실률을 velocity와 particle concentration의 가중
log-linear power law로 적합한다. holdout은 log velocity–log concentration calibration convex
hull 안에서만 bias, RMSE와 likelihood를 계산한다.

결과는 순수 erosion과 corrosion contribution을 분리하지 않고 regime transition을 식별하지 않는다.
서비스 손실 예측, 보수 기준, 합격, 수명과 확률은 별도 자격화 대상이다.

## 기준누설–장비응답 보정

`inspection.reference_leak_response_calibration`은 traceable positive molar leak rate `mol/s`와 같은
clock의 positive instrument response를 고정 log–log 회귀로 적합한다. instrument configuration,
gas, boundary condition, 압력·기준온도 정의, 불확도, provider/result digest를 모두 요구한다.
non-detect, censored, missing과 invalid record는 0이나 검출한계로 대체하지 않고 제외 상태를
결과에 보존한다. holdout은 calibration leak-rate support 안에서만 평가한다.

이 경로는 알 수 없는 누설률을 역산하지 않고, detection probability, 현장 합격, 환기·확산,
FTA 기초사건 확률을 만들지 않는다.

## ESCAPE‑1 공개자료

[ESCAPE‑1 Dryad record](https://doi.org/10.5061/dryad.8931zcrwq)은 CC0로 공개된 통제 지하
천연가스 누출 측정이다. 11개 workbook과 README 1개, 총 2,309,115 byte를 취득하고 모든
provider MD5를 확인했다. `escape_leak_data.audit_escape1_leak_dataset`은 118,606개 시각–ppm·m
표본의 header, 유한성, 비음수, 시각 순서와 파일 SHA-256을 검사한다.

제공자 README는 5·10·20 standard litre/minute 누출을 식별하지만 standard 참조 압력·온도를
정의하지 않는다. 각 trace의 background, steady-release, transit, recovery window도 workbook에
레이블되지 않았다. 따라서 reader는 provider `slpm`을 원문 정의로 보존하고 `mol/s`로
변환하거나 위 보정기에 자동 연결하지 않는다. 원자료는 `data/raw/`에만 두어 배포물에서
제외한다. 공개 검증 요약은 `validation/escape1_leak_data_audit.json`이다.

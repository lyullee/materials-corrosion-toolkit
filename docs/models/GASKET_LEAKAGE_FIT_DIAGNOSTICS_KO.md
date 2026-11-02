# 가스켓 누설 표면 적합 잔차 진단

## 목적

이 모듈은 이미 계산된 `fabrication.gasket_leakage_map_fit` 결과를 받아 calibration과 holdout 잔차를 분리해 요약합니다. 적합 계수를 다시 계산하거나 누설 표면을 수정하지 않습니다.

## Python API

- 입력 계약: `GasketLeakageFitDiagnostics`
- 함수: `diagnose_gasket_leakage_fit`
- 출력: `Calculation`
- model ID: `fabrication.gasket_leakage_fit_diagnostics`

원 적합 모델은 caller가 지정한 contact-pressure 및 differential-pressure 격자에 비음수 bilinear 누설 플럭스 표면을 적합합니다. 적합 데이터는 calibration 역할 행으로 제한되고, 입력 계약은 specimen/source group이 calibration과 holdout에 걸쳐 재사용되는 것을 거부합니다. 진단 API는 이 계산 결과의 full-result SHA-256, input/context digest, 원 적합 요청 digest와 calibration map digest를 확인한 뒤에만 잔차를 집계합니다.

## 입력

입력은 계산된 fit `AssessmentResult`, 해당 전체 결과의 canonical SHA-256, 그리고 다음 caller review입니다.

- 잔차 부호·단위 해석
- source group의 역할과 물리 범위
- 진단 계산의 이용 권한

source result에서 원 관측 행과 예측·잔차 행을 읽으므로, 데이터 파일이나 provider를 자동으로 다시 열지 않습니다. 적합 결과가 저장한 원 관측 식별자, source group, source hash, 역할이 예측 행과 정확히 맞지 않으면 집계를 중단합니다.

## 지표

역할(calibration/holdout)별, source group별, caller-provided specimen label별로 다음 값을 반환합니다.

- 평균 signed error
- 평균 절대 오차
- RMSE
- 최대 절대 오차
- caller residual scale로 나눈 표준화 잔차의 평균, RMS, 최대 절대값

표준화 오차는 각 observation에 명시된 `residual_scale_mol_s_m2`를 사용합니다. 이는 계산 가중치의 크기를 반영하는 기술 통계이며, 측정 불확도나 신뢰구간으로 해석하지 않습니다.

## 사용 예

```python
from matintegrity.contracts import canonical_digest
from matintegrity.models.gasket_leakage_fit_diagnostics import (
    GasketLeakageFitDiagnostics,
    diagnose_gasket_leakage_fit,
)

request = GasketLeakageFitDiagnostics(
    assessment_id="gasket-map-fit-summary-01",
    fit_result=computed_fit_result,
    fit_result_sha256=canonical_digest(computed_fit_result.model_dump(mode="json")),
    residual_interpretation_reviewed=True,
    source_group_roles_and_scope_reviewed=True,
    diagnostic_use_authorized=True,
)
diagnostics = diagnose_gasket_leakage_fit(request)
```

`computed_fit_result`에는 holdout 행이 사전 선언되어 있어야 합니다. 해당 행이 없으면 calibration 요약은 돌려주되 `needs_data`를 반환하며, holdout 진단이 가능하다고 표시하지 않습니다.

## 경계

- holdout 행은 적합 계수에 사용되지 않았던 행이어야 합니다. 진단 모듈은 독립성을 새로 판정하지 않고 원 요청의 구분을 보존합니다.
- specimen ID 및 source group ID는 caller가 제공한 라벨입니다. 이 API가 실제 시편 독립성이나 반복 수를 인증하지 않습니다.
- holdout 지표는 제한된 입력 데이터의 오차 요약입니다. 외부 독립 검증, 다른 joint로의 이전성, 장기 누설 예측, 실링 합격, 허용기준 만족 또는 설계 적합을 뜻하지 않습니다.
- 매개변수 추정 불확도, 계수 공분산, 입력 분포, 측정 오차, 신뢰구간, model-form uncertainty와 failure probability는 계산하지 않습니다.
- 입력 결과 digest, map digest 또는 관측 행 계보가 맞지 않으면 계산을 수행하지 않습니다.

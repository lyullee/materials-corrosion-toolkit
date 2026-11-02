# 보정된 크리비스 wall-sink rate history 적용

## 목적

앞 단계에서 보정한 유효 Arrhenius wall-transfer velocity를 digest와 원 관측으로 확인한 뒤, caller가 입력한 exact temperature knot에 기존 `crevice_wall_sink_rate_history` 계산을 적용한다. 참조속도와 활성화에너지를 사람이 다시 복사·입력하지 않도록 두 계산의 lineage를 직접 잇는다.

이 API는 calibration 계산과 rate-history 계산을 구성하는 integration adapter다. calibration 모델을 새로 적합하거나 입력한 이력 온도에서 측정값을 학습하지 않는다.

## API

- 모듈: `matintegrity.crevice_calibrated_wall_sink_history`
- 입력: `CreviceCalibratedWallSinkHistoryRequest`
- 평가기: `evaluate_crevice_calibrated_wall_sink_history()`
- ModelSpec: `specifications()`
- 모델 ID: `integration.crevice_calibrated_wall_sink_rate_history`
- source ID: `caller_crevice_wall_sink_calibration_application`

필수 lineage는 원 `CreviceWallSinkArrheniusCalibrationRequest`, 그 evaluator가 반환한 전체 `Calculation` 결과 및 canonical SHA-256이다. Adapter는 보정 결과를 입력 관측으로 다시 계산하고 전체 계산 결과 digest가 제공값과 일치하는지 확인한다. 계산 산출물의 `input_sha256`, calibration ID, 물리 범위도 typed 원 입력과 대조한다.

응용 이력은 asset/location/geometry/species/condition ID, 정확한 시간 knots와 온도 knots, 그리고 application Evidence를 가진다. calibration과 응용 Evidence source ID가 겹치면 reject한다. review gate로 calibration과 응용 조건 일치, 이력 조건 mapping, 1차 비가역 wall law 사용을 확인한다.

## 계산과 범위

보정에서 얻은 `reference_wall_transfer_velocity_m_s`, `activation_energy_J_mol`, `reference_temperature_K`를 기존 wall rate history 입력에 넣어 각 exact temperature knot의 `k_w`를 계산한다. 허용 온도는 calibration 관측의 최소/최대 온도 구간과 같다. 하나라도 구간을 벗어나면 전체 rate history를 반환하지 않는다. 온도 또는 속도의 knot 사이 보간은 하지 않는다.

성공 결과에는 기존 rate history 전체와 원 calibration result SHA, rate-history 입력/결과 digest, temperature support 및 holdout RMSE lineage가 포함된다. 원 calibration 요청을 다시 계산했을 때 result digest가 다르면 `out_of_scope`; review가 빠지거나 원 calibration이 더 이상 계산되지 않으면 `needs_data`를 반환한다.

## 연결 예시

```python
from matintegrity.crevice_calibrated_wall_sink_history import (
    CreviceCalibratedWallSinkHistoryRequest,
    evaluate_crevice_calibrated_wall_sink_history,
)

# calibration_result는 fit_crevice_wall_sink_arrhenius(calibration_request)의
# 전체 Calculation.model_dump(mode="json") 결과이며 별도로 canonical SHA를 기록한다.
request = CreviceCalibratedWallSinkHistoryRequest(
    history_id="case-42-wall-k",
    calibration_request=calibration_request,
    calibration_result=calibration_result,
    calibration_result_sha256=calibration_result_sha256,
    asset_id="asset-1",
    location_id="crevice-A",
    geometry_id="slit-v2",
    species_id="H+",
    condition_id="condition-A",
    elapsed_time_s=(0.0, 600.0, 1200.0),
    temperature_K=(298.15, 323.15, 348.15),
    application_evidence=(temperature_history_evidence,),
    calibration_application_and_state_match_reviewed=True,
    output_condition_mapping_reviewed=True,
    first_order_irreversible_wall_law_application_reviewed=True,
)
result = evaluate_crevice_calibrated_wall_sink_history(request)
```

## 제한

이 연결은 effective wall-transfer velocity(`m/s`) 이력만 계산한다. `k_w`를 concentration sink term으로 써서 농도 이력을 계산하려면 별도 transient sink/transport 입력과 geometry basis가 필요하다. 재료 손실률이나 부식률, 질량전달·반응 지배기작, 표면상태 변화, calibration 온도 밖의 예측, acceptance 및 qualification은 추론하지 않는다. Calibration fit가 좋아도 applicability review를 대신하지 않는다.

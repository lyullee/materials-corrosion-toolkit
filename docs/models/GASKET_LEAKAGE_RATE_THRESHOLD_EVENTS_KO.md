# 가스켓 누설률 임계값 이력

## 목적

`integration.gasket_leakage_rate_threshold_events`는 기존 가스켓 누설률 이력을 사용자가 정한 하한·상한과 비교해 임계값 아래·위에 머무는 시간 구간을 계산합니다. 계산 결과는 누설 모델과 외부 위험·결과 모듈 사이의 명시적인 인터페이스로 사용할 수 있습니다.

이 API는 누설률을 새로 예측하지 않습니다. `fabrication.gasket_calibrated_leakage_history`의 계산 완료 결과만 받아서 사용하며, 결과의 전체 해시와 입력·실행 맥락 다이제스트를 확인합니다. 원본의 시간 단위 `s`와 누설률 단위 `mol/s`가 명시되어야 합니다.

## 입력과 판정

- 원본 누설 이력의 `AssessmentResult`와 SHA-256
- 적용 범위에 묶인 하한 및 선택적 상한 (`mol/s`)
- 기준 제공자·개정·기록 ID와 선택한 한계를 포함한 SHA-256
- 기준 및 사용권 관련 `Evidence`
- 물리 범위, 시간축, 기준 적용성, 선형 재구성, 단위, 출처, 사용권 검토

두 계산된 시간 절점 사이의 누설률은 사용자가 검토한 선형 경로로 해석합니다. 경계 교차 시각은 그 재구성에서의 선형 보간값입니다. 원본 절점 밖은 계산하지 않으며, 교차 구간은 제공된 이력의 좌·우 끝에서 잘릴 수 있습니다.

## 출력 해석

`below_minimum_intervals` 및 `above_maximum_intervals`는 한계를 엄격히 벗어난 연속 구간이며, 시작·종료 시각, 지속시간, 이력 끝단에서의 절단 여부를 포함합니다. `time_points_s`와 `molar_leak_rate_points_mol_s`도 원본 값 그대로 남습니다.

하한 미만은 사용자가 하한을 0보다 크게 설정하면 무누설 또는 저누설 구간을 표시하는 데 쓸 수 있습니다. 이 결과는 씰 수용기준, 누설 실패, 위험도, 결과 심각도, 확률을 뜻하지 않습니다. 그러한 해석은 별도 위험 모듈이 조건과 기준을 받아 수행해야 합니다.

## 범위 밖

원본 결과 해시 또는 입력 다이제스트가 불일치하거나, 원본 단위·절점 배열이 적합하지 않으면 `out_of_scope`를 반환합니다. 필수 검토가 빠지면 `needs_data`입니다. 계산 경로는 보간만 수행하며 원본 접촉해석이나 누설 보정식을 다시 실행하지 않습니다.

## Python API

```python
from matintegrity.models.gasket_leakage_rate_threshold_events import (
    GasketLeakageRateThresholdEvents,
    evaluate_gasket_leakage_rate_threshold_events,
)

request = GasketLeakageRateThresholdEvents.model_validate(payload)
result = evaluate_gasket_leakage_rate_threshold_events(request)
```

Payload의 필드명과 단위는 `GasketLeakageRateThresholdEvents` 계약을 기준으로 작성합니다. 기준 해시는 `threshold_provider_id`, `threshold_provider_revision`, `threshold_record_id`, `physical_scope_id`, `minimum_rate_mol_s`, `maximum_rate_mol_s`를 동일한 키로 묶은 정규화 객체의 `canonical_digest`입니다. 사용권과 출처 근거를 분리해 제공해야 합니다.

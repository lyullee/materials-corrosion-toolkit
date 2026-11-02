# 틈 벽면 1차 소모 계수의 Arrhenius 온도 이력

## 목적

`matintegrity.crevice_wall_sink_rate_history.v1`은 사용자가 제공한 기준 벽면 전달속도 계수와 활성화에너지로부터, caller가 제시한 온도 이력의 **정확한 입력 절점**에서만 벽면 1차 소모 계수를 계산한다. 일반 Arrhenius 계산기를 재사용하면서 crevice 대상 식별자, 온도 지원범위, 시간 대응, Evidence, 적용성 리뷰를 하나의 요청으로 묶는다.

이 API는 속도계수 절점 표만 반환한다. 온도 사이를 보간하지 않으며, 틈 농도장·유동·벽면 소모량·부식속도도 계산하지 않는다.

## API

```python
from matintegrity.crevice_wall_sink_rate_history import (
    CreviceWallSinkRateHistoryRequest,
    evaluate_crevice_wall_sink_rate_history,
)
```

필수 입력은 다음과 같다.

- 자산·위치·형상·종·조건 식별자
- 서로 길이가 일치하는 엄격 증가 `elapsed_time_s` 및 같은 순서의 절대온도 `temperature_K`
- 기준 벽면 전달속도 `reference_wall_transfer_velocity_m_s`
- `reference_temperature_K`, `activation_energy_J_mol`
- 닫힌 구간으로 선언한 최소/최대 지원온도
- 계수의 근거, 온도 이력과 조건의 대응, 비가역 1차 벽면 법칙 적용을 확인하는 리뷰 플래그 및 `Evidence`

온도 표본 수는 2~5,000개다. 하나라도 명시된 지원범위를 벗어나면 전체 계수 이력을 반환하지 않고 해당 절점들을 `out_of_scope`로 표시한다. 계산 도중 오버플로 또는 양의 기준계수의 지수 인자 언더플로가 발생해도 결과는 원자적으로 보류한다.

## 식과 결과

```text
k(T) = k_ref exp[-Ea/R (1/T − 1/T_ref)]
R = 8.31446261815324 J/(mol K)
```

각 결과 행은 입력 절점 순서를 유지하며 시간, 온도, 온도계수, 전달속도(m/s), 절점별 입력 digest를 포함한다. 전체 요청에는 canonical SHA-256과 원 Evidence를 기록한다.

기준 속도와 활성화에너지는 caller가 선언하고 검토한다. 이 API는 계수를 데이터에서 적합하지 않고, 해당 재료·전해질·표면에 적합한지 판단하지 않는다.

## 적용 한계

- 출력 속도는 caller 정의의 유효 Arrhenius 법칙을 절점에서 평가한 값이다. 메커니즘이나 활성화에너지의 물리적 타당성을 검증하지 않는다.
- 절점 사이의 온도·계수 값은 계산하지 않는다. downstream 사용자는 보간 또는 piecewise-constant 해석을 별도로 명시하고 검토해야 한다.
- 현재 출력은 앞서 구현된 constant-coefficient transient wall-sink solver에 자동 공급되지 않는다.
- 반응물 고갈, 다종 반응망, 흡착, 침전, 상평형, 형상 변화, 부식률, 금속 손실, 잔여수명 및 위험확률을 추론하지 않는다.
- 온도 지원범위 안의 계산 성공은 실험 검증이나 운전 적합성 증거가 아니다.

## 개발 상태

독립 모듈과 안내서만 추가했다. 중앙 registry/schema/catalog 연결, 테스트, 실제 계산 및 패키지 작업은 상위 작업에서 별도로 처리한다.

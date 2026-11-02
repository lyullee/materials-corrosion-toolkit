# 막힌 틈의 정상상태 확산–벽면 소모 모델

## 목적

`matintegrity.crevice_steady_wall_sink.v1`은 입구 농도가 일정하고 막힌 끝단을 갖는 고정 슬릿에서, 한 용존종이 일정한 유효 확산계수와 선형 벽면 소모 법칙을 따른다는 경우의 정확한 1차원 정상상태 해를 계산한다. 계산 결과는 입력 조건에서 농도 프로파일과 입구 공급량, 벽면 소모량을 비교하는 축약 스크리닝이다.

이는 기존 시간 의존 수송 계산이나 반응망 계산을 대신하지 않는다. 공간 반응망, 다종 전하수지, 상평형, 침전량, 시간 변화, 틈 형상 변화, 부식속도 또는 수명은 계산하지 않는다.

## API

```python
from matintegrity.crevice_steady_wall_sink import (
    CreviceSteadyWallSinkRequest,
    evaluate_crevice_steady_wall_sink,
)
```

`CreviceSteadyWallSinkRequest`에 다음을 제공한다.

- `asset_id`, `location_id`, `geometry_id`, `species_id`, `condition_id`: 계산 대상과 적용 조건 식별자
- `length_m`: 틈 입구에서 막힌 끝까지의 길이
- `effective_diffusivity_m2_s`: 해당 종의 유효 확산계수
- `wall_area_per_volume_m_inv`: 수용액 부피당 반응 벽면 면적
- `wall_transfer_velocity_m_s`: 농도에 비례하는 벽면 소모 속도 계수
- `mouth_concentration_mol_m3`: 입구의 고정 농도
- `sample_positions_m`: 요청한 위치별 농도 출력 지점. 비우면 입구, 1/4, 중간, 3/4, 끝단을 반환한다.
- 세 가지 `*_reviewed` 값과 하나 이상의 `Evidence`: 상수 물성·형상, 막힌 끝단 무유량 경계, 비가역 1차 벽면 소모 법칙의 적용 근거

검토 플래그가 빠져 있으면 `needs_data`를 돌려준다. 수치 범위를 벗어난 해는 자르지 않고 `out_of_scope`로 반환한다.

## 계산식

좌표 `x`는 입구에서 안쪽으로 증가한다. `D`는 유효 확산계수, `C`는 농도, `k_w`는 벽면 소모 속도 계수, `a_w`는 용액 부피당 반응 벽면 면적이다.

```text
D d²C/dx² − k_w a_w C = 0
C(0) = C₀
dC/dx(L) = 0
λ = sqrt(k_w a_w / D)
φ = λ L
C(x) = C₀ cosh(λ(L−x)) / cosh(λL)
```

평균 농도는 `C₀ tanh(φ)/φ`이며, `φ`가 0에 가까울 때는 연속 극한 `C₀`를 사용한다. 입구 기준 단면적당 공급 플럭스와 틈 길이 전체의 벽면 소모량은 정상상태 질량보존상 같아야 한다. API는 두 값을 따로 반환하고 그 차이와 상대 잔차도 제공한다.

큰 `φ`에서도 농도비를 지수식으로 계산해 쌍곡선 함수의 오버플로를 피한다. 표현 가능한 범위를 넘어서는 입력 또는 결과는 이유를 포함한 `out_of_scope`로 처리한다.

## 적용 경계

- 단일 화학종의 선형 확산과 1차 비가역 소모만 취급한다.
- 형상, `D`, `k_w`, `a_w`, 입구 농도는 위치와 시간에 따라 일정하다고 본다.
- 막힌 끝단에서 종의 법선 플럭스가 0이라고 가정한다. 통과 유동이나 압력 구동 흐름은 포함하지 않는다.
- 계수는 사용자가 제공하고 적용성을 검토한다. 라이브러리가 재료·전해질별 값을 추정하지 않는다.
- 정상상태 해는 과도응답, 경쟁 반응, 흡착·탈착, 역반응, 침전/용해, 전기화학 반응 또는 형상 되먹임을 나타내지 않는다.
- 질량수지 잔차가 작다는 사실은 물리 계수의 적절성, 모델 적합성 또는 실험 검증을 뜻하지 않는다.

## 통합과 상태

이 파일은 새 독립 모듈이다. 중앙 registry, JSON schema export, capability/source catalog 연결은 상위 작업에서 수행한다. 테스트, 계산 실행, 패키징은 아직 수행하지 않았다.

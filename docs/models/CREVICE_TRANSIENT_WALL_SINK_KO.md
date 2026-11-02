# 막힌 틈 단일종 과도 확산–벽면 소모 모델

## 목적과 적용 범위

`matintegrity.crevice_transient_wall_sink.v1`은 길이 `L`의 고정된 1차원 blind slit에서 한 용존종의 과도 농도를 계산한다. 지배식은 일정한 유효 확산계수와 일정한 1차 벽면 소비를 갖는 선형 확산–반응식이다. 입구 농도는 일정하고 막힌 끝은 무유량이며, 초기 농도는 틈 전체에서 입구 농도와 같아야 한다.

계산 결과는 사용자가 요청한 시간·위치에서 유한 개수의 고유함수 항을 합한 값이다. 항 개수는 입력 계약의 일부이며, 결과를 무한 급수의 정확해, 오차가 보장된 근사, 수렴 증명 또는 물리적 검증으로 해석하지 않는다.

## Python API

```python
from matintegrity.crevice_transient_wall_sink import (
    CreviceTransientWallSinkRequest,
    evaluate_crevice_transient_wall_sink,
)
```

주요 입력은 다음과 같다.

- 대상 식별: `asset_id`, `location_id`, `geometry_id`, `species_id`, `condition_id`
- 형상·물성: `length_m`, `effective_diffusivity_m2_s`, `wall_area_per_volume_m_inv`
- 벽면 반응: `wall_transfer_velocity_m_s` — 용액 농도에 곱하는 비가역 선형 소비 속도 계수
- 경계·초기값: `mouth_concentration_mol_m3`; 초기 농도도 이 값과 동일하다고 제한한다.
- 표본 격자: `elapsed_times_s`, `sample_positions_m` — caller 순서를 유지한다. 시간은 엄격히 증가해야 하고, 위치는 `0..L` 안이어야 한다.
- 수치 절단: `eigenfunction_term_count` — 1부터 2000까지 caller가 명시한다.
- 근거와 리뷰: 여섯 적용 플래그와 하나 이상의 `Evidence`

시간·위치 표본 수는 각각 200 이하이며 `시간 수 × 위치 수 × 항 수`는 500,000 이하로 제한한다. 어느 리뷰가 빠지면 `needs_data`를 반환한다. 비유한 계산값이 생기면 미완성 시간행은 버리고 성공한 완전 시간행만 prefix로 반환하며, 첫 실패 위치를 기록한다.

## 해의 구성

```text
∂C/∂t = D ∂²C/∂x² − k_w a_w C
C(0,t) = C₀
∂C/∂x(L,t) = 0
C(x,0) = C₀
λ = sqrt(k_w a_w / D),  φ = λL
αₙ = (n + 1/2)π
```

정상상태 해를 `C_s(x)`라 할 때 요청 농도는 아래 유한합으로 계산한다.

```text
C_s(x) = C₀ cosh(λ(L−x)) / cosh(λL)
C_N(x,t) = C_s(x) + Σ[n=0..N−1] Bₙ sin(αₙ x/L) exp(−rₙ t)
Bₙ/C₀ = 2φ² / {αₙ(αₙ² + φ²)}
rₙ = D(αₙ/L)² + k_w a_w
```

`k_w=0`이면 sink가 없는 연속 극한을 적용한다. 정상상태 농도비는 큰 `φ`에서 쌍곡선 함수의 오버플로를 피하도록 지수형 비율로 계산한다. 극단적 입력이나 모드 감쇠율이 부동소수점 표현 범위를 넘으면 값을 잘라 반환하지 않고 `out_of_scope`로 처리한다.

## 결과 해석

`concentration_rows`는 요청한 시간순으로 각 위치의 `mol/m^3` 농도를 담는다. `eigenfunction_indices`와 `mode_decay_rates_per_s`는 실제 합산에 사용한 항의 범위를 기록한다. `input_sha256`, 대상 식별자, 근거 및 적용 리뷰도 함께 반환한다.

- `finite_truncated_expansion`은 유한합임을 표시한다.
- `exact_solution_claimed`, `truncation_error_bound_provided`, `convergence_proven`은 모두 `false`다.
- 시간·위치 격자 또는 항 개수를 바꾼 결과 비교는 사용자가 별도로 수행해야 하며, 차이가 작다는 것만으로 전 영역 오차가 보장되지는 않는다.

## 제한

- 종 하나만 다루며 전하수지, 복합체, 활동도, 경쟁 반응, 침전·용해 및 상 선택은 포함하지 않는다.
- 흐름, 압력구동 대류, 시간에 따른 물성, 형상 변화 및 벽면 피막은 포함하지 않는다.
- 벽면 속도 계수는 사용자가 제공한 유효 1차 법칙이다. 이 코드가 그 값을 데이터에서 적합하거나 부식속도·금속손실로 환산하지 않는다.
- 정상상태 또는 과도 농도 계산은 실험 검증, 재료 적용성, 안전 한계, 수명 또는 위험 확률을 증명하지 않는다.

## 상태

독립 계산 모듈과 한국어 개발 안내서만 추가했다. 중앙 registry, schema export, capability/source catalog 연결은 상위 작업에서 수행한다. 테스트, 실제 계산, 예제 실행 및 패키징은 수행하지 않았다.

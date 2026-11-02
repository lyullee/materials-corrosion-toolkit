# 크리비스 saturation 경로의 interval-average phase rates

## 목적

기존 saturation-driven `CompetingSolidKineticTransport`는 interval 끝의 saturation ratio에서 계산한 속도를 바로 앞 interval 전체에 적용한다. 이 adapter는 같은 caller rate law와 exact cell/knot saturation results를 쓰되, caller가 승인한 구간 내 선형 `S(t)` 경로를 수치 적분해 interval 평균 phase extent rate를 반환한다. 생성된 rate rows를 기존 `CellwiseCompetingSolidRateInterval` 형식으로 사용하면 inventory-limited phase ledger가 기존 보존 규칙을 계속 적용한다.

이것은 경계 업데이트를 덜 거친 방식으로 계산하는 bounded operator-split 대안이다. 시점별 chemistry와 phase reaction을 동시에 푸는 모델이 아니다.

## API

- Python 모듈: `matintegrity.crevice_saturation_interval_rate`
- 입력 계약: `CreviceSaturationIntervalRateRequest`
- 계산기: `evaluate_crevice_saturation_interval_rates()`
- ModelSpec: `specifications()`
- 모델 ID: `integration.crevice_saturation_interval_average_rates`
- source ID: `caller_crevice_saturation_path_average_rate`

요청은 typed `CompetingSolidKineticTransport` (saturation callback/rate-law mode), 각 transport output time의 `crevice_local_solid_saturation` 계산 결과 전체와 result SHA, quadrature order, review gates를 포함한다. 입력 시계는 transport output clock과 정확히 일치해야 한다. 각 knot에서 physical scope, time, all transport cells, candidate solid IDs, local temperature가 campaign과 일치해야 한다.

## 계산식 및 수치적분

기존 caller law는 침전 시 `k_p * max(S-1, 0)^n`, 용해 시 `-k_d * max(1-S, 0)^m`의 signed rate를 사용한다. Rate constants는 existing API 정의에 따라 고정 campaign 온도와 지원범위를 따른다. Saturation ratio `S`를 knot 사이에서 선형으로 재구성하며, interval 안에 `S=1` crossing이 있으면 그 지점에서 적분 구간을 나눈다. 각 부분은 caller 선택 Gauss-Legendre quadrature order(8..64, 기본 16)로 적분하고 duration으로 나눠 interval-average rate를 얻는다.

이 수치적분은 fixed finite-order 계산이다. 오차 추정/수렴 증명을 반환하지 않는다. Saturation ratio가 float 범위 밖이어서 upstream result가 `null`만 제공하면 계산은 범위 밖으로 닫힌다.

## 기존 workflow 적용

출력 `intervals` 각각은 `interval_id`, 시작/종료 시각, `phase_extent_rate_mol_m3_s_by_cell`을 보유한다. 이를 `CellwiseCompetingSolidRateInterval`로 만들고 동일 kinetic campaign의 `phase_rate_laws`를 비워 `kinetic_intervals`로 대체하면 existing `solve_competing_solid_kinetic_transport`의 explicit rate mode로 넘길 수 있다. 단, 캠페인과 kinetic configuration, geometry, temperature가 같은지 caller가 유지해야 한다.

## 한계

상태 경로는 caller 제공 포화도와 해당 계산 모델에 조건부다. Linear `S(t)` 가정, fixed temperature 및 interval average rate를 입고 다음 ledger에서 inventory가 제한되는 operator split을 사용한다. 구간 안에서 고체량이 바뀌어도 `S(t)`를 업데이트하지 않는다. Precipitation amount prediction, phase selection, equilibrium, nucleation, transport feedback, geometry update, simultaneous flow/chemistry, corrosion rate 또는 risk/qualification claim은 포함하지 않는다.

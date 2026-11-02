# 크리비스 셀별 초과 포화도 노출 이력

## 목적

`crevice_local_solid_saturation`의 exact knot 결과를 이어 받아, 각 고체 후보와 공간 셀에서 `log10(Q/K)`가 양수인 부분만 시간 적분한다. 이 값은 caller가 검토한 시간 재구성에 따른 비교 지표로서 반응속도나 석출량을 제공하지 않는다.

모듈은 두 가지 요약을 반환한다.

- `positive_log10_saturation_exposure_s_by_solid_and_cell`: `max(0, log10(Q/K))`의 시간 적분 (`s`)
- `duration_above_saturation_s_by_solid_and_cell`: 재구성된 `log10(Q/K) > 0` 구간의 누적 시간 (`s`)

포화도 로그값을 각 knot 사이에서 선형으로 보고 양의 삼각형/사다리꼴 면적을 해석적으로 구한다. 계산은 시간축만 연결하며 셀 사이 혼합은 하지 않는다.

## API와 입력 계약

- Python 모듈: `matintegrity.crevice_saturation_exposure_history`
- 입력 형식: `CreviceSaturationExposureHistoryRequest`
- 절점 변환: `crevice_saturation_history_knot(saturation_result)`
- 평가 함수: `evaluate_crevice_saturation_exposure_history()`
- ModelSpec: `specifications()`
- 모델 ID: `integration.crevice_saturation_exposure_history`
- source ID: `caller_crevice_cell_saturation_exposure_reconstruction`

각 knot는 `elapsed_time_s`, 전체 계산 결과와 그 canonical SHA-256을 가진다. `crevice_saturation_history_knot()`은 계산된 포화 screen 결과의 경과시간을 읽고 digest를 만들어 knot 객체로 변환한다. 시간은 0에서 시작하고 엄격히 증가해야 한다. 모든 결과의 물리적 scope, exact 시간, 셀 순서, 고체 후보 식별자는 이력 전반에 걸쳐 같아야 한다. 후보 포화도 계산에서 후보 결과가 포화 지수에 따라 재정렬되어도 ID를 기준으로 정렬/대응한다.

최대 입력은 knot 5,000개, knot당 셀 200개, 후보 고체 100개다. 네 검토 gate가 필요하다: 선형 `log10(SI)` 재구성, exact knot/cell lineage, 후보 용해도 기준의 knot 간 일관성, 누적 지표가 속도식이 아니라는 해석 경계.

## 계산 및 실패 처리

각 구간의 좌우 포화 지수 `y0`, `y1`와 시간 간격 `dt`를 이용해 선형 함수의 양수 부분만 적분한다. 둘 다 0 이하이면 노출은 0이다. 둘 다 0 이상이면 사다리꼴 면적을 사용한다. 영점을 가로지르면 양의 삼각형 면적을 사용한다. 포화 초과 시간도 동일한 선형 영점 위치에서 계산한다.

입력 결과 digest 불일치, 시간/물리 범위 불일치, 셀/후보 ID 변경, 비유한 수치가 있으면 해당 지점에서 닫힌다. upstream 계산이 실패한 knot 이전의 완전한 결과는 prefix로 보존한다. 잘못된 digest와 비증가 시간은 입력 계약에서 거부한다.

## 해석과 제한

`log10(Q/K)`는 caller가 제공한 활동도 및 용해도 자료에 조건부다. 그 로그값의 선형 시간 경로도 별도 review 가정이다. 따라서 적분값은 “초과 포화도 크기와 지속시간을 함께 반영한 지표”로만 해석한다. 경험적 또는 이론적 반응률과 곱해 석출량으로 바꾸지 않는다.

이 API는 phase 선택, 평형 투영, 핵생성, precipitation/dissolution 양·속도, 고체 morphology, 공극률, 보호층, 부식률, failure probability 또는 acceptance를 추론하지 않는다. 후보 상과 용해도 데이터의 적용 온도/압력/조성/표준상태 및 사용권한은 caller가 관리해야 한다.

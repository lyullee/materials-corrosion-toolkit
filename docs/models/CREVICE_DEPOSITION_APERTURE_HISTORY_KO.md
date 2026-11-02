# 크리비스 침전 체적-간극 이력 어댑터

## 역할

`crevice_solid_volume_inventory`가 계산한 정확한 시점별 셀 solid volume per reference area를 명시적 슬릿 geometry와 연결해 간극 손실 지표를 만든다. 모듈 `matintegrity.crevice_deposition_aperture_history`는 고체량을 생성하거나 반응/수송을 풀지 않는다. 기존 recession 기반 aperture history와 별개인 침전 측 geometry adapter다.

입력 고체 체적률 `q`의 단위는 `m3/m2`이며 길이 차원이다. 셀의 고체 체적은 `V = q * A_ref`로 구한다. 이 API는 다음 두 값을 별도로 산출한다.

- 면적 평균 등가 간극 손실: `V / (transverse_width * cell_length)`
- covered patch 간극 손실: `V / (coverage * transverse_width * cell_length)`

두 번째 값은 전체 고체 체적을 검토된 침전 면 수에 균등 배분한 뒤 각 covered face의 layer 두께로 바꾸고, 면 수만큼의 두께를 간극에서 차감한다. 따라서 수학적으로 covered patch 손실은 `V/(coverage*plan_area)`와 같지만 결과에는 face count를 사용한 가정이 명시된다. Coverage가 0인 셀에 고체 체적이 양수이면 범위 오류로 끝난다.

## 입력과 lineage

요청 형식은 `CreviceDepositionApertureHistoryRequest`, 평가 함수는 `evaluate_crevice_deposition_aperture_history()`, 모델 specification 함수는 `specifications()`이다. 모델 ID는 `integration.crevice_deposition_aperture_history`, source ID는 `caller_crevice_deposition_aperture_geometry_mapping`이다.

필수 geometry 값은 셀별 시작 aperture, 셀 길이, 횡방향 폭, solid volume 결과의 기준 면적, 침전 면 수(1 또는 2), 셀별 coverage fraction이다. 요청은 최소 한 개의 시간 knot를 요구한다. 시간은 정확히 0에서 시작해 엄격히 증가해야 한다. 각 knot는 solid volume API의 전체 계산 결과와 그 canonical digest를 포함한다. Adapter는 결과의 `physical_scope_id`, `elapsed_time_s`, 셀 개수를 요청 geometry와 대조한다.

다음 review gate가 모두 참이어야 계산한다: 시작 geometry 및 셀 대응, 기준 면적 환산, 침전 면 수 및 균등 배분, 셀 내 coverage 균일성, upstream 결과 lineage, 음수 간극에서의 fail-closed 경계. 값이 맞지 않으면 적합한 knot prefix만 보존하고 첫 실패 knot/cell을 반환한다. 음수 gap은 0으로 자르지 않는다.

## 결과 해석

각 knot에는 `equivalent_mean_aperture_loss_m_by_cell`, `equivalent_mean_remaining_aperture_m_by_cell`, `covered_patch_aperture_loss_m_by_cell`, `covered_patch_remaining_aperture_m_by_cell`가 포함된다. `coverage=0`이고 solid volume도 0이면 covered-patch 결과는 `null`이다.

등가 평균 gap은 셀 체적 보존에 따른 평균 지표다. covered-patch gap은 각 셀 안에서 coverage가 균일하며 침전 체적이 선언된 얼굴에 같은 양으로 나뉜다는 가정의 국소 값이다. 두 결과 모두 셀 내부의 실제 침전 위치 분포를 제공하지 않으며 부분 피복 경계의 유동을 모델링하지 않는다.

## 범위와 제한

이 API는 단순 기하학 mapping만 한다. 침전/용해 반응속도, 상평형, 고체 재배치, 공극률, 층 균열, 부착력, 보호성, 벽면별 비대칭 분포, 압력-유량 변화, transport 재계산을 계산하지 않는다. 각 시간 knot는 독립된 exact snapshot으로 처리되며 중간 시점 보간이나 동역학을 만들지 않는다. 이후 수송 계산에 연결하려면 caller가 어떤 aperture 지표를 geometry 입력으로 채택할지 review하고 그 geometry에 맞는 후속 solver를 별도로 실행해야 한다.

기준 면적과 셀 planform 면적은 서로 다른 quantity이므로 변환을 위해 모두 명시한다. caller는 upstream `m3/m2` 결과가 실제 제공한 `reference_area_m2`에 대응하는지 확인해야 한다. 제시한 coverage 또는 face count가 실측/도면/검토 근거와 맞지 않으면 결과는 물리적 deposit 형상을 나타내지 않는다.

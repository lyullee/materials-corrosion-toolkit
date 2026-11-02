# 고정 형상 크리비스의 다성분 전기중성 확산

## 목적

`transport.crevice_electroneutral_multispecies_diffusion_1d`는 사용자 정의 양·음이온 집합의 1차원 확산을 유한체적법으로 적분한다. 각 셀 경계에서 희석용액 Nernst–Planck flux와 영 전류 조건을 함께 적용해 무차원 전위 기울기를 계산하므로, 단일 중성성분 Fick 확산과 구별된다.

## 입력과 결과

`CreviceElectroneutralDiffusionRequest`에 길이·단면·셀 수, 초기 셀 농도, 종별 전하·확산계수·원소 조성, 정확히 정렬된 시간 knot와 mouth 경계농도 이력을 제공한다. 초기 조성과 모든 mouth 경계 knot는 전기중성이어야 한다. 유효 희석용액 적용성, 고정 형상, 무반응 구간, 국소 전기중성과 영 전류, parameter support 및 사용권 근거 검토를 caller가 명시한다.

출력은 각 계산 knot의 종별 셀 농도와 재고, 셀별 전하 잔차, 종별 유한체적 재고 폐합 잔차, 영 전류 잔차와 계산 진단을 포함한다. 수치 잔차는 물리 검증 증거가 아니다.

## 수치 모델

각 면의 농도 구배와 종별 확산계수로부터 전류 조건

`sum_i(z_i J_i) = 0`

을 만족하는 dimensionless potential gradient를 구해 각 종의 면 flux에 반영한다. 농도는 셀 중심에 두고 face flux 발산을 적분한다. 입구에서는 caller가 지정한 농도 이력을 시간 knot 사이 선형 보간하며, 막힌 끝단은 무유량이다. SciPy BDF를 사용하며 결과 시간은 caller knot에만 반환한다.

## 범위 경계

- 고정 형상, 일정 확산계수, 희석용액 근사, 한 개 액상상, 명시 종만 포함한다.
- 유동, 반응, 종분화, 이온강도/활동도, 전극 전류, 침전·용해, 벽 반응 및 움직이는 경계를 계산하지 않는다.
- 모든 초기 셀 및 입구 knot에 대해 전기중성을 요구한다. 비중성 축적전하와 이중층은 범위 밖이다.
- 이 모델은 부식률·국부 금속손실·수명·고장확률·검사 합격 판정을 산출하지 않는다.

## API 식별자

- Model ID: `transport.crevice_electroneutral_multispecies_diffusion_1d`
- Provider source ID: `caller_crevice_nernst_planck_species_transport`
- Boundary source ID: `caller_crevice_electroneutral_boundary_history`
- 계산 basis: `finite_volume_zero_current_nernst_planck_transport`
- Python API: `solve_crevice_electroneutral_diffusion(request)`

구현과 solver 회귀는 아직 실행 검증되지 않았다. 독립된 이온 수송 실험 및 격자·시간 간격 수렴 자료를 확보한 뒤 검증한다.

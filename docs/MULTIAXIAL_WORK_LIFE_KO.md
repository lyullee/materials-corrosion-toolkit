# 폐합 텐서 경로 일 기반 피로 수명

`fatigue.closed_tensor_work_life`는 호출자가 이미 분리한 폐합 3D 응력–변형률 cycle과 같은 재료상태에서 얻은 일 밀도–파단 cycle 수 보정점을 입력받아 cycle별 손상과 선형 Miner 합을 계산한다. 자동 cycle extraction이나 일반 비비례 피로 법칙은 제공하지 않는다.

## 입력과 계산

응력 배열은 Pa, 변형률 배열은 무차원이며 각 행의 순서는 `[xx, yy, zz, xy, yz, zx]`다. 응력·변형률·표본 ID는 같은 시각 순서로 정렬해야 하고, 각 cycle은 최소 3개 점을 가지며 첫 점과 마지막 점의 닫힘 오차를 선언한 허용치 안에 둬야 한다. `strain_shear_convention="engineering"`이면 전단 항에 추가 계수를 곱하지 않고, `"tensor"`이면 응력–텐서 변형률 contraction의 대칭 전단 두 성분을 반영해 2를 곱한다.

기본 `piecewise_linear` 경로는 구간 평균 응력과 변형률 증분 contraction의 trapezoidal 적분을 사용한다. `piecewise_cubic_hermite`는 각 표본 시각과 응력·변형률 양 끝의 시간 미분을 caller가 명시한다. `piecewise_pchip`은 엄격히 증가하는 caller 시각과 표본값에서 Fritsch–Butland 형상보존 knot 기울기를 계산하고, 별도 미분 입력은 거절한다. `piecewise_periodic_cubic_spline`은 SciPy 주기 cubic spline으로 표본 사이 경로를 구성하며, 첫·끝 응력 및 변형률 벡터가 정확히 같고 모든 시각이 엄격히 증가해야 한다. 이 모드는 별도 `periodic_spline_reviewed` 확인을 요구한다. spline은 주기 경계조건으로 내부 구간만 평가하며 외삽하지 않는다. 세 조각별 3차 경로의 `integral(sigma : d epsilon)`는 정의된 구간 다항식의 곱을 정확 적분한다. 각 보간은 별도 재구성 검토가 필요하다. PCHIP의 성분별 형상보존성과 주기 spline의 C2 매끄러움은 수치 보간 성질이며 물리 경로의 참값이나 피로법칙의 자격화를 보장하지 않는다. 절대 폐합 일 밀도를 보정 곡선에 대응시키고, 일 밀도와 파단 cycle 수의 로그–로그 좌표 사이를 선형 보간한다. 입력 보정점은 양수이고 에너지 순으로 엄격히 증가하며 수명은 엄격히 감소해야 한다. 계산은 보정 범위를 벗어나 외삽하지 않는다. 각 cycle의 할당 횟수를 해당 보간 수명으로 나누고, 모든 cycle이 유효할 때만 Miner 손상을 합산한다.

## 검토 조건과 한계

계산 전 tensor 기저·성분 순서, 응력–변형률 conjugacy, cycle boundary/closure, 선택한 시간 재구성(주기 spline은 전용 검토 플래그), cubic derivative 의미(해당 시), 재료 보정 적용성, work-life fit 및 Miner 규칙에 대한 호출자 검토가 필요하다. SciPy가 설치되지 않은 환경에서 주기 spline을 선택하면 해당 cycle은 계산 불가로 처리된다. 재료 조건 ID가 cycle 이력과 보정 자료에서 정확히 같아야 한다. 결과에는 이력·보정 SHA-256과 전체 입력 digest가 보존된다.

폐합 경로 적분이 비례·비비례 하중의 재료 손상량이라는 보편적 법칙은 아니다. cubic Hermite의 정확성은 caller가 준 미분으로 정의된 다항식 적분에 한정된다. PCHIP의 형상보존성과 주기 spline의 매끄러운 주기 폐합은 성분별 수치 보간 특성에 대한 것이며 텐서 경로의 물리 형상이나 실험 재현성을 보장하지 않는다. 어느 방법도 실제 미계측 하중 경로를 복원하거나 내삽법을 자격화하지 않는다. 부호 방향 효과, 평균응력 효과, 온도·환경 효과, 이력 상호작용, rainflow cycle 정의, 시험 runout·검열 처리와 코드 허용기준은 이 API가 추론하지 않는다. 허용치 초과, 0 일, 비유한 적분 또는 보정 범위 외 cycle이 있으면 전체 손상합을 반환하지 않는다. 제공 예제는 synthetic fixture이며 검증 근거가 아니다.

## 예제

`examples/model_inputs.json`의 `fatigue.closed_tensor_work_life` 항목은 piecewise-linear 요청을 보여준다. `examples/pchip_tensor_work_life.py`와 `examples/periodic_spline_tensor_work_life.py`는 같은 synthetic cycle을 각 재구성 방식에 연결하는 예시다. 실제 사용 시에는 프로젝트가 적법하게 사용할 수 있는 cycle 이력 및 동일 재료 상태의 보정 자료로 synthetic 값과 digest를 교체한다.

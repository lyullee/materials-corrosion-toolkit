# 유한 표본 Crossland 비례응력 한도 스크린

## 목적

`fatigue.multiaxial_crossland_proportional_limit_screen`은 닫힌 한 주기의 대칭 응력 텐서 표본을 받아, 비례응력 경로가 명시한 허용오차 안에 있을 때 caller가 제공한 Crossland 계수와 한도에 비교한다. 이 계산은 고주기 피로 한도 스크리닝이며 수명 예측 API가 아니다.

Crossland 형태의 지표는 편차응력 제2불변의 진폭과 주기 중 최대 정수압 응력을 합성한다. 구현은 통상적인 연속 비례경로 계산을 임의 표본에서 일반 비례경로 전체로 확대하지 않는다. 주어진 표본에 대해서만 편차응력 경로가 한 직선 위에 있는지 확인하고, 허용오차에 맞지 않는 경로는 거부한다.

## 입력 자료

- `SampledStressInvariantHistory`: 재료상태, 위치, 원자료 ID/SHA-256, 표본 ID와 `[xx, yy, zz, xy, yz, zx]` 순서의 응력(Pa)
- 정확히 같은 재료상태의 Crossland 계수 `hydrostatic_coefficient_alpha` 및 `caller_limit_beta_Pa`
- 시험/계산 자료의 `Evidence`, 원자료 SHA-256, 검토자가 선택한 `proportionality_tolerance_Pa`
- 닫힌 주기·응력 텐서 기저, 계수·한도, 재료 적용성, 비례경로 가정 검토 플래그

역사 입력은 양 끝 응력 텐서가 동일한 닫힌 주기여야 한다. 단위는 응력값 및 β가 Pa이다. α는 무차원 비음수로 둔다. 재료·열처리·온도·환경과 시험 범위가 일치하는 α와 β를 호출자가 제공해야 한다. 기본 물성값이나 문헌 계수는 탑재하지 않는다.

## 수치 절차

1. 각 응력 표본에서 평균 법선응력을 빼 편차응력 텐서를 만든다.
2. 모든 표본쌍 중 `sqrt(J2)` 거리의 가장 먼 두 점을 찾아 후보 직선 방향을 설정한다. 작업량은 모든 쌍 개수에 비례하며 `maximum_pair_evaluations`로 제한한다.
3. 각 편차응력 표본의 후보 직선 수직 거리를 계산한다. 최대 잔차가 caller 지정 절대 허용오차를 넘으면 `out_of_scope`를 반환한다.
4. 직선 좌표의 표본 최소/최대 차이 절반을 `sqrt(J2)` 응력 진폭으로 사용하고, 모든 표본에서 최대 정수압 응력 `σH,max`를 취한다.
5. `sqrt(J2)_a + α σH,max`를 caller의 β와 비교해 값과 여유를 반환한다.

## 상태 및 해석

- `computed`: 입력과 리뷰 조건이 충족되어 유한 표본 계산을 마침. `caller_limit_not_exceeded`/`caller_limit_exceeded`는 caller 한도와의 산술 비교 결과다.
- `needs_data`: 기저, 주기, 재료 적용성, 보정, 또는 비례경로 검토가 빠짐.
- `out_of_scope`: 검색 작업량 초과, 비례성 잔차 초과, 또는 유한성/산술 조건 실패.

비례 경로 잔차는 `sqrt(J2)` 내적을 사용한 거리이므로 Pa 단위다. 직선은 최대거리 표본쌍으로 정하며, 동률일 때는 먼저 발견된 쌍을 사용한다. 데이터에 기초한 tolerance를 정하고 그 근거도 별도 Evidence에 기록한다. 자동으로 경로를 투영해 비례응력으로 바꾸지는 않는다.

## 적용 경계

- 비례성은 caller tolerance를 만족하는 유한 편차응력 표본의 직선성이다. 이 판정으로 표본 사이의 경로까지 비례하다고 증명하지 않는다.
- 비례성을 벗어난 응력 경로는 거부한다. 비례응력 진폭 계산을 비비례 하중에 전용하지 않는다.
- 숨은 극값, 연속시간 보간, 반복 계수, 변동진폭 손상, 순서효과, 주기수명, 고장확률, 규격 합격 또는 재료 적격을 추론하지 않는다.
- `caller_limit_exceeded`는 입력된 모델 기준을 넘었다는 의미에 한정된다. 별도의 설계 기준상 판정이나 안전성 선언이 아니다.

## 근거 및 출처

- 방법 문헌: B. Crossland, “Effect of large hydrostatic pressures on the torsional fatigue strength of an alloy steel,” *Proceedings of the International Conference on Fatigue of Metals*, IMechE, London, 1956, pp. 138–149.
- 식 형태 및 최근 정리 참고: [Validation of Multiaxial Fatigue Strength Criteria on Specimens from Structural Steel in the High-Cycle Fatigue Region](https://www.mdpi.com/1996-1944/14/1/116), *Materials* 14(1), 116 (2021).
- 교차 참조용 이론 설명: [Code_Aster Crossland, Dang Van and Papadopoulos criteria](https://docaster-en-codeaster-doc-4113bb35b8213385c636b94f1536856d7f617.gitlab.io/manuals/man_r/r7/r7.04.01/Crit_res_de_Crossland_et_Dang_Van_Papadopoulos.html).

문헌과 소프트웨어 문서는 방법의 출처를 설명한다. 이 패키지는 문헌 원문, 표, 그림 또는 재료별 시험 자료를 재배포하지 않는다. 계수와 한도는 caller가 제공한다.

## API 연결

- Model ID: `fatigue.multiaxial_crossland_proportional_limit_screen`
- 입력: `MultiaxialCrosslandProportionalLimitScreen`
- 계산: `evaluate_multiaxial_crossland_proportional_limit_screen(request)`
- Source IDs: `caller_crossland_finite_proportional_limit_calibration`, `crossland_1956_hydrostatic_pressure_torsional_fatigue_criterion`

일반 Python 흐름은 `ModelRegistry.evaluate(...)`에 이 입력 계약을 전달하는 방식이다. Registry, catalog, public schema, source basis, API 색인, package catalog 및 scope 감사 연결은 완료되어 있다. 수치 실행과 independent scientific validation은 아직 별도 과제다.

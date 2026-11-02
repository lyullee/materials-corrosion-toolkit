# 습윤 CO₂ 기상–탄산 알칼리도 과도 평형 이력

## 목적

정적 탄산 알칼리도 계산 API와 유한 기상 CO₂ 전달 모델을 이력 계산에서 연결한다. 기상–액상 교환으로 변하는 총무기탄소(DIC)와 caller가 지정한 wall/waterborne 탄소 및 알칼리도 flux를 시간 적분한다. 각 ODE 상태 평가에서 해당 시점의 DIC와 총알칼리도로 carbonate-only 산·염기 평형을 다시 풀어 CO₂* 농도를 구하고, 그 값을 기상 전달 구동력에 사용한다.

상위 등록용 Model ID: `integration.wet_co2_transient_gas_carbonate_alkalinity_equilibrium`.

## API

모듈: `matintegrity.wet_co2_transient_carbonate_gas_equilibrium`

- `WetCo2TransientCarbonateInterval`: 하나의 정확한 시간 구간에 적용할 온도, 조건부 평형상수, Henry 관계, 기상-액상 전달속도, 액량 변화, 유입 조성 및 wall 탄소/알칼리도 flux와 Evidence.
- `WetCo2TransientCarbonateHistoryRequest`: 유한 기상 용량, 초기 DIC·알칼리도·액량, wall area, 구간 기록 및 검토 선언.
- `evaluate_wet_co2_transient_carbonate_history(request)`: DOP853로 기상 fugacity와 액상 재고를 과도 적분하고 각 내부 단계에서 탄산 평형을 재해석한다.
- `specifications()`: 상위 registry 통합용 `ModelSpec` 선언.

## 평형 계산

주어진 액상 DIC `Cₜ`, 수소 이온 농도 `H`, caller 조건부 농도 평형상수 `K₁`, `K₂`에서 탄산 종 분배는 denominator `Q = H² + K₁H + K₁K₂`에 대해 다음과 같이 계산한다.

`[CO₂*] = Cₜ H²/Q`

`[HCO₃⁻] = Cₜ K₁H/Q`

`[CO₃²⁻] = Cₜ K₁K₂/Q`

`[OH⁻] = K_w/H`

caller가 제공한 알칼리도는 carbonate-only 관계 `Aₜ = [HCO₃⁻] + 2[CO₃²⁻] + [OH⁻] − [H⁺]`를 만족해야 한다. 지정 pH bracket에서 이 방정식을 이분법으로 풀고, 얻은 CO₂*로 기상 전달량을 계산한다.

## 과도 물질수지

기상 fugacity `f`, 기상 몰용량 `β`, 총 유효 전달속도 `k`, Henry 관계 `Hc/f`, 액체 부피 `V`, 벽면적 `A`에서 gas-liquid CO₂ 몰전달속도는 다음이다.

`Jgl = A k ((Hc/f) f − [CO₂*])`

양의 `Jgl`은 기상에서 액상으로 들어가는 방향이다. DIC 재고는 이 전달량과 caller wall-carbon flux 및 유입·유출량을 합산한다. 알칼리도 재고는 중성 CO₂ 전달에는 영향을 받지 않고 caller wall-equivalent flux 및 물 유입·유출량만 반영한다. 기상 fugacity 감소율은 `df/dt = −Jgl/β`이며 유한 기상 재고와 DIC의 합산 탄소수지를 매 구간 확인한다. 알칼리도 재고수지도 별도로 확인한다.

양의 액량 유량 `q`는 균일 혼합 유입이며, 음수는 순간 벌크 농도로 유출되는 well-mixed 출구다. 입력 시간 구간의 조건과 source flux는 구간 동안 일정하다. knot 사이 보간은 수행하지 않는다.

## 입력 계약 및 계보

| 변수 | 단위 |
|---|---|
| DIC, 총알칼리도, carbonate 종 | mol/m³ |
| 기상 fugacity | Pa |
| 기상 몰용량 | mol/Pa |
| 액량, 벽면적 | m³, m² |
| Henry 농도/fugacity 계수 | mol/(m³·Pa) |
| 가스-액 전달속도 | m/s |
| 액량 유량 | m³/s |
| wall 탄소 flux | mol/(m²·s) |
| wall 알칼리도 flux | mol-equivalent/(m²·s) |
| 온도 | K |
| 시간 | s |

조건부 `K₁`, `K₂`, `Kᵥ`, wall flux, 초기상태마다 공급자·revision·record ID 및 SHA-256 Evidence를 명시한다. 각 조건 상수와 wall flux는 해당 구간 온도·용액 조건과 시간/asset/면적 기준이 일치해야 한다. pH 범위 밖으로 벗어나거나 액량·재고·수지가 유효 범위를 벗어나면 성공 prefix를 남기고 해당 구간에서 중단한다.

## 범위와 물리적 한계

- Carbonate-only 평형이며 입력 조건부 상수는 이상 농도 convention을 가정한다. 활동도계수와 비이상성은 이 모델에서 계산하지 않는다.
- 총알칼리도에 포함된 비탄산 완충종(암모니아, 인산, 붕산, 규산, 유기산 등)과 counterion을 추론하지 않는다. 전체 용액 전기중성 또는 완전한 aqueous reaction network를 보장하지 않는다.
- 온도별 평형상수, Henry 계수와 전달속도는 caller가 구간별 제공한다. 온도의존 법칙을 추론하거나 상수 간 interpolation을 하지 않는다.
- 적분 중 carbonate equilibrium은 준정상 평형으로 즉시 따라온다고 가정한다. 실제 수화·탈수 반응 지연이나 기타 화학 kinetics를 풀지 않는다.
- wall flux는 총 탄소와 전하당량의 외부 경계 source다. 이 모듈은 그것이 전기화학 반응에서 어떻게 계산되었는지 역추론하지 않으며 금속 손실, 부식속도 또는 scale 침전을 계산하지 않는다.
- 매 구간에서 균일혼합 액상과 유한 단일 기상을 가정한다. 기포 분산, 축방향 분포, 계면 저항망, 고체상의 평형은 미포함이다.
- 결과는 모델 계산이며 실험 검증, 설계승인 또는 부식 위험도 판정이 아니다.

## 독립 구현 및 권리

구성식, 계산 구현 및 설명서는 입력된 조건부 carbonate 상수와 일반 물질수지로 독립 작성했다. 외부 문서의 문장·표·수치 데이터를 복사해 포함하지 않는다. 공개 데이터나 실험값을 호출자가 적용하는 경우 원 출처 이용허가, license 및 redistribution 조건을 별도로 따라야 한다.

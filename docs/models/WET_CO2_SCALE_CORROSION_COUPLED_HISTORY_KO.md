# 습윤 CO₂ scale 성장–전기화학 부식 이동경계 이력

## 목적

이 API는 시간 구간마다 현재 scale 두께를 확산막 두께로 반영해 습윤 CO₂ 전기화학 혼합전위를 다시 계산하고, 계산된 양극 금속 용해로 인한 벽 두께 감소와 caller가 지정한 scale 생성·용해를 함께 갱신한다. 다음 구간에서는 갱신된 scale 두께를 사용하므로, scale 상태가 후속 반응물 전달 제한에 영향을 준다.

상위 등록용 Model ID: `integration.wet_co2_scale_corrosion_moving_geometry_history`.

## API

모듈: `matintegrity.wet_co2_scale_corrosion_coupled_history`

- `WetCo2MetalToScaleYield`: 전극 반응 extent에서 용해 금속량, 질량, 밀도, scale 수율로 이어지는 caller 자료.
- `WetCo2MovingScaleInterval`: 구간별 탄산계 경계/Butler–Volmer/전달 요청과 별도 scale net flux.
- `WetCo2ScaleCorrosionMovingGeometryHistoryRequest`: 초기 벽·scale 두께, scale 몰부피, 증거자료, 반응 매핑 및 연속 시간 구간.
- `evaluate_wet_co2_scale_corrosion_moving_geometry_history(request)`: 구간마다 계산을 재실행하고 벽·scale 상태를 전진시킨다.
- `specifications()`: 상위 registry에 넘길 `ModelSpec` 선언.

## 구간 계산

구간 시작에서 이전 단계의 scale 두께 `Lₛ`를 `WetCo2TransportLimitedMixedPotentialRequest` 내 각 반응물 막 두께로 적용한다. 기존 막수송 제한 혼합전위 API가 caller의 농도·확산계수·Butler–Volmer 계수로 전위와 부분전류를 구한다. 이 반응률은 해당 구간에서 일정하다고 본다.

반응 `r`의 양극 extent 플럭스를 `ξ̇ᵣ`, 반응 extent당 용해 금속 원자 수를 `aᵣ`라 하면 용해 금속 flux는 `Ṅₘ,ᵣ = aᵣ ξ̇ᵣ`다. 금속 molar mass `Mᵣ`, 밀도 `ρᵣ`를 사용해 면적평균 벽 감소율을 합산한다.

`Δt_wall = Δt Σᵣ (Ṅₘ,ᵣ Mᵣ / ρᵣ)`

scale 생성은 두 경로로 표현한다. 첫째는 caller가 반응별로 제공한 용해 금속 1 mol당 생성 scale mol 수 `yᵣ`를 통한 `Σᵣ yᵣ Ṅₘ,ᵣ`, 둘째는 별도의 caller 제공 외부 순 scale flux `Jₛ,ext`다. scale 몰부피 `Vₘ`를 적용한 면적 inventory·두께 업데이트는 다음과 같다.

`Nₛ,end/A = Lₛ,start/Vₘ + Δt (Σᵣ yᵣ Ṅₘ,ᵣ + Jₛ,ext)`

`Lₛ,end = Vₘ (Nₛ,end/A)`

`T_wall,end = T_wall,start − Δt_wall`

외부 순 flux의 양수 부호는 scale 생성, 음수는 용해다. 기존 scale 재고를 초과하는 용해나 벽 두께 고갈은 구간에서 `out_of_scope` 처리하고, 앞선 성공 구간 이력과 ledger를 반환한다.

## 요구 증거와 단위

입력 확산/반응 파라미터는 기존 `WetCo2TransportLimitedMixedPotentialRequest` 계약을 따른다. scale 몰부피는 m³/mol; 초기 및 계산 두께는 m; scale·금속 면적 inventory는 mol/m²; 양극 금속 flux는 mol/(m²·s); 금속 질량 flux는 kg/(m²·s); 시간은 s다. 반응별 금속- scale 수율, molar mass, density, scale molar volume, 외부 scale flux는 caller 소유이며 공급자·revision·record ID 및 SHA-256 Evidence를 포함해야 한다.

초기 scale이 wall에 붙어 있고 평면 면적 기준을 공유하는지, 금속 부피 가산성, 금속-반응 및 금속-scale 화학량론, 각 경계와 반응의 시계·asset 범위가 맞는지 검토 플래그로 선언한다. 데이터가 없으면 계산하지 않고 `needs_data`를 반환한다.

## 물리적 경계와 사용상 주의

- 이 계산은 **구간 단위 sequential operator split**이다. 구간 시작의 scale 상태로 전기화학을 풀고, 그 속도로 구간 끝 scale/벽 상태를 갱신한다. 구간 내부에서 두께 변화가 전류에 다시 연속 피드백되지 않는다.
- scale 전체 두께를 각 제한 종의 확산막 두께로 사용한다. 이 단순화가 맞는지, `D`와 적용 농도 차이가 해당 scale에 적합한지는 사용자가 검토해야 한다.
- 용해 금속에 대한 scale 생성량과 외부 scale flux는 입력 자료다. 용해도, 침전, 부착·박리, 다상 조성, morphology 또는 보호효과를 모델이 추론하지 않는다.
- 벽 감소는 지정 면적에 대한 균일 평균이다. 국부부식 깊이, pit geometry, 비균일 scale, 지지력·응력 또는 pressure-boundary 적합성을 산출하지 않는다.
- 전기화학 법칙은 이미 보정·검토된 caller Butler–Volmer 자료에 의존한다. 이 모델은 온도나 CO₂ fugacity로 교환전류, 평형전위, 반응 경로를 만들지 않는다.
- 이력 구간 안에서는 조건과 flux가 일정하다고 보고 구간 knot 사이를 보간하지 않는다. 결과는 실험검증, 설계승인 또는 사용적합성 판정이 아니다.

## 독립 구현 및 데이터 권리

구현은 caller가 제공한 반응·재료 자료와 면적 물질수지, Faraday 변환, 밀도 기반 두께 갱신을 조합한 새 코드다. 외부 문헌의 서술이나 표를 복사해 포함하지 않는다. upstream 데이터셋, 실험 자료와 공급자 상수의 공개/재배포 조건은 각각의 원 출처 라이선스와 약관을 적용한다.

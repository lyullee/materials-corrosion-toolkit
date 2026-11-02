# 원통형 유한 기체–수용액 stage speciation·부식·scale 연성 모델

## API와 모듈 관계

- Model ID: `integration.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback`
- Schema: `matintegrity.wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback.v1`
- 요청: `WetCo2CylindricalFiniteGasStageSpeciationFeedback`
- evaluator: `evaluate_wet_co2_cylindrical_finite_gas_stage_speciation_scale_feedback`
- 기반 API: `integration.wet_co2_cylindrical_stage_speciation_scale_feedback`
- source IDs: `caller_finite_gas_cylindrical_two_film_transfer_and_inventory`, `finite_gas_aqueous_bv_scale_element_balance`, `caller_finite_gas_inventory_initial_state`, `finite_gas_and_outer_liquid_stage_inventory_flux_limit`, 그리고 기반 stage solver의 mass-action·BV·scale source IDs

기존 `integration.wet_co2_finite_gas_liquid_exchange_history`는 완전혼합 단일 액상 구획의 중성 CO₂ 교환을 해석해로 계산하지만 벽 반응이나 spatial chemistry를 포함하지 않는다. 기존 cylindrical finite-liquid ledger는 bulk–wall 전달을 정확한 knot별 기록으로 닫지만 BDF stage 상태를 풀지는 않는다. 이 모델은 두 API의 계산을 단순 연결하지 않고, 한 BDF 상태벡터에 기체 fugacity와 원통 액상 species profile, BV 누적량, 상 inventory를 함께 넣는다.

## caller가 지정하는 기체·전달 입력

caller는 다음을 명시하고 parameter digest와 Evidence를 제공한다.

- 중성·탄소 함유 transported aqueous species 한 종의 ID
- 초기 CO₂ fugacity `f₀` (Pa) 및 선형 기체 inventory capacity `β` (mol/(Pa·m axial))
- 기–액 접촉면적을 축방향 길이로 나눈 값 `A′` (m/m axial)
- Henry 계수 `H` (mol·m⁻³·Pa⁻¹)
- 기상막 계수 `k_g` (mol·m⁻²·s⁻¹·Pa⁻¹), 액상막 계수 `k_l` (m/s)
- 전달 계수 provider ID/revision, 초기 상태 digest와 licensed Evidence

transfer parameter SHA-256은 종 ID, `β`, `A′`, `H`, 두 막 계수, provider ID/revision을 함께 결속한다. 별도의 initial-state SHA-256은 assessment ID, 종 ID, 초기 fugacity와 기체 용량을 결속한다. 단계별 결과에는 두 digest, 상위 aqueous/BV 입력 digest, interval prefix가 남는다.

이 bounded 구현은 고정 `β`, `A′`, `H`, 막 계수와 고정 온도만 지원한다. knot 온도가 하나라도 달라지면 실패한다. Henry와 막 계수가 이 조건에 맞는지는 caller Evidence 및 review gate로 제시해야 하며 소프트웨어가 적합성을 인증하지 않는다.

## same-stage 결합식

기체막과 Henry 변환을 액상 농도 기준으로 나타내고 두 막 저항을 직렬 합성한다.

```text
k_g,H = k_g H
K_L = 1 / (1/k_l + 1/(k_g H))
J = K_L (H f − C_s)
dn_g/dt = −A′ J
df/dt = −A′ J / β
```

`C_s`는 caller가 선택한 중성 탄소 species의 BDF stage 외측 radial-cell 농도다. `J>0`은 기체에서 액상으로의 전달이다. `A′J`는 축방향 단위 길이당 molar rate (mol·m⁻¹·s⁻¹)다. 기체 전달종의 기존 prescribed bulk boundary flux는 끄고, 이 same-stage gas flux를 외측 cell의 species balance에 넣는다. 나머지 species는 기반 cylindrical solver의 radial transport 및 caller boundary를 그대로 사용한다.

유한 inventory 고갈을 막기 위해 stage의 양의 전달률은 남은 interval의 `β f`로, 역전달률의 절댓값은 같은 시간 동안 외측 액상 cell에 존재하는 전달종 몰수로 제한한다. 이는 caller transfer law에 추가한 유한 재고 보호 제한이며, 표면의 별도 반응 속도식으로 해석하지 않는다. stage에서 농도/fugacity가 음수이거나 유한 재고 제한 후에도 solver가 닫히지 않으면 해당 interval prefix와 함께 실패한다.

따라서 각 stage에서 기체 fugacity가 변하고, CO₂ 계열 aqueous species profile이 변하며, 외측에서 벽 방향으로 수송된 벽 인접 조성으로 mass-action solver가 다시 평형 활동도를 계산한다. 이 활동도는 phase precipitation/dissolution law에 들어가고, scale flux 및 BV species source/sink와 함께 동일한 BDF RHS에서 계산된다. 각 knot에서 상 inventory, wall alloy release 및 cylindrical bore radius가 기반 geometry Picard 반복으로 닫힌다.

## 수지와 실패 처리

interval `k`의 gas–liquid 전달량을 `T_k` (mol/m axial)라 두면 다음을 확인한다.

```text
β (f_end − f_start) + T_k = 0
```

기체 전달종의 수용액 장부는 `ΔN_i − N_outer − N_BV − N_scale − T_k = 0`이며 나머지 종은 기존 항만 포함한다. 각 원소별 global balance는 aqueous inventory 변화, scale phase 원소량 변화, gas inventory의 원소량 변화, radial external flow, BV wall release를 함께 사용한다. 내부 기–액 전달은 gas 및 liquid 장부에서 상쇄되어야 한다. 음수 fugacity, 고갈 또는 비유한 농도, 기존 BDF work cap 초과, gas inventory closure, species/charge/element/solid geometry closure 실패는 현재 interval의 세부 실패 이유와 완료 prefix를 포함해 닫힌다. 실패를 완성된 계산값으로 가장하지 않는다.

## 물리 범위와 제한

- 한 개의 caller 고정-capacity 기체 저장조와 중성 탄소 수용종 하나의 전달만 지원한다. gas 조성 변동, 다성분 gas, EOS, 압력용기 변형, 용기 유출, 가스 생성/반응은 계산하지 않는다.
- 기상 저장량은 `β f`로 표현되는 caller 지정 선형 재고다. EOS에서 압력, 부피, 온도에 따른 capacity를 추론하지 않는다.
- 기–액 전달은 caller 지정 고정 Henry 상수 및 두 막 계수를 사용하는 bounded law다. 계수의 실제 공정 적용성, 유효 농도 범위, gas composition correction은 caller 검토 사항이다.
- CO₂ speciation, activity model, 평형 반응 topology, scale 상과 kinetic law, BV 반응 및 wall alloy는 caller 제공 contract와 Evidence를 그대로 사용한다. 자동 종·상 생성은 하지 않는다.
- 액체 유동, 유한 bulk reservoir의 별도 상태, 배관 네트워크, 다상 유동, 기상내 확산, scale 내부 전달, nucleation, 신뢰성/수명 qualification은 범위 밖이다.
- 모델은 코드 수준의 결합 계산을 제공한다. 별도 수치 검증 및 공정 자료 검토 전에는 실측 검증 또는 설계 적격성을 주장하지 않는다.

## 개발·검증 후속 항목

별도 검증 시에는 (1) 무전달 `J=0`, (2) 기상→액상 및 역방향 전달, (3) 기체 inventory 고갈 경계, (4) 작은 시간간격의 해석적 2구획 교환과 비교, (5) CO₂ species·solid·gas 원소수지, (6) BV wall release와 Fe/C 등 원소수지, (7) mesh/radius geometry remap, (8) provider/initial-state digest 불일치, (9) bounded RHS와 mass-action work budget 경계를 확인해야 한다. 이 요청에서 테스트, package build, HPC 계산은 실행하지 않았다.

# 습윤 CO₂ 벽면 응축액 재고 이력

## 목적과 기존 모듈 연결

`integration.wet_co2_condensate_film_history`는 한 고정 벽면 patch에 대한 caller 제공 **net retained-water mass flux**를 적산해 액상 areal inventory와 uniform-equivalent film thickness 이력을 만든다. 기존 [`wet_co2_condensate_state`](WET_CO2_CONDENSATE_STATE_KO.md)는 벽 온도에서 열역학적 응축 가능성과 막 생기는 액상의 CO₂* 평형농도만 제공한다. 이 모듈은 물성·다상 solver가 제공한 응축·증발·배수·보유 효과의 net flux를 시간 재고로 연결한다.

관계식은 면적기준 질량수지에서 직접 유도한다. 문헌의 상관식, 임계 film thickness 또는 부식계수를 쓰지 않는다.

## 상태 업데이트

구간 `i`에서 caller net retained flux `j_i`와 밀도 `ρ_i`가 일정할 때, 물의 질량 재고를 면적당 `m_i`라 하면 유입만으로 계산한 후보는 다음과 같다.

```text
m_candidate = m_i + j_i Δt_i
m_(i+1) = max(0, m_candidate)
h_equivalent = m / ρ
```

음수 flux가 현재 inventory를 초과해 제거하려 하면 inventory는 dry-out에서 0으로 제한한다. 사용할 수 없었던 나머지 sink 요청은 별도 ledger에 남긴다. 양수는 표면에 retained된 물이 증가하는 부호 convention이다. 실제 condensation gross flux와 drainage/evaporation gross flux를 별도 제공받지 않으면 각각을 분해하지 않는다.

## 입력과 결과

- wall patch ID와 초기 수막의 면적당 물 재고 `kg/m²`
- 시간순 연속 구간별 상수 net retained flux `kg/(m²·s)`와 liquid water density `kg/m³`
- flux/density provider revision, configuration/result digest, Evidence 및 상태 검토 flag
- 각 경계의 물 재고 및 equivalent thickness, 구간별 wet duration/dry time, 누적 추가·제거량, dry-out 이후 미충족 sink 및 재고수지 잔차
- 전체 wet 시간과 최대 연속 wet 기간

시간별 flux가 사다리꼴/다른 재구성 방식으로 주어졌다면 caller가 적절한 구간별 평균 net flux로 바꾸고 그 변환 근거를 기록해야 한다. 이 API는 입력 구간 안의 변동을 재구성하지 않는다.

## 적용 가정 및 한계

- Flux는 총 생성량이 아니라 이 고정 면적에 실제 유지되는 **net flux**여야 한다. 바닥 배수, 증발, 물방울 부착·이탈, gas shear 등에 의한 영향은 upstream provider가 계산·측정해 하나의 flux로 공급한다.
- 각 interval의 net flux와 물 밀도는 piecewise constant다. 음수 flux는 있는 재고까지만 제거할 수 있다.
- `m/ρ`는 실제 droplet 형상·접촉각·부분 젖음 coverage를 모르는 상태의 균일막 등가 두께다. local minimum/maximum film thickness나 부식에 유효한 전해질 두께가 아니다.
- patch 밖으로의 lateral 유동은 제외한다. patch가 젖어 있는 시간은 재고가 양수인 시간 기준이며, 최소 부식 가능한 두께를 의미하지 않는다.
- 수막 chemistry, CO₂ 흡수, pH, carbonate scale, corrosion rate, wall loss 및 위험도는 계산하지 않는다.

## 출처·라이선스·검증

모듈은 일반적인 질량보존식만 독립 코드화했으며 외부 텍스트, 표, 자료 행 또는 경험상관식을 포함하지 않는다. 밀도·유량 provider의 배포 license와 측정 traceability는 각각 확인해야 한다. 이번 구현은 별도 검증 전 상태이며, 수치 검증과 실측 응축수 inventory 대조는 후속 검증 단계에서 수행한다.

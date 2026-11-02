# 습윤 CO₂ 유한 액상 재고의 기–액 전달 이력

## 목적

`integration.wet_co2_finite_liquid_transfer_history`는 처방된 기상 CO₂ fugacity와 caller가 제공한 Henry 계수 및 2막 계수로부터, 고정 부피의 잘 섞인 액상에서 중성 용존 `CO2*` 농도 이력을 계산한다. 기존 2막 API는 각 knot의 농도를 caller가 넣고 flux를 평가한다. 이 모듈은 그 관계를 유한 액상 재고에 연결해 다음 interval의 농도를 전달 flux가 직접 갱신하도록 한다.

기–액 두 막의 정상 계면저항 구성은 [Paolinelli–Nesic (2021)](https://doi.org/10.1016/j.ijheatmasstransfer.2020.120689)의 기–액 배관 물질전달 논의와 기존 [2막 계산 API](WET_CO2_TWO_FILM_TRANSFER_KO.md)에 기반한다. 논문은 출판 저작권이 유지되는 자료이므로 원문, 그림, 실험값은 복사하거나 배포물에 넣지 않는다. 액상 재고의 시간 업데이트는 아래 물질수지에서 독립적으로 유도했다.

## 방정식과 exact interval update

한 interval에서 Henry 계수, 기체 fugacity, 접촉면적, 액체 부피, 두 막 계수가 일정하다고 둔다. 전체 저항은 액상 농도 기준으로 환산한다.

```text
K_L = 1 / (1/k_l + 1/(k_g H))
C_eq = H f_CO2
dC_CO2*/dt = (A/V) K_L (C_eq − C_CO2*)
```

계수 `lambda = (A/V) K_L`과 interval 길이 `dt`에 대해 해는

```text
C_1 = C_eq + (C_0 − C_eq) exp(−lambda dt)
Δn_liquid = V (C_1 − C_0)
```

이다. 따라서 부호 있는 액상 전달량은 별도 flux 근사 적분 없이 액상 재고 차로 얻는다. 양수는 gas→liquid, 음수는 liquid→gas 방향이다. 농도와 계수의 큰 크기 차이를 위해 저항 조합은 로그 공간에서 계산한다.

## 입력 및 결과

- 고정된 액상 부피 `fixed_liquid_volume_m3`, 기–액 계면적 `interfacial_area_m2`, 초기 중성 `CO2*` 농도
- 시간 순서대로 이어지는 intervals. 각 interval에 fugacity, 온도, Henry 계수, `k_g`, `k_l`, source/provider revision, configuration/result digest와 Evidence가 포함된다.
- 액상 막 계수 `k_l`은 기존 `degradation.wet_co2_liquid_side_mass_transfer` 계산 결과를 근거로 caller가 입력할 수 있다. 이 API는 그 모델을 내부에서 다시 계산하거나 계수의 유효 범위를 추정하지 않는다.
- 결과는 초기 knot 및 모든 interval 끝의 농도, 각 구간의 `K_L`, 평형농도, signed transfer mol 및 평균 flux를 보존한다.
- 조건이 맞으면 결과 knot을 downstream carbonate chemistry 요청에 caller가 명시적으로 매핑할 수 있다. 농도를 total inorganic carbon, alkalinity 또는 pH로 자동 변환하지 않는다.

## 적용 가정과 제한

- 각 interval에서 fugacity를 유지하는 비고갈 gas reservoir를 둔다. 전달된 몰수가 기체 압력/조성을 바꾸는 밀폐 용기는 범위 밖이다.
- 액체는 단일상·완전혼합·비유동이고 부피와 접촉 면적이 고정이다. 반응, 침전, 벽면 소비, 유입·유출은 포함하지 않는다.
- interval 경계에서 계수와 상태가 불연속적으로 바뀔 수 있으나, 경계 사이의 기상/물성 변화는 재구성하지 않는다.
- `CO2*`는 중성 용존 CO₂ 상태를 나타낸다. 탄산종 분포, pH, 알칼리도, 이온강도, fugacity 계산, metal dissolution 및 corrosion rate는 계산하지 않는다.
- 값의 출처 digest와 caller review는 추적성 조건이다. 값의 측정 타당성, 용매/온도 호환성, 기상 저장조 유지 여부나 현장 적용성에 대한 자동 검증은 아니다.
- 제공되는 농도 이력은 transport/chemistry 연결을 위한 상태 입력일 뿐, 부식률·금속손실·수명·acceptance 또는 위험확률이 아니다.

## 공개 범위 및 검증 상태

새 코드와 설명은 독립 작성했다. 논문 텍스트, 도표, 포인트 데이터는 저장소에 포함하지 않는다. 계산은 모델 검증이 완료되기 전의 구현 상태이며, 별도 수치·독립 데이터 검증은 전체 검증 단계에서 진행해야 한다.

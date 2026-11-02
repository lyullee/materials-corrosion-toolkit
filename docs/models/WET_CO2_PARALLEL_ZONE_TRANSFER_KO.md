# 습윤 CO₂ 구역별 병렬 전달 집계

## 목적

`integration.wet_co2_parallel_zone_transfer`는 stratified layer, slug body/film, annular film 등으로 나뉜 젖은 계면 구역마다 대표 상태와 2막 계수를 입력받아 각 구역 전달률을 계산한 뒤 합산한다. 단일 대표 농도와 단일 대표 계수로 먼저 평균내면 서로 다른 구역의 전달 구동력이 사라질 수 있으므로, 면적별 전달률을 계산한 후 총합한다.

Paolinelli–Nesic (2021)의 [기–액 배관 질량전달 연구](https://doi.org/10.1016/j.ijheatmasstransfer.2020.120689)는 다상 배관에서 유동 양식에 따라 액체 분포와 국부 전달 상태가 달라지는 문제를 다룬다. 본 모듈은 현장 유동 모델을 대체하지 않고, caller가 제공한 구역 상태를 보존하며 병렬면의 질량전달량을 합산한다. 논문 문장, 그림, 측정 결과는 코드와 문서에 복사하지 않았다.

## 계산

각 zone `i`에서 gas/liquid 막 저항을 액상 농도 기준으로 환산한다.

```text
K_L,i = 1 / (1/k_l,i + 1/(k_g,i H_i))
C_eq,i = H_i f_CO2,i
J_i = K_L,i (C_eq,i − C_bulk,i)
Ndot_total = Σ A_i J_i
J_area_average = Ndot_total / Σ A_i
```

각 구역의 계면적은 서로 겹치지 않아야 하며 그 합은 요청의 총 계면적과 일치해야 한다. 구역별 국부 전달 방향이 다를 수 있어, 최종 총합은 signed transfer rate로 낸다.

## 입력 및 결과

- zone ID와 유동 구역 유형, 계면적, 온도, gas CO₂ fugacity, liquid CO₂* 농도
- zone별 Henry 계수, gas film 계수, liquid film 계수
- 각 상태 provider의 버전·digest 및 Evidence, 영역 분할·적용성 검토 flag
- 구역별 평형농도, `K_L`, flux, transfer rate와 총합 및 면적가중 평균 flux

fugacity, Henry 상수와 막 계수는 기존 property/transport API 또는 외부 해석 결과를 caller가 근거와 함께 연결할 수 있다. 이 모듈은 복수 구역 간 혼합·고갈, 구역 전환, 시간 의존 상태를 풀지 않는다.

## 가정과 한계

- 각 zone은 대표적인 한 시점 상태를 가지며 해당 값은 그 구역 면적 전체에 적용 가능하다고 본다.
- 계면적은 불연속의 겹침 없는 zone들로 완전히 나뉘어 총면적을 이룬다.
- 계산 시간 동안 구역 간 물질 교환, 공통 gas reservoir의 fugacity 감소, 액상 inventory 변화는 없다.
- 2막 선형 저항식과 Henry convention이 입력 조건에 적합한지 caller가 확인해야 한다.
- 출력은 국부 전달 계산과 area aggregation 결과이지 부식률, 금속손실, scale, 수명 또는 위험도 예측이 아니다.

## 저작권 및 검증 상태

코드와 문서는 독립 작성했으며 문헌 문구, 표, 그래프나 실험 행을 포함하지 않는다. 구현 후 수치 검증과 현장 데이터 적합성 검증은 별도로 수행해야 한다.

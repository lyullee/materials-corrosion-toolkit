# 액상막 1차 반응을 포함한 습윤 CO₂ 전달

## 목적

`integration.wet_co2_reactive_film_transfer`는 물리적 기상막과 반응이 있는 정지 액상막을 결합해 국부 정상 CO₂ 흡수 flux를 계산한다. 전달된 CO₂*는 액막 안에서 caller가 정의한 비가역 겉보기 1차 sink에 의해 소비될 수 있으며, 결과에서 gas 흡수량, 액막 반응량, bulk 액체로 이동하는 중성 CO₂* 양을 분리한다. 따라서 gas 흡수 flux를 그대로 bulk CO₂* 재고 증가량으로 처리하지 않는다.

근거로 [반응을 동반한 기–액 전달 모델과 Hatta 수를 다룬 RSC 논문](https://doi.org/10.1039/C9RE00390H)을 참고한다. 이 API는 해당 문헌의 단순한 1차 반응 필름 경계값 문제를 별도로 유도한 구현이며, 문헌 문구·그림·측정 데이터나 실험 속도상수를 복사하지 않는다. 산업용 탄산염 chemistry의 실제 기구는 별도 검토가 필요하다.

## 모델 방정식

`k_l`은 반응이 없을 때의 액상 물리 전달계수, `k_rxn`은 CO₂*에 대한 caller 제공 비가역 겉보기 1차 속도상수, `D`는 액상 확산도, `H`는 `CO2*` 농도/fugacity Henry 계수다. 액막 두께는 `δ = D/k_l`, Hatta 수는 `Ha = √(k_rxn D)/k_l`로 둔다.

```text
a = k_l Ha coth(Ha)
b = k_l Ha csch(Ha)
f_i = (k_g f_bulk + b C_bulk) / (k_g + a H)
C_i = H f_i
N_gas = k_g (f_bulk − f_i) = a C_i − b C_bulk
N_bulk = b C_i − a C_bulk
N_reaction = k_l Ha tanh(Ha/2) (C_i + C_bulk)
N_gas = N_bulk + N_reaction
```

`Ha → 0`이면 반응 없는 물리 2막 해로 연속적으로 수렴한다. 코드에서는 작은 Hatta 수와 큰 Hatta 수에 안정적인 극한식을 사용한다. 모든 flux는 gas에서 액체 방향을 양수로 둔다. 반응 sink가 없는 상태는 `k_rxn=0`으로 입력한다.

## 입력·출력과 모듈 연결

- 기상 fugacity, bulk 액상 CO₂*, 온도 및 Henry 계수
- gas film 계수, 물리 liquid film 계수, CO₂* 확산도와 겉보기 1차 sink 상수
- provider revision/digest, Evidence, 적용성 및 사용 검토 flag
- 계면 fugacity·농도, Hatta 수, gas 흡수·bulk 전달·반응 sink flux와 수지 잔차

`k_g`, `k_l`, Henry 계수는 기존 습윤 CO₂ 전달 API 결과를 caller가 연결할 수 있다. 이 모듈은 확산도나 속도상수의 값을 내장하지 않고, 지정 용액·온도·기구에 해당하는 데이터인지 판단하지 않는다.

## 엄격한 적용 경계

- 정상 1차원 stagnant-film 근사이며 액상 내 확산도는 일정하다고 본다. 표면 재생, 접촉시간 분포, 계면파, 시간 변화나 구역별 혼합은 풀지 않는다.
- sink는 액막 전 구간에서 CO₂*에 대한 비가역 1차식이어야 하고 필요한 반응물이 과량으로 일정하게 존재해야 한다. 반응물 고갈, 역반응, 다단 탄산 평형, 복수 반응 및 이온 활동도는 포함하지 않는다.
- 입력의 `k_rxn`이 실제 CO₂ 수화·해리·중화반응에 대한 유효 계수라고 caller가 입증·검토하지 않은 경우 해당 CO₂ 화학에 해석해서는 안 된다.
- gas 흡수 flux 중 일부가 액막에서 반응 소비될 수 있다. 반응 생성물의 종이나 bulk 농도, pH 및 알칼리도 변화는 계산하지 않는다.
- flux는 부식률이나 금속 손실, 수명 또는 위험도를 뜻하지 않는다.

## 재배포와 검증

코드와 설명은 독립 작성했다. 외부 연구의 원문, 데이터, 그림은 저장소에 넣지 않는다. 수치 검증과 반응계별 실험 근거 검증은 별도 작업으로 남아 있다.

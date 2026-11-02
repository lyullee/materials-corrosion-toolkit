# 습윤 CO₂ 가스 배관 벽면 응축 상태

## 목적

`integration.wet_co2_condensate_state`는 한 위치·시점에서 기상 수증기 fugacity와 벽면 온도에 대한 액상 물 평형 fugacity를 비교해 응축 가능 상태를 분류한다. 응축 가능 범위 안에서는 gas CO₂ fugacity와 Henry 계수로 막 생기는 수상의 중성 용존 `CO2*` 평형농도 범위를 계산한다. 이는 상부 응축부식을 위한 열역학 입력 bridge이며, 응축량이나 부식률 계산은 아니다.

Seiersten 외 연구진의 [wet gas pipeline top-of-line corrosion 연구](https://doi.org/10.1088/1757-899X/1201/1/012082)는 물 응축과 응축수 내 산성 기체 용해가 상부 배관 부식 환경을 구성하는 경로를 다룬다. 본 구현은 그 범위를 응축 가능성 및 기초 CO₂* 평형 상태로 한정하며, 실험 조건이나 자료를 옮기지 않고 별도 계산을 작성했다.

## 판정식

```text
S_water = f_water,gas / f_water,equilibrium(T_wall, liquid composition)
C_CO2* = H_CO2*(T_wall, liquid composition) · f_CO2,gas
```

caller가 선언한 fugacity의 절대 오차 경계를 적용해 `S_water`의 결정론적 하한·상한을 계산한다. 하한이 1보다 크면 응축 가능성이 해당 경계 범위 안에서 지지되고, 상한이 1보다 작으면 표시되지 않으며, 나머지는 경계와 겹치는 불확정 상태다. CO₂ fugacity와 Henry 상수의 caller 경계도 곱해 incipient condensate의 `CO2*` 범위로 전파한다. 이 범위들은 확률분포나 신뢰구간으로 해석하지 않는다.

## 입력 및 물성 연동

- bulk gas 및 내부 벽면 온도, 전체압력, 물 vapor fugacity
- 해당 벽면 온도와 응축상 조성에 대한 수상 물 평형 fugacity
- CO₂ fugacity 및 액상 중성 `CO2*` 기준 Henry 계수
- 각 property provider 버전, 설정/결과 digest, Henry 레코드와 deterministic bound

순수 물의 saturation property는 CoolProp 같은 물성 라이브러리에서 제공할 수 있다. 다만 glycol, 염수, 다성분 응축액에서는 순수 물 포화압을 그대로 대입하지 말고, 실제 액상 조성의 물 활동도를 포함하는 property provider 결과를 넣어야 한다. 이 모듈은 어떤 물성 라이브러리도 직접 호출하지 않고, 총압·상평형·Henry 규약이 호환되는지 자동 인증하지 않는다.

## 가정과 한계

- 수증기 실제 fugacity와 벽면 평형 fugacity는 동일한 fugacity 기준 및 표준상태를 사용한다.
- CO₂ Henry 계수는 입력된 온도와 incipient condensate 조성에 맞는다. 초기 응축 액상은 평형 `CO2*` 상태로만 나타낸다.
- 응축 잠재성은 국부 열역학 조건이다. condensed water 양, 수막 두께, 물질전달률, droplets, 표면 젖음과 배수는 산출하지 않는다.
- pH, 알칼리도, 탄산종 분포, H₂S·유기산, corrosion kinetics 및 wall loss를 계산하지 않는다.
- 이후 액상 history나 반응전달 API에 연결하기 전에는 실제 액체의 부피·조성·접촉시간을 별도로 공급해야 한다.

## 재배포 및 검증

코드와 설명은 독립 작성했으며 연구 문장, 표, 그림 및 실험 측정값을 포함하지 않는다. property 데이터의 라이선스는 각 provider 배포 조건을 확인해야 한다. 구현 후 별도 물성 대조와 wet gas condensation 사례 검증이 필요하다.

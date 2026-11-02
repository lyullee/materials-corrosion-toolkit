# 변하는 응축액 재고와 CO₂* 기–액 전달 이력

## 목적 및 기존 API와의 차이

`integration.wet_co2_variable_condensate_transfer_history`는 고정 벽면 patch 위의 액체 부피가 caller 제공 응축 inflow 또는 well-mixed 액체 outflow에 따라 바뀔 때, 중성 용존 `CO2*` 농도와 액면적당 몰 재고를 시간 적분한다. 기존 [`wet_co2_finite_liquid_transfer_history`](WET_CO2_FINITE_LIQUID_TRANSFER_HISTORY_KO.md)는 부피 고정, [`wet_co2_condensate_film_history`](WET_CO2_CONDENSATE_FILM_HISTORY_KO.md)는 물 film 재고만 갱신한다. 본 모듈은 이 둘 사이에서 variable volume과 CO₂ mass transfer를 함께 풀되, 화학 반응은 추가하지 않는다.

입력 수지는 유한 액막에 대한 물질보존에서 독립적으로 유도했다. 별도 경험상관식, 공개 데이터 행 또는 고정 물성 상수는 사용하지 않는다.

## 상태 정의 및 해

기준은 고정 patch의 실제 gas–liquid interface 면적이다. `v`는 액체부피/계면적(`m³/m²`, 길이 차원), `C`는 neutral `CO2*` 농도(`mol/m³`), `q`는 면적기준 액체 체적유량(`m/s`)이다. gas/liquid 두 막을 액상 농도 기준으로 합친 전달속도는 `K`라 둔다. interval 안에서 `K`, Henry 계수 `H`, CO₂ fugacity `f`, `q`, 유입액 농도가 일정하면

```text
v(t) = v0 + q t
Jgas = K (H f − C)
```

양의 `q`는 `C_in` 농도의 응축액 유입, 음의 `q`는 같은 액상 농도를 가진 완전혼합 액체의 배수/유출이다. 이때 농도 미분식은

```text
q > 0: dC/dt = [K H f + q C_in − (K+q) C] / v(t)
q = 0: dC/dt = K (H f − C) / v0
q < 0: dC/dt = K (H f − C) / v(t)
```

각 구간은 이 선형식의 exact interval 해로 갱신한다. `q>0`은 유입 CO₂*를 포함하고, `q<0`은 배출 액상과 함께 나간 용존 CO₂* 몰수를 별도 재고수지에서 제거한다. liquid volume이 0에 도달하는 것은 마지막 interval 끝에서만 허용한다.

## 입력과 출력

- 시작 액체 부피/계면적 및 초기 CO₂* 농도
- 구간별 온도, liquid volume flux, 유입 CO₂* 농도, gas CO₂ fugacity, Henry 계수와 gas/liquid film 계수
- 상태 및 volume flux provider의 버전, configuration/result digest, Evidence와 가정 검토 flag
- 각 시간 knot의 액체 부피/계면적, CO₂* 농도, 면적기준 용존 몰수
- 구간별 gas→liquid 전달량, 유입/유출 CO₂* 재고, 전체 수지잔차

기상 fugacity, Henry 및 2막 계수는 기존 thermodynamic/transfer API에서 caller가 명시적으로 제공한다. 양의 volume flux에 대응하는 응축액의 초기 `CO2*` 농도도 caller의 상평형/물질전달 해석에서 가져온다.

## 범위와 제한

- 계산 patch의 액체는 단일상·완전혼합으로 본다. `v`는 실제 film shape가 아니라 면적기준 액체 재고다.
- 양의 volume flux는 incoming condensate source, 음의 flux는 well-mixed liquid withdrawal로 해석한다. 선택적 증발에서 CO₂*가 비례하지 않게 휘발하는 효과는 지원하지 않는다.
- 입력값은 piecewise constant다. 구간 안 gas composition 변화, dynamic finite-gas feedback, 반응소비, carbonate 평형, pH, scale 및 wall sink는 없다.
- 액체 부피/계면적, 가스/액체 film 계수, Henry convention의 일관성을 caller가 보증해야 한다. property provider 결과를 자동 계산하거나 검사하지 않는다.
- 출력은 neutral dissolved `CO2*` 재고·전달 ledger이며 부식률, 금속손실, 막 보호성, 수명 및 위험도가 아니다.

## 검증과 재배포

코드와 설명은 질량보존식의 독립 구현이며 문헌 문장, 표나 실험데이터를 복제하지 않는다. 이 API는 구현 상태다. 별도 수치 검증 전 설계 안전판정에 단독 사용하지 말고, 뒤 단계에서 analytic limit cases 및 provider 연동 사례를 검증한다.

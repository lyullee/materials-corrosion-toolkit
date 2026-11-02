# 유한 기상 재고와 변하는 응축액의 습윤 CO₂ 이력

## 목적과 구별점

`integration.wet_co2_finite_gas_variable_liquid_history`는 finite gas reservoir와 condensation/drainage로 변하는 액상부피를 한 물질수지 안에서 동시에 갱신한다. 기존 [`wet_co2_finite_gas_liquid_exchange_history`](WET_CO2_FINITE_GAS_LIQUID_EXCHANGE_HISTORY_KO.md)는 기상 재고가 finite이지만 액상부피가 고정이고, [`wet_co2_variable_condensate_transfer_history`](WET_CO2_VARIABLE_CONDENSATE_TRANSFER_HISTORY_KO.md)는 액상부피가 변하지만 기상 fugacity가 지정 저장조 조건으로 주어진다. 본 모듈은 두 조건이 함께 필요한 case를 위한 caller-data 기반 solver다.

## 방정식과 면적기준 수지

reference gas–liquid area당 액상부피를 `v` (`m³/m²`), neutral dissolved `CO2*` 농도를 `C`, gas fugacity를 `f`, 유한 gas inventory capacity를 `β` (`mol/(m²·Pa)`), signed liquid volume flux를 `q` (`m/s`)라 둔다. gas/liquid 물리막을 liquid-concentration basis로 합친 `K`는 각 interval 안에서 일정하다고 둔다.

```text
v(t) = v0 + q (t − t0)
Jgas = K (H f − C)
β df/dt = −Jgas
```

positive `q`는 caller가 CO₂* 농도를 제공하는 응축수 inflow로 보고,

```text
v dC/dt = Jgas + q C_in − q C
```

negative `q`는 완전혼합 수막에서 조성이 같은 liquid outflow로 보아,

```text
v dC/dt = Jgas
```

로 적분한다. 전체 gas + liquid CO₂* inventory 변화는 waterborne CO₂* inflow/outflow ledger와 같아야 한다. gas capacity는 고정 caller parameter이며 EOS로 계산하지 않는다.

## 수치 적분

Piecewise-constant intervals마다 SciPy `solve_ivp`의 `DOP853` 8차 explicit RK solver를 사용하며, `relative_tolerance`와 상태별 절대오차 한계를 요청에 저장한다. SciPy 문서는 `solve_ivp`를 초기값 미분방정식 수치적분으로 정의하고 높은 정밀도의 비강성 문제에 DOP853을 권한다. [solve_ivp 공식 API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html), [DOP853 API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.DOP853.html).

모듈은 interval 경계에서 solver를 재시작해 caller state와 구간별 parameter가 정확히 이어지게 한다. 각 구간에는 solver evaluation count, version, tolerance configuration digest 및 통합된 gas transfer와 물 유입/유출 CO₂*를 보존한다. local tolerance는 전 구간의 global uncertainty bound를 뜻하지 않는다.

## 입력과 연결

- 초기 액체 volume/area, liquid CO₂* 농도, gas CO₂ fugacity
- 초기 상태 및 gas capacity provider의 revision/configuration/result digest와 Evidence
- 고정된 finite-gas capacity per area
- 각 구간의 온도, signed water volume flux, incoming condensate CO₂* 농도, Henry 및 gas/liquid film coefficients
- 상태 provider revision/digest, Evidence, ODE solver tolerance, geometry·flux·basis review flags
- 모든 knot의 gas fugacity, liquid CO₂*, liquid inventory, gas inventory, cumulative transfer

입력은 기존 CoolProp/thermodynamic, gas/liquid transfer 및 condensate APIs 또는 외부 validated solver 결과에서 caller가 가져온다. 이 모듈은 해당 물성을 다시 예측하지 않는다.

## 제한

- liquid은 계면 전체에서 well-mixed라고 둔다. spatial gradient, droplets, partial wetting coverage, lateral exchange 및 계면적 변화는 없다.
- 양의 `q`는 condensate inflow이고 `incoming_co2star_mol_m3`에 그 농도를 지정한다. 음의 `q`는 같은 조성의 mixed-liquid outflow다. 중성 CO₂* 선택 증발은 표현하지 않는다.
- volume은 적분 중 항상 양수여야 한다. dryout event를 자동 검출·재wetting하는 모듈이 아니다.
- finite gas reservoir는 caller가 정한 `β`로만 표현한다. 압력·온도 변화, gas EOS/fugacity feedback 및 저장조 geometry는 계산하지 않는다.
- carbonate equilibrium, pH, 반응, scale, corrosion rate, 금속손실과 risk probability는 범위 밖이다.

## 공개 범위와 검증

코드는 gas/liquid inventory balance를 독립적으로 작성했고 출판 상관식·표·실험값을 포함하지 않는다. SciPy는 optional runtime dependency로 evaluator에서만 가져오며, 누락되면 `needs_data`로 fail-closed한다. 제3자 라이브러리의 실제 배포본과 license notice는 사용자가 확인해야 한다. 별도 test 및 numerical tolerance convergence 검증은 후속 전체 검증 단계에 남겨 둔다.

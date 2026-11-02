# 보정된 가스켓 누설과 유한 기체 재고의 압력 연성

## 모델과 목적

`integration.gasket_leakage_pressure_inventory_decay`는 유한한 고정 체적의 기체가 caller가 제공한 가스켓 누설 보정표를 통해 빠져나갈 때 내부 압력이 변하는 효과를 연립 계산합니다. 입력은 기존 `GasketLeakageHistory` 계약의 시간별 접촉압력, 접촉 면적, 압력차 보정표와 기체 공간의 초기 절대압력·체적·온도입니다. 압력차에 따라 누설률이 바뀌므로 일정 누설률 가정을 쓰는 노출량 API를 보완합니다.

## 방정식과 수치해

각 시간에서 가스켓 노드별 보정 몰 플럭스에 면적을 곱해 총 누설 몰 유량을 합산합니다. 그 유량을 이상기체 재고 수지에 연결합니다.

```text
n = P_abs * V / (R * T)
dP_abs/dt = -(R * T / V) * sum_i(area_i * calibrated_molar_flux_i)
dn_released/dt = sum_i(area_i * calibrated_molar_flux_i)
```

접촉압력은 caller가 제공한 시간 knot 사이에서 선형 보간하고, 누설 보정표는 그 표의 압력축 셀 안에서 쌍선형 보간합니다. 상태변수는 `scipy.integrate.solve_ivp`의 RK45 방법으로 적분합니다. 출력에는 knot별 절대압력·차압·누설률·누적 몰수와 기체 재고 수지 잔차를 기록합니다.

## 필수 입력과 검토

- 보정표, 면적 분할, 접촉압력 시간 이력 및 해당 자료의 공급자/버전/해시/Evidence
- 가스 공간의 고정 체적과 일정 온도, 상류 초기 절대압력 및 하류 절대압력
- 기록된 압력·몰 유량·면적의 단위 일치와 보정표 지원 범위 검토
- 접촉압력 궤적이 내부 압력 저하에 영향을 받지 않는다는 가정 검토
- 데이터 이용 권한과 계산 사용 검토

계산은 이 계약에 포함된 초기 누설 압력차가 초기 절대압력과 하류 경계의 차이와 일치해야 하며, 초기 상태가 보정표 범위 안에 있어야 합니다. 해가 보정표 범위를 벗어나거나 수치 적분이 완료되지 않으면 계산을 `out_of_scope`로 반환합니다.

## 적용 경계

이 모듈은 기체를 이상기체·등온·고정체적으로 취급하며 하류 압력은 일정하다고 가정합니다. 공급된 접촉압력 이력은 압력 감소에 따라 갱신하지 않습니다. 실제기체 압축성, 열교환, 조성 변화, 임계/초크 유동, 누설 경로 변화, 가스켓의 재료 적합성, 밀봉 합격 기준, 고장확률 및 수명은 추정하지 않습니다. 보정표 및 입력 데이터가 이 모델 가정과 조건을 만족하는지 caller가 확인해야 합니다.

## 독립 참고 자료

방정식 수지와 시간 적분기는 각각 이상기체 재고식과 공개 SciPy 적분 API를 근거로 독립 구성했습니다. 외부 문장·코드 블록을 복사하지 않았습니다.

- NIST, *Circular of the Bureau of Standards No. 279: Relations between the Temperatures, Pressures, and Densities of Gases*. [NIST 원문](https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular279.pdf)
- SciPy, `scipy.integrate.solve_ivp` 공식 문서. [API 문서](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)

## API 및 카탈로그 인계

- Model ID: `integration.gasket_leakage_pressure_inventory_decay`
- Schema: `matintegrity.gasket_leakage_pressure_inventory_decay.v1`
- Runtime dependency: `scipy`
- Evaluator: `evaluate_gasket_pressure_inventory_decay(request, *, scipy)`
- Source IDs: `caller_gasket_leak_calibration_map`, `caller_gasket_contact_pressure_history`, `caller_gasket_gas_inventory_volume_temperature_pressure`, `ideal_gas_inventory_balance_with_calibrated_leakage`

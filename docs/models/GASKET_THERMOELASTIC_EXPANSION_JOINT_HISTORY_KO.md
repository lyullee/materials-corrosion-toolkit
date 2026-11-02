# CTE 기반 볼트–가스켓 열팽창 결합 이력

## 목적과 계산 흐름

`integration.gasket_thermoelastic_expansion_joint_history`는 조립체의 각 볼트와 가스켓 접촉 섹터에 대해 사용자가 제공한 선팽창계수 표를 읽고, 기준 온도에서 각 하중 단계 온도까지의 자유 길이·두께 변화를 계산합니다. 계산된 변화량은 `integration.gasket_temperature_compression_joint_history`의 기존 준정적 조립 평형 계산에 입력됩니다.

입력 표는 각 부품 ID, 역할, 유효 자유 치수, 기준 온도, 온도 knot, 선팽창계수, 공급자·revision·record ID, SHA-256, 사용권 ID 및 근거(Evidence)를 포함합니다. 각 볼트와 가스켓 섹터에 정확히 하나의 표가 있어야 하고, 온도 knot은 엄격히 증가해야 합니다. 기준 온도는 최초 조립 온도와 같아야 하며, 모든 해석 온도가 각 표의 지원 구간에 들어가야 합니다. 가스켓 섹터의 유효 치수는 모델의 초기 가스켓 두께와 일치해야 합니다.

온도 구간별 선형 보간된 순간 선팽창계수 `alpha(T)`를 사다리꼴 적분하여 로그 변형률 `q`를 구합니다. 기준식 `alpha=(1/L)(dL/dT)`에 따라 치수 변화는 다음과 같습니다.

```text
q(T) = integral[T_ref..T] alpha(theta) dtheta
free_dimension_change = dimension_ref * expm1(q(T))
```

이 방식은 작은 열변형에서 흔히 쓰는 `dimension_ref * q` 근사 대신 기준식에 따른 지수 변화를 사용합니다. 적분값이 너무 커 `expm1` 결과가 유한하지 않으면 해당 계산은 범위 밖으로 반환합니다. 실제 측정치가 순간 CTE가 아니라 기준 온도부터의 평균/누적 CTE인 경우에는 입력 의미를 확인하고 그대로 넣지 않아야 합니다.

## 입력 검토 및 적용 절차

1. joint-history API에서 볼트, 섹터, 기준 조립 상태, 시간·온도·하중 knot을 구성합니다. 이 API를 사용할 때 기존 단계별 볼트 자유길이 및 가스켓 자유두께 열 이동량은 모두 0으로 둡니다.
2. 각 볼트에는 체결 방향에서 유효한 자유 길이, 각 가스켓 섹터에는 초기 가스켓 두께를 유효 치수로 넣습니다. 실제 구조에서 사용할 축방향 성분·구속 조건이 반영됐는지 검토합니다.
3. 각 부품의 온도별 CTE 값과 측정 상태·재료 조건·지원 범위가 현재 부품에 적용 가능한지 확인합니다. digest는 부품 ID, 역할, 치수, 기준온도, 표, 공급자와 record ID에 결합되어야 합니다. Evidence의 source ID, digest 및 license ID가 입력 레코드와 일치해야 합니다.
4. 네 가지 명시 검토(`cte_condition_and_dimension_applicability_reviewed`, `piecewise_linear_cte_integration_reviewed`, `common_reference_temperature_and_clock_reviewed`, `computational_use_authorized`)를 완료한 뒤 평가합니다. 미확인 항목이 있으면 `needs_data`입니다.
5. 출력의 부품별 자유 열변형과 joint-history의 공통 opening, 볼트 인장력, 섹터 압축력 및 평형 잔차를 함께 검토합니다. 결과는 특정 가정과 입력 상태에서의 조건부 계산입니다.

## 한계

- 이 모듈은 지정된 순간 CTE 표를 온도에 대해 선형 보간합니다. 데이터 지점 사이에 실제 상전이, 비선형 변화 또는 이력 의존성이 있으면 이 보간 가정은 적절하지 않을 수 있습니다.
- 부품별 균일 온도를 사용합니다. 반경·축방향 온도 구배, 비균일 재료, 접촉 열저항, 열전달, residual thermal stress, flange 휨, 국부 접촉 유한요소 해석은 풀지 않습니다.
- 하위 조립 solver가 사용하는 공통 opening 및 준정적 힘 평형의 가정과 범위를 그대로 상속합니다. 동적 impact, 체결 순서, 재체결, bolt relaxation, gasket creep/hysteresis와 누설률은 계산하지 않습니다.
- 유효 치수는 축방향 자유 열팽창으로 축약한 값입니다. 나사산/washer 상세, 조립 구속, 팽창 방향 투영, 접합부의 복잡한 하중 경로에 대한 적합성은 설계자가 판단해야 합니다.
- CTE 입력의 출처·측정법·추적성·사용권은 계산기만으로 보증되지 않습니다. 모델 결과는 재료 승인, 설계코드 적합성, 밀봉 건전성 또는 운전 안전의 인증이 아닙니다.

## 독립 참고자료

- D. A. Swyt, “Uncertainties in Dimensional Measurements Made at Nonstandard Temperatures,” *Journal of Research of the National Institute of Standards and Technology*, 99(1), 31–39, 1994. 순간 선팽창계수의 정의와 치수 측정 온도 보정 배경을 참고합니다. [DOI: 10.6028/jres.099.004](https://doi.org/10.6028/jres.099.004) · [NIST 원문 PDF](https://nvlpubs.nist.gov/nistpubs/jres/099/jresv99n1p31_a1b.pdf)
- “Development of Test Equipment for Measuring Compression Characteristics of Sheet Gaskets at Elevated Temperature,” *Journal of High Pressure Institute of Japan*, 46(6), 2008. 고온 가스켓 압축 특성 측정 맥락만 참고합니다. [DOI: 10.11181/hpi.46.363](https://doi.org/10.11181/hpi.46.363)
- H. Willis and A. Fatemi, “An Experimental Investigation of Compressive Behavior of a Gasket Material,” SAE Technical Paper 930119, 1993. 가스켓 압축 시험의 실험 배경만 참고합니다. [DOI: 10.4271/930119](https://doi.org/10.4271/930119)

위 자료의 문장, 도표, 수치 데이터는 구현에 복사하지 않았습니다. 이 모델의 입력 물성 및 형상 자료는 사용자가 별도 출처와 사용권을 확인하여 제공해야 합니다.

## 개발 API 계약

- 모듈: `matintegrity.models.gasket_thermoelastic_expansion_joint_history`
- 모델 ID: `integration.gasket_thermoelastic_expansion_joint_history`
- 스키마: `matintegrity.gasket_thermoelastic_expansion_joint_history.v1`
- 입력: `GasketThermoelasticExpansionJointHistory`
- 부품 물성 입력: `ComponentThermalExpansionRecord`
- 평가기: `evaluate_gasket_thermoelastic_expansion_joint_history(request)`
- `specifications()` 등록 대상이며 외부 runtime dependency는 없습니다.
- source ID: `caller_bolt_and_gasket_sector_cte_temperature_tables`, `caller_component_effective_free_dimensions_and_reference_temperature`, `piecewise_linear_cte_thermal_strain_integral`, `temperature_dependent_bolt_gasket_joint_equilibrium`

## 검증 과제

배포 전에는 상수 CTE 폐형식 결과와의 비교, knot 경계 및 역방향 온도 이동, CTE 지지범위 이탈, digest/Evidence 불일치, `expm1` overflow, 초기 평형 불일치, 지원 solver의 `needs_data`·`out_of_scope` 전파를 독립 계산으로 확인해야 합니다. 이 문서는 시험 결과를 주장하지 않습니다.

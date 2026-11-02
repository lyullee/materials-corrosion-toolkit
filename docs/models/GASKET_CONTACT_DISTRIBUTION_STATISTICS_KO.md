# 가스켓 접촉압력 면적 가중 분포 요약

## 목적

`fabrication.gasket_contact_distribution_statistics`는 계산된 플랜지·가스켓 접촉압력 field의 각 node 값을 해당 node가 대표하는 caller 면적으로 가중해 분포 통계를 산출한다. 단순 node 수 기준 통계와 달리 각 유한 요소/절점의 면적 차이를 반영한다. 정적 field 또는 viscoelastic contact history의 지정된 계산 knot를 처리한다.

## 입력 데이터와 권리 계보

- 지원되는 `fabrication.flange_contact_field`, `fabrication.flange_nonlinear_contact_field`, `fabrication.flange_viscoelastic_contact_history`, `fabrication.flange_nonlinear_viscoelastic_contact_history`의 computed `AssessmentResult` 및 전체 canonical SHA-256 digest.
- History 결과는 정확히 계산된 `selected_time_s` knot를 사용한다.
- 상류 결과 입력의 ordered node IDs와 `gasket_contact_area_m2`를 사용한다. 선택 결과 field의 node 순서가 원 입력 순서와 일치해야 한다.
- 선택형 기준압 요약을 원하면 각 기준의 압력, 적용 scope와 상류 결과·시간 knot를 결속한 digest, 출처 Evidence 및 사용 license를 함께 제공한다.
- 검토 플래그는 하중 범위·시각, 면적 정의/단위, 이산화 해상도, 요약 해석, criterion 적용성 및 데이터 이용권을 확인하도록 한다.

## 계산 정의

node `i`의 면적 `Aᵢ`, 접촉력 `Fᵢ`, 평균압력 `pᵢ`를 사용한다. 각 node에서 `Fᵢ ≈ Aᵢpᵢ`가 caller 계산 허용오차 안에서 닫히지 않으면 결과를 범위 밖으로 반환한다.

- 유효 총 면적 `A = ΣAᵢ`, 접촉력 합 `F = ΣFᵢ`, 면적 가중 평균압력 `p̄ = F/A`.
- 면적 가중 분산 `s² = Σ[Aᵢ(pᵢ−p̄)²]/A`, 표준편차 `s`, 변동계수 `s/p̄` (`p̄=0`이면 정의하지 않음).
- 면적 가중 경험 분위수는 압력 오름차순으로 누적 면적을 더하고 목표 질량에 처음 도달하는 값을 선택하는 left-continuous 규칙을 쓴다. node 사이 선형 보간은 하지 않는다.
- 각 caller 기준압 `p_min`에 대해 `pᵢ < p_min`인 node 면적을 더해 기준 미달 면적과 면적률을 계산한다. 접촉력이 양수인 node의 면적률도 별도 산출한다.

## API 사용

```python
from matintegrity.models.gasket_contact_distribution_statistics import (
    GasketContactDistributionStatistics,
    summarize_gasket_contact_distribution,
)

request = GasketContactDistributionStatistics(...)
calculation = summarize_gasket_contact_distribution(request)
```

`specifications()`는 ModelSpec 통합 시 사용할 수 있다. 결과는 pressure-based screening, FTA feature, 실험·FE 결과 비교의 요약 입력으로 연결할 수 있다. 각 후속 모듈은 별도 의미·불확실성·acceptance logic을 정의해야 한다.

## 해석 한계

- 통계는 caller가 제공한 유한 node/면적 분할만 표현한다. mesh-independent 연속 field나 mesh 수렴도를 추정하지 않는다.
- nodal 평균압력은 국부 접촉응력이나 씰 표면의 미세 압력분포가 아니다.
- 기준압은 caller의 사용 조건에 한정된다. 보편 seal pressure나 허용 기준으로 간주하지 않는다.
- 누설률, seal acceptance, 코드 적합성, 수명, 손상, 파손확률이나 qualification은 계산하지 않는다.
- 상류 contact solver의 물리적 검증을 대신하지 않는다. 사용 데이터와 계산모델의 검증·적용성은 별도 관리한다.

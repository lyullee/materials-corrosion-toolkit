# 다축 응력–변형률 닫힌 경로의 순 일밀도

## 목적

`matintegrity.multiaxial_tensor_work_cycle`은 caller가 순서와 기준을 검토한 닫힌 응력–변형률 텐서 표본 경로에서 signed net tensor work per volume을 계산한다. 이 계산은 일반화된 일 선적분만 제공한다. 열역학적 비가역 소산, 피로 손상, 수명 또는 재료 적합성을 판단하지 않는다.

## 입력과 단위

- 각 응력·변형률 텐서는 대칭 2차 텐서 6성분 `[xx, yy, zz, xy, yz, zx]` 순서다.
- 응력은 Pa, 변형률은 무차원이다. 응력 전단 성분은 실제 텐서 전단 성분으로 입력한다.
- `strain_shear_convention="tensor"`이면 변형률 전단 성분은 텐서 성분 \(\epsilon_{xy}\)이고, 내적에서 전단 항을 두 번 센다.
- `strain_shear_convention="engineering"`이면 입력 전단 성분은 공학 전단변형률 \(\gamma_{xy}=2\epsilon_{xy}\)이므로, 내적에서 별도 2배 가중을 하지 않는다.
- 응력·변형률·sample ID는 같은 순서와 길이로 정렬한다. ID는 중복될 수 없다.
- 닫힌 경로는 양쪽 응력과 변형률 이력의 첫 성분열과 마지막 성분열이 각각 정확히 일치해야 한다. 끝점에 별도 sample ID를 둔다.
- 응력/변형률 원본 ID와 SHA-256, caller의 부호·기저·conjugacy·cycle 순서 검토 상태를 입력한다. 입력 전체 canonical digest와 원본 핀은 결과에 보존된다.
- 최소 표본 수는 3, 최대 표본 수는 50,000이다. 모든 입력 숫자는 유한해야 한다. 유한 입력에서도 산술 중간값이나 합계가 부동소수점 범위를 넘으면 `out_of_scope`를 반환한다.

## 계산 정의

구간 \(i\)에서 응력과 변형률은 인접 표본 사이를 선형 보간한다고 선언한다. 따라서 구간의 signed work 증분은 평균 응력과 변형률 증분의 텐서 contraction으로 계산한다.

\[
\Delta W_i/V = \bar{\boldsymbol{\sigma}}_i : (\boldsymbol{\epsilon}_{i+1}-\boldsymbol{\epsilon}_i), \qquad
\bar{\boldsymbol{\sigma}}_i = (\boldsymbol{\sigma}_i+\boldsymbol{\sigma}_{i+1})/2
\]

대각 성분은 한 번씩 곱하고, shear convention에 따라 전단 성분의 contraction 계수를 선택한다.

\[
\bar{\boldsymbol{\sigma}}:\Delta\boldsymbol{\epsilon} =
\bar\sigma_{xx}\Delta\epsilon_{xx}+\bar\sigma_{yy}\Delta\epsilon_{yy}+\bar\sigma_{zz}\Delta\epsilon_{zz}
+ w_s(\bar\tau_{xy}\Delta\epsilon_{xy}+\bar\tau_{yz}\Delta\epsilon_{yz}+\bar\tau_{zx}\Delta\epsilon_{zx})
\]

여기서 tensor shear일 때 \(w_s=2\), engineering shear일 때 \(w_s=1\)이다. 전체 결과는 구간별 signed work 증분을 순서대로 합한 \(\oint \boldsymbol{\sigma}:d\boldsymbol{\epsilon}\)이며 단위는 J/m³(동일하게 Pa)다. 입력 점들 사이의 직선 경로에 대한 구간 적분은 정확한 사다리꼴 적분이다.

## 사용 예

```python
from matintegrity.multiaxial_tensor_work_cycle import (
    MultiaxialTensorWorkCycle,
    evaluate_multiaxial_tensor_work_cycle,
)

request = MultiaxialTensorWorkCycle(
    analysis_id="cycle-001",
    material_condition_id="condition-a",
    location_id="point-17",
    stress_history_source_id="stress-export",
    stress_history_sha256="a" * 64,
    strain_history_source_id="strain-export",
    strain_history_sha256="b" * 64,
    sample_ids=["s0", "s1", "s2"],
    stress_tensor_components_Pa=[
        [0, 0, 0, 0, 0, 0],
        [100e6, 20e6, 0, 10e6, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ],
    strain_tensor_components=[
        [0, 0, 0, 0, 0, 0],
        [0.001, 0, 0, 0.0002, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ],
    strain_shear_convention="engineering",
    cycle_closure_and_sample_order_reviewed=True,
    stress_basis_and_sign_reviewed=True,
    strain_basis_and_sign_reviewed=True,
    stress_strain_conjugacy_reviewed=True,
)
result = evaluate_multiaxial_tensor_work_cycle(request)
```

예시 숫자는 인터페이스 형태만 설명한다. 재료 측정값이나 검증 케이스로 사용할 수 없다.

## 적용 한계

결과는 이산 sample 경로의 signed net work다. 0보다 작거나 큰 값 모두 부호를 보존하며, 절댓값·양의 구간 합·음의 구간 합으로 분해하지 않는다. 시간, 온도, 소성변형률, 내부 상태변수, 탄성/소성 분리, 점성·열 효과, 재료 손상 법칙 또는 cycle extraction을 추정하지 않는다. 그러므로 이 값만으로 비가역 소산 에너지, 열 발생, 피로손상, 수명, 고장확률, 허용기준 또는 qualification을 주장할 수 없다.

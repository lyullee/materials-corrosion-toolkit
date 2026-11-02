# 가스켓 접촉압력 기준 미달 면적·시간 노출량

## 목적

`fabrication.gasket_contact_subthreshold_exposure`는 계산된 가스켓 점탄성 접촉 이력에서 caller 기준압보다 낮은 접촉 영역이 시간에 따라 어느 정도 존재했는지 면적·시간 적분으로 요약한다. 하나의 node event만 보는 분석을 넘어 각 시각의 전체 접촉 면적 분할과 반복 이력을 함께 처리한다.

## 입력 및 계보

- 계산 완료된 `fabrication.flange_viscoelastic_contact_history` 또는 `fabrication.flange_nonlinear_viscoelastic_contact_history` `AssessmentResult` 및 전체 canonical digest.
- 각 node의 `mean_contact_pressure_Pa`를 포함하는 두 개 이상의 완전 계산 knot. 시간은 초 단위로 엄격히 증가해야 한다.
- 결과 입력에 고정된 ordered node IDs와 양수 gasket contact areas. 모든 knot의 node ID와 순서는 입력 배열과 정확히 일치해야 한다.
- 적용 scope 및 history digest와 연결된 최소압 기준, provider/revision, 기준 record digest, Evidence 및 usage license.
- 기준 적용성, node 면적분할·해상도, pressure interpolation과 노출량 의미, 데이터 사용권한에 대한 caller 검토.

## 계산 정의

인접 계산 knot `(t₀,p₀)`와 `(t₁,p₁)` 사이에서 각 node 압력은 선형으로 연결한다고 가정한다. 그 선분이 기준 `p_min` 아래에 있는 시간분율 `f_below`를 계산해 해당 node 면적 `A`를 곱한다. 전체 기준 미달 면적시간은 각 node와 모든 시간 구간의 `Σ A × (t₁−t₀) × f_below` 합이다. 기준압 미달 상태에 해당하는 노출 시간 비율은 그 값을 전체 면적과 관찰 지속시간의 곱으로 나누어 정규화한다.

압력 부족량 적분은 양의 부분 `max(p_min−p(t),0)`를 node별로 시간에 따라 적분해 면적을 곱한다. 선형 pressure 경로에서는 전체 구간이 기준 아래면 사다리꼴, 기준을 통과하면 아래쪽 삼각형의 면적을 정확히 적용한다. 결과 단위는 `Pa·m²·s`다.

## API 사용

```python
from matintegrity.models.gasket_contact_subthreshold_exposure import (
    GasketContactSubthresholdExposure,
    evaluate_gasket_contact_subthreshold_exposure,
)

request = GasketContactSubthresholdExposure(...)
calculation = evaluate_gasket_contact_subthreshold_exposure(request)
```

`specifications()`는 중앙 registry의 ModelSpec 통합에 쓸 수 있다. 누적 면적시간과 pressure-deficit dose는 후속 FTA 또는 위험성 평가의 입력 지표로 사용할 수 있으나 event 정의나 확률을 자동 부여하지 않는다.

## 해석 제한

- 구간 내 값은 계산된 양 끝 knot를 잇는 선형 가정의 결과다. 실제 contact solver의 중간 시각 해나 미포착 급격 전이를 주장하지 않는다.
- node 면적을 고정하고 유한 discretization만 적분한다. node 사이 pressure field나 mesh convergence를 재구성하지 않는다.
- 기준압은 caller 적용 조건에만 해당한다. 보편적 seal criterion으로 보지 않는다.
- pressure-deficit dose는 누설 유량 모델이 아니며, 누설률·합격/불합격·수명·파손확률·재료 qualification을 산출하지 않는다.
- 이력 대표성, 기준 적용성, 실험/해석 검증은 별도 관리해야 한다.

# 상분율 선형 대비 평가

`materials.phase_fraction_linear_contrast`는 사용자가 정의한 여러 상분율의 선형 결합과 그 계측 불확도를 계산해 사용자가 공급한 범위와 대조한다. 한 호출에는 단일 물리 시편, 영역, 측정법의 상분율 관측만 넣는다. 상 ID, 계수, 요구 범위와 측정 방법은 모두 호출자 입력이며 규격 값을 내장하지 않는다.

## 입력과 계산

관측 벡터를 `x`, 선형 대비 계수를 `a`, 같은 순서로 식별된 확장 공분산 행렬을 `C`라고 하면 계산은 다음과 같다.

```text
value = aᵀ x
expanded_uncertainty = sqrt(aᵀ C a)
interval = [value - expanded_uncertainty, value + expanded_uncertainty]
```

각 관측의 확장불확도 제곱은 `C`의 해당 대각값과 일치해야 한다. 행렬은 대칭 양의 준정부호여야 하며, 교차 공분산은 상분율 관측과 같은 확장 기준으로 제공한다. `expansion_factor`는 provenance에 기록한다. 모델은 coverage factor를 추정하거나 공분산을 독립으로 가정해 만들지 않는다. 공분산이 없거나 검토 gate가 미완료면 `needs_data`를 반환한다.

구현은 측정 모델의 선형 불확도 전파에서 공분산 항을 유지한다. 이는 사용자가 공급한 불확도를 계산상 전달하는 일반 수학 관계이며 phase definition, 표본 대표성, segmentation bias, 재료 적합성 또는 규격 해석은 별도 근거가 필요하다. [NIST Technical Note 1297, Appendix A](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-appendix-law-propagation-uncertainty)는 공분산을 포함한 불확도 전파의 공개 근거다.

## 사용 예

검토된 Python 계약은 다음과 같이 등록 모델로 실행할 수 있다.

```python
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

result = default_registry().run(
    "materials.phase_fraction_linear_contrast",
    assessment_payload,
    RunContext(asset_id="asset-1", location_id="weld-metal", time_basis="inspection-2026-01"),
)
```

완전한 synthetic 입력은 `examples/model_inputs.json`의 같은 모델 ID 아래 있다. 직접 실행 가능한 검증 예제는 `tests/test_phase_fraction_contrast.py`에 있으며 누리온 batch105에 등록했다. 예제 계수·측정치·공분산은 설명용으로만 사용한다.

## 결과 해석과 경계

`within_declared_range`는 입력 구간이 caller bounds 안에 완전히 포함되는지 나타낸다. 이는 계산된 비교 상태이며 코드 적합 판정, 상분율의 통계적 신뢰구간, 품질 승인, 용접 성능, 내식성, 강도, 인성, 균열 민감도, 수명 또는 고장확률을 뜻하지 않는다. 상분율 합이 1이 되도록 정규화하거나 관측하지 않은 상을 잔여값으로 추정하지 않는다. 복수 시편 간 모집단 변동을 추정하지 않고, 해당 aggregate/campaign 계산은 독립적인 확장 과제로 남긴다.

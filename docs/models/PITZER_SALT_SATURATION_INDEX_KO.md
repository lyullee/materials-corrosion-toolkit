# 단일 염 Pitzer 포화지수 스크리닝

`chemistry.pitzer_salt_saturation_index`는 하나의 순수 전해질 Pitzer 활동도 계산과 caller가 제공한 온도 일치 용해도곱을 연결해 `log10(Q/Ksp)`를 계산한다. 결과 상태는 caller가 선언한 화학식, 평균 이온 활동도 표준상태, 용해도곱과 적용성 검토에 한정된다.

## Python API

```python
from matintegrity.pitzer_salt_saturation_index import (
    PitzerSaltSaturationIndex,
    evaluate_pitzer_salt_saturation_index,
)

request = PitzerSaltSaturationIndex(
    assessment_id="salt-saturation-case",
    activity_request=pitzer_request,
    log10_solubility_product=-5.2,
    solubility_product_temperature_K=298.15,
    solubility_product_source_id="reviewed-ksp-source",
    solubility_product_record_id="ksp-record-01",
    solubility_product_record_sha256="a" * 64,
    salt_formula_and_standard_state_reviewed=True,
    solubility_product_temperature_and_applicability_reviewed=True,
    complete_single_salt_scope_reviewed=True,
    solubility_product_use_authorized=True,
    evidence=(ksp_evidence,),
)
calculation = evaluate_pitzer_salt_saturation_index(request)
```

## 해석과 제한

- `log10(Q/Ksp) < 0`은 지정한 caller 자료에서 포화 미만, `> 0`은 포화 초과에 해당한다. `boundary_tolerance_log10` 안쪽은 경계 근처로 분류한다.
- Pitzer 요청이 계산되지 않으면 포화지수도 반환하지 않는다. 입력 및 Pitzer 결과 digest, Ksp record hash와 Evidence를 함께 보존한다.
- 단일 순수 염의 mean ionic activity만 사용한다. 혼합 전해질 상호작용과 개별 단일 이온 활동도는 제공하지 않는다.
- 포화 상태만 스크리닝한다. 핵생성, 석출/용해량, 상 변화 속도, 부식, 건전성 적합 또는 고장확률은 추론하지 않는다.
- 수치 검증과 배포 포함 여부는 추후 일괄 검증 작업에서 다룬다.

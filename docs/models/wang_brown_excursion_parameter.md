# Wang–Brown형 전단 반전·법선 변형률 excursion 계산

## 목적

`fatigue.wang_brown_reviewed_excursion_parameter`는 caller가 명시한 유한 재료면 및 전단 변형률 반전 끝점에 대해 Wang–Brown 계열의 전단-법선 변형률 파라미터를 계산한다. 핵심 계산은 다음과 같다.

`P = Δγ / 2 + S ε*n`

여기서 `Δγ`는 caller가 지정한 반전 끝점 간 면내 engineering shear 변형률 벡터의 범위, `ε*n`은 끝점을 잇는 caller 순서의 cyclic arc에서 측정한 법선 변형률 excursion, `S`는 재료 조건별 caller 보정계수다. 이 API는 이 파라미터를 유한면에서 산출하며, cycle counting 또는 수명 예측을 대신하지 않는다.

## 공개 기술 근거

주요 방법 근거는 C. H. Wang and M. W. Brown, “A Path-Independent Parameter for Fatigue Under Proportional and Non-Proportional Loading,” *Fatigue & Fracture of Engineering Materials & Structures*, 16 (1993), 1285–1297, [DOI: 10.1111/j.1460-2695.1993.tb00739.x](https://doi.org/10.1111/j.1460-2695.1993.tb00739.x)이다. 이 방법은 최대 전단 변형률 reversal에 대한 법선 변형률 excursion을 비례·비비례 이력의 영향 인자로 사용한다. 이 구현은 논문 문장·도표를 재수록하지 않으며 계산 계약과 caller 검토 경계를 별도로 정의한다.

## 입력과 단위

- 변형률 tensor 행은 `[xx, yy, zz, xy, yz, zx]` 순서다.
- 전단 성분 저장 convention은 `tensor` 또는 `engineering`으로 선언한다. 면내 전단 범위는 두 경우 모두 engineering shear로 출력한다.
- 닫힌 한 주기의 마지막 tensor 행은 첫 행과 정확히 같아야 한다. 내부 행은 caller가 관측 순서대로 제공한다.
- 각 candidate plane은 단위 법선과 두 직교 tangent를 포함한다.
- 각 면별 reversal 시작·끝 표본 index를 caller가 지정한다. index는 중복 종점이 아닌 독립 표본을 참조한다. 끝점 순서는 기록된 경로에서 cyclic으로 이어지며 시작 index보다 앞선 끝점은 종점에서 wrap한다.
- `S`는 dimensionless 입력이며 calibration Evidence, source ID 및 digest와 함께 제공한다. 보편 상수나 기본값은 제공하지 않는다.
- 표본 source Evidence와 material calibration Evidence는 각 요청에서 source ID 및 SHA-256과 일치해야 한다.

## 계산과 검토 경계

tensor 변형률을 각 면의 법선 및 tangent 축으로 투영한다. caller가 지정한 반전 두 점에서 면내 전단 벡터 간 유클리드 범위를 구하고, half-range에 `S`를 곱한 법선 excursion을 더한다. 법선 excursion은 선택된 cyclic arc 안에서 caller 유한 표본으로 계산한 최댓값과 최솟값의 차이다. 반환 결과의 governing plane은 이산 후보 중 parameter가 가장 큰 면이다.

이 API는 reversal pairing을 자동 선택하지 않는다. 최대 shear reversal이 각 면에서 올바르게 선택됐는지, tensor 기준·시각 순서·경로 wrap 해석이 적합한지는 caller가 검토한다. 유한 표본 사이의 극값은 보간하지 않으며, 고주파 경로·연속면 최적화·회전면 이동을 추정하지 않는다.

`S`의 재료·온도·환경·하중형태 간 이전은 자동화하지 않는다. 수명 mapping, 변동진폭 cycle decomposition, 누적손상, 순서효과, 불확실성, 설계허용/규정 적합성 및 재료 qualification은 별도 모델과 자료가 필요하다. 따라서 parameter만으로 안전 판정이나 사용수명을 주장할 수 없다.

## Python API

```python
from matintegrity.wang_brown_excursion_parameter import (
    WangBrownReviewedExcursionParameter,
    evaluate_wang_brown_reviewed_excursion_parameter,
)

request = WangBrownReviewedExcursionParameter(...)
result = evaluate_wang_brown_reviewed_excursion_parameter(request)
```

`specifications()`는 요청 타입, evaluator, 무차원 출력 단위, 전제 및 source ID를 반환한다. 중앙 registry 연결은 별도의 통합 변경 사항이다.

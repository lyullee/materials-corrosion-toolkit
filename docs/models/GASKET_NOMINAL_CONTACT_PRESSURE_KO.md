# 가스켓 평균 접촉압력 산출

## 목적과 범위

`mechanics.gasket_nominal_contact_pressure`는 caller가 제공한 가스켓 압축 반력과 유효 접촉 면적으로 면적 평균 접촉압력을 계산합니다. 외부 접촉 해석기나 실험 데이터 없이도 기존 조인트 평형 계산의 가스켓 반력을 후처리할 수 있습니다.

이 계산은 접촉면 압력이 균일하다고 간주한 평균값입니다. 국부 접촉압력장, 면압의 공간분포, 누설량, 실링 성능 또는 설계 적합성을 계산하지 않습니다.

## Python API

- 요청 계약: `GasketNominalContactPressureRequest`
- 계산 함수: `calculate_gasket_nominal_contact_pressure`
- 모듈: `matintegrity.models.gasket_nominal_contact_pressure`

요청에는 `compressive_gasket_force_N`, 힘 자료의 `gasket_force_evidence`, 면적 근거의 `geometry_evidence`, 그리고 두 데이터의 동일한 물리 범위 검토가 필요합니다. 면적은 다음 중 하나로 지정합니다.

1. caller가 검토한 `effective_contact_area_m2`
2. 동심 원환 가정의 `inner_diameter_m`, `outer_diameter_m`

두 번째 입력은 기하학적 원환 면적을 계산합니다.

\[
A = \frac{\pi}{4}(D_o^2-D_i^2), \qquad \bar p = \frac{F_g}{A}
\]

여기서 지름은 m, 힘은 N, 면적은 m², 평균압력은 Pa입니다. 표준 가스켓 계수나 경험 상수는 적용하지 않습니다.

```python
from matintegrity.contracts import Evidence
from matintegrity.models.gasket_nominal_contact_pressure import (
    GasketNominalContactPressureRequest,
    calculate_gasket_nominal_contact_pressure,
)

request = GasketNominalContactPressureRequest(
    assessment_id="joint-load-case-01",
    compressive_gasket_force_N=120_000.0,
    gasket_force_evidence=Evidence(
        source_id="joint-equilibrium-run-01",
        origin="model_prediction",
        citation="Caller-owned joint equilibrium result",
        sha256="a" * 64,
    ),
    inner_diameter_m=0.10,
    outer_diameter_m=0.14,
    geometry_evidence=Evidence(
        source_id="gasket-drawing-rev-c",
        origin="user_declared",
        citation="Caller-reviewed effective contact diameters",
        sha256="b" * 64,
    ),
    force_area_scope_reviewed=True,
    uniform_mean_pressure_interpretation_reviewed=True,
)
result = calculate_gasket_nominal_contact_pressure(request)
mean_pressure_pa = result.values["mean_contact_pressure_Pa"]
```

## 데이터 계약과 검토

- 압축 반력은 선택된 면적과 같은 조인트, 하중 단계, 접촉 정의에서 나온 값이어야 합니다. 인장 부호 규칙이 있는 solver 값은 caller가 압축 반력으로 변환하고 그 기준을 근거 자료에 기록해야 합니다.
- 유효 면적은 유체 압력에 의한 유효 면적이나 가스켓 명목 폭과 자동으로 같다고 간주하지 않습니다. 직경 방식은 입력 지름이 실제 접촉 링의 내·외경이라는 caller 검토가 필요합니다.
- 직경은 양수 또는 0인 내경과 더 큰 외경을 요구합니다. 접촉 면적은 양수여야 합니다. 압축력이 0이면 평균압력도 0입니다.
- `Evidence`는 힘과 기하의 출처 식별을 보존합니다. 계산기는 출처 자료를 가져오거나 적합성을 판정하지 않습니다.

## 제한 사항

- 평균값만 제공하며 가장자리 효과, 플랜지 회전/유연성, 볼트 하중 편차, 가스켓 비선형성, 시간에 따른 이완, 접촉 손실, 국부 응력 집중은 해석하지 않습니다.
- 유효 면적과 가스켓 힘의 정의가 불일치하면 계산 결과도 물리적으로 의미가 없을 수 있습니다. 범위 일치 검토는 caller의 책임입니다.
- 이 결과는 설계 코드 승인, 재료 허용치, 누설 기준, 위험도 또는 수명 평가에 직접 사용할 수 있는 판정이 아닙니다.

## 근거와 배포

수식은 원환의 기하학적 면적과 힘/면적 정의를 독립적으로 구현한 것입니다. 외부 상관식, 표준 표, 경험 계수 또는 문헌 문장을 포함하지 않습니다. 모듈과 문서는 프로젝트 라이선스에 따라 독립 배포할 수 있습니다.

# 유한 평면 GSA–수명 곡선 연결

## 목적

이 API는 이미 계산 가능한 Ince–Glinka 일반화 변형률 진폭(GSA) 지표와 사용자가 제공하는 유한 수명 곡선을 연결한다. 프로젝트에 내장된 재료 상수나 표준 곡선을 가정하지 않는다. 사용자는 동일 재료 상태에 대한 GSA–파단 반복수 점을 순서대로 공급해야 한다.

## 계산 범위

1. 기존 `ince_glinka_gsa_parameter` 계산기로 입력 폐합 텐서 이력의 사용자가 지정한 유한 평면을 평가한다.
2. 최대 GSA 값이 제공 곡선의 양 끝점 안에 있는지 확인한다.
3. 인접한 점 사이에서 `log(GSA)`에 대한 `log(반복수)` 선형 보간을 적용한다.
4. 정확히 보간점과 일치하면 그 점의 반복수를 그대로 사용한다.

GSA 축은 무차원이다. 반복수는 `cycles_definition`에서 정의한 단위 그대로 반환한다. GSA 또는 반복수의 외삽, 곡선 적합, rainflow 주기계수, Miner 누적, 재료 간 전이는 수행하지 않는다.

## 입력 및 추적성

- 계산 요청은 기존 `InceGlinkaGSACalculation` 계약을 재사용한다.
- 각 곡선 점은 고유 ID, 양의 GSA, 양의 파단 반복수, 출처 레코드 ID, 하나 이상의 `Evidence`를 보유한다.
- 점은 GSA 오름차순으로 제공하며, 반복수는 엄격히 감소해야 한다.
- 계산 재료 상태와 곡선 재료 상태가 같아야 한다.
- 보간, 동일 사이클 반복 가정, 재료 상태/곡선 적용성 검토를 각각 명시적으로 확인해야 한다.
- 결과에는 원 요청 digest, GSA 입력 digest, 사용된 곡선 점 ID, 출처 ID와 Evidence가 포함된다.

## 결과 해석

`computed`는 제공 곡선과 닫힌 단일 사이클을 반복한다고 가정했을 때의 보간 결과만 뜻한다. 실험적 수명 예측 성능, 재료 적합성, 손상 누적 규칙, 설계 허용성, 고장 확률 또는 표준 코드 적합성을 뜻하지 않는다. 리뷰가 빠졌으면 `needs_data`, GSA가 입력 곡선 범위를 벗어나면 `out_of_scope`로 반환하고 수명을 만들지 않는다.

## Python 사용 예

```python
from matintegrity.ince_glinka_gsa_curve_life import (
    GSALifeCurvePoint,
    InceGlinkaGSACurveLife,
    evaluate_ince_glinka_gsa_curve_life,
)

request = InceGlinkaGSACurveLife(
    calculation=caller_gsa_request,
    calibration_id="lab-curve-2026-01",
    calibration_material_condition_id="alloy-condition-A",
    cycles_definition="cycles to the declared failure endpoint",
    curve_points=(
        GSALifeCurvePoint(
            point_id="curve-point-1",
            gsa_parameter=0.001,
            cycles_to_failure=100000,
            source_record_id="lab-curve-record",
            evidence=(caller_evidence,),
        ),
        GSALifeCurvePoint(
            point_id="curve-point-2",
            gsa_parameter=0.01,
            cycles_to_failure=1000,
            source_record_id="lab-curve-record",
            evidence=(caller_evidence,),
        ),
    ),
    interpolation_reviewed=True,
    repeated_cycle_assumption_reviewed=True,
    material_condition_and_curve_applicability_reviewed=True,
)
result = evaluate_ince_glinka_gsa_curve_life(request)
```

이 예시는 API 모양만 보여준다. 값은 실제 재료의 측정 자료가 아니므로 그대로 사용하지 않는다.

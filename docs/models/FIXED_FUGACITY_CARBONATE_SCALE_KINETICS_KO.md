# 고정 퓨가시티 탄산염 이력에서 caller scale kinetics로 연결

## 목적과 경계

`integration.fixed_fugacity_carbonate_to_scale_kinetics`는 이미 계산된 `chemistry.fixed_fugacity_carbonate_history`의 정확한 시점별 CO₃ 농도를 입력으로 받아, 호출자가 제공한 활동도 계수와 다른 수용종 활동도, 온도별 Ksp로 지정 고체상의 포화도를 계산합니다. 모든 시점의 포화도 계산이 성공하면 그 결과를 기존 단일 균일층 `caller_surface_scale_kinetics`에 연결합니다.

이 어댑터는 화학종이나 고체상을 선택하지 않습니다. 활동도 계수, Ksp, 화학량론, scale 속도계수와 몰부피를 추정하지 않습니다. 부식률, 금속 손실, 보호 성능, 수명 또는 고장 확률을 산출하거나 자격화하지 않습니다. 결과는 입력으로 지정한 단일 고체상 및 caller kinetic law의 조건부 계산입니다.

## 입력 계약

- `fixed_fugacity_carbonate_history`: `chemistry.fixed_fugacity_carbonate_history`의 계산 완료 `AssessmentResult`.
- `fixed_fugacity_carbonate_history_sha256`: 결과 JSON의 canonical SHA-256. 모듈은 결과의 요청 입력 digest와 계산 모델 입력 digest도 다시 확인합니다.
- `carbonate_species_id`, `solid_terms`, `selected_solid_id`: 사용자가 검토한 탄산염 종, 고체상 및 활동도 지수.
- `knots`: 원본 history와 일대일 대응하는 모든 시간점. 각 점에 carbonate 활동도 계수, 다른 고체 구성종의 명시적 무차원 활동도, 온도 적용 범위가 해당 점을 포함하는 Ksp 기록을 입력합니다. 시간은 보간 없이 원본 값과 정확히 일치해야 합니다.
- `kinetics_template`: 기존 `CallerSurfaceScaleKinetics` 입력. 인접 history 시점으로 구간을 구성하고, 구간 온도는 해당 구간 왼쪽 history 시점 온도와 같아야 합니다. kinetic law의 계수·상 및 적용성 증거는 이 입력이 제공합니다.
- 검토 플래그: 활동도 표준상태, 전체 구성종, Ksp 온도 범위, 고체상과 kinetics 상의 대응, 포화도 구간 해석, kinetic law 적용성 및 계산 사용 승인을 각각 명시합니다. 하나라도 누락되면 계산을 진행하지 않습니다.

각 activity 및 Ksp 출처는 provider, revision, record ID, SHA-256과 일치하는 `Evidence`를 포함해야 합니다. Ksp 온도 범위가 각 knot을 포함해야 할 뿐 아니라, 각 `CarbonateKspKnotRecord.temperature_applicability_reviewed`도 `True`여야 합니다. 미검토 Ksp knot이 하나라도 있으면 record ID와 시점을 반환하고 포화도/scale 계산을 시작하지 않습니다. `RunContext`의 asset, location, time basis는 입력된 carbonate history의 문맥과 같아야 합니다.

## 계산 흐름

1. source AssessmentResult와 digest, 시점 배열, 문맥, kinetic interval 정렬을 확인합니다.
2. 각 정확한 시점에서 `a_CO3 = gamma_CO3 × [CO3] / (1 mol/L)`로 무차원 활동도를 만듭니다. 다른 반응종 활동도는 호출자 값만 사용합니다.
3. 각 시점에 기존 `aqueous_saturation_screen`을 호출해 호출자 지정 고체상 하나의 log10 포화비를 구합니다. Ksp 기록의 온도 범위가 해당 시점 온도를 포함해야 합니다.
4. 모든 시점의 screen 상태가 `computed`이고 포화비가 유한 표현 범위에 있을 때만 `10**log10(S)`를 계산합니다. 이 정확한 양 끝점 값을 kinetic interval에 넣고 기존 `caller_surface_scale_kinetics`를 호출합니다. 구간 사이 선형 포화도 해석은 별도 사용자 검토 플래그로 제한합니다.

첫 비계산 시점에서 멈추며 그 전까지 계산된 screen 결과와 최초 실패 정보를 반환합니다. 부분 시점만으로 scale kinetics를 실행하지 않습니다.

## Python API

```python
from matintegrity.fixed_fugacity_carbonate_scale_kinetics import (
    FixedFugacityCarbonateScaleKinetics,
    evaluate_fixed_fugacity_carbonate_scale_kinetics,
)

request = FixedFugacityCarbonateScaleKinetics.model_validate(payload)
calculation = evaluate_fixed_fugacity_carbonate_scale_kinetics(request)
```

표준 registry 경로를 사용할 경우 `specifications()`가 모델 정의를 제공합니다. registry/schema/catalog 연결은 중앙 통합 단계에서 처리합니다.

## 실패 및 적용성

필수 검토가 꺼져 있으면 `needs_data`; 원본 saturation solver가 미지원 또는 데이터 부족을 반환하면 그 상태를 보존합니다. 양의 유한 활동도·포화비, 모든 구성종, 정확한 시점 정렬 및 Ksp 온도 적용 범위를 만족하지 못하면 계산을 중단합니다. activity coefficient나 Ksp에 대한 자동 온도 보정, 시점 보간, 평형상 탐색, 경쟁상 선택은 없습니다.

## 재현성과 검토

출력에는 source result/input digest, 호출 입력 digest, 각 activity/Ksp 출처, 각 포화도 screen의 요청·결과 digest, kinetics 요청 digest와 결과가 포함됩니다. 이 lineage를 보존하고, 적용 대상의 화학종 목록·단위·표준상태·온도 범위와 kinetics 보정 자료를 별도로 검토해야 합니다. 이 문서는 사용법과 계산 경계를 기록하며 실험 검증이나 산업 적용 승인을 의미하지 않습니다.

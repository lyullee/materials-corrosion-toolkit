# Ince–Glinka GSA cycle-group Miner campaign

## 목적과 범위

`fatigue.ince_glinka_gsa_miner_campaign`는 호출자가 제공한 유한한 cycle group 각각에 대해 기존 finite-plane Ince–Glinka generalized strain amplitude(GSA) 계산과 기존 caller curve 기반 life mapping을 수행한 뒤, 모든 group의 life가 계산된 경우에만 기존 `miner_damage` API로 damage fraction을 합산합니다. 기존 단일 반복 cycle의 GSA-to-life 경로를 호출자 cycle count가 있는 여러 group에 연결하는 한정된 API입니다.

이 계산은 cycle을 추출하거나 세지 않습니다. cycle group의 계수는 입력자가 제공합니다. 시간 순서, 하중 간 순서 효과, 상호작용 또는 비선형 damage law를 모델링하지 않습니다. 결과는 명시된 life curve와 Miner 합산 규칙에 조건부이며 재료 자격, 합격 판정, 고장 확률 또는 잔여 수명을 뜻하지 않습니다.

## 입력 계약

- `cycle_groups`: 각 행은 고유 `cycle_group_id`, 양의 `allocated_cycle_count` 및 기존 `InceGlinkaGSACurveLife` 요청을 포함합니다.
- 각 life 요청에는 닫힌 stress/strain tensor cycle, finite candidate plane 집합, material condition, evidence가 연결된 단조 GSA-to-life curve, curve 지원 범위 및 기존 interpolation/applicability 검토가 있어야 합니다.
- 모든 group은 동일한 calibration ID, 재료 상태, cycle definition, curve point 집합, material condition, physical scope 및 위치를 사용해야 합니다.
- campaign 입력에는 cycle count/구성 검토, curve·재료 일치, linear Miner 규칙, chronology/sequence effects 제외에 대한 검토와 계산 사용 승인을 기록합니다.
- `declared_damage_limit`은 호출자 선언 값입니다. 기본 failure criterion이나 표준 허용치를 내장하지 않습니다.

## 계산 흐름

1. group ID 중복 여부와 curve·재료·scope 정합성을 확인합니다.
2. 각 group의 기존 `evaluate_ince_glinka_gsa_curve_life`를 호출합니다. 계산은 finite plane 및 curve support 안에서만 life를 반환합니다.
3. 첫 비계산 결과에서 중단하고 계산된 prefix 및 해당 group 결과를 보존합니다. 일부 group만의 Miner damage는 반환하지 않습니다.
4. 모든 group이 life를 얻으면 각 입력 cycle count / 계산 life를 기존 `miner_damage`에 전달하고 caller damage limit 대비 margin을 보고합니다.

## Python API

```python
from matintegrity.ince_glinka_gsa_miner_campaign import (
    InceGlinkaGSAMinerCampaign,
    evaluate_ince_glinka_gsa_miner_campaign,
)

request = InceGlinkaGSAMinerCampaign.model_validate(payload)
calculation = evaluate_ince_glinka_gsa_miner_campaign(request)
```

공용 registry 등록은 중앙 통합 단계에서 `specifications()`로 수행합니다.

## 결과 해석

출력에는 각 group별 입력·life-result digest, curve mapped life, Miner damage 및 전체 누적 damage가 포함됩니다. 각 GSA 요청의 representative-cycle 가정, curve interpolation 및 재료 적용성 검토가 계산의 전제입니다. cycle counting, 반복 횟수 할당, chronology, 비례·비비례 하중 경로의 상호작용, calibration transfer, 확률 해석 및 fatigue qualification은 수행하지 않습니다.

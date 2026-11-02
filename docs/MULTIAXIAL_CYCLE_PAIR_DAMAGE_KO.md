# 명시적 다축 피로 cycle pairing 및 Miner 손상

`fatigue.explicit_critical_plane_cycle_pair_damage`는 한 유한 후보 평면에서 독립 rainflow 계산된 정상응력 채널과 engineering shear-strain 채널을 사용자가 선언한 cycle map으로 연결한다. 원 신호를 함께 보았을 때 성립하는 pairing 규칙은 분석자가 따로 정하고 revision, 설정 digest, 검토 여부와 각 cycle 할당 수를 입력한다. API는 시계열상 cycle 대응을 자동으로 추측하지 않는다.

## 입력과 계산

입력의 `projected_rainflow_result`는 `fatigue.critical_plane_projected_rainflow` 결과 전체이며 SHA-256 digest로 고정한다. 선택한 `plane_id`에 `normal_stress`와 다음 중 하나가 있어야 한다.

- `engineering_shear_strain_directional_component`: 부호가 있는, 명시한 면내 방향의 engineering shear 변형률
- `engineering_shear_strain_vector_magnitude`: 비음수 전단 벡터 크기. 방향 정보는 이미 소실되므로 그 사용을 별도로 검토한다.

정상응력은 Pa, 전단 변형률은 무차원이어야 한다. 각각의 cycle에는 유한한 비음수 range, 유한한 mean(정상응력), 양의 cycle count가 필요하다. pair별 할당량은 양수여야 한다. 각 source cycle의 총 배정량이 원 count를 넘으면 거절한다. 선택한 두 채널의 모든 count가 pair map에 배정되지 않으면 부분 손상만 보고하고 aggregate를 보류한다.

pair마다 전단 변형률 진폭은 range/2, 최대 인장 정상응력은 `max(0, mean + range/2)`로 둔다. FS factor는

`gamma_a * (1 + k * sigma_n,max / sigma_normalization)`

이다. `k`, 정규화 응력, shear modulus, shear fatigue strength/ductility 계수와 지수, 유효 수명 구간은 caller가 재료·상태에 맞춰 제공한다. 기존 FS 수명 계산은 그 factor에 대응하는 수명을 보정된 cycle support 안에서만 반환한다. 어떤 pair라도 수명이 계산되지 않으면 total damage는 보류한다. 모든 pair의 수명이 유효할 때만 caller 선언 cycle allocation / pair life를 합한 선형 Miner 손상을 반환한다.

## 적용 경계

채널별 rainflow 표는 독립 투영 결과다. 여기의 pairing map은 사용자가 외부 근거에 따라 제공한 계산 입력이며 자동으로 유일하거나 물리적으로 참이라고 간주하지 않는다. Cycle pairing, allocation, engineering shear 해석, FS factor 관례, 재료 보정 및 Miner 축적 가정을 각각 검토해야 한다. 같은 원 시계열에서도 pairing 방법을 바꾸면 결과가 달라질 수 있다.

이 계산은 유한 평면 하나와 두 scalar cycle 채널로 제한된다. 전체 면의 최적화, 세 축 이상의 일반 비비례 피로 법칙, 상호작용·sequence effect, 평균응력 진화, overload/underload 기억, 대체 시간 재구성, 재료간 보정 이전, 독립 실험 자격화는 제공하지 않는다. Miner 값은 모델 가정에 따른 누적량이며 고장확률, FTA basic-event 확률, 수명 보증, 코드 합격 판정이 아니다.

## 연결

Python 계약은 `matintegrity.critical_plane_cycle_pairing.CriticalPlaneCyclePairDamage`와 `CriticalPlaneCyclePair`다. 계산 함수는 `critical_plane_cycle_pair_damage(request)`이며 registry ID는 `fatigue.explicit_critical_plane_cycle_pair_damage`다. 독립 사용 입력 예시는 `examples/model_inputs.json`의 같은 ID 항목을 참고한다. 결과 상태와 원 projection, pairing 설정, calibration digest를 계보 추적에 사용한다.

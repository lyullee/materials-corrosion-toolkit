# McDiarmid 지수의 가변진폭 블록 손상 합산

## 모델 식별자와 목적

`fatigue.mcdiarmid_calibrated_miner_campaign`은 여러 caller 정의 하중 블록에서 계산된 McDiarmid 유한면 지수를, 같은 재료 상태와 균열 케이스의 caller 지수–수명 곡선으로 변환하고, 명시적으로 제공된 블록 반복 수에 대해 선형 Miner 손상을 합산합니다. 적합된 지수–수명 데이터가 보간 구간에 없으면 추정하지 않고 실패 범위를 반환합니다.

## 계산 절차

1. 각 블록의 source 결과가 `fatigue.multiaxial_mcdiarmid_finite_plane_limit_screen`의 `computed` 결과인지 확인하고 전체 결과 digest 및 재료 상태·균열 케이스 일치를 검증합니다.
2. 해당 블록의 최대 유한면 지수 `D`를 caller 단조 보정표의 양의 지수 구간 안에서 로그–로그 선형 보간해 수명 `N(D)`를 얻습니다.
3. 각 caller cycle count `n`에 대해 `n/N(D)`를 계산하고 입력 순서대로 누적합니다. 정수 반복에서 caller 손상 기준을 최초로 넘는 위치를 반환합니다.

보정점 밖으로 외삽하지 않습니다. 지수 증가는 엄격히 단조 증가하고 보정 수명은 엄격히 감소하도록 입력 계약에서 제한합니다.

## 입력 및 증거

- 완전히 계산된 McDiarmid 면별 결과와 해당 전체 객체 SHA-256, 같은 물리 범위·asset·location의 순서 블록
- 동일한 재료 상태 및 crack case A/B에 대해 독립적으로 공급된 양의 지수–수명 보정점
- 제공자·revision·기록 ID·정규화된 보정 기록 digest·사용권 Evidence
- 정렬된 블록 순서, log–log 보간, 재료·범위 일치, 선형 Miner 가정 및 계산 사용에 대한 명시 검토

보정 기록 digest는 제공자 메타데이터, 적용 상태 및 모든 점을 고정합니다. 해당 곡선의 시험 타당성, 통계 적합성, 다른 온도·환경·geometry로의 이전 가능성을 입증하지 않습니다.

## 적용 경계

- 이 모델은 caller가 제공한 끝이 정해진 블록 집합만 계산하며, 미래 하중 또는 잔여 수명을 외삽하지 않습니다.
- Miner 선형 합산만 사용합니다. 하중 순서에 따른 overload·underload 효과, 비선형 상호작용, 기억 효과, crack growth 및 확률 손상을 계산하지 않습니다.
- 기초 McDiarmid 지수는 유한 응력 표본과 후보면 집합으로 계산된 근사값이므로, 시간·면 분해능과 해당 강도 criterion의 적용성은 별도 검토해야 합니다.
- 수명은 동일 상태/케이스 caller 데이터에서만 보간합니다. 결과는 조건부 스크리닝이며 안전성 합격·코드 적합·재료 qualification이 아닙니다.

## 독립 참고자료

- D. L. McDiarmid, “A Shear Stress Based Critical-Plane Criterion of Multiaxial Fatigue Failure for Design and Life Prediction,” *Fatigue & Fracture of Engineering Materials & Structures* 17 (1994), 1475–1484. [DOI: 10.1111/j.1460-2695.1994.tb00789.x](https://doi.org/10.1111/j.1460-2695.1994.tb00789.x)
- M. A. Miner, “Cumulative Damage in Fatigue,” *Journal of Applied Mechanics* 12 (1945), A159–A164. [DOI: 10.1115/1.4009458](https://doi.org/10.1115/1.4009458)

## API와 카탈로그 handoff

- Model ID: `fatigue.mcdiarmid_calibrated_miner_campaign`
- Schema version: `matintegrity.mcdiarmid_calibrated_miner_campaign.v1`
- Evaluator: `evaluate_mcdiarmid_miner_campaign(request)`
- Source ID 제안: `mcdiarmid_shear_stress_critical_plane_1994`, `caller_mcdiarmid_index_life_curve`, `caller_ordered_multiaxial_cycle_block_counts`, `linear_miner_damage_rule_for_mcdiarmid_campaign`

이 문서의 식 설명과 API 계약은 독립적으로 작성했으며, 참고문헌 문장을 복사하지 않았습니다.

# 검사·정비 행동의 기대손실 비교

## 목적과 경계

`inspection.action_expected_loss`는 한 물리 범위, 한 사건, 한 기간과 한 생존조건에서 완전하게
정의된 행동 대안을 같은 비용 기준으로 비교한다. 외부 열화·파괴·FTA·검사 의사결정 모델이 각
행동 뒤의 잔여 **기간 최초고장확률**을 계산하고, 사용자가 행동비용과 고장 발생 시 결과비용을
검토한 뒤 이 계산기에 전달한다.

계산기는 다음 식만 적용한다.

```text
행동별 총 기대손실 = 행동비용 합계 + 잔여 최초고장확률 × 고장 결과비용 합계
```

사건확률, 검사 검출성능, 검사 뒤 처분, 수리효과, 공통원인, 비용 또는 결과를 추정하지 않는다.
자원제약 일정, 다기간 정책, 상태별 의사결정나무, 정보가치, 위험회피 효용, 규격 합격도 이
계산기의 범위가 아니다.

## 입력 계약

- `event_id`, `event_definition`, `physical_scope_id`, `horizon_start_s`, `horizon_end_s`,
  `conditioning`이 모든 후보에 공통이다.
- 확률 의미는 `conditional_first_failure_in_period`로 고정한다. 시점 상태확률, 공간 초과확률,
  POD 또는 FTA에서 범위가 다른 사건을 직접 넣을 수 없다.
- 후보는 정확히 하나의 `baseline`과 하나 이상의 `intervention`을 포함한다. baseline 행동비용은
  0이어야 한다.
- 각 후보는 행동 정의, 행동효과 모델 ID·revision·입력 SHA-256, 잔여확률 점추정과 선택적 상한,
  그리고 가산 행동비용 구성요소를 보존한다.
- `probability_basis="upper_bound"`이면 모든 후보에 상한이 있어야 하고 각 상한은 점추정보다
  작을 수 없다.
- 결과비용과 행동비용은 `cost_basis_id` 및 `currency_or_normalized_unit`이 선언한 동일 기준이어야
  한다. 할인, 물가, 통화환산과 기대 운휴비용 여부는 호출자가 먼저 정리한다.
- 행동 정의, 잔여확률, 모든 비용·결과, 의사결정 기준의 검토 gate가 하나라도 거짓이면 산술을
  수행하지 않고 `needs_data`를 반환한다.

## 출력 해석

각 후보에 대해 사용 확률, 직접 행동비용, 기대 고장손실, 총 기대손실, baseline 대비 고장손실
감소, 증분 총손실과 순 기대편익을 원 입력 순서로 반환한다. 유일한 최소값만
`selected_action_id`로 반환한다. 두 값 이상이 사용자가 선언한 절대 비용 동률 허용차 이내이면
후보 ID를 모두 보존하고 `needs_data`로 멈춘다.

선택 결과는 공급된 숫자에 대한 산술상 최소값일 뿐이다. 행동효과 모델의 타당성, 비용의 완전성,
사회적·안전 위험허용도나 법규 적합성을 뜻하지 않는다. 안전 제약이 비용보다 우선해야 하는
업무에서는 해당 제약을 별도 상위 워크플로가 적용해야 한다.

## Python 예

완전한 입력은 `examples/model_inputs.json`의 `inspection.action_expected_loss`에 있다.

```python
from matintegrity import evaluate
from matintegrity.contracts import RunContext

result = evaluate(
    "inspection.action_expected_loss",
    payload,
    RunContext(asset_id=payload["asset_id"], location_id=payload["location_id"],
               time_basis="elapsed seconds"),
)
```

FTA와 연계할 때는 행동별 FTA를 같은 기초사건 범위·기간·conditioning으로 다시 평가하거나,
행동효과 모델이 바뀐 기초사건을 명시적으로 반영해야 한다. baseline의 상위사건 확률을 단순 비율로
낮추거나 POD를 바로 고장확률 감소율로 바꾸지 않는다.

## 외부 FTA·동적 신뢰성 결과 어댑터

`ActionEventProbabilityEvaluation`은 행동 ID·정의, baseline/intervention 역할, 평가자 ID·revision,
configuration/input SHA-256, 위험구조 ID, 계산 상태와 `EventProbability`를 보존한다.
`inspection_action_expected_loss_inputs`는 사용자가 먼저 선언한 전체 행동 ID 집합과 평가행·행동비용
키가 정확히 일치하는지 검사한다. 입력 순서와 무관하게 선언 순서를 복원한다.

모든 행동은 계산 완료 상태여야 하며 event ID, asset, 물리 범위, failure mode, 기간과 conditioning이
같아야 한다. 한 행동의 실패나 누락을 제거하고 나머지만 비교하지 않는다. 각 후보에는 외부 결과
digest, 위험구조 ID와 common-cause group ID가 남는다. 행동마다 다른 위험구조는 허용하지만 그
identity를 숨기지 않으며, 구조 변경의 공학적 타당성은 외부 모델과 검토자의 책임이다.

## 검사 결과별 처분 의사결정나무

`inspection.disposition_decision_tree`는 한 번의 검사 뒤 발생할 상호배타·완전분할 결과와 결과별
처분을 유한 합으로 축약한다. 각 `InspectionDispositionOutcomeBranch`는 결과확률, 처분 정의,
처분효과 모델 ID·revision·configuration/input/result SHA-256, 해당 결과와 처분을 조건으로 한
잔여 기간 최초고장확률 및 처분비용을 보존한다.

```text
기대 처분비용 = Σ 결과확률 × 결과별 처분비용
검사행동의 잔여확률 = Σ 결과확률 × 결과·처분 조건부 잔여확률
기대 행동비용 = 선행 검사비용 + 기대 처분비용
```

결과확률 합은 사용자 허용오차 안에서 1이어야 한다. 분기 수치와 처분을 모두 검토하지 않으면
산술을 보류한다. `inspection_action_candidate_from_disposition_tree_result`는 계산 결과를 기존
행동 기대손실 비교의 estimate-basis 후보로 변환하며 tree 결과 digest와 위험구조를 보존한다.
이 경로는 확률상한을 만들지 않으므로 별도 자격 있는 상한 없이는 upper-bound 비교에 사용할 수 없다.

POD, 오탐률과 결함 사전분포가 있어도 그것만으로 결과 분기확률이 정해지지는 않는다. 검사 procedure,
coverage, true state, 관측결과 및 처분 규칙을 연결한 별도 검토 모델의 출력만 입력한다. 현재 나무는
단일 검사·단일 기간의 고정 처분표이며 순차 관측, 재검사, 시간할인이나 자원제약 정책은 아니다.

## 다기간 고정 정책 경로 평가

`inspection.finite_policy_probability_calibration`은 실제 상태와 관측 라벨의 가중 쌍으로
`P(observation|state)`, 시간순 상태·행동·다음상태 기록으로 `P(next state|state,action)`을 추정한다.
동일 sequence와 source group을 calibration/holdout에 나누지 않으며, untouched holdout log loss와
multiclass Brier score를 보고한다. 미관측 conditioning row를 자동 완성하지 않고 명시적으로 승인한
대칭 pseudocount만 적용한다. `finite_policy_epoch_from_probability_calibration`은 이 결과와 별도 검토된
결정규칙·행동·failure 결과계수를 결합한다. 상태 truth, 행동 인과효과, 독립성이나 신뢰구간은 추정하지
않는다. 공개 연속 ILI 자료는 feature identity와 굴착 truth가 없어 이 보정에 사용하지 않는다.

`inspection.finite_policy_path_generation`은 검토된 유한 상태, 시작 생존조건부 초기분포, 시점별
상태조건부 관측분포, 관측별 고정 행동규칙과 상태-행동 전이분포를 정확히 전개한다. 각 확률족의 합은
1이어야 하며 실패상태로 가는 전이에만 결과비용 현재가치계수를 둔다. 비영 확률 경로를 모두 생성하고
실패 즉시 경로를 끝내며, 0 확률 분기만 생략한다. 경로 수가 사용자 한도를 넘으면 잘라내지 않고
`out_of_scope`로 중단한다.

`multi_period_policy_evaluation_inputs_from_generated_paths`는 생성 결과의 path manifest digest와 전체
경로를 기존 다기간 기대손실 계약으로 옮긴다. 상태·관측·전이·행동·비용·확률을 적합하거나 추정하지
않으며, 명시적 표 전개를 학습·실험보정 또는 정책 최적화로 해석하지 않는다.

`inspection.multi_period_policy_evaluation`은 외부 정책·상태전이 생성기가 만든 하나의 고정 정책을
완전한 유한 경로 집합으로 받아 평가한다. 각 경로는 시작 생존조건부 확률, source digest, 시간순
관측상태와 행동, 행동모델 revision/configuration/input digest, 시점비용과 사용자가 공급한 현재가치
계수를 보존한다. 고장 경로에는 기간 안의 최초고장 시각과 결과비용 현재가치 계수를 정확히 넣고,
고장 뒤 행동은 허용하지 않는다.

```text
경로별 할인 행동비용 = Σ 시점비용 × 현재가치계수
조건부 최초고장확률 = Σ 최초고장 경로확률
기대 총손실 = Σ 경로확률 × (경로별 할인 행동비용 + 경로별 할인 고장결과)
```

경로확률 합은 허용오차 안에서 1이어야 하며, 모든 manifest·확률·행동·고장사건·비용·할인 검토
gate가 참일 때만 계산한다. 이는 한 정책의 유한 기대값이지 정책 탐색이나 최적화가 아니다. 상태전이,
관측확률, 할인계수, 결과비용, 확률상한, 자원제약 또는 규격판정을 추정하지 않는다.

## 다기간 정책의 제약 우선 비교

`inspection.multi_period_policy_comparison`은 같은 사건·범위·기간·시작 생존조건·비용·할인 기준으로
외부 평가가 끝난 정책들을 비교한다. `inspection_policy_candidate_from_evaluation_result`는 고정 정책
평가 결과에서 policy/evaluator configuration·input·result digest와 기대손실을 보존하는 후보를 만든다.
확률상한이나 자원사용량은 이 어댑터가 추정하지 않으며 자격 있는 외부 값만 별도로 넣는다.

비교는 사용자가 승인한 최초고장확률 한도와 자원별 한도를 먼저 적용한다. 자원 ID·단위·점추정 또는
상한 기준은 모든 후보가 정확히 갖춰야 한다. 제약을 모두 통과한 후보 사이에서만 기대 할인 총손실을
비교하고 유일한 최소값을 반환한다. 가장 싼 후보가 안전확률을 위반하면 선택하지 않는다. 통과 후보가
없으면 제약을 완화하지 않고 `out_of_scope`, 비용 동률이면 임의 선택 없이 `needs_data`를 반환한다.

이는 사용자가 공급한 유한 후보집합 안의 제약 충족 최소값이다. 정책·상태전이·확률·자원사용량·상한·
비용·제약을 생성하지 않으며 전역 최적성, 실행 가능한 상세 자원일정, 위험 수용이나 규격 승인을
뜻하지 않는다.

## 검증과 남은 일

`scripts/validate_inspection_action_expected_loss.py`는 독립 작성한 세 행동과 정확한 비용을 직접
계산한다. 점추정에서는 검사, 상한에서는 수리가 최소가 되는 결과를 등록 계산기와 대조한다.
단위검사는 동률, 검토 gate, 상한 누락·순서, 중복 ID, baseline, 기간과 context 경계를 포함한다.
이는 산술·계약 검증이지 실제 검사효과나 경제성 검증이 아니다.

`scripts/validate_inspection_disposition_tree.py`는 결과확률 0.7·0.2·0.1, 처분비용 0·400·100,
조건부 잔여확률 0.10·0.01·0.05와 선행 검사비용 50을 직접 합산한다. 기대 처분비용 90,
총 행동비용 140, 잔여확률 0.077과 후보 변환을 대조한다. 이는 유한합 검증이지 실제 검사 결과나
처분효과의 보정이 아니다.

`scripts/validate_multi_period_inspection_policy.py`는 세 경로 확률 0.5·0.3·0.2와 시점별 비용·
현재가치계수를 독립 합산한다. 기대 할인 행동비용 236.5, 고장결과 160, 총손실 396.5와 조건부
최초고장확률 0.2를 등록 계산기와 대조한다. 실제 정책 생성, 전이·검사효과·비용·할인 또는 최적성의
검증은 아니다.

`scripts/validate_finite_policy_path_generation.py`는 초기상태 0.8·0.2, 상태별 clear/alert 관측,
monitor/repair 규칙과 전이표를 직접 전개한다. 7개 비영 경로의 합 1, 최초고장확률 0.064, 기대 행동비용
19.6, 할인 고장결과 57.6과 총손실 77.2가 생성→평가 경로와 일치한다. 이는 표 산술 검증이지 실제
상태·검사성능·전이·정책의 검증이 아니다.

`scripts/validate_multi_period_policy_comparison.py`는 세 정책 중 저비용 정책이 확률 한도를 위반하고,
다른 정책이 확률·outage 한도를 모두 만족하는 사례를 독립 분류한다. 제약 적용 뒤 유일한 정책과
최소 기대손실 450이 등록 계산기와 일치한다. 실제 정책이나 제약의 공학적 타당성 검증은 아니다.

후속 구현은 특정 외부 저장소의 실제 FTA/동적 신뢰성 export, 순차 검사·재검사 처분나무,
상태전이·관측 경로 생성, 상세 자원일정 최적화, 불확실 비용, 복수 안전·환경 결과 제약, 실제 비용 및
행동효과 독립검증이다.

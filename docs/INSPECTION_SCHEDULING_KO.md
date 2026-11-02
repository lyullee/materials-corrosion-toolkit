# 임계확률 기반 다음 검사시점

## 목적과 경계

`inspection.threshold_inspection_schedule`은 외부 열화·파괴·신뢰성 모델이 만든 누적 최초기준도달
확률곡선에서 다음 검사 후보 하나를 선택한다. 손상모델을 내부에 고정하지 않으므로 두께, 균열,
크리프 또는 사용자가 등록한 모델과 조합할 수 있다. 특정 규격의 검사주기·허용확률·비용·결과값은
포함하지 않는다.

이 계산기는 `conditional_first_failure_in_period` 의미만 받는다. 한 시점에서 임계두께 미달일
확률, 공간 pit 초과확률, POD 또는 FTA의 다른 기간 사건을 이름만 바꿔 입력하면 안 된다. 입력은
평가시점까지 사건이 발생하지 않았다는 동일 conditioning, 물리 범위, 사건 정의, forecast 모델
ID·revision·입력 SHA-256을 보존한다.

현재 바로 조합 가능한 상류 계산은 `reliability.sampled_linear_thickness_first_passage`다. 평가시점
생존을 조건으로 한 잔여두께-비음수 손실률 공동 표본을 선형 도달시각으로 변환한다. 이 계산은
점추정 누적확률만 내므로 일정의 `probability_basis="estimate"`와 조합하며, 신뢰상한 기준을 쓰려면
별도로 자격 있는 전 행 상한을 공급해야 한다.

## 선택 규칙

호출자는 엄격히 증가하는 후보시각과 비감소 누적확률을 제공한다. 각 행은 점추정치와 선택적 상한을
가진다. `probability_basis`가 `estimate`이면 점추정치, `upper_bound`이면 모든 행에 제공된 상한을
판정에 사용한다. 계산기는 다음을 순서대로 수행한다.

1. 평가시점에 최소 notice를 더한 시각부터 최대 deferral을 더한 시각까지 후보를 제한한다.
2. 사용자 승인 최대확률 이하인 후보만 남긴다.
3. 남은 후보 중 가장 늦은 행을 선택한다.
4. 다음 후보가 기준을 초과하면 `criterion_limited`, 확률곡선이 먼저 끝나면
   `forecast_boundary_limited`, 최대 deferral 경계가 제한하면 `maximum_deferral_limited`로 기록한다.

후보 사이 확률은 보간하지 않는다. 따라서 선택시각은 연속시간의 정확한 기준교차시각이 아니며,
후보 격자가 달라지면 선택값도 달라질 수 있다. 허용 창에 후보가 없거나 첫 후보에서 이미 기준을
초과하면 `needs_data`이고 검사시점을 만들지 않는다. 후자의 경우 더 이른 forecast 행 또는 즉시
사용자 결정이 필요하다.

## 필수 검토

- forecast identity와 입력 digest
- 사건·물리 범위·평가시점 생존 conditioning
- 누적 최초기준도달 확률곡선의 의미와 비감소성
- 조직 또는 사용자가 승인한 최대확률, notice와 maximum deferral

네 검토 gate 중 하나라도 거짓이면 `review_required`로 중지한다. 확률상한을 선택기준으로 쓸 때는
모든 후보에 상한이 있어야 하며 상한은 점추정치보다 작을 수 없다.

## Python 사용

```python
from matintegrity import evaluate
from matintegrity.contracts import RunContext

result = evaluate(
    "inspection.threshold_inspection_schedule",
    payload,
    RunContext(asset_id="asset-1", location_id="cml-7", time_basis="elapsed seconds"),
)
```

전체 입력 예제는 `examples/model_inputs.json`, 공개 계약은
`docs/schemas/ThresholdInspectionSchedule.json`과 `InspectionForecastPoint.json`에 있다. JSON은
필수 계산환경이 아니라 Python 프로세스, Slurm 작업과 다른 저장소 사이에서 동일한 identity·단위·
확률 의미·digest를 전달하는 휴대 가능한 형식이다.

## 검증과 미구현 범위

`scripts/validate_inspection_scheduling.py`는 독립 작성한 네 후보를 직접 순회한다. 최대확률 0.08에서
점추정 기준은 세 번째, 상한 기준은 두 번째 후보를 골라야 하며 계산 결과가 정확히 일치하는지
검사한다. 단위검사는 비증가 시각·확률, 불완전 상한, context 불일치, 검토 누락, 후보 부재와 이미
초과된 최초후보를 포함한다.

`scripts/validate_thickness_first_passage.py`는 작성 공동 표본의 도달시각과 질량을 직접 계산한 뒤
그 forecast를 이 일정 계산기에 전달해 기대 후보가 선택되는지 검사한다.

이 검증은 선택 알고리즘의 산술·계약 검증이다. 실제 부식률, 균열성장, 확률모델, 허용확률,
검사효과, 접근성, 비용, 결과, 수리·교체 의사결정 또는 현장 주기를 자격화하지 않는다. 여러 부위의
한 기간의 완전한 행동별 잔여 최초고장확률과 검토된 비용을 비교하는 첫 구성요소는
`inspection.action_expected_loss`로 구현했다. 행동별 FTA adapter, 검사결과별 처분나무, 다기간
정책, 자원제약과 실제 consequence-aware 최적화는 `reliability.risk_inspection`의 남은 범위다.
계약과 해석 경계는 `ACTION_RISK_COMPARISON_KO.md`에 있다.

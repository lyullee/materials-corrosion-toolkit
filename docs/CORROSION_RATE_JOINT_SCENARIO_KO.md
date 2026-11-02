# 부식률 공동 시나리오 두께 평가

`corrosion.rate_joint_scenario`는 표본으로 확인된 부식률 자료와 호출자가 구성한 완전한 부식률 시나리오 집합을 고정 선형 벽 손실 계산으로 연결한다. 반복 시편 표본은 `CorrosionRateSampleSummary`로 유지하고, 계산용 시나리오 속도·가중치·ID는 별도 배열로 입력한다. 두 자료 계보를 섞거나 표본 분위수를 임의 분포로 간주하지 않는다.

## 입력과 의미

- 각 시나리오는 균일 부식률 `scenario_rate_m_s`, `[0,1]` 범위의 가중치, 유일한 `scenario_id`를 갖는다. 배열 길이는 같고 가중치 합은 1이어야 한다.
- `scenario_source_digest`는 시나리오 자료 생성에 사용한 원 입력, 생성 설정, 모델 및 버전을 호출자가 canonical payload로 고정한 SHA-256이다. 모듈은 digest를 검증하지만 원자료가 그 digest에 대응하는지는 호출자 책임이다.
- `weight_meaning`은 현재 `caller_declared_scenario_weight`로 고정한다. 출력의 weighted threshold crossing mass와 weighted wall exhaustion mass는 이 가중치에 따른 합계다. 확률, 신뢰한계 또는 FTA 사건확률로 자동 해석하지 않는다.
- 재료상태, 조건 전이, 고정 선형손실 적용성에 각각 식별 가능한 검토 ID를 요구한다. 검토 표시는 사용자가 제공하며 적합성 자체를 증명하지 않는다.
- 현재 두께, 요구두께, 평가기간은 m와 s로 입력한다. 부식률은 전체 기간에 일정하고 공간적으로 균일하다고 둔다.

예제 입력은 `examples/model_inputs.json`의 `corrosion.rate_joint_scenario` 항목에 있다. Python에서는 `CorrosionRateJointScenario`와 `corrosion_rate_joint_scenario`를 직접 쓰거나 `default_registry().run()` / `run_json()`으로 실행한다. 반환값은 시나리오별 잔여두께, 요구두께 도달 시간, 기간 내 요구두께 도달(경계값 포함)·벽 두께 소진 표시, 가중 잔여두께 및 초과질량을 포함한다.

계산된 잔여두께가 요구두께와 같거나 작으면 요구두께 도달로 표시한다. `current_thickness_m - rate * horizon_s`가 0보다 작으면 결과는 `out_of_scope`다. 음수 두께를 유효한 잔여두께로 표시하지 않고 0으로 제한하되 관통 시나리오와 질량은 따로 기록한다. 현재 두께가 이미 요구두께 이하이면 도달시간은 0이다. 속도가 0이고 아직 임계에 도달하지 않았다면 해당 도달시간은 JSON 친화적 `null`로 반환한다.

## 위험성 모델과의 연결

FTA 또는 신뢰도 모듈로 전달하기 전에는 이 가중치가 어떤 표본추출·Bayesian posterior·전문가 가중치·결정론적 설계집합을 뜻하는지 별도 상위 계약이 명시해야 한다. 시간에 따른 최초도달과 생존조건을 가진 확률이 필요하면 정적 질량을 사건확률로 승격하지 말고 시간축·시편 상관·모델 불확실성을 정의한 reliability 모델을 사용한다. 이 API는 부식 기구, 국부공격, 응력, 하중, 검사·수리, 수용기준 또는 고장확률을 계산하지 않는다.

## 검증 계획

batch71은 배열 정합성, 가중치 합, 검토 게이트, 기간 후 잔여두께, 임계 초과질량, 벽 관통 상태, 입력·출처 계보 및 registry JSON API를 검사하도록 등록했다. 테스트는 사용자 지시에 따라 로컬에서 실행하지 않았으며 누리온 제출도 하지 않았다.

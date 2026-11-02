# 유한 다축 피로 시나리오 수명 envelope

`fatigue.multiaxial_life_scenario_envelope`는 이미 실행되어 `computed` 상태인 `fatigue.multiaxial_life_campaign` 결과 여러 개를 scenario 단위로 받아 수명 최소·최대와 witness를 반환한다. 이 모듈은 피로 수명을 다시 계산하지 않고 기존 결과를 묶는다.

## 입력 계보

각 `MultiaxialLifeScenario`에는 unique `scenario_id`, 전체 `AssessmentResult`, 그리고 `canonical_digest(result.model_dump(mode="json"))`를 넣는다. 원본 결과의 model ID/version, input/context digest, calibration digest, factor result digest, 재료 상태, cycle support 및 `RunContext` asset/location/time basis를 확인한다. 전체 ordered scenario payload에도 SHA-256과 matching provider Evidence가 필요하다. usage-rights Evidence와 license ID는 별도로 입력한다.

Scenario set은 각 row의 결합 상태를 유지해 평가한다. 파라미터별 독립 최솟값·최댓값을 섞어 허구의 시나리오를 만들지 않는다. 결과는 caller가 제공한 유한 scenario set에서 선택된 수명 extrema와 witness만 보고한다.

## 사용 의미와 제한

- 결과는 확률, 신뢰구간, 통계적 분위수, 연속 파라미터 구간 또는 재료 허용 수명이 아니다.
- 불확실성 분포나 scenario coverage를 추론하지 않는다. dependence와 coverage 검토는 caller가 선언한다.
- 각 scenario는 기존 등록 critical-plane life campaign의 계산 결과여야 한다. 계산 실패·범위 밖 결과는 envelope에 들어갈 수 없다.
- 모든 scenario는 동일한 계산 model revision, calibration digest, material condition, cycle support와 RunContext identity를 써야 한다.
- 개별 입력/calibration의 실험적 품질과 비비례 피로법칙의 적용성은 이 API에서 재검증되지 않는다.
- 아직 수치 테스트, 독립 benchmark 또는 실험 qualification을 수행하지 않았다.

# FTA·위험성 모듈 행동별 확률 공급 확장 요청

## 목적

상대 위험성 저장소가 baseline과 검사·정비 행동별로 같은 기간의 상위사건 잔여확률을 재평가해
`inspection.action_expected_loss`에 전달할 수 있게 한다. 이 요청서는 상대 저장소가 이미 변경됐거나
특정 FTA 구현을 자격화했다는 뜻이 아니다.

## 필요한 출력

행동마다 다음 정보를 하나의 JSON record로 제공한다.

- asset, 물리 범위, event ID와 사람이 검토할 수 있는 사건 정의
- horizon start/end, start까지 생존했다는 conditioning
- 확률 의미 `conditional_first_failure_in_period`
- action ID와 완전한 행동 정의
- evaluator/effect-model ID, revision, configuration 또는 input SHA-256
- 잔여 확률 점추정과, 실제로 계산한 경우에만 상한
- 계산 상태와 누락·적용범위 밖 사유
- 사용한 기초사건 ID·정의·기간·확률 의미·provider revision과 공통원인/의존 구조 identity

baseline과 행동별 결과는 같은 top-event 논리, 범위, 기간 및 conditioning을 사용해야 한다. 행동이
기초사건 또는 구조를 바꾸면 변경 집합과 새 digest를 남긴다.

## 금지할 암묵 변환

- POD 또는 검사 coverage를 곧바로 실패확률 감소율로 사용
- baseline 상위사건 확률에 임의 계수를 곱해 행동 결과 생성
- 점유확률, 공간 초과확률, 발생률 또는 상대점수를 기간 최초고장확률로 재명명
- 서로 다른 기간·범위·conditioning의 결과 비교
- 독립성을 가정하거나 공통원인 효과를 삭제하면서 그 가정을 기록하지 않음
- 규격 검사주기, 허용위험 또는 비용을 위험 모델이 임의로 내장

## 수신 검사와 완료 조건

MatIntegrity 측 수신 adapter `ActionEventProbabilityEvaluation`과
`inspection_action_expected_loss_inputs`는 구현됐다. 행동 ID 집합, 공통
event/scope/failure-mode/horizon/conditioning, evaluator revision/digest와 상태를 확인한 뒤 전체
후보만 구성한다. 실패 행동을 제외하고 나머지를 재정규화하지 않는다. 상대 저장소의 실제 export와
고정 revision end-to-end 검증은 아직 남아 있다.

부식 이력의 결정론적 두께 교차를 FTA 기본사건으로 연결하는 별도 공급 어댑터
`adapter.corrosion_rate_history_to_fault_tree_basic_event`도 추가됐다. 이 연결은 caller가 제공한
이벤트 확률·의미·conditioning·확률 scope·Evidence를 받아 `FaultTreeBasicEvent` 및
`IntegrityEventBasis`로 묶고, 원 부식 계산의 요청/result digest와 asset·location·time basis를
확인한다. 부식 감육량이나 교차시점에서 확률을 추정하지 않는다. 따라서 이 공급자 확장 요청은
새 확률 모델을 요구하지 않고, 상대 FTA 모듈의 이미 검토된 확률을 명시적인 증거와 함께 이 계약에
맞춰 내보내도록 한다. 인터페이스 개요는
`docs/models/CORROSION_RATE_HISTORY_FTA_BINDING_KO.md`를 참고한다.

FTA 공급자는 결정론적 건전성 조건과 확률 사건 사이의 mapping을 명시적으로 검토해야 한다.
특히 같은 자산·물리 범위·elapsed-time clock·기간 조건을 공유하는지 확인하고, 독립성 및
공통원인 구조는 별도 revision/digest로 제공해야 한다. 자동 추정 또는 기본 확률로 빈 입력을
메우지 않는다.

완료 조건은 다음과 같다.

1. 고정 리비전의 상대 저장소가 두 개 이상의 행동과 baseline을 기계 판독 JSON으로 내보낸다.
2. 작은 작성 FTA에서 독립 열거 또는 해석해와 확률을 대조한다.
3. 행동효과 없음, 완전 제거, 공통원인 잔존, 실패/누락과 ID mismatch를 검사한다.
4. 실제 데이터 보정, 모델 검증, 비용 검토와 소프트웨어 계약 검사를 구분해 기록한다.
5. 생성 JSON과 수신 결과의 digest를 end-to-end 검증에 고정한다.

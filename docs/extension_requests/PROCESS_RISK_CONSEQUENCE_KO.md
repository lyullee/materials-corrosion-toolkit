# process-risk-consequence-toolkit 연동 확장 요청

## 확인 범위

2026년 10월 28일 GitHub 공개 API에서 `lyullee/process-risk-consequence-toolkit`의 `main` commit
`4106da0020196fcf61c8b6264ae0598e63a881a1`을 읽기 전용으로 확인했다. 저장소는 Apache-2.0을
표시하고 source, release history, dispersion, effects, fire, explosion, conditional-risk 및 provider/workflow
JSON schema를 공개한다. 이 파일명·metadata 확인은 개별 물리 모델의 검증을 대신하지 않는다.

## MatIntegrity에서 제공할 release 전 상태

건전성 평가가 누출 또는 파단 source term을 직접 만들지 않는 경우가 기본이다. 연동 record에는 다음을
보존한다.

- asset/component/location와 failure-mode/event ID
- 평가 horizon과 conditional-first-failure semantics가 검증된 경우에만 `EventProbability`
- flaw/wall state와 계산 상태, geometry/material/provider support
- leak geometry 또는 release history가 외부 모델에서 생성됐음을 나타내는 provider ID/revision/digest
- pressure, temperature, composition의 absolute/gauge·total/partial basis와 clock
- MatIntegrity result/configuration digest와 source evidence tree

## consequence 결과 수신

- source/release/dispersion/effect 단계별 model ID, revision, status와 digest
- receptor/location/time basis, quantity/unit, averaging 또는 dose duration
- conditional consequence와 initiating-event probability를 곱했는지 여부
- grid/trajectory support, truncation·mass/energy balance와 convergence diagnostics
- failure/out-of-scope 행을 삭제하지 않은 완전한 scenario ID 집합

MatIntegrity의 검사·정비 행동 비교로 넘길 때는 consequence와 failure probability를 분리해 보존한다.
행동이 source term이나 isolation time을 바꾸면 effect model만 재사용하지 말고 전체 변경 계보를 남긴다.

## 시간변화 release history 연동

이번 로컬 어댑터는 고정 release rate 방식과 구별되는 구간별 시간변화 source history 요청을 생성한다. 대상은
고정 commit의 `ccps.release-history.v1` request/result schema다. 원격 저장소를 수정하거나 코드를 복사하지
않으며, 이 문서는 연동 권고 사항이다.

- 로컬 어댑터: `matintegrity.consequence_release_history_adapter`
- 요청 생성: `export_ccps_release_history_request`
- 계약: `CcpsReleaseHistoryInterval`, `CcpsReleaseHistorySource`, `CcpsDenseSubstance`,
  `CcpsDenseAtmosphere`, `CcpsDenseReceptor`, `CcpsReleaseHistorySettings`,
  `CcpsReleaseHistoryRequestEnvelope`
- 외부 대상: `lyullee/process-risk-consequence-toolkit@4106da0020196fcf61c8b6264ae0598e63a881a1`
- source catalog ID: `ccps_release_history_schema_bridge`
- 연동 식별자: `lyullee/process-risk-consequence-toolkit@4106da0020196fcf61c8b6264ae0598e63a881a1#ccps.release-history.v1`
- 외부 계약: `contracts/ccps.release_history_request.v1.schema.json` 및
  `contracts/ccps.release_history_result.v1.schema.json`

호출자는 각 source 구간의 시작·끝 시각과 질량 유량, 해당 이력 내 총 질량, 면적, 온도, 검증 근거,
물질 물성 근거, 기상 입력, 수용점, 계산 표본시각을 직접 제공해야 한다. 어댑터는 겹치지 않는 구간과
구간 적분 질량의 일치 여부를 검사한다. 구간은 0초부터 간격 없이 이어져야 하며, source가 없는 기간은
0 유량 구간으로 명시한다. 유한 source는 관측 창 종료 전에 끝나야 하고, 관측 창까지 이어지는 source는
마지막 시각까지 양의 유량을 유지해야 한다. 물성·대기·release 값을 추정하거나 단위를 임의 변환하지 않는다.

건전성 event의 확률·조건·시계 계보는 로컬 envelope에 보존하고 외부 계산 요청에는 넣지 않는다. 따라서
release mass는 사건확률이 아니며, wall loss나 균열 크기로부터 누출구경·유량·파단 시각을 계산하지 않는다.
source clock과 시간 기준은 외부 v1 source 계약에 필드가 없으므로 envelope와 provider request/result를
`request_digest`로 함께 보관해야 한다.

수신 측은 위 request 계약을 실행 가능한 공개 Python API로 제공하고, 전체 result 계약을 반환해야 한다.
응답에는 구간별 질량 장부, 시각별·수용점별 농도 이력, 계산 잔차, 꼬리 종료 상태와 적용성 상태를
손실 없이 전달한다. 실행 실패·미지원 입력·부분 수용점 결과도 제거하지 말고 명시적으로 남긴다.
로컬에는 아직 release-history 결과 importer나 외부 실행 경로가 없으므로, 이 어댑터는 요청 envelope
작성까지만 구현하며 end-to-end 연동 상태로 간주하지 않는다.

검토한 request/result schema 원문 byte digest는 각각
`025c2df40b84dbd75b30295f6445416032500db9a549b343fa2cf0ff656ce707` 및
`4085015227fdee8d2c9e04da06d1e64b5f4a60e5b6f28f913addac66069d2c6d`다. digest pin은 대상 파일의
동일성을 확인하는 용도이며 외부 코드의 라이선스나 물리적 타당성 판정을 대신하지 않는다.

## 금지할 자동 변환과 완료 조건

- wall loss 또는 crack size를 근거 없는 hole diameter나 instantaneous inventory release로 변환하지 않는다.
- consequence footprint 또는 fatality fraction을 failure probability로 사용하지 않는다.
- CoolProp state의 backend, composition, phase와 input pair가 다른 결과를 같은 상태로 합치지 않는다.
- public schema 존재를 end-to-end 통합 검증으로 표시하지 않는다.

완료하려면 상대 저장소의 고정 commit에서 provider request/result 또는 workflow schema로 작성 fixture를
내보내고, MatIntegrity의 `EventProbability`·action-risk 계약과 round-trip digest를 검사해야 한다. 정상,
누락, pressure-basis mismatch, clock mismatch, partial scenario failure와 no-effect action을 포함한다.

# FAD 시간 이력에서 FTA 사건으로 전달하는 확장 요청

## 현재 구현

`structural.failure_assessment_history`는 caller가 검토한 유한 시간 knot와 digest-pinned FAD boundary에서 `Kr/Lr`, 수직 FAD 여유, 최초 outside-boundary knot 및 인접 구간 bracket을 계산한다. Provider receipt는 quantity별 provider/result digest와 Evidence에 더해 asset/location/physical scope/clock/exact knot time/material condition/geometry basis/load-history ID를 담고, request의 해당 knot와 ID를 정확히 대조한다. Curve 밖으로는 extrapolation하지 않으며, 데이터가 빠지거나 범위 밖이면 부분 이력을 반환하지 않는다. 시간 보간, 확률, remaining life, code acceptance는 산출하지 않는다.

계산 API 문서는 `docs/models/FAD_ASSESSMENT_HISTORY_KO.md`, 코드 위치는 `src/matintegrity/fad_history.py`다.

## 후속 FTA 어댑터 요구

남은 확장은 이 계산 결과를 기존 `FaultTreeBasicEvent`/`IntegrityEventBasis`와 연결하는 별도 어댑터다. 정적 FAD 점 API를 이용하지 말고 정확한 `FADAssessmentHistoryRequest` 및 대응 `Calculation` 쌍을 요구한다. 어댑터는 원 요청을 다시 검증하고 완전한 결정론 계산을 재현해 canonical result digest를 대조해야 한다.

FTA 연결 시 caller가 사건 기준, 독립적으로 평가한 `conditional_first_failure_in_period` 확률, conditioning, shared probability scope, probability Evidence 및 rights boundary를 제공해야 한다. 이 probability는 FAD history로부터 추정하거나 조정하지 않는다. FAD history는 결정론적 경계 여유와 nominal knot crossing bracket만 제공한다.

어댑터는 다음 상태를 구분해야 한다.

- 요청 시작점에서 이미 FAD 경계를 벗어남: 기간 최초고장 사건에 쓰지 않고 거부
- 기간 시작은 inside/on이고 이후 최초 negative margin knot가 있음: 그 인접 knot 구간을 bracket으로 전달, 정확 시각은 보고하지 않음
- 제공된 구간에서 negative margin knot가 없음: caller가 확률 사건 정의를 독립적으로 명시한 경우에도 해당 계산 결과가 nominal non-crossing이었다는 점을 그대로 보존
- curve support 밖, 미검토, digest 불일치, scope/time/provider identity 불일치: FTA event를 만들지 않고 `out_of_scope`/`needs_data`

어댑터는 independence/common-cause/cut-set adequacy나 probability calibration을 대신 판단하지 않는다. 생성된 event는 FTA 평가 전에 downstream에서 기존 fault-tree event-scope 검토를 거쳐야 한다.

## 수용 기준

1. 기간 최초경계초과만 `conditional_first_failure_in_period`로 전달하고 기간 시작점부터 한계 초과인 이력은 거부한다.
2. caller probability를 바꾸거나 FAD 계산값에서 추론하지 않는다.
3. request/result digest, FAD curve digest, provider receipts, asset/location/physical scope/material/geometry/load/clock/horizon과 probability scope/evidence/rights를 모두 연결한다.
4. SCC→FTA 및 corrosion-rate→FTA adapter와 동일한 기존 `FaultTreeBasicEvent`/`IntegrityEventBasis` 계약을 사용한다.
5. event probability와 FAD nominal crossing status가 서로 다르게 보일 수 있는 불확도 모델 사용은 caller conditioning/statement로 명시하고, 어댑터는 그 적절성을 승인하지 않는다.
6. 별도 계약/연동 검증에서는 mismatch, tampering, initial-outside, crossing/no-crossing, curve-support edge, probability-meaning 및 rights-boundary 사례를 확인한다.

현재 이 확장 요청은 downstream 모듈 작업 명세일 뿐 FTA 어댑터 구현이나 다른 저장소 변경을 뜻하지 않는다.

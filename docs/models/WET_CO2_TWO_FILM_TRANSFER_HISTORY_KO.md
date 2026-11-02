# Wet-CO₂ 2막 전달 exact-knot 이력 API

## 목적

`matintegrity.wet_co2_two_film_transfer_history.v1`은 caller가 명시한 증가 시각마다 기존 정상상태 2막 전달 계산을 한 번씩 독립 호출한다. 각 knot는 그 시점의 fugacity, Henry 계수, 기막·액막 전달계수와 조건을 완전히 지정한다. 계산은 finite ordered table을 반환하며, 시각 사이의 상태를 만들지 않는다.

## Python API

```python
from matintegrity.wet_co2_two_film_transfer_history import (
    WetCo2TwoFilmTransferKnot,
    WetCo2TwoFilmTransferHistoryRequest,
    evaluate_wet_co2_two_film_transfer_history,
)
```

`WetCo2TwoFilmTransferKnot`에는 다음 두 값을 넣는다.

- `time_s`: history clock의 knot 시각
- `transfer_request`: 해당 시점의 완전한 `WetCo2TwoFilmTransferRequest`

각 nested request의 `time_s`는 knot 시각과 정확히 같아야 한다. History는 자산·위치·시간 기준을 명시하고, 요청 순서가 엄격히 증가하는지 검증한다. 시각을 자동 정렬하거나 누락된 knot를 삽입하지 않는다. 모든 knot의 asset/location은 outer history와 일치해야 하고, 평가 ID는 서로 달라야 한다.

적용 검토 플래그는 exact-knot 자료 대응, 각 점의 독립 정상상태 해석, knot 사이 보간·동역학 부재, prefix 실패 의미에 대해 별도로 받는다. 그중 하나라도 빠지면 `needs_data` 상태로 계산을 시작하지 않는다.

## 실행·계보 계약

각 점은 기존 `evaluate_wet_co2_two_film_transfer`에 그대로 전달된다. 입력 digest, Evidence/source IDs와 digest, nested result digest, 결과 값을 knot별로 보존한다. 모든 점이 성공하면 `complete_requested_history_returned=true`다.

첫 `needs_data` 또는 `out_of_scope` 결과에서 이후 knot 계산을 멈춘다. 완전히 성공한 앞선 시간행만 `committed_prefix`로 반환하고, 실패 knot는 별도 `first_failure`에 시간·인덱스·입력/계보/결과 digest와 상태를 기록한다. 실패한 시간행을 성공 prefix에 넣지 않는다.

## 해석 경계

- 각 행은 해당 입력 knot에서만 유효한 정상상태 2막 전달 계산이다.
- knot 사이의 시간 보간, 물질 축적, 기–액 평형 전파, 시간 적분 또는 대류·확산 동역학은 풀지 않는다.
- Henry convention, 물성·용매 조건의 일치, 접촉 면적과 기막/액막 계수의 적용성은 caller가 확인해야 한다.
- carbonate 종분화, 상평형 변화, scale, 표면 반응, 부식률, 금속손실, 구조 건전성 또는 위험확률을 계산하지 않는다.
- 표본 수가 많거나 행별 계산이 성공해도 시간 연속성·수렴·실험 검증·운전 자격이 입증되는 것은 아니다.

## ModelSpec 연결

`specifications()`는 `degradation.wet_co2_two_film_transfer_history` ID와 typed request/evaluator, 단위, 적용 가정 및 고유 source ID를 반환한다. Registry에 실제로 import/register하는 작업은 중앙 통합 단계에서 수행한다.

이 모듈과 문서만 추가했다. 테스트, 계산 실행, 패키징 및 공용 registry/catalog/schema 수정은 수행하지 않았다.

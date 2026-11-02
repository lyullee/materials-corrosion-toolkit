# 육안 표면검사 기록 계약

## 목적과 경계

`inspection.visual_surface_summary`는 육안검사의 절차와 관측을 다른 모듈이 읽을 수 있는 중립
계약으로 보존한다. 규격 본문·합격기준·결함 판정표는 포함하지 않는다. 계산 완료는 절차 적합성,
검사원 자격, 지시의 결함성, 합격, 수리 필요성, POD, 잔여수명 또는 고장확률을 뜻하지 않는다.

## 입력

`VisualSurfaceExamination`은 다음을 요구한다.

- examination, procedure 및 revision ID와 direct/remote 방식
- 표면 준비·상태, 조명과 분해능 확인의 사용자 근거
- 고유한 `VisualExaminationArea` 목록과 물리 위치, target/examined 면적
- 부분 검사 영역의 명시적 미검사 사유
- 고유한 `VisualSurfaceIndication`과 선언 영역·물리 위치·기술적 유형·자체 증거
- 영역 상호배타성, coverage, 표면상태, 지시 mapping의 검토 상태
- 지시가 없을 때 별도의 negative-result 검토

영역 중복을 자동 추정하지 않는다. 합산 coverage를 사용하려면 호출자가 영역의 상호배타성을
검토해야 한다. 검사면적은 target을 넘을 수 없고 부분 검사에는 사유가 있어야 한다. 지시 길이와
폭은 보고됐을 때만 저장하며 누락값을 0으로 만들지 않는다.

## 출력

계산기는 target·examined·unexamined 면적, coverage, 부분 검사 영역 ID, 보고 유형별 지시 수,
실제 치수가 있는 지시 수와 최대 보고 치수를 반환한다. 필수 검토가 없으면 관측을 버리지 않고
`needs_data`와 `missing_reviews`를 반환한다. 빈 지시 목록은 `negative_result_reviewed=true`일 때만
완료 상태가 된다. 완료된 음성 기록도 결함 부재나 검출확률을 뜻하지 않는다.

공개 스키마는 `VisualExaminationArea.json`, `VisualSurfaceIndication.json`,
`VisualSurfaceExamination.json`이다. 모든 모델과 마찬가지로 Python 객체, Python dict 또는 JSON
경로 중 필요한 방식을 선택할 수 있다. JSON 없이 Python 객체로만 실행하는 예는
`examples/visual_surface.py`다.

## 검증과 후속 확장

`scripts/validate_visual_surface.py`는 3.0 m² target 중 2.5 m² 검사 사례의 coverage 5/6을 독립
계산하고 출력에 합격·POD·고장확률 필드가 없음을 확인한다. 전용 검사는 면적 초과, 부분 검사 사유
누락, 중복 영역, 미선언 영역 지시와 검토 gate를 확인한다. 이는 실제 검사 성능 검증이 아니다.

침투·자분검사는 이 영역·위치·지시 기반을 재사용하되, 전처리·재료 적용성·침투/현상 시간 또는
자화 방향·매질·장비 확인을 각 방법의 별도 계약으로 추가한다. 육안 기록 필드를 억지로 재명명해
두 방법의 완료로 표시하지 않는다.

# 침투·자분 표면검사 계약

## 공통 경계

두 모델은 사용자 통제 절차와 관측을 다른 Python 모듈에 전달하는 기록 계약이다. 규격의 절차표,
허용치, 지시 분류·합격표는 포함하지 않는다. `SurfaceExaminationArea`는 target/examined 면적과
부분 미검사 사유를, `SurfaceIndication`은 영역·물리 위치·보고 유형·선택 치수와 자체 증거를
보존한다. 영역 중복 없음은 호출자가 검토한다. 빈 지시 목록도 별도 negative-result 검토가 있어야
완료된다.

## 침투검사

`inspection.liquid_penetrant_summary`는 visible/fluorescent, 제거 방법, cleaner·penetrant·remover
또는 emulsifier·developer batch, 재료와 표면상태, 전처리·건조, 절대온도, 침투시간, 과잉제거,
현상제 적용·현상시간, 관찰조명과 후세정을 보존한다. 재료/소모품 호환성, 공정 순서, 온도/시간,
표면상태와 지시 mapping을 각각 검토한다. 계산은 coverage와 기술 집계만 반환한다.

## 자분검사

`inspection.magnetic_particle_summary`는 강자성 적용성, dry/wet visible/fluorescent 매질과 batch,
carrier, 조명, 장비와 magnetization pass를 보존한다. 각 pass는 영역, technique, AC/DC 계열,
`[0, π)` field 방향, field adequacy 근거와 선택 전류를 갖는다.

사용자가 승인한 최소 방향분리와 각 영역의 최대 무방향 acute separation을 비교한다. 0°와 180°는
같은 선 방향이므로 분리가 0이며, 한 방향 또는 pass가 없는 영역은 불충분하다. 이 계산은 field의
크기·균일성·깊이 민감도나 절차 적합성을 스스로 증명하지 않는다.

## 검증과 사용

`scripts/validate_surface_examination.py`는 침투 coverage 0.75와 자분 방향 0.1 rad 대 π−0.2 rad의
무방향 분리 0.3 rad를 독립 계산한다. 전용 검사는 공정 검토, 음성기록, 면적·지시·pass ID,
미등록 영역, 방향 부족과 레지스트리 의미를 확인한다. 공개 스키마는 다섯 계약별 JSON으로
내보내며 `examples/model_inputs.json`에 두 등록 모델의 합성 입력이 있다.
JSON 없이 Python 객체만 사용하는 예는 `examples/surface_examination.py`다.

어떤 출력도 indication relevance, 결함 종류·깊이, 합격, 수리, POD, 잔여수명 또는 고장확률이
아니다. 실제 절차 공급자와 독립 인공결함/파괴 truth가 확보된 후에만 별도 검출성능 모델을 연결한다.

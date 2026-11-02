# 대기 노출·기상 공급자 확장 요청

## 목적

MatIntegrity의 1년 대기부식 입력을 현장·기상 프로젝트가 공급할 때 위치·기간·측정 및 재분석
자료의 의미를 잃지 않도록 한다. 현재 구현이 상대 저장소를 변경했다는 뜻은 아니다.

## 요청 출력

- `asset_id`, `location_id`, 외부 표면 범위와 공통 시간 기준
- 정확한 노출 시작·종료와 집계 방법
- 절대온도, 상대습도, 염화물 및 SO2 침적량과 SI 변환 전 원 단위
- 각 값의 측정·재분석·보간 구분, 공급자·버전·격자 또는 센서 ID
- 결측·검출한계·provider assumed-zero를 0과 구분하는 상태
- 원본 content SHA-256과 설정 digest
- 한 해 집계가 해당 재료 쿠폰·설비 위치와 동시인지 여부
- 검증 결과를 전달한다면 holdout source-group ID, 그룹별 표본 수·log-RMSE·absolute log-bias·보정 지원 이탈수와 개별 기준 통과 상태

## 금지되는 자동 연결

ERA5/Open-Meteo 공변량만으로 국부 표면 습윤, 염분 축적, 공식 깊이 또는 다년 부식속도를 만들지
않는다. MatIntegrity의 `transfer_criteria_met=false`를 소비자가 무시하거나 `computed`로 바꾸지
않는다. 평균 1년 손실을 구조용량, 잔여수명 또는 기간 고장확률로 직접 변환하지 않는다.
`source_group_transfer_criteria_met`가 false이거나 새 source-group 진단이 없는 legacy model도 검증을
통과한 것으로 취급하지 않는다. 작은 개별 출처의 실패를 전체 행 집계 지표로 숨기지 않고 그룹별 진단과
전역 gate를 함께 유지한다.

## 인수 검사

고정 공급자 리비전으로 동일 위치·기간·단위를 재현하고, 결측과 assumed-zero가 왕복 직렬화 후
보존되는지 확인한다. 보정 지원범위 이탈과 전이 기준 실패가 상대 서비스에서도 중지 상태로
유지되어야 한다. 실제 통합 검증 전에는 중립 JSON 계약 검사만 완료로 기록한다.
source-group별 진단이 있을 때 각 그룹 관측수 합은 holdout 전체수와 같고, calibration group과
교차하지 않으며, 그룹별 지원이탈 합계는 전체 holdout 이탈률과 일치하는지 확인한다.

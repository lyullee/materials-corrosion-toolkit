# Ti-12Mo-5Zr OCP 시간창 요약

## 목적

이 adapter는 허용 목록에 고정된 공개 기록의 한 OCP 모니터 행열을 입력받아 사용자가 지정한 시간 구간의 부호 보존 전위 기술량을 계산한다. 데이터는 로컬 archive에서만 읽으며 계산 결과는 해당 원자료의 대체물이나 새로운 실험 결과가 아니다.

## 입력과 계약

`Ti12Mo5ZrOCPWindowRequest`는 완전한 단일 workbook의 행 순서, provenance, archive/member digest, 헤더 및 행 수를 검사한다. 요청자는 `window_start_s`, `window_end_s`, 전위 기준 라벨과 근거, 선형 보간 검토 및 로컬 계산 권한을 제공한다. 시간 순서를 자동 정렬하거나 결측값을 채우지 않으며 지원 시간 구간 바깥은 거부한다.

## 산출량

`summarize_ti12mo5zr_ocp_window`는 경계점을 선형 보간하고 내부 원본 점은 그대로 보존하여 시작/끝 전위, 부호 있는 변화량, 시간 평균, signed 전위-시간 적분, 최소/최대값을 반환한다. 적분은 V·s 단위이며 전위 기준은 입력 라벨 그대로 전달한다. 기준 전극, immersion clock, 안정 상태, 전류, 반응 속도, 분극저항을 추정하지 않는다.

## 연동과 한계

행은 `ti12mo5zr_corrosion_data.iter_local_rows`로 읽은 뒤 이 모듈의 요청 계약에 전달한다. JSON 직렬화 가능한 `Calculation` 응답에는 요청 및 입력 행 digest가 포함된다. 이 descriptor는 부식률·재료 순위·수명·안전 승인·실패확률로 해석할 수 없다. 원본 workbook이나 파생 행을 배포하지 않는다. dataset citation/license는 catalog에 기재된 provider 기록을 따른다.

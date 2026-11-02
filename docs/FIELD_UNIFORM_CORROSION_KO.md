# 해안 노출 균일부식 초음파 자료 계약

## 자료와 권리

CEIT가 공개한 Zenodo 자료 `10.5281/zenodo.13897090`의 버전 1을 사용한다. 저장소
메타데이터는 CC BY 4.0을 명시한다. 원 JSON은 공개 소스와 wheel에 포함하지 않으며, 카탈로그의
고정 제공자 MD5와 취득 장부의 SHA-256으로 다시 받을 파일을 식별한다. 공개물에는 독립 작성한
reader, 출처·권리 기록과 원 관측을 복원하지 않는 집계 감사만 포함한다.

자료 설명은 해안 인근에 노출한 명목 5 mm 무도장 강재 시편 하나에 부착한 초음파 센서의 약
6개월 기록이라고 밝힌다. 제공자가 요약한 부식속도는 134 µm/year이다. 이 숫자는 파일 내부의
명시된 계산식이나 독립 치수 측정으로 재현되지 않으므로 참고 메타데이터로만 보존한다.

## 실제 파일 구조

고정 JSON은 49,918,087바이트이며 SHA-256은
`87033b35f7964eb34265e6e4e5f0e1252b2214480b6f39871029811e3e3dbf1b`이다. 하나의
S355 표식 시편, node `AA04`, piezo `V111`에 대해 2,715개 레코드가 있다. 파일 시계는
2022-02-22 12:01:10.833부터 2022-07-29 05:27:35.400까지 엄격히 증가하지만 시간대는
기록돼 있지 않다. 139개 달력 날짜 중 114일에는 20개 레코드가 있다. 따라서 저장소 설명의
“하루 두 번”을 레코드 수로 바꾸거나 반복 acquisition을 독립 시편으로 세지 않는다.

각 레코드는 provider ToF·온도 보정 ToF, 온도, 배터리, 진폭과 길이 2,048의 raw·filtered,
길이 64의 correlation, 길이 512의 envelope 배열을 갖는다. 모든 배열 값은 유한하지만 모든
raw 레코드에 ADC rail 값이 3~77개 있다. 포화 표본을 삭제·보간하거나 전체 신호가 유효하다고
표시하지 않는다.

## 공개 방법 근거와 교정 경계

같은 연구진의 공개 연구 `10.3390/app12020808`은 연속한 후면 에코의 왕복시간으로 두께를
계산하는 pulse-echo 경로를 설명한다. V111 종파 프로브를 사용했고, S355J2G3 무도장 기준
시편의 여덟 위치에서 마이크로미터 치수와 위치별 다섯 ToF 측정을 대조해 실온 음속
5950 m/s를 얻었다. 한 위치의 보고값은 25회 측정 평균이고 그 표준편차를 정밀도 지표로
사용했다. 이 공개 연구와 현장 JSON은 제공기관·강재 계열·프로브 모델·수치 규모가 서로
호환되지만, 현장 장치가 같은 zero correction과 음속 교정 계보를 물려받았다는 직접 증거는
아니다. 따라서 5950 m/s와 ns 단위를 현장 기본값으로 내장하지 않는다.

## Python API

`read_ceit_uniform_corrosion_field`는 원 순서와 엄격 증가 시계, 시편·센서 ID, 장치 코드,
네 신호 배열과 raw rail 개수를 보존한다. JSON은 ToF와 온도 단위를 자체 선언하지 않으므로
기본값에서는 `tof_s`·`ambient_temperature_K`를 만들지 않는다. 외부 근거를 검토한 호출자만
`reported_tof_unit="ns"` 또는 `"s"`, `reported_temperature_unit="degC"` 또는 `"K"`를
지정할 수 있다. 파형 sample interval도 호출자가 검토해 공급하지 않으면 시간축을 만들지 않는다.

`PulseEchoThicknessCalibration`은 교정 ID, 재료·시편·프로브 적용범위, 종파 음속과 교정온도,
zero offset, 입사각, 사용할 raw/보정 ToF 필드, 근거와 검토 상태를 고정한다.
`pulse_echo_thickness_observations(series, calibration=...)`는 다음 조건을 모두 만족할 때만
`remaining_thickness_m`을 만든다.

- reader에서 ToF 단위를 명시적으로 검토했을 것
- 교정의 시편·프로브 적용범위가 모든 레코드와 일치할 것
- 교정을 검토 완료로 표시했을 것
- 보정 ToF를 선택하면 온도보정 근거를 함께 기록할 것
- zero correction 뒤 왕복시간이 양수일 것

계산은 균질 종파의 선언된 경로에서 `thickness = c (ToF - offset) cos(angle) / 2`만 적용한다.
결과에는 교정 전체의 canonical SHA-256과 원 관측 ID를 보존한다. 이 변환은 부식속도를 적합하지
않고, 불확실성이 없으면 Bayesian 두께 갱신 준비 상태로 올리지 않는다. 현재 현장 자료에는 같은
시편의 독립 치수 참값·위치 ID·점별 불확실성과 장치 교정 계보가 없으므로, 제공된 공개 연구를
검토했어도 현장 두께·부식속도·잔여수명·고장확률은 계속 미자격 상태다.

사용자 보유 기준시편이 있으면 `inspection.pulse_echo_sound_speed_fit`으로 음속을 다시 구할 수 있다.
최소 세 calibration 관측과 별도 holdout 관측을 요구하고, 같은 물리 위치나 source group을 양쪽에
배치하지 못하게 한다. zero offset과 입사각은 적합하지 않고 검토된 고정값으로 둔다. 조건부
표준오차는 이 고정값과 기준치수·ToF의 오차를 포함하지 않는다. 출력 교정 조각은 의도적으로
미검토·무시편 범위이므로 사용자가 적용 시편과 전달 가능성을 승인해야 한다.

점별 기준치수와 왕복시간 표준불확실성이 모두 있으면 effective-variance 적합을 선택할 수 있다.
가중치는 `u(t)^2 + c^2 u(ToF/2)^2`의 역수로 반복 갱신하며 reduced chi-square와 holdout 표준화
잔차를 남긴다. 이 선택은 점별 독립 오차만 다루며 공통 zero offset이나 각도·온도·probe 계통오차를
독립 반복오차로 잘못 복제하지 않는다.

## 재현

```powershell
.\.venv\Scripts\python.exe scripts/fetch_data.py --ids ceit-uniform-corrosion-field
.\.venv\Scripts\python.exe scripts/inspect_ceit_uniform_corrosion_field.py
.\.venv\Scripts\python.exe scripts/inspect_ceit_pulse_echo_method.py
.\.venv\Scripts\python.exe scripts/validate_pulse_echo_thickness.py
.\.venv\Scripts\python.exe scripts/validate_pulse_echo_calibration.py
```

공개 집계는 `validation/ceit_uniform_corrosion_field.json`, 방법 근거 감사는
`validation/ceit_pulse_echo_method.json`, 독립 합성 항등식 검증은
`validation/pulse_echo_thickness_math.json`, 기준시편 적합·보류 분리 검증은
`validation/pulse_echo_calibration_math.json`에 기록한다. 다음 자격화 단계는 제공자 장치 문서에서
현장 JSON의 ToF 단위·`tof_c` 보정식·zero correction·교정 이력을 확인하고, 같은 시편·같은 위치의
독립적인 시작·종료 두께와 측정 불확실성을 확보하는 것이다. 그 전에는 후보 두께 범위를 진단값
이상으로 사용하지 않는다.

사용자 보유 교정을 넣는 최소 실행 예는 `examples/pulse_echo_thickness.py`, JSON 없이 Python
객체로 기준시편 음속을 적합하는 예는 `examples/pulse_echo_sound_speed_fit.py`, 교정 JSON Schema는
`docs/schemas/PulseEchoThicknessCalibration.json`에 있다. 예제의 수치는 API 형식 설명용이며
CEIT 현장 자료의 승인값이 아니다.

# 검사 증거 워크플로

이 문서는 검사·시험 결과를 원본 identity·단위·불확도·provider lineage와 함께 보존하는 네 계산기를 설명한다. 이 계산기들은 규격표, 결함 분류기, POD, 손상률, 수명이나 고장확률을 내장하지 않는다.

## 음향방출 campaign

`inspection.acoustic_emission_campaign`은 asset zone·좌표계·센서/채널 위치·결합 기록, calibration source, acquisition interval, event feature와 provider가 보고한 source location을 연결한다. Event 시각이 취득구간 밖이거나 비활성 channel을 참조하면 `needs_data`다. Feature는 exact key·unit token으로 caller support와 비교한다.

운영 중 event 수나 신호크기를 곧바로 결함, 누설, 균열 활성도 또는 위험사건으로 바꾸지 않는다. Source-location 불확도는 provider 결과이며 위치정확도 검증이 아니다.

## 복제 금속조직

`inspection.replica_metallography_evidence`는 replica site·복제면적·표면준비·microscope configuration, morphology descriptor, 정량 metric과 expanded uncertainty를 보존한다. Calibration/holdout/application source group을 구분하고 caller-owned morphology·값·불확도·면적 support를 비교한다.

Morphology 문자열을 재료등급, 상, 열화등급으로 자동 변환하지 않는다. 실물 조직과 replica 전사율, 시간별 변화, 시편독립성과 실제 creep 손상/파단자료가 없으면 수명 모델로 연결하지 않는다.

## 파괴인성 시험 증거

`inspection.fracture_toughness_test_evidence`는 material/condition, 물리 specimen·source group, geometry, notch/crack orientation, temperature, load rate, environment와 initiation·tearing·arrest·user-defined endpoint를 그대로 기록한다. 수치·단위·expanded uncertainty와 caller validity record, provider state/configuration/input/result digest를 보존한다. 동일 specimen이나 source group은 calibration/holdout/application partition을 넘을 수 없다.

이 경로는 표준의 specimen-validity 수치표를 내장하지 않고 endpoint 단위를 자동 변환하지 않는다. FAD 파괴저항, design value, 전이온도, 수명이나 확률로 쓰려면 별도의 자격화된 adapter와 적용성 검토가 필요하다.

## 극저온 누설시험

`inspection.cryogenic_leak_test_evidence`는 시험체·medium·absolute/gauge pressure basis, 비중첩 열사이클의 최저/최고 온도·압력, thermal-stabilization 근거와 background/control/test 관측을 연결한다. Quantified 값은 `value + expanded uncertainty`, below-detection 관측은 검토된 detection limit를 보수적 비교값으로 사용한다. Below-detection을 0으로 바꾸지 않는다.

온도·압력·medium·method·metric·unit support는 caller envelope의 값이며 범위 밖은 `out_of_scope`다. 이 요약만으로 누설원, 서비스 누설률, 검출확률, 열사이클 수명 또는 합격을 판단하지 않는다.

## 위험성 모듈과의 연동

검사 결과를 FTA나 신뢰성 모델에 넣기 전에 물리 범위, 사건 정의, 기간, survival conditioning, 검사 효과와 false-positive/false-negative 모형을 별도로 자격화한다. `computed`는 증거 계약이 완전하다는 뜻이지 정상·무결함·합격이나 낮은 위험을 뜻하지 않는다.

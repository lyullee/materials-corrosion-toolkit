# TOFD acquisition과 대칭 경로 기하

`inspection.tofd_acquisition_summary`는 사용자 관리 절차·리비전, 검사 물리 범위와 재료상태,
서로 다른 송신/수신 probe와 wedge, 측정한 probe index separation, 종파 속도와 국부 벽두께 근거,
encoder, 원 frame SHA-256, lateral/backwall arrival와 upper/lower diffraction pick을 보존한다.
기존 `inspection.tofd_depth`의 한 점 기하 계산은 호환을 위해 유지하지만 검사 기록 계약을 대신하지 않는다.

대칭인 평판에서 tip이 probe pair 중앙 아래에 있고 균질 종파 직선 경로가 적용된다는 사용자의 검토가
있을 때만 같은 frame의 lateral wave 이후 지연에서 깊이를 계산한다. probe index separation을 `S`,
종파 속도를 `v`, 지연을 `dt`라 하면 `q=v*dt/2`, `depth=sqrt(q*(S+q))`다. 선언 벽두께의 대칭
backwall 경로와 실제 backwall-lateral 지연에서 얻은 등가 깊이 차이도 진단값으로 남긴다.

upper/lower pick을 모두 명시한 indication은 두 깊이의 차와 lower-tip 기준 잔여 backwall ligament를
계산한다. 역할이 뒤집혀 lower가 더 얕으면 값을 교환하지 않고 `needs_data`로 둔다. lateral reference가
없거나 pick이 lateral보다 빠른 경우도 원 pick은 보존하고 깊이는 `None`이다. indication을 자산 위치와
연결하려면 physical location과 object-mapping basis가 함께 있어야 한다. indication이 없으면 별도
negative-result review가 필요하다.

encoder frame은 원 순서와 중복 위치를 유지한다. 이 모델은 waveform filtering, envelope, automated
time picking, probe field, wedge delay 보정, 곡면/비대칭 ray tracing, near-surface/backwall dead-zone,
결함 identity, 규격 합격, POD, 잔여수명 또는 고장확률을 만들지 않는다. 대칭 경로 산술이 맞아도 실제
절차와 교정이 자격화됐다는 뜻이 아니다.

공개 계약은 `TofdProbePair`, `EncodedTofdFrame`, `TofdDiffractionPick`, `TofdIndication`,
`TofdExamination`이고 실행 예제는 `examples/tofd.py`다. `scripts/validate_tofd.py`는 독립 작성한 5 mm와
15 mm tip, 25 mm backwall의 Pythagorean path identity를 검증한다.

## 공개 데이터 검토

Mendeley Data `10.17632/sggn77wv29.1`은 CC BY 4.0으로 2D 유한차분 이방성 다층 용접부 TOFD
simulation을 설명한다. 제공자 설명에는 30 mm 구간의 crack depth/length/thickness 4×4×4 조합,
80 mm 송수신 간격, 45°·5 MHz source, displacement field image·단면·A-scan이 명시돼 있다. 이는 물리
시험이나 독립 sizing truth가 아니다. 현재 landing page의 동적 file tree가 해소되지 않고 공개 file API는
인증을 요구하므로 filename·bytes·checksum을 추정하지 않고 metadata-only 후보로 등록했다. 합법적 파일
취득 뒤 좌표·시간 단위, 원 배열과 source geometry를 감사하기 전에는 solver 검증에도 사용하지 않는다.

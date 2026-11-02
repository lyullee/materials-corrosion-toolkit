# COQTEL 국부부식·Lamb-wave 자료

## 자료와 권리

COQTEL 자료 DOI `10.5281/zenodo.14193336`의 HDF5 두 파일을 제공자 MD5로 취득했다. 저장소와
연계 Data in Brief 논문 DOI `10.1016/j.dib.2025.111393`은 CC BY 4.0을 표시한다. 공개 패키지는
원 HDF5, 이미지, 파형, 전기화학 점별 행과 제공자 MATLAB 코드를 포함하지 않는다. 독립 작성한
reader, 인용·체크섬과 집계 감사만 배포한다.

## 물리적 관측 단위

자료는 두 개의 서로 다른 316L 판 실험이다. 각 판은 80×125×1.5 mm이며 파일 하나가 물리 시편
하나에 대응한다. 파일 내부의 `State_i`는 같은 시편의 반복 시간 상태다. 따라서 429개 상태를
429개 독립 시편으로 계산하지 않는다.

각 전기화학 행은 같은 번호의 파형 상태와 대응한다. 실험 1은 166상태, 실험 2는 263상태이며
상태마다 네 actuator의 5×2000 행렬이 있다. 신호 정의는 중심주파수 200 kHz, sampling 2 MHz,
5 cycles다. 행렬의 첫 행은 표본 시계, 둘째 행은 구동 신호, 나머지 세 행은 actuator를 제외한
PZT 번호 오름차순의 수신 신호로 읽는다.

전기화학 시계는 분을 초로 바꾸되 제공자 순서를 유지한다. 실험 1의 마지막 구간에는 같은 시각
10개, 실험 2에는 같은 시각 2개가 있다. 같은 시각의 전류·전위가 동일하다는 조건에서만
`duplicate_policy="preserve_identical"`을 허용하며 제거·평균·임의 시간 간격 생성은 하지 않는다.

## 알려진 교란과 누락 참값

연계 논문은 실험 2의 state 30~100에서 capillary 출구의 공기방울이 존재했다고 보고한다. Reader는
이 71상태를 `reported_air_bubble_interval`로 표시한다. 이를 삭제하거나 부식 손상으로 해석하지
않는다.

각 파일에는 root image 하나가 있지만 어느 `State_i`와 대응하는지와 길이 보정이 HDF5에 없다.
상태별 pit 반경·깊이·부피도 없다. 따라서 전류 적분 전하나 처음–마지막 파형 차이를 pit 치수,
부식속도, POD, 잔여수명 또는 고장확률의 정답으로 사용하지 않는다. 선택 시점의 광학 치수를
합법적이고 명확한 상태 매핑과 함께 별도로 확보하기 전에는 pit-sizing 보정을 진행하지 않는다.

## Python API

- `coqtel_electrochemistry`: source hash·실험·시편·상태 ID, 분→초 시계, 전류·전위, 중복시각,
  전하 적분, 교란 상태와 자격 경계를 반환한다.
- `coqtel_waveform`: 하나의 state·actuator·sensor를 명시적으로 읽고 receiver 행 순서, sampling,
  excitation과 교란 상태를 보존한다.
- `inspect_coqtel_experiment`: 전체 상태·파형 구조, 유한값, 시계와 source hash를 검사하고 원신호
  없이 집계만 반환한다.
- `waveform_change`: 같은 표본시계의 두 수신 신호에 대한 상대 L2 변화와 에너지비를 계산한다.
  이 값은 손상 크기나 확률이 아니다.

```powershell
.venv\Scripts\python.exe scripts\fetch_data.py --ids coqtel
.venv\Scripts\python.exe scripts\inspect_coqtel_data.py
.venv\Scripts\python.exe -m pytest tests\test_composition_signals_records.py -q
```

공개 집계는 `validation/coqtel_dataset.json`에 있다.

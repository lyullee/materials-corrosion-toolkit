# 다축·비비례 피로 공개자료 계약

## 자료와 권리

`ecp-multiaxial-fatigue`는 EN-GJS-600-3 구상흑연주철의 축·비틀림 조합 피로자료다.
고정 공개 record는 <https://doi.org/10.5281/zenodo.14198237>이고 제공자는 CC BY 4.0을
선언한다. 28개 tab-separated 파일 9,032바이트를 제공자 MD5와 대조해 취득했다. 원 파일과
점별 변환값은 로컬 제외 경로에 두며 공개 소스에는 취득 장부, reader, 집계와 해시만 둔다.

자료 record는 연결 논문, 작성자 코드와 재사용 시 인용 대상을 별도로 제시한다. 데이터셋
라이선스를 논문 본문·그림이나 다른 원 관측의 권리로 확대하지 않는다. 작성자 MATLAB
구현은 이 패키지에 복사하지 않았으며 Python reader는 파일 계약에 맞춰 독립 작성했다.

## 행과 관측 단위

각 시험 조건은 FS와 SWT 두 파일에 반복된다. 두 파일은 같은 `Nf_exp` 열을 같은 순서로
보존하고 각 방법의 ECP factor와 provider prediction만 다르게 기록한다. 따라서 28파일의
294행은 294개 독립 실험이 아니다.

`read_ecp_multiaxial_fatigue`는 다음 세 표를 반환한다.

- `configurations`: 14개 파일 조건. 원 `ASS`, `TOR`, `MULTI` load code, blunt/sharp,
  위상 0°/45°/90°, biaxiality ratio, stress ratio를 보존한다.
- `experimental_observations`: FS/SWT pair에서 한 번만 만든 147개 보고 수명 관측이다.
- `processed_method_rows`: FS 147행과 SWT 147행의 factor·예측값이다. 모두
  `provider_processed_same_study`이며 독립 검증값이 아니다.

```python
from matintegrity.multiaxial_fatigue_data import read_ecp_multiaxial_fatigue

loaded = read_ecp_multiaxial_fatigue("data/raw/ecp-multiaxial-fatigue")
observations = loaded["experimental_observations"]
processed = loaded["processed_method_rows"]
```

`article_local_observation_id`는 두 방법 파일의 대응을 위한 행 ID다. 실제 시편 ID가 아니며
동일 ID 또는 서로 다른 ID가 물리적 독립성을 증명하지 않는다. 파일에는 물리 시편 ID,
검열 표식, 종료 정의, 국부 stress/strain tensor history, FE mesh가 없다. 해당 항목은 `null`
또는 검토 필요 상태로 유지하며 명목 조건이나 행 번호에서 만들어 내지 않는다.

## 현재 활용과 금지되는 해석

이 자료는 다음 용도로 사용할 수 있다.

- 비례 및 45°·90° 비비례 조건을 보존하는 데이터 계약 검사
- FS/SWT 처리결과와 실험수명의 중복 없는 연결
- 원 논문·프로토콜 검토 뒤 조건별 보정/보류 분할을 설계하기 위한 후보 목록

현재 상태에서 다음은 할 수 없다.

- provider prediction을 독립 검증으로 다시 평가
- 모든 보고 수명을 확인된 파손 또는 모든 행을 독립 시편으로 간주
- 명목 load code에서 국부 노치근 tensor history를 재구성
- 제공자 ECP factor를 이 패키지의 임계면 구현 정답으로 사용
- 피로수명, 설비 고장확률 또는 규격 합격을 자동 생성

후속 구현에는 연결 논문의 시험 끝점·runout 정의, 시편·반복 관계, 보정에 사용된 조건,
재료 물성, 국부 장 이력과 control-volume 절차의 독립 검토가 필요하다. 그 뒤에도 보정 조건과
독립 보류 조건을 분리하고, 공개되지 않은 FE field를 임의 생성하지 않는다.

## 재현

```powershell
.venv\Scripts\python.exe scripts\register_zenodo.py 14198237 ecp-multiaxial-fatigue `
  --category multiaxial_fatigue --limitation "review required"
.venv\Scripts\python.exe scripts\fetch_data.py --ids ecp-multiaxial-fatigue
.venv\Scripts\python.exe scripts\inspect_ecp_multiaxial_data.py
```

이미 등록된 카탈로그에 `register_zenodo.py`를 다시 실행하면 중복을 거절한다. 재취득은 등록
단계를 반복하지 않고 `fetch_data.py`부터 실행한다. 고정 집계와 파일별 SHA-256은
`validation/ecp_multiaxial_dataset.json`에 있다.

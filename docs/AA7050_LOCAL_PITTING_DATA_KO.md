# AA7050 국부 공식 자료 계약

## 자료와 권리

[Mendeley Data 자료 v1](https://data.mendeley.com/datasets/hhf5sfk5bj/1)은 AA7050 시편 01의
국부 공식 형태와 미세역학 장을 담은 네 MAT 파일을 CC BY 4.0으로 공개한다. 카탈로그에는 DOI,
라이선스 링크, 제공자 파일 URL, 바이트 수와 SHA-256을 고정했다. 원 MAT는 `data/raw/`에만 두고
wheel·sdist·source-review ZIP에는 포함하지 않는다. 공개 코드와 문서에는 출처·해시·구조 감사 및
변환 사실만 남긴다.

[연계 논문](https://doi.org/10.1016/j.corsci.2019.03.016)의 공개 서지·초록·data-availability 설명은
전체 연구가 AA7050-T7451 TS 시편 세 개의 microstructure, strain, crystal-plasticity 모델 유도 stress와 표면 형태를
같은 관심영역에서 다뤘다고 밝힌다. 현재 공개 MAT 묶음의 제목과 파일은 그중 specimen 01을
지칭하므로 이 묶음을 세 개 독립 시편 자료로 확대하지 않는다.

제공자 설명상 관측 단위는 한 AA7050 시편의 같은 300×400 µm 관심영역과 2일·6일 노출이다. 배열의
각 픽셀을 독립 시편으로 세지 않는다. 두 시점은 일반적인 시간 전이, 부식속도 분포 또는 Markov
확률을 식별하기에 충분하지 않다.

## 안전한 로더

`matintegrity.pitting_data.read_local_pitting_numeric_mat`은 호출자가 고정한 SHA-256이 일치하는
MATLAB level-5 파일의 최상위 실수 수치 배열만 읽는다. 다음 자료는 거절한다.

- MATLAB struct·cell·object·sparse·복소 배열
- HDF5 기반 v7.3 MAT
- 128 MiB 초과 파일 또는 256개 초과 최상위 변수
- 체크섬 불일치, 알 수 없는 변수에 붙인 단위, 근거 없는 좌표 정합 주장

로더는 원 변수명·MATLAB class·NumPy dtype·형상·유한/비유한 개수·유한 최소/최대를 기록하고
배열 복사본을 반환한다. 전치·재표본화·정합·필터·threshold·결측치 대체·단위 변환을 수행하지
않는다. 단위와 변수 의미는 변수별 근거를 호출자가 명시해야만 붙일 수 있다.

```python
from matintegrity.pitting_data import read_local_pitting_numeric_mat

result = read_local_pitting_numeric_mat(
    "data/raw/aa7050-local-pitting-evolution/TSS01_stressCropped.mat",
    expected_sha256="4c7f8c0280fe66ee588ba16196072ce61bb1fea8a25d91eaccc918abf246b31f",
    dataset_id="aa7050-local-pitting-evolution",
    physical_specimen_id="provider-aa7050-specimen-01",
    source_group_id="mendeley-hhf5sfk5bj-v1-one-specimen",
    source_role="stress_field",
)
```

## 현재 구조 감사

네 파일 127,766,005바이트의 SHA-256은 제공자 값과 모두 일치했다. 응력 파일은 level-5 MAT이며 `szz`, `szy`,
`szx`, `syy`, `syx`, `sxx`, `spr`, `s1`, `s2`, `svm`의 float32 배열 10개가 있다. 모든 배열은
230×291이고 각 66,930개 값이 유한하다. 짧은 변수명만으로 응력 정의·부호·좌표계·단위를
확정하지 않았으므로 현재 단위는 비어 있다. 수치 범위도 물리적 MPa 범위라고 재명명하지 않는다.

Strain 파일은 `exx`, `eyy`, `exy`, `e1`, `e2`, `epr`, `evm`의 851×1,199 float32 배열 7개다.
2일·6일 형태 파일은 각각 `CORROSIONnew` 2,845×3,931과 2,849×3,968 배열 하나를 가진다. 전 배열의
값은 유한하지만 형태 두 시점의 shape부터 다르고 strain·stress grid도 서로 다르므로 직접 index-wise
정렬·차분·상관을 수행할 수 없다. 현재 기계판독 기록은
`validation/aa7050_local_pitting_dataset.json`이다.

```powershell
.\.venv\Scripts\python.exe scripts/inspect_aa7050_pitting_data.py
```

## 후속 자격화 순서

1. 네 파일의 제공자 SHA-256과 완전한 변수·형상·비유한 상태를 감사한다.
2. 1차 자료의 data dictionary로 좌표축, 길이 단위, 표면 높이 부호, 응력·변형률 정의와 단위를
   변수별로 검토한다.
3. 2일·6일 형태 배열이 동일 물리 grid인지 확인하고, 필요한 경우 제공자가 명시한 정합 변환만
   별도 계약으로 기록한다.
4. pit 정의와 threshold는 연구 목적에 맞게 사전 선언하고 민감도를 보고한다. 한 시편의 공간
   픽셀을 calibration/holdout으로 무작위 분할해 독립 검증으로 부르지 않는다.
5. 성장·확률·FTA·수명으로 연결하려면 별도 독립 시편과 노출 시점, 검열·측정 불확실성 및 외부
   검증을 추가한다.

같은 연구의 stress·strain은 설명 공변량 후보일 뿐 독립 truth가 아니다. 특히 stress는 연계 논문이
설명하는 crystal-plasticity 유도 장이므로 직접 측정된 독립 응력 truth로 바꾸지 않는다. 동일 형상만으로 배열 정합을
승인하지 않으며, 이 자료만으로 행동효과·POD·구조 합격을 만들지 않는다.

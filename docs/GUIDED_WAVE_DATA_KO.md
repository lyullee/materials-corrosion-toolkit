# 배관 유도초음파 자료 계약

## 목적과 공개 경계

`guided-wave-pipeline-shm`은 한 실험실 강관에서 반복 취득한 유도초음파 응답 자료다. 자료 제공자는
CC BY 4.0을 선언하며 고정 record는 `10.17632/ttb63krg6d.1`이다. MatIntegrity는 원 ZIP과 점별
파형을 공개 배포물에 넣지 않고, 독립 작성 reader·출처·체크섬·집계 감사 결과만 배포한다.

이 자료는 잔여두께 측정표가 아니다. 전압 응답을 Bayesian 두께 갱신, 부식률, 결함 크기, POD 또는
고장확률에 직접 넣지 않는다. 별도의 교정시험과 관측모델이 생길 때만 동일 물리 위치·주파수·장치
설정·기준 신호를 보존한 새 공급자로 연결한다.

## 고정 자료에서 확인한 구조

- 외부 ZIP: 103,000,407바이트, SHA-256
  `cf24cb3f1bb79e7c3a37502f5f5c392b6ca8b1a0a35f6e2b04758a1ffa4340fb`
- 내부 ZIP: 106,412,391바이트, SHA-256
  `0bb1b7e58ca71fc438785c0ba71f07174a34983bef8c2498b3c558b1f361a184`
- acquisition workbook 236개, 신호 sheet 1,180개
- 각 workbook의 주파수: 14, 18, 24, 30, 37 kHz
- 각 sheet: 실제 2,509행 × 4열이며 앞 두 행은 label/header, 숫자 표본은 2,507행
- 전체 숫자 신호행: 2,958,260행
- 제공자 sheet 순서는 9종이므로 위치가 아니라 sheet 이름으로 주파수를 읽는다.
- 모든 sheet의 거리 grid는 동일하지만 한 구간이 정확히 반복된다. reader는 정렬·삭제하지 않고
  `repeated_distance_intervals=1`로 보존한다.
- 논문 설명의 2,057 × 4와 실제 2,509 × 4 차이는
  `article_shape_discrepancy=True`로 남긴다.
- `pure DAC` 열은 전수 0이지만 삭제하지 않고 공급자 처리 채널로 유지한다.

논문에서 처음 207개는 건강 상태 기간, 뒤 29개는 순차 가공 손상 이후로 설명된다. 이 207/29
구간 표시는 고정 SHA-256 원본에만 적용한다. 파생 archive나 검토 비활성화 경로는 모두
`unreviewed`다. 29개 파일을 여섯 가공 단계에 나누는 대응표, acquisition 시각, 실제 온도,
가공 치수와 잔여두께는 workbook에 없으므로 `None`으로 유지한다. 반복 acquisition은 하나의
보고 실험관에서 나온 것이며 236개 독립 시편으로 세지 않는다.

## Python API

```python
from matintegrity.guided_wave_data import (
    list_guided_wave_acquisitions,
    read_guided_wave_acquisition,
)

archive = "data/raw/guided-wave-pipeline-shm/ttb63krg6d-1.zip"
inventory = list_guided_wave_acquisitions(archive)
observation = read_guided_wave_acquisition(
    archive,
    1902,
    specimen_id="published-single-steel-tube",
)
```

`list_guided_wave_acquisitions`는 XLS를 열지 않고 archive·member·acquisition ID를 검사한다.
`read_guided_wave_acquisition`은 지정 workbook 하나만 읽는다. 전체 감사나 사용자가 명시한
batch 처리에는 `iter_guided_wave_acquisitions`를 사용한다. reader는 다음을 거절한다.

- 고정 모드에서 다른 외부 SHA-256
- 경로 이탈·역슬래시·중복·암호화 ZIP member
- 외부 ZIP의 복수 파일 또는 XLS가 아닌 내부 파일
- 중복 acquisition ID, 잘못된 workbook·sheet 이름
- OLE BIFF가 아닌 member, 달라진 header·열 수·주파수 집합
- 비수치·비유한 신호 또는 감소하는 거리축
- 비어 있는 호출자 physical specimen ID

파생 archive는 `require_pinned_hash=False`로 읽을 수 있지만 원본 상태 구간을 자동 상속하지 않는다.
`expected_archive_sha256`로 조직 내부의 별도 고정본을 검증할 수도 있다. 어느 경우든 호출자는
하나의 실제 관을 나타내는 `specimen_id`를 직접 제공해야 한다.

## 두 acquisition의 기술 특징

Reader 결과 두 개는 `guided_wave_pair_feature_inputs`로 등록 계산기 입력에 조합한다.

```python
from matintegrity.adapters import guided_wave_pair_feature_inputs
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

inputs = guided_wave_pair_feature_inputs(
    baseline,
    observation,
    frequency_Hz=14_000.0,
    wave_mode="torsional",
    window_start_m=2.0,
    window_end_m=3.2,
    duplicate_distance_policy="mean_aligned_duplicates",
)
result = default_registry().run(
    "inspection.guided_wave_pair_features",
    inputs,
    RunContext(
        asset_id="published-single-steel-tube",
        location_id="positive-distance-window",
        time_basis="provider acquisition order",
    ),
)
```

Adapter는 같은 dataset·archive·physical specimen인지, acquisition ID가 다른지, 요청 주파수가 정확히
하나인지 확인한다. 계산기는 두 거리 grid가 호출자 허용오차 안에서 정렬됐는지 검사하고 보간하거나
정렬하지 않는다. 반복 거리 위치도 두 신호에서 같아야 한다. `preserve_samples`는 원 표본을 유지하고,
`mean_aligned_duplicates`는 연속된 동일 거리 쌍만 각각 평균하며, `reject`는 선택 창 안의 반복을
적용 범위 밖으로 반환한다.

출력은 baseline·observation·residual RMS, baseline으로 정규화한 residual RMS, 전압 제곱합 비,
Pearson 상관, 최대 절대차와 부호 평균차다. 영 baseline 에너지의 비율과 분산이 없는 파형의 상관은
숫자를 만들지 않고 `None`으로 유지한다. 단일 baseline은 결합 상태·환경·장치 변화와 실제 손상을
분리할 수 없으므로 이 descriptor를 결함 크기, 잔여두께, 손상 확률이나 합격값으로 바꾸지 않는다.

세 개 이상의 baseline은 `guided_wave_reference_ensemble_inputs`로 조합할 수 있다. 모든 record는
같은 dataset·archive·physical specimen이어야 하고 baseline ID는 고유하며 observation ID와 겹치지
않는다. 호출자는 baseline/observation source group과 baseline 선택 근거를 작성한다. 등록 계산기
`inspection.guided_wave_reference_ensemble`은 mean 또는 median 점별 reference, baseline spread RMS,
각 baseline을 하나씩 제외한 leave-one-out residual RMS 분포와 observation residual의 상대 비를
반환한다. 영 spread나 영 leave-one-out 기준의 비는 `None`이다.

이 계산은 반복 건강 acquisition의 내부 변동을 단일 baseline보다 잘 드러내지만, 동일 관의 반복을
독립 시편으로 만들지는 않는다. 선택된 ensemble의 최대값이나 95% 표본 분위수도 검출 임계값,
거짓경보율, 이상확률 또는 POD가 아니다. 그런 해석에는 여러 독립 시편·장치·환경·결함 크기와
사전 지정 calibration/holdout 설계가 별도로 필요하다.

## 재현과 검증

```powershell
.\.venv\Scripts\python.exe scripts/inspect_guided_wave_data.py
.\.venv\Scripts\python.exe scripts/validate_guided_wave_features.py
.\.venv\Scripts\python.exe scripts/validate_guided_wave_reference_ensemble.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_guided_wave_data.py tests/test_guided_wave_features.py
```

전수 집계는 `validation/guided_wave_pipeline_dataset.json`에 기록한다. 합성 legacy XLS fixture는
sheet 순서 독립성, archive 안전성, schema 변조, 반복 거리, digest와 상태 구간 gate를 검사한다.
전수 감사는 원본의 236 workbook과 1,180 sheet를 모두 읽지만 원 파형은 검증 JSON에 복제하지
않는다. 이는 구조·소프트웨어 검증이지 손상 검출·위치·크기 또는 현장 성능 검증이 아니다.

실자료 기술 비교는 1622를 baseline, 1901을 같은 건강기간의 후반 기록, 1902와 1930을 각각 첫·마지막
가공 후 기간 기록으로 선언해 14 kHz의 두 모드를 +2.0~+3.2 m에서 계산한다. 이 선택은 여섯 가공
단계나 실제 결함 치수의 대응을 뜻하지 않는다. 건강기간 내부 비교에서도 상당한 residual이 있으므로
가공 후 residual만으로 분류 임계값을 만들지 않는다. `validation/guided_wave_pair_features.json`에는
집계 descriptor와 digest만 있고 공개 배포에서 제외한 점별 전압 배열은 없다.

다중 baseline 검증은 건강기간 전체에 분산해 미리 고정한 acquisition 1622, 1673, 1700, 1750,
1800, 1850, 1890의 median reference를 사용한다. 1901 건강기간 후반, 1902 첫 가공 후 기간,
1930 마지막 가공 후 기간을 같은 14 kHz·두 모드·공간창에서 비교한다. 1930 flexural의 residual은
baseline leave-one-out 최대의 약 1.10배지만, 한 관·미확정 조건·미제공 단계/치수만으로 임계값이나
손상 검증을 만들지 않는다. 집계는 `validation/guided_wave_reference_ensemble.json`에 있다.

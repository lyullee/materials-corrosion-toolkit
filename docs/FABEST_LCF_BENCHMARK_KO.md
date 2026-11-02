# FABEST LCF 벤치마크 연계

## 범위

이 기능은 42CrMo4+QT 강의 단축 저주기 피로 벤치마크와 연결되는 세 가지 계산 계약을 제공한다.

- 주기별 응답의 평균값 및 진폭 예측 오차 집계
- 양의 관측 수명과 예측 수명 사이의 RMS 로그 오차
- 압축 분지 동적탄성률이 선언 기준에서 지정 비율만큼 낮아지는 최초 종료점

공개 데이터 묶음은 별도 원자료이며 패키지에 포함하지 않는다. 로컬 취득본은 제공자 체크섬을 통과한 뒤에만 읽는다. 보정 Case 1-3과 결과가 공개되지 않은 Case 4-5는 역할을 섞지 않는다. 주기 행을 물리 시편 수로 세거나, blind 입력을 실험 결과로 취급하지 않는다.

## 고정 원자료 감사

로컬 v2 archive는 531,469,245바이트이며 제공자 MD5
`339c1ed86c4dd5d3459f487bda879154`와 프로젝트 SHA-256
`50410c8a23305e76087ab340e3a1cc3c39c16db94f4da57090db3104a7c5b6ae`로 고정했다.
압축을 풀지 않은 구조 감사 결과는 다음과 같다.

- member 170개, 실제 파일 136개, 비압축 합계 1,418,792,453바이트
- 위험 경로·중복 경로·암호화 member 0개
- calibration Case 1-3 각각 8개, 합계 24개 experiment folder
- experiment마다 ordered history, cycle summary, representative cycle, experiment summary 각 1개
- calibration 수치표 96개, 총 data row 25,213,349개, header 계열 7개
- validation-target folder의 공개 outcome CSV 0개

`audit_fabest_lcf_archive`는 이 계층과 모든 member CRC·크기를 기록한다.
`iter_fabest_lcf_numeric_rows`는 호출자가 감사 결과의 정확한 member와 header를 넘긴 경우에만 한
수치표를 provider 순서대로 streaming한다. 기본값에서는 header 차이, ragged row, 공란/비수치·비유한
값을 거절한다. `preserve_empty_fields=True`는 공란만 `None`으로 보존하고 그 외 비수치·비유한 값과
ragged row는 계속 거절한다. 이 모드는 누락을 유지하는 구조 scan용이며 대체·보간을 하지 않는다.
experiment folder는 실험 ID로 보존하지만 별도 물리 시편 ID나 시편 독립성을 만들지 않는다.

```powershell
.\.venv\Scripts\python.exe scripts\fetch_data.py --ids fabest-lcf-v2
.\.venv\Scripts\python.exe scripts\inspect_fabest_lcf_data.py `
  --output validation\fabest_lcf_v2_archive.json
.\.venv\Scripts\python.exe scripts\inspect_fabest_lcf_data.py `
  --full-numeric-scan --output validation\fabest_lcf_v2_full_numeric_scan.json
```

Full scan은 빈 필드 수와 해당 row 수를 보고서에 집계하며 이를 수치 대체하지 않는다. Provider가 허용한
비공란 필드의 numeric/finite 형식이 맞지 않거나 CSV row가 ragged하면 전체 scan을 실패 처리한다.

## 주기 응답 오차

`fatigue.cyclic_response_relative_error`는 각 시험 내부의 정렬된 cycle, 관측/예측 평균값, 관측/예측 진폭을 받는다. 평균값과 진폭의 정규화 크기는 각각 양수로 직접 넣어야 한다. 기본 가중치는 평균 0.6, 진폭 0.4이며 두 값의 합은 반드시 1이다.

시험마다 먼저 cycle 평균을 계산한 뒤 시험 간 평균을 계산한다. 따라서 저장 주기가 많은 시험이 전체 점수를 과도하게 지배하지 않는다. 첫 cycle 평균값이 0에 가까울 수 있으므로 라이브러리는 이를 정규화 값으로 자동 채택하지 않는다.

```python
from matintegrity import evaluate
from matintegrity.contracts import RunContext

result = evaluate(
    "fatigue.cyclic_response_relative_error",
    {
        "series": [{
            "experiment_id": "calibration-1",
            "cycle": [1, 10],
            "observed_mean": [10.0, 9.0],
            "predicted_mean": [11.0, 8.5],
            "observed_amplitude": [20.0, 18.0],
            "predicted_amplitude": [19.0, 17.0],
            "mean_normalizer": 10.0,
            "amplitude_normalizer": 20.0,
        }]
    },
    RunContext(asset_id="benchmark", location_id="gauge", time_basis="cycle"),
)
```

## 수명 RMS 로그 오차

`fatigue.life_rmsle`는 미리 정한 고유 case 집합에서 양의 관측 cycle과 예측 cycle을 비교한다. 기본 로그는 10진이며 자연로그도 선택할 수 있다. 반환값에는 case별 부호 있는 로그 잔차가 남아 과대·과소 예측 방향을 확인할 수 있다.

중도절단 시험, runout, 누락 결과는 이 계산기에 숫자로 넣지 않는다. 그런 관측은 생존분석 또는 검열 우도 계약으로 별도 처리해야 한다.

## 동적탄성률 저하 종료점

`fatigue.dynamic_modulus_drop_endpoint`는 엄격히 증가하는 cycle과 압축 분지 동적탄성률, 외부에서 검토한 기준 탄성률, 저하 비율을 받는다. 예를 들어 10% 저하 규칙은 `drop_fraction_threshold=0.1`로 표현한다.

- `first_observed_sample`: 임계값 이하인 최초 관측 cycle을 반환한다.
- `linear_between_samples`: 최초 하강 교차를 끼우는 두 점 안에서만 선형 보간한다.
- 닫힌 관측창에서 교차가 없으면 우측 검열로 보존한다.
- 열린 관측창에서 교차가 없으면 `needs_data`다.

이 종료점은 선언된 실험 규칙에 따른 관측 처리 결과다. 구조물 파손, 설계수명, 위험확률 또는 허용 판정으로 자동 변환하지 않는다.

## 검증과 재현

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_fatigue_benchmark.py -q
.\.venv\Scripts\python.exe scripts\validate_fatigue_benchmark_metrics.py
```

단위시험은 정렬, 고유 식별자, 양수 수명, 가중치 합, 관측점/보간 종료점, 닫힌 관측창의 우측 검열을 확인한다. 검증 JSON은 손계산 가능한 합성값만 사용한다. 이는 수치 계약 검증이며 실제 재료 보정이나 blind 결과 검증이 아니다.

## 출처와 재사용 경계

- 공식 규칙: <https://faber-cost.eu/wp-content/uploads/2026/05/Assignment_FABEST_LCF_FINAL.pdf>
- 공개 데이터 기록: <https://doi.org/10.5281/zenodo.21420213>
- 데이터 기록의 선언 라이선스: CC BY 4.0

구현은 공개된 계산 정의를 독립적으로 수식화했으며 제공자 문장, 그림, 표, 스크립트 또는 제출 양식을 복제하지 않는다. 공개 배포물에는 원자료 대신 출처, 체크섬, 구조 집계, 독립 코드 및 합성 검증만 넣는다.

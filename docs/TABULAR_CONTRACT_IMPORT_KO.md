# CSV·JSONL 계약 가져오기

`matintegrity.tabular_contract_import`는 사용자가 가진 CSV 또는 JSON Lines 행을 공개 Pydantic 계약으로 변환한다. 매핑 profile은 source 경로, target 필드 경로, 값 형식과 필수 여부를 명시한다. 임의 Python 표현식, 함수명, module import 또는 `eval` 문자열을 받지 않는다.

## 기본 사용법

```python
from matintegrity.identification import MaterialDesignation
from matintegrity.tabular_contract_import import TabularFieldMapping, TabularImportProfile, read_csv_contracts

profile = TabularImportProfile(
    profile_id="material-designation-v1",
    target_contract="MaterialDesignation",
    mappings=(
        TabularFieldMapping(target_path=("namespace",), source_path=("namespace",)),
        TabularFieldMapping(target_path=("specification",), source_path=("specification",)),
        TabularFieldMapping(target_path=("edition",), source_path=("edition",)),
        TabularFieldMapping(target_path=("grade",), source_path=("grade",)),
        TabularFieldMapping(target_path=("product_form",), source_path=("product_form",)),
        TabularFieldMapping(target_path=("condition",), source_path=("condition",)),
    ),
)
records, report = read_csv_contracts("caller-data.csv", MaterialDesignation, profile)
```

대상 class 이름과 `target_contract`가 정확히 일치해야 한다. CSV header는 중복될 수 없고 기본적으로 mapping하지 않은 source 열이 있으면 해당 행을 거절한다. 의도적으로 보조 열을 허용할 때만 `allow_unmapped_source_fields=True`를 선언한다.

## 변환 경계

- `string`, `integer`, `number`, `boolean`, `json`, immutable tuple 필드를 위한 명시적 `json_tuple` array 파싱을 수행한다.
- 단위 변환, 열 이름 추측, 기본 공학값, 보간과 누락값 대체를 수행하지 않는다.
- JSONL의 중첩 object는 `source_path=("measurement", "value")`처럼 선택한다.
- target의 중첩 객체는 `target_path`로 구성하고 최종 검증은 대상 Pydantic 계약이 수행한다.
- 거절 finding에는 행 번호와 문제가 된 필드 경로만 남기며 원래 셀 값을 복제하지 않는다.
- 보고서는 source SHA-256, profile digest와 가져온 계약들의 canonical digest를 기록한다.
- 장기 재현 profile은 `expected_source_sha256`와 `expected_target_schema_digest`를 함께 고정할 수 있다. 원파일 또는 대상 계약 JSON Schema가 바뀌면 import를 중단한다.

이 기능은 데이터 형식 연결 도구다. 원 데이터의 이용권리, 단위의 의미, 측정 적격성, 시편 독립성 또는 공학적 유효성을 인증하지 않는다. 원자료와 조직 내부 profile은 공개 저장소 밖에서 관리할 수 있으며 공개 예제에는 합성 자료 또는 재배포가 확인된 자료만 사용한다.

## 부식률 시편 표본 가져오기 예제

`examples/corrosion_rate_sample_import_profile.json`은 각 JSONL 행을 하나의 완성된 `CorrosionRateSampleSummary`로 읽는다. 행 안에 `observations` 배열, 선택적 `quantile_probabilities`, 선택적 `measurement_error_covariance_m_s2`를 둔다. 전체 cross-specimen covariance는 한 표본 그룹에 정렬된 N×N 행렬로 입력된다. 예제 profile은 대상 contract JSON Schema digest를 고정해 다른 계약 버전으로 조용히 읽히지 않도록 한다. CSV에서는 `examples/corrosion_rate_observation_csv_profile.json`과 import helper를 사용해 시편 행을 각각 가져올 수 있다. CSV의 표본 행에는 JSON object형 조건 서명과 evidence JSON array가 필요하다. 표본 그룹과 오차 공분산은 별도 검토 후 summary 계약에 결합한다.

프로파일을 코드에서 재사용하는 예제는 `examples/import_corrosion_rate_samples.py`이고, 입력값 전부가 프로젝트 합성 자료인 한 줄 샘플 그룹은 `examples/corrosion_rate_samples.synthetic.jsonl`에 있다. 동일 helper는 specimen-level CSV에도 typed import를 제공한다.

```python
from examples.import_corrosion_rate_samples import (
    import_corrosion_rate_observations_csv,
    import_corrosion_rate_samples,
)

samples, report = import_corrosion_rate_samples("caller-corrosion-samples.jsonl")
if report.rejected_rows:
    raise ValueError(report.findings)
for sample in samples:
    print(sample.observations[0].source_group_id, len(sample.observations))

observations, csv_report = import_corrosion_rate_observations_csv("caller-coupon-rates.csv")
```

이 호출은 계약 가져오기만 하며 부식 계산을 실행하지 않는다. 파일 SHA-256, mapping profile digest, 대상 schema digest와 가져온 record digest가 report에 기록된다. 사용자 CSV/JSONL에서 원자료 권리·물리 시편 대응·단위·조건 그룹을 확인하는 책임은 호출자에게 남는다.

## CLI batch import

등록 모델의 입력 계약은 동적 module import 없이 CLI에서 선택할 수 있다.

```text
matintegrity import-tabular corrosion.uniform_forecast caller.csv profile.json --format csv --out imported.json
```

`profile.json`은 `TabularImportProfile` JSON Schema를 따라야 하고 `target_contract`는 선택한 등록 모델의 입력 class 이름과 일치해야 한다. 출력에는 import report와 검증을 통과한 입력 record 배열이 함께 들어간다. 이 명령은 모델 계산을 실행하지 않으며, 계산하려면 각 record에 별도의 `RunContext`를 결합해 `matintegrity run` 또는 Python API를 사용한다. CLI는 임의 module/class 경로를 받지 않으므로 profile을 통한 동적 코드 import 경로가 없다.

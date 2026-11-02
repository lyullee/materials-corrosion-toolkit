# COQTEL 전기화학 행 typed API

## 출처와 권리 경계

- Dataset ID: `coqtel`
- Article DOI: `10.1016/j.dib.2025.111393`
- Archive DOI: `10.5281/zenodo.14193336`
- Declared license: CC BY 4.0
- Model ID: `data.coqtel_typed_electrochemistry_rows`
- Source ID: `coqtel_dataset_reader`
- Local archive path convention: `data/raw/coqtel/Essai_Corrosion1.h5`, `Essai_Corrosion2.h5`

이 API는 프로젝트의 기존 `signals.py` parser `coqtel_electrochemistry` 결과를 재사용하여, 전기화학 각 행을 검증된 Pydantic contract와 `Evidence`로 감싼다. 로컬 HDF5 원자료를 공개 패키지에 복사하거나 행별 값을 재배포하지 않는다. 기존 catalog의 두 HDF5 asset MD5/크기와 `signals.py`의 pinned SHA-256은 확인된 자료로 유지하며, typed reader는 기존 parser의 pinned SHA-256 검사를 필수로 호출한다.

CC BY 4.0 attribution, 계산 용도 허가 선언 및 `local_only` 사용 선언이 `CoqtelReadAuthorization` 입력에 필요하다. 행은 attribution과 authorization canonical digest를 포함한다. 이것은 권리의 법적 해석이나 외부 배포 허가 판정을 대신하지 않는다. 공개 배포를 위한 원자료 및 pointwise 값 공개는 별도의 rights review 없이 허용된 것으로 취급하지 않는다.

## API

- `CoqtelReadAuthorization`: dataset/article/license identity, attribution, caller의 computational-use 선언, local-only 선언
- `CoqtelElectrochemistryRow`: 전기화학 한 행과 원자료·행 digest, Evidence, 상태 인덱스, 원본 순서
- `iter_coqtel_electrochemistry_rows(path, authorization=...)`: 원본 시간 순서대로 typed 행을 순회
- `CoqtelArchiveAuditRequest`: metadata audit 입력
- `audit_coqtel_archive(request)`: 파일 경로와 point value 없이 checksum/행 개수/실험 ID만 반환
- `specifications()`: ModelSpec `data.coqtel_typed_electrochemistry_rows` 제공

## 행 계보와 결측 정보

HDF5 EC row `i`는 `State_i`로 연결되고, `state_index`와 `provider_source_row`는 이 1-based 행 식별을 보존한다. `source_order`는 0-based 순회 위치다. 입력 파일의 행을 정렬하지 않는다. 기존 파서가 동일한 말단 timestamp를 허용할 때 그 반복 행을 유지하며, `duplicate_timestamp_from_previous_row`는 현재 행이 앞 행과 동일 시각인 경우만 표시한다. 독립적인 반복 측정이나 시간 간격을 만들어 내지 않는다.

각 행에는 archive SHA-256이 든 Evidence가 있고, 입력 내보내기 authorization digest 및 source row content의 canonical SHA-256이 별도 보존된다. `pit_dimension_per_state`는 자료에서 행별 pit dimension이 제공되지 않으므로 `None`으로 고정된다. root image는 각 State에 연결되어 있지 않으므로 이 API는 이미지에서 행 값을 추정하지 않는다.

현재 EC 관측값은 source parser의 단위 convention을 보존한다: 시간은 초, 전류는 ampere, 전위는 volt. 전위 reference electrode 세부는 이 API가 별도로 결정하지 않는다. current, potential, charge 또는 ultrasonic waveform 변화에서 pit size, corrosion rate, thickness loss, remaining life, failure probability, material ranking을 계산하지 않는다.

## 사용 상 주의

`audit_coqtel_archive`는 통계량이나 raw observation을 반환하지 않는 metadata 전용 감사 인터페이스다. 실제 행이 필요한 경우에는 local cache의 HDF5 경로와 유효한 authorization contract를 `iter_coqtel_electrochemistry_rows`에 전달한다. 반복 시간 상태와 anomaly label을 원래대로 보존해야 한다. 실험 2의 air-bubble anomaly 구간은 데이터 손상 또는 부식 현상으로 재해석하거나 평활화하지 않는다. 두 HDF5 파일은 별도 316L plate 실험이며, 한 파일 안의 State 행은 반복 시간 상태이지 독립 표본이 아니다.

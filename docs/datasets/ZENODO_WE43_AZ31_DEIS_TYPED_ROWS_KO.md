# WE43/AZ31 DEIS matrix typed row API

## 데이터셋과 권리

- Dataset ID: `az-we43-az31-molybdate-eis`
- Official Zenodo record: https://zenodo.org/records/10482561
- DOI: `10.5281/zenodo.10482561`
- Catalog rights status: CC0-1.0, license reviewed `2026-10-31`
- Model ID: `data.zenodo_mg_deis_typed_matrix_rows`
- Source ID: `zenodo_mg_deis_typed_rows`
- Local archive: `data/raw/az-we43-az31-molybdate-eis/Dataset_CorSci.zip`
- Archive size: 30,886,921 bytes
- Catalog publisher MD5: `a0c19043e6ed883e005f35cee2800f66`
- Acquired archive SHA-256: `38d69f883ede6caaf988c3af9dd56f34c071f97b668d93fad778428c26dbed7c`

이 API는 기존 `zenodo_deis_import.inspect_zenodo_deis_archive` 및 `iter_zenodo_deis_rows`를 재사용한다. archive의 CC0 표기와 attribution은 dataset-level lineage이며, `ZenodoDeisReadAuthorization`에서 caller는 계산 사용과 local-only 경계를 명시한다. 이는 추가 권한 판단이나 법률 검토를 대신하지 않는다. 원 archive 및 pointwise matrix values는 public distribution에 복사하지 않는다.

## API

- `ZenodoDeisReadAuthorization`: dataset/DOI/license, attribution, computational-use 및 local-only declaration
- `ZenodoDeisMatrixRow`: DEIS tabular member의 한 원행, column values tuple 및 archive/member/source-row lineage
- `iter_zenodo_deis_typed_rows(path, manifest, source_member_path, authorization=...)`: 지정한 AZ31 또는 WE43 matrix를 기존 parser를 통해 원순서대로 반환
- `ZenodoDeisMatrixAuditRequest`: 선택 member의 metadata-only audit 입력
- `audit_zenodo_deis_matrix(request)`: digest·행/열 개수·blank/nonfinite counts를 반환하고 numeric point values는 숨김
- `specifications()`: metadata audit ModelSpec `data.zenodo_mg_deis_typed_matrix_rows`

## 행·열 의미와 digest

두 선택 member는 `DEIS/AZ31/AZ31-zw.txt`와 `DEIS/WE43/WE43-zw.txt`다. 각 matrix의 source row order는 0-based `source_row_order`로, text line 번호는 1-based `provider_row_number`로 기록한다. 각 행의 숫자 배열은 `matrix_values_as_provided` tuple에 원래 column 순서대로 남긴다. 자료의 matrix dimensions와 member hash는 기존 parser의 pinned manifest에서 취한다.

Archive SHA-256/MD5, byte count, member path/SHA-256, alloy label, source row order, column count 및 matrix tuple을 포함한 canonical row SHA-256이 제공된다. `Evidence`는 CC0 record DOI와 archive digest를 연결하고, row에는 attribution 및 authorization canonical digest도 함께 보존한다.

기존 importer는 column pairing을 자동 적용하지 않는다. 별도 metadata 기반 API에는 실수부/허수부 인접열 grouping을 검토하는 기능이 있으나, 이 row API에서는 해당 변환을 하지 않는다. row가 time인지, columns가 frequency인지, 값의 physical unit이 무엇인지, matrix element가 어느 전기화학 signal인지 unresolved 상태로 유지한다. 값에 숫자 단위나 축을 붙이지 않는다.

## 범위 제한

CC0 데이터셋의 DEIS matrix를 원행으로 노출하는 데이터 계보 reader다. 시간 이력·주파수 축·복소 impedance·전기화학 parameter·부식률·합금 순위·acceptance를 계산하거나 추정하지 않는다. archive에 함께 들어있는 이미지와 XPS 파일은 이 API의 대상이 아니다. WE43/AZ31 및 depositor가 기재한 test setup에 한정된 자료이며, field corrosion behavior나 material qualification의 근거로 확대하지 않는다.

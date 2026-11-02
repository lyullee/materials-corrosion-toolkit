# C1/C2 crack-arrest 시험 typed row API

## 출처와 권리

- Dataset ID: `crack-arrest-c1-c2`
- DOI: `10.17632/g69875w65c.1`
- Official Mendeley record: [Mendeley Data](https://data.mendeley.com/datasets/g69875w65c/1)
- Catalog license status: CC BY 4.0, license reviewed
- Catalog rights/checksum review date: 2026-10-31 (official record rechecked)
- Model ID: `data.mendeley_crack_arrest_typed_rows`
- Source ID: `mendeley_crack_arrest_typed_rows`
- Local archive: `data/raw/crack-arrest-c1-c2/g69875w65c-1.zip`
- Pinned archive SHA-256: `233f70de5d51148b93eab68654297d4ac4aa782864a5c7e43a3520be8ca54bde`
- Pinned archive size: 943,565 bytes

기존 `fracture_data.read_crack_arrest_series` parser를 재사용하며, 호출 시 archive 파일명·크기·SHA-256을 먼저 검사한다. Mendeley catalog는 CC BY 4.0으로 표시하지만, 이 API는 caller의 attribution 및 local-only 계산 승인 선언도 필요로 한다. 권리 관련 입력은 법적 권한 판정이 아니며, archive와 pointwise row를 공개 배포 대상으로 복사하지 않는다.

## Python API

- `CrackArrestReadAuthorization`: dataset DOI/license identity, attribution, computational-use 및 local-only 선언
- `CrackArrestObservationRow`: signed force-displacement 시계열 한 행과 source Evidence/digest
- `iter_crack_arrest_observation_rows(path, specimen_id, authorization=...)`: 명시한 한 specimen의 CSV point를 기존 순서대로 순회
- `CrackArrestArchiveAuditRequest`: metadata audit 입력
- `audit_crack_arrest_specimen(request)`: 파일 경로와 point values를 반환하지 않는 checksum/row-count audit
- `specifications()`: ModelSpec `data.mendeley_crack_arrest_typed_rows` 제공

## 행 식별 및 측정 의미

`source_row_order`는 parser가 읽은 CSV data 행의 0-based 순서이고, `provider_source_row`는 header를 포함한 1-based 행 번호(첫 data row=2)다. 자료를 정렬하거나 시간 샘플을 재배열하지 않는다. 각 행은 고정 archive SHA-256, source member와 그 SHA-256, specimen ID, C1/C2 family, attribution 및 authorization digest를 보존한다. `source_row_sha256`는 명시된 typed row values와 source identity로 만든 canonical digest다. `Evidence.sha256`에는 원 archive digest가 들어간다.

원본은 semicolon-separated five-column table이다. parser는 시간을 초로 유지하고 millimeter 값을 meter로, kilonewton을 newton으로 변환한다. 채널 sign과 zero는 유지하고, cycle index는 0 이상의 정수로 보존한다. 원본이 nonfinite 또는 필수 column 누락이면 reader는 실패하며 행을 삭제·대체하지 않는다. 온도는 파일명 token에서만 추출된 것이므로 specimen log로 확인된 시험체 온도와 혼동하지 않는다.

이 interface는 force-displacement sample 기록기다. crack-arrest toughness 또는 initiation toughness 산정, compliance correction, event picking, FAD 판정, 구조 acceptability, corrosion interaction, remaining life 및 failure probability를 계산하거나 보증하지 않는다. C1/C2 시험군과 specimen validity 및 시험 fixture 해석에는 별도 연구 검토가 필요하다.

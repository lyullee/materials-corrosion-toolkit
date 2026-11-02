# MS-AHSS 1300 수소 투과 XLSX 판독기

## 출처 및 이용 권리

Mendeley Data의 [Hydrogen permeation test on MS AHSS grade 1300](https://doi.org/10.17632/tnsgf7v76z.1)은 martensitic advanced high-strength steel grade 1300의 Devanathan–Stachurski 수소 투과 시험 자료다. 공식 dataset page는 CC BY 4.0 라이선스를 명시하며, 공개 메타데이터 API는 동일한 라이선스, 파일명, UUID, 크기 및 SHA-256을 제공한다. Giuseppe Macoretta의 자료 DOI와 CC BY 4.0 링크를 인용하고 수정 여부를 표시한다.

자료 파일 `Permeation_MS AHSS 1300.xlsx`는 `.gitignore` 적용 대상 `data/raw/mendeley-ahss1300-permeation/`에만 둔다. 고정 크기는 88,885 bytes, 제공자 API SHA-256은 `117d75a3f8329456732beada95b8f2be8bda688da88e6b8c7c83a9ee49698b3b`, 로컬 MD5는 `15316bf88b2e341e153bb6fecf7b823f`다. 판독 전에 크기와 두 digest를 확인한다. 원자료 행을 package, public fixture, example output으로 복사하지 않는다.

## 시험 설명과 파일 구조

자료 페이지는 50 × 50 × 1.2 mm 시편, 양극면의 얇은 Pd 코팅, 0.1 M NaOH 전해질 및 온도 조절 수조를 설명한다. 음극 전류 밀도는 상승·하강 구간에 걸쳐 0.5–10 mA/cm²로 조절되고, 시험 중 측정된 온도는 XLSX에 기록돼 있다. 이 importer의 구조 점검에서는 전류밀도 구간별 두 worksheet가 확인됐다. 각 sheet의 실제 크기는 각각 1,261행 × 6열, 600행 × 6열이다.

## API와 데이터 처리

`AHSS1300PermeationReadAuthorization`으로 출처 표시와 로컬 계산 권한을 지정한 뒤 `iter_mendeley_ahss1300_permeation_rows`에 XLSX 경로를 전달한다. 반환 행은 worksheet명, 원 행 번호, 셀 주소, 셀 저장 유형, 셀 값, 원본 digest와 Evidence를 보존한다. `openpyxl`을 read-only 모드로 이용하고 수식 값 대신 수식 문자열을 보존한다. 시간·전류·전류밀도·온도 단위를 자동 변환하거나 열의 과학적 의미를 추정하지 않는다. `audit_mendeley_ahss1300_workbook`은 값 없이 worksheet 크기와 비어 있지 않은 행, 수식 셀 개수만 반환한다.

## 해석 범위

이 자료는 특정 grade 1300 MS-AHSS 시편 구성과 해당 전기화학 셀·전해질·전류 램프 시험에 대한 연구 자료다. 반복 시편 수, 열처리 상태, 각 데이터 구역의 세부 헤더, 행별 단위와 전류 램프 전환 규칙은 downstream 분석 전에 원본 workbook과 연구 기록에 맞춰 검토해야 한다. effective diffusivity coefficient, 표면 반응/재결합 영향, 농도 경계조건을 이 importer만으로 추정하지 않는다.

행 데이터를 보편 수소 취성 임계값, 부식률, 확산계수, 재료 등급 간 순위, 합격 판정, 수명 또는 파손 확률로 바꾸지 않는다. 측정 해석은 재료 상태, 충전/검출 조건, 시편 두께와 유효 면적, 시간 기준, 온도 보정을 검토한 별도 모델이 담당해야 한다. 라이선스 조건과 함께 재배포할 수 있는 내용은 별도로 점검하고, 원 행은 로컬 범위에 둔다.

## 코드 계약

모듈 `matintegrity.mendeley_ahss1300_permeation_rows`는 `AHSS1300PermeationReadAuthorization`, `AHSS1300WorkbookCell`, `AHSS1300PermeationWorkbookRow`, `AHSS1300WorksheetManifest`, `AHSS1300WorkbookAuditRequest` 계약을 제공한다. registry 모델 `data.mendeley_ahss1300_hydrogen_permeation_workbook_audit`에 연결했고, schema exporter에 요청 계약을 포함했다. 중앙 exporter와 registry/source/capability/model-reference/backlog가 갱신되었고, metadata-only audit model은 공개 schema와 catalog에 연결돼 있다. registry 경로는 파일 크기·MD5·SHA-256 pin을 검증한 뒤 worksheet 크기와 수식 수만 반환하며 셀 내용은 응답에 포함하지 않는다. 원자료 행이 필요한 경우에만 `iter_mendeley_ahss1300_permeation_rows`를 직접 호출해 caller-authorized local stream으로 읽는다.

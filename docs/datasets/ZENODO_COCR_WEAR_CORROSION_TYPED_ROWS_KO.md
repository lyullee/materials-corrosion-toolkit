# Co–Cr 마모·부식 XLSX 자료 판독기

## 자료와 재사용 권리

Zenodo 레코드 [10.5281/zenodo.21253453](https://doi.org/10.5281/zenodo.21253453)는 생체 내 사용 이력이 있는 Co–Cr 무릎 인공관절의 마모 구역과 대조 구역을 비교하는 연구 자료를 제공한다. 레코드는 공개 접근이며 Zenodo API의 라이선스 식별자는 CC BY 4.0이다. 저자 Raul Davalos Monteiro와 DOI를 출처로 표시하고, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 링크 및 변경 여부를 밝혀야 한다.

이 판독기는 레코드에서 여섯 개 XLSX 전기화학 파일만 선택한다. 이미지 자산은 크고 행 기반 자료 API의 범위 밖이므로 내려받거나 저장소에 복사하지 않는다. 원시 파일은 `.gitignore` 적용 대상 `data/raw/zenodo-21253453-cocr/`에 유지한다. 카탈로그에는 각 원본 파일명, 파일 ID, 제공자 MD5, 파일 크기, 로컬 SHA-256 및 공식 다운로드 URL을 보존한다.

## 확인한 파일 구성

선택된 파일은 EIS 대조·마모 파일, LPR 대조·마모 파일, 변환된 대조 LPR 파일, PDP 대조·마모 파일이다. 공식 레코드 API는 이들을 XLSX로 제공하며, 개별 크기와 MD5는 manifest에 고정돼 있다. 로컬 파일은 해당 MD5 및 SHA-256 기준까지 대조했다.

구조 점검에서 EIS 파일은 시간별 시험을 나눈 여러 worksheet와 빈 보조 sheet를 포함했다. LPR 대조 및 마모 파일은 시간 조건별 데이터 구역이 가로로 배치돼 있었고, 변환된 대조 workbook에는 `Raw_Data`, `Converted_Normalized`, `Rp_Summary` 계열 worksheet가 있었다. PDP 파일은 한 worksheet에 여러 구역을 가로로 둔 긴 표였다. 따라서 이 importer는 특정 헤더 행, 시험 조건, 단위, 반복 수를 추정해 표를 재구성하지 않고 원래 셀 좌표를 보존한다.

## API 동작

`CoCrCorrosionReadAuthorization`에 CC BY 출처, 계산 이용, 로컬 사용 권한을 명시하고 `iter_zenodo_cocr_corrosion_rows`에 데이터 디렉터리를 전달한다. 각 출력 행은 원본 파일·파일 ID·checksum, worksheet, 원본 행 번호, 셀 주소와 저장된 셀 유형/값, authorization 및 원본 행 digest를 포함한다. 수치 셀은 숫자로, 날짜/시간은 ISO 형식 문자열로, 수식은 수식 문자열 그대로 기록한다. 수식은 평가하지 않는다. XLSX 해석은 프로젝트의 선택 의존성 `openpyxl`을 사용한다.

`audit_zenodo_cocr_workbooks`는 값을 반환하지 않고 파일 해시, sheet 이름, worksheet 크기, 비어 있지 않은 행 수와 수식 셀 수를 돌려준다. 데이터 행 API는 복잡한 병합 표를 임의로 평탄화하거나 단위를 변환하지 않는다. 후속 분석 전에 호출자는 원본 sheet의 구역별 헤더, 단위, 측정 조건, 시험 시점, 대조·마모 시편 식별을 직접 확인해 별도 파싱 프로파일로 지정해야 한다.

## 해석 범위와 제한

레코드는 한 연구의 회수된 보철물과 시험 결과를 다루며, 광범위한 Co–Cr 모집단, 독립적인 임상 표본, 일반 구조 재료의 부식 검증 집합을 뜻하지 않는다. 대조/마모 구역이라는 파일 이름만으로 시험 시편 수, 면적, 전해질 조건, 기준 전극, 시간축의 정의, 각 행의 의미를 확정하지 않는다. `Converted_Normalized`나 `Rp_Summary`의 값도 제공자 가공 결과로 남겨 두고 원시 측정과 섞거나 새로운 통계값으로 간주하지 않는다.

이 importer는 저항·전류를 부식률이나 금속 손실로 바꾸지 않고, PDP 결과로 보편적인 pitting 임계값을 만들지 않으며, 구조 건전성·서비스 수명·합격·고장확률을 평가하지 않는다. 행별 관측값은 로컬 전용으로 처리한다. 외부 배포본에는 point data 또는 연구 이미지가 들어가지 않도록 하고, 프로젝트가 재배포할 별도 유도 데이터를 만들 경우 CC BY attribution과 독립적인 기술·권리 리뷰를 다시 수행한다.

## 코드 계약

모듈 `matintegrity.zenodo_cocr_wear_corrosion_rows`는 `CoCrCorrosionWorkbookRow`, `CoCrWorkbookCell`, `CoCrCorrosionReadAuthorization`, `CoCrWorksheetManifest`, `CoCrWorkbookManifest` 계약을 제공한다. `iter_zenodo_cocr_corrosion_rows`와 `audit_zenodo_cocr_workbooks`는 직접 import해 사용하는 Python API다. 중앙 schema/catalog sync 및 registry 모델 등록은 별도 통합 작업으로 남긴다.

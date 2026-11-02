# Mendeley ZE41/AZ91D 마그네슘 합금 SCC typed-row reader

## 데이터와 권리

- 공식 버전 기록: [Mendeley Data v1](https://data.mendeley.com/datasets/59rcng6nsr/1), DOI [10.17632/59rcng6nsr.1](https://doi.org/10.17632/59rcng6nsr.1)
- 공식 파일 및 권리 메타데이터: [Mendeley 공개 API](https://data.mendeley.com/public-api/datasets/59rcng6nsr)
- 제공자는 dataset에 CC BY 4.0을 선언한다. 라이선스 문구는 제3자 소유로 식별된 내용에 별도 허가가 필요할 수 있다고 명시한다. 개별 행의 원출처와 재배포 권리는 따로 검토해야 한다.
- 버전 1에는 AZ91D와 ZE41의 base 및 friction-stir-processed 조건을 담은 XLSX 네 개가 있다. 이 데이터는 실험실 Mg 합금 SCC/부식 자료이며 다른 재료, 용액, 공정, 구조물의 성능을 입증하지 않는다.
- 원본 파일은 `data/raw/mendeley-ze41-az91d-fsp-scc/`에 로컬 전용으로 둔다. 배포물에는 포함하지 않는다. 제공자 API의 파일 크기와 SHA-256은 `data/catalogs/datasets.json`, 로컬 확보 기록은 raw 폴더의 `local_manifest.json`에서 확인한다.

## 가져오기 경계

`matintegrity.mendeley_mg_fsp_scc_rows`는 정확한 파일명, 바이트 크기, provider SHA-256을 확인한 뒤 비어 있지 않은 XLSX 행을 workbook·worksheet·row·cell 순서로 전달한다. 셀 주소, 저장 형식, 원시 값과 출처 digest를 보존한다. 시트 이름과 행은 원자료 구조 정보로 유지하며, reader는 이를 시험 조건이나 물리적 의미로 번역하지 않는다.

이 API는 단위, 응력 수준의 정의, 시편 및 반복시험 계층, 파손 기준, SCC 성장률 또는 부식률을 추론하지 않는다. 피로·균열·수명 모델 보정, 재료 순위, 수용 여부, 서비스 적격성을 산출하지 않는다. 사용자가 데이터 사용을 승인하고 출처를 명시해야 하며, 행 결과는 로컬 분석 전용이다.

## Python API

```python
from matintegrity.mendeley_mg_fsp_scc_rows import (
    MagnesiumFspSccReadAuthorization,
    iter_magnesium_fsp_scc_rows,
)

authorization = MagnesiumFspSccReadAuthorization(
    attribution="Ashokkumar S. et al., Mendeley Data v1, DOI:10.17632/59rcng6nsr.1",
    computational_use_authorized=True,
    local_only_authorized=True,
)

for row in iter_magnesium_fsp_scc_rows(
    "data/raw/mendeley-ze41-az91d-fsp-scc",
    authorization=authorization,
):
    consume_local_row(row)
```

`include_filenames=(...)`로 고정된 네 파일 중 선택해서 읽을 수 있다. `audit_magnesium_fsp_scc_directory`는 네 파일의 digest와 sheet 크기만 반환하며 셀 값은 출력하지 않는다. 읽기 API와 audit API는 워크북 파일을 수정하지 않는다.

## 출처 및 재현 정보

- 네 파일의 provider ID, 크기, SHA-256, 다운로드 URL은 데이터 catalog에 고정되어 있다.
- XLSX 파일은 로컬에서 구조만 확인했다. 워크북 dimension 기록상 파일별로 5개 sheet가 있으나, 열 제목·셀 값·해석 결과는 배포용 문서에 복사하지 않는다.
- 원자료의 사용자 인용은 버전 DOI와 CC BY 4.0 출처표시를 포함해야 한다. 제3자 출처가 있는 항목은 그 권리를 추가 확인한다.
- 이 reader는 구조 보존과 provenance 확인을 위한 importer다. 측정값의 타당성 검증 또는 SCC 모델 검증을 대신하지 않는다.

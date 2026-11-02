# Dryad formate-packer H₂S/CO₂ 부식 workbook local reader

## 자료 식별과 권리

- Dryad 자료 DOI: [10.5061/dryad.p1mf340](https://doi.org/10.5061/dryad.p1mf340)
- associated article DOI: [10.1098/rsos.180405](https://doi.org/10.1098/rsos.180405)
- 원 기록: [Dryad dataset record](https://datadryad.org/dataset/doi%3A10.5061%2Fdryad.p1mf340), [Dryad public API metadata](https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.p1mf340), [Zenodo-mirrored version record](https://zenodo.org/records/4937236)
- 데이터셋 라이선스: Dryad metadata와 Zenodo API가 명시한 CC0-1.0. 논문도 CC BY 4.0으로 공개되었다. 자료 계보를 위해 논문 및 데이터 DOI를 함께 인용한다.
- 파일: `Data 1.xlsx`, 13,414 bytes, provider MD5 `ab545c29253c47eac2cf4996930f1d94`, 로컬 SHA-256 `9f524b0ad274caba47deb1f14a70a6841474a82353e288f6b83e1455f7bfca15`.
- 직접 파일: [Zenodo content endpoint](https://zenodo.org/api/records/4937236/files/Data%201.xlsx/content).

원본은 `data/raw/dryad-formate-packer-h2s-co2/`의 ignored local-only 경로에 둔다. 파일과 행별 관측값은 package, release, fixture 또는 public example에 복사하지 않는다. `data/catalogs/datasets.json`의 파일 manifest는 파일명, 공식 URL, publisher MD5, 크기 제한을 기록한다. `data/catalogs/sources.json`에는 독립 reader의 역할과 재사용 경계를 기록한다.

## workbook 구조와 Python API

Workbook 구조는 `Sheet1` 한 장, 97행 × 23열이다. 시트에는 여러 figure/table 관련 셀 블록과 공백 구간이 섞여 있다. 이 reader는 데이터 의미를 평탄화하지 않고 비어 있지 않은 원행 전체를 보존한다.

- `FormatePackerReadAuthorization`: caller의 attribution, 계산 사용 및 local-only 승인
- `FormatePackerWorkbookCell`: 열 번호, 셀 주소, 저장 유형, 저장 값
- `FormatePackerWorkbookRow`: 시트명, 원행, 전체 셀 및 원행 digest
- `iter_dryad_formate_packer_rows(path, authorization=...)`: 해시를 확인한 로컬 workbook의 비어 있지 않은 행을 원래 순서로 읽음
- `FormatePackerWorkbookAuditRequest` 및 `audit_dryad_formate_packer_workbook(...)`: 수치 셀값을 반환하지 않고 파일·시트·행 개수와 digest만 보고

선택 의존성 `openpyxl`을 read-only/data-only 비활성 상태로 사용한다. 수식은 계산하지 않고 원 수식 문자열로 둔다. 날짜·시간 셀은 ISO 문자열로 표현한다. 승인된 파일명, 바이트 수, provider MD5와 검토된 local SHA-256이 일치하지 않으면 읽기를 거부한다.

```python
from matintegrity.dryad_formate_packer_corrosion_rows import (
    FormatePackerReadAuthorization,
    iter_dryad_formate_packer_rows,
)

authorization = FormatePackerReadAuthorization(
    attribution=(
        "Xu, Tao and Wang (2018), article DOI 10.1098/rsos.180405; "
        "Dryad dataset DOI 10.5061/dryad.p1mf340; CC0-1.0"
    ),
    computational_use_authorized=True,
    local_only_authorized=True,
)
for row in iter_dryad_formate_packer_rows(
    "data/raw/dryad-formate-packer-h2s-co2/Data 1.xlsx",
    authorization=authorization,
):
    # Caller chooses a separately reviewed parser profile for figure/table blocks.
    print(row.worksheet_name, row.provider_row_number, row.source_row_sha256)
```

## 해석 범위와 주의점

관련 연구는 formate 기반 packer fluid의 고온·고압 H₂S/CO₂ 혼합 환경에서 Alloy G3, N80 및 TP110SS를 다룬다. 논문에 나오는 한 고온·고압 시험 조건은 총압 7 MPa, CO₂ 분압 2.5 MPa, H₂S 1000 ppm, 120 °C 및 72 h다. 다른 figure block에는 실온 시험이나 조성·첨가제 변화 등 별도 조건이 포함된다. 이 조건을 workbook 전체에 일괄 부여하지 않는다.

Workbook 셀은 figure/table 중심으로 배열되어 있으나 각 값이 독립 실측 원자료인지, figure에서 읽어 옮긴 요약인지, 반복 평균인지 모든 셀에 대한 설명은 제공되지 않는다. reader는 아래 내용을 추정하지 않는다.

- figure 제목과 표 영역을 근거로 한 자동 의미 분류 또는 시험조건 연결
- 종·시편의 행별 독립성, 반복 수, 분산 및 불확도
- H₂S 제거제/부식 억제제 조성의 일반화 또는 현장 사용 적합성
- CO₂ 단독 수용액, 다른 alloy/heat treatment, 유동 조건으로의 전이
- electrochemical Tafel/BV 계수, 보편적 부식률 모델, acceptance, 수명 또는 실패 확률

이 기록은 wet-CO₂ 평가 연구에서 고산성 혼합가스/packer-fluid 사례를 조건부 비교하고 파서 개발에 참고할 수 있는 후보이다. CO₂-only 모델의 보정·독립 검증 데이터로 바로 사용하면 안 된다. 셀값을 후속 모델 입력으로 쓰기 전에는 원 논문 및 XLSX figure block의 의미, 단위, 조건, replicate 처리와 해당 값의 측정/요약 구분을 연구자가 별도로 검토해야 한다.

## 원 출처

- Dryad API metadata: <https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.p1mf340> (license `CC0-1.0`, file identity, size, digest)
- Zenodo API record: <https://zenodo.org/api/records/4937236> (mirror metadata: `cc-zero`, exact XLSX filename/size/MD5 and downloadable file URL)
- Xu, P., Tao, Z., Wang, Z. (2018), *Corrosion-resistant systems of formate packer fluid for G3/N80/TP110SS pipes at high temperature, high pressure and high H₂S/CO₂ ratios*, Royal Society Open Science, DOI `10.1098/rsos.180405`: <https://pmc.ncbi.nlm.nih.gov/articles/PMC6083718/>.

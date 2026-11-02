# X80 / SRB SCC 실험 데이터의 로컬 typed-row reader

## 데이터 식별과 이용조건

- 공식 기록: [Mendeley Data v1](https://data.mendeley.com/datasets/cmyhpvspp9/1), DOI `10.17632/cmyhpvspp9.1`.
- 기계 판독 공식 메타데이터: [Mendeley public dataset API](https://data.mendeley.com/public-api/datasets/cmyhpvspp9).
- 제공자 페이지는 X80 pipeline steel을 SRB가 포함된 simulated Yingtan soil solution에 두고 cathodic potential 조건을 달리한 SCC 자료라고 설명한다. 버전은 1이며 제공자 기여자는 Xingfa Wang으로 기재되어 있다.
- 기록 수준 이용허락은 CC BY 4.0이다. Mendeley에 표시된 이용조건은 제3자에 속한다고 식별된 내용은 별도 허가가 필요할 수 있다고 경고한다. 확인되지 않은 연결 논문 DOI나 실험 source chain을 임의로 부여하지 않는다.
- 공식 API의 파일 크기와 SHA-256을 확인했고, 내려받은 세 파일은 모두 제공자 digest와 일치했다.

| 원본 파일 | 구조(시트별 행 × 열) | 바이트 | 제공자 SHA-256 |
|---|---:|---:|---|
| `Data of  AC Impedance.xls` | `Sheet1` 30×16, `Sheet2` 30×8, `Sheet3` 0×0 | 32,256 | `a63e376753c3608d2ca082af139d974de76b7d7b28699bcc43d8fc8d0d72ab25` |
| `Data of  Slow Strain Rate Tensile Test.xls` | `Sheet1` 34,123×8, `Sheet2` 0×0, `Sheet3` 0×0 | 4,858,368 | `302e7a4c1fedaf4de06f92304f4c5dc2f850c8b91250d900dfd138420f6d2ad6` |
| `Data of Polarization Curves.xls` | `Sheet1` 2,386×6, `Sheet2` 0×0, `Sheet3` 0×0 | 299,008 | `0e483b5ab53ff050c669a3ba0d8933ed77107fc904aa9831b989090c430b3250` |

원본과 `local_manifest.json`은 무시 처리된 `data/raw/mendeley-x80-srb-scc/` 아래에만 둔다. 데이터 행은 release, fixture, public example에 복사하지 않는다. 공식 API의 metadata/파일 ID는 `data/catalogs/datasets.json`에도 기록되어 있다.

## API 경계와 사용 예

- `X80SCCReadAuthorization`은 정확한 버전 DOI, CC BY 라이선스 표기, attribution 및 caller의 local computational-use 승인을 요구한다.
- `X80SCCWorkbookCell`은 1-based column 위치, `xlrd` cell type code와 원 셀 값을 유지한다.
- `X80SCCWorkbookRow`는 원 파일명·제공자 파일 ID·시험 종류·셀 순서·행 digest·Evidence를 결합한다.
- `iter_x80_srb_scc_rows(directory, authorization=..., include_kinds=(...))`는 세 XLS 파일 중 선택한 종류만 digest 확인 후 순서대로 읽는다.
- `audit_x80_srb_scc_directory(request)`는 file digests 및 sheet dimensions만 반환하며 셀 값은 내보내지 않는다.
- 모델/인터페이스 ID: `data.mendeley_x80_srb_scc_typed_rows`; source ID: `mendeley_x80_srb_scc_lab_rows`.

```python
from matintegrity.mendeley_x80_srb_scc_rows import (
    X80SCCReadAuthorization,
    iter_x80_srb_scc_rows,
)

authorization = X80SCCReadAuthorization(
    attribution=(
        "Wang (2018), Mendeley Data v1, DOI 10.17632/cmyhpvspp9.1; "
        "CC BY 4.0; local row structure parsing with independent provenance review"
    ),
    computational_use_authorized=True,
    local_only_authorized=True,
)
for row in iter_x80_srb_scc_rows(
    "data/raw/mendeley-x80-srb-scc",
    authorization=authorization,
    include_kinds=("polarization",),
):
    # Establish units, sample identity and environmental condition separately.
    print(row.source_filename, row.worksheet_name, row.provider_row_number)
```

The legacy XLS importer retains cell type codes and row/column order. Numeric date-like values remain numeric serials; formula cells are only the cached values exposed by `xlrd`, and formulas are neither reconstructed nor executed.

## 해석 제한

Provider filenames are used only to keep EIS, polarization and SSRT files separate. The reader does not infer electrochemical units/reference electrode, specimen or replicate identity, SRB state, condition-to-row mapping, or measurement uncertainty. It does not fit equivalent circuits, estimate Tafel/BV parameters, calculate corrosion rate or SCC susceptibility, assess acceptance or remaining life, or validate service transfer. Treat each asset as experiment-specific evidence until a researcher reviews the original test protocol, field definitions, source attribution and cell-level semantics. CC BY on the dataset record must not be read as a blanket license for any separately identified third-party contribution.

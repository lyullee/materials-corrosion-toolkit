# Mendeley 폭발용접 다층판 피로 데이터 typed-row reader

## 데이터 출처와 권리

- 공식 버전 기록: [Mendeley Data v1](https://data.mendeley.com/datasets/mc8bc9tm59/1), DOI [10.17632/mc8bc9tm59.1](https://doi.org/10.17632/mc8bc9tm59.1)
- 제공 파일과 라이선스 메타데이터: [공개 API](https://data.mendeley.com/public-api/datasets/mc8bc9tm59)
- 제공자는 dataset을 CC BY 4.0으로 표시한다. 이용 허가문은 dataset 내부에서 제3자 저작물로 식별된 내용에 별도 승인이 필요할 수 있다고 안내한다. 원자료의 점별 데이터를 재배포하기 전에 행 출처와 제3자 권리를 검토한다.
- 버전 1에는 Ti 또는 Zr 계열 층과 탄소강을 포함한 폭발용접 다층판의 피로시험 workbook 한 개가 있다. 공개된 방법 설명은 완전 반전 축하중을 다루지만, 시험별 열의 단위와 시편 관계는 데이터 자체와 연구 출처를 확인한 후 사용한다.
- 이 자료는 특정 다층 구조의 피로 시험 자료이며 부식률 또는 부식 피로 시험 결과가 아니다. 다른 적층, 접합 공정, 환경, 구조물로 일반화할 수 없다.
- 원본 XLSX는 `data/raw/mendeley-explosive-weld-multilayer-fatigue/`에서 로컬 전용으로 보관한다. 배포물에는 포함하지 않는다. provider 파일 ID, 크기, SHA-256은 `data/catalogs/datasets.json`과 raw 폴더의 `local_manifest.json`에 기록했다.

## Reader 범위

`matintegrity.mendeley_explosive_weld_fatigue_rows`는 고정 파일명, 바이트 크기, SHA-256을 확인한 후 비어 있지 않은 행을 workbook·worksheet·row·cell 순서로 돌려준다. 셀 주소, 저장 형식, 원래 값과 provenance digest를 보존한다.

추가 API `data.mendeley_explosive_weld_multilayer_fatigue_mapped_rows`는 호출자가 명시한 worksheet, raw header 값, 포함할 행 범위, column 의미, 단위 토큰과 역할만 사용한다. Workbook에는 시트별 구조 차이, 수식 셀과 보조 행이 있으므로 reader가 header로부터 열 의미나 단위를 자동 결정하지 않는다. 매핑 계약을 만족하지 않으면 추출을 거부한다. 허용되는 role은 `record_id`, `condition`, `measurement`, `derived_formula`, `metadata`, `unclassified`이며 role 지정 자체가 값 검증이나 과학적 판단을 뜻하지 않는다.

수식 셀은 openpyxl `data_only=False`로 읽은 원 수식 문자열과 cell type을 그대로 보존하며 계산하지 않는다. 원본에 캐시된 계산값이 있더라도 reader는 그 결과값을 복구·평가하지 않는다. 빈 행과 수식 행도 caller가 선택한 inclusive row span 안에서는 건너뛰지 않는다. 단위 토큰도 호출자가 지정한 문자열 그대로 저장하고 변환하지 않는다. 단위를 확인하지 못한 경우에는 명시적으로 `unknown`을 넣고 분석 단계에서 그 열을 사용하지 않는다.

Mapped request는 전체 출력 행 수와 mapped-cell 수의 상한을 반드시 지정해야 한다. reader는 결과 행을 materialize하기 전에 worksheet mapping별 요청량을 합산한다. 둘 중 하나라도 caller budget을 넘으면 원시 행을 잘라 내지 않고 `out_of_scope`로 거부한다. 각 상한은 10,000행과 100,000 mapped cell 이하만 허용된다.

Reader는 열 이름이나 시트명을 물리량 또는 적층 구분으로 해석하지 않는다. 단위, 피로한도, S–N 곡선, 균열성장 법칙, 부식 저항, 허용기준, 수명 또는 실패확률을 계산하지 않는다. `local_only_authorized=True`와 출처 DOI를 포함한 호출자 승인값을 요구한다.

## Python API

```python
from matintegrity.mendeley_explosive_weld_fatigue_rows import (
    ExplosiveWeldFatigueReadAuthorization,
    iter_explosive_weld_fatigue_rows,
)

authorization = ExplosiveWeldFatigueReadAuthorization(
    attribution=(
        "Karolczuk et al., Mendeley Data v1, "
        "DOI:10.17632/mc8bc9tm59.1"
    ),
    computational_use_authorized=True,
    local_only_authorized=True,
)

for row in iter_explosive_weld_fatigue_rows(
    "data/raw/mendeley-explosive-weld-multilayer-fatigue",
    authorization=authorization,
):
    consume_local_row(row)
```

Mapped extraction에는 호출자가 실제 workbook header와 검토한 필드 해석을 모두 제공한다. 아래는 형식 예시이며, 임의의 실제 column 의미나 단위를 기본값으로 선언하지 않는다.

```python
from matintegrity.mendeley_explosive_weld_fatigue_rows import (
    ExplosiveWeldFatigueColumnMapping,
    ExplosiveWeldFatigueWorksheetMapping,
    ExplosiveWeldFatigueMappedImportRequest,
    import_explosive_weld_fatigue_mapped_rows,
)

column_mapping = ExplosiveWeldFatigueColumnMapping(
    column_number=caller_reviewed_column_number,
    field_id="caller_field_identifier",
    caller_meaning="caller reviewed field definition",
    unit_token="caller reviewed unit token or unknown",
    role="measurement",
    expected_header_value=caller_exact_raw_header_cell,
    mapping_evidence=(caller_mapping_evidence,),
    mapping_reviewed=True,
)
sheet_mapping = ExplosiveWeldFatigueWorksheetMapping(
    worksheet_name=caller_exact_sheet_name,
    header_row_number=caller_header_row,
    data_start_row=caller_first_data_row,
    data_end_row=caller_last_data_row,
    columns=(column_mapping,),
)
mapped = import_explosive_weld_fatigue_mapped_rows(
    ExplosiveWeldFatigueMappedImportRequest(
        local_data_directory="data/raw/mendeley-explosive-weld-multilayer-fatigue",
        authorization=authorization,
        worksheet_mappings=(sheet_mapping,),
        maximum_output_rows=caller_reviewed_row_budget,
        maximum_output_cells=caller_reviewed_cell_budget,
        mapping_reviewed=True,
    )
)
```

Each mapping's `expected_header_value` is compared exactly with the pinned local file. This only verifies that the reviewed mapping still targets the same source header; it does not establish whether the caller's meaning or units are scientifically correct.

`audit_explosive_weld_fatigue_directory`는 provider digest와 workbook/sheet 크기만 반환하고 셀 값을 출력하지 않는다. 실제 해석은 독립적인 공학 검토 단계에서 단위, 물리 시험 단위, 반복 수, 적층 식별자를 확인하고 수행해야 한다.

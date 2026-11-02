# 공개 FCGR workbook import

`import_fcgr_workbook(FcgrWorkbookImportRequest(...))`는 caller가 지정한 Excel worksheet, column index, 헤더 텍스트, specimen identity, 행 구간, 단위와 출처/권리/적용성 검토를 확인해 `TabulatedCrackGrowthCurve`를 만든다. 로컬 파일은 `FcgrWorkbookImportRequest.from_file(path, ...)`로 bytes를 고정할 수 있다. Excel 해석은 선택 `science` 의존성의 openpyxl을 사용한다.

Importer는 sheet·column·range를 추측하지 않는다. 선택된 행 전부가 숫자이고 양의 유한값이어야 하며 delta-K가 source order에서 엄격히 증가해야 한다. 행 정렬·중복 제거·runout 분류·단위 추정은 하지 않는다. SHA-256이 요청의 고정 digest와 일치하지 않으면 거절한다. 결과는 원 workbook SHA-256, 출처, 라이선스, 권리/적용성 검토 ID, source worksheet/row ID, 원 단위 점과 SI curve를 함께 반환한다. Workbook bytes와 point data는 패키지에 포함되지 않는다.

이 저장소는 원 workbook을 포함하지 않는 [S460 import profile](../data/profiles/mendeley_s460_fcgr_import.json)을 제공한다. 이 파일은 SHA-256 pin, CC BY attribution, 6개 worksheet의 명시적인 header/column/range/R mapping을 보존한다. 파일 경로와 profile로 입력을 구성하려면 다음처럼 호출한다.

```python
import json
from pathlib import Path

from matintegrity.fcgr_curve_import import FcgrWorkbookImportRequest, import_fcgr_workbook

profile = json.loads(Path("data/profiles/mendeley_s460_fcgr_import.json").read_text())
request = FcgrWorkbookImportRequest.from_file("Paris Law Constants.xlsx", **profile)
imported = import_fcgr_workbook(request)
```

Profile의 material/environment ID는 source metadata의 한계를 드러내는 표기다. Service calculation 전에 source 문헌에서 실제 material condition과 시험환경을 검토하고 적용성 ID를 갱신해야 한다. 주파수는 의도적으로 null이다.

## S460 자료 이용 경계

Pureza, Dennis; Brito, José; Alencar, Guilherme; Veloso, Luís; Cardoso, Hermano (2026), *S460_Fatigue_Characterization*, version 2, Mendeley Data, DOI [10.17632/ytny53v2fn.2](https://doi.org/10.17632/ytny53v2fn.2). Dataset page에는 CC BY 4.0과 여섯 compact-tension specimen의 crack-growth 처리 데이터/Paris curve 목적이 표시되어 있다. [공식 데이터 페이지](https://data.mendeley.com/datasets/ytny53v2fn/2).

프로젝트 로컬 workbook 관찰에서 CT sheet의 ΔK [MPa√m]와 da/dN [mm/cycle] 열, sheet별 R값, data row window를 확인했다. workbook 자체에는 시험 주파수를 식별하지 못했다. 따라서 `frequency_Hz=None`은 미보고 값을 보존하며, delta-K에 대한 rate/cycle 조회에는 사용할 수 있지만 load-block crack-growth life integration 및 frequency-matched curve-family 선택에서는 거절된다. 주파수를 추정하거나 다른 specimen/문헌값으로 대체하지 않는다. 환경, 재료 상태, 곡선 선정 행과 적용성은 caller가 직접 근거를 대고 검토해야 한다.

```python
from pathlib import Path

from matintegrity.fcgr_curve_import import (
    FcgrWorkbookImportRequest,
    FcgrWorkbookSheetSelection,
    import_fcgr_workbook,
)
from matintegrity.models.crack import TabulatedGrowthRateQuery, tabulated_growth_rate

path = Path("Paris Law Constants.xlsx")  # CC BY 4.0 dataset file obtained by the caller
request = FcgrWorkbookImportRequest.from_file(
    path,
    expected_source_sha256="c80725a36672ca065aac19caed98be1fc2f7375d64ded4eb3052a25f1a0d0e54",
    source_citation="Pureza et al. (2026), S460_Fatigue_Characterization, v2, Mendeley Data, doi:10.17632/ytny53v2fn.2",
    license_id="CC-BY-4.0",
    rights_review_id="mendeley_s460_fatigue_characterization_v2",
    applicability_review_id="caller-reviewed-S460-condition-and-environment",
    frequency_Hz=None,
    delta_k_unit="MPa*sqrt(m)",
    rate_unit="mm/cycle",
    below_minimum_policy="out_of_scope",
    pointwise_computational_use_authorized=True,
    curve_applicability_reviewed=True,
    sheet_selections=(
        FcgrWorkbookSheetSelection(
            sheet_name="CT01 R=0.1",
            curve_id="S460-CT01-R01",
            source_group_id="S460-study-R01",
            physical_specimen_id="CT01",
            material_condition_id="caller-reviewed-S460-condition",
            environment_id="caller-reviewed-test-environment",
            stress_ratio=0.1,
            header_row=2,
            first_data_row=5,
            last_data_row=19,
            delta_k_column_index=16,
            rate_column_index=13,
            expected_delta_k_header="dK [MPa√m]",
            expected_rate_header="da/dN [mm/cycle]",
            specimen_and_row_window_reviewed=True,
        ),
    ),
)
imported = import_fcgr_workbook(request)
curve = imported.curves[0].curve
query = tabulated_growth_rate(
    TabulatedGrowthRateQuery(curve=curve, query_delta_k_Pa_sqrt_m=[45e6])
)
```

위 예제의 재료 환경 식별자와 열/행 구간은 사용자가 현재 원 workbook·연구 문맥과 대조해야 한다. importer 입력의 review flag는 그 확인을 대신하지 않는다. 이 자료 한 연구의 여섯 specimen은 여섯 독립 연구가 아니며 corrosion-fatigue 또는 별도 재료/환경 조건 검증도 아니다. CC BY 4.0에 따른 적절한 출처표시와 변경사항 표기를 유지하고, 원 workbook을 공개 배포할 때에는 라이선스 원문 및 재배포 조건을 별도 확인한다.

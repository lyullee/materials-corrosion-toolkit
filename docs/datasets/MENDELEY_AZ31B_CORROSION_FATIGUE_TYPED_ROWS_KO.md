# AZ31B 부식피로 데이터의 로컬 workbook reader

## 데이터셋과 권리 경계

- 공식 데이터 기록: [Mendeley Data v1](https://data.mendeley.com/datasets/5b5rk27wmx/1), DOI `10.17632/5b5rk27wmx.1`.
- 공식 기계 판독 파일·권리 metadata: [Mendeley public dataset API](https://data.mendeley.com/public-api/datasets/5b5rk27wmx).
- 관련 논문: Shaha et al. (2018), *Improving Corrosion and Corrosion-Fatigue Resistance of AZ31B Cast Mg Alloy Using Combined Cold Spray and Top Coatings*, DOI `10.3390/coatings8120443`, [publisher page](https://www.mdpi.com/2079-6412/8/12/443). 논문 페이지는 as-cast AZ31B 기판, cold-sprayed AA7075 및 e-paint 상부 코팅의 부식·부식피로 시험을 설명한다.
- 논문은 electrochemical corrosion/fatigue 시험에 3.5 wt.% NaCl과 실온 환경을 설명한다. 이 조건을 figure-numbered 원 workbook의 모든 row에 자동 결합하지 않는다.
- Mendeley 기록은 dataset을 CC BY 4.0으로 표시한다. 라이선스 설명은 dataset 안에 제3자 소유로 특정된 자료가 있으면 별도 허가가 필요할 수 있다고 명시한다. 재사용자는 figure/table 블록별로 그러한 출처가 있는지 따로 검토해야 한다.
- 원자료는 figure 번호가 들어간 XLSX 8개다. 파일 ID, 제공자 크기 및 SHA-256은 `data/catalogs/datasets.json`과 파일 상수에 고정되어 있다. 내려받은 파일은 raw-only 경로 `data/raw/mendeley-az31b-corrosion-fatigue-cold-spray/`에 둔다.

검토한 workbook layout(행×열)은 다음과 같다. 이 목록은 시트 제목과 크기만 기록하며 figure/table 해석을 의미하지 않는다.

| 원본 파일 | 시트별 크기 |
|---|---|
| `Paper-2-Fig. 4b.-Feb07-18.xlsx` | `AZ31-7075Al-SP7` 257×7 |
| `Paper-2-Fig. 5a.-Feb07-18.xlsx` | `ocp` 9,000×6 |
| `Paper-2-Fig. 5b.-Feb07-18.xlsx` | `Tafel` 1,265×6; `Sheet1` 1,349×13 |
| `Paper-2-Fig. 6a.-Feb07-18.xlsx` | `Sheet1` 338×6 |
| `Paper-2-Fig. 6b.-Feb07-18.xlsx` | `Phase` 64×7 |
| `Paper-2-Fig. 7.-Feb07-18.xlsx` | `Sheet1` 22×10; `Sheet2` 1×1 |
| `Paper-2-Fig. 9a.-Feb07-18.xlsx` | `Sheet1` 16,323×11 |
| `Paper-2-Fig. 9b.-Feb07-18.xlsx` | `Sheet1` 16,323×5 |

원본 셀 값은 release, fixture, 예제 또는 공개 문서에 복사하지 않는다. API는 workbook 구조와 row provenance를 보존하는 로컬 파서이며, 논문 그림을 재구성하거나 분석 결과를 배포하지 않는다.

## Python API

- `AZ31BCorrosionFatigueReadAuthorization`: dataset/article DOI, CC BY 4.0 attribution, caller computational-use 및 local-only 승인을 요구한다.
- `AZ31BCorrosionFatigueWorkbookCell`: 원 열 번호, coordinate, Excel 저장 유형 및 raw cell value를 보존한다. 수식은 계산하지 않는다.
- `AZ31BCorrosionFatigueWorkbookRow`: 원 파일, provider file ID, workbook/sheet/row, 셀, Evidence와 canonical row digest를 결합한다.
- `iter_az31b_corrosion_fatigue_rows(directory, authorization=..., include_filenames=...)`: 선택된 고정 자산을 byte count와 provider SHA-256 확인 후 원래 행/열 순서로 전달한다.
- `audit_az31b_corrosion_fatigue_directory(request)`: 모든 workbook을 검증한 뒤 sheet dimensions와 해시만 반환하며 셀 값을 내보내지 않는다.
- 모델/interface ID: `data.mendeley_az31b_corrosion_fatigue_typed_rows`; source ID: `mendeley_az31b_corrosion_fatigue_lab_rows`.

```python
from matintegrity.mendeley_az31b_corrosion_fatigue_rows import (
    AZ31BCorrosionFatigueReadAuthorization,
    iter_az31b_corrosion_fatigue_rows,
)

authorization = AZ31BCorrosionFatigueReadAuthorization(
    attribution=(
        "Shaha et al. (2018), article DOI 10.3390/coatings8120443; "
        "Mendeley Data v1 DOI 10.17632/5b5rk27wmx.1; CC BY 4.0; "
        "local parsing with separate provenance review"
    ),
    computational_use_authorized=True,
    local_only_authorized=True,
)
for row in iter_az31b_corrosion_fatigue_rows(
    "data/raw/mendeley-az31b-corrosion-fatigue-cold-spray",
    authorization=authorization,
):
    # A separately reviewed parser must establish each block's meaning and units.
    print(row.source_filename, row.worksheet_name, row.provider_row_number)
```

`openpyxl` runs in read-only mode with `data_only=False`; formulas are never executed. Numeric/date/cell storage details are preserved as far as the XLSX cell model permits. The raw dataset stays local.

## 범위와 해석 제한

Workbook filenames retain the provider figure-number labels but the reader does not use them to infer table semantics. The parser does not assign axes, units, corrosion potential reference, exposed area, solution condition, coating state, specimen identity, replicate group, fatigue stress level, failure criterion or observation uncertainty. It does not fit EIS circuits, derive polarization parameters, estimate a corrosion rate, fit an S–N curve, compute a general corrosion-fatigue law, or establish coating acceptance/field life. The system is specific to the documented coated AZ31B/AA7075 material and test conditions; transfer requires separate source interpretation and validation.

# CT110 습윤 CO₂ 부식표 typed-row reader

## 목적과 공개자료

이 reader는 PLOS Figshare에 공개된 코일드 튜빙 CT110 용접금속(WM) 및 모재(BM) 중량감량 부식표의 로컬 사본을 검증하고, 원래 worksheet 행을 입력 근거와 함께 typed record로 제공한다. 논문 본문이나 표 수치를 코드·예제·배포 파일에 복제하지 않는다.

- 데이터 레코드: [PLOS Figshare supporting data](https://plos.figshare.com/articles/dataset/S1_File_-/13628192), DOI `10.1371/journal.pone.0244237.s017`
- 관련 논문: [PLOS ONE article](https://doi.org/10.1371/journal.pone.0244237)
- 레코드가 선언한 이용조건: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- 파일: `pone.0244237.s017.xlsx`, 9,331 bytes
- 공개 metadata MD5: `95fa4a025f4afe1aac1b5de41c420160`
- 이 PC 사본 SHA-256: `8e6ce76d2e67f9a24af1ccfadebc4453e5601c3a7694c7f4bf3d56d259145470`

실제 workbook을 내려받아 위 크기와 publisher MD5를 대조했다. reader는 추가로 이 로컬 사본 SHA-256을 요구한다. 원본은 `.gitignore`의 `data/raw/` 경로에만 보관하고 source/package artifact에 넣지 않는다. 사본 사용 시 호출자가 저자·두 DOI·CC BY 4.0 표시를 담은 attribution 및 local computational-use 권한을 제공해야 한다.

## 확인된 구조

고정된 workbook에는 `Sheet1`, `Sheet2`, `Sheet3`가 있다. Sheet1에는 온도, WM, BM의 세 관측 행이 있고 부식률 단위는 `mm/year`로 표시되어 있다. Sheet2와 Sheet3은 비어 있다. 고유 시편 식별자와 독립 반복 구조는 확인되지 않았으므로 reader가 만들거나 추정하지 않는다. 온도 범위는 제한된 세 점뿐이며, 이를 온도 의존식이나 일반 재료 데이터베이스로 취급해서는 안 된다.

## Python API

`matintegrity[science]`의 `openpyxl` 선택 의존성을 reader가 호출될 때 가져온다. Authorization 예:

```python
from matintegrity.ct110_wet_co2_typed_rows import (
    CT110ReadAuthorization,
    iter_ct110_corrosion_rows,
)

authorization = CT110ReadAuthorization(
    attribution=(
        "Liu et al. (2021), article DOI 10.1371/journal.pone.0244237; "
        "supporting data DOI 10.1371/journal.pone.0244237.s017; CC BY 4.0"
    ),
    computational_use_authorized=True,
    local_only_authorized=True,
)

for row in iter_ct110_corrosion_rows(
    "data/raw/plos-ct110-co2-weld/pone.0244237.s017.xlsx",
    authorization=authorization,
):
    # 각 row는 workbook/sheet/원래 행과 cell 위치, 파일·행 digest, Evidence를 보존한다.
    consume(row)
```

`audit_ct110_workbook`은 파일 identity, worksheet 구조와 row digest를 확인하는 registry용 요약 API다. 개별 부식률 값은 audit 결과에 넣지 않는다. Reader 결과는 row 순서와 원 단위를 유지한다. 재계산, fitting, 누락 보완, 반복수 추정, 온도 또는 CO₂ 분압 외삽은 수행하지 않는다.

## 한계 및 권리 경계

- 라이선스 표시는 publisher의 dataset record에서 확인한 것이며 법률 자문이나 제3자 권리 보증이 아니다. 재배포하려면 CC BY 4.0의 저작자표시와 변경표시 조건을 따라야 한다.
- 파일의 integrity pin은 파일 내용이 과학적으로 타당하다는 검증이 아니다.
- 구조가 고정된 workbook이 아니면 parser는 거부한다. 데이터 버전이 바뀌면 새 asset pin과 구조 검토가 필요하다.
- 이 입력만으로 재료 수명, 현장 부식률, 위험도, acceptance 또는 모델 일반화 성능을 주장하지 않는다.

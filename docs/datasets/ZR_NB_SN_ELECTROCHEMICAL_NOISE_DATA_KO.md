# Zr 합금 전기화학 잡음 표 데이터

## 공개 자료와 권리

- 현재 고정한 기록: Zenodo record `23220129`, concept record `20115353`, DOI `10.5281/zenodo.23220129`, v2.
- 게시 기록은 해당 version의 자료를 CC BY 4.0으로 표시한다. 재사용 시 저자·DOI를 인용하고 변경 여부를 밝혀야 한다.
- 기록에는 처리된 전기화학 자료가 포함되고, 수집 원시 시간 이력은 별도 합리적 요청으로 제공된다고 기술되어 있다. 이 프로젝트는 공개 XLSX만 다루며 비공개 요청 원자료나 게시된 Jupyter 코드를 내려받거나 실행하지 않는다.
- 원본 XLSX 사본은 `data/raw/zenodo-corrosion-zr-nb-sn-23220129-v2/`의 로컬 전용 경로에 보관한다. 이 경로는 배포 파일에서 제외된다. Zenodo가 게시한 파일 크기와 MD5, 로컬 보관 파일의 SHA-256은 `local_manifest.json`에서 기록한다.

## 자료 범위

표는 Zr–Nb 세 조성(Fe 300, 400, 600 ppm)과 Zr–Sn 계열 한 조성(Fe 1100 ppm)의 시간영역 전류·전위 잡음 및 주파수영역 PSD 자료를 포함한다. 각 파일 쌍은 서로 다른 물성/합금 조건이므로 하나의 독립 표본 집단으로 합치지 않는다. 주파수 표에는 스펙트럼 잡음 저항 계산 결과도 실려 있다. 게시 설명의 용액·pH·온도·수집률은 조건 설명으로 보존하고 개별 셀 값이 실제 측정·추정·계산 중 무엇인지 workbook 구조를 확인하기 전에는 의미를 부여하지 않는다.

## 사용과 경계

`matintegrity.zenodo_zr_alloy_electrochemistry` typed-row reader가 각 workbook/worksheet/원행/셀 순서, 셀 형식과 원본 파일 digest를 보존한다. 수식은 문자열로만 보존하고 실행하지 않으며, 빈 행은 생략하되 원래 행 번호는 유지한다. caller attribution과 로컬 전용 계산 권한이 필요하고, 승인된 파일명·크기·SHA-256 조합 외 입력은 거부한다. 수집된 표를 부식률, 표면 손실, 수명, 합격 여부 또는 독립 실험 검증으로 재해석하지 않는다. 같은 record의 notebook 계산이나 article 해석을 복제하지 않으며, 새 모델 검증은 본 라이브러리의 별도 방법·독립 데이터가 마련된 후 수행한다.

```python
from matintegrity.zenodo_zr_alloy_electrochemistry import (
    ZrAlloyReadAuthorization,
    iter_zr_alloy_workbook_rows,
)

authorization = ZrAlloyReadAuthorization(
    attribution="Soares et al., Zenodo v2, DOI: 10.5281/zenodo.23220129",
    computational_use_authorized=True,
    local_only_authorized=True,
)
rows = iter_zr_alloy_workbook_rows("/local/path/to/pinned.xlsx", authorization=authorization)
first_provider_row = next(rows, None)  # Continue consuming locally as required by the analysis.
```

원본 XLSX는 `data/raw` 아래에서만 다루고 패키지, 예제 fixture, HPC snapshot 또는 결과 archive에 포함하지 않는다. 이 입력 API는 자료 발견·정리 인터페이스이며, 아직 공정·환경 파라미터로 보정된 부식 예측 모델이나 검증 근거가 아니다.

## 원자료 인용

Soares, A. R. et al. (2026), *Supplementary data for: Electrochemical corrosion analysis of Zr–Nb and Zr–Sn alloys using classical, noise, and wavelet-based methods*, Zenodo, version 2, DOI: 10.5281/zenodo.23220129, CC BY 4.0.

기록과 version별 파일·라이선스는 [공식 Zenodo record](https://zenodo.org/records/23220129)에서 확인한다.

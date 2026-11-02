# 수소 실험 수치 내보내기와 검토

탄화물 트랩 공개 자료의 OPJU 두 파일을 공식 Origin Viewer로 열어 CSV로 저장하고 원본과 별도로 보존했다. 수치 읽기 경로는 확보됐으며 물리 모델 보정에는 시험 형상·경계조건·시편 대응 검토가 추가로 필요하다. [자료 제공자와 이용조건](https://doi.org/10.5281/zenodo.10416768)은 `THIRD_PARTY_NOTICES.md`에 기록했다. 이 문서는 원자료의 문장·그림·수치 표를 복제하지 않고 재현 절차와 조사 집계를 설명한다.

## 파일과 관측 단위

| 구분 | 고유 CSV | 읽은 수치 행 | 해석 |
|---|---:|---:|---|
| 투과 원시 채널 | 5 | 40,859 | 서로 다른 기록이며 독립 시편 수는 미확정 |
| 투과 계수 요약 | 1 | 4 | 제공자가 계산한 유효 확산계수·농도·오차 표시 |
| 열탈착 원시 채널 | 2 | 98,983 | 18개 온도/탈착률/원본 적분 열 묶음 |
| 열탈착 노출 요약 | 1 | 18 | 16개 충전 조건과 2개 미충전 대조 |

전체 11개 CSV 중 두 쌍이 바이트까지 같아 고유 파일은 9개다. 중복은 삭제하지 않고 동일 해시와 별칭으로 기록한다. 기존 취득량 17자료·65파일에는 이 로컬 파생 파일을 더하지 않는다. 각 파일의 원 프로젝트·도구 버전·workbook/worksheet 검토 상태·SHA-256은 로컬 `export_manifest.json`, 공개 가능한 집계는 `data/data_inventory.json`에 있다. 일부 worksheet 대응은 미확정으로 남긴다. 파일 해시가 같아도 실제 시험 조건이나 시편 독립성이 검증됐다는 뜻은 아니다.

## 확인한 데이터 문제

- 투과의 A/B/C는 전위·전류·계측 시계 채널로 보존하고 D의 이동 시계와 E의 처리 전류를 분리한다. 전극 면적이 없어 전류를 전류밀도로 만들지 않는다. 소스 주석의 `density`라는 단어로 단위를 확정하지 않는다.
- BQ2의 계측 시계−이동 시계는 3,834초인데 충전 시작 주석은 3,835초다. 다른 기록의 일정 이동량도 물리적 충전 시작으로 자동 선택하지 않는다. Fe-Mo 원 기록의 초기 계측 과도 구간을 포함해 사용 구간을 별도로 검토해야 한다.
- 처리 전류의 음수 2,493행을 보존한다. 주석의 기준값과 실제 처리 열에서 역산한 차감값도 자동으로 같다고 가정하지 않는다. 배경 제거·0 절단·시간 이동은 로더가 수행하지 않는다.
- 확산 요약의 `(Ti,Mo)C steel`은 CSV 내 쉼표가 인용되지 않아 7열로 나뉜다. 기본 정책은 거절이며 `join_split_ti_mo`를 명시한 경우에만 그 정확한 표식의 두 조각을 연결한다. 원 파일은 고치지 않는다.
- 확산계수 원 숫자는 m²/s 척도다. 그래프가 10⁻¹¹ m²/s 축을 쓴다는 이유로 원 숫자에 다시 10⁻¹¹을 곱하지 않는다. 원본의 유효 계수는 격자 고유 확산계수와 구분한다. 공개 보충자료는 열탈착률과 잔류량을 시편 질량 기준 수소 질량 ppm으로 표시한다. 투과 요약의 오차 막대는 적어도 두 번의 측정으로 계산한 표준편차지만, 파일별 반복·시편 대응은 미확정이다. 오차 0과 `--` 누락을 구분한다.
- 열탈착 온도는 반복 17,328구간·역전 8,786구간을 포함한다. 순서를 정렬하거나 중복 온도를 삭제하지 않는다. 음의 탈착률 869행도 유지한다. 명목 가열률을 이용해 측정하지 않은 정밀 표본 시계를 만들지 않는다.
- IP2의 한 곡선 끝에는 `--`로 표시한 미기록 온도 411행과 빈 신호 열이 있다. 이를 숫자 관측으로 만들지 않고 별도 누락 집계로 보존한다. 중간 누락이나 일부 채널만 없는 관측은 거절한다.
- 원시 표의 세 번째 채널은 제공자가 만든 적분 열이며 새로운 측정이 아니다. 원시 온도 전체 범위와 요약표 주석의 실온~260°C 적분 범위도 다르다. 같은 적분을 두 번 적합 자료에 넣지 않는다. 10⁻⁵ ppm/s 그래프 표시와 원 탈착률 값도 이중으로 배율 변환하지 않는다.
- 노출시간 요약은 순서가 정렬돼 있지 않으며 동일 시편의 연속 이력으로 취급하지 않는다. `uncharged`와 충전 후 노출 0시간을 구분한다. 보조 회귀·적합 곡선 시트는 관측으로 내보내지 않았다.
- 원시 열탈착 곡선의 크기와 노출시간 요약을 함께 대조하면 IP0은 TiC, IP2는 (Ti,Mo)C 계열일 가능성이 높다. 이는 파일 간 재료명 대응이며 각 곡선의 물리 시편 ID나 반복 관계를 확정하지 않는다.

## 재현 절차

1. `scripts/fetch_data.py --ids carbide-traps --include-optional`로 취득한다. 이미 있는 파일은 취득 장부와 체크섬을 먼저 확인한다. 전체 ZIP은 약 2.64 GB다.
2. ZIP의 `Thermal desorption spectroscopy and hydroge permeability raw data/`에서 OPJU 두 개를 `data/derived/carbide-traps/viewer-input/`에 복사한다. 파일명의 원래 철자를 보존한다. 단순히 OPJ로 이름을 바꾸거나 내장 스크립트를 실행하지 않는다.
3. [OriginLab 공식 Viewer](https://www.originlab.com/viewer/index.aspx)를 별도 로컬 도구로 사용한다. 이번 실행 버전은 파일 버전 구성요소 기준 10.4.0.25다. 제품 UI 버전은 10.4로 표시된다. 도구와 설치 패키지는 저장소 의존성·배포물에 넣지 않는다.
4. workbook과 원 데이터 worksheet를 선택하고 `File → Export Data to CSV`로 저장한다. 투과는 BQ0·BQ2·두 번째 기록·Fe-Mo 기록과 Book1/Sheet2 요약을 구분한다. TDS는 IP0time/Sheet1·IP2time/Sheet1·A4ElapsedTime/Sheet1을 선택한다. 현재 파일명 대응은 `scripts/record_hydrogen_exports.py`의 `EXPORTS`에 있다. 변경된 내보내기는 같은 버전이라고 덮어 기록하지 말고 대응과 단위를 다시 검토한다.
5. 그래프 축을 눈으로 대조하고 원 숫자에 표시 배율을 다시 적용하지 않았는지 확인한다. 일부 worksheet 이름이나 축 기준이 불분명하면 검토 상태를 미확정으로 남긴다.
6. 실제 사용한 Viewer 버전으로 장부를 생성하고 집계를 확인한다.

```powershell
.\.venv\Scripts\python.exe scripts/record_hydrogen_exports.py --tool-version 10.4.0.25
.\.venv\Scripts\python.exe scripts/inspect_open_data.py
.\.venv\Scripts\python.exe scripts/verify.py
```

장부 작성기는 취득 당시 검증한 전체 ZIP 해시를 장부에서 가져오고 현재 프로젝트 member 두 개를 다시 해시한다. 전체 ZIP을 재해시한 것처럼 기록하지 않는다. CSV마다 별도 해시를 계산하고 로더가 읽을 때 다시 대조한다. 실제 파일·장부·도구는 제외 경로에 남기며 공개 배포에는 로더·합성 검사·설명·집계만 담는다. 제공자 조건과 도구 이용조건을 분리해 유지한다.

## Python API

```python
import json
from pathlib import Path
from matintegrity.hydrogen_exports import (
    TabularExportProvenance, read_permeation_export,
)

folder = Path("data/derived/carbide-traps/viewer-export")
manifest = json.loads((folder / "export_manifest.json").read_text(encoding="utf-8"))
record = next(r for r in manifest["exports"] if r["reader"] == "read_permeation_export")
reference = TabularExportProvenance.model_validate(record["provenance"])
frame = read_permeation_export(
    folder / record["filename"], reference, **record["reader_kwargs"],
)
```

`read_permeation_summary`, `read_tds_export`, `read_tds_exposure_summary`도 같은 provenance 계약을 받는다. 호출자가 단위를 선언하지 않으면 원 채널을 유지하고 SI 열을 누락 값으로 남긴다. 두 TDS 로더는 `ppm_basis="hydrogen_mass_per_sample_mass"`를 명시한 경우에만 공개 보충자료로 검토한 질량 기준을 attrs에 기록하며 기본값은 `unresolved`다. 파생·대체 파일에 이 검토값을 자동 상속하지 않는다. 반환 DataFrame의 `attrs`에는 선언 단위·원본 해시·시계 정책·관측 의미·미확정 항목이 있다. CSV만 다시 저장하면 attrs가 사라지므로 장부나 별도 JSON을 함께 보존한다. 과학 의존성은 이 로더를 호출할 때만 필요하다.

물리 신호 변환은 별도 계약을 사용한다. `HydrogenPermeationSignalCalibration`은 정확한 export
해시와 specimen/material ID, 선택 전류·시계, clock origin, 막 면적, 바깥쪽 플럭스 부호,
전자수, 전류효율, 배경처리와 각 근거를 요구한다. `permeation_flux_observations`는 모든 시각이
원점 이후이며 엄격히 증가할 때만 signed `mol H atoms/(m²·s)`와 누적 `mol H atoms/m²`를
만든다. 행을 정렬·필터링하거나 음수를 0으로 자르지 않는다.

`HydrogenTdsSignalCalibration`은 정확한 series index/label, heating-program ID, 수소 원자
몰질량, 질량 ppm 기준과 검출기 검토를 요구한다. `tds_molar_observations`는 한 series의 signed
`mol H atoms/(kg sample·s)`와 source-derived `mol H atoms/kg sample`을 만들되 온도 순서와 원
source row를 유지한다. 검토된 시편 질량이 있으면 전체 `mol/s`와 `mol`도 추가하고, 없으면
질량 정규화 결과만 만든다. 시계가 없으므로 동역학 적합 준비 상태는 명시적으로 false다. 두
변환의 calibration digest를 원 provenance와 함께 저장한다.

투과에서 반복·역전 시각은 기본적으로 거절하고 `clock_policy="preserve"`를 명시한 경우에만 그대로 읽는다. 이 정책은 미분·적분이 유효하다는 선언이 아니다. TDS는 온도가 시계가 아니므로 원 순서를 기본으로 보존한다. 수치·형식 검사와 질량 ppm 검토가 성공해도 보정에 필요한 경계 농도·투과막 두께·전극 면적·전위 기준·실제 specimen ID·검출기 응답은 채워지지 않는다.

## 다음 물리 검토

공개 본문에서 열탈착 시편의 유한 원통 치수(지름 5 mm, 길이 25 mm), 48시간 전기화학 사전충전과 질량 ppm 보고는 확인했다. 보충자료의 명목 가열 프로그램은 100 K/h지만 측정 표본 시계가 아니므로 온도에서 elapsed time을 재구성하지 않는다. 본문에 시편별 질량이 없어 전체 mol 환산에도 쓰지 않는다. 투과막 두께·전극 면적·전위 기준, 충전 조건의 원곡선 대응, 시계 원점·가열 및 방출 경계·배경 보정·검출기 보정과 각 파일의 시편 대응은 계속 확인한다. 확인된 값만 위 신호 변환 계약에 넣는다. 전기화학 충전과 기체 압력 경계를 구분한다. 평판 투과 모델과 열탈착 시편 형상을 자동으로 같게 두지 않는다. 이후 유한 영역 수송·포획/탈리 속도 모델을 질량 보존·해석해·공간/시간 수렴으로 검사하고, 보정과 독립 실험 비교를 분리한다. 현재 국소 평형 계산, CSV 구조 검사 또는 단위 변환을 동역학·균열·설비 고장확률 검증으로 표시하지 않는다.

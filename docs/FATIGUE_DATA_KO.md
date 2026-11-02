# 피로 시험자료 계약과 검토 경계

## 범위

현재 피로자료 경로는 FABEST의 stress-controlled 고주기 관측과 별도 strain-life 관측, BAM P92의 기록 파형을 읽는다. 자료를 읽는 것과 수명곡선 자격·손상 보정·독립 실험 검증을 구분한다. 외부 workbook과 점별 관측은 공개 배포물에서 제외하고 코드·집계·출처·체크섬만 배포한다.

2026-10-26에 등록된 Strathclyde의 [S355 이상 해상 재생에너지 강재 피로 데이터베이스](https://pureportal.strath.ac.uk/en/datasets/data-for-an-open-database-of-s-n-fatigue-data-for-high-strength-s/)는 dataset package에 CC BY 4.0을 선언하며 S–N 및 fatigue-crack-growth/ΔK 자료를 설명한다. 현재 카탈로그에는 메타데이터만 등록했다. 익명 파일 요청은 HTTP 403을 반환했고 체크섬도 확인하지 못했다. 자료가 논문에서 디지타이즈됐으므로 각 원 관측의 재배포권, 행·시편 출처, runout과 단위 검토 전까지 취득·적합·점별 재배포를 보류한다. 이 기록은 새로운 모델 검증 자료가 아니다.

같은 Strathclyde 계열에서 2026년 9월 고강도강 FCGR compilation, 2026년 공기환경 S355 FCGR workbook(+별도 load-spectrum workbook), 2025년 seawater free-corrosion S355 FCGR workbook을 추가 식별했다. 각 제공 레코드는 dataset package에 CC BY 4.0을 표시하지만, 세부 자료는 문헌 표 전사와 figure digitization을 포함할 수 있다. 파일별 익명 요청은 HTTP 403이었고 제공자 체크섬이 없어 모두 metadata-only다. 관련 workbook 사이의 같은 publication·series·point 중복을 확인하기 전에는 각각 별도의 보류 검증집합으로 계산하지 않는다. 원자료 확보 후 workbook sheet/field audit, source publication ID, test/specimen grouping, unit·R·frequency·environment·stage·runout semantics 검토가 먼저 필요하다.

검토자가 합법적인 원 CSV를 확보한 경우 일반 입력 경로는 `matintegrity.fcgr_curve_import`다. 이 API는 명시적 단위 변환과 행별 include/exclude 결정을 받아 기존 `TabulatedCrackGrowthCurve`로 연결하고 원 파일 digest 및 mapped row audit를 반환한다. stage 값의 의미를 추정하거나 특정 stage를 자동 제외하지 않으며, 이 경로는 위 메타데이터 전용 workbook들을 읽었다는 뜻이 아니다.

추가로 [Dryad의 AM 고엔트로피 합금 피로 자료](https://doi.org/10.5061/dryad.vq83bk48n)를 식별했다. provider README는 세 개 macroscale SENB 시편의 처리 CSV가 ΔK와 da/dN을 포함한다고 설명하고, Dryad API는 해당 ZIP의 CC0 metadata, 정확한 크기와 SHA-256을 제공한다. 원자료 API 다운로드는 이 환경에서 HTTP 401을 반환해 archive는 취득하지 않았으며 catalog는 `metadata_only`다. 자료는 단일 AM HEA 연구의 처리 출력이므로 철강·부식피로·일반 설비 검증과 독립된 validation set으로 보지 않는다. microscale 자료는 J 기반이므로 ΔK curve importer로 섞지 않는다.

[Mendeley S460 fatigue characterization v2](https://data.mendeley.com/datasets/ytny53v2fn/2)는 CC BY 4.0이며 dataset API에 파일별 SHA-256이 공개되어 있다. 그중 `Paris Law Constants.xlsx` 하나(210,307 bytes)만 `data/raw`에 받아 provider SHA-256과 일치시켰다. workbook은 CT01–CT06 specimen별 여섯 시트와 별도 요약 시트로 구성된다. 관측 시트는 ΔK [MPa·√m], da/dN [mm/cycle], R=0.1/0.25/0.5를 보고하고 표에 기재된 증가 ΔK 점은 각각 15, 14, 22, 22, 23, 23개다. 이 구조 감사는 실험 정확도 평가가 아니며, 여섯 시편은 단일 연구 안에서 독립적인 여섯 연구로 보지 않는다. 시트에서 주파수를 찾지 못했으므로 현재 frequency-required curve API에 직접 전달하지 않는다. 나머지 253개 데이터 파일은 취득하지 않았다.

FABEST 고정 자료는 [Zenodo record 10.5281/zenodo.21509581](https://doi.org/10.5281/zenodo.21509581)의 CC BY 4.0 workbook이다. 로더는 VBA를 실행하지 않으며 제공자의 regression 출력은 원 관측과 분리한다.

## FABEST 종료 계약

`read_fabest`는 다음 필드를 서로 바꾸지 않는다.

- `reported_endpoint`: provider가 기록한 `finished`, `interrupted` 또는 누락
- `cycles_to_end`: 정의된 END까지의 보고 cycle. 실제 END 정의가 곡선 sheet에 없을 수 있음
- `cycles_to_reported_break`: 별도 break-cycle 열의 보고값
- `endpoint_contract_status`: 위 필드 조합의 구조 상태
- `provider_interrupted`: 제공자 interruption 표식. 자동 runout 또는 우측 검열 판정이 아님
- `calibration_role`: 추가 검토가 없는 행도 `candidate_failure_observation` 또는 `candidate_censored_observation`일 뿐

고정 workbook의 고주기 60그룹·663행에서는 break cycle 567행, interruption 95행, 미확정 1행이다. 데이터 사전에는 END 코드가 정의돼 있지만 60개 곡선 sheet 모두 `END`/`END_PAR`를 제공하지 않는다. Break cycle과 no-crack 계열 주석이 함께 있는 18행도 원 필드를 보존한다.

## 시편명과 자유문

문자 접미사가 있는 54행은 재시험이라고 정의되지 않았다. `specimen_label_suffix_status="letter_suffix_semantics_unresolved"`로 표시하고 시편 계보·독립성·누적 cycle을 만들지 않는다. `physical_specimen_independence_reviewed`는 근거가 없으면 false다.

주석 89행에는 단순 문자열 규칙으로 `reported_thread_damage`, `reported_grip_fretting`, `reported_no_crack`, `reported_excluded`, `reported_mistake`, `reported_possible_buckling`, `reported_comment_temperature` 등을 붙인다. 태그는 원문 검토를 찾기 위한 색인이다. 파단 위치, 시험 유효성, self-heating 또는 온도 측정 위치를 판정하지 않는다. `reported_comment_temperature_degC`도 원 문자열 숫자일 뿐 SI 시편 온도로 승격하지 않는다.

## 보정 사용

`fit_censored_sn` 자체는 사용자가 제공한 failure/censoring 배열을 적합한다. FABEST 전체에 자동 적용하지 않는다. 현재 FAB005 시범은 주석·문자 접미사가 없는 candidate 행만 선택하고, 그 선택 범위에서 provider interruption을 우측 검열로 보는 가정을 별도로 기록한다. 같은 자료에서 얻은 작은 시범 적합은 서비스용 S–N 곡선, 보수 하한, 독립 검증 또는 기간 고장확률이 아니다.

## 재현

```powershell
.\.venv\Scripts\python.exe scripts\inspect_fabest_data.py
.\.venv\Scripts\python.exe scripts\inspect_open_data.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_fatigue_observations.py
```

감사기는 고정 SHA-256, 파일 크기, 73개 sheet, 관측·정적·회귀·strain-life 분리, 종료 상태와 자유문 태그 집계를 확인한다. 이는 소프트웨어·자료구조 검증이며 시험 프로토콜이나 재료 수명모델의 실험 자격이 아니다.

## 다음 작업

60그룹별 원 시험 프로토콜 또는 제공자 설명에서 END 기준, interruption 사유, 문자 접미사와 물리 시편 관계, 온도 측정 위치·시각, 목표부/고정부 파손 처리와 독립 시험 집단을 확인한다. 확인 뒤에도 원 필드와 검토 결론을 분리하고, 보정·보류·독립 기관 검증을 서로 다른 상태로 기록한다.

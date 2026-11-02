# 연구·검증·개발 재개 설명서

## 첫 30분에 확인할 파일

1. [README](../README.md): 단위 API 선택, 목적, 주요 입출력, 현재 공개 상태.
2. [상세 사용 설명서](GETTING_STARTED_KO.md)와 [모듈 디렉터리](MODULE_DIRECTORY_KO.md): 실제 입력 계약과 적용 한계.
3. [공개 상태](RELEASE_STATUS_KO.md): 남은 실패·데이터 의존성·검증 범위.
4. [개발 이력](DEVELOPMENT_HISTORY_KO.md): 어떤 순서와 근거로 구현·수정·검사했는지.
5. `validation/core_execution_receipt.json`, `physical_review_receipt.json`, `prepublish_checks.json`: 숫자의 실제 분모와 근거.
6. `tests/data/core_physics_full_run_targets.json`, `core_physics_formula_cases.json`: 고정된 63개 군 및 232개 API 목록과 시험 매핑.
7. `data/catalogs/datasets.json`, `sources.json`, `THIRD_PARTY_NOTICES.md`: 자료 취득·권리·출처·사용 한계.

첫 공개 commit는 그 이전 로컬 작업을 모은 누적 snapshot이다. 공개 이전 모든 작업이 개별 Git commit로 남아 있다고 가정하면 안 된다. 이력에 없는 실행·시험을 통과했다고 복원하지 않는다.

## 숫자를 섞지 않는 규칙

| 숫자 | 의미 |
|---|---|
| 757 | registry에 등록된 전체 API. 자료 읽기·계약·교환·품질·워크플로 포함 |
| 63 | 검토 대상으로 고정한 핵심 물리 기능 묶음 |
| 232 | 위 63개 군에 명시적으로 배정한 개별 실행 감사 API |
| 116 | 이전 단계의 입력 계약 감사 대상 집합 |
| 101 | 더 넓은 기술 범위를 분류했던 backlog 항목. 독립 계산기 수와 다름 |
| 400 | 주 JSON 예제 파일에 들어 있는 API 수. 전체 예제·시험의 합계가 아님 |

시험 수·계산군 수·API 수·데이터 행 수·독립 시편 수를 서로 환산하지 않는다. 대표 시험이 있는 계산군을 그 안의 모든 모델·분기·실험 검증 완료로 표시하지 않는다.

## 개발 환경 복원

```bash
git clone https://github.com/lyullee/materials-corrosion-toolkit.git
cd materials-corrosion-toolkit
git checkout v0.1.0a1
python -m venv .venv
python -m pip install -e ".[science,thermo,dev]"
python -m pip check
python -m matintegrity.cli models
```

배포 버전, Git commit, Python·OS·라이브러리 버전과 입력·자료·provider 해시를 함께 남긴다. `validation/environment.json`은 특정 시점의 환경 기록이며 모든 플랫폼의 lockfile은 아니다. 핵심 코드는 기본 의존성만으로 import되어야 한다. 선택 라이브러리 부재 시험은 `tests/test_core_without_science_imports.py`에 있다.

## 검증을 재개하는 순서

### 빠른 계약·물리 회귀

```bash
python -m pytest -q tests/test_physical_consistency_review.py
python -m pytest -q tests/test_prepublish_runtime_regressions.py tests/test_core_without_science_imports.py
python scripts/verify_core_physics_formulas.py
python scripts/audit_schema_coverage.py
```

### 고정된 개별 계산 전수 실행

```bash
python scripts/prepare_core_full_run_inputs.py
# 별도로 허용된 Hannover 원자료를 취득한 경우에만 아래 단계를 추가한다.
python scripts/prepare_hannover_sines_execution.py
python scripts/run_core_physics_full_calculations.py
python scripts/report_core_execution.py
```

원자료·생성된 절대 파일 경로·상세 결과는 `artifacts/validation/full_core_calculations`에 남고 공개 제외한다. `--pending`은 재개용이며 최종 전수 실행과 구분한다. 모든 232개가 계산되지 않으면 종료 코드가 1일 수 있다. 그 경우 `summary.json`에서 계산 오류인지 외부 근거 보류인지 먼저 확인한다.

### 전체 기존 검사

```bash
python -m pytest -q
python -m ruff check src tests scripts examples
python -m ruff format --check src tests scripts examples
python scripts/verify.py
```

현재는 알려진 전체 정적 지적과 주 예제 파일 완전성 검사 때문에 이 묶음이 실패할 수 있다. 기존 검사를 삭제하거나 범위를 줄여 전체 완료로 표시하지 않는다. 마지막 전체 실행 이후의 파일별 재실행 대조 결과와 새 전체 실행 결과는 구분한다.

## 현재 먼저 해결할 과업

1. 전체 Ruff 지적을 파일·종류별로 분류한다. 정의 누락류는 고쳤지만 loop closure, 중복 정의·키, unused 등 남은 지적을 모두 서식으로 치부하지 않는다. 계산 의미를 바꿀 수 있는 항목부터 독립 기준값·분기 시험과 함께 수정한다.
2. 주 JSON 예제 파일의 400/757 포함 상태를 보완한다. 선행 결과·외부 provider·권한 있는 파일이 필요한 API에는 정직한 준비 절차와 실행 가능한 wiring 예제를 제공한다. 실측·권한을 허위로 만든 독립 fixture를 만들지 않는다.
3. 실측 초기 두께 근거가 없는 `corrosion.piecewise_linear_rate_thickness_history` 정상 실행과 기초 관측자료 권한이 없는 대기 부식 자료 읽기는 확보 전까지 보류한다.
4. 물리 계산 간 연결의 기존 대표 근거는 15/63개 군이다. 결과→규칙 소비 모듈 63/63과 섞지 말고, 필요한 실제 물리 체인을 우선순위에 따라 추가한다.
5. 재료별 상수·가정·실험 endpoint를 고정한 독립 holdout 비교를 추가한다. 동일 자료의 피팅 오차는 독립 검증으로 세지 않는다.

## 데이터 취득과 연구 분할

카탈로그의 URL·버전·SHA-256/공급자 checksum·bytes·라이선스·기초 관측자료 권리 상태를 확인한 뒤 취득한다. 실측 표와 논문 출판 라이선스는 다를 수 있다. 원자료는 `data/raw`, 파생 관측은 `data/derived`, 연구 근거는 `data/evidence`에만 두고 공개 대상에서 제외한다.

교정·holdout은 실제 시편·source group·재료 상태·시험 endpoint에 따라 사전에 나눈다. 한 시편의 반복 시간점·픽셀·증강 이미지·여러 하중 단계는 독립 시편 수가 아니다. nominal load에서 재구성한 응력을 실제 local tensor 측정이라고 표시하지 않는다.

## 독립 과업의 병렬 실행

로컬과 HPC에서 독립 case를 ID로 나눈다. case별 입력·소스·환경 해시, seed, 시작/종료, 상태, 예외, 출력 해시를 남긴다. 완료된 case를 분석하는 동안 다음 독립 case를 실행할 수 있다. 단, 파일을 공유하는 수정·카탈로그 생성·배포 snapshot은 순서를 지켜야 한다.

`hpc`와 `scripts/hpc_pytest_shard.py`는 분할 구조를 보여 준다. 사용자 계정·인증·OTP·호스트별 연결 정보는 저장소에 넣지 않는다. 원격 작업 제출은 운영자가 허용한 자원·스케줄러 조건에서만 수행한다. 원격 성공 상태를 로컬 파일 존재만으로 대신하지 않는다.

## 단위 모델 추가·수정 체크리스트

1. 물리량, 단위, 부호, 기하·재료·시간 범위와 보류 조건을 먼저 작성한다.
2. Pydantic 입력 계약과 독립적으로 작성한 계산 함수를 둔다. `Calculation`과 표준 `AssessmentResult`를 유지한다.
3. `ModelSpec`의 ID·버전·가정·선언 출력 단위·provider·확률 의미를 등록한다.
4. 작은 해석해, 수지·불변량, 경계값, 잘못된 입력, 필요한 연결을 검증한다.
5. 스키마·카탈로그·상세 API 문서·README 디렉터리·예제·검증 매핑을 갱신한다.
6. 새로운 공개 자료·라이브러리의 권리와 출처를 별도로 기록한다.
7. 기존 Python import와 다른 저장소의 교환 계약을 바꾸면 버전·이행 안내와 확장 요청서를 남긴다.

```bash
python scripts/build_source_catalog.py
python scripts/build_capability_catalog.py
python scripts/sync_catalogs.py
python scripts/export_schemas.py
python scripts/build_model_reference.py
python scripts/build_publication_docs.py
```

schema/test source hash가 바뀌면 변경한 근거를 검토하고 해당 시험을 재실행한 뒤 매핑을 갱신한다. 단순히 해시만 덮어써 과거 통과 상태를 유지하지 않는다. 관련 저장소의 물리를 이 프로젝트에서 검증했다고 표시하지 말고 [확장 요청서](extension_requests/README_KO.md)에 필요한 입출력·단위·ID·검사 조건을 전달한다.

## 배포·인용·버전

첫 공개 버전은 `0.1.0a1`이며 Python namespace는 `matintegrity`다. GitHub tag, PyPI 배포와 Zenodo 보관본의 버전·해시를 맞춘다. 원자료나 비밀정보가 없는 허용 목록으로만 snapshot을 만든다. 계정 권한·토큰은 문서에 넣지 않는다. DOI가 발급되면 `CITATION.cff`, `.zenodo.json`과 공개 기록을 갱신하되 이미 보관한 아카이브의 바이트가 바뀌었다고 가장하지 않는다.

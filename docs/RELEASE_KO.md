# 배포 재현과 공개 범위

독립 저장소의 루트는 이 패키지 디렉터리다. 상위 디렉터리는 배포 대상이 아니다. 외부 자료 캐시·수집 근거·파생 관측은 `.gitignore`와 source manifest에서 제외한다. MIT 코드 라이선스는 외부 데이터와 의존성의 라이선스를 바꾸지 않는다.

## 로컬 재현

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[science,thermo,dev]"
.\.venv\Scripts\python.exe scripts/verify.py
.\.venv\Scripts\python.exe scripts/fetch_data.py
.\.venv\Scripts\python.exe scripts/fetch_data.py --ids carbide-traps --include-optional
.\.venv\Scripts\python.exe scripts/inspect_open_data.py
.\.venv\Scripts\python.exe examples/python_composition.py
.\.venv\Scripts\python.exe examples/process_history.py
.\.venv\Scripts\python.exe scripts/build_release.py
.\.venv\Scripts\python.exe -m build
.\.venv\Scripts\python.exe scripts/check_installed_wheel.py
.\.venv\Scripts\python.exe scripts/audit_packages.py
```

확보 기록의 최초 취득일·해시는 보존한다. 재취득에서 제공자가 파일을 바꾸거나 삭제하면 성공한 것으로 간주하지 않고 리비전·체크섬 불일치를 검토한다. 데이터 조사에는 과학 의존성과 카탈로그의 기본 취득 파일이 필요하며 외부 파일은 wheel에 포함되지 않는다.

`validation/summary.json`과 `unit_tests.xml`은 코드 검사 결과, `environment.json`은 빌드 환경의 버전·설치 메타데이터, `release_manifest.json`은 공개 소스의 파일별 해시다. `clean_install.json`과 `package_audit.json`은 해당 파일이 존재할 때 실제 별도 환경 설치·포함 목록 점검의 증거다. 로그만 생성하고 실행을 생략한 항목은 성공으로 기록하지 않는다. 기존 `release_manifest.json`이 현재 선택 파일·크기·SHA-256과 맞지 않으면 allowlist에서 제외하며, 배포 직전 `build_release.py`가 manifest를 새로 작성한 뒤 검토 묶음에 포함한다.

검사 기록까지 source archive에 포함하려면 첫 빌드·감사 후 `build_release.py`, `python -m build`, `audit_packages.py`를 한 번 더 실행한다. 외부 `dist/checksums.json`에 최종 세 배포물의 SHA-256을 기록하므로 소스가 자신의 해시를 포함하는 순환을 만들지 않는다.

핵심 wheel 검사는 `python -m venv artifacts/core_environment`로 만든 별도 환경에 wheel만 설치한 뒤 그 Python으로 `scripts/smoke_core.py`를 실행한다. 선택 기능 검사는 별도 환경에 `"dist/matintegrity-0.1.0.dev0-py3-none-any.whl[science,thermo,dev]"`를 설치하고 `python -m pytest -q --junitxml=validation/clean_full_tests.xml`로 실행한다. 개발용 editable 설치나 system site packages가 섞이지 않게 한다.

`check_installed_wheel.py`는 두 환경의 생성·wheel 재설치·의존성 확인·핵심 실행·전체 검사·설치 코드/카탈로그 해시 대조를 재현한다. 환경과 상세 로그는 제외 경로인 `artifacts/`에 두고 요약 증거만 `validation/`에 저장한다. 이전 버전의 설치 기록을 새 소스의 증거로 재사용하지 않는다.

## 배포물

민감도 설계와 외부 응답 JSON은 실제 파라미터·사용자 모델 설정을 포함할 수 있다. 원본 design/evaluations/report는 `data/derived/` 등 로컬 제외 경로에 보존하고, 공개 배포에는 작성한 합성 예제·수학 검증 집계·계약만 포함한다. digest만으로 사용자 자료의 재배포 권리가 생기는 것은 아니다.

- wheel: 설치 가능한 Python 패키지와 세 개의 공개 카탈로그. 선택 의존성은 해당 기능에서만 불러온다.
- source archive: 소스·테스트·예제·매뉴얼·카탈로그·취득 장부·검증 기록. raw 데이터는 제외한다.
- `matintegrity-source-review.zip`: 명시한 허용 경로만 담은 검토용 소스 묶음. 버전관리 저장소의 대체물은 아니며 빌드 검토용이다.

배포 source selection에는 내부 작업 지침 `AGENTS.md`를 포함하지 않는다. `validation/`의 구조화된 JSON/XML 증거만 선택하며, 임시 조사 콘솔 덤프와 `.txt` 로그는 공개하지 않는다. 새 증거 형식은 공개 가치·출처·민감정보 포함 여부를 검토한 뒤 allowlist에 명시한다.

`build_release.py`는 공개 카탈로그와 wheel용 카탈로그 사본의 byte equality도 확인한다. 불일치가 있으면 scripts/sync_catalogs.py를 다시 실행한 뒤 릴리스한다. `setup.py`의 setuptools build hook도 wheel을 구성할 때 같은 검사를 적용하므로 `python -m build` 직접 실행에서도 오래된 카탈로그 사본이 패키지에 들어가지 않는다. 외부 바이너리·개인 경로 표식도 검사한다. 이 검사는 소스 포함 범위를 확인하며 법적 권리나 과학적 정확성 인증이 아니다. 공개 전 제3자 고지·라이선스·자료별 재배포 상태를 유지한다. 테스트 출력에도 불필요한 호스트 이름을 보존하지 않는다.

MATLAB `.mat` 원자료도 source manifest·검토 묶음·실제 배포 포함 검사에서 제외한다. WILLOW와 다른 외부 자료의 숫자 관측은 로컬 캐시로 재취득하며 배포물에는 조사 집계·변환 코드·근거·체크섬을 남긴다.

## GitHub 사용

새 저장소에는 이 디렉터리의 공개 소스만 넣는다. `data/raw`, `data/derived`, `data/evidence`, 환경·산출물·빌드 캐시를 올리지 않는다. 새로운 파일을 추가하면 `scripts/build_release.py`로 포함 목록을 검토한다. 현재 작업은 로컬 구현·검증·문서화이며 원격 저장소 생성·push·다른 프로젝트 변경은 포함하지 않았다. CI 구성은 저장소에 push된 뒤 실제 실행 결과를 확인해야 한다.

공개 취득 장부의 요청/응답 주소에서는 query·fragment·URL 자격정보를 제거한다. 임시 서명 URL은 재현 가능한 자산 주소가 아니며 배포 검사에서 거절한다. 재취득은 별도로 검토한 카탈로그의 안정된 원 주소와 체크섬을 사용한다.

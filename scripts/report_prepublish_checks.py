"""Summarize bounded prepublication checks without hiding outstanding CI gates."""

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def xml_counts(path):
    cases = list(ET.parse(path).iter("testcase"))
    return dict(
        cases=len(cases),
        failed=sum(any(n.find(t) is not None for t in ("failure", "error")) for n in cases),
        skipped=sum(n.find("skipped") is not None for n in cases),
    )


def tree(root):
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file() and p.suffix in {".py", ".json"} and "__pycache__" not in p.parts
    }


def main():
    expected = tree(ROOT / "src/matintegrity")
    installed = {}
    probe = """
import hashlib,importlib.util,json,sys
from pathlib import Path
import matintegrity
from matintegrity.registry import default_registry
root=Path(matintegrity.__file__).resolve().parent
assert root.is_relative_to(Path(sys.prefix).resolve()), 'Package did not import from selected installation'
files={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and p.suffix in {'.py','.json'} and '__pycache__' not in p.parts}
print(json.dumps(dict(models=len(default_registry().list_models()),tree=files,optional={n:importlib.util.find_spec(n) is not None for n in ('scipy','CoolProp','pandas','rainflow')})))
"""
    for environment in ("core", "full"):
        python = ROOT / f"artifacts/{environment}_environment/Scripts/python.exe"
        run = subprocess.run(
            [str(python), "-I", "-c", probe],
            capture_output=True,
            text=True,
            encoding="utf8",
            errors="replace",
        )
        (ARTIFACTS / f"prepublish-{environment}-source-probe.log").write_text(
            run.stdout + run.stderr, encoding="utf8"
        )
        if run.returncode:
            raise RuntimeError(f"{environment} installed source probe failed; inspect local artifact log")
        data = json.loads(run.stdout)
        if data.pop("tree") != expected:
            raise ValueError(
                f"{environment} installed wheel does not exactly match current Python/catalog files"
            )
        if environment == "core" and any(data["optional"].values()):
            raise ValueError("Core environment unexpectedly contains optional dependencies")
        installed[environment] = data | dict(source_matches=True)
    runtime_lint = json.loads((ARTIFACTS / "prepublish-runtime-lint.log").read_text(encoding="utf8"))
    style = json.loads((ARTIFACTS / "prepublish-lint-final.log").read_text(encoding="utf8"))
    archive = json.loads((ROOT / "validation/prepublish_artifact_audit.json").read_text(encoding="utf8"))
    source = json.loads((ROOT / "validation/public_source_boundary_audit.json").read_text(encoding="utf8"))
    rights = json.loads((ROOT / "validation/release_rights_metadata_audit.json").read_text(encoding="utf8"))
    schemas = json.loads((ARTIFACTS / "validation/registry_schema_coverage.json").read_text(encoding="utf8"))
    from matintegrity.registry import default_registry

    examples = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf8"))["models"]
    result = dict(
        scope="Local prepublication inspection, no GitHub upload and no legal/scientific certification.",
        installation=installed,
        source_tree_sha256=hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest(),
        registry_models=schemas["registered_models"],
        schemas_covered=schemas["covered_models"],
        source_boundary=source,
        archive_and_secret_scan=archive,
        rights_metadata_status=rights["status"],
        runtime_static_errors=len(runtime_lint),
        remaining_full_lint_findings=len(style),
        targeted_tests=xml_counts(ARTIFACTS / "prepublish-checks.xml"),
        installed_numerical_tests=xml_counts(ARTIFACTS / "prepublish-installed-tests.xml"),
        main_example_executions=xml_counts(ARTIFACTS / "prepublish-model-examples.xml"),
        outstanding_main_example_membership=dict(
            main_file_examples=len(examples),
            registered=len(default_registry().list_models()),
            missing_from_main_file=len(set(default_registry().list_models()) - set(examples)),
        ),
        remaining_gates=[
            "Full Ruff style/lint and formatting policy",
            "Main example file completeness test (400 of 757 API IDs)",
            "Two normal full-run cases still require external measurement/rights evidence",
        ],
        github_uploaded=False,
    )
    (ROOT / "validation/prepublish_checks.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    lines = [
        "# GitHub 공개 전 추가 점검",
        "",
        "이번 점검은 로컬 검사·문제 수정이며 GitHub 게시를 수행하지 않았다. 모든 CI 기준을 통과했다거나 법적·물리적 인증을 받았다는 뜻이 아니다.",
        "",
        "| 검사 | 결과 |",
        "|---|---|",
        f"| 등록 API 입력 스키마 | {schemas['covered_models']}/{schemas['registered_models']} 일치 |",
        f"| 배포 후보 파일 경계·고신뢰 비밀정보 패턴 | {archive['status']}, {archive['public_files_scanned']}개 파일 |",
        "| 실제 wheel·소스 배포본 | 제한 원자료·로컬 로그 제외; 테스트 JSON 포함 확인 |",
        "| 기본/선택 의존성 설치본 | 원본 Python·카탈로그 파일과 해시 일치 |",
        "| 기본 설치 | SciPy·CoolProp·pandas·rainflow 없이 API 등록 및 기본 계산 확인 |",
        f"| 추가 분기·배포 경계 시험 | {result['targeted_tests']['cases']}개, 실패 {result['targeted_tests']['failed']}개 |",
        f"| 주 예제 실행 | {result['main_example_executions']['cases']}개, 실패 {result['main_example_executions']['failed']}개 |",
        f"| 실제 설치 wheel의 작업 폴더 밖 수치 검사 | {result['installed_numerical_tests']['cases']}개, 실패 {result['installed_numerical_tests']['failed']}개 |",
        f"| 실행을 막는 선택 정적 오류 | {len(runtime_lint)}건 |",
        f"| 전체 Ruff 지적 | {len(style)}건 남음 |",
        "",
        "## 수정한 문제",
        "",
        "- 기본 API 등록이 SciPy를 먼저 요구하던 보정 모듈을 지연 import로 바꿨다. 해당 보정 기능에 SciPy가 없으면 needs_data로 남긴다.",
        "- 틈 부식 형상 피드백의 콜백 인자 누락, 동적 수리 RHS의 외부 누적 변수 선언 누락을 수정했다.",
        "- 활동도 온도 슬라이스의 잘못된 변수 참조, 스케일 반응 내부의 성분 인덱스 누락을 수정했다.",
        "- 응축막 두께 계산에서 밀도를 사용한 뒤 할당하던 순서를 고쳤다. 구간별 밀도가 다를 때도 해당 구간 밀도를 사용한다.",
        "- 로컬 계산 로그를 소스 아카이브·공개 파일 선택·Git 제외 목록에서 제외했다. 파일은 로컬에 보존했다.",
        "- JSON 이스케이프 경로를 해석하지 못하던 검사에 디코딩 검사를 추가했다. NDJSON과 의도적인 파서 오류 fixture는 구분한다.",
        "- 소스 배포본에 tests/data JSON·JSONL과 공개 프로파일이 빠지던 포함 규칙을 보완했다.",
        "",
        "## 공개 전에 남는 기준",
        "",
        "전체 Ruff·서식 정책과 단일 주 예제 파일 완전성 검사는 여전히 자동 CI 통과를 막는다. 이를 숨기려고 검사나 기대조건을 삭제하지 않았다. 357개는 주 예제 파일에 없는 API 수이며 코드 미구현 수나 미시험 수가 아니다.",
        "개별 계산 230/232의 나머지 두 건은 실측 초기 두께 근거와 관측자료 사용권한이 필요하다. 그 근거를 만들거나 보류를 성공으로 바꾸지 않았다.",
        "비밀정보 검사는 개인키·GitHub 토큰·AWS 키의 고신뢰 패턴과 경로·파일 경계 검사이며 모든 비밀정보나 모든 보안 취약점의 부재를 보장하지 않는다. 데이터 권리 검사는 메타데이터 구조 확인이며 법률 판단이 아니다.",
        "",
        "## 재현",
        "",
        "```powershell",
        "python scripts/audit_public_source_boundary.py",
        "python scripts/audit_schema_coverage.py",
        "python scripts/audit_release_rights.py",
        "python -m build --no-isolation --outdir artifacts/prepublish-dist",
        "python scripts/audit_prepublish_artifacts.py",
        "# 기본/전체 환경에 위 wheel 설치 후 다음 집계를 실행",
        "python scripts/report_prepublish_checks.py",
        "```",
        "",
        "공개 영수증: validation/prepublish_checks.json 및 validation/prepublish_artifact_audit.json. 로컬 로그: artifacts/prepublish-*.log. 검사한 배포 후보는 artifacts/prepublish-dist/에 유지한다.",
        "이 폴더에는 아직 Git 저장소가 없다. 상위 연구 폴더 전체를 한꺼번에 공개 대상으로 선택하지 말고, 프로젝트 배포 경계와 제외 규칙을 유지해야 한다.",
    ]
    (ROOT / "docs/PREPUBLISH_CHECKS_KO.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print(
        json.dumps(
            dict(
                targeted_tests=result["targeted_tests"],
                examples=result["main_example_executions"],
                runtime_static_errors=len(runtime_lint),
                lint_findings=len(style),
                installation=installed,
            ),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

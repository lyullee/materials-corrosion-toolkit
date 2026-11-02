"""Publish aggregate receipts without local paths or third-party observation rows."""

import hashlib
import json
import platform
import xml.etree.ElementTree as ET
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts/validation"
REASONS = {
    "corrosion.piecewise_linear_rate_thickness_history": "실측 초기 두께와 측정 근거 필요; 임의 값을 실측으로 표시하지 않음",
    "data.mendeley_atmospheric_corrosion_typed_rows": "기초 관측자료 사용권한 확인 필요; 편집 데이터 라이선스와 구분",
}


def receipt(path):
    if not path.exists():
        return None
    nodes = list(ET.parse(path).iter("testcase"))
    return dict(
        cases=len(nodes),
        failed=sum(any(n.find(t) is not None for t in ("failure", "error")) for n in nodes),
        skipped=sum(n.find("skipped") is not None for n in nodes),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def main():
    source = ARTIFACTS / "full_core_calculations/summary.json"
    summary = json.loads(source.read_text(encoding="utf8"))
    groups = json.loads((ROOT / "tests/data/core_physics_full_run_targets.json").read_text(encoding="utf8"))[
        "groups"
    ]
    records = {r["model_id"]: r for r in summary["records"]}
    assert set(records) == {m for g in groups for m in g["model_ids"]}
    clean = [
        dict(
            model_id=m,
            status=r["status"],
            reason=REASONS.get(m),
            attempt_statuses=[a["status"] for a in r["attempts"]],
        )
        for m, r in sorted(records.items())
    ]
    receipts = {
        name: receipt(ARTIFACTS / relative)
        for name, relative in {
            "formula": "formula_63/results.xml",
            "extreme": "three_stage_review/extreme.xml",
            "physical_connections": "three_stage_review/connection.xml",
            "rule_handoff": "three_stage_review/rule_handoff.xml",
            "regression_selected": "three_stage_review/regression.xml",
            "repairs": "full_core_calculations/repairs.xml",
            "external_prerequisites": "full_core_calculations/prerequisites.xml",
            "analytic_examples": "full_core_calculations/examples.xml",
            "full_suite": "full_core_calculations/full_suite.xml",
            "review_gates_after_repairs": "full_core_calculations/review_gates.xml",
            "examples_catalog_sensitivity_after_repairs": "full_core_calculations/post_full_fixes.xml",
        }.items()
    }
    payload = dict(
        scope="63 fixed groups; 232 explicitly enumerated model IDs. Representative mathematical checks are not all-branch experimental validation.",
        computed=summary["computed"],
        target=summary["target_models"],
        records=clean,
        receipts=receipts,
        environment=dict(
            python=platform.python_version(),
            **{p: version(p) for p in ("numpy", "scipy", "pydantic", "CoolProp", "pytest")},
        ),
    )
    # Replace complete test files with their later receipts. Do not sum reruns
    # or disguise the first full suite as a fresh all-green run.
    latest = {}
    for relative in [
        "full_suite.xml",
        "review_gates.xml",
        "post_full_fixes.xml",
        "prerequisites.xml",
        "examples.xml",
    ]:
        path = ARTIFACTS / "full_core_calculations" / relative
        if not path.exists():
            continue
        cases = list(ET.parse(path).iter("testcase"))
        classes = {c.get("classname") for c in cases}
        latest = {key: value for key, value in latest.items() if key[0] not in classes}
        latest.update({(c.get("classname"), c.get("name")): c for c in cases})
    payload["reconciled_latest_by_test_file"] = dict(
        cases=len(latest),
        passed=sum(
            not any(c.find(t) is not None for t in ("failure", "error", "skipped")) for c in latest.values()
        ),
        failed=[
            f"{key[0]}::{key[1]}"
            for key, c in latest.items()
            if any(c.find(t) is not None for t in ("failure", "error"))
        ],
        skipped=[
            dict(test=f"{key[0]}::{key[1]}", reason=c.find("skipped").get("message"))
            for key, c in latest.items()
            if c.find("skipped") is not None
        ],
    )
    main_examples = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf8"))["models"]
    from matintegrity.registry import default_registry

    payload["main_example_file_coverage"] = dict(
        included=len(main_examples),
        registered=len(default_registry().list_models()),
        absent_from_main_file=sorted(set(default_registry().list_models()) - set(main_examples)),
        meaning="Only membership in examples/model_inputs.json; absence does not mean absent calculation code or absent other test fixtures.",
    )
    target = ROOT / "validation/core_execution_receipt.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    lines = [
        "# 개별 계산 실행 및 누락 검사 결과",
        "",
        f"개별 공개 JSON API 계산 완료: **{summary['computed']}/{summary['target_models']}개**.",
        "",
        "63개 계산군은 기능 묶음이며, 그 안에서 이번 감사 대상으로 명시한 고유 API가 232개다. 이전 116개는 입력 계약 감사 대상 집합이다. 757개 전체 등록 API와 혼동하지 않는다.",
        "",
        "검사 사례는 자체 작성 수학 문제를 우선 사용한다. Sines 수명 피팅은 Hannover 공개 시험의 실제 파단 수명과 별도로 재구성한 공칭 단축 응력을 사용했다. 다축 실험 검증이나 재료 허용치 검증은 아니다.",
        "Hannover 자료: Christian Dänekas, DOI [10.25835/0dojws6u](https://doi.org/10.25835/0dojws6u), CC BY 4.0. 원자료·관측행·로컬 경로는 공개 영수증에 포함하지 않는다.",
        "",
        "## 완료하지 않은 외부 근거",
        "",
    ]
    lines += [f"- `{m}`: {reason}." for m, reason in REASONS.items()]
    lines += [
        "",
        "위 두 항목은 정상 계산 완료 수에 포함하지 않았다. 근거 누락·권한 미승인 거부 시험은 별도로 수행했다. 거부 시험의 통과가 정상 계산 실행을 대신하지 않는다.",
        "",
        "## 실행 영수증",
        "",
        "| 검사 | 실행 사례 | 실패 | 건너뜀 |",
        "|---|---:|---:|---:|",
    ]
    for name, r in receipts.items():
        if r:
            lines.append(f"| {name} | {r['cases']} | {r['failed']} | {r['skipped']} |")
    latest_summary = payload["reconciled_latest_by_test_file"]
    lines += [
        "",
        f"전수 실행 후 수정한 파일의 재실행 영수증을 대체 대조한 결과: {latest_summary['cases']}개 중 {latest_summary['passed']}개 통과, {len(latest_summary['failed'])}개 실패, {len(latest_summary['skipped'])}개 건너뜀. 전체를 수정 후 새로 실행한 결과와는 구분한다.",
        "주 예제 JSON에는 400개 API가 들어 있고 전체 등록 API는 757개여서, 단일 파일이 전체 API를 포함해야 한다는 기존 검사 1개가 남는다. 이 검사나 기대조건을 삭제하지 않았다. 누락 357개는 그 파일에 없는 API 수이며, 계산 코드 미구현 수나 미시험 모델 수가 아니다. 별도 계산·입력 fixture의 실행 근거는 이 문서의 232개 목록과 영수증으로 판단한다.",
        "전수 실행의 건너뜀 3개는 옛 116개 입력 감사 범위 밖의 보조 baseline이다. 해당 B-dot·Davies·SIT 모델은 이번 232개 전수 공개 API 실행에서 별도로 계산 완료했다.",
    ]
    lines += [
        "",
        "동일 시험이 여러 묶음에 포함될 수 있으므로 사례 수를 합산하지 않는다. 대표 계산식·극단값·선택 회귀는 63개 군별 확인이다. 물리 계산 간 연결 확인 15/63과 결과→규칙 소비 모듈 연결 63/63을 구분한다.",
        "",
        "## 개별 API 실행 목록",
        "",
        "| 계산군 | 모델 ID | 정상 계산 | 비고 |",
        "|---|---|---|---|",
    ]
    for group in groups:
        for model in group["model_ids"]:
            row = records[model]
            lines.append(
                f"| {group['group']}. {group['name']} | `{model}` | {'완료' if row['status'] == 'computed' else '보류'} | {REASONS.get(model, '')} |"
            )
    lines += [
        "",
        "## 재현",
        "",
        "프로젝트 루트에서 다음 순서로 실행한다. 과학·열역학 선택 의존성이 필요하다.",
        "",
        "```powershell",
        "python scripts/prepare_core_full_run_inputs.py",
        "# 아래 단계는 별도 취득한 해시 고정 Hannover 자료가 로컬에 있을 때만 실행",
        "python scripts/prepare_hannover_sines_execution.py",
        "python scripts/run_core_physics_full_calculations.py",
        "python scripts/summarize_three_stage_review.py --run",
        "python -m pytest -q",
        "python scripts/report_core_execution.py",
        "```",
        "",
        "전체 계산 스크립트는 232개 전부 계산되지 않으면 종료 코드 1을 반환한다. `--pending`은 재개용이며 최종 전수 실행에는 사용하지 않았다.",
        "공개 요약은 `validation/core_execution_receipt.json`, 로컬 상세 입력·결과·실행 XML은 제외 폴더 `artifacts/validation/`에 있다.",
        "실행 성공은 수식 타당성·현장 적합성·모든 분기·모든 물리 결합·실험 검증 완료를 뜻하지 않는다.",
    ]
    (ROOT / "docs/CORE_EXECUTION_VERIFICATION_KO.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print(f"Public receipt: {summary['computed']}/{summary['target_models']}; no observation rows exported")


if __name__ == "__main__":
    main()

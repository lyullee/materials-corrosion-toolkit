"""Reconcile actual pytest receipts with the 63-group review manifests."""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/validation/three_stage_review"


def main():
    manifest = json.loads(
        (ROOT / "tests/data/core_physics_three_stage_cases.json").read_text(encoding="utf8")
    )["stages"]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    execution_failed = False
    if "--run" in sys.argv:

        def run(stage):
            nodes = list(dict.fromkeys(node for row in manifest[stage] for node in row["nodes"]))
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", *nodes, "--junitxml=" + str(OUTPUT / f"{stage}.xml")],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf8",
                errors="replace",
            )
            (OUTPUT / f"{stage}.log").write_text(completed.stdout + completed.stderr, encoding="utf8")
            return stage, completed.returncode, completed.stdout[-2000:]

        with ThreadPoolExecutor(max_workers=4) as pool:
            for future in as_completed([pool.submit(run, stage) for stage in manifest]):
                stage, code, tail = future.result()
                print(stage, "exit", code, tail, flush=True)
                execution_failed = execution_failed or code != 0
    stages = {}
    for stage in manifest:
        rows = manifest[stage]
        cases = list(ET.parse(OUTPUT / f"{stage}.xml").iter("testcase"))
        for row in rows:
            findings = []
            for node in row["nodes"]:
                path, name = node.split("::")
                classname = path.removesuffix(".py").replace("/", ".")
                matched = [
                    c
                    for c in cases
                    if c.get("classname") == classname
                    and (c.get("name") == name or c.get("name", "").startswith(name + "["))
                ]
                status = (
                    "passed"
                    if matched
                    and all(
                        not any(c.find(tag) is not None for tag in ("failure", "error", "skipped"))
                        for c in matched
                    )
                    else "unresolved"
                )
                # A parameter profile applied to one model does not demonstrate
                # one calculation result feeding another calculation.
                if stage == "connection" and row["group"] == 40:
                    status = "insufficient_connection_evidence"
                findings.append({"node": node, "status": status, "executed_cases": len(matched)})
            row["results"] = findings
            row["status"] = (
                "passed" if findings and all(f["status"] == "passed" for f in findings) else "unconfirmed"
            )
        stages[stage] = {
            "passed_groups": sum(r["status"] == "passed" for r in rows),
            "executed_cases": len(cases),
            "failed_cases": sum(any(c.find(t) is not None for t in ("failure", "error")) for c in cases),
            "skipped_cases": sum(c.find("skipped") is not None for c in cases),
            "groups": rows,
        }
    (OUTPUT / "coverage.json").write_text(
        json.dumps(stages, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    lines = [
        "# 극단값·연결·기존 기능 재확인",
        "",
        "대상은 기존 63개 계산군이다. 실제 실행 XML과 명시한 시험 목록을 대조했다.",
        "통과는 군별 대표 시험의 통과이며 모든 하위 모델과 분기를 포괄하지 않는다.",
        "미확인은 실행 근거 부족을 뜻한다. 통과한 시험 수를 계산군 수로 환산하지 않는다.",
        "",
        "| 항목 | 대표 시험 통과 계산군 | 실행 시험 | 실패 | 건너뜀 |",
        "|---|---:|---:|---:|---:|",
    ]
    for stage, label in [
        ("extreme", "극단값"),
        ("connection", "물리 계산 간 연결"),
        ("rule_handoff", "계산 결과→규칙 소비 모듈"),
        ("regression", "기존 기능 재확인"),
    ]:
        s = stages[stage]
        lines.append(
            f"| {label} | {s['passed_groups']}/63 | {s['executed_cases']} | {s['failed_cases']} | {s['skipped_cases']} |"
        )
    lines += [
        "",
        "회귀시험은 이전 계산식 기준값 시험도 포함한다. 이는 선택한 기존 동작의 재실행이며 저장소 전체 시험 통과를 뜻하지 않는다.",
        "연결 시험의 parameter profile 단독 실행은 두 계산 간 결과 전달이 아니므로 연결 완료 수에서 제외했다.",
        "",
        "| 번호 | 계산군 | 극단값 | 물리 계산 간 연결 | 기존 기능 재확인 | 규칙 소비 모듈 연결 |",
        "|---|---|---|---|---|---|",
    ]
    for index in range(63):
        row = stages["regression"]["groups"][index]
        values = ["확인" if stages[s]["groups"][index]["status"] == "passed" else "미확인" for s in stages]
        lines.append(f"| {row['group']} | {row['name']} | {' | '.join(values)} |")
    lines += [
        "",
        "세부 시험 경로와 실행 결과: `artifacts/validation/three_stage_review/coverage.json`.",
        "원 실행 영수증: 같은 폴더의 `extreme.xml`, `connection.xml`, `regression.xml`.",
        "재실행과 집계: `.venv\\Scripts\\python.exe -X utf8 scripts/summarize_three_stage_review.py --run`.",
        "집계만 재생성하려면 `--run`을 생략한다.",
    ]
    (ROOT / "docs/THREE_STAGE_VERIFICATION_KO.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    for stage, s in stages.items():
        print(
            stage,
            f"{s['passed_groups']}/63 groups",
            f"{s['executed_cases']} tests",
            f"{s['failed_cases']} failed",
        )
    return (
        1 if execution_failed or any(s["failed_cases"] or s["skipped_cases"] for s in stages.values()) else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())

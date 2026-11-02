"""Regenerate the implementation backlog from its machine-readable audit."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data/catalogs/implementation_scope_audit.json"
OUTPUT = ROOT / "docs/IMPLEMENTATION_BACKLOG_KO.md"


def main():
    rows = json.loads(AUDIT.read_text(encoding="utf-8"))["items"]
    classifications = ("provider_dependent", "data_validation_pending", "code_incomplete")
    counts = {key: sum(row["classification"] == key for row in rows) for key in classifications}
    source_audit = [entry for row in rows for entry in row.get("source_path_audit", [])]
    source_present = sum(entry.get("presence") == "present" for entry in source_audit)
    source_missing = sum(entry.get("presence") != "present" for entry in source_audit)
    mapped_rows = sum(bool(row.get("source_paths")) for row in rows)
    components = [component for row in rows for component in row.get("component_catalog_audit", [])]
    unmapped_components = sum(component.get("catalog_status") == "unmapped" for component in components)
    parsed_files = sum(
        entry.get("ast_status") == "parsed" for row in rows for entry in row.get("source_path_audit", [])
    )
    explicit_symbols = [item for row in rows for item in row.get("code_symbol_evidence_audit", [])]
    missing_explicit_symbols = sum(item.get("status") != "present" for item in explicit_symbols)
    trace = json.loads(AUDIT.read_text(encoding="utf-8")).get("trace_coverage", {})
    trace_rows = trace.get("rows_with_complete_path_trace", mapped_rows)
    total_rows = trace.get("scope_rows", len(rows))
    trace_percent = 100.0 * trace_rows / total_rows if total_rows else 100.0
    lines = [
        "# 101개 확장 범위 구현 추적",
        "",
        f"이 카탈로그는 최초 scope 감사의 항목별 판단을 보존한다. 최초 13개 `code_incomplete` 중 현재 {counts['code_incomplete']}개 capability가 코드 범위 미완성으로 남았다. bounded child 계산 코드가 추가되어도 parent 도메인 완료나 수치 검증으로 간주하지 않는다. `implementation_complete`는 제한된 코드 경로의 상태이며 전체 기술 구현이나 qualification을 뜻하지 않는다.",
        "",
        "현재 분류: " + ", ".join(f"{key} {counts[key]}개" for key in classifications) + ".",
        "",
        f"코드 범위 추적성: {trace_rows}/{total_rows}행 ({trace_percent:.1f}%)이 소스·근거 경로, 실제 파일, AST 파싱까지 연결됐다. 이는 코드 구현 완료율이 아니다. 별도 구현 상태에서는 `code_incomplete` capability {counts['code_incomplete']}개가 남아 있다.",
        "",
        f"최신 경로 감사: 101개 행 중 {mapped_rows}개에 소스 경로가 연결되어 있다. 총 {source_present}개 파일 경로가 현재 존재하고 {source_missing}개는 누락됐다. 파일 존재·SHA-256은 경로의 현행성만 기록하며 계산 구현의 완전성이나 정확성 증거가 아니다. 상세값은 `data/catalogs/implementation_scope_audit.json`의 `source_path_audit`에 있다.",
        "",
        f"카탈로그 연결 감사: {len(components)}개 구현 구성요소를 capability 자체 또는 다른 capability의 명시적 구성요소로 확인했으며, 현재 미연결 구성요소는 {unmapped_components}개다. 연결 상태는 구현 완전성을 뜻하지 않는다.",
        "",
        f"AST 구조 감사: {parsed_files}개 경로를 파싱했고, 기존의 명시 심볼 근거 {len(explicit_symbols)}개 중 현재 선언이 없는 심볼은 {missing_explicit_symbols}개다. 선언 위치 확인도 함수의 capability 동작 연결이나 실행 검증을 뜻하지 않는다.",
        "",
        "`current_code_evidence`의 심볼·해시 추적이 없는 행은 ‘소스 경로 자체가 없음’과 다르다. 현재 심볼 수준 추적은 최초 코드 미완성 13개에만 있다. 나머지 88개도 코드 존재를 경로 수준으로 확인했을 뿐이며, 전체 도메인 완성 상태로 승격하지 않는다.",
        "",
        "`provider_dependent`는 caller-owned provider/limits/qualification law가 필요한 경로다. `data_validation_pending`은 독립 자료, calibration applicability 또는 physical validation이 남았다는 뜻이다. 두 범주 모두 해당 field domain의 완전한 simulator를 뜻하지 않는다.",
        "",
        "이 101개 항목은 분야별 규모와 완료 기준이 서로 달라 하나의 합산 구현률로 환산하지 않는다. 항목별 분류·잔여 범위와 실행 검증 상태를 함께 읽는다.",
        "",
        "",
        "## 항목별 최초 분류와 근거",
        "",
        "| 항목 | 최초 분류 | 최신 판단과 범위 경계 | 코드 위치 |",
        "|---|---|---|---|",
    ]
    for row in rows:
        paths = ", ".join(f"`{path}`" for path in row.get("source_paths", [])) or "미매핑"
        assessment = (
            row.get("current_remaining_scope")
            if row["classification"] == "code_incomplete"
            else row.get("assessment_basis", "")
        )
        lines.append(f"| `{row['capability_id']}` | {row['classification']} | {assessment} | {paths} |")
    lines.extend(
        [
            "",
            f"## 최초 코드 미완성 13개 중 현재 부분 범위 항목 {counts['code_incomplete']}개의 추적",
            "",
            "아래 실행 검증은 미실행이다. 위치와 hash는 `current_code_evidence`에 기록한다.",
            "",
            "| 항목 | 최신 bounded 코드 | 코드 위치 | 남은 기술 범위 |",
            "|---|---|---|---|",
        ]
    )
    for row in rows:
        if row["classification"] != "code_incomplete":
            continue
        locations = "; ".join(
            f"`{entry['path']}:{entry['line']}`" for entry in row.get("current_code_evidence", [])
        )
        lines.append(
            f"| `{row['capability_id']}` | {row.get('bounded_calculation_code_state', '미표시')} | {locations} | {row.get('current_remaining_scope', '재검토 필요')} |"
        )
    lines.extend(
        [
            "",
            "테스트·수치 계산·HPC 실행·패키징은 이 구현 추적에 포함하지 않았다. 101개 capability는 프로젝트 전체 기술 목표의 부분 범위다.",
            "",
        ]
    )
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

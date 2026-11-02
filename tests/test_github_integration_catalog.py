import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_github_integration_catalog_is_pinned_and_requests_exist():
    payload = json.loads((ROOT / "data/catalogs/github_integrations.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "matintegrity.github_integrations.v1"
    assert {row["repository"] for row in payload["repositories"]} == {
        "api581-risk-analysis",
        "process-risk-consequence-toolkit",
    }
    for row in payload["repositories"]:
        assert len(row["reviewed_commit"]) == 40
        assert row["reviewed_schema_sha256"]
        assert all(len(value) == 64 for value in row["reviewed_schema_sha256"].values())
        assert (ROOT / row["request_document"]).is_file()
        assert row["end_to_end_status"] == "not_run"
        assert row["qualification_status"] == "not_claimed"


def test_catalog_audit_runs_offline():
    result = subprocess.run(
        [sys.executable, "scripts/inspect_github_integration_catalog.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary == {
        "repositories": 2,
        "request_documents_present": 2,
        "end_to_end_runs": 0,
        "consumer_executions": 2,
        "numeric_pof_provider_executions": 1,
        "engineering_qualifications": 0,
    }


def test_extension_request_index_covers_all_request_documents():
    docs = ROOT / "docs/extension_requests"
    index = (docs / "README_KO.md").read_text(encoding="utf-8")
    listed = set(__import__("re").findall(r"`([A-Z0-9_]+_KO\.md)`", index))
    actual = {path.name for path in docs.glob("*.md") if path.name != "README_KO.md"}
    assert listed == actual

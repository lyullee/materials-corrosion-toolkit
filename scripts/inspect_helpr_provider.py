"""Audit a locally excluded checkout of the official HELPR provider repository."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tomllib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKOUT = ROOT / "data/evidence/helpr/repo"
EXPECTED_REVISION = "ae12d20b6608123af41dd9d5f70db6b6547fece5"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(CHECKOUT), *arguments], text=True, encoding="utf-8"
    ).strip()


def main():
    revision = git("rev-parse", "HEAD")
    if revision != EXPECTED_REVISION:
        raise ValueError("HELPR checkout is not the reviewed v2.1.0 revision")
    if git("status", "--short"):
        raise ValueError("HELPR evidence checkout has local modifications")
    metadata = tomllib.loads((CHECKOUT / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    if project["name"] != "helpr" or project["version"] != "2.1.0":
        raise ValueError("unexpected HELPR package identity")
    license_text = (CHECKOUT / "LICENSE.md").read_text(encoding="utf-8")
    if not license_text.startswith("BSD 3-Clause License"):
        raise ValueError("reviewed HELPR license declaration changed")
    reviewed = {
        relative: sha256(CHECKOUT / relative)
        for relative in (
            "LICENSE.md",
            "COPYRIGHT.txt",
            "pyproject.toml",
            "README.md",
            "CHANGELOG.md",
            "src/helpr/api.py",
            "src/helpr/utilities/saving.py",
            "src/helpr/utilities/postprocessing.py",
        )
    }
    record = {
        "schema_version": "matintegrity.external_provider_review.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "provider_id": "sandia.helpr",
        "provider_name": "Hydrogen Extremely Low Probability of Rupture",
        "provider_version": project["version"],
        "provider_revision": revision,
        "provider_tag": git("describe", "--tags", "--exact-match", "HEAD"),
        "repository": "https://github.com/sandialabs/helpr",
        "documentation": "https://sandialabs.github.io/helpr/",
        "license": "BSD-3-Clause",
        "runtime_dependency_added": False,
        "upstream_code_copied": False,
        "reviewed_file_sha256": reviewed,
        "reviewed_output": {
            "method": "CrackEvolutionAnalysis.save_results",
            "life_criteria_files": [
                "nominal_life_criteria.csv",
                "probabilistic_life_criteria.csv",
            ],
            "columns": [
                "a(crit)",
                "Cycles to a(crit)",
                "Cycles to 25% a(crit)",
                "Cycles to 1/2 Nc",
                "Cycles to FAD line",
            ],
            "limitations": [
                "CSV does not carry provider revision or configuration digest.",
                "CSV does not carry asset, location, material, load-case, or physical sample identity.",
                "Blank and NaN criteria require provider-run interpretation and are not observed runouts.",
                "Life criteria are not failure probabilities or independent experimental validation.",
            ],
        },
        "integration_decision": (
            "Use an optional version-pinned CSV boundary and restore required provenance in an independent "
            "MatIntegrity contract. Do not copy HELPR physics, API 579 tables, or design curves."
        ),
    }
    target = ROOT / "validation/helpr_provider_review.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()

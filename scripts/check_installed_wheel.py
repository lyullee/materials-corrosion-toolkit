"""Recheck a built wheel in isolated core and science environments, not an editable checkout."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "artifacts/install-verification"


def run(python: Path, arguments: list[str], label: str):
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [str(python), *arguments],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    (LOGS / f"{label}.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{label} failed; inspect artifacts/install-verification/{label}.txt")
    return result.stdout


def tree(root: Path):
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file() and p.suffix in {".py", ".json"} and "__pycache__" not in p.parts
    }


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    wheels = list((ROOT / "dist").glob("*.whl"))
    if len(wheels) != 1:
        raise ValueError("build exactly one reviewed wheel before running the installation check")
    wheel = wheels[0]
    interpreters = {}
    for label in ("core", "full"):
        folder = ROOT / f"artifacts/{label}_environment"
        python = folder / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if not python.exists():
            run(Path(sys.executable), ["-m", "venv", str(folder)], f"create-{label}")
        run(
            python,
            [
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--force-reinstall",
                "--no-deps",
                str(wheel),
            ],
            f"wheel-{label}",
        )
        requirement = str(wheel) + ("[science,thermo,dev]" if label == "full" else "")
        run(
            python,
            ["-m", "pip", "install", "--disable-pip-version-check", requirement],
            f"dependencies-{label}",
        )
        run(python, ["-m", "pip", "check"], f"dependency-check-{label}")
        interpreters[label] = python
    run(interpreters["core"], ["scripts/smoke_core.py"], "core-smoke")
    run(
        interpreters["full"],
        ["-m", "pytest", "-q", "--junitxml=validation/clean_full_tests.xml"],
        "full-tests",
    )
    xml = ET.parse(ROOT / "validation/clean_full_tests.xml")
    suites = list(xml.getroot().iter("testsuite"))
    for suite in suites:
        suite.attrib.pop("hostname", None)
    xml.write(ROOT / "validation/clean_full_tests.xml", encoding="utf-8", xml_declaration=True)
    probe = """
import hashlib,importlib.metadata,json,platform,sys
from pathlib import Path
import matintegrity
from matintegrity.registry import default_registry
root=Path(matintegrity.__file__).resolve().parent
assert root.is_relative_to(Path(sys.prefix).resolve()), "package did not import from the selected environment"
tree={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file() and p.suffix in {".py",".json"} and "__pycache__" not in p.parts}
versions={d.metadata["Name"]:d.version for d in sorted(importlib.metadata.distributions(),key=lambda d:d.metadata["Name"].lower())}
print(json.dumps(dict(python=platform.python_version(),platform=platform.system(),models=len(default_registry().list_models()),all_installed_versions=versions,installed_tree=tree)))
"""
    evidence = json.loads(run(interpreters["full"], ["-c", probe], "installed-source-probe"))
    installed = evidence.pop("installed_tree")
    if installed != tree(ROOT / "src/matintegrity"):
        raise ValueError("installed package code/catalogs do not match the current source")
    evidence.update(
        status="passed",
        checked_at_utc=datetime.now(timezone.utc).isoformat(),
        installation="independent non-editable wheel with optional dependencies",
        installed_source_matches_working_src=True,
        source_tree_sha256=hashlib.sha256(
            json.dumps(installed, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        tests=sum(int(s.get("tests", "0")) for s in suites),
        failures=sum(int(s.get("failures", "0")) for s in suites),
        errors=sum(int(s.get("errors", "0")) for s in suites),
    )
    (ROOT / "validation/clean_full_install.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                key: evidence[key]
                for key in (
                    "status",
                    "models",
                    "tests",
                    "failures",
                    "errors",
                    "installed_source_matches_working_src",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

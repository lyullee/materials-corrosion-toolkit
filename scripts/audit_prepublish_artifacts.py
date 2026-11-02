"""Inspect public files and built archives; never print a suspected secret value."""

import argparse
import hashlib
import json
import re
import tarfile
import zipfile
from pathlib import Path

from build_release import ROOT, public_files

BLOCKED = {
    "raw",
    "derived",
    "evidence",
    "artifacts",
    "hpc-local",
    "hpc-results",
    "__pycache__",
    ".venv",
    ".git",
}
SUFFIXES = {".pdf", ".opju", ".h5", ".mat", ".xlsx", ".xlsm", ".pptx", ".pyc"}
PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b"),
    "aws_access_key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", default="artifacts/prepublish-dist")
    args = parser.parse_args()
    files = public_files()
    findings = []
    for path in files:
        text = path.read_text(encoding="utf8")
        for kind, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(dict(path=path.relative_to(ROOT).as_posix(), kind=kind))
    folder = (ROOT / args.dist).resolve()
    if not folder.is_relative_to(ROOT):
        raise ValueError("Distribution audit must remain inside this project")
    archives = list(folder.glob("*.whl")) + list(folder.glob("*.tar.gz"))
    if len(archives) != 2:
        raise ValueError("Exactly one freshly built wheel and source archive required")
    records = []
    for path in archives:
        if path.suffix == ".whl":
            with zipfile.ZipFile(path) as archive:
                names = [n for n in archive.namelist() if not n.endswith("/")]
        else:
            with tarfile.open(path) as archive:
                if any(m.issym() or m.islnk() for m in archive.getmembers()):
                    raise ValueError("Source archive contains an unreviewed link")
                names = [m.name for m in archive.getmembers() if m.isfile()]
            if not any(n.endswith("/tests/data/core_physics_full_run_targets.json") for n in names):
                raise ValueError("Source archive omitted required test JSON fixtures")
        forbidden = [
            n
            for n in names
            if BLOCKED.intersection(Path(n).parts)
            or Path(n).suffix.lower() in SUFFIXES
            or ".." in Path(n).parts
            or Path(n).is_absolute()
        ]
        if forbidden:
            raise ValueError(f"Private or restricted members in {path.name}: {forbidden[:3]}")
        records.append(
            dict(
                archive=path.name,
                files=len(names),
                bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                private_assets_absent=True,
            )
        )
    result = dict(
        status="passed" if not findings else "failed",
        public_files_scanned=len(files),
        secret_patterns=list(PATTERNS),
        suspected_secrets=findings,
        artifacts=records,
        meaning="High-confidence credential patterns and archive membership checks only; not exhaustive security or legal clearance.",
    )
    (ROOT / "validation/prepublish_artifact_audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    print(json.dumps(result, ensure_ascii=False))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

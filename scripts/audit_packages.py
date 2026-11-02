"""Inspect actual wheel, source archive and review ZIP inclusion boundaries."""

import hashlib
import json
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_PARTS = {
    ".venv",
    "raw",
    "derived",
    "evidence",
    "__pycache__",
    "core_environment",
    "hpc-local",
    "hpc-results",
    "artifacts",
}
BLOCKED_SUFFIXES = {".pdf", ".h5", ".mat", ".xlsx", ".xlsm", ".pptx", ".opju", ".pyc"}


def main():
    packages = [
        *sorted((ROOT / "dist").glob("*.whl")),
        *sorted((ROOT / "dist").glob("*.tar.gz")),
        ROOT / "dist/matintegrity-source-review.zip",
    ]
    if len(packages) != 3:
        raise ValueError(
            "expected one wheel, one source archive and one review archive; reconcile releases explicitly"
        )
    records = []
    checksums = []
    for path in packages:
        if path.name.endswith(".tar.gz"):
            with tarfile.open(path) as archive:
                names = [m.name for m in archive.getmembers() if m.isfile()]
        else:
            with zipfile.ZipFile(path) as archive:
                names = [n for n in archive.namelist() if not n.endswith("/")]
        for name in names:
            member = Path(name)
            if (
                member.is_absolute()
                or ".." in member.parts
                or BLOCKED_PARTS.intersection(member.parts)
                or member.suffix.lower() in BLOCKED_SUFFIXES
            ):
                raise ValueError(f"unexpected asset in {path.name}: {name}")
        if not any(n.endswith("catalog_data/datasets.json") for n in names):
            raise ValueError("packaged dataset metadata is missing")
        records.append(dict(artifact=path.name, files=len(names), restricted_asset_check="passed"))
        checksums.append(
            dict(
                artifact=path.name,
                bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    record = dict(
        checked_on_utc=datetime.now(timezone.utc).date().isoformat(),
        status="passed",
        artifacts=records,
        qualification="Archive path/inclusion check only; not scientific or legal qualification. Exact archive digests are in the external dist/checksums.json to avoid a self-referential source hash.",
    )
    (ROOT / "validation/package_audit.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    (ROOT / "dist/checksums.json").write_text(json.dumps(checksums, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()

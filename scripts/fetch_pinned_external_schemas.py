"""Fetch reviewed external JSON schemas into an excluded validation cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/catalogs/github_integrations.json"


def _raw_url(owner: str, repository: str, commit: str, path: str) -> str:
    clean = PurePosixPath(path)
    if clean.is_absolute() or ".." in clean.parts:
        raise ValueError("external schema path must be a relative POSIX path")
    return f"https://raw.githubusercontent.com/{owner}/{repository}/{commit}/{clean.as_posix()}"


def fetch_schema(
    *,
    url: str,
    expected_sha256: str,
    opener: Callable[..., object] = urllib.request.urlopen,
) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "matintegrity-schema-audit/1"})
    with opener(request, timeout=30) as response:
        raw = response.read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError(f"external schema SHA-256 mismatch: expected {expected_sha256}, got {digest}")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("external schema root must be a JSON object")
    return raw


def _atomic_write(target: Path, raw: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, target)
    finally:
        temporary = Path(temporary_name)
        if temporary.exists():
            temporary.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=ROOT / "artifacts/external-schemas",
        help="Excluded local cache; never point this at a package or release directory.",
    )
    args = parser.parse_args()
    cache_dir = args.cache_dir.resolve()
    if ROOT.resolve() not in cache_dir.parents or cache_dir == ROOT.resolve():
        raise ValueError("schema cache must be a dedicated directory inside the project")
    if "artifacts" not in cache_dir.parts:
        raise ValueError("schema cache must remain under the excluded artifacts directory")

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    fetched = []
    for repository in catalog["repositories"]:
        for path, expected_sha256 in repository["reviewed_schema_sha256"].items():
            url = _raw_url(
                repository["owner"],
                repository["repository"],
                repository["reviewed_commit"],
                path,
            )
            raw = fetch_schema(url=url, expected_sha256=expected_sha256)
            target = cache_dir / repository["repository"] / repository["reviewed_commit"] / path
            _atomic_write(target, raw)
            fetched.append(
                {
                    "repository": repository["repository"],
                    "commit": repository["reviewed_commit"],
                    "path": path,
                    "sha256": expected_sha256,
                    "bytes": len(raw),
                    "cache_path": target.relative_to(ROOT).as_posix(),
                }
            )
    print(json.dumps({"fetched": fetched}, ensure_ascii=False))


if __name__ == "__main__":
    main()

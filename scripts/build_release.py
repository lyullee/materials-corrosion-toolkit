"""Create an allowlisted review archive and fail on local/restricted asset leakage."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "pyproject.toml",
    "setup.py",
    "MANIFEST.in",
    ".gitignore",
    ".gitattributes",
    "CITATION.cff",
    ".zenodo.json",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
}
DIRECTORIES = {"src", "docs", "examples", "tests", "scripts", "validation", "hpc", ".github"}
PUBLIC_DATA_DIRECTORIES = {"data/profiles"}
DATA_FILES = {"data/acquisition_log.json", "data/data_inventory.json"}
PACKAGE_CATALOGS = {
    "capabilities": ("data/catalogs/capabilities.json", "src/matintegrity/catalog_data/capabilities.json"),
    "datasets": ("data/catalogs/datasets.json", "src/matintegrity/catalog_data/datasets.json"),
    "sources": ("data/catalogs/sources.json", "src/matintegrity/catalog_data/sources.json"),
    "ct110_weld_corrosion_rates": (
        "validation/ct110_weld_corrosion_rates.json",
        "src/matintegrity/catalog_data/ct110_weld_corrosion_rates.json",
    ),
}
FORBIDDEN_MARKERS = (
    "C:\\Users\\",
    "/Users/",
    "C:/Users/",
)


def validate_catalog_sync(root: Path = ROOT) -> None:
    """Reject release snapshots whose installed-package catalogs lag public sources."""
    for name, (source_relative, package_relative) in PACKAGE_CATALOGS.items():
        source = root / source_relative
        packaged = root / package_relative
        if not source.is_file() or not packaged.is_file():
            raise ValueError(f"missing {name} catalog; run scripts/sync_catalogs.py before release")
        if source.read_bytes() != packaged.read_bytes():
            raise ValueError(f"stale packaged {name} catalog; run scripts/sync_catalogs.py before release")


def _json_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from _json_strings(key)
            yield from _json_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _json_strings(child)


def public_files():
    validate_catalog_sync()
    files = []
    candidates = {ROOT / name for name in ROOT_FILES | DATA_FILES}
    for directory in DIRECTORIES | {"data/catalogs"} | PUBLIC_DATA_DIRECTORIES:
        folder = ROOT / directory
        if folder.is_dir():
            candidates.update(folder.rglob("*"))
    for path in candidates:
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(
            part in {".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "build", "dist"}
            or part.endswith(".egg-info")
            for part in relative.parts
        ):
            continue
        key = relative.as_posix()
        if key.startswith("validation/hpc-local/"):
            continue
        if not (
            key in ROOT_FILES
            or relative.parts[0] in DIRECTORIES
            or key in DATA_FILES
            or key.startswith("data/catalogs/")
            or key.startswith("data/profiles/")
        ):
            continue
        if relative.parts[0] == "validation" and path.suffix.lower() not in {".json", ".xml"}:
            continue
        if path.suffix.lower() in {
            ".pdf",
            ".h5",
            ".mat",
            ".xlsx",
            ".xlsm",
            ".jpg",
            ".png",
            ".opju",
            ".pptx",
            ".zip",
            ".pyc",
        }:
            raise ValueError(f"external/binary asset in public source selection: {key}")
        text = path.read_text(encoding="utf-8")
        if key == "data/acquisition_log.json":
            for record in json.loads(text)["attempts"]:
                for field in ("url", "resolved_url"):
                    if field not in record:
                        continue
                    url = urlsplit(record[field])
                    if url.query or url.fragment or "@" in url.netloc:
                        raise ValueError(
                            "acquisition URLs must omit query strings, fragments and credentials before public release"
                        )
        checked_texts = [text, text.replace("\\\\", "\\")]
        if path.suffix.lower() in {".json", ".jsonl"}:
            try:
                decoded = json.loads(text)
            except json.JSONDecodeError:
                try:
                    decoded = [json.loads(line) for line in text.splitlines() if line.strip()]
                except json.JSONDecodeError:
                    # Malformed parser fixtures are intentionally public tests.
                    if not key.startswith("tests/"):
                        raise ValueError(f"invalid public JSON outside parser tests: {key}") from None
                    decoded = None
                checked_texts.extend(_json_strings(decoded))
            else:
                checked_texts.extend(_json_strings(decoded))
        if path.name != "build_release.py" and any(
            marker in value for value in checked_texts for marker in FORBIDDEN_MARKERS
        ):
            raise ValueError(f"local research marker found in public source selection: {key}")
        files.append(path)
    manifest_path = ROOT / "validation/release_manifest.json"
    if manifest_path in files:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            records = manifest["files"]
            expected_paths = sorted(
                path.relative_to(ROOT).as_posix() for path in files if path != manifest_path
            )
            recorded_paths = sorted(record["path"] for record in records)
            valid = recorded_paths == expected_paths
            if valid:
                by_path = {record["path"]: record for record in records}
                for path in files:
                    if path == manifest_path:
                        continue
                    record = by_path[path.relative_to(ROOT).as_posix()]
                    valid = (
                        record.get("bytes") == path.stat().st_size
                        and record.get("sha256") == hashlib.sha256(path.read_bytes()).hexdigest()
                    )
                    if not valid:
                        break
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
            valid = False
        if not valid:
            files.remove(manifest_path)
    return sorted(files)


def main():
    version_dir = ROOT / "validation"
    version_dir.mkdir(exist_ok=True)
    packages = [
        "numpy",
        "pydantic",
        "pint",
        "scipy",
        "pandas",
        "rainflow",
        "h5py",
        "openpyxl",
        "xlrd",
        "xlwt",
        "CoolProp",
        "pytest",
        "ruff",
        "build",
    ]
    versions = {"python": platform.python_version(), "platform": platform.system(), "packages": {}}
    for name in packages:
        try:
            distribution = importlib.metadata.distribution(name)
            versions["packages"][name] = {
                "version": distribution.version,
                "license_expression": distribution.metadata.get("License-Expression")
                or distribution.metadata.get("License"),
            }
        except importlib.metadata.PackageNotFoundError:
            versions["packages"][name] = {"status": "not installed"}
    (version_dir / "environment.json").write_text(
        json.dumps(versions, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    files = public_files()
    manifest = [
        dict(
            path=p.relative_to(ROOT).as_posix(),
            bytes=p.stat().st_size,
            sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        )
        for p in files
        if p.name != "release_manifest.json"
    ]
    (version_dir / "release_manifest.json").write_text(
        json.dumps(dict(files=manifest), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    files = public_files()
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    target = dist / "matintegrity-source-review.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
    result = dict(
        files=len(files),
        archive=target.name,
        bytes=target.stat().st_size,
        sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        restricted_asset_check="passed",
        meaning="Source-content audit only; not a legal-rights or scientific qualification certificate.",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""Audit dataset metadata and verify locally acquired publisher assets."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/catalogs/datasets.json"
HEX_DIGEST = re.compile(r"^[0-9a-f]+$")


def digest(path: Path, algorithm: str) -> str:
    git_blob = algorithm == "git-blob-sha1"
    value = hashlib.new("sha1" if git_blob else algorithm)
    if git_blob:
        value.update(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def audit() -> dict:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if catalog.get("schema") != "matintegrity.datasets.v1":
        raise ValueError("unexpected dataset catalog schema")
    datasets = catalog.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        raise ValueError("dataset catalog must contain dataset records")
    ids: set[str] = set()
    asset_count = 0
    missing_publisher_checksums = 0
    local_verified = 0
    local_unverified = 0
    local_sha256_recorded = 0
    policies: Counter[str] = Counter()
    rights: Counter[str] = Counter()
    findings: list[dict] = []
    for record in datasets:
        dataset_id = record.get("id")
        if not isinstance(dataset_id, str) or not dataset_id or dataset_id in ids:
            raise ValueError(f"missing or duplicate dataset id: {dataset_id!r}")
        ids.add(dataset_id)
        for field in ("title", "license", "rights_status", "acquisition_policy"):
            if not record.get(field):
                raise ValueError(f"{dataset_id}: missing required {field}")
        if record["acquisition_policy"] not in {
            "allowed",
            "allowed_selected_assets",
            "allowed_selected_text_assets",
            "metadata_only",
            "do_not_download",
        }:
            raise ValueError(f"{dataset_id}: unknown acquisition policy")
        policies[record["acquisition_policy"]] += 1
        rights[record["rights_status"]] += 1
        filenames: set[str] = set()
        for asset in record.get("assets", []):
            asset_count += 1
            filename = asset.get("filename")
            if not isinstance(filename, str) or Path(filename).name != filename or filename in filenames:
                raise ValueError(f"{dataset_id}: invalid or duplicate asset filename")
            filenames.add(filename)
            parsed = urlsplit(asset.get("url", ""))
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError(f"{dataset_id}/{filename}: asset URL must use HTTPS")
            expected_size = asset.get("bytes")
            if expected_size is not None and (not isinstance(expected_size, int) or expected_size <= 0):
                raise ValueError(f"{dataset_id}/{filename}: invalid declared byte count")
            checksum = asset.get("checksum")
            if checksum:
                algorithm, separator, expected = checksum.partition(":")
                if not separator or (
                    algorithm not in hashlib.algorithms_available and algorithm != "git-blob-sha1"
                ):
                    raise ValueError(f"{dataset_id}/{filename}: unsupported checksum declaration")
                digest_algorithm = "sha1" if algorithm == "git-blob-sha1" else algorithm
                if (
                    not HEX_DIGEST.fullmatch(expected)
                    or len(expected) != hashlib.new(digest_algorithm).digest_size * 2
                ):
                    raise ValueError(f"{dataset_id}/{filename}: malformed checksum")
            else:
                missing_publisher_checksums += 1
                findings.append(
                    {
                        "dataset_id": dataset_id,
                        "filename": filename,
                        "finding": "publisher_checksum_unavailable",
                    }
                )
            local = ROOT / "data/raw" / dataset_id / filename
            if local.is_file():
                if expected_size is not None and local.stat().st_size != expected_size:
                    raise ValueError(f"{dataset_id}/{filename}: local byte count differs from catalog")
                if checksum:
                    if digest(local, algorithm) != expected:
                        raise ValueError(
                            f"{dataset_id}/{filename}: local file differs from publisher checksum"
                        )
                    local_verified += 1
                else:
                    local_unverified += 1
                    local_sha256 = digest(local, "sha256")
                    local_sha256_recorded += 1
                    findings.append(
                        {
                            "dataset_id": dataset_id,
                            "filename": filename,
                            "finding": "local_copy_without_publisher_checksum",
                            "local_bytes": local.stat().st_size,
                            "local_sha256": local_sha256,
                            "digest_scope": "local_file_integrity_only_not_provider_match",
                        }
                    )
    return {
        "schema": "matintegrity.dataset_catalog_audit.v1",
        "datasets": len(datasets),
        "assets": asset_count,
        "publisher_checksums_missing": missing_publisher_checksums,
        "locally_checksum_verified_assets": local_verified,
        "local_assets_without_publisher_checksum": local_unverified,
        "local_assets_with_recorded_sha256_but_no_provider_checksum": local_sha256_recorded,
        "acquisition_policies": dict(sorted(policies.items())),
        "rights_statuses": dict(sorted(rights.items())),
        "findings": findings,
    }


def main() -> None:
    print(json.dumps(audit(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

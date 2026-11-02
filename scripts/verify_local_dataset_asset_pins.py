"""Verify catalog-pinned metadata against exact local raw-asset paths."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "catalogs" / "datasets.json"
DEFAULT_OUTPUT = ROOT / "validation" / "local_dataset_asset_integrity.json"


def _hash_file(path: Path, algorithm: str) -> tuple[str, int]:
    digest = hashlib.new(algorithm)
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def _git_blob_sha1(path: Path) -> tuple[str, int]:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest(), len(payload)


def verify(dataset_ids: list[str]) -> dict:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    available = {row["id"]: row for row in catalog["datasets"]}
    unknown = sorted(set(dataset_ids) - set(available))
    if unknown:
        raise ValueError(f"unknown dataset IDs: {unknown}")

    rows = []
    for dataset_id in sorted(set(dataset_ids)):
        dataset = available[dataset_id]
        for asset in dataset.get("assets", []):
            filename = asset.get("filename")
            if not isinstance(filename, str) or not filename:
                continue
            path = (ROOT / "data" / "raw" / dataset_id / filename).resolve()
            path.relative_to((ROOT / "data" / "raw").resolve())
            if not path.is_file() or path.name.endswith(".part"):
                rows.append({
                    "dataset_id": dataset_id,
                    "filename": filename,
                    "status": "local_file_missing",
                })
                continue

            declaration = asset.get("checksum")
            algorithm, expected_digest = declaration.split(":", 1) if isinstance(declaration, str) and ":" in declaration else (None, None)
            if algorithm == "git-blob-sha1":
                observed_digest, observed_size = _git_blob_sha1(path)
            elif algorithm in hashlib.algorithms_available:
                observed_digest, observed_size = _hash_file(path, algorithm)
            else:
                rows.append({
                    "dataset_id": dataset_id,
                    "filename": filename,
                    "status": "checksum_missing_or_unsupported",
                    "declared_checksum": declaration,
                })
                continue
            checksum_matches = observed_digest.casefold() == expected_digest.casefold()
            byte_count_matches = asset.get("bytes") == observed_size
            rows.append({
                "dataset_id": dataset_id,
                "filename": filename,
                "status": "match" if checksum_matches and byte_count_matches else "mismatch",
                "declared_checksum": declaration,
                "observed_checksum": f"{algorithm}:{observed_digest}",
                "declared_bytes": asset.get("bytes"),
                "observed_bytes": observed_size,
                "checksum_matches": checksum_matches,
                "byte_count_matches": byte_count_matches,
            })

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {
        "schema_version": "matintegrity.local_dataset_asset_integrity.v1",
        "dataset_catalog_sha256": hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
        "dataset_ids": sorted(set(dataset_ids)),
        "asset_count": len(rows),
        "status_counts": counts,
        "meaning": "Exact local bytes and declared catalog pins only; no source authenticity, license, redistribution, scientific suitability, or package-content conclusion.",
        "assets": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-id", action="append", required=True, help="Dataset ID to inspect; may be repeated.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = verify(args.dataset_id)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"assets={report['asset_count']} status_counts={report['status_counts']} output={output.relative_to(ROOT)}")
    if report["status_counts"].get("mismatch", 0):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

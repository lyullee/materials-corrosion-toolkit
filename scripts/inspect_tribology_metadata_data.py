"""Audit pinned Zenodo tribology RDF metadata without reading linked measurements."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matintegrity.tribology_metadata_data import audit_tribology_metadata_dataset

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--directory",
        type=Path,
        default=ROOT / "data/raw/zenodo-7923128-tribology-metadata",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "validation/tribology_metadata_data_audit.json",
    )
    args = parser.parse_args()
    audit = audit_tribology_metadata_dataset(args.directory)
    summary = {
        "schema": "matintegrity.tribology_metadata_data_audit_summary.v1",
        "dataset_id": audit.dataset_id,
        "provider_record": audit.provider_record,
        "license": audit.license_id,
        "provider_checksum_verified_file_count": audit.file_count,
        "total_bytes": audit.total_bytes,
        "roles": {
            role: sum(row.role == role for row in audit.files)
            for role in sorted({row.role for row in audit.files})
        },
        "file_sha256": {row.filename: row.local_sha256 for row in audit.files},
        "numerical_use_status": audit.numerical_use_status,
        "qualification": (
            "The acquired files are RDF metadata and descriptions. Linked institutional RO-Crates "
            "containing raw and processed measurements were not acquired or interpreted. Metadata "
            "rows are not Archard calibration observations, independent specimens, service-life "
            "evidence, acceptance results or failure probabilities."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": audit.file_count, "bytes": audit.total_bytes}))


if __name__ == "__main__":
    main()

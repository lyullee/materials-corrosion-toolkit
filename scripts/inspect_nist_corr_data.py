"""Write aggregate archive evidence for the locally cached NIST CORR-DATA file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matintegrity.nist_corr_data import audit_nist_corr_data_archive

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive",
        type=Path,
        default=ROOT / "data/raw/nist-corr-data-corrosion-observations/CORR-DATA_Database.zip",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "validation/nist_corr_data_audit.json")
    args = parser.parse_args()
    report = audit_nist_corr_data_archive(args.archive)
    target = args.output.resolve()
    if ROOT not in target.parents:
        raise ValueError("audit output must remain inside the project")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "records": report.record_count,
                "archive_members": report.archive_member_count,
                "reference_keys": report.reference_key_count,
                "pointwise_records_published": report.pointwise_records_published,
                "qualification": report.qualification,
            }
        )
    )


if __name__ == "__main__":
    main()

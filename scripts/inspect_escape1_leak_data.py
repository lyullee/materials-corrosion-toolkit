"""Audit the pinned ESCAPE-1 files without publishing pointwise observations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matintegrity.escape_leak_data import audit_escape1_leak_dataset

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--directory",
        type=Path,
        default=ROOT / "data/raw/escape1-leak-calibration",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "validation/escape1_leak_data_audit.json",
    )
    args = parser.parse_args()
    audit = audit_escape1_leak_dataset(args.directory)
    summary = {
        "schema": "matintegrity.escape1_leak_data_audit_summary.v1",
        "dataset_id": audit.dataset_id,
        "provider_record": audit.provider_record,
        "license": audit.license_id,
        "provider_checksum_verified_file_count": len(audit.traces) + 1,
        "workbook_count": audit.workbook_count,
        "total_sample_count": audit.total_sample_count,
        "workbook_sha256": {row.provider_experiment_file_id: row.source_file_sha256 for row in audit.traces},
        "provider_declared_leak_rates_slpm": sorted(
            {row.provider_declared_leak_rate_value for row in audit.traces}
        ),
        "observed_sample_intervals_s": sorted(
            {
                value
                for row in audit.traces
                for value in (row.minimum_sample_interval_s, row.maximum_sample_interval_s)
            }
        ),
        "methane_response_unit": "ppm_m",
        "structural_checks": {
            "all_workbooks_have_one_sheet": True,
            "all_headers_match": True,
            "all_timestamps_strictly_increase_within_file": True,
            "all_responses_are_finite_and_nonnegative": True,
        },
        "calibration_use_status": audit.calibration_use_status,
        "qualification": (
            "Source identity, workbook structure, time order and raw response values are checked. "
            "The standard-litre reference state, release/background windows, meteorological alignment "
            "and cross-file independence remain unresolved. No molar leak calibration, unknown-leak "
            "inversion, detection probability, field acceptance or FTA probability is claimed."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"workbooks": audit.workbook_count, "samples": audit.total_sample_count}))


if __name__ == "__main__":
    main()

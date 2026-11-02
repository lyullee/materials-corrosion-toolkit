"""Audit the pinned FABEST LCF v2 package without extracting or executing provider files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matintegrity.fabest_lcf_data import audit_fabest_lcf_archive, iter_fabest_lcf_numeric_rows

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/fabest-lcf-v2/FABEST_LCF_Benchmark_Package_v2.0.zip"

EXPECTED = {
    "source_bytes": 531_469_245,
    "source_md5": "339c1ed86c4dd5d3459f487bda879154",
    "source_sha256": "50410c8a23305e76087ab340e3a1cc3c39c16db94f4da57090db3104a7c5b6ae",
    "archive_members": 170,
    "archive_files": 136,
    "archive_uncompressed_bytes": 1_418_792_453,
    "unsafe_member_paths": (),
    "duplicate_member_paths": (),
    "encrypted_members": (),
    "extension_counts": {
        ".5": 1,
        ".5pct": 1,
        ".csv": 98,
        ".docx": 1,
        ".pdf": 34,
        ".txt": 2,
        ".zip": 1,
        "<directory>": 32,
    },
    "calibration_experiment_count": 24,
    "calibration_table_count": 96,
    "calibration_data_rows": 25_213_349,
    "calibration_header_families": 7,
    "experiments_by_case": {1: 8, 2: 8, 3: 8},
    "tables_by_kind": {
        "cycle_summary": 24,
        "experiment_summary": 24,
        "ordered_history": 24,
        "representative_cycle": 24,
    },
    "blind_outcome_status": "not_present_in_validation_target_folder",
    "provider_code_executed": False,
}


def inspect_fabest_lcf_package(path: Path = ARCHIVE, *, full_numeric_scan: bool = False) -> dict:
    result = audit_fabest_lcf_archive(path)
    for key, expected in EXPECTED.items():
        actual = getattr(result, key)
        if actual != expected:
            raise ValueError(f"pinned FABEST LCF package changed: {key}: {actual!r}")
    report = result.model_dump(mode="json")
    if full_numeric_scan:
        scanned_rows = 0
        blank_cells = 0
        rows_with_blank_cells = 0
        for table in result.tables:
            rows = 0
            for _, values in iter_fabest_lcf_numeric_rows(
                path,
                member=table.member,
                expected_header=table.header,
                preserve_empty_fields=True,
            ):
                rows += 1
                row_blank_cells = sum(value is None for value in values)
                blank_cells += row_blank_cells
                rows_with_blank_cells += row_blank_cells > 0
            if rows != table.data_rows:
                raise ValueError(f"numeric scan row count changed: {table.member}")
            scanned_rows += rows
        report["full_numeric_scan"] = {
            "status": "passed",
            "tables": len(result.tables),
            "rows": scanned_rows,
            "blank_cells_preserved": blank_cells,
            "rows_with_blank_cells": rows_with_blank_cells,
            "checks": [
                "exact_header",
                "column_count",
                "nonblank_numeric_parse",
                "finite_nonblank_values",
                "blank_fields_preserved",
            ],
        }
    else:
        report["full_numeric_scan"] = {
            "status": "not_run",
            "tables": 0,
            "rows": 0,
            "checks": [],
        }
    report["qualification"] = (
        "The fixed archive contains 24 calibration experiment folders, each with four numeric CSV "
        "roles and one protocol document. Archive hierarchy supplies experiment folders but no "
        "separate physical-specimen identities. The validation-target folder contains no CSV "
        "outcomes. Structure and row counts do not validate constitutive models, fatigue criteria, "
        "material transferability, blind predictions or component acceptance."
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--full-numeric-scan", action="store_true")
    args = parser.parse_args()
    report = (
        json.dumps(
            inspect_fabest_lcf_package(full_numeric_scan=args.full_numeric_scan),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    if args.output is None:
        print(report, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(args.output)

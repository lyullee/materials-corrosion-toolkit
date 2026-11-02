"""Audit the pinned pressure-decay leak-test workbook without fitting leak rate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matintegrity.pressure_decay_leak_data import read_pressure_decay_leak_workbook

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        type=Path,
        default=ROOT / "data/raw/zenodo-20582921-pressure-decay/DataSet Temperatue-Pressure.xlsx",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "validation/pressure_decay_leak_data_audit.json",
    )
    args = parser.parse_args()
    time_s, _, audit = read_pressure_decay_leak_workbook(args.path)
    summary = {
        "schema": "matintegrity.pressure_decay_leak_data_audit_summary.v1",
        "dataset_id": audit.dataset_id,
        "provider_record": audit.provider_record,
        "license": audit.license_id,
        "source_file_sha256": audit.source_file_sha256,
        "series_count": audit.series_count,
        "total_samples": audit.total_samples,
        "time_range_s": [float(time_s[0]), float(time_s[-1])],
        "series": [row.model_dump(mode="json") for row in audit.series],
        "missing_configuration": audit.missing_configuration,
        "calibration_use_status": audit.calibration_use_status,
        "qualification": (
            "Workbook time, temperature and gauge-pressure columns are structurally audited. The provider "
            "description mentions a reference state, ambient and internal gas temperatures, but the workbook "
            "contains two capillary lengths and one unresolved temperature column per series. Vessel volume, "
            "absolute pressure, blank/outgassing history and uncertainty are absent, so no leak rate, gas-law "
            "inventory change, defect inversion, acceptance or probability is produced."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"series": audit.series_count, "samples": audit.total_samples}))


if __name__ == "__main__":
    main()

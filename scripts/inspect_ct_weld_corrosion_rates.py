"""Check local copies of CC BY coiled-tubing weld supplements against the public fixture."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/experimental-coiled-tubing-weld-corrosion"
FIXTURE = ROOT / "validation/ct110_weld_corrosion_rates.json"
EXPECTED = {
    "pone.0244237.s017.xlsx": "95fa4a025f4afe1aac1b5de41c420160",
    "pone.0244237.s018.xlsx": "931827263749cc61aa3e275f4b8c4b62",
}


def inspect(raw_dir: Path = RAW, fixture_path: Path = FIXTURE) -> dict:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    observations = iter(fixture["observations"])
    checked = []
    for filename, provider_md5 in EXPECTED.items():
        path = raw_dir / filename
        digest = hashlib.md5(path.read_bytes()).hexdigest()  # noqa: S324 - provider checksum only
        if digest != provider_md5:
            raise ValueError(f"provider MD5 mismatch for {filename}")
        workbook = load_workbook(path, data_only=True, read_only=True)
        if workbook.sheetnames != ["Sheet1", "Sheet2", "Sheet3"]:
            raise ValueError(f"unexpected worksheets in {filename}")
        sheet = workbook["Sheet1"]
        if filename.endswith("s017.xlsx"):
            conditions = [
                {
                    "temperature_C": 30,
                    "co2_partial_pressure_MPa": 0.3,
                    "total_pressure_MPa": 4,
                    "pH": 5.6,
                    "exposure_h": 96,
                },
                {
                    "temperature_C": 60,
                    "co2_partial_pressure_MPa": 0.3,
                    "total_pressure_MPa": 4,
                    "pH": 5.6,
                    "exposure_h": 96,
                },
                {
                    "temperature_C": 90,
                    "co2_partial_pressure_MPa": 0.3,
                    "total_pressure_MPa": 4,
                    "pH": 5.6,
                    "exposure_h": 96,
                },
            ]
            group = "temperature_sweep_co2_0.3_mpa"
        else:
            conditions = [
                {
                    "temperature_C": 60,
                    "co2_partial_pressure_MPa": 0.1,
                    "total_pressure_MPa": 4,
                    "pH": 5.6,
                    "exposure_h": 96,
                },
                {
                    "temperature_C": 60,
                    "co2_partial_pressure_MPa": 0.2,
                    "total_pressure_MPa": 4,
                    "pH": 5.6,
                    "exposure_h": 96,
                },
                {
                    "temperature_C": 60,
                    "co2_partial_pressure_MPa": 0.3,
                    "total_pressure_MPa": 4,
                    "pH": 5.6,
                    "exposure_h": 96,
                },
            ]
            group = "co2_pressure_sweep_at_60_C"
        first_data_row = 6 if filename.endswith("s017.xlsx") else 5
        values = [
            (sheet.cell(row, 4).value, sheet.cell(row, 5).value)
            for row in range(first_data_row, first_data_row + 3)
        ]
        for index, (condition, (weld, base)) in enumerate(zip(conditions, values, strict=True)):
            observation = next(observations)
            axis_key = "temperature_C" if filename.endswith("s017.xlsx") else "co2_partial_pressure_MPa"
            axis_row = first_data_row + index
            if (
                observation["condition_signature"] != condition
                or observation["condition_group_id"] != group
                or sheet.cell(axis_row, 3).value != condition[axis_key]
                or observation["weld_rate_mm_year"] != weld
                or observation["base_rate_mm_year"] != base
            ):
                raise ValueError(
                    f"public fixture does not match {filename} observation {observation['comparison_id']}"
                )
        checked.append({"filename": filename, "md5": digest, "observations": len(values)})
    try:
        next(observations)
    except StopIteration:
        pass
    else:
        raise ValueError("fixture contains unmatched observations")
    return {
        "schema": "matintegrity.ct110_weld_corrosion_source_audit.v1",
        "dataset_id": fixture["dataset_id"],
        "provider_files": checked,
        "matched_observations": sum(item["observations"] for item in checked),
        "physical_specimen_ids_available": fixture["physical_specimen_ids_available"],
        "uncertainty_available": fixture["uncertainty_available"],
    }


if __name__ == "__main__":
    print(json.dumps(inspect(), indent=2))

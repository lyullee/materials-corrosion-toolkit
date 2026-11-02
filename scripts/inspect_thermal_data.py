"""Inspect the pinned thermal-rod archive without treating fitted outputs as new experiments."""

from __future__ import annotations

import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np

from matintegrity.thermal_data import read_thermal_rod_fitted_results, read_thermal_rod_series

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/thermal-rod-transient/sbcf36976g-1.zip"


def inspect():
    catalog = json.loads((ROOT / "data/catalogs/datasets.json").read_text(encoding="utf-8"))
    dataset = next(item for item in catalog["datasets"] if item["id"] == "thermal-rod-transient")
    expected = dataset["assets"][0]["checksum"].split(":", 1)[1]
    actual = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError("thermal-rod archive checksum changed")
    with zipfile.ZipFile(ARCHIVE) as archive:
        run_ids = sorted(
            Path(name).stem
            for name in archive.namelist()
            if "/Raw_Data/" in name.replace("\\", "/") and name.lower().endswith(".csv")
        )
    fitted = read_thermal_rod_fitted_results(ARCHIVE)
    if set(run_ids) != set(fitted.run_id):
        raise ValueError("raw thermal runs and processed fit columns no longer map one-to-one")
    rows = 0
    negatives = 0
    controller_changes = 0
    time_steps = Counter()
    durations = []
    member_hashes = set()
    for run_id in run_ids:
        frame = read_thermal_rod_series(ARCHIVE, run_id)
        rows += len(frame)
        temperatures = frame[[f"tc{i}_excess_temperature_K" for i in range(1, 7)]].to_numpy()
        negatives += int(np.count_nonzero(temperatures < 0))
        controller_changes += int(frame.controller_setting_counts.nunique() > 1)
        time_steps.update(round(float(value), 6) for value in np.diff(frame.time_s))
        durations.append(float(frame.time_s.iloc[-1] - frame.time_s.iloc[0]))
        member_hashes.add(frame.attrs["source_member_sha256"])
    return dict(
        archive_sha256=actual,
        archive_bytes=ARCHIVE.stat().st_size,
        raw_runs=len(run_ids),
        unique_raw_members=len(member_hashes),
        raw_rows=rows,
        thermocouple_observations=rows * 6,
        negative_excess_temperature_observations=negatives,
        runs_with_controller_setting_changes=controller_changes,
        most_common_time_steps_s=time_steps.most_common(8),
        duration_range_s=[min(durations), max(durations)],
        fitted_output_rows=len(fitted),
        experiment_groups={key: int(value) for key, value in fitted.experiment_group.value_counts().items()},
        source_sheets={key: int(value) for key, value in fitted.source_sheet.value_counts().items()},
        fitted_conductivity_range_W_m_K=[
            float(fitted.fitted_conductivity_W_m_K.min()),
            float(fitted.fitted_conductivity_W_m_K.max()),
        ],
        fitted_convection_range_W_m2_K=[
            float(fitted.fitted_convection_W_m2_K.min()),
            float(fitted.fitted_convection_W_m2_K.max()),
        ],
        qualification=(
            "Primary multi-thermocouple transient runs with CC-BY-4.0 attribution. Processed h, k, "
            "boundary-ramp and power values were fitted to these same runs and are not independent "
            "experimental validation. Controller counts are not heat rate."
        ),
    )


if __name__ == "__main__":
    print(json.dumps(inspect(), indent=2, allow_nan=False))

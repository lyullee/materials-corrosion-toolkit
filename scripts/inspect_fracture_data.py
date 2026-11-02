"""Aggregate the pinned C1/C2 crack-arrest archive without deriving toughness values."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np

from matintegrity.fracture_data import list_crack_arrest_runs, read_crack_arrest_series

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/crack-arrest-c1-c2/g69875w65c-1.zip"


def inspect_fracture_data(path: Path = ARCHIVE) -> dict:
    runs = list_crack_arrest_runs(path)
    rows = 0
    negative_force = 0
    positive_force = 0
    zero_force = 0
    durations = []
    time_steps = []
    cycle_reversals = 0
    run_rows = {}
    for specimen_id in runs.specimen_id:
        frame = read_crack_arrest_series(path, specimen_id)
        values = frame.force_N.to_numpy()
        clock = frame.time_s.to_numpy()
        cycles = frame.reported_cycle_index.to_numpy()
        rows += len(frame)
        negative_force += int(np.sum(values < 0))
        positive_force += int(np.sum(values > 0))
        zero_force += int(np.sum(values == 0))
        durations.append(float(clock[-1] - clock[0]))
        time_steps.extend(np.round(np.diff(clock), 12).tolist())
        cycle_reversals += int(np.sum(np.diff(cycles) < 0))
        run_rows[specimen_id] = len(frame)
    with zipfile.ZipFile(path) as archive:
        whole_header_quoted = sum(
            archive.read(name).splitlines()[0].startswith(b'"Time Sec;')
            for name in archive.namelist()
            if name.lower().endswith(".csv")
        )
    unique_steps, step_counts = np.unique(np.asarray(time_steps), return_counts=True)
    result = {
        "source_id": "crack-arrest-c1-c2",
        "source_archive_sha256": runs.attrs["source_archive_sha256"],
        "license_id": runs.attrs["license_id"],
        "runs": len(runs),
        "families": runs.test_family.value_counts().sort_index().to_dict(),
        "temperature_range_K": [
            float(runs.reported_temperature_K.min()),
            float(runs.reported_temperature_K.max()),
        ],
        "rows": rows,
        "force_sign_counts": {
            "negative": negative_force,
            "zero": zero_force,
            "positive": positive_force,
        },
        "duration_range_s": [min(durations), max(durations)],
        "time_step_counts_s": {
            format(float(step), ".12g"): int(count)
            for step, count in zip(unique_steps, step_counts, strict=True)
        },
        "cycle_index_reversals": cycle_reversals,
        "whole_header_quoted_files": whole_header_quoted,
        "run_rows": run_rows,
        "qualification": (
            "Raw signed machine channels and filename-derived temperature metadata only. No zeroing, filtering, event picking, specimen-validity decision, toughness calculation, FAD calibration or independent structural validation is performed."
        ),
    }
    if result["runs"] != 18 or result["rows"] != 79341 or result["families"] != {"C1": 9, "C2": 9}:
        raise ValueError("pinned crack-arrest archive structure changed")
    return result


if __name__ == "__main__":
    print(json.dumps(inspect_fracture_data(), indent=2, ensure_ascii=False))

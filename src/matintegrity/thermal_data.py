"""Readers for the pinned one-dimensional thermal-rod experiment."""

from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

EXPECTED_RAW_COLUMNS = ["Time", "TC1", "TC2", "TC3", "TC4", "TC5", "TC6", "Power (1023 Max)"]
RESULT_WORKBOOKS = {
    "Temperature Results.xlsx": "fixed_wind_varied_heater_setting",
    "Wind Results.xlsx": "fixed_heater_setting_varied_wind",
    "AdditiveRodResults.xlsx": "additively_manufactured_304L",
}


def _open_archive(path: str | Path):
    archive_path = Path(path)
    return archive_path, zipfile.ZipFile(archive_path)


def _unique_member(archive: zipfile.ZipFile, suffix: str) -> str:
    matches = [name for name in archive.namelist() if name.replace("\\", "/").endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"expected one archive member ending in {suffix!r}, found {len(matches)}")
    return matches[0]


def read_thermal_rod_series(path: str | Path, run_id: str):
    """Read one raw run without converting controller counts into heat flux."""
    import numpy as np
    import pandas as pd

    if not run_id or "/" in run_id or "\\" in run_id or run_id.lower().endswith(".csv"):
        raise ValueError("run_id must be the source filename stem only")
    archive_path, archive = _open_archive(path)
    with archive:
        member = _unique_member(archive, f"/Raw_Data/{run_id}.csv")
        payload = archive.read(member)
    frame = pd.read_csv(io.BytesIO(payload))
    if frame.columns.tolist() != EXPECTED_RAW_COLUMNS:
        raise ValueError("thermal-rod raw column names or declared controller scale changed")
    if frame.empty or frame.isna().any().any():
        raise ValueError("complete thermal-rod numeric rows required")
    numeric = frame.apply(pd.to_numeric, errors="raise")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("finite thermal-rod values required")
    if numeric.Time.iloc[0] < 0 or np.any(np.diff(numeric.Time) <= 0):
        raise ValueError("thermal-rod time must be nonnegative and strictly increasing")
    result = pd.DataFrame({"time_s": numeric.Time})
    for index in range(1, 7):
        result[f"tc{index}_excess_temperature_K"] = numeric[f"TC{index}"]
    result["controller_setting_counts"] = numeric["Power (1023 Max)"]
    result.attrs.update(
        source_id="thermal-rod-transient",
        source_doi="10.17632/sbcf36976g.1",
        source_archive_sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        source_member=member,
        source_member_sha256=hashlib.sha256(payload).hexdigest(),
        license_id="CC-BY-4.0",
        run_id=run_id,
        temperature_basis="excess above source-declared ambient; numerically kelvin differences",
        controller_setting_basis="reported counts on a 1023 maximum scale; not watts or heat flux",
        limitations=[
            "Six thermocouple channels belong to one rod run and are not independent specimens.",
            "Negative excess-temperature readings are preserved and are not clipped.",
            "Sensor position, rod geometry, ambient temperature, heat-input efficiency and material state require run-family metadata before simulation comparison.",
        ],
    )
    return result


def _fitted_rows(frame, workbook: str, group: str, sheet: str):
    import pandas as pd

    if frame.shape[0] < 26 or frame.shape[1] < 2 or str(frame.iat[0, 0]).strip() != "Variable":
        raise ValueError("thermal-rod fitted-results worksheet schema changed")
    labels = {
        str(frame.iat[row, 0]).strip(): row for row in range(frame.shape[0]) if pd.notna(frame.iat[row, 0])
    }
    transient = labels.get("Transient model")
    alpha_row, delay_row = labels.get("alpha"), labels.get("tau")
    if transient is None or alpha_row is None or delay_row is None:
        raise ValueError("transient fit or fitted boundary-ramp fields absent")
    wanted = ["h", "k", "Pss", "standard_error", "h error", "k error", "Pss error"]
    rows = {}
    for offset in range(1, 8):
        label = str(frame.iat[transient + offset, 0]).strip()
        if label in rows:
            raise ValueError("duplicate transient fit label")
        rows[label] = transient + offset
    if set(rows) != set(wanted):
        raise ValueError("transient fit labels changed")
    output = []
    for column in range(1, frame.shape[1]):
        run = frame.iat[0, column]
        if pd.isna(run):
            continue
        values = {label: float(frame.iat[row, column]) for label, row in rows.items()}
        boundary_alpha = float(frame.iat[alpha_row, column])
        boundary_delay = float(frame.iat[delay_row, column])
        if not all(value >= 0 for value in values.values()) or not all(
            math_isfinite(value) for value in values.values()
        ):
            raise ValueError("finite nonnegative fitted thermal parameters required")
        if (
            boundary_alpha <= 0
            or boundary_delay < 0
            or not all(math_isfinite(value) for value in (boundary_alpha, boundary_delay))
        ):
            raise ValueError("positive finite boundary-ramp rate and nonnegative delay required")
        output.append(
            dict(
                run_id=str(run).strip(),
                source_workbook=workbook,
                experiment_group=group,
                source_sheet=sheet,
                fitted_boundary_ramp_rate_1_s=boundary_alpha,
                fitted_boundary_delay_s=boundary_delay,
                fitted_convection_W_m2_K=values["h"],
                fitted_conductivity_W_m_K=values["k"],
                fitted_steady_power_W=values["Pss"],
                fitted_standard_error_K=values["standard_error"],
                reported_h_error=values["h error"],
                reported_k_error=values["k error"],
                reported_power_error=values["Pss error"],
            )
        )
    return output


def math_isfinite(value: float) -> bool:
    import math

    return math.isfinite(value)


def read_thermal_rod_fitted_results(path: str | Path):
    """Read source-fitted results and label them as same-data parameter estimates."""
    import pandas as pd

    archive_path, archive = _open_archive(path)
    records = []
    with archive:
        for workbook, group in RESULT_WORKBOOKS.items():
            member = _unique_member(archive, f"/{workbook}")
            sheets = pd.read_excel(io.BytesIO(archive.read(member)), sheet_name=None, header=None)
            for sheet, frame in sheets.items():
                records.extend(_fitted_rows(frame, workbook, group, str(sheet)))
    result = pd.DataFrame(records)
    if len(result) != 77 or not result.run_id.is_unique:
        raise ValueError("expected 77 unique fitted thermal-rod runs")
    result.attrs.update(
        source_id="thermal-rod-transient",
        source_doi="10.17632/sbcf36976g.1",
        source_archive_sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        license_id="CC-BY-4.0",
        parameter_relationship="estimated from the same raw temperature runs; not independent validation targets",
        limitations=[
            "Reported parameter-error fields inherit the source fitting assumptions and are not reinterpreted as complete model-form uncertainty.",
            "Each run appears once across the three processed workbooks; worksheet cells are fitted outputs rather than additional experiments.",
        ],
    )
    return result

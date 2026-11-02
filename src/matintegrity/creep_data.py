"""Read the fixed BAM CMSX-6 workbook and processed constant-load traces."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np


def _number(value):
    result = float(str(value).strip().replace(",", "."))
    if not math.isfinite(result):
        raise ValueError("finite reported numeric value required")
    return result


def read_cmsx6_creep(workbook: str | Path):
    """Return one observation per test; explicit time-limit endpoints are censored."""
    import pandas as pd

    path = Path(workbook)
    book = pd.ExcelFile(path)
    names = [s for s in book.sheet_names if s.startswith("Vh5205_C-")]
    if not names:
        raise ValueError("CMSX-6 test worksheets absent")
    rows = []
    for name in names:
        sheet = pd.read_excel(book, sheet_name=name, header=None)
        if sheet.shape[1] < 7 or sheet.iat[2, 2] != "ENTRY":
            raise ValueError("CMSX-6 workbook schema changed")
        records = {}
        wanted = {
            "Test ID",
            "Load control type",
            "(Digital) Material Identifier",
            "Specified temperature",
            "Test duration",
            "Creep rupture time",
            "End of test criterium",
            "Initial stress",
        }
        for row in sheet.values[3:]:
            if pd.notna(row[2]):
                key = str(row[2]).strip()
                if key not in wanted:
                    continue
                if key in records:
                    raise ValueError("duplicate test metadata key")
                records[key] = (row[4], row[6])

        def item(key, unit=None, _records=records):
            stored_unit, value = _records[key]
            if unit is not None and stored_unit != unit:
                raise ValueError(f"unexpected unit for {key}")
            return value

        if (
            item("Test ID") != name
            or item("Load control type") != "Constant force"
            or item("(Digital) Material Identifier") != "CMSX-6"
        ):
            raise ValueError("test identity, alloy or load-control regime changed")
        temperature = str(item("Specified temperature", "°C")).strip()
        if not temperature.endswith("°C"):
            raise ValueError("explicit specified Celsius temperature required")
        duration = _number(item("Test duration", "h")) * 3600
        rupture = item("Creep rupture time", "h")
        criterion = str(item("End of test criterium")).strip()
        if criterion == "Test piece break":
            endpoint = _number(rupture) * 3600
            if endpoint <= 0 or endpoint > duration:
                raise ValueError("inconsistent reported rupture and test duration")
            censored, endpoint_kind = False, "rupture"
        elif criterion == "Time limit" and str(rupture).strip() == "Not applicable":
            endpoint, censored, endpoint_kind = duration, True, "administrative_time_limit"
        else:
            endpoint, censored, endpoint_kind = None, None, "unresolved"
        rows.append(
            dict(
                specimen_id=name,
                material_condition_id="BAM-CMSX6-reference-v1.0-single-crystal-heat-treated",
                stress_basis="initial_nominal_constant_load",
                temperature_basis="nominal_specified",
                initial_stress_Pa=_number(item("Initial stress", "MPa")) * 1e6,
                temperature_K=_number(temperature[:-2]) + 273.15,
                endpoint_time_s=endpoint,
                right_censored=censored,
                endpoint_kind=endpoint_kind,
                reported_test_duration_s=duration,
                reported_control="constant_force",
            )
        )
    frame = pd.DataFrame(rows)
    if (
        not frame.specimen_id.is_unique
        or np.any(frame.initial_stress_Pa <= 0)
        or np.any(frame.temperature_K <= 0)
        or np.any(frame.reported_test_duration_s <= 0)
    ):
        raise ValueError("unique positive specimen conditions required")
    frame.attrs.update(
        source_id="cmsx6-creep",
        source_doi="10.5281/zenodo.14750432",
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        license_id="CC-BY-4.0",
        limitations=[
            "Initial nominal stress under constant force is not constant true stress.",
            "Same laboratory and material condition; orientation deviations are not identical physical specimens or multiple temperature levels.",
            "Use reported endpoint metadata, never the last waveform sample, for rupture/censor times.",
        ],
    )
    return frame


def read_cmsx6_trace(path: str | Path, *, duplicate_policy="reject"):
    """Read the processed LIS clock in hours and extension in percent into SI."""
    import pandas as pd

    if duplicate_policy not in {"reject", "preserve"}:
        raise ValueError("duplicate_policy must explicitly reject or preserve repeated clock values")
    path = Path(path)
    lines = path.read_text(encoding="latin1").splitlines()
    marker = next((i for i, line in enumerate(lines) if line.split("\t")[0] == "[data]"), None)
    if (
        marker is None
        or lines[marker + 2].split("\t")[:5] != ["t", "e", "Tc", "Tc", "Tc"]
        or lines[marker + 3].split("\t")[:5] != ["h", "%", "°C", "°C", "°C"]
    ):
        raise ValueError("explicit processed LIS axes or units changed")
    rows = []
    for line in lines[marker + 4 :]:
        cells = line.split("\t")
        if not any(c.strip() for c in cells):
            continue
        if len(cells) < 5:
            raise ValueError("incomplete processed trace row")
        values = [_number(c) for c in cells[:5]]
        rows.append([values[0] * 3600, values[1] / 100, *[v + 273.15 for v in values[2:]]])
    frame = pd.DataFrame(
        rows,
        columns=[
            "time_s",
            "plastic_extension_fraction",
            "top_temperature_K",
            "middle_temperature_K",
            "bottom_temperature_K",
        ],
    )
    if frame.empty or np.any(np.diff(frame.time_s) < 0) or frame.time_s.iloc[0] < 0:
        raise ValueError("nondecreasing nonnegative processed creep clock required")
    duplicates = int(np.count_nonzero(np.diff(frame.time_s) == 0))
    if duplicates and duplicate_policy == "reject":
        raise ValueError(
            "repeated processed clock values require explicit preserve policy; do not invent sub-resolution times"
        )
    frame["repeated_timestamp"] = frame.time_s.duplicated(keep=False)
    frame.attrs.update(
        specimen_id=path.stem,
        clock_origin="end_of_loading",
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        source_time_unit="h",
        source_extension_unit="percent",
        origin="processed_observations",
        repeated_clock_intervals=duplicates,
        limitations=[
            "Processed extension from end of loading; loading/heating histories are separate.",
            "The LIS explicitly labels hours although a workbook schema row describes seconds; this reader uses file-local units.",
            "Trace endpoint is not automatically a rupture time.",
        ],
    )
    return frame

"""Explicit data ingestion; qualifiers and missing evidence are preserved."""

from __future__ import annotations

import csv
import math
import re
import zipfile
from bisect import bisect_left
from fractions import Fraction
from io import StringIO
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract


class TabulatedProperty(Contract):
    property_id: str = Field(min_length=1)
    x: list[float] = Field(min_length=2)
    y: list[float] = Field(min_length=2)
    x_unit: str = Field(min_length=1)
    y_unit: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    interpolation: Literal["linear", "pchip"] = "linear"

    @model_validator(mode="after")
    def ordered(self):
        if len(self.x) != len(self.y) or any(b <= a for a, b in zip(self.x, self.x[1:], strict=False)):
            raise ValueError("property table requires aligned, strictly increasing coordinates")
        return self

    def at(self, coordinate: float) -> float:
        if isinstance(coordinate, bool) or not math.isfinite(coordinate):
            raise ValueError("finite coordinate required")
        coordinate = float(coordinate)
        if not self.x[0] <= coordinate <= self.x[-1]:
            raise ValueError("property extrapolation is disabled; supply qualified data covering the state")
        if self.interpolation == "linear":
            index = bisect_left(self.x, coordinate)
            if self.x[index] == coordinate:
                return self.y[index]
            left = index - 1
            weight = (Fraction(coordinate) - Fraction(self.x[left])) / (
                Fraction(self.x[index]) - Fraction(self.x[left])
            )
            exact = Fraction(self.y[left]) + weight * (Fraction(self.y[index]) - Fraction(self.y[left]))
            result = float(exact)
            if not math.isfinite(result) or (exact and result == 0):
                raise ArithmeticError("nonzero interpolated property is not representable")
            return result
        from scipy.interpolate import PchipInterpolator

        result = float(PchipInterpolator(self.x, self.y, extrapolate=False)(coordinate))
        if not math.isfinite(result):
            raise ArithmeticError("PCHIP property result is not finite")
        return result


def parse_reported_value(value: str) -> dict:
    """Parse a scalar/inequality/range while leaving nonnumeric ratings unresolved."""
    raw = str(value).strip()
    number = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
    scalar = re.fullmatch(rf"({number})", raw)
    if scalar and math.isfinite(float(scalar[1])):
        v = float(scalar[1])
        return dict(raw=raw, kind="exact", lower=v, upper=v, lower_closed=True, upper_closed=True)
    bound = re.fullmatch(rf"(<=|>=|<|>|≤|≥)\s*({number})", raw)
    if bound and math.isfinite(float(bound[2])):
        symbol, value = bound[1], float(bound[2])
        lower = symbol in {">", ">=", "≥"}
        return dict(
            raw=raw,
            kind="lower_bound" if lower else "upper_bound",
            lower=value if lower else None,
            upper=None if lower else value,
            lower_closed=symbol in {">=", "≥"},
            upper_closed=symbol in {"<=", "≤"},
        )
    interval = re.fullmatch(rf"({number})\s*(?:to|–|—|-)\s*({number})", raw)
    if (
        interval
        and all(math.isfinite(float(interval[k])) for k in (1, 2))
        and float(interval[1]) <= float(interval[2])
    ):
        return dict(
            raw=raw,
            kind="interval",
            lower=float(interval[1]),
            upper=float(interval[2]),
            lower_closed=True,
            upper_closed=True,
        )
    return dict(raw=raw, kind="unresolved", lower=None, upper=None, lower_closed=False, upper_closed=False)


def archive_text(path: str | Path, member: str, encoding: str = "utf-8-sig") -> str:
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo(member)
        if info.file_size > 32 * 1024 * 1024:
            raise ValueError("text member too large for this bounded table loader")
        return archive.read(member).decode(encoding)


def read_corr_data(path: str | Path) -> list[dict]:
    text = archive_text(path, "CORR-DATA_Database.csv")
    rows = []
    for index, row in enumerate(csv.DictReader(StringIO(text)), 1):
        rate_key = next((key for key in row if key and "mm/yr" in key), None)
        if rate_key is None:
            raise ValueError("CORR-DATA rate column is missing; provider schema may have changed")
        rows.append(
            dict(
                row_number=index,
                fields=row,
                reported_rate_mm_year=parse_reported_value(row[rate_key]),
                source_id="nist-corr",
                redistribution_status="review_required",
            )
        )
    return rows


def read_galvanized_polarization(path: str | Path):
    """Read published signed polarization curves; do not auto-select Tafel branches."""
    import pandas as pd

    workbook = pd.ExcelFile(path, engine="openpyxl")
    if len(workbook.sheet_names) != 1:
        raise ValueError("select a provider polarization workbook with exactly one electrolyte sheet")
    sheet = workbook.sheet_names[0]
    raw = pd.read_excel(workbook, header=None)
    records = []
    for column in range(1, raw.shape[1], 3):
        if (
            str(raw.iat[1, column]).strip() != "Potential (V)"
            or str(raw.iat[1, column + 1]).strip() != "Current (A·cm-2)"
        ):
            raise ValueError("polarization workbook headings/units changed")
        specimen = str(raw.iat[0, column]).strip()
        for row in range(2, len(raw)):
            potential, current = raw.iat[row, column], raw.iat[row, column + 1]
            if pd.isna(potential) and pd.isna(current):
                continue
            potential, current = float(potential), float(current)
            if not math.isfinite(potential) or not math.isfinite(current):
                raise ValueError("incomplete or non-finite polarization observation")
            records.append(
                dict(
                    source_row=row + 1,
                    specimen_id=specimen,
                    electrolyte_id=sheet,
                    potential_V=potential,
                    signed_current_density_A_m2=current * 1e4,
                    source_id="galvanized-polarization",
                )
            )
    frame = pd.DataFrame(records)
    if frame.empty:
        raise ValueError("no numerical polarization observations found")
    return frame


def read_weld_fatigue(path: str | Path):
    import pandas as pd

    frame = pd.read_csv(path, sep="\t", na_values=["NA"])
    required = {
        "SpecimenName",
        "StressRatio",
        "NominalStressRange_MPa",
        "LoadCyclesToFailure",
        "RunOut",
        "Outlier",
    }
    if not required <= set(frame):
        raise ValueError("weld fatigue schema mismatch")
    frame["material"] = frame.SpecimenName.str.extract(r"-(S\d+)-", expand=False)
    frame["treatment"] = frame.SpecimenName.str.rsplit("-", n=1).str[-1]
    frame["repeated_specimen"] = frame.SpecimenName.duplicated(keep=False)
    frame["stress_range_Pa"] = frame.NominalStressRange_MPa * 1e6
    if not frame.RunOut.dropna().isin([0, 1]).all():
        raise ValueError("unrecognized fatigue censoring flag")
    frame["runout"] = frame.RunOut.astype("boolean")
    frame["row_valid"] = (
        frame.RunOut.notna()
        & frame.Outlier.notna()
        & frame.SpecimenName.notna()
        & frame.NominalStressRange_MPa.gt(0)
        & frame.LoadCyclesToFailure.gt(0)
    )
    return frame


def process_chunks(archive_path: str | Path, *, chunksize: int = 100_000):
    """Yield process observations without loading a multi-month history at once."""
    import pandas as pd

    with zipfile.ZipFile(archive_path) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError("select a process archive with one CSV member")
        with archive.open(names[0]) as stream:
            yield from pd.read_csv(stream, chunksize=chunksize)


def read_bam_creep_fatigue(path: str | Path) -> dict:
    """Read one P92 LIS test, preserving recorded-cycle gaps and control context."""
    import pandas as pd

    lines = Path(path).read_text(encoding="cp1252").splitlines()
    markers = {
        line.strip().split("\t")[0]: index for index, line in enumerate(lines) if line.strip().startswith("[")
    }
    if "[Data]" not in markers or "[MAX-MIN]" not in markers:
        raise ValueError("BAM section markers missing")
    start = markers["[Data]"]
    header = lines[start + 1].split("\t")[:5]
    units = lines[start + 2].split("\t")[:5]
    if header != ["Time", "Cycle", "Stress", "Strain", "Temperature"] or units != [
        "s",
        "No",
        "MPa",
        "%",
        "°C",
    ]:
        raise ValueError("BAM waveform schema or units changed")
    frame = pd.read_csv(
        StringIO("\n".join(lines[start + 3 :])),
        sep="\t",
        header=None,
        usecols=range(5),
        names=["time_s", "cycle", "stress_MPa", "strain_percent", "temperature_degC"],
    )
    if not np.isfinite(frame.to_numpy(dtype=float)).all() or (frame.time_s.diff().dropna() < 0).any():
        raise ValueError("BAM waveform contains unresolved numerical or clock values")
    frame["stress_Pa"] = frame.stress_MPa * 1e6
    frame["strain_fraction"] = frame.strain_percent / 100
    frame["temperature_K"] = frame.temperature_degC + 273.15
    if (
        not np.isfinite(frame[["stress_Pa", "strain_fraction", "temperature_K"]].to_numpy()).all()
        or (frame.temperature_K <= 0).any()
    ):
        raise ValueError("BAM normalized waveform contains an invalid SI value")
    if (frame.cycle <= 0).any() or (frame.cycle % 1 != 0).any() or (frame.cycle.diff().dropna() < 0).any():
        raise ValueError("BAM cycle identifiers must be positive, integral and nondecreasing")
    selected = {}
    for line in lines[: markers["[MAX-MIN]"]]:
        cells = line.split("\t")
        if cells[0] in {
            "Test Design",
            "Material",
            "Testing Temperature",
            "Cycles to Failure, Nf",
            "Total No. of Cycles, N",
        }:
            selected[cells[0]] = cells[4].strip()
    repeated = int((frame.time_s.diff().dropna() == 0).sum())
    extrema = None
    maxmin_start = markers["[MAX-MIN]"]
    if maxmin_start + 1 < start and lines[maxmin_start + 1].startswith("Cycle\t"):
        expected = [
            "Cycle",
            "Stress-Max",
            "Stress-Min",
            "Strain-Max",
            "Strain-Min",
            "Temperature-Max",
            "Temperature-Min",
        ]
        if lines[maxmin_start + 1].split("\t")[:7] != expected:
            raise ValueError("BAM cycle extrema schema changed")
        if lines[maxmin_start + 2].split("\t")[:7] != ["No", "MPa", "MPa", "%", "%", "°C", "°C"]:
            raise ValueError("BAM cycle extrema units changed")
        extrema = pd.read_csv(
            StringIO("\n".join(lines[maxmin_start + 3 : start])),
            sep="\t",
            header=None,
            usecols=range(7),
            names=[
                "cycle",
                "maximum_stress_MPa",
                "minimum_stress_MPa",
                "maximum_strain_percent",
                "minimum_strain_percent",
                "maximum_temperature_degC",
                "minimum_temperature_degC",
            ],
        )
        extrema = extrema.dropna(how="all")
        if not np.isfinite(extrema.to_numpy(dtype=float)).all() or np.any(np.diff(extrema.cycle) <= 0):
            raise ValueError("nonfinite or unordered cycle extrema")
        for kind in ("maximum", "minimum"):
            extrema[f"{kind}_stress_Pa"] = extrema[f"{kind}_stress_MPa"] * 1e6
            extrema[f"{kind}_strain_fraction"] = extrema[f"{kind}_strain_percent"] / 100
            extrema[f"{kind}_temperature_K"] = extrema[f"{kind}_temperature_degC"] + 273.15
        if (extrema.cycle <= 0).any() or (extrema.cycle % 1 != 0).any():
            raise ValueError("positive integral extrema cycle identifiers required")
        for quantity in ("stress_Pa", "strain_fraction", "temperature_K"):
            if (extrema[f"maximum_{quantity}"] < extrema[f"minimum_{quantity}"]).any():
                raise ValueError("cycle extrema bounds are reversed")
    return dict(
        source_id="bam-p92",
        metadata=selected,
        waveform=frame,
        cycle_extrema=extrema,
        zero_duration_intervals=repeated,
        clock_strictly_increasing=repeated == 0,
        qualification="Recorded order and rounded duplicate timestamps are preserved; time derivatives require clock-resolution treatment. Missing cycles are not interpolated.",
    )

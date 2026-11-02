"""Read the pinned corrosion-resistant-alloy metric compilation safely.

The workbook combines values reported by many publications.  This reader preserves
endpoint, statistic, reference, censoring and source-row identity; it does not turn the
compilation into a material ranking, a specimen database or a qualified design table.
"""

from __future__ import annotations

import hashlib
import math
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MetricColumn:
    column: int
    metric: str
    statistic: str
    source_unit: str


@dataclass(frozen=True)
class SheetDefinition:
    composition_columns: tuple[tuple[str, int], ...]
    metric_columns: tuple[MetricColumn, ...]
    condition_columns: tuple[tuple[str, int], ...]
    reference_column: int
    material_class_column: int


ELEMENTS_25 = (
    "Fe",
    "Cr",
    "Ni",
    "Mo",
    "W",
    "N",
    "Nb",
    "C",
    "Si",
    "Mn",
    "Cu",
    "P",
    "S",
    "Al",
    "V",
    "Ta",
    "Re",
    "Ce",
    "Ti",
    "Co",
    "B",
    "Mg",
    "Y",
    "Gd",
)


def _composition(elements: tuple[str, ...], start: int = 2) -> tuple[tuple[str, int], ...]:
    return tuple((element, start + index) for index, element in enumerate(elements))


SHEETS: dict[str, SheetDefinition] = {
    "Pitting Potential": SheetDefinition(
        _composition(ELEMENTS_25),
        (
            MetricColumn(26, "pitting_potential", "average", "mV_vs_SCE"),
            MetricColumn(27, "pitting_potential", "maximum", "mV_vs_SCE"),
            MetricColumn(28, "pitting_potential", "minimum", "mV_vs_SCE"),
        ),
        (
            ("test_temperature_degC", 29),
            ("test_solution", 30),
            ("chloride_concentration_mol_L", 31),
            ("pH", 32),
            ("test_method", 33),
            ("scan_rate_mV_s", 34),
            ("heat_treatment", 35),
            ("microstructure", 36),
            ("comments", 37),
        ),
        38,
        39,
    ),
    "Repassivation Potential": SheetDefinition(
        _composition(ELEMENTS_25),
        (MetricColumn(26, "repassivation_potential", "average", "mV_vs_SCE"),),
        (
            ("test_temperature_degC", 27),
            ("test_solution", 28),
            ("chloride_concentration_mol_L", 29),
            ("pH", 30),
            ("test_method", 31),
            ("scan_rate_mV_s", 32),
            ("heat_treatment", 33),
            ("microstructure", 34),
            ("comments", 35),
        ),
        37,
        36,
    ),
    "Crevice Corrosion Potential": SheetDefinition(
        _composition(ELEMENTS_25[:14]),
        (
            MetricColumn(16, "crevice_corrosion_potential", "average", "mV_vs_SCE"),
            MetricColumn(17, "crevice_corrosion_potential", "maximum", "mV_vs_SCE"),
            MetricColumn(18, "crevice_corrosion_potential", "minimum", "mV_vs_SCE"),
        ),
        (
            ("test_temperature_degC", 19),
            ("test_solution", 20),
            ("chloride_concentration_mol_L", 21),
            ("pH", 22),
            ("test_method", 23),
            ("scan_rate_mV_s", 24),
            ("heat_treatment", 25),
            ("microstructure", 26),
            ("comments", 27),
        ),
        28,
        29,
    ),
    "Pitting Temp": SheetDefinition(
        _composition(ELEMENTS_25[:14]),
        (
            MetricColumn(16, "critical_pitting_temperature", "average", "degC"),
            MetricColumn(17, "critical_pitting_temperature", "maximum", "degC"),
            MetricColumn(18, "critical_pitting_temperature", "minimum", "degC"),
        ),
        (
            ("test_solution", 19),
            ("test_method", 20),
            ("test_potential_mV_vs_SCE", 21),
            ("temperature_scan_rate_degC_min", 22),
            ("heat_treatment", 23),
            ("microstructure", 24),
            ("comments", 25),
        ),
        26,
        27,
    ),
    "Crevice Corrosion Temp": SheetDefinition(
        _composition(
            (
                "Fe",
                "Cr",
                "Ni",
                "Mo",
                "W",
                "N",
                "Nb",
                "C",
                "Si",
                "Mn",
                "Cu",
                "P",
                "S",
                "Al",
                "V",
                "Co",
                "Re",
                "Ce",
                "Ti",
                "Nb+Ta",
            )
        ),
        (
            MetricColumn(22, "critical_crevice_temperature", "average", "degC"),
            MetricColumn(23, "critical_crevice_temperature", "maximum", "degC"),
            MetricColumn(24, "critical_crevice_temperature", "minimum", "degC"),
        ),
        (
            ("test_solution", 25),
            ("test_method", 26),
            ("test_potential_mV_vs_SCE", 27),
            ("temperature_scan_rate_degC_min", 28),
            ("heat_treatment", 29),
            ("microstructure", 30),
            ("comments", 31),
        ),
        32,
        33,
    ),
    "HEAs_Ecorr, icorr, ipass, Rate": SheetDefinition(
        _composition(ELEMENTS_25[:21]),
        (
            MetricColumn(23, "corrosion_potential", "average", "mV_vs_SCE"),
            MetricColumn(24, "corrosion_potential", "standard_error", "mV"),
            MetricColumn(25, "corrosion_current_density", "average", "A_per_cm2"),
            MetricColumn(26, "corrosion_current_density", "standard_error", "A_per_cm2"),
            MetricColumn(27, "corrosion_rate", "reported", "mm_per_year"),
            MetricColumn(28, "passivation_current_density", "reported", "A_per_cm2"),
        ),
        (
            ("corrosion_value_method", 29),
            ("oxide", 30),
            ("test_temperature_degC", 31),
            ("test_solution", 32),
            ("chloride_concentration_mol_L", 33),
            ("pH", 34),
            ("test_method", 35),
            ("scan_rate_mV_s", 36),
            ("heat_treatment", 37),
            ("microstructure", 38),
            ("comments", 39),
        ),
        40,
        41,
    ),
}

EXPECTED_WORKBOOK_SHA256 = "d0ce5e9c4b42e0b5a20dbd5c4896791703c5f433ae19bc032674d5848d9d1438"
COMPILATION_DOI = "10.6084/m9.figshare.13038257.v2"
_BOUND = re.compile(r"^\s*([<>])\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee]\s*[+-]?\s*\d+)?)\s*$")
_SPACED_SCIENTIFIC = re.compile(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*[Ee]\s*([+-]?)\s*(\d+)\s*$")


def _cell(row: tuple[Any, ...], column: int) -> Any:
    return row[column - 1] if column <= len(row) else None


def _finite(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _parse_metric(value: Any) -> tuple[str, float | None, str | None]:
    number = _finite(value)
    if number is not None:
        return "exact", number, None
    if value is None or str(value).strip().upper() in {"", "NA", "N/A", "--"}:
        return "missing", None, None
    text = str(value).strip()
    match = _BOUND.match(text)
    if match:
        number_text = re.sub(r"\s+", "", match.group(2))
        return ("lower_bound" if match.group(1) == ">" else "upper_bound", float(number_text), text)
    match = _SPACED_SCIENTIFIC.match(text)
    if match:
        sign = match.group(2) or "+"
        return "exact_text_numeric", float(f"{match.group(1)}e{sign}{match.group(3)}"), text
    return "qualitative", None, text


def _normalize(value: float | None, unit: str) -> tuple[float | None, str]:
    if value is None:
        return None, {
            "mV_vs_SCE": "V_vs_SCE",
            "mV": "V",
            "degC": "K",
            "A_per_cm2": "A_per_m2",
            "mm_per_year": "m_per_s",
        }[unit]
    if unit == "mV_vs_SCE":
        return value * 1e-3, "V_vs_SCE"
    if unit == "mV":
        return value * 1e-3, "V"
    if unit == "degC":
        return value + 273.15, "K"
    if unit == "A_per_cm2":
        return value * 1e4, "A_per_m2"
    if unit == "mm_per_year":
        return value * 1e-3 / (365.25 * 86400.0), "m_per_s"
    raise ValueError(f"unsupported source unit: {unit}")


def _reference_catalog(workbook) -> dict[int, dict[str, str | None]]:
    sheet = workbook["References"]
    result: dict[int, dict[str, str | None]] = {}
    for row in sheet.iter_rows(min_row=2, values_only=True):
        number = _finite(_cell(row, 1))
        if number is None or not number.is_integer():
            continue
        citation = None if _cell(row, 2) is None else str(_cell(row, 2)).strip()
        raw_doi = None if _cell(row, 3) is None else str(_cell(row, 3)).strip().lstrip("\ufeff")
        doi = None if raw_doi is None or raw_doi.upper() in {"", "NA", "N/A"} else raw_doi
        result[int(number)] = {"citation": citation, "doi": doi}
    return result


def read_corrosion_alloy_metrics(path: str | Path, *, require_pinned_hash: bool = False):
    """Return a long-form metric table from the CC BY 4.0 compilation workbook.

    Bounds and qualitative outcomes are retained rather than imputed.  Normalized values
    preserve the SCE reference for potentials.  Physical specimen identity, test validity and
    underlying-observation redistribution rights remain explicitly unresolved.
    """
    import openpyxl
    import pandas as pd

    source = Path(path)
    payload = source.read_bytes()
    source_sha256 = hashlib.sha256(payload).hexdigest()
    if require_pinned_hash and source_sha256 != EXPECTED_WORKBOOK_SHA256:
        raise ValueError("workbook does not match the pinned Figshare v2 asset")
    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        if any(name.lower().endswith("vbaproject.bin") for name in names):
            raise ValueError("macro-enabled workbook content is not accepted")
        if any("externallinks/" in name.lower() for name in names):
            raise ValueError("workbook external links are not accepted")

    workbook = openpyxl.load_workbook(source, read_only=True, data_only=True)
    missing = (set(SHEETS) | {"References"}) - set(workbook.sheetnames)
    if missing:
        raise ValueError(f"required workbook sheets are missing: {sorted(missing)}")
    references = _reference_catalog(workbook)
    records: list[dict[str, Any]] = []
    for sheet_name, definition in SHEETS.items():
        sheet = workbook[sheet_name]
        slug = re.sub(r"[^a-z0-9]+", "-", sheet_name.lower()).strip("-")
        for row_number, row in enumerate(sheet.iter_rows(min_row=3, values_only=True), start=3):
            source_number = _finite(_cell(row, 1))
            if source_number is None or not source_number.is_integer():
                continue
            source_number_int = int(source_number)
            reference_value = _finite(_cell(row, definition.reference_column))
            reference_number = (
                int(reference_value) if reference_value is not None and reference_value.is_integer() else None
            )
            reference = references.get(reference_number, {})
            composition_raw = {
                element: _cell(row, column) for element, column in definition.composition_columns
            }
            composition_numeric = {
                element: value
                for element, raw in composition_raw.items()
                if (value := _finite(raw)) is not None
            }
            conditions = {field: _cell(row, column) for field, column in definition.condition_columns}
            source_observation_id = f"{slug}:{source_number_int}"
            for metric_column in definition.metric_columns:
                raw_value = _cell(row, metric_column.column)
                status, parsed_value, qualifier = _parse_metric(raw_value)
                normalized_value, normalized_unit = _normalize(parsed_value, metric_column.source_unit)
                metric_slug = metric_column.metric.replace("_", "-")
                records.append(
                    {
                        "observation_id": (
                            f"{source_observation_id}:{metric_slug}:{metric_column.statistic}"
                        ),
                        "source_observation_id": source_observation_id,
                        "source_sheet": sheet_name,
                        "source_row": row_number,
                        "source_number": source_number_int,
                        "metric": metric_column.metric,
                        "statistic": metric_column.statistic,
                        "raw_value": raw_value,
                        "value_status": status,
                        "qualifier": qualifier,
                        "reported_value": parsed_value,
                        "source_unit": metric_column.source_unit,
                        "normalized_value": normalized_value,
                        "normalized_unit": normalized_unit,
                        "potential_reference": ("SCE" if metric_column.source_unit == "mV_vs_SCE" else None),
                        "composition_wt_percent": composition_numeric,
                        "composition_raw": composition_raw,
                        "material_class": _cell(row, definition.material_class_column),
                        "conditions": conditions,
                        "reference_number": reference_number,
                        "underlying_reference_doi": reference.get("doi"),
                        "underlying_reference_citation": reference.get("citation"),
                        "source_group_id": (
                            None if reference_number is None else f"compilation-reference:{reference_number}"
                        ),
                        "physical_specimen_id": None,
                        "physical_specimen_independence_reviewed": False,
                        "test_validity_reviewed": False,
                        "compilation_license_id": "CC-BY-4.0",
                        "underlying_observation_rights_status": "unresolved",
                        "source_workbook_sha256": source_sha256,
                    }
                )
    frame = pd.DataFrame.from_records(records)
    if frame.observation_id.duplicated().any():
        raise ValueError("workbook produced duplicate metric observation identifiers")
    frame.attrs.update(
        source_id="corrosion-resistant-alloy-metrics",
        source_doi=COMPILATION_DOI,
        source_workbook_sha256=source_sha256,
        compilation_license_id="CC-BY-4.0",
        workbook_formula_execution=False,
        workbook_macro_execution=False,
        source_rows=int(frame.source_observation_id.nunique()),
        reference_catalog_entries=len(references),
        qualification=(
            "Compiled corrosion metrics with endpoint and censoring preserved. Physical specimen identity, "
            "test validity and underlying-observation redistribution rights are unresolved; no material "
            "ranking, standard acceptance rule or service-life model is inferred."
        ),
    )
    return frame

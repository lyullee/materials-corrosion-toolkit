"""Local, digest-pinned rows from a CC BY Co-Cr wear-corrosion dataset.

Workbook cells are preserved as source values with their sheet and row identity.
Formulas are kept as formula text and are never evaluated by this importer.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterator
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, StrictBool, StrictFloat, StrictInt, StrictStr

from .contracts import Contract, Evidence, canonical_digest

DATASET_ID = "zenodo-cocr-prosthesis-wear-corrosion"
DATASET_DOI = "10.5281/zenodo.21253453"
LICENSE_ID = "CC-BY-4.0"
SOURCE_ID = "zenodo_cocr_wear_corrosion_rows"
_ASSETS: dict[str, tuple[int, str, str]] = {
    "EIS CONTROL RAW DATA.xlsx": (
        73_998,
        "4be9a722c9b3a368333dc7a18b6ab860",
        "3bb5a8f205a6df0dc611b1083fc548dfb54073e6df08e2395ce404d6138642be",
    ),
    "EIS WEAR RAW DATA.xlsx": (
        80_856,
        "3cc2a95c15308b3ca87cb25dbc02065d",
        "478a8f6759fd132a63f7cdd028160928b14ab4ba794f43c9af309699cfbb0a50",
    ),
    "lpr control cocr.xlsx": (
        25_419,
        "5b0ae749d76b37c7a059684db91779f1",
        "edae34bff5bfc64b75fddc1e0876a2eb4fd78b17f77d89acef4e620a53b3d452",
    ),
    "LPR WEAR.xlsx": (
        26_382,
        "1f131699ea70c6407cdab8427baea8e6",
        "76101d802d48f36c60953fba6364fb2a36c34063bae6741c6e895c3bb22adb88",
    ),
    "LPR_Control_Converted.xlsx": (
        20_823,
        "52bbefbbdb119a3ed401fc21766ddaf5",
        "c11493e81284c1376db9f4b43b8524e35ef36c1b5c03eb50074c8b619a65c563",
    ),
    "PDP CONTROL VS WEAR.xlsx": (
        149_066,
        "a863cb3ad8fd67e870c9bf6d566f9233",
        "a54768e08504958ecdc167433ff99b1ce7ce5cce55e1e50fb23719c2b169969f",
    ),
}
_FILE_IDS = {
    "EIS CONTROL RAW DATA.xlsx": "c2259abe-d249-4879-bb3c-4a380aad6caa",
    "EIS WEAR RAW DATA.xlsx": "ec16408d-d04c-4c90-b453-c85372568dbb",
    "lpr control cocr.xlsx": "20223541-845a-403e-83eb-fed9f80fbf28",
    "LPR WEAR.xlsx": "fd21f6c4-bbb4-4e9e-9ec9-efac2c311ab4",
    "LPR_Control_Converted.xlsx": "703c6d48-fc45-4e31-af3d-d84e18beab25",
    "PDP CONTROL VS WEAR.xlsx": "f648f64c-57f5-4da7-8328-8d8ac19682e2",
}


class CoCrCorrosionReadAuthorization(Contract):
    """Caller declaration for CC BY attribution and local computation."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: StrictStr = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class CoCrWorkbookCell(Contract):
    """One nonblank Excel cell; coordinate and unmodified value type are preserved."""

    coordinate: StrictStr = Field(min_length=2)
    cell_kind: Literal["text", "number", "boolean", "date", "datetime", "time", "formula", "error"]
    value: StrictStr | StrictInt | StrictFloat | StrictBool


class CoCrCorrosionWorkbookRow(Contract):
    """One source workbook row bound to file digest, worksheet, attribution, and Evidence."""

    schema_version: Literal["matintegrity.zenodo_cocr_corrosion_workbook_row.v1"] = (
        "matintegrity.zenodo_cocr_corrosion_workbook_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: StrictStr = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    provider_filename: StrictStr
    provider_file_id: StrictStr
    provider_md5: str = Field(pattern=r"^[a-f0-9]{32}$")
    provider_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_bytes: StrictInt = Field(gt=0)
    worksheet_name: StrictStr = Field(min_length=1)
    provider_row_number: StrictInt = Field(ge=1)
    source_order: StrictInt = Field(ge=0)
    cells: tuple[CoCrWorkbookCell, ...]
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    formulas_evaluated: Literal[False] = False
    units_converted: Literal[False] = False
    corrosion_rate_inferred: Literal[False] = False
    remaining_life_inferred: Literal[False] = False
    failure_probability_inferred: Literal[False] = False


class CoCrWorksheetManifest(Contract):
    worksheet_name: StrictStr = Field(min_length=1)
    maximum_row: StrictInt = Field(ge=0)
    maximum_column: StrictInt = Field(ge=0)
    nonempty_row_count: StrictInt = Field(ge=0)
    formula_cell_count: StrictInt = Field(ge=0)


class CoCrWorkbookManifest(Contract):
    provider_filename: StrictStr = Field(min_length=1)
    provider_file_id: StrictStr = Field(min_length=1)
    provider_bytes: StrictInt = Field(gt=0)
    provider_md5: str = Field(pattern=r"^[a-f0-9]{32}$")
    provider_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    worksheets: tuple[CoCrWorksheetManifest, ...]


def _pinned_file(path: Path) -> tuple[int, str, str]:
    expected = _ASSETS.get(path.name)
    if expected is None or not path.is_file():
        raise ValueError("only the six catalogued Zenodo corrosion workbooks are accepted")
    expected_bytes, expected_md5, expected_sha256 = expected
    size = path.stat().st_size
    if size != expected_bytes:
        raise ValueError(f"provider byte count differs for {path.name}")
    md5 = hashlib.md5(usedforsecurity=False)
    sha256 = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(chunk)
            sha256.update(chunk)
    if md5.hexdigest() != expected_md5 or sha256.hexdigest() != expected_sha256:
        raise ValueError(f"provider digest differs for {path.name}")
    return size, md5.hexdigest(), sha256.hexdigest()


def _cell_value(value: Any, data_type: str) -> tuple[str, str | int | float | bool]:
    if data_type == "f":
        return "formula", str(value)
    if data_type == "e":
        return "error", str(value)
    if isinstance(value, bool):
        return "boolean", value
    if isinstance(value, datetime):
        return "datetime", value.isoformat()
    if isinstance(value, date):
        return "date", value.isoformat()
    if isinstance(value, time):
        return "time", value.isoformat()
    if isinstance(value, str):
        return "text", value
    if isinstance(value, int):
        return "number", value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("spreadsheet contains a non-finite numeric cell")
        return "number", value
    raise ValueError(f"unsupported workbook cell type: {type(value).__name__}")


def audit_zenodo_cocr_workbooks(directory: str | Path) -> tuple[CoCrWorkbookManifest, ...]:
    """Return structural workbook metadata only, without cell values."""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("XLSX reading requires the optional openpyxl dependency") from exc
    root = Path(directory)
    result: list[CoCrWorkbookManifest] = []
    for filename in _ASSETS:
        path = root / filename
        size, md5, sha256 = _pinned_file(path)
        workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
        sheets: list[CoCrWorksheetManifest] = []
        try:
            for worksheet in workbook.worksheets:
                nonempty_rows = 0
                formula_count = 0
                for row in worksheet.iter_rows(values_only=False):
                    cells = [cell for cell in row if cell.value is not None]
                    if cells:
                        nonempty_rows += 1
                        formula_count += sum(cell.data_type == "f" for cell in cells)
                sheets.append(CoCrWorksheetManifest(
                    worksheet_name=worksheet.title,
                    maximum_row=worksheet.max_row or 0,
                    maximum_column=worksheet.max_column or 0,
                    nonempty_row_count=nonempty_rows,
                    formula_cell_count=formula_count,
                ))
        finally:
            workbook.close()
        result.append(CoCrWorkbookManifest(
            provider_filename=filename,
            provider_file_id=_FILE_IDS[filename],
            provider_bytes=size,
            provider_md5=md5,
            provider_sha256=sha256,
            worksheets=tuple(sheets),
        ))
    return tuple(result)


def iter_zenodo_cocr_corrosion_rows(
    directory: str | Path,
    *,
    authorization: CoCrCorrosionReadAuthorization,
) -> Iterator[CoCrCorrosionWorkbookRow]:
    """Yield nonblank rows from all six selected workbooks in stable source order.

    Formula cells remain formula text because the workbook is opened with
    ``data_only=False``; formulas are not executed and units are not normalized.
    """
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    try:
        from openpyxl import load_workbook
        from openpyxl.utils import get_column_letter
    except ImportError as exc:
        raise RuntimeError("XLSX reading requires the optional openpyxl dependency") from exc
    root = Path(directory)
    auth_sha = canonical_digest(authorization.model_dump(mode="json"))
    source_order = 0
    for filename in _ASSETS:
        path = root / filename
        size, md5, sha256 = _pinned_file(path)
        workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
        try:
            for worksheet in workbook.worksheets:
                for row_number, row in enumerate(worksheet.iter_rows(values_only=False), start=1):
                    cells: list[CoCrWorkbookCell] = []
                    for column_number, cell in enumerate(row, start=1):
                        if cell.value is None:
                            continue
                        kind, value = _cell_value(cell.value, cell.data_type)
                        cells.append(CoCrWorkbookCell(
                            coordinate=f"{get_column_letter(column_number)}{row_number}",
                            cell_kind=kind,
                            value=value,
                        ))
                    if not cells:
                        continue
                    row_payload = [cell.model_dump(mode="json") for cell in cells]
                    row_sha = canonical_digest({
                        "dataset_id": DATASET_ID,
                        "provider_file_id": _FILE_IDS[filename],
                        "provider_sha256": sha256,
                        "worksheet": worksheet.title,
                        "row_number": row_number,
                        "cells": row_payload,
                        "authorization_sha256": auth_sha,
                    })
                    yield CoCrCorrosionWorkbookRow(
                        attribution=authorization.attribution,
                        authorization_sha256=auth_sha,
                        provider_filename=filename,
                        provider_file_id=_FILE_IDS[filename],
                        provider_md5=md5,
                        provider_sha256=sha256,
                        provider_bytes=size,
                        worksheet_name=worksheet.title,
                        provider_row_number=row_number,
                        source_order=source_order,
                        cells=tuple(cells),
                        source_row_sha256=row_sha,
                        evidence=Evidence(
                            source_id=DATASET_ID,
                            origin="open_dataset",
                            citation=(
                                f"{authorization.attribution}; https://doi.org/{DATASET_DOI}; "
                                "Zenodo archive file; CC BY 4.0"
                            ),
                            license_id=LICENSE_ID,
                            sha256=sha256,
                        ),
                    )
                    source_order += 1
        finally:
            workbook.close()

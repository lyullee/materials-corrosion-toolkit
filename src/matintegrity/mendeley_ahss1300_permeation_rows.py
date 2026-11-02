"""Typed local XLSX rows from the licensed MS-AHSS 1300 hydrogen test dataset."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterator
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, StrictBool, StrictFloat, StrictInt, StrictStr, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

DATASET_ID = "mendeley-ahss1300-hydrogen-permeation"
DATASET_DOI = "10.17632/tnsgf7v76z.1"
LICENSE_ID = "CC-BY-4.0"
SOURCE_ID = "mendeley_ahss1300_hydrogen_permeation_rows"
ARCHIVE_FILENAME = "Permeation_MS AHSS 1300.xlsx"
ARCHIVE_BYTES = 88_885
ARCHIVE_MD5 = "15316bf88b2e341e153bb6fecf7b823f"
ARCHIVE_SHA256 = "117d75a3f8329456732beada95b8f2be8bda688da88e6b8c7c83a9ee49698b3b"
PROVIDER_FILE_ID = "64121556-2ab2-4aec-8a20-4bc51d48ad44"


class AHSS1300PermeationReadAuthorization(Contract):
    """Caller declaration for CC BY attribution and local computational use."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: StrictStr = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]

    @model_validator(mode="after")
    def require_versioned_attribution(self):
        if DATASET_DOI not in self.attribution or "creativecommons.org/licenses/by/4.0" not in self.attribution:
            raise ValueError("attribution must identify the versioned dataset DOI and CC BY 4.0 license link")
        return self


class AHSS1300WorkbookCell(Contract):
    """A nonblank source cell with original coordinate, scalar type, and value."""

    coordinate: StrictStr = Field(min_length=2)
    cell_kind: Literal["text", "number", "boolean", "date", "datetime", "time", "formula", "error"]
    value: StrictStr | StrictInt | StrictFloat | StrictBool


class AHSS1300PermeationWorkbookRow(Contract):
    """One workbook row tied to the fixed provider file, worksheet, and source order."""

    schema_version: Literal["matintegrity.mendeley_ahss1300_permeation_row.v1"] = (
        "matintegrity.mendeley_ahss1300_permeation_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: StrictStr = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    provider_filename: Literal[ARCHIVE_FILENAME] = ARCHIVE_FILENAME
    provider_file_id: Literal[PROVIDER_FILE_ID] = PROVIDER_FILE_ID
    provider_bytes: StrictInt = ARCHIVE_BYTES
    provider_md5: Literal[ARCHIVE_MD5] = ARCHIVE_MD5
    provider_sha256: Literal[ARCHIVE_SHA256] = ARCHIVE_SHA256
    worksheet_name: StrictStr = Field(min_length=1)
    provider_row_number: StrictInt = Field(ge=1)
    source_order: StrictInt = Field(ge=0)
    cells: tuple[AHSS1300WorkbookCell, ...]
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    formulas_evaluated: Literal[False] = False
    units_converted: Literal[False] = False
    effective_diffusivity_inferred: Literal[False] = False
    remaining_life_inferred: Literal[False] = False
    failure_probability_inferred: Literal[False] = False


class AHSS1300WorksheetManifest(Contract):
    worksheet_name: StrictStr = Field(min_length=1)
    maximum_row: StrictInt = Field(ge=0)
    maximum_column: StrictInt = Field(ge=0)
    nonempty_row_count: StrictInt = Field(ge=0)
    formula_cell_count: StrictInt = Field(ge=0)


class AHSS1300WorkbookAuditRequest(Contract):
    """Request a metadata-only audit of the exact local, pinned workbook."""

    local_workbook_path: StrictStr = Field(min_length=1)
    authorization: AHSS1300PermeationReadAuthorization


def _validate_archive(path: Path) -> None:
    if path.name != ARCHIVE_FILENAME or not path.is_file():
        raise ValueError("only the catalogued AHSS 1300 XLSX file is accepted")
    if path.stat().st_size != ARCHIVE_BYTES:
        raise ValueError("AHSS 1300 file byte count differs from the provider metadata")
    md5 = hashlib.md5(usedforsecurity=False)
    sha256 = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(block)
            sha256.update(block)
    if md5.hexdigest() != ARCHIVE_MD5 or sha256.hexdigest() != ARCHIVE_SHA256:
        raise ValueError("AHSS 1300 XLSX digest differs from the provider metadata")


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
            raise ValueError("workbook contains a non-finite numeric cell")
        return "number", value
    raise ValueError(f"unsupported workbook cell type: {type(value).__name__}")


def audit_mendeley_ahss1300_workbook(path: str | Path) -> tuple[AHSS1300WorksheetManifest, ...]:
    """Return sheet structure and formula counts without exposing cell values."""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("XLSX import requires the optional openpyxl dependency") from exc
    workbook_path = Path(path)
    _validate_archive(workbook_path)
    workbook = load_workbook(workbook_path, read_only=True, data_only=False, keep_links=False)
    result: list[AHSS1300WorksheetManifest] = []
    try:
        for worksheet in workbook.worksheets:
            nonempty_rows = 0
            formulas = 0
            for row in worksheet.iter_rows(values_only=False):
                populated = [cell for cell in row if cell.value is not None]
                if populated:
                    nonempty_rows += 1
                    formulas += sum(cell.data_type == "f" for cell in populated)
            result.append(AHSS1300WorksheetManifest(
                worksheet_name=worksheet.title,
                maximum_row=worksheet.max_row or 0,
                maximum_column=worksheet.max_column or 0,
                nonempty_row_count=nonempty_rows,
                formula_cell_count=formulas,
            ))
    finally:
        workbook.close()
    return tuple(result)


def evaluate_ahss1300_workbook_audit(request: AHSS1300WorkbookAuditRequest) -> Calculation:
    """Return only pinned source metadata and sheet dimensions through the registry.

    Cell values remain available only from the explicit local streaming helper; they
    are not embedded in this registry calculation or its serialized assessment.
    """
    manifests = audit_mendeley_ahss1300_workbook(request.local_workbook_path)
    return Calculation(values={
        "model_id": "data.mendeley_ahss1300_hydrogen_permeation_workbook_audit",
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "license_id": LICENSE_ID,
        "provider_file_id": PROVIDER_FILE_ID,
        "provider_filename": ARCHIVE_FILENAME,
        "provider_bytes": ARCHIVE_BYTES,
        "provider_md5": ARCHIVE_MD5,
        "provider_sha256": ARCHIVE_SHA256,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "worksheet_manifests": [row.model_dump(mode="json") for row in manifests],
        "cell_values_returned": False,
        "formulas_evaluated": False,
        "units_converted": False,
        "material_properties_inferred": False,
        "qualification_claimed": False,
    }, notes=(
        "The registry endpoint returns worksheet dimensions and formula counts only; it does not return workbook cell contents.",
        "Use iter_mendeley_ahss1300_permeation_rows for an explicitly authorized local stream of source-ordered typed rows.",
        "This audit does not interpret worksheet columns or infer hydrogen transport properties.",
    ))


def specifications() -> tuple[ModelSpec, ...]:
    return (
        ModelSpec(
            model_id="data.mendeley_ahss1300_hydrogen_permeation_workbook_audit",
            input_type=AHSS1300WorkbookAuditRequest,
            evaluator=evaluate_ahss1300_workbook_audit,
            units={
                "provider_bytes": "byte",
                "worksheet_manifests[].maximum_row": "1",
                "worksheet_manifests[].maximum_column": "1",
                "worksheet_manifests[].nonempty_row_count": "1",
                "worksheet_manifests[].formula_cell_count": "1",
            },
            assumptions=(
                "Only the exact provider-pinned Mendeley workbook is accepted by filename, size, MD5 and SHA-256.",
                "The registry evaluator returns workbook and worksheet metadata only; raw cell values are not included in its result.",
                "The provider declares CC BY 4.0; users must preserve attribution and review possible third-party content before reuse or redistribution.",
                "Worksheet structure is not a semantic mapping: units, row meaning, specimen hierarchy and current-ramp interpretation require caller review.",
                "No hydrogen diffusivity, trapping, embrittlement threshold, remaining life, probability or service qualification is inferred.",
            ),
            source_ids=(SOURCE_ID,),
            qualification="data_import",
        ),
    )
def iter_mendeley_ahss1300_permeation_rows(
    path: str | Path,
    *,
    authorization: AHSS1300PermeationReadAuthorization,
) -> Iterator[AHSS1300PermeationWorkbookRow]:
    """Yield nonempty workbook rows while preserving sheet, row, and cell identities.

    The workbook is read with ``data_only=False``. Formula cells are returned as
    formula text; this importer does not evaluate formulas or normalize units.
    """
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    try:
        from openpyxl import load_workbook
        from openpyxl.utils import get_column_letter
    except ImportError as exc:
        raise RuntimeError("XLSX import requires the optional openpyxl dependency") from exc
    workbook_path = Path(path)
    _validate_archive(workbook_path)
    auth_sha = canonical_digest(authorization.model_dump(mode="json"))
    source_order = 0
    workbook = load_workbook(workbook_path, read_only=True, data_only=False, keep_links=False)
    try:
        for worksheet in workbook.worksheets:
            for row_number, row in enumerate(worksheet.iter_rows(values_only=False), start=1):
                cells: list[AHSS1300WorkbookCell] = []
                for column_number, cell in enumerate(row, start=1):
                    if cell.value is None:
                        continue
                    kind, value = _cell_value(cell.value, cell.data_type)
                    cells.append(AHSS1300WorkbookCell(
                        coordinate=f"{get_column_letter(column_number)}{row_number}",
                        cell_kind=kind,
                        value=value,
                    ))
                if not cells:
                    continue
                serialized_cells = [cell.model_dump(mode="json") for cell in cells]
                row_sha = canonical_digest({
                    "dataset_id": DATASET_ID,
                    "provider_file_id": PROVIDER_FILE_ID,
                    "provider_sha256": ARCHIVE_SHA256,
                    "worksheet": worksheet.title,
                    "row_number": row_number,
                    "cells": serialized_cells,
                    "authorization_sha256": auth_sha,
                })
                yield AHSS1300PermeationWorkbookRow(
                    attribution=authorization.attribution,
                    authorization_sha256=auth_sha,
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
                            "Mendeley Data file; CC BY 4.0"
                        ),
                        license_id=LICENSE_ID,
                        sha256=ARCHIVE_SHA256,
                    ),
                )
                source_order += 1
    finally:
        workbook.close()

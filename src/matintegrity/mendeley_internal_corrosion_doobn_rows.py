"""Local-only typed workbook rows for an openly licensed internal-corrosion DOOBN dataset."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

DATASET_ID = "mendeley-internal-corrosion-doobn"
DATASET_DOI = "10.17632/g5h5gktwnd.3"
DATASET_URL = "https://data.mendeley.com/datasets/g5h5gktwnd/3"
LICENSE_ID = "CC-BY-4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
SOURCE_ID = "mendeley_internal_corrosion_doobn_xlsx_rows"
MODEL_ID = "data.mendeley_internal_corrosion_doobn_typed_rows"
WORKBOOK_FILENAME = "Internal Corrosion - Export Gas Data - 2015 to 2020.xlsx"
WORKBOOK_BYTES = 271763
WORKBOOK_SHA256 = "44f03e17d5669d20ed3ea6a35132e89a68b9e6755be5a5f87dca421830bff0b6"
SHEET_LAYOUT = (("Export Gas Data", 2919, 18),)


class InternalCorrosionReadAuthorization(Contract):
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]

    @model_validator(mode="after")
    def attribution_pins_dataset(self):
        if not self.attribution.strip() or DATASET_DOI not in self.attribution:
            raise ValueError("attribution must cite the exact Mendeley dataset version DOI")
        return self


class InternalCorrosionWorkbookCell(Contract):
    column_number: StrictInt = Field(ge=1, le=256)
    address: str = Field(min_length=2, max_length=16)
    cell_type: str = Field(min_length=1, max_length=8)
    raw_value: Any


class InternalCorrosionWorkbookRow(Contract):
    schema_version: Literal["matintegrity.mendeley_internal_corrosion_workbook_row.v1"] = (
        "matintegrity.mendeley_internal_corrosion_workbook_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_filename: Literal[WORKBOOK_FILENAME] = WORKBOOK_FILENAME
    source_file_bytes: StrictInt = Field(gt=0)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    worksheet_name: Literal["Export Gas Data"] = "Export Gas Data"
    provider_row_number: StrictInt = Field(ge=1, le=2919)
    cells: tuple[InternalCorrosionWorkbookCell, ...] = Field(min_length=1, max_length=256)
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence

    @model_validator(mode="after")
    def validate_lineage(self):
        if self.evidence.source_id != DATASET_ID or self.evidence.license_id != LICENSE_ID:
            raise ValueError("row Evidence must retain the versioned dataset identity and license")
        if self.evidence.sha256 != self.source_file_sha256:
            raise ValueError("row Evidence must pin the complete workbook SHA-256")
        if DATASET_DOI not in self.evidence.citation:
            raise ValueError("row Evidence citation must identify the exact dataset version")
        if len({cell.column_number for cell in self.cells}) != len(self.cells):
            raise ValueError("a row cannot contain duplicate worksheet columns")
        expected = canonical_digest(self.model_dump(mode="json", exclude={"source_row_sha256"}))
        if self.source_row_sha256 != expected:
            raise ValueError("row digest must cover typed cells and complete provenance")
        return self


class InternalCorrosionWorkbookAuditRequest(Contract):
    local_workbook_path: str = Field(min_length=1)
    authorization: InternalCorrosionReadAuthorization


def _verify_workbook(path: Path) -> tuple[int, str]:
    if path.name != WORKBOOK_FILENAME or not path.is_file():
        raise ValueError("only the pinned local version-3 workbook is accepted")
    size = path.stat().st_size
    if size != WORKBOOK_BYTES:
        raise ValueError("local workbook size differs from the official Mendeley file record")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    actual = digest.hexdigest()
    if actual != WORKBOOK_SHA256:
        raise ValueError("local workbook digest differs from the official version-3 file digest")
    return size, actual


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def iter_internal_corrosion_doobn_rows(
    path: str | Path, *, authorization: InternalCorrosionReadAuthorization
) -> Iterator[InternalCorrosionWorkbookRow]:
    """Yield original nonempty workbook rows after exact version, size and digest checks.

    The importer preserves cell coordinates, storage types, formulas-as-text, blank cells,
    and row order. It does not interpret node names, elicit or validate probabilities, or
    execute a Bayesian network.
    """
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install matintegrity[science] to read XLSX workbooks") from exc
    source = Path(path)
    size, digest = _verify_workbook(source)
    workbook = load_workbook(source, read_only=True, data_only=False, keep_links=False)
    auth_digest = canonical_digest(authorization.model_dump(mode="json"))
    try:
        actual_layout = tuple((ws.title, ws.max_row, ws.max_column) for ws in workbook.worksheets)
        if actual_layout != SHEET_LAYOUT:
            raise ValueError("worksheet names or dimensions differ from the reviewed version-3 layout")
        sheet = workbook["Export Gas Data"]
        for row_number in range(1, sheet.max_row + 1):
            cells = tuple(
                InternalCorrosionWorkbookCell(
                    column_number=column,
                    address=cell.coordinate,
                    cell_type=cell.data_type,
                    raw_value=_json_value(cell.value),
                )
                for column, cell in enumerate(
                    (sheet.cell(row_number, col) for col in range(1, sheet.max_column + 1)),
                    start=1,
                )
            )
            if not any(cell.raw_value is not None for cell in cells):
                continue
            evidence = Evidence(
                source_id=DATASET_ID,
                origin="open_dataset",
                citation=f"{authorization.attribution}; dataset DOI {DATASET_DOI}; CC BY 4.0",
                license_id=LICENSE_ID,
                sha256=digest,
            )
            fields = dict(
                attribution=authorization.attribution,
                authorization_sha256=auth_digest,
                source_file_bytes=size,
                source_file_sha256=digest,
                worksheet_name=sheet.title,
                provider_row_number=row_number,
                cells=cells,
                evidence=evidence,
            )
            provisional = InternalCorrosionWorkbookRow.model_construct(
                **fields, source_row_sha256="0" * 64
            )
            row_digest = canonical_digest(
                provisional.model_dump(mode="json", exclude={"source_row_sha256"})
            )
            yield InternalCorrosionWorkbookRow.model_validate(
                fields | {"source_row_sha256": row_digest}
            )
    finally:
        workbook.close()


def audit_internal_corrosion_doobn_workbook(
    request: InternalCorrosionWorkbookAuditRequest,
) -> Calculation:
    """Report pinned workbook structure without returning cell values."""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install matintegrity[science] to read XLSX workbooks") from exc
    source = Path(request.local_workbook_path)
    size, digest = _verify_workbook(source)
    workbook = load_workbook(source, read_only=True, data_only=False, keep_links=False)
    try:
        sheets = []
        for sheet in workbook.worksheets:
            nonempty_rows = 0
            for row in sheet.iter_rows():
                if any(cell.value is not None for cell in row):
                    nonempty_rows += 1
            sheets.append({
                "name": sheet.title,
                "max_row": sheet.max_row,
                "max_column": sheet.max_column,
                "nonempty_rows": nonempty_rows,
            })
        return Calculation(values={
            "model_id": MODEL_ID,
            "dataset_id": DATASET_ID,
            "dataset_doi": DATASET_DOI,
            "license_id": LICENSE_ID,
            "authorization_sha256": canonical_digest(
                request.authorization.model_dump(mode="json")
            ),
            "source_file_bytes": size,
            "source_file_sha256": digest,
            "sheets": sheets,
            "cell_values_emitted": False,
            "network_model_executed": False,
            "status": "audited_local_only",
        })
    finally:
        workbook.close()


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=InternalCorrosionWorkbookAuditRequest,
        evaluator=audit_internal_corrosion_doobn_workbook,
        units={"source_file_bytes": "byte", "max_row": "1", "max_column": "1"},
        assumptions=(
            "Audit the exact Mendeley Data version 3 workbook by official file size and SHA-256.",
            "Metadata-only audit returns sheet structure but never emits source cell values.",
            "Row iteration is local-only, caller-attributed and preserves source rows without semantic interpretation.",
            "The published data can include third-party material; permission and provenance checks remain caller responsibility before reuse.",
            "The reader does not execute or validate the associated Dynamic Object-Oriented Bayesian Network.",
        ),
        source_ids=(SOURCE_ID,),
        version="1.0.0",
    ),)

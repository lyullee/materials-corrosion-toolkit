"""Local-only typed cell access for the CC0 Dryad formate-packer corrosion workbook."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest

DATASET_ID = "dryad_formate_packer_h2s_co2_corrosion"
DATASET_DOI = "10.5061/dryad.p1mf340"
ARTICLE_DOI = "10.1098/rsos.180405"
ZENODO_RECORD_ID = "4937236"
RECORD_URL = "https://datadryad.org/dataset/doi%3A10.5061%2Fdryad.p1mf340"
ZENODO_RECORD_URL = "https://zenodo.org/records/4937236"
LICENSE_ID = "CC0-1.0"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
SOURCE_ID = "dryad_formate_packer_corrosion_workbook_rows"
WORKBOOK_FILENAME = "Data 1.xlsx"
WORKBOOK_BYTES = 13414
PUBLISHER_MD5 = "ab545c29253c47eac2cf4996930f1d94"
LOCAL_SHA256 = "9f524b0ad274caba47deb1f14a70a6841474a82353e288f6b83e1455f7bfca15"
WORKSHEET_LAYOUT = (("Sheet1", 97, 23),)


class FormatePackerReadAuthorization(Contract):
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    article_doi: Literal[ARTICLE_DOI] = ARTICLE_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]

    @model_validator(mode="after")
    def attribution_has_lineage(self):
        value = self.attribution.strip()
        if not value or DATASET_DOI not in value or ARTICLE_DOI not in value:
            raise ValueError("attribution must cite both the dataset and its associated article")
        return self


class FormatePackerWorkbookCell(Contract):
    column_number: StrictInt = Field(ge=1, le=256)
    address: str = Field(min_length=2, max_length=16)
    cell_type: str = Field(min_length=1, max_length=8)
    value: Any


class FormatePackerWorkbookRow(Contract):
    schema_version: Literal["matintegrity.dryad_formate_packer_workbook_row.v1"] = (
        "matintegrity.dryad_formate_packer_workbook_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    article_doi: Literal[ARTICLE_DOI] = ARTICLE_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_filename: Literal[WORKBOOK_FILENAME] = WORKBOOK_FILENAME
    source_file_bytes: StrictInt = Field(gt=0)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    worksheet_name: str = Field(min_length=1, max_length=128)
    provider_row_number: StrictInt = Field(ge=1)
    source_order: StrictInt = Field(ge=0)
    cells: tuple[FormatePackerWorkbookCell, ...] = Field(min_length=1, max_length=256)
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence

    @model_validator(mode="after")
    def validate_provenance(self):
        if self.evidence.source_id != DATASET_ID or self.evidence.license_id != LICENSE_ID:
            raise ValueError("row Evidence must identify the CC0 Dryad record")
        if self.evidence.sha256 != self.source_file_sha256:
            raise ValueError("row Evidence must pin the local workbook SHA-256")
        if DATASET_DOI not in self.evidence.citation or ARTICLE_DOI not in self.evidence.citation:
            raise ValueError("row Evidence must retain dataset and article DOI citations")
        if self.source_order != self.provider_row_number - 1:
            raise ValueError("source order must preserve original one-based worksheet row order")
        if len({cell.column_number for cell in self.cells}) != len(self.cells):
            raise ValueError("a row may contain no duplicate worksheet columns")
        if self.source_row_sha256 != canonical_digest(self.model_dump(mode="json", exclude={"source_row_sha256"})):
            raise ValueError("row digest must cover the complete typed source row and provenance")
        return self


class FormatePackerWorkbookAuditRequest(Contract):
    local_workbook_path: str = Field(min_length=1)
    authorization: FormatePackerReadAuthorization


def _verify(path: Path) -> tuple[int, str]:
    if path.name != WORKBOOK_FILENAME or not path.is_file():
        raise ValueError("only the pinned local Dryad workbook is accepted")
    size = path.stat().st_size
    if size != WORKBOOK_BYTES:
        raise ValueError("local workbook size differs from the provider file record")
    md5 = hashlib.md5(usedforsecurity=False)
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(block)
            sha.update(block)
    if md5.hexdigest() != PUBLISHER_MD5:
        raise ValueError("local file MD5 differs from the provider asset checksum")
    if sha.hexdigest() != LOCAL_SHA256:
        raise ValueError("local file SHA-256 differs from the reviewed local pin")
    return size, sha.hexdigest()


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def iter_dryad_formate_packer_rows(
    path: str | Path, *, authorization: FormatePackerReadAuthorization
) -> Iterator[FormatePackerWorkbookRow]:
    """Yield nonempty source rows with every cell, coordinate, type and row order preserved.

    This structural importer does not classify figure blocks, infer experimental conditions,
    execute formulas, or convert units. Numeric observations remain local to the caller.
    """
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install matintegrity[science] to read XLSX workbooks") from exc
    source = Path(path)
    size, digest = _verify(source)
    book = load_workbook(source, read_only=True, data_only=False, keep_links=False)
    auth_digest = canonical_digest(authorization.model_dump(mode="json"))
    try:
        actual = tuple((sheet.title, sheet.max_row, sheet.max_column) for sheet in book.worksheets)
        if actual != WORKSHEET_LAYOUT:
            raise ValueError("worksheet names or dimensions differ from the reviewed workbook layout")
        sheet = book["Sheet1"]
        order = 0
        for row_number in range(1, sheet.max_row + 1):
            source_cells = [sheet.cell(row_number, col) for col in range(1, sheet.max_column + 1)]
            if not any(cell.value is not None for cell in source_cells):
                continue
            cells = tuple(FormatePackerWorkbookCell(
                column_number=col,
                address=cell.coordinate,
                cell_type=cell.data_type,
                value=_json_value(cell.value),
            ) for col, cell in enumerate(source_cells, 1))
            evidence = Evidence(
                source_id=DATASET_ID,
                origin="open_dataset",
                citation=f"{authorization.attribution}; dataset DOI {DATASET_DOI}; article DOI {ARTICLE_DOI}; CC0-1.0",
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
                source_order=row_number - 1,
                cells=cells,
                evidence=evidence,
            )
            candidate = FormatePackerWorkbookRow.model_construct(**fields, source_row_sha256="0" * 64)
            row_digest = canonical_digest(candidate.model_dump(mode="json", exclude={"source_row_sha256"}))
            yield FormatePackerWorkbookRow.model_validate(fields | {"source_row_sha256": row_digest})
            order += 1
    finally:
        book.close()


def audit_dryad_formate_packer_workbook(request: FormatePackerWorkbookAuditRequest) -> Calculation:
    """Return workbook structure and hashes without returning its cell values."""
    path = Path(request.local_workbook_path)
    size, digest = _verify(path)
    rows = tuple(iter_dryad_formate_packer_rows(path, authorization=request.authorization))
    return Calculation(values={
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "article_doi": ARTICLE_DOI,
        "license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "source_filename": path.name,
        "source_file_bytes": size,
        "source_file_sha256": digest,
        "worksheet_layout": [{"name": name, "rows": rows_count, "columns": columns}
                             for name, rows_count, columns in WORKSHEET_LAYOUT],
        "nonempty_source_rows": len(rows),
        "source_row_sha256": [row.source_row_sha256 for row in rows],
        "local_only": True,
        "numeric_values_emitted": False,
        "conditions_or_units_inferred": False,
        "status": "audited_local_only",
    })

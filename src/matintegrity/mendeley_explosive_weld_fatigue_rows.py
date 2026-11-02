"""Local-only typed workbook rows for explosively welded multilayer-plate fatigue data."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterator
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

DATASET_ID = "mendeley-explosive-weld-multilayer-fatigue"
DATASET_DOI = "10.17632/mc8bc9tm59.1"
LICENSE_ID = "CC-BY-4.0"
MODEL_ID = "data.mendeley_explosive_weld_multilayer_fatigue_typed_rows"
SOURCE_ID = "mendeley_explosive_weld_multilayer_fatigue_rows"
CALLER_MAPPING_SOURCE_ID = "caller_explosive_weld_workbook_column_mapping"
MAPPED_MODEL_ID = "data.mendeley_explosive_weld_multilayer_fatigue_mapped_rows"
FILENAME = "MultilayerPlatesData.xlsx"
FILE_METADATA = {
    FILENAME: {
        "file_id": "a61942c3-e97e-4bfd-ba1d-573d4b32eddd",
        "bytes": 1393400,
        "sha256": "3d8243ee1ec3ada1d98d401185eed86edb0817e31305d3c378b056cb5556082a",
    }
}


class ExplosiveWeldFatigueReadAuthorization(Contract):
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]

    @model_validator(mode="after")
    def attribution_pins_dataset(self):
        if DATASET_DOI not in self.attribution:
            raise ValueError("attribution must cite the exact versioned dataset DOI")
        return self


class ExplosiveWeldFatigueWorkbookCell(Contract):
    column_number: StrictInt = Field(ge=1, le=512)
    address: str = Field(min_length=2, max_length=16)
    cell_type: str = Field(min_length=1, max_length=8)
    raw_value: Any


class ExplosiveWeldFatigueWorkbookRow(Contract):
    schema_version: Literal["matintegrity.mendeley_explosive_weld_fatigue_row.v1"] = (
        "matintegrity.mendeley_explosive_weld_fatigue_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_filename: Literal[FILENAME] = FILENAME
    provider_file_id: str = Field(min_length=1, max_length=128)
    source_file_bytes: StrictInt = Field(gt=0)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    worksheet_name: str = Field(min_length=1, max_length=128)
    provider_row_number: StrictInt = Field(ge=1)
    cells: tuple[ExplosiveWeldFatigueWorkbookCell, ...] = Field(min_length=1, max_length=512)
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence

    @model_validator(mode="after")
    def validate_lineage(self):
        metadata = FILE_METADATA[FILENAME]
        if (self.provider_file_id != metadata["file_id"] or self.source_file_bytes != metadata["bytes"]
                or self.source_file_sha256 != metadata["sha256"]):
            raise ValueError("row file lineage differs from official provider metadata")
        if self.evidence.source_id != DATASET_ID or self.evidence.license_id != LICENSE_ID:
            raise ValueError("Evidence must retain dataset identity and CC BY license")
        if self.evidence.sha256 != self.source_file_sha256 or DATASET_DOI not in self.evidence.citation:
            raise ValueError("Evidence must cite the dataset and pin the workbook digest")
        if len({cell.column_number for cell in self.cells}) != len(self.cells):
            raise ValueError("row cell columns must be unique")
        expected = canonical_digest(self.model_dump(mode="json", exclude={"source_row_sha256"}))
        if self.source_row_sha256 != expected:
            raise ValueError("row digest must cover cell contents and complete source provenance")
        return self


class ExplosiveWeldFatigueAuditRequest(Contract):
    local_data_directory: str = Field(min_length=1)
    authorization: ExplosiveWeldFatigueReadAuthorization


class ExplosiveWeldFatigueColumnMapping(Contract):
    """Caller-reviewed identity, unit and role for one exact workbook column."""

    column_number: StrictInt = Field(ge=1, le=512)
    field_id: str = Field(min_length=1)
    caller_meaning: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    role: Literal["record_id", "condition", "measurement", "derived_formula", "metadata", "unclassified"]
    expected_header_value: Any
    mapping_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    mapping_reviewed: Literal[True]


class ExplosiveWeldFatigueWorksheetMapping(Contract):
    """Caller-selected row span and column map for one exact worksheet."""

    worksheet_name: str = Field(min_length=1, max_length=128)
    header_row_number: StrictInt = Field(ge=1)
    data_start_row: StrictInt = Field(ge=1)
    data_end_row: StrictInt = Field(ge=1)
    columns: tuple[ExplosiveWeldFatigueColumnMapping, ...] = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def validate_mapping(self):
        if self.data_start_row <= self.header_row_number or self.data_end_row < self.data_start_row:
            raise ValueError("caller must select an ordered data span strictly below the reviewed header row")
        column_ids = [item.column_number for item in self.columns]
        field_ids = [item.field_id for item in self.columns]
        if len(column_ids) != len(set(column_ids)) or len(field_ids) != len(set(field_ids)):
            raise ValueError("mapped columns and caller field IDs must be unique within a worksheet")
        return self


class ExplosiveWeldFatigueMappedImportRequest(Contract):
    """Exact local asset plus explicit, evidence-bound interpretation mapping."""

    local_data_directory: str = Field(min_length=1)
    authorization: ExplosiveWeldFatigueReadAuthorization
    worksheet_mappings: tuple[ExplosiveWeldFatigueWorksheetMapping, ...] = Field(min_length=1, max_length=64)
    maximum_output_rows: StrictInt = Field(ge=1, le=10_000)
    maximum_output_cells: StrictInt = Field(ge=1, le=100_000)
    mapping_reviewed: Literal[True]

    @model_validator(mode="after")
    def unique_sheets(self):
        names = [item.worksheet_name for item in self.worksheet_mappings]
        if len(names) != len(set(names)):
            raise ValueError("worksheet mappings must name unique sheets")
        return self


class ExplosiveWeldFatigueObservationField(Contract):
    field_id: str = Field(min_length=1)
    caller_meaning: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    role: Literal["record_id", "condition", "measurement", "derived_formula", "metadata", "unclassified"]
    column_number: StrictInt = Field(ge=1)
    cell_address: str = Field(min_length=2, max_length=16)
    cell_type: str = Field(min_length=1, max_length=8)
    raw_value: Any
    source_header_value: Any
    mapping_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)


class ExplosiveWeldFatigueMappedObservationRow(Contract):
    schema_version: Literal["matintegrity.mendeley_explosive_weld_fatigue_mapped_row.v1"] = (
        "matintegrity.mendeley_explosive_weld_fatigue_mapped_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    mapping_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_filename: Literal[FILENAME] = FILENAME
    provider_file_id: str = Field(min_length=1, max_length=128)
    source_file_bytes: StrictInt = Field(gt=0)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    worksheet_name: str = Field(min_length=1, max_length=128)
    header_row_number: StrictInt = Field(ge=1)
    provider_row_number: StrictInt = Field(ge=1)
    fields: tuple[ExplosiveWeldFatigueObservationField, ...] = Field(min_length=1, max_length=512)
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence

    @model_validator(mode="after")
    def validate_provenance(self):
        meta = FILE_METADATA[FILENAME]
        if (self.provider_file_id != meta["file_id"] or self.source_file_bytes != meta["bytes"]
                or self.source_file_sha256 != meta["sha256"]):
            raise ValueError("mapped row asset lineage differs from the pinned provider record")
        if self.evidence.source_id != DATASET_ID or self.evidence.sha256 != self.source_file_sha256:
            raise ValueError("mapped row Evidence must bind the exact dataset file digest")
        if self.evidence.license_id != LICENSE_ID or DATASET_DOI not in self.evidence.citation:
            raise ValueError("mapped row Evidence must preserve the dataset citation and license")
        if len({row.field_id for row in self.fields}) != len(self.fields):
            raise ValueError("mapped observation field IDs must be unique per row")
        expected = canonical_digest(self.model_dump(mode="json", exclude={"source_row_sha256"}))
        if self.source_row_sha256 != expected:
            raise ValueError("mapped row digest must cover source cells, caller mapping and provenance")
        return self


def _verify(path: Path) -> tuple[dict[str, Any], str]:
    metadata = FILE_METADATA.get(path.name)
    if metadata is None or not path.is_file():
        raise ValueError("only the pinned Mendeley version-1 workbook is accepted")
    if path.stat().st_size != metadata["bytes"]:
        raise ValueError("local workbook size differs from the official file record")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    actual = digest.hexdigest()
    if actual != metadata["sha256"]:
        raise ValueError("local workbook SHA-256 differs from the official file digest")
    return metadata, actual


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def iter_explosive_weld_fatigue_rows(
    directory: str | Path, *, authorization: ExplosiveWeldFatigueReadAuthorization,
) -> Iterator[ExplosiveWeldFatigueWorkbookRow]:
    """Yield nonempty source rows after provider identity and SHA-256 checks.

    The reader preserves native cells and source order; it does not interpret sheet labels,
    units, stack-up identities, fatigue-life definitions, or material equivalence.
    """
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install matintegrity[science] to read XLSX workbooks") from exc
    path = Path(directory) / FILENAME
    metadata, digest = _verify(path)
    auth_digest = canonical_digest(authorization.model_dump(mode="json"))
    workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
    try:
        for sheet in workbook.worksheets:
            for row_number, source_cells in enumerate(sheet.iter_rows(), start=1):
                if not any(cell.value is not None for cell in source_cells):
                    continue
                cells = tuple(ExplosiveWeldFatigueWorkbookCell(
                    column_number=column, address=cell.coordinate, cell_type=cell.data_type,
                    raw_value=_json_value(cell.value),
                ) for column, cell in enumerate(source_cells, start=1))
                evidence = Evidence(
                    source_id=DATASET_ID, origin="open_dataset",
                    citation=f"{authorization.attribution}; dataset DOI {DATASET_DOI}; CC BY 4.0",
                    license_id=LICENSE_ID, sha256=digest,
                )
                fields = dict(
                    attribution=authorization.attribution,
                    authorization_sha256=auth_digest,
                    source_filename=FILENAME,
                    provider_file_id=metadata["file_id"],
                    source_file_bytes=metadata["bytes"],
                    source_file_sha256=digest,
                    worksheet_name=sheet.title,
                    provider_row_number=row_number,
                    cells=cells,
                    evidence=evidence,
                )
                provisional = ExplosiveWeldFatigueWorkbookRow.model_construct(
                    **fields, source_row_sha256="0" * 64
                )
                row_digest = canonical_digest(
                    provisional.model_dump(mode="json", exclude={"source_row_sha256"})
                )
                yield ExplosiveWeldFatigueWorkbookRow.model_validate(
                    fields | {"source_row_sha256": row_digest}
                )
    finally:
        workbook.close()


def audit_explosive_weld_fatigue_directory(
    request: ExplosiveWeldFatigueAuditRequest,
) -> Calculation:
    """Return workbook and sheet dimensions without emitting cell values."""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install matintegrity[science] to read XLSX workbooks") from exc
    path = Path(request.local_data_directory) / FILENAME
    metadata, digest = _verify(path)
    workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
    try:
        sheets = []
        for sheet in workbook.worksheets:
            nonempty_rows = sum(1 for row in sheet.iter_rows() if any(c.value is not None for c in row))
            sheets.append({"name": sheet.title, "rows": sheet.max_row,
                           "columns": sheet.max_column, "nonempty_rows": nonempty_rows})
    finally:
        workbook.close()
    return Calculation(values={
        "model_id": MODEL_ID, "dataset_id": DATASET_ID, "dataset_doi": DATASET_DOI,
        "license_id": LICENSE_ID,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "file": {"filename": FILENAME, "provider_file_id": metadata["file_id"],
                 "bytes": metadata["bytes"], "sha256": digest, "sheets": sheets},
        "cell_values_emitted": False, "worksheet_semantics_interpreted": False,
        "fatigue_or_integrity_model_executed": False, "status": "audited_local_only",
    })


def import_explosive_weld_fatigue_mapped_rows(
    request: ExplosiveWeldFatigueMappedImportRequest,
) -> Calculation:
    """Extract caller-selected rows using only an explicit, header-pinned column map.

    Cells are read with formulas preserved. This function does not discover headers,
    convert units, evaluate formulas, identify specimen groups, or fit fatigue relations.
    """
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install matintegrity[science] to read XLSX workbooks") from exc
    path = Path(request.local_data_directory) / FILENAME
    metadata, digest = _verify(path)
    request_digest = canonical_digest(request.model_dump(mode="json"))
    authorization_digest = canonical_digest(request.authorization.model_dump(mode="json"))
    mapping_digest = canonical_digest({
        "mapping_reviewed": request.mapping_reviewed,
        "worksheet_mappings": [row.model_dump(mode="json") for row in request.worksheet_mappings],
    })
    workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
    rows: list[ExplosiveWeldFatigueMappedObservationRow] = []
    try:
        sheets = {sheet.title: sheet for sheet in workbook.worksheets}
        requested_rows = sum(
            sheet_map.data_end_row - sheet_map.data_start_row + 1
            for sheet_map in request.worksheet_mappings
        )
        requested_cells = sum(
            (sheet_map.data_end_row - sheet_map.data_start_row + 1) * len(sheet_map.columns)
            for sheet_map in request.worksheet_mappings
        )
        if (requested_rows > request.maximum_output_rows
                or requested_cells > request.maximum_output_cells):
            return Calculation(status="out_of_scope", values={
                "reason": "caller_mapped_output_budget_exceeded",
                "requested_output_rows": requested_rows,
                "maximum_output_rows": request.maximum_output_rows,
                "requested_output_cells": requested_cells,
                "maximum_output_cells": request.maximum_output_cells,
                "materialized_rows": 0,
                "raw_rows_dropped": False,
            })
        for sheet_map in request.worksheet_mappings:
            sheet = sheets.get(sheet_map.worksheet_name)
            if sheet is None:
                return Calculation(status="out_of_scope", values={
                    "reason": "caller_mapped_worksheet_not_in_pinned_workbook",
                    "worksheet_name": sheet_map.worksheet_name,
                    "request_sha256": request_digest,
                    "source_file_sha256": digest,
                    "probability_inferred": False,
                })
            if sheet_map.data_end_row > sheet.max_row or any(
                col.column_number > sheet.max_column for col in sheet_map.columns
            ):
                return Calculation(status="out_of_scope", values={
                    "reason": "caller_mapping_exceeds_workbook_dimensions",
                    "worksheet_name": sheet_map.worksheet_name,
                    "request_sha256": request_digest,
                    "source_file_sha256": digest,
                })
            header_values: dict[int, Any] = {}
            for col_map in sheet_map.columns:
                header_value = sheet.cell(sheet_map.header_row_number, col_map.column_number).value
                if header_value != col_map.expected_header_value:
                    return Calculation(status="out_of_scope", values={
                        "reason": "caller_mapping_header_value_mismatch",
                        "worksheet_name": sheet_map.worksheet_name,
                        "header_row_number": sheet_map.header_row_number,
                        "column_number": col_map.column_number,
                        "request_sha256": request_digest,
                        "source_file_sha256": digest,
                    })
                header_values[col_map.column_number] = _json_value(header_value)
            for row_number, source_cells in enumerate(
                sheet.iter_rows(min_row=sheet_map.data_start_row,
                                 max_row=sheet_map.data_end_row, min_col=1,
                                 max_col=sheet.max_column),
                start=sheet_map.data_start_row,
            ):
                fields = tuple(ExplosiveWeldFatigueObservationField(
                    field_id=col_map.field_id,
                    caller_meaning=col_map.caller_meaning,
                    unit_token=col_map.unit_token,
                    role=col_map.role,
                    column_number=col_map.column_number,
                    cell_address=source_cells[col_map.column_number - 1].coordinate,
                    cell_type=source_cells[col_map.column_number - 1].data_type,
                    raw_value=_json_value(source_cells[col_map.column_number - 1].value),
                    source_header_value=header_values[col_map.column_number],
                    mapping_evidence=col_map.mapping_evidence,
                ) for col_map in sheet_map.columns)
                evidence = Evidence(
                    source_id=DATASET_ID,
                    origin="open_dataset",
                    citation=f"{request.authorization.attribution}; dataset DOI {DATASET_DOI}; CC BY 4.0",
                    license_id=LICENSE_ID,
                    sha256=digest,
                )
                row_fields = dict(
                    attribution=request.authorization.attribution,
                    authorization_sha256=authorization_digest,
                    mapping_sha256=mapping_digest,
                    source_filename=FILENAME,
                    provider_file_id=metadata["file_id"],
                    source_file_bytes=metadata["bytes"],
                    source_file_sha256=digest,
                    worksheet_name=sheet.title,
                    header_row_number=sheet_map.header_row_number,
                    provider_row_number=row_number,
                    fields=fields,
                    evidence=evidence,
                )
                provisional = ExplosiveWeldFatigueMappedObservationRow.model_construct(
                    **row_fields, source_row_sha256="0" * 64
                )
                row_digest = canonical_digest(
                    provisional.model_dump(mode="json", exclude={"source_row_sha256"})
                )
                rows.append(ExplosiveWeldFatigueMappedObservationRow.model_validate(
                    row_fields | {"source_row_sha256": row_digest}
                ))
    finally:
        workbook.close()
    return Calculation(values={
        "model_id": MAPPED_MODEL_ID,
        "status": "computed",
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "source_file_id": metadata["file_id"],
        "source_file_bytes": metadata["bytes"],
        "source_file_sha256": digest,
        "request_sha256": request_digest,
        "mapping_sha256": mapping_digest,
        "authorization_sha256": authorization_digest,
        "row_count": len(rows),
        "maximum_output_rows": request.maximum_output_rows,
        "maximum_output_cells": request.maximum_output_cells,
        "mapped_rows": [row.model_dump(mode="json") for row in rows],
        "formula_cells_preserved_as_source_text": True,
        "formulas_evaluated": False,
        "unit_conversion_performed": False,
        "column_meanings_inferred": False,
        "fatigue_law_fitted": False,
        "design_allowables_computed": False,
        "qualification_claimed": False,
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (
        ModelSpec(
            model_id=MODEL_ID,
            input_type=ExplosiveWeldFatigueAuditRequest,
            evaluator=audit_explosive_weld_fatigue_directory,
            units={"bytes": "byte", "rows": "1", "columns": "1"},
            assumptions=(
                "Only the exact Mendeley version-1 workbook is accepted by filename, byte count and SHA-256.",
                "The audit returns file and worksheet dimensions without cell values.",
                "Typed import preserves cell order and representation; it does not interpret workbook semantics.",
                "The provider declares CC BY 4.0; embedded third-party content may need separate permission.",
                "The reader does not infer a fatigue law, corrosion resistance, life, acceptance or service qualification.",
            ),
            source_ids=(SOURCE_ID,), version="1.0.0",
        ),
        ModelSpec(
            model_id=MAPPED_MODEL_ID,
            input_type=ExplosiveWeldFatigueMappedImportRequest,
            evaluator=import_explosive_weld_fatigue_mapped_rows,
            units={"source_file_bytes": "byte", "row_count": "1"},
            assumptions=(
                "The caller maps each worksheet, header value, inclusive row span, field meaning, unit token and field role.",
                "A mapping is rejected if its worksheet, dimensions or exact raw header values do not match the pinned workbook.",
                "Mapped rows preserve native cell types, raw formulas, cell addresses, caller mapping Evidence and source digests.",
                "No formula is evaluated, no unit is converted, and no material or specimen identity is inferred from labels.",
                "This data import does not fit a fatigue law, calculate design allowables or claim engineering qualification.",
                "The provider declares CC BY 4.0; possible third-party workbook content remains subject to separate rights review.",
            ),
            source_ids=(SOURCE_ID, CALLER_MAPPING_SOURCE_ID),
            version="1.0.0",
            qualification="data_import",
        ),
    )

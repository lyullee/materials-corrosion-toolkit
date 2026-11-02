"""Local-only typed workbook rows for Mendeley X80/SRB stress-corrosion experiments."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

DATASET_ID = "mendeley-x80-srb-scc"
DATASET_DOI = "10.17632/cmyhpvspp9.1"
DATASET_URL = "https://data.mendeley.com/datasets/cmyhpvspp9/1"
LICENSE_ID = "CC-BY-4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
MODEL_ID = "data.mendeley_x80_srb_scc_typed_rows"
SOURCE_ID = "mendeley_x80_srb_scc_lab_rows"

FILE_METADATA = {
    "Data of  AC Impedance.xls": {
        "file_id": "936ef5db-6420-455d-84c0-351e7a543b15",
        "bytes": 32256,
        "sha256": "a63e376753c3608d2ca082af139d974de76b7d7b28699bcc43d8fc8d0d72ab25",
        "data_kind": "eis",
    },
    "Data of  Slow Strain Rate Tensile Test.xls": {
        "file_id": "f71a75bf-fd74-40f3-916b-7001e721d07c",
        "bytes": 4858368,
        "sha256": "302e7a4c1fedaf4de06f92304f4c5dc2f850c8b91250d900dfd138420f6d2ad6",
        "data_kind": "ssrt",
    },
    "Data of Polarization Curves.xls": {
        "file_id": "6bbf8839-02d3-496f-b582-c8207ddc2421",
        "bytes": 299008,
        "sha256": "0e483b5ab53ff050c669a3ba0d8933ed77107fc904aa9831b989090c430b3250",
        "data_kind": "polarization",
    },
}


class X80SCCReadAuthorization(Contract):
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]

    @model_validator(mode="after")
    def attribution_pins_dataset_version(self):
        if not self.attribution.strip() or DATASET_DOI not in self.attribution:
            raise ValueError("attribution must identify the versioned Mendeley dataset DOI")
        return self


class X80SCCWorkbookCell(Contract):
    column_number: StrictInt = Field(ge=1, le=512)
    cell_type_code: StrictInt = Field(ge=0, le=99)
    raw_value: Any


class X80SCCWorkbookRow(Contract):
    schema_version: Literal["matintegrity.mendeley_x80_srb_scc_workbook_row.v1"] = (
        "matintegrity.mendeley_x80_srb_scc_workbook_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_filename: str = Field(min_length=1, max_length=256)
    provider_file_id: str = Field(min_length=1, max_length=128)
    data_kind: Literal["eis", "polarization", "ssrt"]
    source_file_bytes: StrictInt = Field(gt=0)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    worksheet_name: str = Field(min_length=1, max_length=128)
    provider_row_number: StrictInt = Field(ge=1)
    cells: tuple[X80SCCWorkbookCell, ...] = Field(min_length=1, max_length=512)
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence

    @model_validator(mode="after")
    def validate_source_lineage(self):
        if self.source_filename not in FILE_METADATA:
            raise ValueError("row references an unpinned provider filename")
        metadata = FILE_METADATA[self.source_filename]
        if (self.provider_file_id != metadata["file_id"]
                or self.source_file_bytes != metadata["bytes"]
                or self.source_file_sha256 != metadata["sha256"]
                or self.data_kind != metadata["data_kind"]):
            raise ValueError("row file identity differs from the pinned versioned asset record")
        if self.evidence.source_id != DATASET_ID or self.evidence.license_id != LICENSE_ID:
            raise ValueError("Evidence must preserve the dataset identity and CC BY license")
        if self.evidence.sha256 != self.source_file_sha256:
            raise ValueError("Evidence must pin the complete provider file digest")
        if DATASET_DOI not in self.evidence.citation:
            raise ValueError("Evidence must cite the exact versioned dataset")
        if len({cell.column_number for cell in self.cells}) != len(self.cells):
            raise ValueError("a row may not contain duplicate source columns")
        expected = canonical_digest(self.model_dump(mode="json", exclude={"source_row_sha256"}))
        if self.source_row_sha256 != expected:
            raise ValueError("row digest must cover typed cells and full provenance")
        return self


class X80SCCDirectoryAuditRequest(Contract):
    local_data_directory: str = Field(min_length=1)
    authorization: X80SCCReadAuthorization


def _verified_asset(path: Path) -> tuple[dict[str, Any], str]:
    if path.name not in FILE_METADATA or not path.is_file():
        raise ValueError("only the three pinned Mendeley version-1 XLS assets are accepted")
    metadata = FILE_METADATA[path.name]
    if path.stat().st_size != metadata["bytes"]:
        raise ValueError("local XLS byte count differs from official Mendeley metadata")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    actual = digest.hexdigest()
    if actual != metadata["sha256"]:
        raise ValueError("local XLS SHA-256 differs from the official provider digest")
    return metadata, actual


def _xlrd_cell_value(cell: Any) -> Any:
    # xlrd returns Excel dates as numeric serials unless a caller explicitly converts them.
    value = cell.value
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def iter_x80_srb_scc_rows(
    directory: str | Path, *, authorization: X80SCCReadAuthorization,
    include_kinds: tuple[Literal["eis", "polarization", "ssrt"], ...] = ("eis", "polarization", "ssrt"),
) -> Iterator[X80SCCWorkbookRow]:
    """Yield typed original rows from selected pinned XLS assets in explicit file order.

    The parser preserves workbook/sheet/row/column order and xlrd cell type codes. It does not
    infer electrochemical units, specimen grouping, bacterial state, or test-condition mapping.
    """
    try:
        import xlrd
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install matintegrity[science] to read legacy XLS workbooks") from exc
    if not include_kinds or len(set(include_kinds)) != len(include_kinds):
        raise ValueError("include_kinds must be a nonempty unique selection")
    unknown = set(include_kinds) - {value["data_kind"] for value in FILE_METADATA.values()}
    if unknown:
        raise ValueError(f"unsupported dataset kind selection: {sorted(unknown)}")
    folder = Path(directory)
    auth_digest = canonical_digest(authorization.model_dump(mode="json"))
    for filename, expected in FILE_METADATA.items():
        if expected["data_kind"] not in include_kinds:
            continue
        path = folder / filename
        metadata, digest = _verified_asset(path)
        workbook = xlrd.open_workbook(str(path), on_demand=True)
        try:
            for sheet in workbook.sheets():
                for row_index in range(sheet.nrows):
                    cells = tuple(
                        X80SCCWorkbookCell(
                            column_number=col_index + 1,
                            cell_type_code=sheet.cell_type(row_index, col_index),
                            raw_value=_xlrd_cell_value(sheet.cell(row_index, col_index)),
                        )
                        for col_index in range(sheet.ncols)
                    )
                    if not any(cell.cell_type_code not in (0, 6) for cell in cells):
                        continue
                    evidence = Evidence(
                        source_id=DATASET_ID,
                        origin="open_dataset",
                        citation=f"{authorization.attribution}; Mendeley Data DOI {DATASET_DOI}; CC BY 4.0",
                        license_id=LICENSE_ID,
                        sha256=digest,
                    )
                    fields = dict(
                        attribution=authorization.attribution,
                        authorization_sha256=auth_digest,
                        source_filename=filename,
                        provider_file_id=metadata["file_id"],
                        data_kind=metadata["data_kind"],
                        source_file_bytes=metadata["bytes"],
                        source_file_sha256=digest,
                        worksheet_name=sheet.name,
                        provider_row_number=row_index + 1,
                        cells=cells,
                        evidence=evidence,
                    )
                    provisional = X80SCCWorkbookRow.model_construct(
                        **fields, source_row_sha256="0" * 64
                    )
                    row_digest = canonical_digest(
                        provisional.model_dump(mode="json", exclude={"source_row_sha256"})
                    )
                    yield X80SCCWorkbookRow.model_validate(
                        fields | {"source_row_sha256": row_digest}
                    )
        finally:
            workbook.release_resources()


def audit_x80_srb_scc_directory(request: X80SCCDirectoryAuditRequest) -> Calculation:
    """Return pinned asset and legacy-workbook structure metadata, never point values."""
    try:
        import xlrd
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install matintegrity[science] to read legacy XLS workbooks") from exc
    folder = Path(request.local_data_directory)
    files = []
    for filename, expected in FILE_METADATA.items():
        path = folder / filename
        metadata, digest = _verified_asset(path)
        book = xlrd.open_workbook(str(path), on_demand=True)
        try:
            sheets = []
            for sheet in book.sheets():
                sheets.append({"name": sheet.name, "rows": sheet.nrows, "columns": sheet.ncols})
            files.append({
                "filename": filename,
                "provider_file_id": metadata["file_id"],
                "data_kind": metadata["data_kind"],
                "bytes": metadata["bytes"],
                "sha256": digest,
                "sheets": sheets,
            })
        finally:
            book.release_resources()
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "license_id": LICENSE_ID,
        "authorization_sha256": canonical_digest(
            request.authorization.model_dump(mode="json")
        ),
        "files": files,
        "cell_values_emitted": False,
        "conditions_interpreted": False,
        "corrosion_rate_inferred": False,
        "status": "audited_local_only",
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=X80SCCDirectoryAuditRequest,
        evaluator=audit_x80_srb_scc_directory,
        units={"bytes": "byte", "rows": "1", "columns": "1"},
        assumptions=(
            "Audit only three exact Mendeley version-1 XLS assets using official byte counts and SHA-256 values.",
            "Metadata audit reports workbook structure but not test observations.",
            "Row iteration is caller-local and preserves source order, cells, storage codes and file lineage.",
            "The dataset record declares CC BY 4.0; any embedded third-party content still requires separate provenance review.",
            "The reader does not interpret conditions or compute SCC susceptibility, corrosion rates, hydrogen damage or qualification.",
        ),
        source_ids=(SOURCE_ID,),
        version="1.0.0",
    ),)

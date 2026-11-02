"""Local-only typed workbook rows for a Mendeley magnesium-alloy SCC dataset."""

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

DATASET_ID = "mendeley-ze41-az91d-fsp-scc"
DATASET_DOI = "10.17632/59rcng6nsr.1"
LICENSE_ID = "CC-BY-4.0"
MODEL_ID = "data.mendeley_mg_fsp_scc_typed_rows"
SOURCE_ID = "mendeley_mg_fsp_scc_lab_rows"

FILE_METADATA = {
    "AZ91D Base-SCC RD .xlsx": {
        "file_id": "f026c487-1b70-4820-b708-613a5cf448d6", "bytes": 339092,
        "sha256": "25da3d79639fdfc02740ce47a1a7a85df5705c8455fff362fbcc748d8e2bb637",
    },
    "AZ91D-FSP-SCC RD  .xlsx": {
        "file_id": "c37ba5ef-9b4d-438d-92bc-ae03fa10185f", "bytes": 747229,
        "sha256": "584561ac76e19916983fe67f34b39867b1cfc2cc9ad8a4cbd625a26906e54380",
    },
    "ZE41 Base-SCC RD .xlsx": {
        "file_id": "1123e0ab-7677-42a5-8971-ce313bdea4af", "bytes": 515093,
        "sha256": "bd81f2f7f6881b76b350de9ce6f92a9710a2d56f7db98aaf34f3b0310ce2fc1f",
    },
    "ZE41-FSP-SCC RD .xlsx": {
        "file_id": "88beda01-70c8-4461-a8a1-11ed9acffb26", "bytes": 481558,
        "sha256": "08ed648e514ad3cbabd96f4b6673d8c7b07053198eb06a3ea53d5321f21b116c",
    },
}


class MagnesiumFspSccReadAuthorization(Contract):
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


class MagnesiumFspSccWorkbookCell(Contract):
    column_number: StrictInt = Field(ge=1, le=512)
    address: str = Field(min_length=2, max_length=16)
    cell_type: str = Field(min_length=1, max_length=8)
    raw_value: Any


class MagnesiumFspSccWorkbookRow(Contract):
    schema_version: Literal["matintegrity.mendeley_mg_fsp_scc_row.v1"] = "matintegrity.mendeley_mg_fsp_scc_row.v1"
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_filename: str = Field(min_length=1, max_length=256)
    provider_file_id: str = Field(min_length=1, max_length=128)
    source_file_bytes: StrictInt = Field(gt=0)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    worksheet_name: str = Field(min_length=1, max_length=128)
    provider_row_number: StrictInt = Field(ge=1)
    cells: tuple[MagnesiumFspSccWorkbookCell, ...] = Field(min_length=1, max_length=512)
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence

    @model_validator(mode="after")
    def validate_lineage(self):
        metadata = FILE_METADATA.get(self.source_filename)
        if metadata is None:
            raise ValueError("row refers to an unpinned provider asset")
        if (self.provider_file_id != metadata["file_id"] or self.source_file_bytes != metadata["bytes"]
                or self.source_file_sha256 != metadata["sha256"]):
            raise ValueError("source row file lineage differs from official provider metadata")
        if self.evidence.source_id != DATASET_ID or self.evidence.license_id != LICENSE_ID:
            raise ValueError("Evidence must retain dataset identity and CC BY license")
        if self.evidence.sha256 != self.source_file_sha256 or DATASET_DOI not in self.evidence.citation:
            raise ValueError("Evidence must cite the dataset and pin the workbook digest")
        if len({cell.column_number for cell in self.cells}) != len(self.cells):
            raise ValueError("row cell columns must be unique")
        expected = canonical_digest(self.model_dump(mode="json", exclude={"source_row_sha256"}))
        if self.source_row_sha256 != expected:
            raise ValueError("row digest must cover cell contents and source provenance")
        return self


class MagnesiumFspSccAuditRequest(Contract):
    local_data_directory: str = Field(min_length=1)
    authorization: MagnesiumFspSccReadAuthorization


def _verify(path: Path) -> tuple[dict[str, Any], str]:
    metadata = FILE_METADATA.get(path.name)
    if metadata is None or not path.is_file():
        raise ValueError("only the four pinned Mendeley version-1 workbook assets are accepted")
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


def iter_magnesium_fsp_scc_rows(
    directory: str | Path, *, authorization: MagnesiumFspSccReadAuthorization,
    include_filenames: tuple[str, ...] | None = None,
) -> Iterator[MagnesiumFspSccWorkbookRow]:
    """Yield nonempty original XLSX rows after exact provider identity and digest checks.

    The importer preserves source coordinates and native cell representations. It does not
    interpret worksheet labels, units, sample hierarchy or SCC/corrosion outcomes.
    """
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install matintegrity[science] to read XLSX workbooks") from exc
    names = tuple(FILE_METADATA) if include_filenames is None else include_filenames
    if not names or len(set(names)) != len(names) or set(names) - set(FILE_METADATA):
        raise ValueError("include_filenames must be a nonempty unique selection of pinned files")
    root = Path(directory)
    auth_digest = canonical_digest(authorization.model_dump(mode="json"))
    for filename in names:
        path = root / filename
        metadata, digest = _verify(path)
        workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
        try:
            for sheet in workbook.worksheets:
                for row_number, source_cells in enumerate(sheet.iter_rows(), start=1):
                    if not any(cell.value is not None for cell in source_cells):
                        continue
                    cells = tuple(MagnesiumFspSccWorkbookCell(
                        column_number=column,
                        address=cell.coordinate,
                        cell_type=cell.data_type,
                        raw_value=_json_value(cell.value),
                    ) for column, cell in enumerate(source_cells, start=1))
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
                        source_filename=filename,
                        provider_file_id=metadata["file_id"],
                        source_file_bytes=metadata["bytes"],
                        source_file_sha256=digest,
                        worksheet_name=sheet.title,
                        provider_row_number=row_number,
                        cells=cells,
                        evidence=evidence,
                    )
                    provisional = MagnesiumFspSccWorkbookRow.model_construct(
                        **fields, source_row_sha256="0" * 64
                    )
                    row_digest = canonical_digest(
                        provisional.model_dump(mode="json", exclude={"source_row_sha256"})
                    )
                    yield MagnesiumFspSccWorkbookRow.model_validate(
                        fields | {"source_row_sha256": row_digest}
                    )
        finally:
            workbook.close()


def audit_magnesium_fsp_scc_directory(request: MagnesiumFspSccAuditRequest) -> Calculation:
    """Return local workbook/sheet dimensions and hashes without emitting cell values."""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install matintegrity[science] to read XLSX workbooks") from exc
    root = Path(request.local_data_directory)
    files = []
    for filename in FILE_METADATA:
        path = root / filename
        metadata, digest = _verify(path)
        workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
        try:
            sheets = []
            for sheet in workbook.worksheets:
                nonempty_rows = sum(1 for row in sheet.iter_rows() if any(c.value is not None for c in row))
                sheets.append({"name": sheet.title, "rows": sheet.max_row,
                               "columns": sheet.max_column, "nonempty_rows": nonempty_rows})
            files.append({"filename": filename, "provider_file_id": metadata["file_id"],
                          "bytes": metadata["bytes"], "sha256": digest, "sheets": sheets})
        finally:
            workbook.close()
    return Calculation(values={
        "model_id": MODEL_ID, "dataset_id": DATASET_ID, "dataset_doi": DATASET_DOI,
        "license_id": LICENSE_ID,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "files": files, "cell_values_emitted": False, "worksheet_semantics_interpreted": False,
        "scc_or_corrosion_model_executed": False, "status": "audited_local_only",
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=MagnesiumFspSccAuditRequest,
        evaluator=audit_magnesium_fsp_scc_directory,
        units={"bytes": "byte", "rows": "1", "columns": "1"},
        assumptions=(
            "Only the four exact Mendeley Data version-1 XLSX assets are accepted by name, size and SHA-256.",
            "Audit returns file and worksheet dimensions without cell values.",
            "Typed import preserves source cell order and storage representation; it does not interpret worksheet semantics.",
            "The provider declares CC BY 4.0, while possible third-party material may need separate permission.",
            "The reader does not infer SCC susceptibility, crack-growth law, corrosion rate, life or engineering qualification.",
        ),
        source_ids=(SOURCE_ID,), version="1.0.0",
    ),)

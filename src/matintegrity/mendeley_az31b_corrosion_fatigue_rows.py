"""Local-only typed workbook rows for an AZ31B corrosion-fatigue dataset."""

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

DATASET_ID = "mendeley-az31b-corrosion-fatigue-cold-spray"
DATASET_DOI = "10.17632/5b5rk27wmx.1"
ARTICLE_DOI = "10.3390/coatings8120443"
LICENSE_ID = "CC-BY-4.0"
MODEL_ID = "data.mendeley_az31b_corrosion_fatigue_typed_rows"
SOURCE_ID = "mendeley_az31b_corrosion_fatigue_lab_rows"

FILE_METADATA = {
    "Paper-2-Fig. 4b.-Feb07-18.xlsx": {
        "file_id": "f11ec1e0-c99a-4bdc-8a2a-57491b153469", "bytes": 24733,
        "sha256": "28711532dc422397cf04baae3419e333af19c67567bbf5dcaceaf872deeca885",
    },
    "Paper-2-Fig. 5a.-Feb07-18.xlsx": {
        "file_id": "1f0c5b17-fd2f-4763-8124-d1d9aeebd3d6", "bytes": 379045,
        "sha256": "549110882ec8ca802c35b3c6542619e3402f51bc8b8ffaad270f72dda1e7d836",
    },
    "Paper-2-Fig. 5b.-Feb07-18.xlsx": {
        "file_id": "c73acc7a-ba4c-4204-967f-b5747de7000a", "bytes": 241420,
        "sha256": "637862f55fa803361f7bf0730dd63418c4c37c1328dd8138d80b21f491e161e9",
    },
    "Paper-2-Fig. 6a.-Feb07-18.xlsx": {
        "file_id": "0efea7ab-4d06-45e6-8857-7ee6d0875533", "bytes": 15289,
        "sha256": "8cc41e20cabf7f113c20b19520a9536be45fe8e50a2816a3aeaee42a60601c2b",
    },
    "Paper-2-Fig. 6b.-Feb07-18.xlsx": {
        "file_id": "fb6a4989-a202-4c83-90ad-e8dd27eeba1a", "bytes": 15345,
        "sha256": "0f2d88af66d41be31dd7800df0cb45e6244e4b43ad81eb894710bbff80a4c094",
    },
    "Paper-2-Fig. 7.-Feb07-18.xlsx": {
        "file_id": "131c95ee-6e5f-4a72-a3dc-cfd8c4924509", "bytes": 7793151,
        "sha256": "da330c29639d2a53de9e3662d47c4b2766d9f26db0307bf02a8fd99a3dd874ee",
    },
    "Paper-2-Fig. 9a.-Feb07-18.xlsx": {
        "file_id": "1d3d8eb6-d179-461c-baf4-87ccbe306f3c", "bytes": 703659,
        "sha256": "c88b1cbc94072842001c9d738f119e95fe15e41deb4d27237f96d5d50628171b",
    },
    "Paper-2-Fig. 9b.-Feb07-18.xlsx": {
        "file_id": "4bd8899d-efbe-4cbf-9482-21a37d392df3", "bytes": 703488,
        "sha256": "d88a0ef45d060e4f4d6d8c20188c465728880e7c1ec1213f97c0022d6530cacb",
    },
}


class AZ31BCorrosionFatigueReadAuthorization(Contract):
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    article_doi: Literal[ARTICLE_DOI] = ARTICLE_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]

    @model_validator(mode="after")
    def attribution_pins_sources(self):
        if not self.attribution.strip() or DATASET_DOI not in self.attribution or ARTICLE_DOI not in self.attribution:
            raise ValueError("attribution must cite the versioned dataset and associated article")
        return self


class AZ31BCorrosionFatigueWorkbookCell(Contract):
    column_number: StrictInt = Field(ge=1, le=512)
    address: str = Field(min_length=2, max_length=16)
    cell_type: str = Field(min_length=1, max_length=8)
    raw_value: Any


class AZ31BCorrosionFatigueWorkbookRow(Contract):
    schema_version: Literal["matintegrity.mendeley_az31b_corrosion_fatigue_row.v1"] = (
        "matintegrity.mendeley_az31b_corrosion_fatigue_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    article_doi: Literal[ARTICLE_DOI] = ARTICLE_DOI
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
    cells: tuple[AZ31BCorrosionFatigueWorkbookCell, ...] = Field(min_length=1, max_length=512)
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence

    @model_validator(mode="after")
    def validate_lineage(self):
        if self.source_filename not in FILE_METADATA:
            raise ValueError("row refers to an unpinned provider asset")
        metadata = FILE_METADATA[self.source_filename]
        if (self.provider_file_id != metadata["file_id"]
                or self.source_file_bytes != metadata["bytes"]
                or self.source_file_sha256 != metadata["sha256"]):
            raise ValueError("source row file lineage differs from official metadata")
        if self.evidence.source_id != DATASET_ID or self.evidence.license_id != LICENSE_ID:
            raise ValueError("Evidence must retain dataset identity and CC BY license")
        if self.evidence.sha256 != self.source_file_sha256:
            raise ValueError("Evidence must pin the exact workbook SHA-256")
        if DATASET_DOI not in self.evidence.citation or ARTICLE_DOI not in self.evidence.citation:
            raise ValueError("Evidence must cite both the dataset and its associated article")
        if len({cell.column_number for cell in self.cells}) != len(self.cells):
            raise ValueError("row cell columns must be unique")
        expected = canonical_digest(self.model_dump(mode="json", exclude={"source_row_sha256"}))
        if self.source_row_sha256 != expected:
            raise ValueError("row digest must cover cells and complete source provenance")
        return self


class AZ31BCorrosionFatigueAuditRequest(Contract):
    local_data_directory: str = Field(min_length=1)
    authorization: AZ31BCorrosionFatigueReadAuthorization


def _verify(path: Path) -> tuple[dict[str, Any], str]:
    if path.name not in FILE_METADATA or not path.is_file():
        raise ValueError("only the eight pinned Mendeley version-1 workbook assets are accepted")
    metadata = FILE_METADATA[path.name]
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


def iter_az31b_corrosion_fatigue_rows(
    directory: str | Path, *, authorization: AZ31BCorrosionFatigueReadAuthorization,
    include_filenames: tuple[str, ...] | None = None,
) -> Iterator[AZ31BCorrosionFatigueWorkbookRow]:
    """Yield original nonempty XLSX rows after exact provider identity and digest checks.

    File names are preserved verbatim. The importer does not infer figure semantics, test
    conditions, replicate identity, units or the meaning of any table block.
    """
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install matintegrity[science] to read XLSX workbooks") from exc
    names = tuple(FILE_METADATA) if include_filenames is None else include_filenames
    if not names or len(set(names)) != len(names) or set(names) - set(FILE_METADATA):
        raise ValueError("include_filenames must be a nonempty unique selection of pinned files")
    root = Path(directory)
    authorization_digest = canonical_digest(authorization.model_dump(mode="json"))
    for filename in names:
        path = root / filename
        metadata, digest = _verify(path)
        workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
        try:
            for sheet in workbook.worksheets:
                for row_number, source_cells in enumerate(sheet.iter_rows(), start=1):
                    if not any(cell.value is not None for cell in source_cells):
                        continue
                    cells = tuple(AZ31BCorrosionFatigueWorkbookCell(
                        column_number=column,
                        address=cell.coordinate,
                        cell_type=cell.data_type,
                        raw_value=_json_value(cell.value),
                    ) for column, cell in enumerate(source_cells, start=1))
                    evidence = Evidence(
                        source_id=DATASET_ID,
                        origin="open_dataset",
                        citation=f"{authorization.attribution}; dataset DOI {DATASET_DOI}; article DOI {ARTICLE_DOI}; CC BY 4.0",
                        license_id=LICENSE_ID,
                        sha256=digest,
                    )
                    fields = dict(
                        attribution=authorization.attribution,
                        authorization_sha256=authorization_digest,
                        source_filename=filename,
                        provider_file_id=metadata["file_id"],
                        source_file_bytes=metadata["bytes"],
                        source_file_sha256=digest,
                        worksheet_name=sheet.title,
                        provider_row_number=row_number,
                        cells=cells,
                        evidence=evidence,
                    )
                    provisional = AZ31BCorrosionFatigueWorkbookRow.model_construct(
                        **fields, source_row_sha256="0" * 64
                    )
                    row_digest = canonical_digest(
                        provisional.model_dump(mode="json", exclude={"source_row_sha256"})
                    )
                    yield AZ31BCorrosionFatigueWorkbookRow.model_validate(
                        fields | {"source_row_sha256": row_digest}
                    )
        finally:
            workbook.close()


def audit_az31b_corrosion_fatigue_directory(
    request: AZ31BCorrosionFatigueAuditRequest,
) -> Calculation:
    """Audit the eight pinned workbook layouts without emitting cell values."""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install matintegrity[science] to read XLSX workbooks") from exc
    root = Path(request.local_data_directory)
    files = []
    for filename, expected in FILE_METADATA.items():
        path = root / filename
        metadata, digest = _verify(path)
        workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
        try:
            sheets = []
            for sheet in workbook.worksheets:
                nonempty_rows = sum(
                    1 for row in sheet.iter_rows() if any(cell.value is not None for cell in row)
                )
                sheets.append({
                    "name": sheet.title,
                    "rows": sheet.max_row,
                    "columns": sheet.max_column,
                    "nonempty_rows": nonempty_rows,
                })
            files.append({
                "filename": filename,
                "provider_file_id": metadata["file_id"],
                "bytes": metadata["bytes"],
                "sha256": digest,
                "sheets": sheets,
            })
        finally:
            workbook.close()
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "article_doi": ARTICLE_DOI,
        "license_id": LICENSE_ID,
        "authorization_sha256": canonical_digest(
            request.authorization.model_dump(mode="json")
        ),
        "files": files,
        "cell_values_emitted": False,
        "figure_meaning_interpreted": False,
        "corrosion_fatigue_model_executed": False,
        "status": "audited_local_only",
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=AZ31BCorrosionFatigueAuditRequest,
        evaluator=audit_az31b_corrosion_fatigue_directory,
        units={"bytes": "byte", "rows": "1", "columns": "1"},
        assumptions=(
            "Only eight exact Mendeley Data version-1 XLSX assets are accepted by file name, byte count and SHA-256.",
            "Audit returns workbook and sheet structure without numeric data values.",
            "Local row import preserves cell coordinates, storage types and source order; it does not parse figure semantics.",
            "The dataset is declared CC BY 4.0; third-party contents identified within the assets may require separate permission.",
            "The reader does not infer corrosion rate, fatigue law, coating effectiveness, life, acceptance or service qualification.",
        ),
        source_ids=(SOURCE_ID,),
        version="1.0.0",
    ),)

"""Read-only, provenance-preserving row access for pinned AESEC workbooks."""

from __future__ import annotations

import hashlib
from datetime import date, datetime, time
from io import BytesIO
from pathlib import Path
from typing import Iterator, Literal
from zipfile import ZipFile

from pydantic import Field

from .contracts import Contract

DATASET_ID = "zenodo-ti12mo5hf-oxygen-corrosion"
PROVIDER_RECORD = "https://doi.org/10.5281/zenodo.19462164"
LICENSE_ID = "CC0-1.0"
ARCHIVE_FILENAME = "Data_Zenodo_EA2026.zip"
ARCHIVE_BYTES = 47_558_332
ARCHIVE_SHA256 = "0d50714744e0c6b1b2359beedde96f6b8842ad45ba19c6fcc224b90fd95d6915"
MAX_ARCHIVE_BYTES = ARCHIVE_BYTES
MAX_WORKBOOK_BYTES = 300_000
MAX_ROWS = 6_000
MAX_COLUMNS = 16

_AESEC = {
    "Data_Zenodo_EA2026/AESEC/Ti12Mo5Hf.xlsx": {
        "sha256": "ebb6feb5a8413a045f947b511b3859185ce7471ada408faba2cbb50c6b7f87be",
        "bytes": 260_255,
        "rows": 5_076,
    },
    "Data_Zenodo_EA2026/AESEC/Ti12Mo5Hf0.3O.xlsx": {
        "sha256": "1b417efd20b85deaa8f27c1459332af71ad7d9dd4ebfd5efd29cbba1f3676567",
        "bytes": 266_785,
        "rows": 5_075,
    },
}
_EXPECTED_HEADERS = (
    "time [s]",
    "vTi [ng·s^-1·cm^-2]",
    "vHf [ng·s^-1·cm^-2]",
    "vMo [ng·s^-1·cm^-2]",
    "Potential vs. Ag/AgCl [V]",
    "|je| [µA/cm2]",
    "jƩ [µA/cm2]",
)


class Ti12Mo5HfAESECRequest(Contract):
    """Explicit local-use consent and a narrow allowlisted source selection."""

    schema_version: Literal["matintegrity.zenodo_ti12mo5hf_aesec_request.v1"] = (
        "matintegrity.zenodo_ti12mo5hf_aesec_request.v1"
    )
    local_archive_path: str = Field(min_length=1)
    member_path: Literal[
        "Data_Zenodo_EA2026/AESEC/Ti12Mo5Hf.xlsx",
        "Data_Zenodo_EA2026/AESEC/Ti12Mo5Hf0.3O.xlsx",
    ]
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class Ti12Mo5HfAESECProvenance(Contract):
    schema_version: Literal["matintegrity.zenodo_ti12mo5hf_aesec_provenance.v1"] = (
        "matintegrity.zenodo_ti12mo5hf_aesec_provenance.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    archive_filename: Literal[ARCHIVE_FILENAME] = ARCHIVE_FILENAME
    archive_bytes: Literal[ARCHIVE_BYTES] = ARCHIVE_BYTES
    archive_sha256: Literal[ARCHIVE_SHA256] = ARCHIVE_SHA256
    member_path: str = Field(min_length=1)
    member_bytes: int = Field(gt=0, le=MAX_WORKBOOK_BYTES)
    member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sheet_name: Literal["Sheet1"] = "Sheet1"
    row_index_base: Literal[1] = 1
    header_row: Literal[1] = 1
    provider_row_count_including_header: int = Field(ge=2, le=MAX_ROWS)
    source_data_values_transformed: Literal[False] = False


class Ti12Mo5HfAESECRow(Contract):
    schema_version: Literal["matintegrity.zenodo_ti12mo5hf_aesec_row.v1"] = (
        "matintegrity.zenodo_ti12mo5hf_aesec_row.v1"
    )
    provenance: Ti12Mo5HfAESECProvenance
    source_row_number: int = Field(ge=2, le=MAX_ROWS)
    source_headers: tuple[str, ...] = _EXPECTED_HEADERS
    # Cells follow source column order; blank Excel cells remain None.
    raw_cells: tuple[str | float | int | bool | None, ...] = Field(min_length=7, max_length=7)
    interpretation: Literal["provider_cells_verbatim_no_conversion_or_inference"] = (
        "provider_cells_verbatim_no_conversion_or_inference"
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _excel_value(value):
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    raise TypeError(f"Unsupported spreadsheet cell type: {type(value).__name__}")


def iter_local_aesec_rows(
    request: Ti12Mo5HfAESECRequest,
) -> Iterator[Ti12Mo5HfAESECRow]:
    """Stream raw cells from one digest-pinned local AESEC workbook in memory.

    The ZIP is never extracted. Each yielded row carries source/member hashes,
    original column labels and row number. No unit conversion, fit, filtering,
    condition segmentation or corrosion calculation is performed.
    """
    if not request.computational_use_authorized or not request.local_only_authorized:
        raise PermissionError("Explicit computational-use and local-only authorization is required")
    archive = Path(request.local_archive_path)
    if archive.name != ARCHIVE_FILENAME:
        raise ValueError(f"Expected local source archive named {ARCHIVE_FILENAME!r}")
    if archive.stat().st_size != ARCHIVE_BYTES or archive.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Archive byte count does not match the pinned source")

    archive_hash = hashlib.sha256()
    with archive.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            archive_hash.update(block)
    if archive_hash.hexdigest() != ARCHIVE_SHA256:
        raise ValueError("Archive SHA-256 does not match the pinned source")

    member_pin = _AESEC[request.member_path]
    with ZipFile(archive) as bundle:
        try:
            info = bundle.getinfo(request.member_path)
        except KeyError as error:
            raise ValueError("Allowlisted workbook is missing from the archive") from error
        if info.file_size != member_pin["bytes"] or info.file_size > MAX_WORKBOOK_BYTES:
            raise ValueError("Workbook member size differs from the pinned source")
        workbook_bytes = bundle.read(info)
    member_hash = _sha256(workbook_bytes)
    if member_hash != member_pin["sha256"]:
        raise ValueError("Workbook member SHA-256 differs from the pinned source")

    try:
        from openpyxl import load_workbook
    except ImportError as error:
        raise RuntimeError("Install the optional science dependencies to read XLSX files") from error

    workbook = load_workbook(BytesIO(workbook_bytes), read_only=True, data_only=False)
    try:
        if workbook.sheetnames != ["Sheet1"]:
            raise ValueError("Workbook sheet structure differs from the reviewed source")
        sheet = workbook["Sheet1"]
        if sheet.max_row != member_pin["rows"] or sheet.max_row > MAX_ROWS:
            raise ValueError("Workbook row count differs from the pinned structure")
        if sheet.max_column != len(_EXPECTED_HEADERS) or sheet.max_column > MAX_COLUMNS:
            raise ValueError("Workbook column count differs from the reviewed structure")
        header = tuple(_excel_value(cell) for cell in next(sheet.iter_rows(min_row=1, max_row=1, values_only=True)))
        if header != _EXPECTED_HEADERS:
            raise ValueError("Workbook header labels differ from the reviewed structure")
        provenance = Ti12Mo5HfAESECProvenance(
            member_path=request.member_path,
            member_bytes=info.file_size,
            member_sha256=member_hash,
            provider_row_count_including_header=sheet.max_row,
        )
        for row_number, cells in enumerate(
            sheet.iter_rows(min_row=2, max_row=sheet.max_row, values_only=True), start=2
        ):
            if len(cells) != len(_EXPECTED_HEADERS):
                raise ValueError(f"Unexpected source row width at row {row_number}")
            yield Ti12Mo5HfAESECRow(
                provenance=provenance,
                source_row_number=row_number,
                raw_cells=tuple(_excel_value(value) for value in cells),
            )
    finally:
        workbook.close()

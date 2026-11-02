"""Provenance-pinned local row reader for a public aqueous Ti-Mo-Zr dataset."""

from __future__ import annotations

import hashlib
import math
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Iterator, Literal
from zipfile import ZipFile

from pydantic import Field

from .contracts import Contract

DATASET_ID = "zenodo-ti12mo5zr-aqueous-corrosion"
PROVIDER_RECORD = "https://doi.org/10.5281/zenodo.14981665"
CONCEPT_RECORD = "https://doi.org/10.5281/zenodo.13903531"
LICENSE_ID = "CC0-1.0"
ARCHIVE_NAME = "zenodo_APSUC_2024.zip"
ARCHIVE_BYTES = 54_257_020
ARCHIVE_MD5 = "900a6e1fd9aa550299d01ce892e24d22"
ARCHIVE_SHA256 = "caf53855e78ff7162c361ba73435892759926f2d60513f5d42220239ce21f537"
MAX_ARCHIVE_BYTES = ARCHIVE_BYTES
MAX_MEMBER_BYTES = 800_000
MAX_ROWS = 11_000
MAX_COLUMNS = 8


class _Member:
    __slots__ = ("byte_count", "sha256", "rows", "columns", "headers", "kind")

    def __init__(self, byte_count, sha256, rows, columns, headers, kind):
        self.byte_count = byte_count
        self.sha256 = sha256
        self.rows = rows
        self.columns = columns
        self.headers = headers
        self.kind = kind


_MEMBERS = {
    "zenodo_APSUC_2024/Fig.2/TiMoZr_5100s_OCP.1.xls": _Member(728576, "e1e76ff4cb2216ea03968032e7cf4fdc2805afb632dc3243a3e181348d73d516", 10201, 3, ("Index", "Time [s]", "Potential [V]"), "ocp_monitor"),
    "zenodo_APSUC_2024/Fig.2/TiMoZr_5100s_OCP.2.xls": _Member(728576, "d81d71195e3ebf75c6d671c9405e5e77a2affb7c42474565dd333f868c7f9d57", 10201, 3, ("Index", "Time [s]", "Potential [V]"), "ocp_monitor"),
    "zenodo_APSUC_2024/Fig.2/TiMoZr_5100s_OCP.3.xls": _Member(728576, "6f8ad5522adb0e53ad1338ed629c093b9655e105461eefce439271d2c80c9e68", 10201, 3, ("Index", "Time [s]", "Potential [V]"), "ocp_monitor"),
    "zenodo_APSUC_2024/Fig.2/TiMo_5100s_OCP.1.xls": _Member(728576, "c606272b78e7fdfad5311350858ebad9f1fffeeaad439fac96ba5af35c4e4e60", 10201, 3, ("Index", "Time [s]", "Potential [V]"), "ocp_monitor"),
    "zenodo_APSUC_2024/Fig.2/TiMo_5100s_OCP.2.xls": _Member(728576, "6df1035d8495da493e7ad72275bc7a5f907acd2d158619cc95123bf518c3f189", 10201, 3, ("Index", "Time [s]", "Potential [V]"), "ocp_monitor"),
    "zenodo_APSUC_2024/Fig.2/TiMo_5100s_OCP.3.xls": _Member(728576, "22e838dac176217dd1d0ba35e7765704cc61bc1e4a48457a2f4f42a76bd4500b", 10201, 3, ("Index", "Time [s]", "Potential [V]"), "ocp_monitor"),
    "zenodo_APSUC_2024/Fig.3/Fig.3a/TiMoZr_5100s_EIS.1.xls": _Member(33280, "3fa4c218671ed7fb977d63f4aa8e7fbf283b9b1f11e1771361a6714b2ce8a815", 75, 5, ("Index", "Frequency (Hz)", "Time [s]", "|Z| [Ohm]", "WE.-Phase [deg]"), "eis_spectrum"),
    "zenodo_APSUC_2024/Fig.3/Fig.3a/TiMoZr_5100s_EIS.2.xls": _Member(33280, "e052ebfc8059e75d80eff1fbc3c4bca55cd7f7a8efaa501df8c16895770b0578", 75, 5, ("Index", "Frequency (Hz)", "Time [s]", "|Z| [Ohm]", "WE.-Phase [deg]"), "eis_spectrum"),
    "zenodo_APSUC_2024/Fig.3/Fig.3a/TiMoZr_5100s_EIS.3.xls": _Member(33280, "a68df7e1ad9769437dbeda246c4bafc58209648d3a9eb87806eae248efb51d3e", 75, 5, ("Index", "Frequency (Hz)", "Time [s]", "|Z| [Ohm]", "WE.-Phase [deg]"), "eis_spectrum"),
    "zenodo_APSUC_2024/Fig.3/Fig.3a/TiMo_5100s_EIS.1.xls": _Member(33280, "f6f502c39793664ee2ef5381a657337facaf76b8db0d31bb7c96cdb37988d537", 75, 5, ("Index", "Frequency (Hz)", "Time [s]", "|Z| [Ohm]", "WE.-Phase [deg]"), "eis_spectrum"),
    "zenodo_APSUC_2024/Fig.3/Fig.3a/TiMo_5100s_EIS.2.xls": _Member(33280, "001f608ea1a986fea783d4d436274b9b60f8cfb368b07197667cea8da185c832", 75, 5, ("Index", "Frequency (Hz)", "Time [s]", "|Z| [Ohm]", "WE.-Phase [deg]"), "eis_spectrum"),
    "zenodo_APSUC_2024/Fig.3/Fig.3a/TiMo_5100s_EIS.3.xls": _Member(33280, "f64374b39a6dfa3802f463286dce7a299f6ca3e3d19d4d8a3945da2069088491", 75, 5, ("Index", "Frequency (Hz)", "Time [s]", "|Z| [Ohm]", "WE.-Phase [deg]"), "eis_spectrum"),
    "zenodo_APSUC_2024/Fig.5/Fig.5a/TiMo_Potential_OCP_PSP_OCP_AESEC.xls": _Member(304640, "76e0d219f1614cacf54790bef836e9fb3f194b31817566d4e4a3c93ba3fb8b1f", 5062, 2, ("time [s]", "Potential [V]"), "aesec_potential"),
    "zenodo_APSUC_2024/Fig.5/Fig.5b/TiMoZr_Potential_OCP_PSP_OCP_AESEC.xls": _Member(304640, "416c75c1ac4104dd58a37a45720ce3126aa196ca45d37a02ee80cf076e27c033", 5062, 2, ("time [s]", "Potential [V]"), "aesec_potential"),
    "zenodo_APSUC_2024/Fig.5/Fig.5c/TiMo_Dissolution_Rate_OCP_PSP_OCP_AESEC.xls": _Member(510976, "0a10355af534c3254a76ea5c7aa69a9ff4ae4578f68646c2c88b582afe2165c2", 6604, 3, ("time [s]", "vTi [ng·s^-1·cm^-2]", "vMo [ng·s^-1·cm^-2]"), "aesec_elemental_dissolution_rate"),
    "zenodo_APSUC_2024/Fig.5/Fig.5d/TiMoZr_DissolutionRate_OCP_PSP_OCP_AESEC.xls": _Member(582144, "52aef79a7284b88296f00ade100756efbdd60893028fe302a1e29fee4c9ae024", 6122, 4, ("time [s]", "vTi [ng·s^-1·cm^-2]", "vMo [ng·s^-1·cm^-2]", "vZr [ng·s^-1·cm^-2]"), "aesec_elemental_dissolution_rate"),
}


class Ti12Mo5ZrWorkbookRequest(Contract):
    schema_version: Literal["matintegrity.zenodo_ti12mo5zr_workbook_request.v1"] = (
        "matintegrity.zenodo_ti12mo5zr_workbook_request.v1"
    )
    local_archive_path: str = Field(min_length=1)
    member_path: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class Ti12Mo5ZrWorkbookProvenance(Contract):
    schema_version: Literal["matintegrity.zenodo_ti12mo5zr_workbook_provenance.v1"] = (
        "matintegrity.zenodo_ti12mo5zr_workbook_provenance.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    archive_name: Literal[ARCHIVE_NAME] = ARCHIVE_NAME
    archive_bytes: Literal[ARCHIVE_BYTES] = ARCHIVE_BYTES
    archive_sha256: Literal[ARCHIVE_SHA256] = ARCHIVE_SHA256
    member_path: str = Field(min_length=1)
    member_bytes: int = Field(gt=0, le=MAX_MEMBER_BYTES)
    member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    row_count_including_header: int = Field(ge=2, le=MAX_ROWS)
    column_count: int = Field(ge=2, le=MAX_COLUMNS)
    source_kind: Literal["ocp_monitor", "eis_spectrum", "aesec_potential", "aesec_elemental_dissolution_rate"]
    source_row_number_base: Literal[1] = 1
    values_transformed: Literal[False] = False


class Ti12Mo5ZrRawRow(Contract):
    schema_version: Literal["matintegrity.zenodo_ti12mo5zr_raw_row.v1"] = (
        "matintegrity.zenodo_ti12mo5zr_raw_row.v1"
    )
    provenance: Ti12Mo5ZrWorkbookProvenance
    source_row_number: int = Field(ge=2, le=MAX_ROWS)
    raw_headers: tuple[str, ...] = Field(min_length=2, max_length=MAX_COLUMNS)
    raw_cells: tuple[str | float | int | bool | None, ...] = Field(min_length=2, max_length=MAX_COLUMNS)
    row_semantics: Literal["provider_row_unmodified_units_and_time_unconverted"] = (
        "provider_row_unmodified_units_and_time_unconverted"
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _cell_value(value, ctype: int, datemode: int):
    import xlrd

    if ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
        return None
    if ctype == xlrd.XL_CELL_DATE:
        year, month, day, hour, minute, second = xlrd.xldate_as_tuple(value, datemode)
        return datetime(year, month, day, hour, minute, second).isoformat()
    if ctype == xlrd.XL_CELL_NUMBER:
        if not math.isfinite(value):
            raise ValueError("Non-finite numeric source cell")
        return float(value)
    if ctype == xlrd.XL_CELL_BOOLEAN:
        return bool(value)
    return str(value)


def iter_local_rows(request: Ti12Mo5ZrWorkbookRequest) -> Iterator[Ti12Mo5ZrRawRow]:
    """Yield digest-pinned workbook rows without extracting files or interpreting values."""
    if not request.computational_use_authorized or not request.local_only_authorized:
        raise PermissionError("Explicit computational-use and local-only authorization is required")
    try:
        member_policy = _MEMBERS[request.member_path]
    except KeyError as error:
        raise ValueError("Only exact allowlisted OCP, EIS and AESEC workbooks are accepted") from error
    archive = Path(request.local_archive_path)
    if archive.name != ARCHIVE_NAME or archive.stat().st_size != ARCHIVE_BYTES:
        raise ValueError("Local archive name or byte count does not match the pinned provider asset")
    if _sha256_file(archive) != ARCHIVE_SHA256:
        raise ValueError("Local archive SHA-256 does not match the pinned provider asset")

    with ZipFile(archive) as bundle:
        try:
            info = bundle.getinfo(request.member_path)
        except KeyError as error:
            raise ValueError("Allowlisted workbook is absent from the archive") from error
        if info.file_size != member_policy.byte_count or info.file_size > MAX_MEMBER_BYTES:
            raise ValueError("Workbook member size does not match the reviewed source pin")
        member_bytes = bundle.read(info)
    member_sha = hashlib.sha256(member_bytes).hexdigest()
    if member_sha != member_policy.sha256:
        raise ValueError("Workbook member digest does not match the reviewed source pin")

    try:
        import xlrd
    except ImportError as error:
        raise RuntimeError("Install the optional science dependencies to read legacy XLS files") from error
    book = xlrd.open_workbook(file_contents=member_bytes, on_demand=True)
    try:
        if book.sheet_names() != ["Sheet1"]:
            raise ValueError("Workbook sheet structure changed from the pinned source")
        sheet = book.sheet_by_index(0)
        if (sheet.nrows != member_policy.rows or sheet.nrows > MAX_ROWS
                or sheet.ncols != member_policy.columns or sheet.ncols > MAX_COLUMNS):
            raise ValueError("Workbook dimensions changed from the pinned source")
        headers = tuple(str(value) for value in sheet.row_values(0))
        if headers != member_policy.headers:
            raise ValueError("Workbook header labels changed from the pinned source")
        provenance = Ti12Mo5ZrWorkbookProvenance(
            member_path=request.member_path,
            member_bytes=info.file_size,
            member_sha256=member_sha,
            row_count_including_header=sheet.nrows,
            column_count=sheet.ncols,
            source_kind=member_policy.kind,
        )
        for row_index in range(1, sheet.nrows):
            row = sheet.row(row_index)
            values = tuple(_cell_value(cell.value, cell.ctype, book.datemode) for cell in row)
            yield Ti12Mo5ZrRawRow(
                provenance=provenance,
                source_row_number=row_index + 1,
                raw_headers=headers,
                raw_cells=values,
            )
    finally:
        book.release_resources()

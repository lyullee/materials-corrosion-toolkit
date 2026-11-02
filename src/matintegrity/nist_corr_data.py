"""Structure-only audit for the locally cached NIST CORR-DATA compilation."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import Field

from .contracts import Contract

DATASET_ID = "nist-corr-data-corrosion-observations"
PROVIDER_RECORD = "https://doi.org/10.18434/M3TH4R"
ARCHIVE_SHA256 = "013d9c5d7d4b9433d8a679c8b793d17f487463e0472b466d289450290d0da95c"
ARCHIVE_BYTES = 354591
CSV_MEMBER = "CORR-DATA_Database.csv"
EXPECTED_MEMBERS = frozenset({CSV_MEMBER, "about-CORR-DATA_Database.txt", "columnDefinitions.txt"})
EXPECTED_HEADER = (
    "Environment",
    "Material Group",
    "Material Family",
    "Material",
    "Rate (mm/yr) or Rating",
    "Rate (mils/yr) or Rating",
    "Localized Attack",
    "UNS",
    "Condition/Comment",
    "Concentration (Vol %)",
    "Temperature (deg C)",
    "Temperature (deg F)",
    "Duration",
    "Reference #",
    "Reference",
)
_SCALAR = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?$")
_RANGE = re.compile(r"^[-+]?\d+(?:\.\d+)?\s*[-\u2013]\s*[-+]?\d+(?:\.\d+)?$")
MENDELEY_SCC_ARCHIVE_BYTES = 81799
MENDELEY_SCC_ARCHIVE_SHA256 = "5a33a81abb00752aa4c682dd25722b6abca64898de5107bf83011130c80b30a2"
MENDELEY_SCC_INNER_SHA256 = "5866f9605ed2360869660d15772d816d3d94d6ac6e3642ecab27d09d2e07e5ed"
MENDELEY_SCC_WORKBOOK_SHA256 = "db8e97acb40f6de317ba279613ad9543f5cd6d7217f511581e6d6dffb9c15c5b"


class NistCorrDataArchiveAudit(Contract):
    """Compact archive and schema evidence; no provider rows or text are retained."""

    schema_version: Literal["matintegrity.nist_corr_data_archive_audit.v1"] = (
        "matintegrity.nist_corr_data_archive_audit.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    archive_sha256: Literal[ARCHIVE_SHA256] = ARCHIVE_SHA256
    archive_bytes: Literal[ARCHIVE_BYTES] = ARCHIVE_BYTES
    archive_member_count: Literal[3] = 3
    csv_member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    header_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    header_column_count: Literal[15] = 15
    record_count: int = Field(gt=0)
    row_widths: dict[str, int]
    blank_counts: dict[str, int]
    token_classes: dict[str, dict[str, int]]
    reference_key_count: int = Field(gt=0)
    rows_without_reference_key: int = Field(ge=0)
    numerical_interpretation: Literal["not_performed"] = "not_performed"
    pointwise_records_published: Literal[False] = False
    qualification: Literal["archive_structure_only"] = "archive_structure_only"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _packaged_dataset() -> dict:
    path = Path(__file__).with_name("catalog_data") / "datasets.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    row = next((item for item in catalog["datasets"] if item["id"] == DATASET_ID), None)
    if row is None:
        raise ValueError("packaged dataset catalog lacks the pinned NIST CORR-DATA record")
    return row


def _classify_token(token: str) -> str:
    value = token.strip()
    if not value:
        return "blank"
    if _SCALAR.fullmatch(value):
        return "numeric_scalar"
    if _RANGE.fullmatch(value):
        return "numeric_range"
    if value.upper() in {"A", "B", "C", "D"}:
        return "qualitative_rating_code"
    return "other_text_or_notation"


def _summarize_archive_bytes(archive_bytes: bytes) -> dict:
    """Validate provider layout and emit aggregate structural facts only."""
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        infos = archive.infolist()
        names = [row.filename for row in infos]
        if len(names) != len(set(names)) or set(names) != EXPECTED_MEMBERS:
            raise ValueError("NIST CORR-DATA archive members differ from the pinned manifest")
        if any(row.is_dir() or row.file_size > 8_000_000 or row.flag_bits & 0x1 for row in infos):
            raise ValueError("NIST CORR-DATA archive contains an unsupported member")
        if archive.testzip() is not None:
            raise ValueError("NIST CORR-DATA archive member CRC check failed")
        csv_bytes = archive.read(CSV_MEMBER)

    try:
        text = csv_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("NIST CORR-DATA CSV is not valid UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != EXPECTED_HEADER:
        raise ValueError("NIST CORR-DATA CSV header differs from the reviewed provider schema")

    blank_counts: Counter[str] = Counter()
    token_classes: dict[str, Counter[str]] = {
        "Rate (mm/yr) or Rating": Counter(),
        "Rate (mils/yr) or Rating": Counter(),
        "Concentration (Vol %)": Counter(),
        "Temperature (deg C)": Counter(),
        "Temperature (deg F)": Counter(),
        "Duration": Counter(),
    }
    row_widths: Counter[str] = Counter()
    reference_keys: set[str] = set()
    rows_without_reference_key = 0
    record_count = 0
    for row in reader:
        record_count += 1
        if None in row or any(value is None for value in row.values()):
            raise ValueError("NIST CORR-DATA contains a row with a nonconforming number of fields")
        row_widths[str(len(row))] += 1
        for name, value in row.items():
            if not value.strip():
                blank_counts[name] += 1
        for name, counter in token_classes.items():
            counter[_classify_token(row[name])] += 1
        reference_key = row["Reference #"].strip()
        if reference_key:
            reference_keys.add(reference_key)
        else:
            rows_without_reference_key += 1

    return {
        "archive_member_count": 3,
        "csv_member_sha256": _sha256_bytes(csv_bytes),
        "header_sha256": _sha256_bytes(("\x1f".join(EXPECTED_HEADER)).encode()),
        "header_column_count": len(EXPECTED_HEADER),
        "record_count": record_count,
        "row_widths": dict(row_widths),
        "blank_counts": dict(blank_counts),
        "token_classes": {key: dict(value) for key, value in token_classes.items()},
        "reference_key_count": len(reference_keys),
        "rows_without_reference_key": rows_without_reference_key,
    }


def audit_nist_corr_data_archive(archive_path: str | Path) -> NistCorrDataArchiveAudit:
    """Check the pinned ZIP/CSV and summarize field coverage without publishing rows."""
    dataset = _packaged_dataset()
    assets = [row for row in dataset.get("assets", []) if row.get("filename") == "CORR-DATA_Database.zip"]
    if (
        len(assets) != 1
        or assets[0].get("checksum") != f"sha256:{ARCHIVE_SHA256}"
        or assets[0].get("bytes") != ARCHIVE_BYTES
    ):
        raise ValueError("packaged NIST CORR-DATA catalog differs from the parser's reviewed pin")
    path = Path(archive_path)
    if path.stat().st_size != ARCHIVE_BYTES:
        raise ValueError("NIST CORR-DATA archive byte size differs from the pinned manifest")
    archive_bytes = path.read_bytes()
    archive_sha256 = _sha256_bytes(archive_bytes)
    if archive_sha256 != ARCHIVE_SHA256:
        raise ValueError("NIST CORR-DATA archive SHA-256 differs from the pinned manifest")
    return NistCorrDataArchiveAudit(archive_sha256=archive_sha256, **_summarize_archive_bytes(archive_bytes))


def _summarize_mendeley_scc_archive_bytes(archive_bytes: bytes) -> dict:
    """Summarize an SCC archive fixture or pinned archive without exposing cell content."""
    import io

    import openpyxl

    archive_sha256 = _sha256_bytes(archive_bytes)
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as outer:
        if len(outer.infolist()) != 1:
            raise ValueError("SCC provider archive member count changed")
        inner_info = outer.infolist()[0]
        if inner_info.file_size > 2_000_000 or not inner_info.filename.endswith("Processed Data.zip"):
            raise ValueError("SCC provider archive member differs from the reviewed layout")
        inner_bytes = outer.read(inner_info)
    inner_sha256 = _sha256_bytes(inner_bytes)
    with zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner:
        if len(inner.infolist()) != 1 or inner.infolist()[0].file_size > 2_000_000:
            raise ValueError("SCC workbook archive member count or size changed")
        workbook_bytes = inner.read(inner.infolist()[0])
    workbook = openpyxl.load_workbook(io.BytesIO(workbook_bytes), read_only=True, data_only=False)
    sheet_summary = []
    formula_cells = 0
    for sheet in workbook.worksheets:
        formulas = 0
        nonempty = 0
        for row in sheet.iter_rows():
            for cell in row:
                formulas += cell.data_type == "f"
                nonempty += cell.value is not None
        formula_cells += formulas
        sheet_summary.append(
            {
                "name_sha256": _sha256_bytes(sheet.title.encode()),
                "reported_rows": sheet.max_row,
                "reported_columns": sheet.max_column,
                "nonempty_cells": nonempty,
                "formula_cells": formulas,
            }
        )
    workbook.close()
    return {
        "dataset_id": "mendeley-304l-chloride-scc-salt-loading",
        "provider_record": "https://doi.org/10.17632/mrwrphjvjr.1",
        "license": "CC-BY-4.0",
        "archive_bytes": len(archive_bytes),
        "archive_sha256": archive_sha256,
        "inner_archive_bytes": len(inner_bytes),
        "inner_archive_sha256": inner_sha256,
        "workbook_sha256": _sha256_bytes(workbook_bytes),
        "sheet_count": len(sheet_summary),
        "sheets": sheet_summary,
        "formula_cells": formula_cells,
        "numerical_interpretation": "not_performed",
        "pointwise_values_published": False,
        "qualification": "versioned_archive_structure_only_provider_checksum_unavailable",
    }


def audit_mendeley_scc_archive(archive_path: str | Path) -> dict:
    """Verify the locally observed digest pin and catalog before structural SCC audit."""
    path = Path(archive_path)
    dataset = json.loads(
        (Path(__file__).with_name("catalog_data") / "datasets.json").read_text(encoding="utf-8")
    )
    record = next(
        (item for item in dataset["datasets"] if item["id"] == "mendeley-304l-chloride-scc-salt-loading"),
        None,
    )
    if record is None or record.get("license") != "CC-BY-4.0":
        raise ValueError("packaged catalog lacks the reviewed Mendeley SCC dataset record")
    assets = [item for item in record.get("assets", []) if item.get("filename") == "processed-data.zip"]
    if len(assets) != 1 or assets[0].get("bytes") != MENDELEY_SCC_ARCHIVE_BYTES:
        raise ValueError("packaged Mendeley SCC asset size differs from the reviewed archive pin")
    archive_bytes = path.read_bytes()
    if len(archive_bytes) != MENDELEY_SCC_ARCHIVE_BYTES:
        raise ValueError("Mendeley SCC archive byte size differs from the locally observed pin")
    if _sha256_bytes(archive_bytes) != MENDELEY_SCC_ARCHIVE_SHA256:
        raise ValueError("Mendeley SCC archive SHA-256 differs from the locally observed pin")
    report = _summarize_mendeley_scc_archive_bytes(archive_bytes)
    if report["inner_archive_sha256"] != MENDELEY_SCC_INNER_SHA256:
        raise ValueError("Mendeley SCC inner archive SHA-256 differs from the locally observed pin")
    if report["workbook_sha256"] != MENDELEY_SCC_WORKBOOK_SHA256:
        raise ValueError("Mendeley SCC workbook SHA-256 differs from the locally observed pin")
    return report

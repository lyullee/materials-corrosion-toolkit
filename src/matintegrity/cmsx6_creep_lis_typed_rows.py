"""Typed, local-only rows from one catalog-pinned BAM CMSX-6 creep LIS asset."""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

DATASET_ID = "cmsx6-creep"
DATASET_DOI = "10.5281/zenodo.14750432"
LICENSE_ID = "CC-BY-4.0"
MODEL_ID = "data.bam_cmsx6_creep_lis_typed_rows"
SOURCE_ID = "bam_cmsx6_creep_lis_typed_rows"
ASSET_FILENAME = "Vh5205_C-97.LIS"
ASSET_BYTES = 360_637
# MD5 is the provider-published catalog pin; SHA-256 is computed for each local read.
ASSET_MD5 = "c9a1e0cf2430762634b8da84cfe10fdd"
MAX_ASSET_BYTES = 2_000_000
MAX_PHYSICAL_LINES = 100_000

_INTEGER = re.compile(r"^[+-]?\d+$")
_DOT_DECIMAL = re.compile(r"^[+-]?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?$")
_COMMA_DECIMAL = re.compile(r"^[+-]?(?:\d+,\d*|,\d+)(?:[eE][+-]?\d+)?$")


class CMSX6LISReadAuthorization(Contract):
    """Caller attribution and local-only computational-use declaration."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class CMSX6LISColumnValue(Contract):
    """One tabular cell with provider tokens and a locale-declared parse, if numeric."""

    field_position: StrictInt = Field(ge=0)
    label_token: str | None = None
    symbol_token: str | None = None
    unit_token: str | None = None
    raw_value_token: str
    numeric_value: float | None = None
    numeric_parse_status: Literal["integer", "dot_decimal", "comma_decimal", "non_numeric", "header_alignment_unknown"]


class CMSX6LISTypedRow(Contract):
    """One original physical line, represented without assigning material semantics."""

    schema_version: Literal["matintegrity.cmsx6_creep_lis_typed_row.v1"] = (
        "matintegrity.cmsx6_creep_lis_typed_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_filename: Literal[ASSET_FILENAME] = ASSET_FILENAME
    source_file_md5: str = Field(pattern=r"^[a-f0-9]{32}$")
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_file_bytes: StrictInt = Field(gt=0, le=MAX_ASSET_BYTES)
    source_row_order: StrictInt = Field(ge=0)
    source_physical_line: StrictInt = Field(ge=1)
    section: Literal["file_header", "metadata", "time_series"]
    row_kind: Literal[
        "header", "blank", "metadata", "metadata_continuation", "section_marker",
        "column_labels", "column_symbols", "column_units", "data", "unclassified",
    ]
    raw_text: str
    raw_tokens: tuple[str, ...]
    values: tuple[CMSX6LISColumnValue, ...] = ()
    alignment_issue: str | None = None
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    material_strength_inferred: Literal[False] = False
    creep_law_inferred: Literal[False] = False
    lifetime_inferred: Literal[False] = False


class CMSX6LISReadRequest(Contract):
    local_file_path: str = Field(min_length=1)
    authorization: CMSX6LISReadAuthorization


def _verify_local_asset(path: Path) -> tuple[bytes, str, str]:
    if path.name != ASSET_FILENAME or not path.is_file():
        raise ValueError("only the catalog-pinned local CMSX-6 LIS asset is accepted")
    if path.stat().st_size != ASSET_BYTES:
        raise ValueError("local LIS byte count differs from the catalog pin")
    payload = path.read_bytes()
    if len(payload) > MAX_ASSET_BYTES:
        raise ValueError("local LIS exceeds the parser safety size limit")
    md5 = hashlib.md5(payload, usedforsecurity=False).hexdigest()
    if md5 != ASSET_MD5:
        raise ValueError("local LIS MD5 differs from the provider-published catalog pin")
    sha256 = hashlib.sha256(payload).hexdigest()
    return payload, md5, sha256


def _decode_line(raw: bytes) -> str:
    # The provider's legacy LIS is a Windows-1252 tabular text export.
    return raw.decode("cp1252", errors="strict")


def _parse_numeric(token: str) -> tuple[float | None, str]:
    stripped = token.strip()
    if not stripped:
        return None, "non_numeric"
    try:
        if _INTEGER.fullmatch(stripped):
            return float(int(stripped)), "integer"
        if _DOT_DECIMAL.fullmatch(stripped):
            value = float(stripped)
            return (value, "dot_decimal") if math.isfinite(value) else (None, "non_numeric")
        if _COMMA_DECIMAL.fullmatch(stripped):
            value = float(stripped.replace(",", "."))
            return (value, "comma_decimal") if math.isfinite(value) else (None, "non_numeric")
    except (ValueError, OverflowError):
        pass
    return None, "non_numeric"


def iter_cmsx6_creep_lis_rows(
    path: str | Path,
    *,
    authorization: CMSX6LISReadAuthorization,
) -> Iterator[CMSX6LISTypedRow]:
    """Yield the pinned LIS file line-by-line in original order; never alter source values."""
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    payload, md5, sha256 = _verify_local_asset(Path(path))
    raw_lines = payload.splitlines()
    if len(raw_lines) > MAX_PHYSICAL_LINES:
        raise ValueError("local LIS contains more physical lines than the parser limit")
    try:
        lines = [_decode_line(line) for line in raw_lines]
    except UnicodeDecodeError as exc:
        raise ValueError("local LIS is not valid Windows-1252 text") from exc

    auth_sha = canonical_digest(authorization.model_dump(mode="json"))
    evidence = Evidence(
        source_id=DATASET_ID,
        origin="open_dataset",
        citation=f"{authorization.attribution}; {DATASET_DOI}",
        license_id=LICENSE_ID,
        sha256=sha256,
    )

    section: Literal["file_header", "metadata", "time_series"] = "file_header"
    header_stage = 0
    labels: list[str] = []
    symbols: list[str] = []
    units: list[str] = []
    for order, (raw_bytes, raw_text) in enumerate(zip(raw_lines, lines, strict=True)):
        tokens = tuple(raw_text.split("\t"))
        compact = raw_text.strip()
        row_kind: str
        values: tuple[CMSX6LISColumnValue, ...] = ()
        alignment_issue = None

        if not compact:
            row_kind = "blank"
        elif section == "file_header":
            row_kind = "header"
            if compact == "[data]":
                section = "time_series"
                row_kind = "section_marker"
                header_stage = 0
            elif len(tokens) >= 3 and tokens[0].strip() == "ENTRY" and tokens[1].strip() == "SYMBOL":
                section = "metadata"
                row_kind = "column_labels"
        elif section == "metadata" and "[data]" in tokens:
            row_kind = "section_marker"
            section = "time_series"
            header_stage = 0
        elif section == "time_series" and compact == "[data]":
            row_kind = "section_marker"
            header_stage = 0
        elif section == "time_series" and header_stage < 3:
            fields = list(tokens)
            while fields and fields[-1] == "":
                fields.pop()
            if header_stage == 0:
                labels = fields
                row_kind = "column_labels"
            elif header_stage == 1:
                symbols = fields
                row_kind = "column_symbols"
            else:
                units = fields
                row_kind = "column_units"
            header_stage += 1
        elif section == "time_series":
            fields = list(tokens)
            while fields and fields[-1] == "":
                fields.pop()
            if not fields:
                row_kind = "blank"
            else:
                row_kind = "data"
                header_widths = (len(labels), len(symbols), len(units))
                max_header_width = max(header_widths, default=0)
                if len(set(header_widths)) != 1 or len(fields) != max_header_width:
                    alignment_issue = (
                        f"header widths={header_widths}; value field count={len(fields)}; raw row retained"
                    )
                values = tuple(
                    CMSX6LISColumnValue(
                        field_position=index,
                        label_token=labels[index] if index < len(labels) else None,
                        symbol_token=symbols[index] if index < len(symbols) else None,
                        unit_token=units[index] if index < len(units) else None,
                        raw_value_token=value,
                        numeric_value=_parse_numeric(value)[0],
                        numeric_parse_status=(
                            _parse_numeric(value)[1]
                            if index < max_header_width and len(set(header_widths)) == 1
                            else "header_alignment_unknown"
                        ),
                    )
                    for index, value in enumerate(fields)
                )
        else:
            row_kind = "metadata"
            if len(tokens) <= 1 or not tokens[0].strip():
                row_kind = "metadata_continuation"
            section = "metadata"

        row_sha = hashlib.sha256(raw_bytes).hexdigest()
        lineage = {
            "dataset_id": DATASET_ID,
            "source_sha256": sha256,
            "source_row_order": order,
            "source_physical_line": order + 1,
            "raw_line_sha256": row_sha,
            "raw_tokens": tokens,
        }
        yield CMSX6LISTypedRow(
            attribution=authorization.attribution,
            authorization_sha256=auth_sha,
            source_file_md5=md5,
            source_file_sha256=sha256,
            source_file_bytes=len(payload),
            source_row_order=order,
            source_physical_line=order + 1,
            section=section,
            row_kind=row_kind,
            raw_text=raw_text,
            raw_tokens=tokens,
            values=values,
            alignment_issue=alignment_issue,
            source_row_sha256=canonical_digest(lineage),
            evidence=evidence,
        )


def audit_cmsx6_creep_lis(request: CMSX6LISReadRequest) -> Calculation:
    """Report local source pin and row-shape counts without returning observation values."""
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    payload, md5, sha256 = _verify_local_asset(Path(request.local_file_path))
    rows = list(
        iter_cmsx6_creep_lis_rows(
            request.local_file_path,
            authorization=request.authorization,
        )
    )
    return Calculation(
        values={
            "model_id": MODEL_ID,
            "dataset_id": DATASET_ID,
            "dataset_doi": DATASET_DOI,
            "license_id": LICENSE_ID,
            "attribution": request.authorization.attribution,
            "source_filename": ASSET_FILENAME,
            "source_file_md5": md5,
            "source_file_sha256": sha256,
            "source_file_bytes": len(payload),
            "physical_line_count": len(rows),
            "blank_line_count": sum(row.row_kind == "blank" for row in rows),
            "metadata_line_count": sum(row.section == "metadata" for row in rows),
            "time_series_data_line_count": sum(row.row_kind == "data" for row in rows),
            "header_alignment_issue_line_count": sum(row.alignment_issue is not None for row in rows),
            "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
            "local_only": True,
        },
        notes=(
            "The audit returns structure and lineage only; it does not qualify test quality or interpret creep behavior.",
            "The provider-published MD5 verifies the selected asset snapshot; the computed SHA-256 pins this local read.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            MODEL_ID,
            CMSX6LISReadRequest,
            audit_cmsx6_creep_lis,
            {
                "model_id": "1",
                "dataset_id": "1",
                "source_file_sha256": "1",
                "physical_line_count": "1",
                "time_series_data_line_count": "1",
                "local_only": "1",
            },
            (
                "Only one catalog-pinned local LIS asset is accepted; raw records remain local-only.",
                "Text, source order, unit tokens, decimal tokens and tab fields are retained without deriving creep parameters.",
                "Numeric parsing follows the source's comma-decimal token form and retains the unmodified source token.",
            ),
            (SOURCE_ID, DATASET_ID),
        )
    ]

"""Local-only typed access to the version-pinned Zr alloy electrochemistry workbooks.

This reader preserves spreadsheet rows as provider records. It does not interpret
the published quantities as corrosion rates, pitting truth, or life evidence.
"""

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

DATASET_ID = "zenodo-zr-nb-sn-electrochemical-noise-v2"
DATASET_DOI = "10.5281/zenodo.23220129"
LICENSE_ID = "CC-BY-4.0"
SOURCE_ID = "zenodo_zr_nb_sn_electrochemical_typed_rows"
MODEL_ID = "data.zenodo_zr_nb_sn_electrochemical_typed_rows"
_PINS = {
    "Zr-Nb(600 ppm Fe) - Frequency.xlsx": (656105, "e48c0de646c1f2fad70f0584b375444ac2cdc775675fb5c4699dee5ce80f0438"),
    "Zr-Nb(300 ppm Fe) - Time.xlsx": (948470, "617633b7433672fcd54badf8da13cc2d7b21d400408028467eb7f0a418739c8c"),
    "Zr-Nb(600 ppm Fe) - Time.xlsx": (991814, "6b0a53a793fe2c29e5ee8298d5ef84268de92bf15f84b685cb41086ecaf6d56a"),
    "Zr-Nb(400 ppm Fe) - Time.xlsx": (904006, "bb1320f3cfb873f610373a980a88eb7d2fcd8d2080c836b342fcac7c3c29477c"),
    "Zr-Nb(300 ppm Fe) - Frequency.xlsx": (647268, "06fcbc044060242d5530a4b6c3441a8ff1a78e91803aef5b11c6934c852dcff5"),
    "Zr-Nb(400 ppm Fe) - Frequency.xlsx": (672967, "4fcd7436f028e177126838dae4f4ee4b69528b2cf56c232ff1b8d93c85c6cf01"),
    "Zr-Nb-Sn(1100 ppm Fe) - Time.xlsx": (818977, "72c2f0dfb7e21091a38c4b2b8da766b0ea2699a21ab054233f1246aedbdeb1dc"),
    "Zr-Nb-Sn(1100 ppm Fe) - Frequency.xlsx": (623425, "0cadc796b0d6e73c6a585c2de909e94888795357f20dd471e3dc9581a9d43ae4"),
}


class ZrAlloyReadAuthorization(Contract):
    """Caller declaration for attribution and local-only access to CC BY material."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]

    @model_validator(mode="after")
    def nonblank_attribution(self):
        if not self.attribution.strip():
            raise ValueError("CC BY 4.0 attribution must be nonempty")
        return self


class ZrAlloyWorkbookRow(Contract):
    """One non-empty spreadsheet row, retaining provider coordinates and cell order."""

    schema_version: Literal["matintegrity.zenodo_zr_alloy_workbook_row.v1"] = (
        "matintegrity.zenodo_zr_alloy_workbook_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_filename: str = Field(min_length=1)
    source_file_bytes: StrictInt = Field(gt=0)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_order: StrictInt = Field(ge=0)
    worksheet_name: str = Field(min_length=1)
    provider_row_number: StrictInt = Field(ge=1)
    provider_column_count: StrictInt = Field(ge=0)
    row_kind: Literal["unclassified_provider_row"] = "unclassified_provider_row"
    cells: tuple[Any, ...]
    cell_types: tuple[str, ...]
    row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    specimen_identity_resolved: Literal[False] = False
    corrosion_rate_inferred: Literal[False] = False
    penetration_inferred: Literal[False] = False
    remaining_life_inferred: Literal[False] = False
    failure_probability_inferred: Literal[False] = False

    @model_validator(mode="after")
    def pinned_aligned_digest_and_evidence(self):
        pin = _PINS.get(self.source_filename)
        if pin is None or (self.source_file_bytes, self.source_file_sha256) != pin:
            raise ValueError("row source identity must match one pinned Zenodo v2 workbook")
        if self.provider_column_count != len(self.cells) or len(self.cells) != len(self.cell_types):
            raise ValueError("provider column count, cells and cell types must align")
        if any(
            not (value is None or isinstance(value, (str, int, float, bool)))
            or isinstance(value, float) and not math.isfinite(value)
            for value in self.cells
        ):
            raise ValueError("row cells must be finite JSON-compatible scalar values")
        if (
            self.evidence.source_id != DATASET_ID
            or self.evidence.license_id != LICENSE_ID
            or self.evidence.sha256 != self.source_file_sha256
            or self.attribution not in self.evidence.citation
            or f"https://doi.org/{DATASET_DOI}" not in self.evidence.citation
        ):
            raise ValueError("row Evidence must match its pinned dataset, license, source digest and attribution")
        expected_digest = canonical_digest(self.model_dump(mode="json", exclude={"row_sha256"}))
        if self.row_sha256 != expected_digest:
            raise ValueError("row digest must cover the complete typed row and Evidence")
        return self


class ZrAlloyWorkbookAuditRequest(Contract):
    local_workbook_path: str = Field(min_length=1)
    authorization: ZrAlloyReadAuthorization


def _verify_workbook(path: Path) -> tuple[int, str]:
    pin = _PINS.get(path.name)
    if pin is None or not path.is_file():
        raise ValueError("only a catalogued version-2 local XLSX workbook is accepted")
    expected_bytes, expected_sha256 = pin
    if path.stat().st_size != expected_bytes:
        raise ValueError("workbook byte count differs from the pinned Zenodo file")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    actual = digest.hexdigest()
    if actual != expected_sha256:
        raise ValueError("workbook SHA-256 differs from the pinned Zenodo file")
    return expected_bytes, actual


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def iter_zr_alloy_workbook_rows(
    path: str | Path, *, authorization: ZrAlloyReadAuthorization
) -> Iterator[ZrAlloyWorkbookRow]:
    """Yield non-empty cells in workbook, worksheet, row, then column order.

    XLSX parsing is optional and requires openpyxl. Formulas are retained as their
    formula strings; they are never evaluated or treated as measured values.
    Blank rows are omitted, while physical source row numbers remain explicit.
    """
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError("install matintegrity[science] to read XLSX workbooks") from exc

    source = Path(path)
    size, source_sha256 = _verify_workbook(source)
    auth_sha = canonical_digest(authorization.model_dump(mode="json"))
    workbook = load_workbook(source, read_only=True, data_only=False, keep_links=False)
    try:
        order = 0
        for sheet in workbook.worksheets:
            for row_number, cells in enumerate(sheet.iter_rows(), start=1):
                values = tuple(_json_value(cell.value) for cell in cells)
                if any(
                    not (value is None or isinstance(value, (str, int, float, bool)))
                    or isinstance(value, float) and not math.isfinite(value)
                    for value in values
                ):
                    raise ValueError(
                        f"worksheet {sheet.title!r} row {row_number} contains a non-finite or unsupported cell value"
                    )
                if not any(value is not None for value in values):
                    continue
                types = tuple(cell.data_type for cell in cells)
                evidence = Evidence(
                    source_id=DATASET_ID,
                    origin="open_dataset",
                    citation=f"{authorization.attribution}; https://doi.org/{DATASET_DOI} (CC BY 4.0)",
                    license_id=LICENSE_ID,
                    sha256=source_sha256,
                )
                row_fields = dict(
                    attribution=authorization.attribution,
                    authorization_sha256=auth_sha,
                    source_filename=source.name,
                    source_file_bytes=size,
                    source_file_sha256=source_sha256,
                    source_order=order,
                    worksheet_name=sheet.title,
                    provider_row_number=row_number,
                    provider_column_count=len(values),
                    cells=values,
                    cell_types=types,
                    evidence=evidence,
                )
                candidate = ZrAlloyWorkbookRow.model_construct(**row_fields, row_sha256="0" * 64)
                row_digest = canonical_digest(candidate.model_dump(mode="json", exclude={"row_sha256"}))
                yield ZrAlloyWorkbookRow.model_validate(row_fields | {"row_sha256": row_digest})
                order += 1
    finally:
        workbook.close()


def audit_zr_alloy_workbook(request: ZrAlloyWorkbookAuditRequest) -> Calculation:
    """Return local-source identity metadata without emitting sheet or row values."""
    source = Path(request.local_workbook_path)
    size, digest = _verify_workbook(source)
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "source_filename": source.name,
        "source_file_bytes": size,
        "source_file_sha256": digest,
        "point_values_returned": False,
        "local_path_returned": False,
        "local_only": True,
        "corrosion_rate_computed": False,
        "penetration_computed": False,
    }, notes=(
        "Use iter_zr_alloy_workbook_rows for source-order point records; cell meanings remain provider-defined.",
        "The reader preserves raw cell order and formula strings but does not execute formulas or infer specimen identity.",
        "No corrosion rate, localized penetration, remaining life, acceptance result, or failure probability is derived.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=ZrAlloyWorkbookAuditRequest,
        evaluator=audit_zr_alloy_workbook,
        units={"source_file_bytes": "byte"},
        assumptions=(
            "Only the eight pinned Zenodo v2 XLSX files are accepted by filename, byte length, and SHA-256.",
            "Caller supplies attribution and local-only computational authorization; rows retain sheet, row, cell, source-file, and authorization identity.",
            "Blank rows are omitted but row numbers remain source coordinates; formula strings are never evaluated.",
            "The parser does not infer specimen identity, physical replication, rate, penetration, life, acceptance, or probability.",
            "Raw workbooks are local-only and must stay outside public release archives.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="data_import",
    )]

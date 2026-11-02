"""Local, checksum-pinned typed access to a small CC BY wet-CO2 workbook."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, StrictFloat, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

DATASET_ID = "plos_coiled_tubing_weld_hpht_co2_weight_loss_2021_s1"
DATASET_DOI = "10.1371/journal.pone.0244237.s017"
ARTICLE_DOI = "10.1371/journal.pone.0244237"
RECORD_URL = "https://plos.figshare.com/articles/dataset/S1_File_-/13628192"
LICENSE_ID = "CC-BY-4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
MODEL_ID = "data.plos_ct110_wet_co2_typed_rows"
SOURCE_ID = "plos_ct110_wet_co2_typed_rows"
WORKBOOK_FILENAME = "pone.0244237.s017.xlsx"
WORKBOOK_BYTES = 9331
PUBLISHER_MD5 = "95fa4a025f4afe1aac1b5de41c420160"
LOCAL_SHA256 = "8e6ce76d2e67f9a24af1ccfadebc4453e5601c3a7694c7f4bf3d56d259145470"
_SHEETS = ("Sheet1", "Sheet2", "Sheet3")
_TEMPERATURES_C = (30.0, 60.0, 90.0)


class CT110ReadAuthorization(Contract):
    """Caller declaration of CC BY attribution and local computational use."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    article_doi: Literal[ARTICLE_DOI] = ARTICLE_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]

    @model_validator(mode="after")
    def validate_attribution(self):
        text = self.attribution.strip()
        if not text or DATASET_DOI not in text or ARTICLE_DOI not in text or "CC BY 4.0" not in text:
            raise ValueError("attribution must identify both DOIs and the CC BY 4.0 license")
        return self


class CT110CorrosionRateRow(Contract):
    """One original temperature row with separate weld-metal and base-metal cells."""

    schema_version: Literal["matintegrity.ct110_wet_co2_corrosion_row.v1"] = (
        "matintegrity.ct110_wet_co2_corrosion_row.v1"
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
    worksheet_name: Literal["Sheet1"] = "Sheet1"
    provider_row_number: StrictInt = Field(ge=6, le=8)
    source_order: StrictInt = Field(ge=0, le=2)
    temperature_cell: str
    weld_metal_cell: str
    base_metal_cell: str
    source_cells: tuple[Any, ...]
    source_cell_types: tuple[str, ...]
    temperature_C: StrictFloat
    weld_metal_corrosion_rate_mm_per_year: StrictFloat
    base_metal_corrosion_rate_mm_per_year: StrictFloat
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    specimen_identity_resolved: Literal[False] = False
    replicate_independence_established: Literal[False] = False
    life_or_probability_inferred: Literal[False] = False

    @model_validator(mode="after")
    def validate_lineage(self):
        if (
            self.evidence.source_id != DATASET_ID
            or self.evidence.license_id != LICENSE_ID
            or self.evidence.sha256 != self.source_file_sha256
            or DATASET_DOI not in self.evidence.citation
            or ARTICLE_DOI not in self.evidence.citation
        ):
            raise ValueError("Evidence must match the pinned CC BY dataset and supplied attribution")
        if self.provider_row_number != self.source_order + 6:
            raise ValueError("provider row and source order must preserve the original worksheet order")
        if len(self.source_cells) != 5 or len(self.source_cell_types) != 5:
            raise ValueError("source row must preserve all five provider columns and their cell types")
        if (self.temperature_cell, self.weld_metal_cell, self.base_metal_cell) != (
            f"C{self.provider_row_number}", f"D{self.provider_row_number}", f"E{self.provider_row_number}"
        ):
            raise ValueError("cell coordinates must match the provider's temperature, WM and BM columns")
        if not all(math.isfinite(value) for value in (
            self.temperature_C,
            self.weld_metal_corrosion_rate_mm_per_year,
            self.base_metal_corrosion_rate_mm_per_year,
        )):
            raise ValueError("observed values must be finite")
        if self.weld_metal_corrosion_rate_mm_per_year < 0 or self.base_metal_corrosion_rate_mm_per_year < 0:
            raise ValueError("reported corrosion rates must be nonnegative")
        expected_row_digest = canonical_digest(self.model_dump(mode="json", exclude={"source_row_sha256"}))
        if self.source_row_sha256 != expected_row_digest:
            raise ValueError("typed source-row digest must cover the preserved provider cells and metadata")
        return self


class CT110WorkbookAuditRequest(Contract):
    local_workbook_path: str = Field(min_length=1)
    authorization: CT110ReadAuthorization


def _verify_workbook(path: Path) -> tuple[int, str]:
    if path.name != WORKBOOK_FILENAME or not path.is_file():
        raise ValueError("only the catalogued local CT110 workbook filename is accepted")
    size = path.stat().st_size
    if size != WORKBOOK_BYTES:
        raise ValueError("workbook size differs from the pinned publisher asset")
    md5 = hashlib.md5(usedforsecurity=False)
    sha256 = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(block)
            sha256.update(block)
    if md5.hexdigest() != PUBLISHER_MD5:
        raise ValueError("workbook MD5 differs from the public Figshare file metadata")
    if sha256.hexdigest() != LOCAL_SHA256:
        raise ValueError("workbook SHA-256 differs from the reviewed local pin")
    return size, sha256.hexdigest()


def _cell_value(value: Any, *, cell: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"expected one finite numeric measurement at {cell}")
    return float(value)


def iter_ct110_corrosion_rows(
    path: str | Path, *, authorization: CT110ReadAuthorization
) -> Iterator[CT110CorrosionRateRow]:
    """Yield the three pinned temperature rows without altering or fitting values.

    The optional XLSX dependency is imported only when this local reader is used.
    Raw files are not copied to public package data or emitted as parser fixtures.
    """
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("install matintegrity[science] to read XLSX workbooks") from exc

    source = Path(path)
    size, source_sha256 = _verify_workbook(source)
    workbook = load_workbook(source, read_only=True, data_only=False, keep_links=False)
    auth_sha = canonical_digest(authorization.model_dump(mode="json"))
    try:
        if tuple(workbook.sheetnames) != _SHEETS:
            raise ValueError("workbook worksheet names or order differ from the reviewed source layout")
        sheet = workbook["Sheet1"]
        if (sheet.max_row, sheet.max_column) != (8, 5):
            raise ValueError("Sheet1 dimensions differ from the reviewed source layout")
        expected = {
            "D4": "Corrosion Rate/(mm/year)",
            "C5": "Temperature/(C°)",
            "D5": "WM",
            "E5": "BM",
        }
        for address, value in expected.items():
            cell = sheet[address]
            if cell.data_type == "f" or cell.value != value:
                raise ValueError(f"unexpected header at {address}")
        for row_number in range(1, 4):
            if any(sheet.cell(row_number, col).value is not None for col in range(1, 6)):
                raise ValueError("unexpected content above the reviewed header")
        for sheet_name in ("Sheet2", "Sheet3"):
            if any(cell.value is not None for row in workbook[sheet_name].iter_rows() for cell in row):
                raise ValueError(f"unexpected non-empty content in {sheet_name}")

        for order, row_number in enumerate(range(6, 9)):
            cells = [sheet.cell(row_number, col) for col in range(1, 6)]
            if any(cell.data_type == "f" for cell in cells):
                raise ValueError(f"formulas are not accepted in provider row {row_number}")
            if cells[0].value is not None or cells[1].value is not None:
                raise ValueError(f"unexpected leading cells in provider row {row_number}")
            temperature = _cell_value(cells[2].value, cell=f"C{row_number}")
            weld_rate = _cell_value(cells[3].value, cell=f"D{row_number}")
            base_rate = _cell_value(cells[4].value, cell=f"E{row_number}")
            if temperature != _TEMPERATURES_C[order]:
                raise ValueError("temperature rows differ from the pinned source's reviewed order")
            evidence = Evidence(
                source_id=DATASET_ID,
                origin="open_dataset",
                citation=f"{authorization.attribution}; dataset DOI {DATASET_DOI}; article DOI {ARTICLE_DOI}; CC BY 4.0",
                license_id=LICENSE_ID,
                sha256=source_sha256,
            )
            row_fields = dict(
                attribution=authorization.attribution,
                authorization_sha256=auth_sha,
                source_file_bytes=size,
                source_file_sha256=source_sha256,
                provider_row_number=row_number,
                source_order=order,
                temperature_cell=f"C{row_number}",
                weld_metal_cell=f"D{row_number}",
                base_metal_cell=f"E{row_number}",
                source_cells=tuple(cell.value for cell in cells),
                source_cell_types=tuple(cell.data_type for cell in cells),
                temperature_C=temperature,
                weld_metal_corrosion_rate_mm_per_year=weld_rate,
                base_metal_corrosion_rate_mm_per_year=base_rate,
                evidence=evidence,
            )
            candidate = CT110CorrosionRateRow.model_construct(
                **row_fields, source_row_sha256="0" * 64
            )
            row_sha256 = canonical_digest(candidate.model_dump(mode="json", exclude={"source_row_sha256"}))
            yield CT110CorrosionRateRow.model_validate(row_fields | {"source_row_sha256": row_sha256})
    finally:
        workbook.close()


def audit_ct110_workbook(request: CT110WorkbookAuditRequest) -> Calculation:
    """Return local identity/shape metadata while keeping measured values out of audit output."""
    path = Path(request.local_workbook_path)
    size, digest = _verify_workbook(path)
    rows = tuple(iter_ct110_corrosion_rows(path, authorization=request.authorization))
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "article_doi": ARTICLE_DOI,
        "record_url": RECORD_URL,
        "license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "source_filename": path.name,
        "source_file_bytes": size,
        "source_file_sha256": digest,
        "worksheet_names": list(_SHEETS),
        "typed_measurement_rows": len(rows),
        "groups": ["weld_metal", "base_metal"],
        "temperature_support_C": list(_TEMPERATURES_C),
        "rate_unit": "mm/year",
        "source_rows_sha256": [row.source_row_sha256 for row in rows],
        "specimen_identity_resolved": False,
        "replicate_independence_established": False,
        "fit_or_extrapolation_performed": False,
        "life_or_probability_inferred": False,
        "data_values_emitted": False,
        "status": "audited_local_only",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CT110WorkbookAuditRequest,
        evaluator=audit_ct110_workbook,
        units={"temperature_support_C": "degC", "typed_measurement_rows": "count"},
        assumptions=(
            "The exact publisher workbook size, MD5 and local SHA-256 must match before parsing.",
            "Only the three reviewed numeric temperature rows in Sheet1 are typed; every other worksheet must remain empty as pinned.",
            "Each row reports weld-metal and base-metal corrosion rates in mm/year. The workbook does not establish unique physical specimen identity or replicate independence.",
            "Reader access requires caller-provided CC BY 4.0 attribution and local computational-use authorization; raw measurements remain local-only.",
            "No fitting, extrapolation, corrosion-mechanism inference, design acceptance, life or failure probability is calculated.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]

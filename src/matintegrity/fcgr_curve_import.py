"""Fail-closed import of caller-reviewed fatigue crack-growth CSV tables.

This module normalizes explicitly declared units and selection decisions. It does
not infer row validity, stage meaning, publication rights, or curve applicability.
"""

from __future__ import annotations

import csv
import hashlib
import io
import math
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Positive
from .models.crack import TabulatedCrackGrowthCurve


_DELTA_K_TO_PA_SQRT_M = {
    "Pa*sqrt(m)": 1.0,
    "MPa*sqrt(m)": 1.0e6,
    "N/mm^1.5": 1.0e3**1.5,
}
_RATE_TO_M_PER_CYCLE = {"m/cycle": 1.0, "mm/cycle": 1.0e-3}


class FcgrCsvImportRequest(Contract):
    """Mapping and review declarations for one UTF-8 CSV source."""

    csv_bytes: bytes = Field(min_length=1)
    expected_source_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    curve_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    source_citation: str = Field(min_length=1)
    license_id: str = Field(min_length=1)
    rights_review_id: str = Field(min_length=1)
    applicability_review_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    stress_ratio: float = Field(ge=0, lt=1)
    frequency_Hz: Positive | None = None
    delta_k_column: str = Field(min_length=1)
    rate_column: str = Field(min_length=1)
    row_id_column: str = Field(min_length=1)
    disposition_column: str = Field(min_length=1)
    exclusion_reason_column: str = Field(default="exclusion_reason", min_length=1)
    stage_column: str | None = None
    delta_k_unit: Literal["Pa*sqrt(m)", "MPa*sqrt(m)", "N/mm^1.5"]
    rate_unit: Literal["m/cycle", "mm/cycle"]
    below_minimum_policy: Literal["out_of_scope", "zero_below_declared_threshold"]
    declared_threshold_delta_k_Pa_sqrt_m: float | None = Field(default=None, ge=0)
    pointwise_computational_use_authorized: Literal[True]
    curve_applicability_reviewed: Literal[True]
    physical_specimen_identity_status: Literal[
        "identified", "not_required_for_user_model", "not_established"
    ]

    @model_validator(mode="after")
    def distinct_mapped_columns(self):
        mapped = [self.delta_k_column, self.rate_column, self.row_id_column, self.disposition_column]
        if self.stage_column is not None:
            mapped.append(self.stage_column)
        if len(mapped) != len(set(mapped)):
            raise ValueError("FCGR data, row-ID and disposition columns must be distinct")
        if self.exclusion_reason_column in mapped:
            raise ValueError("the exclusion-reason column must differ from all other mapped columns")
        return self

    @classmethod
    def from_file(cls, path: str | Path, **fields):
        """Read and freeze one local file's bytes into a request, optionally pinning its digest."""
        return cls(csv_bytes=Path(path).read_bytes(), **fields)


class FcgrImportedRow(Contract):
    """Audit record retaining mapped source cells and the row decision."""

    source_record_number: int = Field(ge=1)
    row_id: str
    disposition: Literal["include", "exclude"]
    stage_raw: str | None
    delta_k_raw: str
    rate_raw: str
    exclusion_reason: str | None


class FcgrCsvImportResult(Contract):
    source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_citation: str
    license_id: str
    rights_review_id: str
    applicability_review_id: str
    source_row_count: int = Field(ge=1)
    included_row_ids: tuple[str, ...]
    audit_rows: tuple[FcgrImportedRow, ...]
    curve: TabulatedCrackGrowthCurve


def import_fcgr_csv(request: FcgrCsvImportRequest) -> FcgrCsvImportResult:
    """Convert explicitly selected CSV rows into the SI tabulated-curve contract.

    Input rows must already be ordered by strictly increasing delta-K; this
    function deliberately does not sort, deduplicate, filter by stage, or infer
    runouts. Every excluded row needs a caller-provided reason.
    """

    try:
        text = request.csv_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("FCGR CSV must be UTF-8 or UTF-8 with BOM") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    if reader.fieldnames is None:
        raise ValueError("FCGR CSV must include a header row")
    required = {
        request.delta_k_column,
        request.rate_column,
        request.row_id_column,
        request.disposition_column,
    }
    if request.stage_column is not None:
        required.add(request.stage_column)
    if request.exclusion_reason_column in reader.fieldnames:
        required.add(request.exclusion_reason_column)
    missing = sorted(required - set(reader.fieldnames))
    if missing:
        raise ValueError(f"FCGR CSV is missing mapped columns: {', '.join(missing)}")
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("FCGR CSV column names must be unique")

    delta_factor = _DELTA_K_TO_PA_SQRT_M[request.delta_k_unit]
    rate_factor = _RATE_TO_M_PER_CYCLE[request.rate_unit]
    included_ids: list[str] = []
    audit_rows: list[FcgrImportedRow] = []
    delta_values: list[float] = []
    rate_values: list[float] = []
    previous_delta = -math.inf
    seen_ids: set[str] = set()

    for record_number, row in enumerate(reader, start=1):
        if None in row:
            raise ValueError(f"FCGR CSV record {record_number} has more cells than the header")
        row_id = (row.get(request.row_id_column) or "").strip()
        if not row_id:
            raise ValueError(f"FCGR CSV record {record_number} has an empty row identifier")
        if row_id in seen_ids:
            raise ValueError(f"duplicate FCGR row identifier: {row_id}")
        seen_ids.add(row_id)
        disposition = (row.get(request.disposition_column) or "").strip().lower()
        if disposition not in {"include", "exclude"}:
            raise ValueError(
                f"FCGR row {row_id} requires an explicit include/exclude disposition"
            )
        raw_dk = (row.get(request.delta_k_column) or "").strip()
        raw_rate = (row.get(request.rate_column) or "").strip()
        raw_stage = row.get(request.stage_column) if request.stage_column else None
        raw_stage = raw_stage.strip() if raw_stage is not None else None
        reason = (
            (row.get(request.exclusion_reason_column) or "").strip()
            if disposition == "exclude"
            else None
        )
        if disposition == "exclude" and not reason:
            raise ValueError(f"excluded FCGR row {row_id} requires an exclusion_reason column value")
        if disposition == "include":
            try:
                delta = float(raw_dk) * delta_factor
                rate = float(raw_rate) * rate_factor
            except (TypeError, ValueError) as exc:
                raise ValueError(f"FCGR row {row_id} has nonnumeric selected values") from exc
            if not math.isfinite(delta) or not math.isfinite(rate) or delta <= 0 or rate <= 0:
                raise ValueError(f"FCGR row {row_id} must have positive finite delta-K and rate")
            if delta <= previous_delta:
                raise ValueError(
                    "included FCGR rows must have strictly increasing delta-K in source order; "
                    "sorting and duplicate consolidation are not automatic"
                )
            previous_delta = delta
            delta_values.append(delta)
            rate_values.append(rate)
            included_ids.append(row_id)
        audit_rows.append(
            FcgrImportedRow(
                source_record_number=record_number,
                row_id=row_id,
                disposition=disposition,
                stage_raw=raw_stage,
                delta_k_raw=raw_dk,
                rate_raw=raw_rate,
                exclusion_reason=reason,
            )
        )
    if len(delta_values) < 2:
        raise ValueError("at least two explicitly included FCGR rows are required")
    if request.below_minimum_policy == "zero_below_declared_threshold":
        threshold = request.declared_threshold_delta_k_Pa_sqrt_m
        if threshold is None or threshold > delta_values[0]:
            raise ValueError("the declared threshold must be present and no greater than the first point")
    elif request.declared_threshold_delta_k_Pa_sqrt_m is not None:
        raise ValueError("a threshold is only valid with zero_below_declared_threshold")

    source_digest = hashlib.sha256(request.csv_bytes).hexdigest()
    if request.expected_source_sha256 is not None and request.expected_source_sha256 != source_digest:
        raise ValueError("FCGR CSV SHA-256 does not match the expected source digest")
    curve = TabulatedCrackGrowthCurve(
        curve_id=request.curve_id,
        source_group_id=request.source_group_id,
        material_condition_id=request.material_condition_id,
        environment_id=request.environment_id,
        stress_ratio=request.stress_ratio,
        frequency_Hz=request.frequency_Hz,
        delta_k_Pa_sqrt_m=delta_values,
        crack_growth_m_cycle=rate_values,
        below_minimum_policy=request.below_minimum_policy,
        declared_threshold_delta_k_Pa_sqrt_m=request.declared_threshold_delta_k_Pa_sqrt_m,
        source_content_sha256=source_digest,
        source_citation=request.source_citation,
        license_id=request.license_id,
        rights_review_id=request.rights_review_id,
        applicability_review_id=request.applicability_review_id,
        pointwise_computational_use_authorized=request.pointwise_computational_use_authorized,
        curve_applicability_reviewed=request.curve_applicability_reviewed,
        physical_specimen_identity_status=request.physical_specimen_identity_status,
    )
    return FcgrCsvImportResult(
        source_content_sha256=source_digest,
        source_citation=request.source_citation,
        license_id=request.license_id,
        rights_review_id=request.rights_review_id,
        applicability_review_id=request.applicability_review_id,
        source_row_count=len(audit_rows),
        included_row_ids=tuple(included_ids),
        audit_rows=tuple(audit_rows),
        curve=curve,
    )


class FcgrWorkbookSheetSelection(Contract):
    """Caller-reviewed column and row window for one workbook specimen curve."""

    sheet_name: str = Field(min_length=1)
    curve_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    stress_ratio: float = Field(ge=0, lt=1)
    header_row: int = Field(default=2, ge=1)
    first_data_row: int = Field(ge=1)
    last_data_row: int = Field(ge=1)
    delta_k_column_index: int = Field(ge=1)
    rate_column_index: int = Field(ge=1)
    expected_delta_k_header: str = Field(min_length=1)
    expected_rate_header: str = Field(min_length=1)
    specimen_and_row_window_reviewed: Literal[True]

    @model_validator(mode="after")
    def coherent_window(self):
        if self.first_data_row <= self.header_row or self.last_data_row < self.first_data_row:
            raise ValueError("selected FCGR row window must follow the declared header")
        if self.delta_k_column_index == self.rate_column_index:
            raise ValueError("delta-K and growth-rate columns must differ")
        return self


class FcgrWorkbookImportRequest(Contract):
    """Explicit mapping and reuse basis for selected specimen sheets in an Excel workbook."""

    workbook_bytes: bytes = Field(min_length=1)
    expected_source_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    source_citation: str = Field(min_length=1)
    license_id: str = Field(min_length=1)
    rights_review_id: str = Field(min_length=1)
    applicability_review_id: str = Field(min_length=1)
    frequency_Hz: Positive | None = None
    delta_k_unit: Literal["Pa*sqrt(m)", "MPa*sqrt(m)", "N/mm^1.5"]
    rate_unit: Literal["m/cycle", "mm/cycle"]
    below_minimum_policy: Literal["out_of_scope", "zero_below_declared_threshold"]
    declared_threshold_delta_k_Pa_sqrt_m: float | None = Field(default=None, ge=0)
    pointwise_computational_use_authorized: Literal[True]
    curve_applicability_reviewed: Literal[True]
    sheet_selections: tuple[FcgrWorkbookSheetSelection, ...] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def unique_selection_ids(self):
        sheets = [row.sheet_name for row in self.sheet_selections]
        curves = [row.curve_id for row in self.sheet_selections]
        if len(set(sheets)) != len(sheets) or len(set(curves)) != len(curves):
            raise ValueError("workbook sheet names and curve IDs must be unique")
        if self.below_minimum_policy == "zero_below_declared_threshold":
            if self.declared_threshold_delta_k_Pa_sqrt_m is None:
                raise ValueError("zero-growth policy requires an explicit threshold")
        elif self.declared_threshold_delta_k_Pa_sqrt_m is not None:
            raise ValueError("a threshold is only valid with zero_below_declared_threshold")
        if len(self.workbook_bytes) > 50_000_000:
            raise ValueError("FCGR workbook exceeds the 50 MB import limit")
        return self

    @classmethod
    def from_file(cls, path: str | Path, **fields):
        return cls(workbook_bytes=Path(path).read_bytes(), **fields)


class FcgrWorkbookImportedPoint(Contract):
    source_row_id: str
    worksheet_row_number: int = Field(ge=1)
    delta_k_source_value: Positive
    crack_growth_source_value: Positive


class FcgrWorkbookCurveResult(Contract):
    worksheet_name: str
    curve: TabulatedCrackGrowthCurve
    imported_points: tuple[FcgrWorkbookImportedPoint, ...] = Field(min_length=2)


class FcgrWorkbookImportResult(Contract):
    source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_citation: str
    license_id: str
    rights_review_id: str
    applicability_review_id: str
    frequency_Hz: Positive | None
    curves: tuple[FcgrWorkbookCurveResult, ...]


def import_fcgr_workbook(request: FcgrWorkbookImportRequest) -> FcgrWorkbookImportResult:
    """Import only caller-selected, header-checked ordered FCGR rows from Excel.

    No workbook sheet, point range, unit, frequency, or runout treatment is inferred.
    Selected rows must already have strictly increasing delta-K and positive rates.
    """
    try:
        from openpyxl import load_workbook
    except ImportError as error:
        raise ImportError("Excel FCGR import requires the optional science dependencies (openpyxl)") from error

    source_digest = hashlib.sha256(request.workbook_bytes).hexdigest()
    if request.expected_source_sha256 is not None and source_digest != request.expected_source_sha256:
        raise ValueError("FCGR workbook SHA-256 does not match the expected source digest")
    try:
        workbook = load_workbook(io.BytesIO(request.workbook_bytes), read_only=True, data_only=True, keep_links=False)
    except Exception as error:
        raise ValueError("FCGR workbook could not be opened as a readable Excel workbook") from error

    delta_factor = _DELTA_K_TO_PA_SQRT_M[request.delta_k_unit]
    rate_factor = _RATE_TO_M_PER_CYCLE[request.rate_unit]
    results = []
    try:
        for selection in request.sheet_selections:
            if selection.sheet_name not in workbook.sheetnames:
                raise ValueError(f"selected FCGR worksheet is absent: {selection.sheet_name}")
            sheet = workbook[selection.sheet_name]
            if selection.last_data_row > sheet.max_row:
                raise ValueError(f"selected row window exceeds worksheet support: {selection.sheet_name}")
            delta_header = sheet.cell(selection.header_row, selection.delta_k_column_index).value
            rate_header = sheet.cell(selection.header_row, selection.rate_column_index).value
            if delta_header != selection.expected_delta_k_header or rate_header != selection.expected_rate_header:
                raise ValueError(f"selected FCGR columns do not match reviewed headers: {selection.sheet_name}")
            delta_values = []
            rate_values = []
            points = []
            for row_number in range(selection.first_data_row, selection.last_data_row + 1):
                raw_delta = sheet.cell(row_number, selection.delta_k_column_index).value
                raw_rate = sheet.cell(row_number, selection.rate_column_index).value
                if (
                    isinstance(raw_delta, bool) or not isinstance(raw_delta, (int, float))
                    or isinstance(raw_rate, bool) or not isinstance(raw_rate, (int, float))
                ):
                    raise ValueError(
                        f"selected FCGR row {selection.sheet_name}:{row_number} is not numeric; revise the explicit row window"
                    )
                delta = float(raw_delta) * delta_factor
                rate = float(raw_rate) * rate_factor
                if not math.isfinite(delta) or not math.isfinite(rate) or delta <= 0 or rate <= 0:
                    raise ValueError(f"selected FCGR row {selection.sheet_name}:{row_number} is not positive finite data")
                if delta_values and delta <= delta_values[-1]:
                    raise ValueError(
                        f"selected FCGR rows are not strictly increasing in delta-K: {selection.sheet_name}:{row_number}"
                    )
                delta_values.append(delta)
                rate_values.append(rate)
                points.append(FcgrWorkbookImportedPoint(
                    source_row_id=f"{selection.sheet_name}:row:{row_number}",
                    worksheet_row_number=row_number,
                    delta_k_source_value=float(raw_delta),
                    crack_growth_source_value=float(raw_rate),
                ))
            curve = TabulatedCrackGrowthCurve(
                curve_id=selection.curve_id,
                source_group_id=selection.source_group_id,
                material_condition_id=selection.material_condition_id,
                environment_id=selection.environment_id,
                stress_ratio=selection.stress_ratio,
                frequency_Hz=request.frequency_Hz,
                delta_k_Pa_sqrt_m=delta_values,
                crack_growth_m_cycle=rate_values,
                below_minimum_policy=request.below_minimum_policy,
                declared_threshold_delta_k_Pa_sqrt_m=request.declared_threshold_delta_k_Pa_sqrt_m,
                source_content_sha256=source_digest,
                source_citation=request.source_citation,
                license_id=request.license_id,
                rights_review_id=request.rights_review_id,
                applicability_review_id=request.applicability_review_id,
                pointwise_computational_use_authorized=request.pointwise_computational_use_authorized,
                curve_applicability_reviewed=request.curve_applicability_reviewed,
                physical_specimen_identity_status="identified",
            )
            results.append(FcgrWorkbookCurveResult(
                worksheet_name=selection.sheet_name,
                curve=curve,
                imported_points=tuple(points),
            ))
    finally:
        workbook.close()

    return FcgrWorkbookImportResult(
        source_content_sha256=source_digest,
        source_citation=request.source_citation,
        license_id=request.license_id,
        rights_review_id=request.rights_review_id,
        applicability_review_id=request.applicability_review_id,
        frequency_Hz=request.frequency_Hz,
        curves=tuple(results),
    )

"""Read processed consecutive ILI feature workbooks without inventing feature tracks."""

from __future__ import annotations

import hashlib
import math
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from pathlib import Path
from typing import Literal
from zipfile import ZipFile

from pydantic import Field, field_validator, model_validator

from .contracts import Contract

PIPELINE_ILI_HEADERS = (
    "Year",
    "GWNUM",
    "JL.m",
    "RD.m",
    "SO.deg",
    "SPD.m",
    "SPO.deg",
    "EPD.m",
    "EPO.deg",
    "SIPRD.m",
    "SIPO.deg",
    "WT.mm",
    "L.mm",
    "W.mm",
    "MD.mm",
)
_SPREADSHEET_NAMESPACE = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_CELL_REFERENCE = re.compile(r"^([A-Z]+)([1-9][0-9]*)$")
_MAX_WORKSHEET_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024


class PipelineIliFeature(Contract):
    schema_version: Literal["matintegrity.pipeline_ili_feature.v1"] = "matintegrity.pipeline_ili_feature.v1"
    physical_pipeline_id: str = Field(min_length=1)
    inspection_run_id: str = Field(min_length=1)
    source_filename: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_row_number: int = Field(ge=2)
    source_role: Literal["processed_filtered_provider_observation"] = (
        "processed_filtered_provider_observation"
    )
    inspection_year_token: int
    inspection_year_is_real_asset_age: Literal[False] = False
    girth_weld_number_token: float | None
    joint_length_m: float | None
    relative_location_to_joint_m: float | None
    seam_orientation_rad: float | None
    start_absolute_distance_m: float | None
    start_circumferential_orientation_rad: float | None
    end_absolute_distance_m: float | None
    end_circumferential_orientation_rad: float | None
    significant_point_relative_distance_m: float | None
    significant_point_circumferential_orientation_rad: float | None
    nominal_wall_thickness_m: float | None
    reported_feature_length_m: float | None
    reported_feature_width_m: float | None
    reported_maximum_depth_m: float | None
    feature_identity_status: Literal["provider_row_without_physical_feature_identity"] = (
        "provider_row_without_physical_feature_identity"
    )
    quality_flags: tuple[str, ...] = ()

    @field_validator(
        "girth_weld_number_token",
        "joint_length_m",
        "relative_location_to_joint_m",
        "seam_orientation_rad",
        "start_absolute_distance_m",
        "start_circumferential_orientation_rad",
        "end_absolute_distance_m",
        "end_circumferential_orientation_rad",
        "significant_point_relative_distance_m",
        "significant_point_circumferential_orientation_rad",
        "nominal_wall_thickness_m",
        "reported_feature_length_m",
        "reported_feature_width_m",
        "reported_maximum_depth_m",
    )
    @classmethod
    def finite_optional_values(cls, value):
        if value is not None and not math.isfinite(value):
            raise ValueError("ILI numeric values must be finite when present")
        return value


class PipelineIliWorkbookAudit(Contract):
    schema_version: Literal["matintegrity.pipeline_ili_workbook_audit.v1"] = (
        "matintegrity.pipeline_ili_workbook_audit.v1"
    )
    source_filename: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_bytes: int = Field(gt=0)
    sheet_name: str = Field(min_length=1)
    headers: tuple[str, ...]
    expected_inspection_year_token: int
    observed_inspection_year_tokens: tuple[int, ...]
    observation_count: int = Field(ge=0)
    missing_count_by_header: dict[str, int]
    numeric_minimum_by_header: dict[str, float | None]
    numeric_maximum_by_header: dict[str, float | None]
    nonnumeric_count_by_header: dict[str, int]
    formula_cell_count: int = Field(ge=0)
    year_mismatch_count: int = Field(ge=0)

    @model_validator(mode="after")
    def aligned_header_statistics(self):
        keys = set(self.headers)
        for values, label in (
            (self.missing_count_by_header, "missing counts"),
            (self.numeric_minimum_by_header, "numeric minima"),
            (self.numeric_maximum_by_header, "numeric maxima"),
            (self.nonnumeric_count_by_header, "nonnumeric counts"),
        ):
            if set(values) != keys:
                raise ValueError(f"ILI {label} must align with headers")
        return self


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _open_sheet(path: Path, *, data_only: bool):
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ImportError("pipeline ILI workbook reading requires the science dependency openpyxl") from exc
    workbook = load_workbook(path, read_only=True, data_only=data_only, keep_links=False)
    if len(workbook.sheetnames) != 1:
        workbook.close()
        raise ValueError("pipeline ILI workbook must contain exactly one worksheet")
    sheet = workbook[workbook.sheetnames[0]]
    headers = tuple(cell.value for cell in next(sheet.iter_rows(min_row=1, max_row=1)))
    if headers != PIPELINE_ILI_HEADERS:
        workbook.close()
        raise ValueError("pipeline ILI workbook headers differ from the reviewed contract")
    return workbook, sheet


def _optional_float(value) -> float | None:
    if value is None:
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("pipeline ILI workbook contains a non-finite numeric value")
    return result


def _to_rad(value) -> float | None:
    result = _optional_float(value)
    return None if result is None else math.radians(result)


def _to_m_from_mm(value) -> float | None:
    result = _optional_float(value)
    return None if result is None else result * 1e-3


def iter_pipeline_ili_features(
    path: str | Path,
    *,
    physical_pipeline_id: str,
    inspection_run_id: str,
    expected_inspection_year_token: int,
    expected_sha256: str,
    start_provider_row: int = 2,
    stop_provider_row: int | None = None,
) -> Iterator[PipelineIliFeature]:
    """Yield SI-normalized provider rows while preserving source row and missing values."""
    if not physical_pipeline_id.strip() or not inspection_run_id.strip():
        raise ValueError("pipeline and inspection-run identities are required")
    if start_provider_row < 2:
        raise ValueError("pipeline ILI data start row must be at least two")
    if stop_provider_row is not None and stop_provider_row < start_provider_row:
        raise ValueError("pipeline ILI stop row precedes start row")
    source = Path(path).resolve()
    actual_sha256 = _sha256(source)
    if actual_sha256 != expected_sha256:
        raise ValueError("pipeline ILI workbook SHA-256 differs from the caller-pinned value")
    # Keep formulas visible so a provider or user workbook cannot smuggle a
    # cached spreadsheet result into the independently reviewed numeric path.
    workbook, sheet = _open_sheet(source, data_only=False)
    try:
        for provider_row_number, row in enumerate(
            sheet.iter_rows(min_row=start_provider_row, max_row=stop_provider_row, values_only=True),
            start=start_provider_row,
        ):
            if len(row) != len(PIPELINE_ILI_HEADERS):
                raise ValueError("pipeline ILI row width differs from the reviewed contract")
            if any(isinstance(value, str) and value.startswith("=") for value in row):
                raise ValueError("pipeline ILI reader rejects formula cells")
            year = int(row[0])
            if year != expected_inspection_year_token:
                raise ValueError("pipeline ILI row year differs from the caller-declared inspection run")
            flags = []
            for name, value in zip(
                (
                    "joint_length",
                    "relative_location",
                    "start_distance",
                    "end_distance",
                    "significant_distance",
                ),
                (row[2], row[3], row[5], row[7], row[9]),
                strict=True,
            ):
                if value is not None and float(value) < 0:
                    flags.append(f"negative_{name}_preserved")
            for name, value in zip(
                ("wall_thickness", "feature_length", "feature_width", "maximum_depth"),
                row[11:15],
                strict=True,
            ):
                if value is not None and float(value) < 0:
                    flags.append(f"negative_{name}_preserved")
            yield PipelineIliFeature(
                physical_pipeline_id=physical_pipeline_id,
                inspection_run_id=inspection_run_id,
                source_filename=source.name,
                source_sha256=actual_sha256,
                provider_row_number=provider_row_number,
                inspection_year_token=year,
                girth_weld_number_token=_optional_float(row[1]),
                joint_length_m=_optional_float(row[2]),
                relative_location_to_joint_m=_optional_float(row[3]),
                seam_orientation_rad=_to_rad(row[4]),
                start_absolute_distance_m=_optional_float(row[5]),
                start_circumferential_orientation_rad=_to_rad(row[6]),
                end_absolute_distance_m=_optional_float(row[7]),
                end_circumferential_orientation_rad=_to_rad(row[8]),
                significant_point_relative_distance_m=_optional_float(row[9]),
                significant_point_circumferential_orientation_rad=_to_rad(row[10]),
                nominal_wall_thickness_m=_to_m_from_mm(row[11]),
                reported_feature_length_m=_to_m_from_mm(row[12]),
                reported_feature_width_m=_to_m_from_mm(row[13]),
                reported_maximum_depth_m=_to_m_from_mm(row[14]),
                quality_flags=tuple(flags),
            )
    finally:
        workbook.close()


def audit_pipeline_ili_workbook(
    path: str | Path,
    *,
    expected_inspection_year_token: int,
    expected_sha256: str,
) -> PipelineIliWorkbookAudit:
    """Scan every provider cell without evaluating formulas or inferring feature tracks."""
    source = Path(path).resolve()
    actual_sha256 = _sha256(source)
    if actual_sha256 != expected_sha256:
        raise ValueError("pipeline ILI workbook SHA-256 differs from the caller-pinned value")
    with ZipFile(source) as archive:
        worksheet_members = [
            item
            for item in archive.infolist()
            if item.filename.startswith("xl/worksheets/")
            and item.filename.endswith(".xml")
            and "/_rels/" not in item.filename
        ]
        if len(worksheet_members) != 1:
            raise ValueError("pipeline ILI workbook must contain exactly one worksheet")
        worksheet_member = worksheet_members[0]
        if worksheet_member.file_size > _MAX_WORKSHEET_UNCOMPRESSED_BYTES:
            raise ValueError("pipeline ILI worksheet exceeds the audit safety limit")
        shared_strings = _read_shared_strings(archive)
        sheet_name = _read_single_sheet_name(archive)
        with archive.open(worksheet_member) as stream:
            row_iterator = _iter_xlsx_rows(stream, shared_strings)
            try:
                header_row_number, header_values, header_formula_count = next(row_iterator)
            except StopIteration as exc:
                raise ValueError("pipeline ILI workbook has no header row") from exc
            headers = tuple(header_values)
            if header_row_number != 1 or headers != PIPELINE_ILI_HEADERS:
                raise ValueError("pipeline ILI workbook headers differ from the reviewed contract")
            if header_formula_count:
                raise ValueError("pipeline ILI workbook header must not contain formulas")
            audit_rows = list(_audit_xlsx_rows(row_iterator, expected_inspection_year_token))
    if len(audit_rows) != 1:
        raise RuntimeError("pipeline ILI worksheet audit did not produce exactly one result")
    row_audit = audit_rows[0]
    return PipelineIliWorkbookAudit(
        source_filename=source.name,
        source_sha256=actual_sha256,
        source_bytes=source.stat().st_size,
        sheet_name=sheet_name,
        headers=PIPELINE_ILI_HEADERS,
        expected_inspection_year_token=expected_inspection_year_token,
        observed_inspection_year_tokens=tuple(sorted(row_audit["years"])),
        observation_count=row_audit["observation_count"],
        missing_count_by_header=row_audit["missing"],
        numeric_minimum_by_header=row_audit["minima"],
        numeric_maximum_by_header=row_audit["maxima"],
        nonnumeric_count_by_header=row_audit["nonnumeric"],
        formula_cell_count=row_audit["formula_count"],
        year_mismatch_count=row_audit["year_mismatch_count"],
    )


def _read_shared_strings(archive: ZipFile) -> tuple[str, ...]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return ()
    strings = []
    with archive.open("xl/sharedStrings.xml") as stream:
        for _, element in ET.iterparse(stream, events=("end",)):
            if element.tag == f"{_SPREADSHEET_NAMESPACE}si":
                strings.append(
                    "".join(node.text or "" for node in element.iter(f"{_SPREADSHEET_NAMESPACE}t"))
                )
                element.clear()
    return tuple(strings)


def _read_single_sheet_name(archive: ZipFile) -> str:
    with archive.open("xl/workbook.xml") as stream:
        root = ET.parse(stream).getroot()
    sheets = root.findall(f".//{_SPREADSHEET_NAMESPACE}sheet")
    if len(sheets) != 1:
        raise ValueError("pipeline ILI workbook must declare exactly one worksheet")
    return sheets[0].attrib["name"]


def _column_index(cell_reference: str) -> int:
    match = _CELL_REFERENCE.fullmatch(cell_reference)
    if match is None:
        raise ValueError("pipeline ILI workbook contains an invalid cell reference")
    result = 0
    for character in match.group(1):
        result = result * 26 + ord(character) - ord("A") + 1
    return result - 1


def _iter_xlsx_rows(stream, shared_strings: tuple[str, ...]):
    for _, row_element in ET.iterparse(stream, events=("end",)):
        if row_element.tag != f"{_SPREADSHEET_NAMESPACE}row":
            continue
        row_number = int(row_element.attrib["r"])
        values: list[object | None] = [None] * len(PIPELINE_ILI_HEADERS)
        formula_count = 0
        for cell in row_element.findall(f"{_SPREADSHEET_NAMESPACE}c"):
            index = _column_index(cell.attrib["r"])
            if index >= len(values):
                raise ValueError("pipeline ILI row contains a column outside the reviewed contract")
            if cell.find(f"{_SPREADSHEET_NAMESPACE}f") is not None:
                formula_count += 1
                values[index] = "__FORMULA_CELL_NOT_EVALUATED__"
                continue
            cell_type = cell.attrib.get("t")
            if cell_type == "inlineStr":
                values[index] = "".join(node.text or "" for node in cell.iter(f"{_SPREADSHEET_NAMESPACE}t"))
                continue
            value_element = cell.find(f"{_SPREADSHEET_NAMESPACE}v")
            if value_element is None or value_element.text is None:
                continue
            raw = value_element.text
            if cell_type == "s":
                values[index] = shared_strings[int(raw)]
            elif cell_type in {None, "n"}:
                values[index] = raw
            elif cell_type == "b":
                values[index] = raw
            else:
                values[index] = raw
        yield row_number, values, formula_count
        row_element.clear()


def _audit_xlsx_rows(row_iterator, expected_inspection_year_token: int):
    missing = {name: 0 for name in PIPELINE_ILI_HEADERS}
    minima: dict[str, float | None] = {name: None for name in PIPELINE_ILI_HEADERS}
    maxima: dict[str, float | None] = {name: None for name in PIPELINE_ILI_HEADERS}
    nonnumeric = {name: 0 for name in PIPELINE_ILI_HEADERS}
    years: set[int] = set()
    formula_count = 0
    year_mismatch_count = 0
    observation_count = 0
    for row_number, row, row_formula_count in row_iterator:
        if row_number < 2:
            continue
        observation_count += 1
        formula_count += row_formula_count
        for name, value in zip(PIPELINE_ILI_HEADERS, row, strict=True):
            if value is None:
                missing[name] += 1
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                nonnumeric[name] += 1
                continue
            if not math.isfinite(numeric):
                nonnumeric[name] += 1
                continue
            minima[name] = numeric if minima[name] is None else min(minima[name], numeric)
            maxima[name] = numeric if maxima[name] is None else max(maxima[name], numeric)
        if row[0] is not None:
            try:
                year = int(float(row[0]))
            except (TypeError, ValueError):
                year_mismatch_count += 1
            else:
                years.add(year)
                if year != expected_inspection_year_token:
                    year_mismatch_count += 1
    yield {
        "missing": missing,
        "minima": minima,
        "maxima": maxima,
        "nonnumeric": nonnumeric,
        "years": years,
        "formula_count": formula_count,
        "year_mismatch_count": year_mismatch_count,
        "observation_count": observation_count,
    }

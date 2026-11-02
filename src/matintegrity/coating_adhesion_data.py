"""Read pinned coating pull-off observations while retaining unresolved source units."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import Field

from .contracts import Contract

DATASET_ID = "zenodo-4777893-coating-adhesion"
PROVIDER_RECORD = "https://doi.org/10.5281/zenodo.4777893"
LICENSE_ID = "CC-BY-4.0"
FILENAME = "Adhesion strength.xlsx"
SOURCE_SHA256 = "86400b73328cae2c4c6ed23f643b44b134982a675f4f7fbca9b4065ece4cdd98"


class CoatingAdhesionGroupRecord(Contract):
    schema_version: Literal["matintegrity.coating_adhesion_group.v1"] = (
        "matintegrity.coating_adhesion_group.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_sheet_name: Literal["ADHESION"] = "ADHESION"
    source_row: int = Field(ge=3, le=34)
    provider_sample_label: str = Field(min_length=1)
    provider_condition: Literal[
        "climate_room",
        "ambient_laboratory",
        "after_water_absorption",
        "primer_plus_coating_section_condition_unresolved",
    ]
    observation_count: int = Field(ge=2, le=5)
    provider_native_values: tuple[float, ...] = Field(min_length=2, max_length=5)
    quantity_label: Literal["adhesion_strength"] = "adhesion_strength"
    unit_status: Literal["not_declared_in_workbook_or_readme"] = "not_declared_in_workbook_or_readme"
    substrate: Literal["wood"] = "wood"
    physical_dolly_identity_status: Literal["column_label_only"] = "column_label_only"
    interpretation_status: Literal["raw_replicates_not_metal_coating_qualification"] = (
        "raw_replicates_not_metal_coating_qualification"
    )


class CoatingAdhesionDatasetAudit(Contract):
    schema_version: Literal["matintegrity.coating_adhesion_dataset_audit.v1"] = (
        "matintegrity.coating_adhesion_dataset_audit.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    groups: tuple[CoatingAdhesionGroupRecord, ...] = Field(min_length=35, max_length=35)
    group_count: Literal[35]
    raw_observation_count: Literal[107]
    formula_cells_used_as_observations: Literal[False] = False
    unit_status: Literal["withheld_no_source_unit_label"] = "withheld_no_source_unit_label"
    calibration_use_status: Literal["withheld_wood_substrate_and_missing_test_metadata"] = (
        "withheld_wood_substrate_and_missing_test_metadata"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _numeric_cells(sheet, row: int, columns: tuple[int, ...]) -> tuple[float, ...]:
    values = []
    for column in columns:
        value = sheet.cell(row, column).value
        if isinstance(value, bool):
            raise ValueError("coating adhesion observation cannot be boolean")
        if isinstance(value, (int, float)):
            values.append(float(value))
    return tuple(values)


def read_coating_adhesion_workbook(
    path: str | Path,
    *,
    expected_sha256: str = SOURCE_SHA256,
) -> CoatingAdhesionDatasetAudit:
    """Return raw provider-native replicates without inventing a stress unit or qualification."""
    source = Path(path)
    actual = _sha256(source)
    if actual != expected_sha256:
        raise ValueError("coating adhesion workbook SHA-256 differs from the pinned digest")
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover
        raise ImportError("coating adhesion XLSX reading requires openpyxl") from exc
    workbook = load_workbook(source, read_only=True, data_only=False)
    try:
        if workbook.sheetnames != ["ADHESION", "COLOR", "pH and adhesion correlation"]:
            raise ValueError("coating adhesion workbook sheet identities differ")
        sheet = workbook["ADHESION"]
        if sheet.max_row != 50 or sheet.max_column != 24:
            raise ValueError("coating adhesion workbook shape differs")
        if sheet.cell(2, 1).value != "Sample" or sheet.cell(9, 1).value != "Primers + coatings":
            raise ValueError("coating adhesion identity headers differ")
        records = []
        condition_columns = (
            ("climate_room", (2, 3, 4)),
            ("ambient_laboratory", (7, 8, 9, 10, 11)),
            ("after_water_absorption", (14, 15, 16)),
        )
        for row in range(3, 8):
            label = sheet.cell(row, 1).value
            if not isinstance(label, str) or not label.strip():
                raise ValueError("coating adhesion sample label is missing")
            for condition, columns in condition_columns:
                values = _numeric_cells(sheet, row, columns)
                if len(values) < 2 or any(value < 0 for value in values):
                    raise ValueError("coating adhesion raw replicate group is invalid")
                records.append(
                    CoatingAdhesionGroupRecord(
                        source_file_sha256=actual,
                        source_row=row,
                        provider_sample_label=label.strip(),
                        provider_condition=condition,
                        observation_count=len(values),
                        provider_native_values=values,
                    )
                )
        primer_rows = (*range(12, 17), *range(18, 23), *range(24, 29), *range(30, 35))
        for row in primer_rows:
            label = sheet.cell(row, 1).value
            if not isinstance(label, str) or not label.strip():
                raise ValueError("primer-plus-coating sample label is missing")
            values = _numeric_cells(sheet, row, (2, 3, 4, 5))
            if len(values) < 2 or any(value < 0 for value in values):
                raise ValueError("primer-plus-coating raw replicate group is invalid")
            records.append(
                CoatingAdhesionGroupRecord(
                    source_file_sha256=actual,
                    source_row=row,
                    provider_sample_label=label.strip(),
                    provider_condition="primer_plus_coating_section_condition_unresolved",
                    observation_count=len(values),
                    provider_native_values=values,
                )
            )
    finally:
        workbook.close()
    return CoatingAdhesionDatasetAudit(
        source_file_sha256=actual,
        groups=tuple(records),
        group_count=len(records),
        raw_observation_count=sum(record.observation_count for record in records),
    )

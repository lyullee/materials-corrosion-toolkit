"""Read a pinned HyMatBase hydrogen fatigue workbook without resolving source conflicts."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .contracts import Contract

HYDROGEN_FATIGUE_SERIES_COLUMNS = (("E", "F"), ("H", "I"), ("K", "L"), ("N", "O"))


class HydrogenFatigueSeries(Contract):
    schema_version: Literal["matintegrity.hydrogen_fatigue_series.v1"] = (
        "matintegrity.hydrogen_fatigue_series.v1"
    )
    series_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    physical_material_condition_id: str = Field(min_length=1)
    material_designation_token: str = Field(min_length=1)
    product_form_token: str = Field(min_length=1)
    temper_token: str = Field(min_length=1)
    microstructure_token: str = Field(min_length=1)
    environment_token: str = Field(min_length=1)
    workbook_pressure_Pa: float = Field(gt=0)
    provider_record_pressure_Pa: float | None = Field(default=None, gt=0)
    pressure_reconciliation_status: Literal[
        "record_not_supplied", "record_matches_workbook", "record_conflicts_with_workbook"
    ]
    pressure_conflict_acknowledged: bool
    workbook_temperature_token: str = Field(min_length=1)
    provider_record_temperature_K: float | None = Field(default=None, gt=0)
    specimen_orientation_token: str = Field(min_length=1)
    test_method_token: str = Field(min_length=1)
    stress_ratio: float
    frequency_Hz: float = Field(gt=0)
    source_filename: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_sheet: Literal["Mechanical Properties-Fatigue"] = "Mechanical Properties-Fatigue"
    source_delta_k_column: str = Field(pattern=r"^[A-Z]+$")
    source_growth_column: str = Field(pattern=r"^[A-Z]+$")
    physical_specimen_identity_status: Literal["not_supplied_in_workbook"] = "not_supplied_in_workbook"
    validity_status: Literal["provider_method_named_validity_not_independently_reviewed"] = (
        "provider_method_named_validity_not_independently_reviewed"
    )
    point_count: int = Field(gt=0)

    @field_validator("workbook_pressure_Pa", "provider_record_pressure_Pa", "frequency_Hz")
    @classmethod
    def finite_values(cls, value):
        if value is not None and not math.isfinite(value):
            raise ValueError("hydrogen fatigue series values must be finite")
        return value

    @model_validator(mode="after")
    def conflict_is_acknowledged(self):
        if self.pressure_reconciliation_status == "record_conflicts_with_workbook":
            if not self.pressure_conflict_acknowledged:
                raise ValueError("provider record/workbook pressure conflict must be acknowledged")
        elif self.pressure_conflict_acknowledged:
            raise ValueError("pressure conflict acknowledgement is only valid for a detected conflict")
        return self


class HydrogenFatigueGrowthPoint(Contract):
    schema_version: Literal["matintegrity.hydrogen_fatigue_growth_point.v1"] = (
        "matintegrity.hydrogen_fatigue_growth_point.v1"
    )
    series_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    physical_material_condition_id: str = Field(min_length=1)
    source_filename: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_sheet: Literal["Mechanical Properties-Fatigue"] = "Mechanical Properties-Fatigue"
    provider_row_number: int = Field(ge=14)
    delta_k_Pa_sqrt_m: float = Field(gt=0)
    crack_growth_m_cycle: float = Field(gt=0)
    source_role: Literal["provider_reported_curve_point"] = "provider_reported_curve_point"
    physical_specimen_id: None = None
    independent_observation_status: Literal["not_established_from_workbook"] = "not_established_from_workbook"

    @field_validator("delta_k_Pa_sqrt_m", "crack_growth_m_cycle")
    @classmethod
    def finite_values(cls, value):
        if not math.isfinite(value):
            raise ValueError("hydrogen fatigue point values must be finite")
        return value


class HydrogenFatigueWorkbookAudit(Contract):
    schema_version: Literal["matintegrity.hydrogen_fatigue_workbook_audit.v1"] = (
        "matintegrity.hydrogen_fatigue_workbook_audit.v1"
    )
    source_filename: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_bytes: int = Field(gt=0)
    worksheet_names: tuple[str, ...]
    formula_cell_count: int = Field(ge=0)
    series_count: int = Field(gt=0)
    point_count: int = Field(gt=0)
    point_count_by_series: dict[str, int]
    delta_k_minimum_Pa_sqrt_m: float = Field(gt=0)
    delta_k_maximum_Pa_sqrt_m: float = Field(gt=0)
    crack_growth_minimum_m_cycle: float = Field(gt=0)
    crack_growth_maximum_m_cycle: float = Field(gt=0)
    pressure_reconciliation_status: Literal[
        "record_not_supplied", "record_matches_workbook", "record_conflicts_with_workbook"
    ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _number(value, *, label: str, positive: bool = False) -> float:
    if isinstance(value, str) and value.startswith("="):
        raise ValueError(f"hydrogen fatigue reader rejects formula in {label}")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"hydrogen fatigue {label} must be numeric") from exc
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValueError(f"hydrogen fatigue {label} must be positive and finite")
    return result


def _load_workbook(path: Path):
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ImportError("hydrogen fatigue workbook reading requires openpyxl") from exc
    return load_workbook(path, read_only=False, data_only=False, keep_links=False)


def read_hymatbase_hydrogen_fatigue(
    path: str | Path,
    *,
    expected_sha256: str,
    source_group_id: str,
    physical_material_condition_id: str,
    provider_record_pressure_Pa: float | None,
    provider_record_temperature_K: float | None,
    acknowledge_pressure_conflict: bool = False,
) -> tuple[tuple[HydrogenFatigueSeries, ...], tuple[HydrogenFatigueGrowthPoint, ...]]:
    """Read four provider curves while preserving the record/workbook pressure disagreement."""
    if not source_group_id.strip() or not physical_material_condition_id.strip():
        raise ValueError("source group and physical material-condition identities are required")
    source = Path(path).resolve()
    actual_sha256 = _sha256(source)
    if actual_sha256 != expected_sha256:
        raise ValueError("hydrogen fatigue workbook SHA-256 differs from the caller-pinned value")
    workbook = _load_workbook(source)
    try:
        required = {
            "Material",
            "Environment",
            "Mechanical Properties-Fracture",
            "Mechanical Properties-Fatigue",
            "fatigue plot",
        }
        if set(workbook.sheetnames) != required:
            raise ValueError("hydrogen fatigue workbook sheet names differ from the reviewed contract")
        material = workbook["Material"]
        environment = workbook["Environment"]
        fatigue = workbook["Mechanical Properties-Fatigue"]
        if (
            tuple(fatigue.cell(12, column).value for column in (5, 6, 8, 9, 11, 12, 14, 15))
            != (
                "∆K\n(MPa m1/2)",
                "da/dN\n(m/cycle)",
            )
            * 4
        ):
            raise ValueError("hydrogen fatigue curve headers differ from the reviewed contract")
        if tuple(environment.cell(row, 4).value for row in (7, 8, 9)) != (
            "Temperature (\u02daC)",
            "Pressure (MPa)",
            "test environment",
        ):
            raise ValueError("hydrogen fatigue environment labels differ from the reviewed contract")

        workbook_pressure_pa = (
            _number(environment["F8"].value, label="workbook pressure", positive=True) * 1e6
        )
        if provider_record_pressure_Pa is None:
            reconciliation = "record_not_supplied"
        elif math.isclose(provider_record_pressure_Pa, workbook_pressure_pa, rel_tol=1e-12):
            reconciliation = "record_matches_workbook"
        else:
            reconciliation = "record_conflicts_with_workbook"
        if reconciliation == "record_conflicts_with_workbook" and not acknowledge_pressure_conflict:
            raise ValueError("provider record/workbook pressure conflict must be acknowledged")
        if reconciliation != "record_conflicts_with_workbook" and acknowledge_pressure_conflict:
            raise ValueError("pressure conflict acknowledgement supplied without a detected conflict")

        points: list[HydrogenFatigueGrowthPoint] = []
        series: list[HydrogenFatigueSeries] = []
        for delta_column, growth_column in HYDROGEN_FATIGUE_SERIES_COLUMNS:
            delta_index = fatigue[delta_column + "1"].column
            growth_index = fatigue[growth_column + "1"].column
            stress_ratio = _number(fatigue.cell(8, growth_index).value, label="stress ratio")
            frequency = _number(fatigue.cell(9, growth_index).value, label="frequency", positive=True)
            series_id = f"R={stress_ratio:g};f={frequency:g}Hz;cols={delta_column}-{growth_column}"
            series_points = []
            for row_number in range(14, fatigue.max_row + 1):
                delta_value = fatigue.cell(row_number, delta_index).value
                growth_value = fatigue.cell(row_number, growth_index).value
                if delta_value is None and growth_value is None:
                    continue
                if delta_value is None or growth_value is None:
                    raise ValueError("hydrogen fatigue point pair contains one missing value")
                point = HydrogenFatigueGrowthPoint(
                    series_id=series_id,
                    source_group_id=source_group_id,
                    physical_material_condition_id=physical_material_condition_id,
                    source_filename=source.name,
                    source_sha256=actual_sha256,
                    provider_row_number=row_number,
                    delta_k_Pa_sqrt_m=_number(delta_value, label="delta K", positive=True) * 1e6,
                    crack_growth_m_cycle=_number(growth_value, label="crack growth", positive=True),
                )
                points.append(point)
                series_points.append(point)
            if not series_points:
                raise ValueError("hydrogen fatigue series contains no points")
            series.append(
                HydrogenFatigueSeries(
                    series_id=series_id,
                    source_group_id=source_group_id,
                    physical_material_condition_id=physical_material_condition_id,
                    material_designation_token=str(material["A1"].value).strip(),
                    product_form_token=str(material["A3"].value).strip(),
                    temper_token=str(material["A4"].value).strip(),
                    microstructure_token=str(material["F9"].value).strip(),
                    environment_token=str(environment["F9"].value).strip(),
                    workbook_pressure_Pa=workbook_pressure_pa,
                    provider_record_pressure_Pa=provider_record_pressure_Pa,
                    pressure_reconciliation_status=reconciliation,
                    pressure_conflict_acknowledged=acknowledge_pressure_conflict,
                    workbook_temperature_token=str(environment["F7"].value).strip(),
                    provider_record_temperature_K=provider_record_temperature_K,
                    specimen_orientation_token=str(fatigue.cell(6, growth_index).value).strip(),
                    test_method_token=str(fatigue.cell(7, growth_index).value).strip(),
                    stress_ratio=stress_ratio,
                    frequency_Hz=frequency,
                    source_filename=source.name,
                    source_sha256=actual_sha256,
                    source_delta_k_column=delta_column,
                    source_growth_column=growth_column,
                    point_count=len(series_points),
                )
            )
        return tuple(series), tuple(points)
    finally:
        workbook.close()


def audit_hymatbase_hydrogen_fatigue(
    path: str | Path,
    *,
    expected_sha256: str,
    source_group_id: str,
    physical_material_condition_id: str,
    provider_record_pressure_Pa: float | None,
    provider_record_temperature_K: float | None,
    acknowledge_pressure_conflict: bool = False,
) -> HydrogenFatigueWorkbookAudit:
    """Return aggregate structure evidence without copying pointwise provider data."""
    source = Path(path).resolve()
    series, points = read_hymatbase_hydrogen_fatigue(
        source,
        expected_sha256=expected_sha256,
        source_group_id=source_group_id,
        physical_material_condition_id=physical_material_condition_id,
        provider_record_pressure_Pa=provider_record_pressure_Pa,
        provider_record_temperature_K=provider_record_temperature_K,
        acknowledge_pressure_conflict=acknowledge_pressure_conflict,
    )
    workbook = _load_workbook(source)
    try:
        formula_count = sum(
            1
            for sheet in workbook.worksheets
            for row in sheet.iter_rows()
            for cell in row
            if cell.data_type == "f"
        )
        sheet_names = tuple(workbook.sheetnames)
    finally:
        workbook.close()
    return HydrogenFatigueWorkbookAudit(
        source_filename=source.name,
        source_sha256=_sha256(source),
        source_bytes=source.stat().st_size,
        worksheet_names=sheet_names,
        formula_cell_count=formula_count,
        series_count=len(series),
        point_count=len(points),
        point_count_by_series={item.series_id: item.point_count for item in series},
        delta_k_minimum_Pa_sqrt_m=min(item.delta_k_Pa_sqrt_m for item in points),
        delta_k_maximum_Pa_sqrt_m=max(item.delta_k_Pa_sqrt_m for item in points),
        crack_growth_minimum_m_cycle=min(item.crack_growth_m_cycle for item in points),
        crack_growth_maximum_m_cycle=max(item.crack_growth_m_cycle for item in points),
        pressure_reconciliation_status=series[0].pressure_reconciliation_status,
    )

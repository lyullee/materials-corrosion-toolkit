"""Read a pinned pressure-decay workbook without inferring a leak rate."""

from __future__ import annotations

import hashlib
from pathlib import Path
from collections.abc import Iterator
from typing import Literal

import numpy as np
from pydantic import Field

from .contracts import Calculation, Contract, canonical_digest
from .registry import ModelSpec

DATASET_ID = "zenodo-20582921-pressure-decay-leak-test"
PROVIDER_RECORD = "https://doi.org/10.5281/zenodo.20582921"
LICENSE_ID = "CC-BY-4.0"
FILENAME = "DataSet Temperatue-Pressure.xlsx"
SOURCE_SHA256 = "f2b34758d95a2ebb43ee4ec4630acefdc331ce8f4e6e8477bfda8b4248fda5ad"
ROW_ADAPTER_SOURCE_ID = "zenodo_pressure_decay_leak_sample_row_adapter"

SERIES_COLUMNS = (
    ("Nitorgen N2", "nitrogen", 100.0, 2, 3),
    ("Nitorgen N2", "nitrogen", 20.0, 4, 5),
    ("Air", "air", 100.0, 6, 7),
    ("Air", "air", 20.0, 8, 9),
    ("Argon Ar", "argon", 100.0, 10, 11),
    ("Argon Ar", "argon", 20.0, 12, 13),
    ("Carbon dioxide CO2", "carbon_dioxide", 100.0, 14, 15),
    ("Carbon dioxide CO2", "carbon_dioxide", 20.0, 16, 17),
    ("Propane-butane PB", "propane_butane", 100.0, 18, 19),
    ("Propane-butane PB", "propane_butane", 20.0, 20, 21),
)


class PressureDecayLeakSeriesRecord(Contract):
    schema_version: Literal["matintegrity.pressure_decay_leak_series.v1"] = (
        "matintegrity.pressure_decay_leak_series.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_sheet_name: str = Field(min_length=1)
    series_id: str = Field(min_length=1)
    provider_gas_label: str = Field(min_length=1)
    normalized_gas_label: Literal["nitrogen", "air", "argon", "carbon_dioxide", "propane_butane"]
    provider_capillary_length_m: float = Field(gt=0)
    sample_count: Literal[31]
    time_unit: Literal["s"] = "s"
    temperature_unit: Literal["K"] = "K"
    temperature_role: Literal["unresolved_ambient_or_internal"] = "unresolved_ambient_or_internal"
    pressure_unit: Literal["Pa"] = "Pa"
    pressure_basis: Literal["relative_gauge_provider_description"] = "relative_gauge_provider_description"
    minimum_temperature_K: float = Field(gt=0)
    maximum_temperature_K: float = Field(gt=0)
    minimum_pressure_Pa: float = Field(ge=0)
    maximum_pressure_Pa: float = Field(ge=0)
    timestamps_strictly_increasing: Literal[True]
    reference_or_blank_series_present: Literal[False] = False
    interpretation_status: Literal["raw_pressure_temperature_not_leak_rate"] = (
        "raw_pressure_temperature_not_leak_rate"
    )


class PressureDecayLeakDatasetAudit(Contract):
    schema_version: Literal["matintegrity.pressure_decay_leak_dataset_audit.v1"] = (
        "matintegrity.pressure_decay_leak_dataset_audit.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    series: tuple[PressureDecayLeakSeriesRecord, ...] = Field(min_length=10, max_length=10)
    series_count: Literal[10]
    total_samples: Literal[310]
    provider_description_configuration_count: Literal[3]
    workbook_configuration_count: Literal[2]
    missing_configuration: Literal["reference_state_without_artificial_defect"]
    calibration_use_status: Literal["withheld_missing_blank_volume_and_pressure_basis"] = (
        "withheld_missing_blank_volume_and_pressure_basis"
    )


class PressureDecayLeakReadAuthorization(Contract):
    """Caller authorization and attribution required for a local row-view call."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class PressureDecayLeakArchiveAuditRequest(Contract):
    """Audit the exact locally pinned workbook and keep its path private."""

    local_archive_path: str = Field(min_length=1)
    authorization: PressureDecayLeakReadAuthorization


class PressureDecayLeakSample(Contract):
    """One sample from a pinned pressure/temperature series; not a leak-rate datum."""

    schema_version: Literal["matintegrity.pressure_decay_leak_sample.v1"] = (
        "matintegrity.pressure_decay_leak_sample.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_sheet_name: str = Field(min_length=1)
    series_id: str = Field(min_length=1)
    provider_gas_label: str = Field(min_length=1)
    normalized_gas_label: Literal["nitrogen", "air", "argon", "carbon_dioxide", "propane_butane"]
    provider_capillary_length_m: float = Field(gt=0)
    sample_index: int = Field(ge=0, le=30, strict=True)
    time_s: float = Field(ge=0)
    temperature_K: float = Field(gt=0)
    pressure_Pa: float = Field(ge=0)
    temperature_role: Literal["unresolved_ambient_or_internal"] = "unresolved_ambient_or_internal"
    pressure_basis: Literal["relative_gauge_provider_description"] = "relative_gauge_provider_description"
    interpretation_status: Literal["raw_pressure_temperature_not_leak_rate"] = (
        "raw_pressure_temperature_not_leak_rate"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_pressure_decay_leak_workbook(
    path: str | Path,
    *,
    expected_sha256: str = SOURCE_SHA256,
) -> tuple[np.ndarray, dict[str, tuple[np.ndarray, np.ndarray]], PressureDecayLeakDatasetAudit]:
    """Return SI time/temperature/pressure arrays while withholding leak-rate inference."""
    source = Path(path)
    actual_sha256 = _sha256(source)
    if actual_sha256 != expected_sha256:
        raise ValueError("pressure-decay workbook SHA-256 differs from the caller-pinned digest")
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover
        raise ImportError("pressure-decay XLSX reading requires openpyxl") from exc
    workbook = load_workbook(source, read_only=True, data_only=False)
    try:
        if len(workbook.worksheets) != 1:
            raise ValueError("pressure-decay workbook must contain exactly one sheet")
        sheet = workbook.worksheets[0]
        if sheet.max_row != 34 or sheet.max_column < 21:
            raise ValueError("pressure-decay workbook shape differs from the reviewed source")
        if sheet.cell(1, 1).value != "Testing gas" or sheet.cell(2, 1).value != "Lenght of capilar [mm]":
            raise ValueError("pressure-decay workbook identity headers differ")
        if sheet.cell(3, 1).value != "Time t [s]":
            raise ValueError("pressure-decay time header differs")
        times = np.asarray([float(sheet.cell(row, 1).value) for row in range(4, 35)], dtype=float)
        if not np.all(np.isfinite(times)) or np.any(np.diff(times) <= 0):
            raise ValueError("pressure-decay timestamps must be finite and strictly increasing")
        if times.tolist() != [float(value) for value in range(0, 901, 30)]:
            raise ValueError("pressure-decay timestamp grid differs from the reviewed 0-900 s grid")
        arrays = {}
        records = []
        for raw_gas, normalized_gas, length_mm, temperature_column, pressure_column in SERIES_COLUMNS:
            gas_header_column = temperature_column if length_mm == 100.0 else temperature_column - 2
            if sheet.cell(1, gas_header_column).value != raw_gas:
                raise ValueError("pressure-decay gas header differs from the reviewed layout")
            if sheet.cell(2, temperature_column).value != f"{int(length_mm)} mm":
                raise ValueError("pressure-decay capillary-length header differs")
            if sheet.cell(3, temperature_column).value != "Temperatures T [°C]":
                raise ValueError("pressure-decay temperature header differs")
            if sheet.cell(3, pressure_column).value != "Pressure [Pa]":
                raise ValueError("pressure-decay pressure header differs")
            temperature_K = np.asarray(
                [float(sheet.cell(row, temperature_column).value) + 273.15 for row in range(4, 35)],
                dtype=float,
            )
            pressure_Pa = np.asarray(
                [float(sheet.cell(row, pressure_column).value) for row in range(4, 35)], dtype=float
            )
            if not np.all(np.isfinite(temperature_K)) or np.any(temperature_K <= 0):
                raise ValueError("pressure-decay temperatures must be finite absolute temperatures")
            if not np.all(np.isfinite(pressure_Pa)) or np.any(pressure_Pa < 0):
                raise ValueError("pressure-decay gauge pressures must be finite and nonnegative")
            series_id = f"{normalized_gas}-{int(length_mm)}mm"
            arrays[series_id] = (temperature_K, pressure_Pa)
            records.append(
                PressureDecayLeakSeriesRecord(
                    source_file_sha256=actual_sha256,
                    source_sheet_name=sheet.title,
                    series_id=series_id,
                    provider_gas_label=raw_gas,
                    normalized_gas_label=normalized_gas,
                    provider_capillary_length_m=length_mm / 1000.0,
                    sample_count=31,
                    minimum_temperature_K=float(np.min(temperature_K)),
                    maximum_temperature_K=float(np.max(temperature_K)),
                    minimum_pressure_Pa=float(np.min(pressure_Pa)),
                    maximum_pressure_Pa=float(np.max(pressure_Pa)),
                    timestamps_strictly_increasing=True,
                )
            )
    finally:
        workbook.close()
    audit = PressureDecayLeakDatasetAudit(
        source_file_sha256=actual_sha256,
        series=tuple(records),
        series_count=10,
        total_samples=310,
        provider_description_configuration_count=3,
        workbook_configuration_count=2,
        missing_configuration="reference_state_without_artificial_defect",
    )
    return times, arrays, audit


def iter_pressure_decay_leak_samples(
    path: str | Path,
    *,
    authorization: PressureDecayLeakReadAuthorization,
) -> Iterator[PressureDecayLeakSample]:
    """Yield a provenance-linked row view of the ten pinned provider series.

    The workbook parser still audits its exact 31-knot layout first; the iterator
    exposes those points as typed records and never infers a leak rate.
    """
    if not authorization.attribution.strip():
        raise ValueError("CC BY attribution must be nonempty")
    authorization_sha256 = canonical_digest(authorization.model_dump(mode="json"))
    times, arrays, audit = read_pressure_decay_leak_workbook(path)
    metadata = {row.series_id: row for row in audit.series}
    for series_id, (temperature_K, pressure_Pa) in arrays.items():
        series = metadata[series_id]
        for index, (time_s, temperature, pressure) in enumerate(
            zip(times, temperature_K, pressure_Pa, strict=True)
        ):
            yield PressureDecayLeakSample(
                source_file_sha256=audit.source_file_sha256,
                attribution=authorization.attribution,
                authorization_sha256=authorization_sha256,
                local_only=True,
                source_sheet_name=series.source_sheet_name,
                series_id=series.series_id,
                provider_gas_label=series.provider_gas_label,
                normalized_gas_label=series.normalized_gas_label,
                provider_capillary_length_m=series.provider_capillary_length_m,
                sample_index=index,
                time_s=float(time_s),
                temperature_K=float(temperature),
                pressure_Pa=float(pressure),
            )


def audit_pressure_decay_leak_archive(request: PressureDecayLeakArchiveAuditRequest) -> Calculation:
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY attribution must be nonempty")
    times, arrays, audit = read_pressure_decay_leak_workbook(request.local_archive_path)
    return Calculation(values={
        "model_id": "data.zenodo_pressure_decay_leak_sample_rows",
        "dataset_id": DATASET_ID,
        "provider_record": PROVIDER_RECORD,
        "license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "source_file_sha256": audit.source_file_sha256,
        "series_count": audit.series_count,
        "sample_count": audit.total_samples,
        "series_ids": [row.series_id for row in audit.series],
        "request_authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "local_path_returned": False,
        "leak_rate_inferred": False,
        "calibration_use_status": audit.calibration_use_status,
        "interpretation_limit": "provider pressure/temperature sample rows only; not a leak rate or acceptance measurement",
    }, notes=("The registered evaluator audits the pinned workbook and returns only metadata; use the row iterator for caller-authorized samples.",))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="data.zenodo_pressure_decay_leak_sample_rows",
        input_type=PressureDecayLeakArchiveAuditRequest,
        evaluator=audit_pressure_decay_leak_archive,
        units={"series_count": "1", "sample_count": "row"},
        assumptions=("The exact CC BY 4.0 workbook digest, provider layout and caller attribution are required.", "Temperature role and pressure basis remain as described by the provider; no leak-rate inference or calibration is performed."),
        source_ids=(ROW_ADAPTER_SOURCE_ID,),
        qualification="data_import",
    )]

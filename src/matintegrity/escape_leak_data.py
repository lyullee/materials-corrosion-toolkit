"""Read the pinned CC0 ESCAPE-1 methane traces without inferring leak calibration."""

from __future__ import annotations

import hashlib
import math
from datetime import time
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract

ESCAPE1_DATASET_ID = "escape1-controlled-subsurface-natural-gas-release-v1"
ESCAPE1_PROVIDER_RECORD = "https://doi.org/10.5061/dryad.8931zcrwq"
ESCAPE1_LICENSE_ID = "CC0-1.0"
ESCAPE1_README_SHA256 = "c9937d0112a7780933991833745d98a14f41fe7a7ddf8c1e8741bf664f09be74"

# Digests are calculated from the immutable files exposed by provider record 10064717.
ESCAPE1_WORKBOOKS = {
    "DEC2Measurements.xlsx": ("ed15aacac65de64d59e43d01b738f239f85f60959382b9ea393bb2e0264c55de", 20.0),
    "DEC3Measurements.xlsx": ("1821fc8d5efa092b360bfaa3e6ffa2579c620754b086cb453b92eb49f41d8998", 20.0),
    "NOV11Measurements.xlsx": ("25d1ac57a2e4ba508b43174a07647e20e62188dc480ce1d4e2d06ffc2e421aa4", 10.0),
    "NOV12Measurements.xlsx": ("a25cbec2a3da284fc111be01742d10d6dc615220f98584dd5d5ba79e5f85c08e", 10.0),
    "NOV12Measurements2.xlsx": ("96908f3958089d2e293166e060e5505118585a8cc645ced1fe77470bf676e9b4", 10.0),
    "NOV18Measurements.xlsx": ("1cf7486cf38162a3464fd32f0bcd5366d3b5afe3074064785aa55f42f324165b", 10.0),
    "NOV1Measurements.xlsx": ("a061ae8944694ec1bbb110c02a714c5e6618f676fdc870159bb8a2824bf0ea07", 5.0),
    "NOV22Measurements.xlsx": ("8e0bb5715c033e0fb76b211a1b044936f103fb5b99c1be60918501061527448c", 10.0),
    "NOV4Measurements.xlsx": ("1c6e6427861e0d5f13c73bd8105bcd670d4137d44975f924d9e6bd2e50d9b39f", 5.0),
    "OCT1Measurements.xlsx": ("387558bf3c06ea339c70a06f9c1102b61a0270455b499510057851ae9f6d6c87", 10.0),
    "SEPT30Measurements.xlsx": ("0126428a6d27b18fdc79c4678fd704f1903c52a4b42687a57081f5d0114451fa", 10.0),
}


class EscapeLeakTraceRecord(Contract):
    """Identity and structural diagnostics for one provider workbook trace."""

    schema_version: Literal["matintegrity.escape1_leak_trace.v1"] = "matintegrity.escape1_leak_trace.v1"
    dataset_id: Literal[ESCAPE1_DATASET_ID] = ESCAPE1_DATASET_ID
    provider_record: Literal[ESCAPE1_PROVIDER_RECORD] = ESCAPE1_PROVIDER_RECORD
    license_id: Literal[ESCAPE1_LICENSE_ID] = ESCAPE1_LICENSE_ID
    provider_experiment_file_id: str = Field(min_length=1)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_sheet_name: str = Field(min_length=1)
    sample_count: int = Field(gt=1)
    time_quantity: Literal["provider_local_time_of_day"] = "provider_local_time_of_day"
    time_unit: Literal["s_from_local_midnight"] = "s_from_local_midnight"
    time_zone: Literal["Mountain Time_provider_statement_without_dst_resolution"] = (
        "Mountain Time_provider_statement_without_dst_resolution"
    )
    methane_response_quantity: Literal["path_integrated_methane_mixing_ratio"] = (
        "path_integrated_methane_mixing_ratio"
    )
    methane_response_unit: Literal["ppm_m"] = "ppm_m"
    provider_declared_leak_rate_value: float = Field(gt=0)
    provider_declared_leak_rate_unit: Literal["standard_litre_per_minute"] = "standard_litre_per_minute"
    leak_reference_pressure_temperature: Literal["unresolved"] = "unresolved"
    detector_height_m: Literal[2.0] = 2.0
    nominal_burial_depth_m: Literal[0.9] = 0.9
    timestamps_strictly_increasing: Literal[True]
    minimum_sample_interval_s: float = Field(gt=0)
    maximum_sample_interval_s: float = Field(gt=0)
    minimum_response_ppm_m: float = Field(ge=0)
    maximum_response_ppm_m: float = Field(ge=0)
    physical_independence_status: Literal["unresolved_across_experiment_files"] = (
        "unresolved_across_experiment_files"
    )
    interpretation_status: Literal["raw_response_not_calibration_ready"] = (
        "raw_response_not_calibration_ready"
    )

    @model_validator(mode="after")
    def ordered_ranges(self):
        if self.maximum_sample_interval_s < self.minimum_sample_interval_s:
            raise ValueError("maximum sample interval cannot be below minimum")
        if self.maximum_response_ppm_m < self.minimum_response_ppm_m:
            raise ValueError("maximum response cannot be below minimum")
        return self


class EscapeLeakDatasetAudit(Contract):
    """Complete pinned-file audit without combining experiments into calibration rows."""

    schema_version: Literal["matintegrity.escape1_leak_dataset_audit.v1"] = (
        "matintegrity.escape1_leak_dataset_audit.v1"
    )
    dataset_id: Literal[ESCAPE1_DATASET_ID] = ESCAPE1_DATASET_ID
    provider_record: Literal[ESCAPE1_PROVIDER_RECORD] = ESCAPE1_PROVIDER_RECORD
    license_id: Literal[ESCAPE1_LICENSE_ID] = ESCAPE1_LICENSE_ID
    readme_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    traces: tuple[EscapeLeakTraceRecord, ...]
    total_sample_count: int = Field(gt=0)
    workbook_count: Literal[11]
    provider_reported_experiment_count: Literal[11]
    calibration_use_status: Literal["withheld_reference_state_and_windows_unresolved"] = (
        "withheld_reference_state_and_windows_unresolved"
    )

    @model_validator(mode="after")
    def complete_manifest(self):
        names = {row.provider_experiment_file_id for row in self.traces}
        if names != set(ESCAPE1_WORKBOOKS):
            raise ValueError("ESCAPE-1 audit must cover the complete pinned workbook manifest")
        if self.total_sample_count != sum(row.sample_count for row in self.traces):
            raise ValueError("ESCAPE-1 total sample count does not match trace records")
        return self


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _seconds_from_midnight(value, *, cell: str) -> float:
    if not isinstance(value, time):
        raise ValueError(f"ESCAPE-1 timestamp must be an Excel time at {cell}")
    return value.hour * 3600 + value.minute * 60 + value.second + value.microsecond / 1e6


def read_escape1_leak_trace(
    directory: str | Path,
    filename: str,
    *,
    expected_sha256: str | None = None,
) -> tuple[np.ndarray, np.ndarray, EscapeLeakTraceRecord]:
    """Read one pinned trace; retain provider slpm because its reference state is absent."""
    if filename not in ESCAPE1_WORKBOOKS:
        raise ValueError("filename is not in the reviewed ESCAPE-1 workbook manifest")
    path = Path(directory) / filename
    reviewed_sha256, leak_rate_slpm = ESCAPE1_WORKBOOKS[filename]
    expected = reviewed_sha256 if expected_sha256 is None else expected_sha256
    actual = _sha256(path)
    if actual != expected:
        raise ValueError("ESCAPE-1 workbook SHA-256 differs from the caller-pinned digest")
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - optional dependency environment
        raise ImportError("ESCAPE-1 XLSX reading requires the science extra with openpyxl") from exc
    workbook = load_workbook(path, read_only=True, data_only=False)
    try:
        if len(workbook.worksheets) != 1:
            raise ValueError("ESCAPE-1 workbook must contain exactly one sheet")
        sheet = workbook.worksheets[0]
        if sheet.max_column != 2 or sheet.max_row < 3:
            raise ValueError("ESCAPE-1 worksheet must contain two columns and at least two samples")
        if (sheet.cell(1, 1).value, sheet.cell(1, 2).value) != ("Time", "Methane ppmm"):
            raise ValueError("ESCAPE-1 worksheet header differs from the reviewed provider header")
        seconds: list[float] = []
        response: list[float] = []
        for row_number, (timestamp_cell, response_cell) in enumerate(
            sheet.iter_rows(min_row=2, max_col=2, values_only=True), start=2
        ):
            seconds.append(_seconds_from_midnight(timestamp_cell, cell=f"A{row_number}"))
            if isinstance(response_cell, bool):
                raise ValueError(f"boolean methane response at B{row_number}")
            try:
                value = float(response_cell)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"nonnumeric methane response at B{row_number}") from exc
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"nonfinite or negative methane response at B{row_number}")
            response.append(value)
    finally:
        workbook.close()
    time_s = np.asarray(seconds, dtype=float)
    response_ppm_m = np.asarray(response, dtype=float)
    intervals = np.diff(time_s)
    if np.any(intervals <= 0):
        raise ValueError("ESCAPE-1 timestamps must be strictly increasing within one workbook")
    record = EscapeLeakTraceRecord(
        provider_experiment_file_id=filename,
        source_file_sha256=actual,
        source_sheet_name=sheet.title,
        sample_count=len(time_s),
        provider_declared_leak_rate_value=leak_rate_slpm,
        timestamps_strictly_increasing=True,
        minimum_sample_interval_s=float(np.min(intervals)),
        maximum_sample_interval_s=float(np.max(intervals)),
        minimum_response_ppm_m=float(np.min(response_ppm_m)),
        maximum_response_ppm_m=float(np.max(response_ppm_m)),
    )
    return time_s, response_ppm_m, record


def audit_escape1_leak_dataset(directory: str | Path) -> EscapeLeakDatasetAudit:
    """Audit all eleven pinned workbooks and the provider README."""
    root = Path(directory)
    readme = root / "README.md"
    if _sha256(readme) != ESCAPE1_README_SHA256:
        raise ValueError("ESCAPE-1 README SHA-256 differs from the reviewed provider file")
    traces = tuple(read_escape1_leak_trace(root, filename)[2] for filename in sorted(ESCAPE1_WORKBOOKS))
    return EscapeLeakDatasetAudit(
        readme_sha256=ESCAPE1_README_SHA256,
        traces=traces,
        total_sample_count=sum(row.sample_count for row in traces),
        workbook_count=11,
        provider_reported_experiment_count=11,
    )

"""Read pinned cathodic-protection DPlot exports without applying acceptance criteria."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, StrictInt

from .contracts import Calculation, Contract, canonical_digest
from .registry import ModelSpec

DATASET_ID = "zenodo-18735817-cathodic-protection"
PROVIDER_RECORD = "https://doi.org/10.5281/zenodo.18735817"
LICENSE_ID = "CC-BY-4.0"

SOURCE_FILES = {
    "OCP in Flexural Beam.csv": "4a150608916a712bbe3b98808b9a97419bfb588aa3272cb888bd847143f51191",
    "OCP in Prism.csv": "06832af8baeb39a48213be5a89c998d4c5d5e301af55ec01a20298659f0f05d4",
    "OCP in Shear Beam.csv": "293e04b0228164926946b449b5f9a5c4dc18f7d6bc34d587a56c4843fc9b4009",
    "Potentiodynamic Scan in Flexural Beam.csv": "8fa12176261bef65ea4110b20068e255c2cfc642d212ec3c974ca25513badd7c",
    "Potentiodynamic Scan in Prism.csv": "642c778088657dd62539e4237456801eef712f47aad3cababa43aecdfdcb6d69",
}


class CathodicProtectionCurveRecord(Contract):
    schema_version: Literal["matintegrity.cathodic_protection_curve.v1"] = (
        "matintegrity.cathodic_protection_curve.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    source_filename: str = Field(min_length=1)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_index: int = Field(ge=1)
    provider_curve_label: str = Field(min_length=1)
    measurement_kind: Literal["open_circuit_potential", "potentiodynamic_scan"]
    sample_count: int = Field(gt=1)
    x_quantity: Literal["time", "current"]
    x_unit: Literal["s", "provider_current_axis_unresolved"]
    y_quantity: Literal["potential"] = "potential"
    y_unit: Literal["V_vs_calomel"] = "V_vs_calomel"
    minimum_x: float
    maximum_x: float
    minimum_potential_V: float
    maximum_potential_V: float
    interpretation_status: Literal["raw_curve_no_acceptance_or_corrosion_rate"] = (
        "raw_curve_no_acceptance_or_corrosion_rate"
    )


class CathodicProtectionDatasetAudit(Contract):
    schema_version: Literal["matintegrity.cathodic_protection_dataset_audit.v1"] = (
        "matintegrity.cathodic_protection_dataset_audit.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    curves: tuple[CathodicProtectionCurveRecord, ...] = Field(min_length=8, max_length=8)
    file_count: Literal[5]
    curve_count: Literal[8]
    total_samples: Literal[11922]
    workbook_preserved_but_not_normalized: Literal[True] = True
    calibration_use_status: Literal["withheld_missing_exposure_and_instrument_metadata"] = (
        "withheld_missing_exposure_and_instrument_metadata"
    )


class CathodicProtectionReadAuthorization(Contract):
    """Caller attribution and local/computational authorization for sample rows."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class CathodicProtectionArchiveAuditRequest(Contract):
    """Audit the pinned local exports while keeping the path private."""

    local_data_directory: str = Field(min_length=1)
    authorization: CathodicProtectionReadAuthorization


class CathodicProtectionSample(Contract):
    """One provider curve sample; not a protection decision or corrosion rate."""

    schema_version: Literal["matintegrity.cathodic_protection_sample.v1"] = "matintegrity.cathodic_protection_sample.v1"
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_filename: str = Field(min_length=1)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_index: StrictInt = Field(ge=1)
    provider_curve_label: str = Field(min_length=1)
    curve_sample_index: StrictInt = Field(ge=0)
    measurement_kind: Literal["open_circuit_potential", "potentiodynamic_scan"]
    x_quantity: Literal["time", "current"]
    x_unit: Literal["s", "provider_current_axis_unresolved"]
    x_value_provider_native: float
    potential_V_vs_calomel: float
    reference_electrode_subtype: Literal["unresolved_calomel_subtype"] = "unresolved_calomel_subtype"
    local_only: Literal[True] = True
    interpretation_status: Literal["raw_curve_sample_no_protection_or_corrosion_rate"] = (
        "raw_curve_sample_no_protection_or_corrosion_rate"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_dplot_curves(
    path: str | Path,
    *,
    expected_sha256: str | None = None,
) -> tuple[dict[str, tuple[np.ndarray, np.ndarray]], tuple[CathodicProtectionCurveRecord, ...]]:
    """Parse numeric curves from one reviewed DPlot export and retain its native axes."""
    source = Path(path)
    pinned = expected_sha256 or SOURCE_FILES.get(source.name)
    if pinned is None:
        raise ValueError("caller must pin SHA-256 for an unlisted cathodic-protection file")
    actual = _sha256(source)
    if actual != pinned:
        raise ValueError("cathodic-protection CSV SHA-256 differs from the pinned digest")
    rows = list(csv.reader(source.open(encoding="utf-8-sig", errors="strict")))
    if len(rows) < 10 or rows[0] != ["DPLOT v1.6"] or rows[1] != ["data"]:
        raise ValueError("cathodic-protection CSV is not the reviewed DPlot layout")
    try:
        curve_count = int(rows[2][0])
    except (IndexError, ValueError) as exc:
        raise ValueError("DPlot curve count is invalid") from exc
    kind = "open_circuit_potential" if source.name.startswith("OCP ") else "potentiodynamic_scan"
    x_quantity = "time" if kind == "open_circuit_potential" else "current"
    x_unit = "s" if kind == "open_circuit_potential" else "provider_current_axis_unresolved"
    cursor = 3
    curves: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    records = []
    for curve_index in range(1, curve_count + 1):
        try:
            sample_count = int(rows[cursor][0])
        except (IndexError, ValueError) as exc:
            raise ValueError("DPlot sample count is invalid") from exc
        cursor += 1
        values = []
        for row in rows[cursor : cursor + sample_count]:
            if len(row) != 2:
                raise ValueError("DPlot numeric row must contain exactly two fields")
            try:
                values.append((float(row[0]), float(row[1])))
            except ValueError as exc:
                raise ValueError("DPlot curve contains a nonnumeric sample") from exc
        if len(values) != sample_count:
            raise ValueError("DPlot curve is truncated")
        cursor += sample_count
        if cursor + 1 >= len(rows) or len(rows[cursor]) != 1 or not rows[cursor + 1]:
            raise ValueError("DPlot curve trailer differs from the reviewed layout")
        label = rows[cursor + 1][0].strip()
        if not label:
            raise ValueError("DPlot curve label is empty")
        cursor += 3
        data = np.asarray(values, dtype=float)
        if not np.all(np.isfinite(data)):
            raise ValueError("DPlot curve values must be finite")
        curve_id = f"{source.stem}:{curve_index}:{label}"
        curves[curve_id] = (data[:, 0], data[:, 1])
        records.append(
            CathodicProtectionCurveRecord(
                source_filename=source.name,
                source_file_sha256=actual,
                curve_index=curve_index,
                provider_curve_label=label,
                measurement_kind=kind,
                sample_count=sample_count,
                x_quantity=x_quantity,
                x_unit=x_unit,
                minimum_x=float(np.min(data[:, 0])),
                maximum_x=float(np.max(data[:, 0])),
                minimum_potential_V=float(np.min(data[:, 1])),
                maximum_potential_V=float(np.max(data[:, 1])),
            )
        )
    return curves, tuple(records)


def audit_cathodic_protection_dataset(
    directory: str | Path,
) -> tuple[dict[str, tuple[np.ndarray, np.ndarray]], CathodicProtectionDatasetAudit]:
    """Audit all five pinned exports; do not derive protection or corrosion criteria."""
    root = Path(directory)
    arrays = {}
    records = []
    for filename, digest in SOURCE_FILES.items():
        file_arrays, file_records = read_dplot_curves(root / filename, expected_sha256=digest)
        arrays.update(file_arrays)
        records.extend(file_records)
    audit = CathodicProtectionDatasetAudit(
        curves=tuple(records), file_count=5, curve_count=8, total_samples=sum(r.sample_count for r in records)
    )
    return arrays, audit


def iter_cathodic_protection_samples(
    directory: str | Path,
    *,
    authorization: CathodicProtectionReadAuthorization,
) -> Iterator[CathodicProtectionSample]:
    """Yield typed provider samples in pinned file, curve and sample order.

    Reuses the existing reviewed DPlot parser and copies no provider data into
    the package. Each source file is checked against its exact SHA-256 pin.
    """
    if not authorization.attribution.strip():
        raise ValueError("CC BY attribution must be nonempty")
    authorization_sha256 = canonical_digest(authorization.model_dump(mode="json"))
    root = Path(directory)
    count = 0
    for filename, expected_sha256 in SOURCE_FILES.items():
        arrays, records = read_dplot_curves(root / filename, expected_sha256=expected_sha256)
        for curve_id, (x_values, y_values) in arrays.items():
            prefix, index_token, label = curve_id.split(":", 2)
            if prefix != Path(filename).stem:
                raise ValueError("parsed curve identity differs from the pinned source filename")
            curve_index = int(index_token)
            record = next(
                (r for r in records if r.curve_index == curve_index and r.provider_curve_label == label),
                None,
            )
            if record is None or len(x_values) != record.sample_count or len(y_values) != record.sample_count:
                raise ValueError("parsed curve samples do not match their audited curve record")
            record_sha256 = canonical_digest(record.model_dump(mode="json"))
            for sample_index, (x_value, potential) in enumerate(zip(x_values, y_values, strict=True)):
                yield CathodicProtectionSample(
                    attribution=authorization.attribution,
                    authorization_sha256=authorization_sha256,
                    source_filename=filename,
                    source_file_sha256=record.source_file_sha256,
                    curve_record_sha256=record_sha256,
                    curve_index=record.curve_index,
                    provider_curve_label=record.provider_curve_label,
                    curve_sample_index=sample_index,
                    measurement_kind=record.measurement_kind,
                    x_quantity=record.x_quantity,
                    x_unit=record.x_unit,
                    x_value_provider_native=float(x_value),
                    potential_V_vs_calomel=float(potential),
                )
                count += 1
    if count != 11_922:
        raise ValueError(f"typed cathodic-protection sample count {count} differs from the pinned dataset scope")


def audit_cathodic_protection_exports(request: CathodicProtectionArchiveAuditRequest) -> Calculation:
    """Return metadata for the locally authorized allowlisted exports only."""
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY attribution must be nonempty")
    _, audit = audit_cathodic_protection_dataset(request.local_data_directory)
    return Calculation(values={
        "model_id": "data.zenodo_cathodic_protection_sample_rows",
        "dataset_id": DATASET_ID,
        "provider_record": PROVIDER_RECORD,
        "license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "source_file_sha256": {row.source_filename: row.source_file_sha256 for row in audit.curves},
        "curve_count": audit.curve_count,
        "sample_count": audit.total_samples,
        "raw_rows_returned": False,
        "local_path_returned": False,
        "local_only": True,
        "calibration_use_status": audit.calibration_use_status,
        "interpretation_limit": "raw OCP/polarization samples only; no protection criterion or corrosion rate",
    }, notes=("Metadata only. Use iter_cathodic_protection_samples for caller-authorized local sample access.",))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="data.zenodo_cathodic_protection_sample_rows",
        input_type=CathodicProtectionArchiveAuditRequest,
        evaluator=audit_cathodic_protection_exports,
        units={"curve_count": "1", "sample_count": "row"},
        assumptions=("Only five locally held CSV files with exact SHA-256 pins and the reviewed DPlot layout are accepted.", "The caller must provide attribution and local/computational-use authorization.", "Potential-axis reference details and potentiodynamic current units remain unresolved; no protection criterion, corrosion rate or calibration is inferred."),
        source_ids=("zenodo_18735817_cathodic_protection_typed_rows",),
        qualification="data_import",
    )]

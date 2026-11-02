"""Typed, digest-pinned local row access to the Mendeley thermal-rod archive."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec
from .thermal_data import read_thermal_rod_series

DATASET_ID = "thermal-rod-transient"
DATASET_DOI = "10.17632/sbcf36976g.1"
LICENSE_ID = "CC-BY-4.0"
SOURCE_ID = "mendeley_thermal_rod_typed_rows"
MODEL_ID = "data.mendeley_thermal_rod_typed_rows"
ARCHIVE_FILENAME = "sbcf36976g-1.zip"
ARCHIVE_SHA256 = "9226632888404fe792358bc5a33cf2edacbb16e35352a36a6c0c1c4c155e723a"
ARCHIVE_BYTES = 2_099_328


class ThermalRodReadAuthorization(Contract):
    """Caller attribution and local-only computational-use declaration."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class ThermalRodObservationRow(Contract):
    """One source CSV observation with archive, member, and row lineage."""

    schema_version: Literal["matintegrity.thermal_rod_observation_row.v1"] = (
        "matintegrity.thermal_rod_observation_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_archive_filename: Literal[ARCHIVE_FILENAME] = ARCHIVE_FILENAME
    source_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_archive_bytes: StrictInt = Field(gt=0)
    source_member: str = Field(min_length=1)
    source_member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    run_id: str = Field(min_length=1)
    source_row_order: StrictInt = Field(ge=0)
    provider_source_row: StrictInt = Field(ge=2)
    time_s: float
    tc1_excess_temperature_K: float
    tc2_excess_temperature_K: float
    tc3_excess_temperature_K: float
    tc4_excess_temperature_K: float
    tc5_excess_temperature_K: float
    tc6_excess_temperature_K: float
    controller_setting_counts: float
    temperature_basis: Literal["excess_above_source_declared_ambient; kelvin_difference"] = (
        "excess_above_source_declared_ambient; kelvin_difference"
    )
    controller_setting_basis: Literal["reported_counts_on_1023_maximum_scale_not_power"] = (
        "reported_counts_on_1023_maximum_scale_not_power"
    )
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    heat_flux_inferred: Literal[False] = False
    material_property_inferred: Literal[False] = False
    corrosion_metric_inferred: Literal[False] = False


class ThermalRodArchiveAuditRequest(Contract):
    local_archive_path: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    authorization: ThermalRodReadAuthorization


def _verify_archive(path: Path) -> tuple[str, int]:
    if path.name != ARCHIVE_FILENAME or not path.is_file():
        raise ValueError("only the catalogued local thermal-rod archive is accepted")
    byte_count = path.stat().st_size
    if byte_count != ARCHIVE_BYTES:
        raise ValueError("thermal-rod archive byte count differs from the catalog pin")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    actual = digest.hexdigest()
    if actual != ARCHIVE_SHA256:
        raise ValueError("thermal-rod archive SHA-256 differs from the catalog pin")
    return actual, byte_count


def iter_thermal_rod_observation_rows(
    path: str | Path,
    run_id: str,
    *,
    authorization: ThermalRodReadAuthorization,
) -> Iterator[ThermalRodObservationRow]:
    """Yield one pinned raw run in CSV order, retaining excess temperatures as reported."""
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    archive_path = Path(path)
    archive_sha256, archive_bytes = _verify_archive(archive_path)
    frame = read_thermal_rod_series(archive_path, run_id)
    if frame.attrs.get("source_archive_sha256") != archive_sha256:
        raise ValueError("existing thermal reader and archive pin disagree")
    authorization_sha256 = canonical_digest(authorization.model_dump(mode="json"))
    source_member = str(frame.attrs["source_member"])
    source_member_sha256 = str(frame.attrs["source_member_sha256"])
    for order, row in enumerate(frame.itertuples(index=False), start=0):
        values = {
            "time_s": float(row.time_s),
            **{
                f"tc{index}_excess_temperature_K": float(getattr(row, f"tc{index}_excess_temperature_K"))
                for index in range(1, 7)
            },
            "controller_setting_counts": float(row.controller_setting_counts),
        }
        lineage = {
            "dataset_id": DATASET_ID,
            "source_archive_sha256": archive_sha256,
            "source_archive_filename": ARCHIVE_FILENAME,
            "source_member": source_member,
            "source_member_sha256": source_member_sha256,
            "run_id": run_id,
            "source_row_order": order,
            "provider_source_row": order + 2,
            "values": values,
            "units": {
                "time_s": "s",
                **{f"tc{index}_excess_temperature_K": "K_difference" for index in range(1, 7)},
                "controller_setting_counts": "count_on_1023_max_scale",
            },
        }
        yield ThermalRodObservationRow(
            attribution=authorization.attribution,
            authorization_sha256=authorization_sha256,
            source_archive_sha256=archive_sha256,
            source_archive_bytes=archive_bytes,
            source_member=source_member,
            source_member_sha256=source_member_sha256,
            run_id=run_id,
            source_row_order=order,
            provider_source_row=order + 2,
            **values,
            source_row_sha256=canonical_digest(lineage),
            evidence=Evidence(
                source_id=DATASET_ID,
                origin="open_dataset",
                citation=f"{authorization.attribution}; https://doi.org/{DATASET_DOI}",
                license_id=LICENSE_ID,
                sha256=archive_sha256,
            ),
        )


def audit_thermal_rod_run(request: ThermalRodArchiveAuditRequest) -> Calculation:
    """Audit a run's pinned archive/member metadata without returning point values."""
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    archive_path = Path(request.local_archive_path)
    archive_sha256, archive_bytes = _verify_archive(archive_path)
    frame = read_thermal_rod_series(archive_path, request.run_id)
    if frame.attrs.get("source_archive_sha256") != archive_sha256:
        raise ValueError("existing thermal reader and archive pin disagree")
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "source_archive_filename": ARCHIVE_FILENAME,
        "source_archive_sha256": archive_sha256,
        "source_archive_bytes": archive_bytes,
        "source_member": frame.attrs["source_member"],
        "source_member_sha256": frame.attrs["source_member_sha256"],
        "run_id": request.run_id,
        "source_row_count": int(len(frame)),
        "source_order_preserved": True,
        "point_values_returned": False,
        "local_path_returned": False,
        "local_only": True,
        "controller_setting_converted_to_power": False,
        "thermal_properties_inferred": False,
    }, notes=(
        "Metadata-only run audit; use iter_thermal_rod_observation_rows for authorized local row access.",
        "The one-dimensional thermal-rod experiment is not a corrosion or structural-integrity qualification dataset.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=ThermalRodArchiveAuditRequest,
        evaluator=audit_thermal_rod_run,
        units={"source_archive_bytes": "byte", "source_row_count": "row"},
        assumptions=(
            "Only the catalogued archive name, byte count and SHA-256 are accepted; rows come from the existing raw-run parser.",
            "Caller provides attribution and computational/local-only authorization; output records both license and authorization digest.",
            "Thermocouple values remain source-reported ambient-excess temperatures; controller counts are not converted to watts or heat flux.",
            "No corrosion metric, material property, structural response or qualification is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="data_import",
    )]

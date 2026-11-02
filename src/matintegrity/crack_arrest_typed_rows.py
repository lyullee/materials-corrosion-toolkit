"""Typed, digest-pinned local row access for Mendeley C1/C2 crack-arrest traces."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .fracture_data import read_crack_arrest_series
from .registry import ModelSpec

DATASET_ID = "crack-arrest-c1-c2"
DATASET_DOI = "10.17632/g69875w65c.1"
LICENSE_ID = "CC-BY-4.0"
SOURCE_ID = "mendeley_crack_arrest_typed_rows"
MODEL_ID = "data.mendeley_crack_arrest_typed_rows"
ARCHIVE_FILENAME = "g69875w65c-1.zip"
ARCHIVE_SHA256 = "233f70de5d51148b93eab68654297d4ac4aa782864a5c7e43a3520be8ca54bde"
ARCHIVE_BYTES = 943_565


class CrackArrestReadAuthorization(Contract):
    """Caller attribution and local-only computational-use declaration."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class CrackArrestObservationRow(Contract):
    """One signed force-displacement sample with file, member, and row lineage."""

    schema_version: Literal["matintegrity.crack_arrest_observation_row.v1"] = (
        "matintegrity.crack_arrest_observation_row.v1"
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
    specimen_id: str = Field(min_length=1)
    test_family: Literal["C1", "C2"]
    reported_temperature_C_from_filename: float
    reported_temperature_K_from_filename: float
    temperature_provenance: Literal["filename_token_only; specimen_log_not_checked"] = (
        "filename_token_only; specimen_log_not_checked"
    )
    source_row_order: StrictInt = Field(ge=0)
    provider_source_row: StrictInt = Field(ge=2)
    time_s: float
    machine_displacement_m: float
    force_N: float
    extensometer_displacement_m: float
    reported_cycle_index: StrictInt = Field(ge=0)
    time_unit: Literal["s"] = "s"
    displacement_unit: Literal["m"] = "m"
    force_unit: Literal["N"] = "N"
    sign_and_zero_handling: Literal["source_sign_and_zero_preserved"] = "source_sign_and_zero_preserved"
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    toughness_inferred: Literal[False] = False
    acceptance_inferred: Literal[False] = False
    failure_probability_inferred: Literal[False] = False


class CrackArrestArchiveAuditRequest(Contract):
    local_archive_path: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    authorization: CrackArrestReadAuthorization


def _verify_archive(path: Path) -> tuple[str, int]:
    if path.name != ARCHIVE_FILENAME or not path.is_file():
        raise ValueError("only the catalogued local crack-arrest archive is accepted")
    byte_count = path.stat().st_size
    if byte_count != ARCHIVE_BYTES:
        raise ValueError("crack-arrest archive byte count differs from the catalog pin")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    actual = digest.hexdigest()
    if actual != ARCHIVE_SHA256:
        raise ValueError("crack-arrest archive SHA-256 differs from the catalog pin")
    return actual, byte_count


def iter_crack_arrest_observation_rows(
    path: str | Path,
    specimen_id: str,
    *,
    authorization: CrackArrestReadAuthorization,
) -> Iterator[CrackArrestObservationRow]:
    """Yield one source specimen CSV in original point order; do not reinterpret its curve."""
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    archive_path = Path(path)
    archive_sha256, archive_bytes = _verify_archive(archive_path)
    frame = read_crack_arrest_series(archive_path, specimen_id)
    if frame.attrs.get("source_archive_sha256") != archive_sha256:
        raise ValueError("existing crack-arrest reader and archive pin disagree")
    auth_sha256 = canonical_digest(authorization.model_dump(mode="json"))
    source_member = str(frame.attrs["source_member"])
    source_member_sha256 = str(frame.attrs["source_member_sha256"])
    for order, row in enumerate(frame.itertuples(index=False), start=0):
        values = {
            "time_s": float(row.time_s),
            "machine_displacement_m": float(row.machine_displacement_m),
            "force_N": float(row.force_N),
            "extensometer_displacement_m": float(row.extensometer_displacement_m),
            "reported_cycle_index": int(row.reported_cycle_index),
        }
        lineage = {
            "dataset_id": DATASET_ID,
            "source_archive_sha256": archive_sha256,
            "source_member": source_member,
            "source_member_sha256": source_member_sha256,
            "specimen_id": frame.attrs["specimen_id"],
            "test_family": frame.attrs["test_family"],
            "reported_temperature_K_from_filename": float(frame.attrs["reported_temperature_K"]),
            "source_row_order": order,
            "provider_source_row": order + 2,
            "values": values,
        }
        yield CrackArrestObservationRow(
            attribution=authorization.attribution,
            authorization_sha256=auth_sha256,
            source_archive_sha256=archive_sha256,
            source_archive_bytes=archive_bytes,
            source_member=source_member,
            source_member_sha256=source_member_sha256,
            specimen_id=str(frame.attrs["specimen_id"]),
            test_family=str(frame.attrs["test_family"]),
            reported_temperature_C_from_filename=float(frame.attrs["reported_temperature_K"]) - 273.15,
            reported_temperature_K_from_filename=float(frame.attrs["reported_temperature_K"]),
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


def audit_crack_arrest_specimen(request: CrackArrestArchiveAuditRequest) -> Calculation:
    """Return pinned file/member/row-count metadata without exposing point values or paths."""
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    archive_path = Path(request.local_archive_path)
    archive_sha256, archive_bytes = _verify_archive(archive_path)
    frame = read_crack_arrest_series(archive_path, request.specimen_id)
    if frame.attrs.get("source_archive_sha256") != archive_sha256:
        raise ValueError("existing crack-arrest reader and archive pin disagree")
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
        "specimen_id": frame.attrs["specimen_id"],
        "test_family": frame.attrs["test_family"],
        "reported_temperature_K_from_filename": float(frame.attrs["reported_temperature_K"]),
        "temperature_provenance": frame.attrs["temperature_origin"],
        "source_row_count": int(len(frame)),
        "source_order_preserved": True,
        "point_values_returned": False,
        "local_path_returned": False,
        "local_only": True,
        "toughness_inferred": False,
        "acceptance_inferred": False,
    }, notes=(
        "Metadata-only specimen audit; use iter_crack_arrest_observation_rows for authorized local row access.",
        "The force-displacement trace is not converted to crack-arrest toughness, initiation toughness, an FAD curve, acceptance or failure probability.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CrackArrestArchiveAuditRequest,
        evaluator=audit_crack_arrest_specimen,
        units={"source_archive_bytes": "byte", "source_row_count": "row", "reported_temperature_K_from_filename": "K"},
        assumptions=(
            "Only the exact catalogued archive filename, byte count and SHA-256 are accepted before reusing the existing bounded CSV reader.",
            "Caller supplies CC BY 4.0 attribution and computational/local-only authorization; row Evidence retains archive digest and license.",
            "CSV row order, source signs and zero are preserved. Temperature comes from a filename token and is not specimen-log verified.",
            "No crack-arrest or initiation toughness, FAD assessment, acceptance, corrosion interaction or failure probability is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="data_import",
    )]

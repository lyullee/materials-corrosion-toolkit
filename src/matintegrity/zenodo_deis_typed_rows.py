"""Typed, provenance-preserving local rows for the pinned WE43/AZ31 DEIS matrices."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec
from .zenodo_deis_import import (
    ARCHIVE_BYTES,
    ARCHIVE_SHA256,
    DATASET_DOI,
    DATASET_ID,
    DeisMatrixMember,
    ZenodoDeisArchiveManifest,
    inspect_zenodo_deis_archive,
    iter_zenodo_deis_rows,
)

LICENSE_ID = "CC0-1.0"
SOURCE_ID = "zenodo_mg_deis_typed_rows"
MODEL_ID = "data.zenodo_mg_deis_typed_matrix_rows"
ARCHIVE_FILENAME = "Dataset_CorSci.zip"
ARCHIVE_MD5 = "a0c19043e6ed883e005f35cee2800f66"
MEMBER_MATERIAL = {
    "DEIS/AZ31/AZ31-zw.txt": "AZ31",
    "DEIS/WE43/WE43-zw.txt": "WE43",
}
MEMBER_PATH = Literal["DEIS/AZ31/AZ31-zw.txt", "DEIS/WE43/WE43-zw.txt"]


class ZenodoDeisReadAuthorization(Contract):
    """Caller attribution and local-only computational-use declaration."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class ZenodoDeisMatrixRow(Contract):
    """One original numeric matrix row without assigning columns to physical quantities."""

    schema_version: Literal["matintegrity.zenodo_deis_matrix_row.v1"] = (
        "matintegrity.zenodo_deis_matrix_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_archive_filename: Literal[ARCHIVE_FILENAME] = ARCHIVE_FILENAME
    source_archive_bytes: StrictInt = Field(gt=0)
    source_archive_md5: str = Field(pattern=r"^[a-f0-9]{32}$")
    source_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_member_path: MEMBER_PATH
    source_member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    declared_alloy_label: Literal["AZ31", "WE43"]
    source_row_order: StrictInt = Field(ge=0)
    provider_row_number: StrictInt = Field(ge=1)
    source_column_count: StrictInt = Field(gt=0, le=10_000)
    matrix_values_as_provided: tuple[float, ...] = Field(min_length=1, max_length=10_000)
    delimiter: Literal["tab"] = "tab"
    row_axis_mapping: Literal["unresolved"] = "unresolved"
    column_axis_mapping: Literal["unresolved"] = "unresolved"
    units_mapping: Literal["unresolved"] = "unresolved"
    time_series_identity_inferred: Literal[False] = False
    frequency_axis_inferred: Literal[False] = False
    corrosion_quantity_inferred: Literal[False] = False
    material_performance_inferred: Literal[False] = False
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence


class ZenodoDeisMatrixAuditRequest(Contract):
    local_archive_path: str = Field(min_length=1)
    source_member_path: MEMBER_PATH
    authorization: ZenodoDeisReadAuthorization


def _pinned_manifest(path: Path) -> ZenodoDeisArchiveManifest:
    if path.name != ARCHIVE_FILENAME or not path.is_file():
        raise ValueError("only the catalogued local Zenodo DEIS archive is accepted")
    if path.stat().st_size != ARCHIVE_BYTES:
        raise ValueError("Zenodo DEIS archive byte count differs from the catalog pin")
    md5 = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(block)
    if md5.hexdigest() != ARCHIVE_MD5:
        raise ValueError("Zenodo DEIS archive MD5 differs from the catalog publisher checksum")
    manifest = inspect_zenodo_deis_archive(path)
    if manifest.archive_sha256 != ARCHIVE_SHA256:
        raise ValueError("Zenodo DEIS archive digest differs from the pinned revision")
    return manifest


def iter_zenodo_deis_typed_rows(
    path: str | Path,
    manifest: ZenodoDeisArchiveManifest,
    source_member_path: MEMBER_PATH,
    *,
    authorization: ZenodoDeisReadAuthorization,
) -> Iterator[ZenodoDeisMatrixRow]:
    """Yield source matrix rows in file order with local-only evidence and digest lineage."""
    if not authorization.attribution.strip():
        raise ValueError("dataset attribution must be nonempty")
    if manifest.archive_sha256 != ARCHIVE_SHA256:
        raise ValueError("manifest does not reference the pinned archive revision")
    source = Path(path)
    if source.name != ARCHIVE_FILENAME or source.stat().st_size != ARCHIVE_BYTES:
        raise ValueError("local archive identity does not match the catalogued asset")
    md5 = hashlib.md5()
    with source.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(block)
    if md5.hexdigest() != ARCHIVE_MD5:
        raise ValueError("local archive MD5 differs from the catalog publisher checksum")
    member = next((row for row in manifest.matrices if row.member_path == source_member_path), None)
    if member is None:
        raise ValueError("requested matrix member is absent from the inspected manifest")
    authorization_sha256 = canonical_digest(authorization.model_dump(mode="json"))
    for row_order, matrix_values in enumerate(iter_zenodo_deis_rows(source, manifest, source_member_path)):
        values = tuple(float(value) for value in matrix_values)
        lineage = {
            "dataset_id": DATASET_ID,
            "archive_sha256": manifest.archive_sha256,
            "archive_md5": ARCHIVE_MD5,
            "member_path": source_member_path,
            "member_sha256": member.member_sha256,
            "source_row_order": row_order,
            "provider_row_number": row_order + 1,
            "matrix_values_as_provided": values,
            "column_count": member.column_count,
            "axis_and_units_status": "unresolved",
        }
        yield ZenodoDeisMatrixRow(
            attribution=authorization.attribution,
            authorization_sha256=authorization_sha256,
            source_archive_bytes=source.stat().st_size,
            source_archive_md5=ARCHIVE_MD5,
            source_archive_sha256=manifest.archive_sha256,
            source_member_path=source_member_path,
            source_member_sha256=member.member_sha256,
            declared_alloy_label=MEMBER_MATERIAL[source_member_path],
            source_row_order=row_order,
            provider_row_number=row_order + 1,
            source_column_count=member.column_count,
            matrix_values_as_provided=values,
            source_row_sha256=canonical_digest(lineage),
            evidence=Evidence(
                source_id=DATASET_ID,
                origin="open_dataset",
                citation=f"{authorization.attribution}; https://doi.org/{DATASET_DOI}",
                license_id=LICENSE_ID,
                sha256=manifest.archive_sha256,
            ),
        )


def audit_zenodo_deis_matrix(request: ZenodoDeisMatrixAuditRequest) -> Calculation:
    """Return pinned file/member dimensions and lineage without numeric matrix values."""
    if not request.authorization.attribution.strip():
        raise ValueError("dataset attribution must be nonempty")
    source = Path(request.local_archive_path)
    manifest = _pinned_manifest(source)
    member = next((row for row in manifest.matrices if row.member_path == request.source_member_path), None)
    if member is None:
        raise ValueError("requested matrix member is absent from the inspected manifest")
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "source_archive_filename": ARCHIVE_FILENAME,
        "source_archive_bytes": source.stat().st_size,
        "source_archive_md5": ARCHIVE_MD5,
        "source_archive_sha256": manifest.archive_sha256,
        "source_member_path": member.member_path,
        "source_member_sha256": member.member_sha256,
        "declared_alloy_label": member.declared_material_label,
        "source_row_count": member.row_count,
        "source_column_count": member.column_count,
        "blank_cell_count": member.blank_cell_count,
        "nonfinite_cell_count": member.nonfinite_cell_count,
        "axis_mapping": "unresolved",
        "units_mapping": "unresolved",
        "numeric_values_returned": False,
        "local_only": True,
        "frequency_axis_inferred": False,
        "time_series_inferred": False,
        "corrosion_quantity_inferred": False,
    }, notes=(
        "Metadata-only audit; use iter_zenodo_deis_typed_rows with the inspected manifest for local row access.",
        "The importer does not assign matrix rows to time, columns to frequency, real/imaginary pairing, or physical units.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=ZenodoDeisMatrixAuditRequest,
        evaluator=audit_zenodo_deis_matrix,
        units={"source_archive_bytes": "byte", "source_row_count": "row", "source_column_count": "column"},
        assumptions=(
            "Only the catalogued CC0 archive filename, byte count, publisher MD5 and SHA-256 are accepted; the existing bounded matrix parser is reused.",
            "Caller supplies dataset attribution and computational/local-only authorization; each row retains file/member digest and Evidence lineage.",
            "Matrix row and column positions remain as provided; units, time axis, frequency axis and spectrum interpretation are unresolved.",
            "No corrosion rate, material ranking, acceptance, performance or qualification is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="data_import",
    )]

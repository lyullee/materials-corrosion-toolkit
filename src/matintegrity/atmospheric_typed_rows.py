"""Authorization- and digest-aware rows from the pinned atmospheric corrosion reader."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt

from .atmospheric_data import (
    AtmosphericCorrosionObservation,
    DATASET_ID,
    PINNED_ARCHIVE_SHA256,
    read_atmospheric_corrosion_observations,
)
from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

DATASET_DOI = "10.17632/ysr7wy3y7z.1"
LICENSE_ID = "CC-BY-4.0"
LICENSE_SCOPE = "compilation_license_only_underlying_observation_rights_unresolved"
SOURCE_ID = "mendeley_atmospheric_corrosion_typed_rows"
MODEL_ID = "data.mendeley_atmospheric_corrosion_typed_rows"
ARCHIVE_FILENAME = "ysr7wy3y7z-1.zip"
ARCHIVE_BYTES = 290_946
ARCHIVE_MD5 = "a28c35bea466ca2e1b280d875fdbb168"


class AtmosphericReadAuthorization(Contract):
    """Caller declaration for attribution, computational use, and local-only access."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    license_scope: Literal[LICENSE_SCOPE] = LICENSE_SCOPE
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    underlying_observation_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class AtmosphericCorrosionObservationRow(Contract):
    """Parser record with exact provider row, source pin, caller authorization, and Evidence."""

    schema_version: Literal["matintegrity.atmospheric_corrosion_typed_row.v1"] = (
        "matintegrity.atmospheric_corrosion_typed_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    license_scope: Literal[LICENSE_SCOPE] = LICENSE_SCOPE
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_archive_filename: Literal[ARCHIVE_FILENAME] = ARCHIVE_FILENAME
    source_archive_bytes: StrictInt = Field(gt=0)
    source_archive_md5: Literal[ARCHIVE_MD5] = ARCHIVE_MD5
    source_archive_sha256: Literal[PINNED_ARCHIVE_SHA256] = PINNED_ARCHIVE_SHA256
    source_order: StrictInt = Field(ge=0)
    provider_partition: Literal["programme", "independent"]
    provider_source_row: StrictInt = Field(ge=2)
    observation_id: str = Field(min_length=1)
    parsed_record: AtmosphericCorrosionObservation
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    underlying_observation_rights_status: Literal["unresolved"] = "unresolved"
    evidence: Evidence
    localized_corrosion_inferred: Literal[False] = False
    long_term_rate_inferred: Literal[False] = False
    remaining_life_inferred: Literal[False] = False
    failure_probability_inferred: Literal[False] = False


class AtmosphericArchiveAuditRequest(Contract):
    local_archive_path: str = Field(min_length=1)
    partition: Literal["programme", "independent", "both"] = "both"
    authorization: AtmosphericReadAuthorization


def _validate_local_archive(path: Path) -> int:
    if path.name != ARCHIVE_FILENAME or not path.is_file():
        raise ValueError("only the catalogued atmospheric archive filename is accepted")
    size = path.stat().st_size
    if size != ARCHIVE_BYTES:
        raise ValueError("atmospheric archive byte count differs from the reviewed catalog pin")
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != ARCHIVE_MD5:
        raise ValueError("atmospheric archive MD5 differs from the catalogued asset")
    return size


def iter_atmospheric_corrosion_typed_rows(
    path: str | Path,
    *,
    authorization: AtmosphericReadAuthorization,
    partition: Literal["programme", "independent", "both"] = "both",
) -> Iterator[AtmosphericCorrosionObservationRow]:
    """Yield existing parser rows in parser order; preserve source meanings without qualifying them."""
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 compilation attribution must be nonempty")
    archive_path = Path(path)
    archive_bytes = _validate_local_archive(archive_path)
    records = read_atmospheric_corrosion_observations(
        archive_path, partition=partition, require_pinned_hash=True
    )
    authorization_sha256 = canonical_digest(authorization.model_dump(mode="json"))
    for source_order, record in enumerate(records):
        if record.source_archive_sha256 != PINNED_ARCHIVE_SHA256:
            raise ValueError("existing atmospheric parser and archive pin disagree")
        payload = record.model_dump(mode="json")
        yield AtmosphericCorrosionObservationRow(
            attribution=authorization.attribution,
            authorization_sha256=authorization_sha256,
            source_archive_bytes=archive_bytes,
            source_order=source_order,
            provider_partition=record.provider_partition,
            provider_source_row=record.provider_source_row,
            observation_id=record.observation_id,
            parsed_record=record,
            source_row_sha256=canonical_digest({
                "dataset_id": DATASET_ID,
                "archive_sha256": record.source_archive_sha256,
                "source_order": source_order,
                "partition": record.provider_partition,
                "source_row": record.provider_source_row,
                "parsed_record": payload,
                "authorization_sha256": authorization_sha256,
                "underlying_observation_rights_status": "unresolved",
            }),
            evidence=Evidence(
                source_id=DATASET_ID,
                origin="open_dataset",
                citation=f"{authorization.attribution}; https://doi.org/{DATASET_DOI} (CC BY 4.0 compilation only)",
                license_id=LICENSE_ID,
                sha256=record.source_archive_sha256,
            ),
        )


def audit_atmospheric_corrosion_archive(
    request: AtmosphericArchiveAuditRequest,
) -> Calculation:
    """Return fixed source and partition metadata only; never emit observation values or paths."""
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY 4.0 compilation attribution must be nonempty")
    path = Path(request.local_archive_path)
    archive_bytes = _validate_local_archive(path)
    rows = read_atmospheric_corrosion_observations(
        path, partition=request.partition, require_pinned_hash=True
    )
    if any(row.source_archive_sha256 != PINNED_ARCHIVE_SHA256 for row in rows):
        raise ValueError("existing atmospheric parser and archive pin disagree")
    partitions = {name: sum(row.provider_partition == name for row in rows)
                  for name in ("programme", "independent")}
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "license_id": LICENSE_ID,
        "license_scope": LICENSE_SCOPE,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "source_archive_filename": ARCHIVE_FILENAME,
        "source_archive_bytes": archive_bytes,
        "source_archive_md5": ARCHIVE_MD5,
        "source_archive_sha256": PINNED_ARCHIVE_SHA256,
        "partition": request.partition,
        "programme_row_count": partitions["programme"],
        "independent_row_count": partitions["independent"],
        "source_order_preserved": True,
        "underlying_observation_rights_status": "unresolved",
        "point_values_returned": False,
        "local_path_returned": False,
        "local_only": True,
    }, notes=(
        "The provider CC BY declaration applies to the compilation; rights to individual underlying observations remain unresolved.",
        "Metadata-only audit; use iter_atmospheric_corrosion_typed_rows for explicitly authorized local row access.",
        "First-year atmospheric loss and climate covariates do not establish localized penetration, long-term loss, remaining life, acceptance, or failure probability.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=AtmosphericArchiveAuditRequest,
        evaluator=audit_atmospheric_corrosion_archive,
        units={
            "source_archive_bytes": "byte",
            "programme_row_count": "row",
            "independent_row_count": "row",
        },
        assumptions=(
            "Only the catalogued archive name, byte count, Mendeley archive SHA-256 and MD5 are accepted.",
            "Rows come only from the existing parser; caller provides attribution and explicit computational, observation-use, and local-only authorization.",
            "The dataset compilation license does not resolve underlying observation rights; per-row status remains unresolved and outputs remain local-only.",
            "The parser's reported and converted quantities retain its existing unit semantics; no localized rate, multi-year growth, remaining life, acceptance or probability is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="data_import",
    )]

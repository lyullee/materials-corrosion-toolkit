"""Local-only, provenance-first access to the Zenodo Ti-12Mo-5Hf dataset.

This module audits the published ZIP container and exposes its safe member
inventory. It deliberately does not extract provider files or interpret
instrument columns; schema-specific parsing needs a separately reviewed API.
"""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import Field

from .contracts import Calculation, Contract
from .registry import ModelSpec

DATASET_ID = "zenodo-ti12mo5hf-oxygen-corrosion"
PROVIDER_RECORD = "https://doi.org/10.5281/zenodo.19462164"
LICENSE_ID = "CC0-1.0"
ARCHIVE_NAME = "Data_Zenodo_EA2026.zip"
ARCHIVE_BYTES = 47_558_332
ARCHIVE_MD5 = "36611789e98e7608a99841541447a918"
README_NAME = "README_EA2026.txt"
README_BYTES = 4_175
README_MD5 = "17d39381ff21630d4cdbf1f6e9b101cf"
README_SHA256 = "71c6d8984747a6342751733d60a8b2f39cc273d5b9a8605f2f1de5e9d352017c"
DEFAULT_LOCAL_DIRECTORY = Path("data/raw") / DATASET_ID
MAX_MEMBERS = 20_000
MAX_UNCOMPRESSED_BYTES = 2_000_000_000


class Ti12Mo5HfProviderCondition(Contract):
    """A compact transcription of facts explicitly declared by the depositor."""

    schema_version: Literal["matintegrity.zenodo_ti12mo5hf_condition.v1"] = (
        "matintegrity.zenodo_ti12mo5hf_condition.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    metadata_sha256: Literal[README_SHA256] = README_SHA256
    alloy_label: Literal["Ti12Mo5Hf", "Ti12Mo5Hf0.3O"]
    environment_label: Literal["PBS+33mM H2O2"] = "PBS+33mM H2O2"
    declared_program: tuple[str, ...] = (
        "open_circuit_potential_1200_s",
        "potentiostatic_minus_1_V_vs_Ag_AgCl_1200_s",
        "open_circuit_potential_monitoring",
    )
    immersion_observation_times_h: tuple[float, ...] = (2.0, 24.0, 168.0)
    provenance_kind: Literal["provider_metadata_transcription"] = (
        "provider_metadata_transcription"
    )
    interpretation_status: Literal["declared_conditions_only_no_column_mapping"] = (
        "declared_conditions_only_no_column_mapping"
    )


class ArchiveMember(Contract):
    path: str = Field(min_length=1)
    uncompressed_bytes: int = Field(ge=0)
    compressed_bytes: int = Field(ge=0)
    crc32_hex: str = Field(pattern=r"^[0-9a-f]{8}$")
    suffix: str = Field(min_length=1)


class Ti12Mo5HfArchiveAudit(Contract):
    schema_version: Literal["matintegrity.zenodo_ti12mo5hf_archive_audit.v1"] = (
        "matintegrity.zenodo_ti12mo5hf_archive_audit.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    archive_filename: Literal[ARCHIVE_NAME] = ARCHIVE_NAME
    archive_bytes: Literal[ARCHIVE_BYTES] = ARCHIVE_BYTES
    archive_md5: Literal[ARCHIVE_MD5] = ARCHIVE_MD5
    archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    member_count: int = Field(ge=0, le=MAX_MEMBERS)
    uncompressed_total_bytes: int = Field(ge=0, le=MAX_UNCOMPRESSED_BYTES)
    members: tuple[ArchiveMember, ...]
    extracted: Literal[False] = False
    point_data_interpreted: Literal[False] = False


class Ti12Mo5HfArchiveAuditRequest(Contract):
    """Explicit authorization and digest pin for a local archive audit."""

    schema_version: Literal["matintegrity.zenodo_ti12mo5hf_archive_audit_request.v1"] = (
        "matintegrity.zenodo_ti12mo5hf_archive_audit_request.v1"
    )
    local_path: str = Field(min_length=1)
    expected_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


def _digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _checked_member_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Unsafe ZIP member path: {name!r}")
    return normalized


def audit_local_archive(path: str | Path = DEFAULT_LOCAL_DIRECTORY / ARCHIVE_NAME) -> Ti12Mo5HfArchiveAudit:
    """Validate the pinned source ZIP and return a bounded, non-extracting inventory.

    The caller must obtain the asset independently and place it under ignored
    ``data/raw``. No network access, extraction, conversion, or scientific
    calculation occurs here.
    """
    archive = Path(path)
    if archive.name != ARCHIVE_NAME:
        raise ValueError(f"Expected local asset named {ARCHIVE_NAME!r}")
    if archive.stat().st_size != ARCHIVE_BYTES:
        raise ValueError("Archive byte length does not match the publisher-pinned value")
    if _digest(archive, "md5") != ARCHIVE_MD5:
        raise ValueError("Archive MD5 does not match the publisher-pinned value")
    sha256 = _digest(archive, "sha256")

    members: list[ArchiveMember] = []
    total = 0
    with zipfile.ZipFile(archive) as bundle:
        infos = bundle.infolist()
        if len(infos) > MAX_MEMBERS:
            raise ValueError("ZIP member count exceeds the configured bound")
        for info in infos:
            safe_name = _checked_member_name(info.filename)
            total += info.file_size
            if total > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("ZIP expanded size exceeds the configured bound")
            suffix = Path(safe_name).suffix.lower() or "[none]"
            members.append(ArchiveMember(
                path=safe_name,
                uncompressed_bytes=info.file_size,
                compressed_bytes=info.compress_size,
                crc32_hex=f"{info.CRC:08x}",
                suffix=suffix,
            ))
    return Ti12Mo5HfArchiveAudit(
        archive_sha256=sha256,
        member_count=len(members),
        uncompressed_total_bytes=total,
        members=tuple(members),
    )


def declared_conditions() -> tuple[Ti12Mo5HfProviderCondition, ...]:
    """Return depositor-described test context, not a reconstructed time series."""
    return tuple(
        Ti12Mo5HfProviderCondition(alloy_label=alloy)
        for alloy in ("Ti12Mo5Hf", "Ti12Mo5Hf0.3O")
    )


def evaluate_archive_audit_request(request: Ti12Mo5HfArchiveAuditRequest) -> Calculation:
    """Run a read-only audit after explicit local/computational-use authorization."""
    if not request.computational_use_authorized or not request.local_only_authorized:
        raise PermissionError("Explicit computational-use and local-only authorization is required")
    audit = audit_local_archive(request.local_path)
    if audit.archive_sha256 != request.expected_archive_sha256:
        raise ValueError("Archive SHA-256 does not match the caller-pinned digest")
    return Calculation(
        values={"archive_audit": audit.model_dump(mode="json")},
        notes=(
            "Read-only local ZIP metadata audit; no network, extraction, raw measurement values, or physical inference.",
            "The source archive was checked against publisher byte-count/MD5 pins and caller SHA-256 pin.",
        ),
    )


def specifications() -> list[ModelSpec]:
    """Expose an opt-in ModelSpec without modifying any central registry."""
    return [
        ModelSpec(
            model_id="data.zenodo_ti12mo5hf_archive_audit",
            input_type=Ti12Mo5HfArchiveAuditRequest,
            evaluator=evaluate_archive_audit_request,
            units={
                "archive_audit.archive_bytes": "byte",
                "archive_audit.member_count": "1",
                "archive_audit.uncompressed_total_bytes": "byte",
                "archive_audit.archive_sha256": "1",
            },
            assumptions=(
                "Caller supplies a local file and explicitly authorizes computational use and local-only processing.",
                "Only the publisher-pinned archive is accepted; publisher byte count, MD5 and caller SHA-256 must match.",
                "The evaluator returns archive metadata only; it performs no network access, extraction, or source-data interpretation.",
            ),
            source_ids=(DATASET_ID,),
            qualification="data_import",
        )
    ]

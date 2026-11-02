"""Read checksum-pinned SECCM chronoamperometry without reproducing provider processing."""

from __future__ import annotations

import csv
import hashlib
import io
import math
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract

SECCM_DATASET_ID = "seccm-ebsd-316l-pitting-v1"
SECCM_ARCHIVE_SHA256 = "84134e37cfc3864d1206bc86d12a90dc42458ea4463610dc7de687a7674bc95e"
SECCM_PROVIDER_MD5 = "5650c5b968f60445e5708c1668c09da0"
SECCM_PROVIDER_RECORD = "https://doi.org/10.5281/zenodo.18668632"
SECCM_CODE_COMMIT = "5ae5802d189cb100d0071b8efc557805060fcdf6"
SECCM_CODE_SHA256 = "9ee751ef2e7cee2daa36f73968ef1b889d33d30e3bbf3feb222aab1081886d24"

MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_MEMBER_BYTES = 20 * 1024 * 1024
MAX_TOTAL_DECODED_BYTES = 64 * 1024 * 1024
MAX_CA_ROWS = 20_000
EXPECTED_MEMBERS = {
    "selected_oval_pixels.csv": "footprint_pixels",
    "SEM_EBSD.csv": "sem_intensity_table",
    "SS_NaCl_CA_M_1031_C.csv": "raw_chronoamperometry",
    "SS_NaCl_Parameters_M_1031_C.csv": "acquisition_parameters",
    "CA_SECCM_descriptors_area.csv": "provider_descriptors",
    "CA_SECCM_descriptors_area_normalised.csv": "provider_derived_descriptors",
    "ebsd_filtered.csv": "provider_processed_ebsd",
    "labels.csv": "provider_labels",
    "oxygen_flux.txt": "provider_model_table",
    "README_dataset.md": "provider_readme",
}
_SIGNAL_LABEL = re.compile(r"^I_Substrate_A_LN_\d+$")


class SeccmArchiveMemberRecord(Contract):
    """Identity and declared role of one member in the pinned provider ZIP."""

    schema_version: Literal["matintegrity.seccm_archive_member.v1"] = "matintegrity.seccm_archive_member.v1"
    member_name: str = Field(min_length=1)
    member_role: Literal[
        "footprint_pixels",
        "sem_intensity_table",
        "raw_chronoamperometry",
        "acquisition_parameters",
        "provider_descriptors",
        "provider_derived_descriptors",
        "provider_processed_ebsd",
        "provider_labels",
        "provider_model_table",
        "provider_readme",
    ]
    uncompressed_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class SeccmArchiveAudit(Contract):
    """Structural audit of the complete archive and raw CA matrix."""

    schema_version: Literal["matintegrity.seccm_archive_audit.v1"] = "matintegrity.seccm_archive_audit.v1"
    dataset_id: str = Field(min_length=1)
    provider_record: str = Field(min_length=1)
    license_id: Literal["CC-BY-4.0"] = "CC-BY-4.0"
    archive_md5: str = Field(pattern=r"^[a-f0-9]{32}$")
    archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    archive_bytes: int = Field(gt=0)
    members: tuple[SeccmArchiveMemberRecord, ...]
    map_ids: tuple[int, ...]
    sample_count_per_trace: int = Field(gt=0)
    time_min_s: float = Field(ge=0)
    time_max_s: float = Field(gt=0)
    time_strictly_increasing: Literal[True]
    substrate_current_min_A: float
    substrate_current_max_A: float
    physical_specimen_scope: Literal["provider_map_physical_independence_unresolved"] = (
        "provider_map_physical_independence_unresolved"
    )
    table_relationship_status: Literal["member_roles_only_cross_table_alignment_unreviewed"] = (
        "member_roles_only_cross_table_alignment_unreviewed"
    )

    @model_validator(mode="after")
    def identities_are_complete(self):
        if self.map_ids != tuple(range(1, 206)):
            raise ValueError("pinned raw CA map IDs must be exactly 1 through 205")
        if len(self.members) != len(EXPECTED_MEMBERS):
            raise ValueError("pinned archive audit must cover every expected member")
        return self


class SeccmChronoamperometryTrace(Contract):
    """Provenance for one raw current trace returned as separate NumPy arrays."""

    schema_version: Literal["matintegrity.seccm_chronoamperometry_trace.v1"] = (
        "matintegrity.seccm_chronoamperometry_trace.v1"
    )
    dataset_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    map_id: int = Field(ge=1, le=205)
    map_point_label: str = Field(pattern=r"^MAP_Point_\d+$")
    provider_signal_label: str = Field(pattern=r"^I_Substrate_A_LN_\d+$")
    source_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_member: Literal["SS_NaCl_CA_M_1031_C.csv"] = "SS_NaCl_CA_M_1031_C.csv"
    source_member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sample_count: int = Field(gt=0)
    time_unit: Literal["s"] = "s"
    current_quantity: Literal["substrate_current"] = "substrate_current"
    current_unit: Literal["A"] = "A"
    unit_basis: str = Field(min_length=1)
    provider_code_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    provider_code_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    physical_specimen_independence: Literal["unresolved_across_map_points"] = "unresolved_across_map_points"
    interpretation_status: Literal["raw_signal_only"] = "raw_signal_only"


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _open_pinned_archive(path: str | Path, expected_archive_sha256: str) -> tuple[bytes, dict[str, bytes]]:
    source = Path(path)
    if source.stat().st_size <= 0 or source.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("SECCM archive is empty or exceeds the reviewed safety limit")
    content = source.read_bytes()
    if _sha256(content) != expected_archive_sha256:
        raise ValueError("SECCM archive SHA-256 differs from the caller-pinned digest")
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise ValueError("SECCM source is not a valid ZIP archive") from exc
    payloads: dict[str, bytes] = {}
    total = 0
    with archive:
        seen: set[str] = set()
        for member in archive.infolist():
            name = member.filename
            member_path = PurePosixPath(name)
            if (
                not name
                or "\\" in name
                or member_path.is_absolute()
                or any(part in {"", ".", ".."} for part in member_path.parts)
                or member.is_dir()
            ):
                raise ValueError(f"unsafe or unexpected SECCM ZIP member path: {name!r}")
            if name in seen:
                raise ValueError(f"duplicate SECCM ZIP member path: {name}")
            seen.add(name)
            if member.flag_bits & 0x1:
                raise ValueError(f"encrypted SECCM ZIP member is not supported: {name}")
            if member.file_size <= 0 or member.file_size > MAX_MEMBER_BYTES:
                raise ValueError(f"SECCM ZIP member exceeds its reviewed size limit: {name}")
            total += member.file_size
            if total > MAX_TOTAL_DECODED_BYTES:
                raise ValueError("SECCM ZIP decoded content exceeds the reviewed safety limit")
            payloads[name] = archive.read(member)
    if set(payloads) != set(EXPECTED_MEMBERS):
        raise ValueError("SECCM ZIP membership differs from the reviewed ten-file manifest")
    return content, payloads


def _parse_raw_ca(payload: bytes, selected_map_id: int | None = None) -> dict:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("SECCM raw CA member must be UTF-8 CSV") from exc
    rows = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(rows)
        signal_header = next(rows)
    except StopIteration as exc:
        raise ValueError("SECCM raw CA member is missing its two header rows") from exc
    expected_header = ["Unnamed: 0", *(f"MAP_Point_{value}" for value in range(1, 206))]
    if header != expected_header:
        raise ValueError("SECCM raw CA map-point header changed")
    if (
        len(signal_header) != 206
        or signal_header[0] != "Time_Hold_s"
        or not all(_SIGNAL_LABEL.fullmatch(value) for value in signal_header[1:])
        or len(set(signal_header[1:])) != 205
    ):
        raise ValueError("SECCM raw CA embedded quantity/unit header changed")
    if selected_map_id is not None and selected_map_id not in range(1, 206):
        raise ValueError("SECCM map_id must be between 1 and 205")

    time_values: list[float] = []
    selected_values: list[float] = []
    current_min = math.inf
    current_max = -math.inf
    previous_time: float | None = None
    for row_number, row in enumerate(rows, start=3):
        if row_number > MAX_CA_ROWS + 2:
            raise ValueError("SECCM raw CA member exceeds the reviewed row limit")
        if len(row) != 206:
            raise ValueError(f"SECCM raw CA row {row_number} does not have 206 fields")
        try:
            time_value = float(row[0])
            currents = [float(value) for value in row[1:]]
        except ValueError as exc:
            raise ValueError(f"SECCM raw CA row {row_number} contains nonnumeric text") from exc
        if not math.isfinite(time_value) or not all(math.isfinite(value) for value in currents):
            raise ValueError(f"SECCM raw CA row {row_number} contains a nonfinite value")
        if time_value < 0 or (previous_time is not None and time_value <= previous_time):
            raise ValueError("SECCM raw CA time must be nonnegative and strictly increasing")
        previous_time = time_value
        time_values.append(time_value)
        current_min = min(current_min, min(currents))
        current_max = max(current_max, max(currents))
        if selected_map_id is not None:
            selected_values.append(currents[selected_map_id - 1])
    if not time_values:
        raise ValueError("SECCM raw CA member contains no numeric samples")
    return {
        "map_ids": tuple(range(1, 206)),
        "signal_header": signal_header,
        "time_s": np.asarray(time_values, dtype=float),
        "selected_current_A": np.asarray(selected_values, dtype=float),
        "current_min_A": current_min,
        "current_max_A": current_max,
    }


def audit_seccm_archive(
    path: str | Path,
    *,
    expected_archive_sha256: str = SECCM_ARCHIVE_SHA256,
    dataset_id: str = SECCM_DATASET_ID,
) -> SeccmArchiveAudit:
    """Audit all archive members and the complete raw CA numeric matrix."""
    content, payloads = _open_pinned_archive(path, expected_archive_sha256)
    parsed = _parse_raw_ca(payloads["SS_NaCl_CA_M_1031_C.csv"])
    members = tuple(
        SeccmArchiveMemberRecord(
            member_name=name,
            member_role=EXPECTED_MEMBERS[name],
            uncompressed_bytes=len(payloads[name]),
            sha256=_sha256(payloads[name]),
        )
        for name in sorted(payloads)
    )
    return SeccmArchiveAudit(
        dataset_id=dataset_id,
        provider_record=SECCM_PROVIDER_RECORD,
        archive_md5=hashlib.md5(content, usedforsecurity=False).hexdigest(),
        archive_sha256=_sha256(content),
        archive_bytes=len(content),
        members=members,
        map_ids=parsed["map_ids"],
        sample_count_per_trace=len(parsed["time_s"]),
        time_min_s=float(parsed["time_s"][0]),
        time_max_s=float(parsed["time_s"][-1]),
        time_strictly_increasing=True,
        substrate_current_min_A=float(parsed["current_min_A"]),
        substrate_current_max_A=float(parsed["current_max_A"]),
    )


def read_seccm_ca_trace(
    path: str | Path,
    map_id: int,
    *,
    physical_specimen_id: str,
    source_group_id: str,
    expected_archive_sha256: str = SECCM_ARCHIVE_SHA256,
    dataset_id: str = SECCM_DATASET_ID,
) -> dict:
    """Return one raw site trace without smoothing, scaling, labeling, or descriptor extraction."""
    if not physical_specimen_id.strip() or not source_group_id.strip():
        raise ValueError("physical specimen and source-group identities are required")
    content, payloads = _open_pinned_archive(path, expected_archive_sha256)
    raw = payloads["SS_NaCl_CA_M_1031_C.csv"]
    parsed = _parse_raw_ca(raw, selected_map_id=map_id)
    metadata = SeccmChronoamperometryTrace(
        dataset_id=dataset_id,
        physical_specimen_id=physical_specimen_id,
        source_group_id=source_group_id,
        map_id=map_id,
        map_point_label=f"MAP_Point_{map_id}",
        provider_signal_label=parsed["signal_header"][map_id],
        source_archive_sha256=_sha256(content),
        source_member_sha256=_sha256(raw),
        sample_count=len(parsed["time_s"]),
        unit_basis=(
            "Pinned provider CSV embedded headers Time_Hold_s and I_Substrate_A; independently "
            f"reviewed against provider MIT notebook commit {SECCM_CODE_COMMIT}."
        ),
        provider_code_commit=SECCM_CODE_COMMIT,
        provider_code_sha256=SECCM_CODE_SHA256,
    )
    return {
        "metadata": metadata,
        "time_s": parsed["time_s"],
        "substrate_current_A": parsed["selected_current_A"],
    }

"""Bounded local reader for the CC0 Zenodo magnesium-alloy DEIS archive.

The base reader preserves the provider's numeric matrix order. An optional
caller-reviewed view follows the depositor's adjacent real/imaginary column
description, without assigning row axes, units, or timestamps.
"""

from __future__ import annotations

import csv
import hashlib
import io
import math
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import Field

from .contracts import Calculation, Contract, canonical_digest
from .registry import ModelSpec

DATASET_ID = "az-we43-az31-molybdate-eis"
DATASET_DOI = "10.5281/zenodo.10482561"
ARCHIVE_SHA256 = "38d69f883ede6caaf988c3af9dd56f34c071f97b668d93fad778428c26dbed7c"
ARCHIVE_BYTES = 30_886_921
DEPOSITOR_METADATA_SHA256 = "c1d178a8a7602316963078ee9351b6966f73db9f380d1438205a02723218024a"
DEPOSITOR_METADATA_BYTES = 7_513
DEIS_MEMBERS = {
    "DEIS/AZ31/AZ31-zw.txt": "AZ31",
    "DEIS/WE43/WE43-zw.txt": "WE43",
}
EXPECTED_MEMBERS = frozenset(
    {
        "DEIS/AZ31/",
        "DEIS/AZ31/AZ31-zw.txt",
        "DEIS/WE43/",
        "DEIS/WE43/WE43-zw.txt",
        "SEM/Opt_AZ31_1h.jpg",
        "SEM/Opt_AZ31_24h.jpg",
        "SEM/Opt_WE43_1h.jpg",
        "SEM/Opt_WE43_24h.jpg",
        "SEM/SEM_AZ31_1h.tif",
        "SEM/SEM_AZ31_24h.tif",
        "SEM/SEM_WE43_1h.tif",
        "SEM/SEM_WE43_24h.tif",
        "XPS/AZ31_1h.vms",
        "XPS/AZ31_24h.vms",
        "XPS/WE43_1h.vms",
        "XPS/WE43_24h.vms",
    }
)
EXPECTED_MATRIX_SHAPE = (54, 8640)
MAX_ARCHIVE_BYTES = ARCHIVE_BYTES
MAX_MATRIX_BYTES = 8_000_000


class ZenodoDeisArchiveAuditRequest(Contract):
    assessment_id: str = Field(min_length=1)
    local_archive_path: str = Field(min_length=1)
    local_only_archive_path_reviewed: bool
    cc0_dataset_reuse_basis_reviewed: bool
    computational_use_authorized: bool


def audit_zenodo_deis_archive_request(request: ZenodoDeisArchiveAuditRequest) -> Calculation:
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "dataset_license_id": "CC0-1.0",
        "input_sha256": input_digest,
    }
    missing = [
        name for name in (
            "local_only_archive_path_reviewed",
            "cc0_dataset_reuse_basis_reviewed",
            "computational_use_authorized",
        ) if not getattr(request, name)
    ]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    try:
        manifest = inspect_zenodo_deis_archive(request.local_archive_path)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        return Calculation(
            status="out_of_scope",
            values=base | {"archive_error_type": type(exc).__name__},
            notes=("The local archive did not satisfy the pinned revision and matrix structure contract.",),
        )
    return Calculation(
        values=base | {
            "manifest": manifest.model_dump(mode="json"),
            "raw_measurements_returned": False,
            "physical_qualification_inferred": False,
        },
        notes=("This result verifies archive layout and parser boundaries only; the row streaming API remains a separate caller-controlled data operation.",),
    )


class DeisMatrixMember(Contract):
    member_path: Literal["DEIS/AZ31/AZ31-zw.txt", "DEIS/WE43/WE43-zw.txt"]
    declared_material_label: Literal["AZ31", "WE43"]
    member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    member_bytes: int = Field(gt=0, le=MAX_MATRIX_BYTES)
    row_count: int = Field(gt=0, le=1000)
    column_count: int = Field(gt=0, le=10000)
    blank_cell_count: int = Field(ge=0)
    nonfinite_cell_count: int = Field(ge=0)
    delimiter: Literal["tab"] = "tab"
    raw_column_order_preserved: Literal[True] = True
    axis_mapping: Literal["not_declared_by_importer"] = "not_declared_by_importer"
    units_mapping: Literal["not_declared_by_importer"] = "not_declared_by_importer"
    spectrum_partitioning: Literal["not_declared_by_importer"] = "not_declared_by_importer"


class ZenodoDeisArchiveManifest(Contract):
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    dataset_license_id: Literal["CC0-1.0"] = "CC0-1.0"
    archive_sha256: Literal[ARCHIVE_SHA256]
    archive_bytes: Literal[ARCHIVE_BYTES]
    declared_use: Literal["local_analysis_only_until_caller_supplies_applicability"] = (
        "local_analysis_only_until_caller_supplies_applicability"
    )
    matrices: tuple[DeisMatrixMember, ...] = Field(min_length=2, max_length=2)
    non_deis_members_present: Literal[True] = True
    measured_observations_exported: Literal[False] = False
    physical_qualification_inferred: Literal[False] = False


class DeisAdjacentColumnPairView(Contract):
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    archive_sha256: Literal[ARCHIVE_SHA256]
    metadata_sha256: Literal[DEPOSITOR_METADATA_SHA256]
    member_path: Literal["DEIS/AZ31/AZ31-zw.txt", "DEIS/WE43/WE43-zw.txt"]
    member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    matrix_row_count: Literal[54] = 54
    matrix_column_count: Literal[8640] = 8640
    row_index_base: Literal[0] = 0
    column_index_base: Literal[0] = 0
    provider_described_spectrum_pair_count: Literal[4320] = 4320
    even_column_role: Literal["real_component"] = "real_component"
    following_odd_column_role: Literal["imaginary_component"] = "imaginary_component"
    real_column_index_formula: Literal["2*i"] = "2*i"
    imaginary_column_index_formula: Literal["2*i+1"] = "2*i+1"
    zero_based_adjacent_pairing_reviewed: Literal[True]
    row_axis_mapping: Literal["unresolved"] = "unresolved"
    time_mapping: Literal["unresolved"] = "unresolved"
    frequency_mapping: Literal["unresolved"] = "unresolved"
    impedance_units: Literal["unresolved"] = "unresolved"
    pairing_is_physical_time_series: Literal[False] = False


class ZenodoDeisDepositorConditionSummary(Contract):
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    metadata_sha256: Literal[DEPOSITOR_METADATA_SHA256]
    metadata_bytes: Literal[DEPOSITOR_METADATA_BYTES]
    alloy_labels: tuple[Literal["AZ31"], Literal["WE43"]] = ("AZ31", "WE43")
    electrolyte_label: Literal["Hank's solution"] = "Hank's solution"
    inhibitor_stock_chemical_label: Literal["sodium molybdate as reported"] = "sodium molybdate as reported"
    inhibitor_final_chemical_label: Literal["Na2MoO4 as reported"] = "Na2MoO4 as reported"
    temperature_value: Literal[37.0] = 37.0
    temperature_uncertainty: Literal[0.1] = 0.1
    temperature_unit: Literal["degC as reported"] = "degC as reported"
    working_electrode_area_value: Literal[0.6] = 0.6
    working_electrode_area_unit: Literal["cm2 as reported"] = "cm2 as reported"
    final_electrolyte_volume_value: Literal[60.0] = 60.0
    final_electrolyte_volume_unit: Literal["mL as reported"] = "mL as reported"
    inhibitor_stock_concentration_value: Literal[600.0] = 600.0
    inhibitor_final_concentration_value: Literal[150.0] = 150.0
    inhibitor_concentration_unit: Literal["mM as reported"] = "mM as reported"
    inhibitor_injection_duration_value: Literal[50.0] = 50.0
    inhibitor_injection_duration_unit: Literal["min as reported"] = "min as reported"
    baseline_without_inhibitor_duration_value: Literal[10.0] = 10.0
    baseline_duration_unit: Literal["min as reported"] = "min as reported"
    post_inhibition_exposure_duration_value: Literal[12.0] = 12.0
    exposure_duration_unit: Literal["h as reported"] = "h as reported"
    inhibitor_initial_electrolyte_volume_value: Literal[45.0] = 45.0
    inhibitor_initial_electrolyte_volume_unit: Literal["mL as reported"] = "mL as reported"
    all_facts_are_depositor_metadata: Literal[True] = True
    continuous_concentration_path_reconstructed: Literal[False] = False
    matrix_columns_mapped_to_timestamps: Literal[False] = False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _matrix_member_manifest(archive: zipfile.ZipFile, member_path: str) -> DeisMatrixMember:
    try:
        info = archive.getinfo(member_path)
    except KeyError as exc:
        raise ValueError(f"required DEIS member is absent: {member_path}") from exc
    if info.is_dir() or info.file_size <= 0 or info.file_size > MAX_MATRIX_BYTES:
        raise ValueError("DEIS member size/type is outside the reviewed import bound")
    raw = archive.read(info)
    member_hash = hashlib.sha256(raw).hexdigest()
    text = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8-sig", errors="strict", newline="")
    reader = csv.reader(text, delimiter="\t", strict=True)
    row_count = 0
    column_count: int | None = None
    blank_count = 0
    nonfinite_count = 0
    try:
        for row in reader:
            row_count += 1
            if row_count > 1000:
                raise ValueError("DEIS matrix row budget exceeded")
            if column_count is None:
                column_count = len(row)
            if len(row) != column_count or len(row) > 10000:
                raise ValueError("DEIS matrix rows have inconsistent or oversized width")
            for value in row:
                token = value.strip()
                if not token:
                    blank_count += 1
                    continue
                try:
                    number = float(token)
                except ValueError as exc:
                    raise ValueError("DEIS matrix contains an unexpected nonnumeric token") from exc
                if not math.isfinite(number):
                    nonfinite_count += 1
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError("DEIS matrix is not valid UTF-8 tabular data") from exc
    finally:
        text.close()
    if (row_count, column_count) != EXPECTED_MATRIX_SHAPE:
        raise ValueError("DEIS matrix shape differs from the reviewed dataset revision")
    if blank_count or nonfinite_count:
        raise ValueError("DEIS matrix contains blank or nonfinite cells; no repair is performed")
    return DeisMatrixMember(
        member_path=member_path,
        declared_material_label=DEIS_MEMBERS[member_path],
        member_sha256=member_hash,
        member_bytes=info.file_size,
        row_count=row_count,
        column_count=column_count,
        blank_cell_count=blank_count,
        nonfinite_cell_count=nonfinite_count,
    )


def inspect_zenodo_deis_archive(path: str | Path) -> ZenodoDeisArchiveManifest:
    """Pin the local archive and summarize DEIS table shape without returning values."""
    archive_path = Path(path)
    if not archive_path.is_file() or archive_path.stat().st_size != ARCHIVE_BYTES:
        raise ValueError("local archive size differs from the pinned Zenodo asset")
    archive_hash = _sha256(archive_path)
    if archive_hash != ARCHIVE_SHA256:
        raise ValueError("local archive SHA-256 differs from the pinned Zenodo asset")
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        if len(names) != len(set(names)) or set(names) != EXPECTED_MEMBERS:
            raise ValueError("archive member inventory differs from the pinned record")
        if sum(item.file_size for item in infos) > 100_000_000:
            raise ValueError("archive uncompressed-size budget exceeded")
        if any(item.flag_bits & 0x1 or item.file_size > 25_000_000 for item in infos):
            raise ValueError("archive contains an encrypted or oversized member")
        if archive.testzip() is not None:
            raise ValueError("archive member CRC validation failed")
        matrices = tuple(_matrix_member_manifest(archive, member) for member in DEIS_MEMBERS)
    return ZenodoDeisArchiveManifest(archive_sha256=archive_hash, matrices=matrices)


def iter_zenodo_deis_rows(
    path: str | Path,
    manifest: ZenodoDeisArchiveManifest,
    member_path: Literal["DEIS/AZ31/AZ31-zw.txt", "DEIS/WE43/WE43-zw.txt"],
) -> Iterator[tuple[float, ...]]:
    """Stream one raw matrix by row after rechecking archive and member digests.

    Row and column positions are retained as supplied. No frequency/time axis,
    component pairing, unit conversion, interpolation, or smoothing is applied.
    """
    if manifest.archive_sha256 != ARCHIVE_SHA256:
        raise ValueError("manifest is not bound to this pinned archive revision")
    archive_path = Path(path)
    fresh_manifest = inspect_zenodo_deis_archive(archive_path)
    if canonical_digest(fresh_manifest.model_dump(mode="json")) != canonical_digest(
        manifest.model_dump(mode="json")
    ):
        raise ValueError("supplied manifest differs from a fresh pinned archive inspection")
    member = next((row for row in manifest.matrices if row.member_path == member_path), None)
    if member is None:
        raise ValueError("requested member is not in the manifest")
    with zipfile.ZipFile(archive_path) as archive:
        raw = archive.read(member_path)
    if hashlib.sha256(raw).hexdigest() != member.member_sha256:
        raise ValueError("DEIS member changed after its manifest was produced")
    text = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8-sig", errors="strict", newline="")
    try:
        reader = csv.reader(text, delimiter="\t", strict=True)
        row_count = 0
        for row in reader:
            row_count += 1
            if len(row) != member.column_count or row_count > member.row_count:
                raise ValueError("DEIS matrix shape changed during streaming")
            numbers = tuple(float(value) for value in row)
            if any(not math.isfinite(value) for value in numbers):
                raise ValueError("DEIS matrix contains a nonfinite value")
            yield numbers
        if row_count != member.row_count:
            raise ValueError("DEIS matrix row count changed during streaming")
    finally:
        text.close()


def summarize_zenodo_deis_depositor_conditions(
    metadata_path: str | Path,
) -> ZenodoDeisDepositorConditionSummary:
    """Return fixed-version facts from the depositor's separately pinned metadata."""
    path = Path(metadata_path)
    if not path.is_file() or path.stat().st_size != DEPOSITOR_METADATA_BYTES:
        raise ValueError("depositor metadata size differs from the pinned description file")
    if _sha256(path) != DEPOSITOR_METADATA_SHA256:
        raise ValueError("depositor metadata SHA-256 differs from the pinned description file")
    return ZenodoDeisDepositorConditionSummary(metadata_sha256=DEPOSITOR_METADATA_SHA256)


def create_zenodo_deis_adjacent_pair_view(
    manifest: ZenodoDeisArchiveManifest,
    conditions: ZenodoDeisDepositorConditionSummary,
    member_path: Literal["DEIS/AZ31/AZ31-zw.txt", "DEIS/WE43/WE43-zw.txt"],
    *,
    zero_based_adjacent_pairing_reviewed: bool,
) -> DeisAdjacentColumnPairView:
    """Opt in to the depositor-described adjacent real/imaginary column grouping.

    This maps column pairs only. It does not define what matrix rows represent.
    """
    if not zero_based_adjacent_pairing_reviewed:
        raise ValueError("caller review of the pinned metadata's adjacent real/imaginary mapping is required")
    if manifest.archive_sha256 != ARCHIVE_SHA256 or conditions.metadata_sha256 != DEPOSITOR_METADATA_SHA256:
        raise ValueError("archive manifest and depositor metadata summary must match their pinned revisions")
    member = next((row for row in manifest.matrices if row.member_path == member_path), None)
    if member is None or member.column_count != EXPECTED_MATRIX_SHAPE[1] or member.row_count != EXPECTED_MATRIX_SHAPE[0]:
        raise ValueError("selected DEIS member does not match the reviewed matrix shape")
    return DeisAdjacentColumnPairView(
        archive_sha256=manifest.archive_sha256,
        metadata_sha256=conditions.metadata_sha256,
        member_path=member_path,
        member_sha256=member.member_sha256,
        zero_based_adjacent_pairing_reviewed=True,
    )


def iter_zenodo_deis_adjacent_spectrum_pairs(
    path: str | Path,
    manifest: ZenodoDeisArchiveManifest,
    view: DeisAdjacentColumnPairView,
) -> Iterator[tuple[int, tuple[tuple[float, float], ...]]]:
    """Stream row-indexed adjacent (real, imaginary) pairs under explicit review.

    Each yield is `(zero_based_row_index, ((real_0, imag_0), ...))`. Row axes,
    timestamp, frequency, units and physical spectrum timing remain unresolved.
    """
    if not view.zero_based_adjacent_pairing_reviewed:
        raise ValueError("adjacent column pairing has not been caller-reviewed")
    if view.archive_sha256 != manifest.archive_sha256 or view.archive_sha256 != ARCHIVE_SHA256:
        raise ValueError("pair view does not match the supplied archive manifest")
    member = next((row for row in manifest.matrices if row.member_path == view.member_path), None)
    if member is None or member.member_sha256 != view.member_sha256:
        raise ValueError("pair view member digest does not match the archive manifest")
    for row_index, values in enumerate(iter_zenodo_deis_rows(path, manifest, view.member_path)):
        pairs = tuple((values[2 * pair], values[2 * pair + 1]) for pair in range(view.provider_described_spectrum_pair_count))
        yield row_index, pairs


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "data.zenodo_deis_archive_structure",
            ZenodoDeisArchiveAuditRequest,
            audit_zenodo_deis_archive_request,
            {"manifest.matrices[].row_count": "row", "manifest.matrices[].column_count": "column"},
            (
                "Read one pinned CC0 Zenodo archive from a caller-supplied local path; network access is not performed.",
                "Verify archive/member digests, exact member inventory, matrix shape and finite numeric contents.",
                "Keep matrix row order while leaving axes, units, spectrum pairing and physical interpretation unspecified.",
                "Archive audit is not electrochemical fitting, corrosion rate, alloy ranking or qualification.",
            ),
            ("zenodo_mg_deis_archive_structure",),
            qualification="data_import",
        )
    ]

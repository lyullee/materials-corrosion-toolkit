"""Safe, optional Oxford .cpr/.crc phase-label ingestion through DefDAP."""

from __future__ import annotations

import hashlib
import math
import shutil
import stat
import tempfile
import zipfile
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Literal

import numpy as np
from pydantic import Field

from .contracts import Contract
from .spatial_fields import numeric_array_digest


class OxfordEbsdPhaseLabelReadRecord(Contract):
    """Audit metadata for labels read from one Oxford binary map pair."""

    schema_version: Literal["matintegrity.oxford_ebsd_phase_label_read.v1"] = (
        "matintegrity.oxford_ebsd_phase_label_read.v1"
    )
    archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cpr_member: str = Field(min_length=1)
    cpr_member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    crc_member: str = Field(min_length=1)
    crc_member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    label_array_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    shape: tuple[int, int]
    dtype: str = Field(min_length=1)
    label_values: tuple[int, ...]
    nonindexed_label_value: int = 0
    provider_grid_step_value: float | None = None
    provider_grid_step_unit_status: Literal["not_declared_by_adapter"] = "not_declared_by_adapter"
    phase_descriptor_count: int = Field(ge=0)
    reader_compatibility_patch: Literal["none", "identity_rotation_placeholder_for_omitted_orientation"] = (
        "none"
    )
    reader_name: Literal["DefDAP"] = "DefDAP"
    reader_version: str = Field(min_length=1)
    file_format: Literal["Oxford .cpr/.crc"] = "Oxford .cpr/.crc"


@dataclass(frozen=True)
class OxfordEbsdPhaseLabelMap:
    """Read-only copy of one raw integer phase-label map and its audit record."""

    labels: np.ndarray
    record: OxfordEbsdPhaseLabelReadRecord

    def __post_init__(self) -> None:
        array = np.array(self.labels, copy=True)
        if array.shape != self.record.shape or array.dtype.kind not in "iu":
            raise ValueError("phase-label array must be integer-valued and match the reader record shape")
        if tuple(int(value) for value in np.unique(array)) != self.record.label_values:
            raise ValueError("phase-label values do not match the reader record")
        if numeric_array_digest(array) != self.record.label_array_sha256:
            raise ValueError("phase-label array does not match the reader record digest")
        array.setflags(write=False)
        object.__setattr__(self, "labels", array)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _archive_entries(archive: zipfile.ZipFile, *, max_uncompressed_bytes: int) -> dict[str, zipfile.ZipInfo]:
    entries: dict[str, zipfile.ZipInfo] = {}
    if len(archive.infolist()) > 4096:
        raise ValueError("EBSD archive contains too many members")
    total_uncompressed = 0
    for info in archive.infolist():
        name = info.filename
        path = PurePosixPath(name)
        mode = info.external_attr >> 16
        if (
            not name
            or "\\" in name
            or path.is_absolute()
            or any(part in {"", ".", ".."} for part in path.parts)
            or (len(path.parts) == 1 and ":" in path.parts[0])
        ):
            raise ValueError(f"unsafe path in EBSD archive: {name!r}")
        if name in entries:
            raise ValueError(f"duplicate path in EBSD archive: {name!r}")
        if info.flag_bits & 0x1:
            raise ValueError(f"encrypted EBSD archive member is unsupported: {name!r}")
        if stat.S_ISLNK(mode):
            raise ValueError(f"symbolic link in EBSD archive is unsupported: {name!r}")
        total_uncompressed += info.file_size
        if total_uncompressed > max_uncompressed_bytes:
            raise ValueError("EBSD archive exceeds the configured uncompressed-size limit")
        entries[name] = info
    return entries


def read_oxford_ebsd_phase_labels(
    archive_path: str | Path,
    member_basename: str,
    *,
    expected_archive_sha256: str,
    max_archive_bytes: int = 60_000_000,
    max_uncompressed_bytes: int = 150_000_000,
    max_member_bytes: int = 100_000_000,
    loader_factory: Callable[[], Any] | None = None,
) -> OxfordEbsdPhaseLabelMap:
    """Read one explicitly selected Oxford pair without extracting other archive content.

    The optional DefDAP reader supplies raw integer phase labels and format metadata only.
    This adapter does not infer label identities, physical step units, ROI or uncertainty.
    """
    archive_file = Path(archive_path)
    if not archive_file.is_file():
        raise FileNotFoundError(archive_file)
    if archive_file.stat().st_size > max_archive_bytes:
        raise ValueError("EBSD archive exceeds the configured compressed-size limit")
    if len(expected_archive_sha256) != 64 or any(
        char not in "0123456789abcdef" for char in expected_archive_sha256
    ):
        raise ValueError("expected_archive_sha256 must be a lowercase SHA-256 digest")
    archive_digest = _sha256_file(archive_file)
    if archive_digest != expected_archive_sha256:
        raise ValueError("EBSD archive digest differs from the caller-pinned SHA-256")
    if (
        not member_basename
        or Path(member_basename).name != member_basename
        or member_basename in {".", ".."}
        or "/" in member_basename
        or "\\" in member_basename
    ):
        raise ValueError("member_basename must be a plain file stem from the archive")

    cpr_name = f"{member_basename}.cpr"
    crc_name = f"{member_basename}.crc"
    with zipfile.ZipFile(archive_file) as archive:
        entries = _archive_entries(archive, max_uncompressed_bytes=max_uncompressed_bytes)
        if cpr_name not in entries or crc_name not in entries:
            raise ValueError("archive must contain the exact requested Oxford .cpr/.crc member pair")
        cpr_info, crc_info = entries[cpr_name], entries[crc_name]
        if cpr_info.file_size > max_member_bytes or crc_info.file_size > max_member_bytes:
            raise ValueError("requested Oxford member exceeds the configured uncompressed-size limit")
        with tempfile.TemporaryDirectory(prefix="matintegrity-oxford-ebsd-") as temporary:
            folder = Path(temporary)
            extracted: dict[str, Path] = {}
            for info in (cpr_info, crc_info):
                target = folder / info.filename
                with archive.open(info) as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination, length=1024 * 1024)
                if target.stat().st_size != info.file_size:
                    raise ValueError(f"extracted member size differs from its ZIP directory: {info.filename}")
                extracted[info.filename] = target
            cpr_digest = _sha256_file(extracted[cpr_name])
            crc_digest = _sha256_file(extracted[crc_name])

            if loader_factory is None:
                try:
                    from defdap.file_readers import OxfordBinaryLoader
                except ImportError as exc:
                    raise ImportError(
                        "Oxford EBSD reading requires the optional 'ebsd' dependency: pip install matintegrity[ebsd]"
                    ) from exc
                loader_factory = OxfordBinaryLoader
            try:
                reader_version = version("DefDAP")
            except PackageNotFoundError:
                if loader_factory.__module__.startswith("defdap"):
                    raise ImportError(
                        "DefDAP package metadata is unavailable; install a packaged DefDAP release"
                    ) from None
                reader_version = "injected-test-reader"

            reader_folder = folder / "reader-input"
            reader_folder.mkdir()
            reader_crc = reader_folder / crc_name
            shutil.copyfile(extracted[crc_name], reader_crc)
            cpr_text = extracted[cpr_name].read_text(encoding="utf-8-sig")
            has_orientation_group = any(
                line.strip().casefold() == "[acquisition surface]" for line in cpr_text.splitlines()
            )
            orientation_keys = {"euler1", "euler2", "euler3"}
            if has_orientation_group:
                current_group = ""
                observed_orientation_keys = set()
                for line in cpr_text.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("[") and stripped.endswith("]"):
                        current_group = stripped[1:-1].strip().casefold()
                    elif current_group == "acquisition surface" and "=" in stripped:
                        observed_orientation_keys.add(stripped.split("=", 1)[0].strip().casefold())
                if not orientation_keys.issubset(observed_orientation_keys):
                    raise ValueError("Oxford CPR has a partial acquisition-orientation group")
                compatibility_patch = "none"
                reader_cpr_text = cpr_text
            else:
                compatibility_patch = "identity_rotation_placeholder_for_omitted_orientation"
                reader_cpr_text = (
                    cpr_text.rstrip() + "\n\n[Acquisition Surface]\nEuler1=0\nEuler2=0\nEuler3=0\n"
                )
            (reader_folder / cpr_name).write_text(reader_cpr_text, encoding="utf-8", newline="\n")

            loader = loader_factory()
            loader.load(reader_crc)
            raw_labels = np.asarray(loader.loaded_data.phase)
            metadata = loader.loaded_metadata
            shape_value = tuple(int(value) for value in metadata.get("shape", ()))
            if len(shape_value) != 2 or any(value <= 0 for value in shape_value):
                raise ValueError("Oxford reader returned an invalid two-dimensional map shape")
            if (
                raw_labels.shape != shape_value
                or raw_labels.dtype.kind not in "iu"
                or raw_labels.dtype.kind == "b"
            ):
                raise ValueError("Oxford reader returned labels with an invalid dtype or unexpected shape")
            labels = np.array(raw_labels, copy=True)
            observed = tuple(int(value) for value in np.unique(labels))
            step_value = metadata.get("step_size")
            if step_value is not None:
                step_value = float(step_value)
                if not math.isfinite(step_value) or step_value < 0:
                    raise ValueError("Oxford reader returned a negative or nonfinite grid step")
                if step_value == 0:
                    step_value = None
            phase_descriptors = metadata.get("phases", ())
            phase_count = len(phase_descriptors) if phase_descriptors is not None else 0

            record = OxfordEbsdPhaseLabelReadRecord(
                archive_sha256=archive_digest,
                cpr_member=cpr_name,
                cpr_member_sha256=cpr_digest,
                crc_member=crc_name,
                crc_member_sha256=crc_digest,
                label_array_sha256=numeric_array_digest(labels),
                shape=shape_value,
                dtype=str(labels.dtype),
                label_values=observed,
                provider_grid_step_value=step_value,
                phase_descriptor_count=phase_count,
                reader_compatibility_patch=compatibility_patch,
                reader_version=reader_version,
            )
    return OxfordEbsdPhaseLabelMap(labels=labels, record=record)

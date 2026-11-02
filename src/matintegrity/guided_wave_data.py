"""Read the pinned pipeline guided-wave archive without inferring wall loss or damage steps."""

from __future__ import annotations

import hashlib
import io
import math
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Iterator

import numpy as np

GUIDED_WAVE_ARCHIVE_SHA256 = "cf24cb3f1bb79e7c3a37502f5f5c392b6ca8b1a0a35f6e2b04758a1ffa4340fb"
GUIDED_WAVE_DATASET_ID = "guided-wave-pipeline-shm"
EXPECTED_FREQUENCIES_HZ = (14_000.0, 18_000.0, 24_000.0, 30_000.0, 37_000.0)
ARTICLE_REPORTED_MATRIX_SHAPE = (2057, 4)
MAX_OUTER_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_NESTED_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_WORKBOOK_BYTES = 8 * 1024 * 1024
MAX_NESTED_MEMBERS = 1000

_WORKBOOK = re.compile(r"^Window-1\.G4-288-(?P<acquisition_id>\d+)-V-0-waveform\.xls$")
_SHEET = re.compile(r"^V 0 (?P<frequency>\d+(?:\.\d+)?)kHz (?P<cycles>\d+(?:\.\d+)?)cy$")
_HEADERS = ("distance [m]", "torsional [V]", "flexural [V]", "pure DAC [V]")
_OLE_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _safe_members(archive: zipfile.ZipFile, *, label: str) -> list[zipfile.ZipInfo]:
    """Reject path aliases, traversal, encryption and duplicate members before reading."""
    if len(archive.infolist()) > MAX_NESTED_MEMBERS:
        raise ValueError(f"too many {label} members")
    seen: set[str] = set()
    files: list[zipfile.ZipInfo] = []
    for member in archive.infolist():
        name = member.filename
        path = PurePosixPath(name)
        if (
            not name
            or "\\" in name
            or path.is_absolute()
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise ValueError(f"unsafe {label} member path: {name!r}")
        normalized = path.as_posix().rstrip("/")
        if normalized in seen:
            raise ValueError(f"duplicate {label} member path: {normalized}")
        seen.add(normalized)
        if member.flag_bits & 0x1:
            raise ValueError(f"encrypted {label} member is not supported: {name}")
        if not member.is_dir():
            files.append(member)
    return files


def _open_nested_archive(
    path: str | Path,
    *,
    require_pinned_hash: bool,
    expected_archive_sha256: str,
) -> tuple[bytes, str, str, list[tuple[int, zipfile.ZipInfo]]]:
    source = Path(path)
    if source.stat().st_size > MAX_OUTER_ARCHIVE_BYTES:
        raise ValueError("guided-wave outer archive exceeds the safety limit")
    outer_content = source.read_bytes()
    outer_sha256 = _sha256(outer_content)
    if require_pinned_hash and outer_sha256 != expected_archive_sha256:
        raise ValueError("guided-wave outer archive digest does not match the pinned source")
    try:
        outer = zipfile.ZipFile(io.BytesIO(outer_content))
    except zipfile.BadZipFile as exc:
        raise ValueError("guided-wave outer archive is not a valid ZIP") from exc
    with outer:
        outer_files = _safe_members(outer, label="outer ZIP")
        if len(outer_files) != 1 or not outer_files[0].filename.lower().endswith(".zip"):
            raise ValueError("guided-wave outer archive must contain exactly one nested ZIP")
        if outer_files[0].file_size > MAX_NESTED_ARCHIVE_BYTES:
            raise ValueError("guided-wave nested archive exceeds the safety limit")
        nested_content = outer.read(outer_files[0])
    nested_sha256 = _sha256(nested_content)
    try:
        nested = zipfile.ZipFile(io.BytesIO(nested_content))
    except zipfile.BadZipFile as exc:
        raise ValueError("guided-wave nested archive is not a valid ZIP") from exc
    with nested:
        nested_files = _safe_members(nested, label="nested ZIP")
        acquisitions: list[tuple[int, zipfile.ZipInfo]] = []
        seen_ids: set[int] = set()
        for member in nested_files:
            if member.file_size > MAX_WORKBOOK_BYTES:
                raise ValueError(f"guided-wave workbook exceeds the safety limit: {member.filename}")
            match = _WORKBOOK.fullmatch(PurePosixPath(member.filename).name)
            if match is None:
                raise ValueError(f"unexpected guided-wave nested member: {member.filename}")
            acquisition_id = int(match.group("acquisition_id"))
            if acquisition_id in seen_ids:
                raise ValueError(f"duplicate guided-wave acquisition ID: {acquisition_id}")
            seen_ids.add(acquisition_id)
            acquisitions.append((acquisition_id, member))
    if not acquisitions:
        raise ValueError("guided-wave archive contains no workbooks")
    acquisitions.sort(key=lambda item: item[0])
    return nested_content, outer_sha256, nested_sha256, acquisitions


def _period_labels(
    acquisition_ids: list[int], *, source_is_pinned: bool, article_state_review: bool
) -> dict[int, str]:
    if not source_is_pinned or not article_state_review:
        return {value: "unreviewed" for value in acquisition_ids}
    if len(acquisition_ids) != 236:
        raise ValueError("pinned guided-wave archive no longer has 236 acquisitions")
    return {
        value: "reported_healthy_period" if index < 207 else "post_machining_period"
        for index, value in enumerate(acquisition_ids)
    }


def list_guided_wave_acquisitions(
    path: str | Path,
    *,
    require_pinned_hash: bool = True,
    expected_archive_sha256: str = GUIDED_WAVE_ARCHIVE_SHA256,
    article_state_review: bool = True,
) -> dict:
    """List workbook identities without parsing signal matrices."""
    nested_content, outer_sha256, nested_sha256, acquisitions = _open_nested_archive(
        path,
        require_pinned_hash=require_pinned_hash,
        expected_archive_sha256=expected_archive_sha256,
    )
    source_is_pinned = outer_sha256 == GUIDED_WAVE_ARCHIVE_SHA256
    acquisition_ids = [value for value, _ in acquisitions]
    periods = _period_labels(
        acquisition_ids,
        source_is_pinned=source_is_pinned,
        article_state_review=article_state_review,
    )
    return {
        "dataset_id": GUIDED_WAVE_DATASET_ID,
        "outer_archive_sha256": outer_sha256,
        "outer_archive_bytes": Path(path).stat().st_size,
        "nested_archive_sha256": nested_sha256,
        "nested_archive_bytes": len(nested_content),
        "source_is_pinned": source_is_pinned,
        "article_state_review_applied": bool(source_is_pinned and article_state_review),
        "acquisitions": [
            {
                "acquisition_id": acquisition_id,
                "member_path": member.filename,
                "compressed_bytes": member.compress_size,
                "workbook_bytes": member.file_size,
                "article_period_group": periods[acquisition_id],
                "machining_step_id": None,
                "timestamp": None,
                "temperature_K": None,
            }
            for acquisition_id, member in acquisitions
        ],
        "qualification": (
            "The archive inventory establishes file identities only. The reviewed article period split "
            "is applied only to the pinned archive. It does not identify any of the six machining steps, "
            "natural corrosion growth, remaining thickness, timestamps, temperatures or independent specimens."
        ),
    }


def _number(sheet, row: int, column: int) -> float:
    value = sheet.cell_value(row, column)
    if isinstance(value, bool):
        raise ValueError("boolean cell cannot be a guided-wave observation")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"nonnumeric guided-wave value at {sheet.name}!R{row + 1}C{column + 1}") from exc
    if not math.isfinite(number):
        raise ValueError(f"nonfinite guided-wave value at {sheet.name}!R{row + 1}C{column + 1}")
    return number


def _read_workbook(
    content: bytes,
    *,
    acquisition_id: int,
    member_path: str,
    specimen_id: str,
    article_period_group: str,
    outer_archive_sha256: str,
    nested_archive_sha256: str,
    source_sheet_order_required: bool = True,
) -> dict:
    if not content.startswith(_OLE_MAGIC):
        raise ValueError("guided-wave member is not an OLE BIFF workbook")
    try:
        import xlrd
    except ImportError as exc:  # pragma: no cover - exercised by optional-dependency install checks
        raise ImportError("guided-wave XLS reading requires the 'science' extra with xlrd") from exc
    try:
        workbook = xlrd.open_workbook(file_contents=content, on_demand=True)
    except xlrd.XLRDError as exc:
        raise ValueError("guided-wave member is not a readable legacy XLS workbook") from exc
    signals = []
    seen_frequencies: set[float] = set()
    try:
        for sheet_index, sheet_name in enumerate(workbook.sheet_names()):
            match = _SHEET.fullmatch(sheet_name)
            if match is None:
                raise ValueError(f"unrecognized guided-wave sheet name: {sheet_name}")
            frequency_hz = float(match.group("frequency")) * 1000.0
            cycles = float(match.group("cycles"))
            if frequency_hz in seen_frequencies:
                raise ValueError(f"duplicate guided-wave frequency: {frequency_hz}")
            seen_frequencies.add(frequency_hz)
            sheet = workbook.sheet_by_index(sheet_index)
            if sheet.nrows < 4 or sheet.ncols != 4:
                raise ValueError(f"unexpected guided-wave matrix shape in {sheet_name}")
            headers = tuple(str(sheet.cell_value(1, column)).strip() for column in range(4))
            if headers != _HEADERS:
                raise ValueError(f"guided-wave column schema changed in {sheet_name}")
            raw_window_label = str(sheet.cell_value(0, 0)).strip()
            if not raw_window_label:
                raise ValueError(f"missing provider raw-window label in {sheet_name}")
            matrix = np.asarray(
                [[_number(sheet, row, column) for column in range(4)] for row in range(2, sheet.nrows)],
                dtype=float,
            )
            distance_steps = np.diff(matrix[:, 0])
            if np.any(distance_steps < 0):
                raise ValueError(f"distance axis decreases in {sheet_name}; provider order is preserved")
            signals.append(
                {
                    "source_sheet_name": sheet_name,
                    "source_sheet_index": sheet_index,
                    "frequency_Hz": frequency_hz,
                    "excitation_cycles": cycles,
                    "raw_window_label": raw_window_label,
                    "source_matrix_shape": (sheet.nrows, sheet.ncols),
                    "numeric_sample_rows": len(matrix),
                    "repeated_distance_intervals": int(np.count_nonzero(distance_steps == 0)),
                    "distance_axis_order": "provider_nondecreasing_not_sorted",
                    "distance_m": matrix[:, 0],
                    "torsional_V": matrix[:, 1],
                    "flexural_V": matrix[:, 2],
                    "provider_pure_dac_V": matrix[:, 3],
                    "article_reported_matrix_shape": ARTICLE_REPORTED_MATRIX_SHAPE,
                    "article_shape_discrepancy": (sheet.nrows, sheet.ncols) != ARTICLE_REPORTED_MATRIX_SHAPE,
                }
            )
    finally:
        workbook.release_resources()
    if tuple(sorted(seen_frequencies)) != EXPECTED_FREQUENCIES_HZ:
        raise ValueError("guided-wave workbook does not contain the five expected frequencies")
    source_sheet_order = tuple(signal["frequency_Hz"] for signal in signals)
    if not source_sheet_order_required:
        source_sheet_order = tuple(sorted(source_sheet_order))
    signals.sort(key=lambda signal: signal["frequency_Hz"])
    return {
        "dataset_id": GUIDED_WAVE_DATASET_ID,
        "outer_archive_sha256": outer_archive_sha256,
        "nested_archive_sha256": nested_archive_sha256,
        "acquisition_id": acquisition_id,
        "specimen_id": specimen_id,
        "member_path": member_path,
        "workbook_sha256": _sha256(content),
        "source_sheet_frequency_order_Hz": source_sheet_order,
        "article_period_group": article_period_group,
        "article_period_group_basis": (
            "reviewed_pinned_archive_sequence" if article_period_group != "unreviewed" else "not_applied"
        ),
        "machining_step_id": None,
        "timestamp": None,
        "temperature_K": None,
        "signals": signals,
        "observation_meaning": "guided_wave_voltage_response_not_direct_wall_thickness",
        "physical_specimen_independence": "single_reported_laboratory_tube",
        "qualification": (
            "Voltage channels and the provider DAC column are preserved separately. No damage-step, "
            "defect dimension, remaining thickness, probability of detection, corrosion rate or failure "
            "probability is inferred from the waveforms."
        ),
    }


def iter_guided_wave_acquisitions(
    path: str | Path,
    *,
    specimen_id: str,
    require_pinned_hash: bool = True,
    expected_archive_sha256: str = GUIDED_WAVE_ARCHIVE_SHA256,
    article_state_review: bool = True,
) -> Iterator[dict]:
    """Parse acquisitions once through the nested archive; each result owns its NumPy arrays."""
    if not isinstance(specimen_id, str) or not specimen_id.strip():
        raise ValueError("a caller-supplied physical specimen ID is required")
    nested_content, outer_sha256, nested_sha256, acquisitions = _open_nested_archive(
        path,
        require_pinned_hash=require_pinned_hash,
        expected_archive_sha256=expected_archive_sha256,
    )
    acquisition_ids = [value for value, _ in acquisitions]
    periods = _period_labels(
        acquisition_ids,
        source_is_pinned=outer_sha256 == GUIDED_WAVE_ARCHIVE_SHA256,
        article_state_review=article_state_review,
    )
    with zipfile.ZipFile(io.BytesIO(nested_content)) as nested:
        for acquisition_id, member in acquisitions:
            yield _read_workbook(
                nested.read(member),
                acquisition_id=acquisition_id,
                member_path=member.filename,
                specimen_id=specimen_id,
                article_period_group=periods[acquisition_id],
                outer_archive_sha256=outer_sha256,
                nested_archive_sha256=nested_sha256,
            )


def read_guided_wave_acquisition(
    path: str | Path,
    acquisition_id: int,
    *,
    specimen_id: str,
    require_pinned_hash: bool = True,
    expected_archive_sha256: str = GUIDED_WAVE_ARCHIVE_SHA256,
    article_state_review: bool = True,
) -> dict:
    """Load exactly one acquisition while retaining archive and physical-scope identities."""
    if isinstance(acquisition_id, bool) or not isinstance(acquisition_id, int) or acquisition_id < 0:
        raise ValueError("acquisition ID must be a nonnegative integer")
    if not isinstance(specimen_id, str) or not specimen_id.strip():
        raise ValueError("a caller-supplied physical specimen ID is required")
    nested_content, outer_sha256, nested_sha256, acquisitions = _open_nested_archive(
        path,
        require_pinned_hash=require_pinned_hash,
        expected_archive_sha256=expected_archive_sha256,
    )
    acquisition_ids = [value for value, _ in acquisitions]
    selected = next((member for value, member in acquisitions if value == acquisition_id), None)
    if selected is None:
        raise KeyError(f"guided-wave acquisition ID not found: {acquisition_id}")
    periods = _period_labels(
        acquisition_ids,
        source_is_pinned=outer_sha256 == GUIDED_WAVE_ARCHIVE_SHA256,
        article_state_review=article_state_review,
    )
    with zipfile.ZipFile(io.BytesIO(nested_content)) as nested:
        return _read_workbook(
            nested.read(selected),
            acquisition_id=acquisition_id,
            member_path=selected.filename,
            specimen_id=specimen_id,
            article_period_group=periods[acquisition_id],
            outer_archive_sha256=outer_sha256,
            nested_archive_sha256=nested_sha256,
        )

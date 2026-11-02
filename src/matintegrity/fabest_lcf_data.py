"""Safe structural audit and streaming access for the public FABEST LCF package."""

from __future__ import annotations

import csv
import hashlib
import io
import math
import re
from collections import Counter
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from typing import Literal
from zipfile import ZipFile

from pydantic import Field

from .contracts import Contract

TABLE_FILENAMES = {
    "amp_mean_values.csv": "cycle_summary",
    "For_FEM.csv": "ordered_history",
    "half_life_history.csv": "representative_cycle",
    "output_half.csv": "experiment_summary",
}
EXPERIMENT_PATTERN = re.compile(r"^Exp_(?P<case>[123])_(?P<label>[A-Za-z0-9.]+)$")


class FabestLcfMemberAudit(Contract):
    member: str = Field(min_length=1)
    bytes: int = Field(ge=0)
    compressed_bytes: int = Field(ge=0)
    crc32: str = Field(pattern=r"^[0-9a-f]{8}$")
    encrypted: bool
    is_directory: bool


class FabestLcfTableAudit(Contract):
    experiment_id: str = Field(min_length=1)
    case_id: Literal[1, 2, 3]
    table_kind: Literal["cycle_summary", "ordered_history", "representative_cycle", "experiment_summary"]
    member: str = Field(min_length=1)
    bytes: int = Field(gt=0)
    header: tuple[str, ...] = Field(min_length=1)
    delimiter: Literal[",", ";"]
    data_rows: int = Field(ge=0)


class FabestLcfExperimentAudit(Contract):
    experiment_id: str = Field(min_length=1)
    case_id: Literal[1, 2, 3]
    control_mode: Literal["strain_controlled", "stress_controlled"]
    table_members: dict[str, str]
    protocol_member: str = Field(min_length=1)
    physical_specimen_id: None = None
    physical_specimen_identity_status: Literal["not_declared_by_archive_structure"] = (
        "not_declared_by_archive_structure"
    )


class FabestLcfArchiveAudit(Contract):
    source_id: Literal["fabest-lcf-v2"] = "fabest-lcf-v2"
    record_doi: Literal["10.5281/zenodo.21420213"] = "10.5281/zenodo.21420213"
    source_bytes: int = Field(gt=0)
    source_md5: str = Field(pattern=r"^[a-f0-9]{32}$")
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    archive_members: int = Field(gt=0)
    archive_files: int = Field(gt=0)
    archive_uncompressed_bytes: int = Field(gt=0)
    unsafe_member_paths: tuple[str, ...]
    duplicate_member_paths: tuple[str, ...]
    encrypted_members: tuple[str, ...]
    extension_counts: dict[str, int]
    members: tuple[FabestLcfMemberAudit, ...]
    calibration_experiment_count: int = Field(gt=0)
    calibration_table_count: int = Field(gt=0)
    calibration_data_rows: int = Field(gt=0)
    calibration_header_families: int = Field(gt=0)
    experiments_by_case: dict[int, int]
    tables_by_kind: dict[str, int]
    experiments: tuple[FabestLcfExperimentAudit, ...]
    tables: tuple[FabestLcfTableAudit, ...]
    blind_outcome_status: Literal["not_present_in_validation_target_folder"] = (
        "not_present_in_validation_target_folder"
    )
    provider_code_executed: Literal[False] = False


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in name


def _file_digests(path: Path) -> tuple[str, str, int]:
    md5 = hashlib.md5(usedforsecurity=False)
    sha256 = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            md5.update(chunk)
            sha256.update(chunk)
            size += len(chunk)
    return md5.hexdigest(), sha256.hexdigest(), size


def _table_header_and_rows(archive: ZipFile, member: str) -> tuple[tuple[str, ...], str, int]:
    with archive.open(member) as raw:
        first = raw.readline()
        if not first:
            raise ValueError(f"empty CSV member: {member}")
        try:
            header_text = first.decode("utf-8-sig").rstrip("\r\n")
        except UnicodeDecodeError as exc:
            raise ValueError(f"CSV header is not UTF-8: {member}") from exc
        comma_count = header_text.count(",")
        semicolon_count = header_text.count(";")
        if not comma_count and not semicolon_count:
            raise ValueError(f"CSV delimiter is unresolved: {member}")
        delimiter = ";" if semicolon_count > comma_count else ","
        header = tuple(next(csv.reader([header_text], delimiter=delimiter)))
        if not header or any(not value for value in header) or len(header) != len(set(header)):
            raise ValueError(f"CSV header requires unique nonempty columns: {member}")
        row_count = 0
        last_byte = first[-1:]
        for chunk in iter(lambda: raw.read(1024 * 1024), b""):
            row_count += chunk.count(b"\n")
            if chunk:
                last_byte = chunk[-1:]
        if last_byte not in {b"\n", b"\r"}:
            row_count += 1
    return header, delimiter, row_count


def audit_fabest_lcf_archive(path: str | Path) -> FabestLcfArchiveAudit:
    """Audit archive identity and experiment/table structure without extracting or executing files."""
    path = Path(path)
    source_md5, source_sha256, source_bytes = _file_digests(path)
    with ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        counts = Counter(names)
        duplicate_paths = tuple(sorted(name for name, count in counts.items() if count > 1))
        unsafe_paths = tuple(sorted(name for name in names if not _safe_member(name)))
        encrypted = tuple(sorted(info.filename for info in infos if info.flag_bits & 1))
        members = tuple(
            FabestLcfMemberAudit(
                member=info.filename,
                bytes=info.file_size,
                compressed_bytes=info.compress_size,
                crc32=f"{info.CRC:08x}",
                encrypted=bool(info.flag_bits & 1),
                is_directory=info.is_dir(),
            )
            for info in infos
        )
        tables = []
        experiment_parts: dict[str, dict] = {}
        for info in infos:
            parts = PurePosixPath(info.filename).parts
            if len(parts) < 4 or parts[0] != "04_Calibration_Set_Cases_1_2_3":
                continue
            experiment_id = parts[-2]
            match = EXPERIMENT_PATTERN.fullmatch(experiment_id)
            if match is None:
                continue
            case_id = int(match.group("case"))
            case_directory = parts[1]
            if not case_directory.startswith(f"Case_{case_id}_"):
                raise ValueError(f"case directory and experiment ID disagree: {info.filename}")
            record = experiment_parts.setdefault(
                experiment_id,
                {
                    "case_id": case_id,
                    "control_mode": "stress_controlled" if case_id == 3 else "strain_controlled",
                    "table_members": {},
                    "protocol_members": [],
                },
            )
            filename = parts[-1]
            if filename in TABLE_FILENAMES:
                table_kind = TABLE_FILENAMES[filename]
                if table_kind in record["table_members"]:
                    raise ValueError(f"duplicate table kind in {experiment_id}: {table_kind}")
                header, delimiter, rows = _table_header_and_rows(archive, info.filename)
                record["table_members"][table_kind] = info.filename
                tables.append(
                    FabestLcfTableAudit(
                        experiment_id=experiment_id,
                        case_id=case_id,
                        table_kind=table_kind,
                        member=info.filename,
                        bytes=info.file_size,
                        header=header,
                        delimiter=delimiter,
                        data_rows=rows,
                    )
                )
            elif filename.lower().endswith(".pdf"):
                record["protocol_members"].append(info.filename)

        expected_kinds = set(TABLE_FILENAMES.values())
        experiments = []
        for experiment_id in sorted(experiment_parts, key=lambda value: tuple(value.split("_"))):
            record = experiment_parts[experiment_id]
            if set(record["table_members"]) != expected_kinds:
                raise ValueError(f"incomplete calibration tables for {experiment_id}")
            if len(record["protocol_members"]) != 1:
                raise ValueError(f"exactly one experiment protocol required for {experiment_id}")
            experiments.append(
                FabestLcfExperimentAudit(
                    experiment_id=experiment_id,
                    case_id=record["case_id"],
                    control_mode=record["control_mode"],
                    table_members=record["table_members"],
                    protocol_member=record["protocol_members"][0],
                )
            )

        validation_files = [
            info
            for info in infos
            if info.filename.startswith("05_Validation_Targets_Cases_4_5/") and not info.is_dir()
        ]
        if any(PurePosixPath(info.filename).suffix.lower() == ".csv" for info in validation_files):
            raise ValueError("validation target folder unexpectedly contains CSV outcomes")

        return FabestLcfArchiveAudit(
            source_bytes=source_bytes,
            source_md5=source_md5,
            source_sha256=source_sha256,
            archive_members=len(infos),
            archive_files=sum(not info.is_dir() for info in infos),
            archive_uncompressed_bytes=sum(info.file_size for info in infos),
            unsafe_member_paths=unsafe_paths,
            duplicate_member_paths=duplicate_paths,
            encrypted_members=encrypted,
            extension_counts=dict(
                sorted(Counter(PurePosixPath(name).suffix.lower() or "<directory>" for name in names).items())
            ),
            members=members,
            calibration_experiment_count=len(experiments),
            calibration_table_count=len(tables),
            calibration_data_rows=sum(table.data_rows for table in tables),
            calibration_header_families=len({table.header for table in tables}),
            experiments_by_case=dict(sorted(Counter(item.case_id for item in experiments).items())),
            tables_by_kind=dict(sorted(Counter(item.table_kind for item in tables).items())),
            experiments=tuple(experiments),
            tables=tuple(sorted(tables, key=lambda item: (item.experiment_id, item.table_kind))),
        )


def iter_fabest_lcf_numeric_rows(
    path: str | Path,
    *,
    member: str,
    expected_header: tuple[str, ...],
    preserve_empty_fields: bool = False,
) -> Iterator[tuple[int, tuple[float | None, ...]]]:
    """Stream reviewed numeric fields, optionally preserving blank cells as None."""
    if not _safe_member(member):
        raise ValueError("unsafe archive member path")
    with ZipFile(path) as archive:
        matches = [info for info in archive.infolist() if info.filename == member]
        if len(matches) != 1 or matches[0].is_dir() or matches[0].flag_bits & 1:
            raise ValueError("one unencrypted file member is required")
        with archive.open(matches[0]) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as text:
            first = text.readline()
            delimiter = ";" if first.count(";") > first.count(",") else ","
            header = tuple(next(csv.reader([first.rstrip("\r\n")], delimiter=delimiter)))
            if header != expected_header:
                raise ValueError("CSV header differs from the reviewed table descriptor")
            for source_row, row in enumerate(csv.reader(text, delimiter=delimiter), 2):
                if len(row) != len(header):
                    raise ValueError(f"ragged CSV row at {member}:{source_row}")
                values_list: list[float | None] = []
                for value in row:
                    if not value.strip() and preserve_empty_fields:
                        values_list.append(None)
                        continue
                    try:
                        values_list.append(float(value))
                    except ValueError as exc:
                        raise ValueError(f"nonnumeric CSV value at {member}:{source_row}") from exc
                values = tuple(values_list)
                if not all(value is None or math.isfinite(value) for value in values):
                    raise ValueError(f"nonfinite CSV value at {member}:{source_row}")
                yield source_row, values

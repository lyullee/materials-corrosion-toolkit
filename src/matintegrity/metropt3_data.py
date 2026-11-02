"""Read a locally integrity-pinned UCI MetroPT-3 compressor process archive.

The fixed digests identify and protect the project-held copies; they are not
publisher-issued checksums or evidence that the copies were independently
compared against a provider checksum.
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

from pydantic import Field, StrictInt

from .contracts import Calculation, Contract, canonical_digest
from .registry import ModelSpec

DATASET_ID = "metropt3"
PROVIDER_RECORD = "https://doi.org/10.24432/C5VW3R"
RIGHTS_URL = "https://archive.ics.uci.edu/dataset/791/metropt+3+dataset"
LICENSE_ID = "CC-BY-4.0"
ARCHIVE_NAME = "metropt+3+dataset.zip"
ARCHIVE_BYTES = 218_381_995
ARCHIVE_SHA256 = "aab991a970e58210de853bb8078ce0e63abb4d9412fdc5c79792dae3d8e1721a"
MEMBER_NAME = "MetroPT3(AirCompressor).csv"
MEMBER_BYTES = 218_300_507
MEMBER_SHA256 = "db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24"
EXPECTED_DATA_ROWS = 1_516_948
SOURCE_ID = "uci_metropt3_process_history_reader"
HEADERS = (
    "",
    "timestamp",
    "TP2",
    "TP3",
    "H1",
    "DV_pressure",
    "Reservoirs",
    "Oil_temperature",
    "Motor_current",
    "COMP",
    "DV_eletric",
    "Towers",
    "MPG",
    "LPS",
    "Pressure_switch",
    "Oil_level",
    "Caudal_impulses",
)


class MetroPT3ArchiveAuthorization(Contract):
    """Explicit attribution and local/computational-use declaration for a reader call."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class MetroPT3ArchiveAuditRequest(Contract):
    """Audit the pinned local archive without returning or extracting its data."""

    local_archive_path: str = Field(min_length=1)
    authorization: MetroPT3ArchiveAuthorization


class MetroPT3Row(Contract):
    """One provider row with raw cells, parsed numeric channels and source lineage."""

    schema_version: Literal["matintegrity.metropt3_row.v1"] = "matintegrity.metropt3_row.v1"
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    member_path: Literal[MEMBER_NAME] = MEMBER_NAME
    member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_row_number: StrictInt = Field(ge=2)
    provider_index: StrictInt = Field(ge=0)
    timestamp_text: str = Field(min_length=1)
    raw_signal_cells: dict[str, str]
    signal_values_provider_native: dict[str, float]
    units_status: Literal["provider_native_unresolved"] = "provider_native_unresolved"
    local_only: Literal[True] = True


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_archive(path: Path) -> None:
    if path.name != ARCHIVE_NAME or path.stat().st_size != ARCHIVE_BYTES:
        raise ValueError("archive name or byte count differs from the catalogued MetroPT-3 asset")
    if _sha256_file(path) != ARCHIVE_SHA256:
        raise ValueError("MetroPT-3 archive SHA-256 differs from the catalog pin")
    try:
        with zipfile.ZipFile(path) as archive:
            members = [row for row in archive.infolist() if not row.is_dir()]
            if len(members) != 2 or MEMBER_NAME not in {row.filename for row in members}:
                raise ValueError("archive member inventory differs from the reviewed MetroPT-3 package")
            data = archive.getinfo(MEMBER_NAME)
            if data.file_size != MEMBER_BYTES:
                raise ValueError("MetroPT-3 CSV member size differs from the pinned asset")
            digest = hashlib.sha256()
            with archive.open(data) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            if digest.hexdigest() != MEMBER_SHA256:
                raise ValueError("MetroPT-3 CSV member digest differs from the reviewed pin")
    except (zipfile.BadZipFile, KeyError, RuntimeError) as exc:
        raise ValueError("local MetroPT-3 ZIP is unreadable or incomplete") from exc


def iter_metropt3_rows(
    archive_path: str | Path,
    *,
    authorization: MetroPT3ArchiveAuthorization,
) -> Iterator[MetroPT3Row]:
    """Stream provider rows from the one allowlisted local CSV; never extracts the ZIP.

    Signals retain provider-native values and labels because some units and pressure
    reference semantics need downstream, source-specific review. The dataset is
    compressor process/predictive-maintenance context data, not corrosion evidence.
    """
    if not authorization.attribution.strip():
        raise ValueError("CC BY attribution must be nonempty")
    authorization_sha256 = canonical_digest(authorization.model_dump(mode="json"))
    path = Path(archive_path)
    _verify_archive(path)
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise ValueError("local MetroPT-3 ZIP is unreadable") from exc
    with archive:
        with archive.open(MEMBER_NAME) as binary, io.TextIOWrapper(binary, encoding="utf-8", errors="strict", newline="") as text:
            reader = csv.reader(text)
            try:
                headers = tuple(next(reader))
            except StopIteration as exc:
                raise ValueError("MetroPT-3 CSV is empty") from exc
            if headers != HEADERS:
                raise ValueError("MetroPT-3 provider CSV headers differ from the pinned layout")
            previous_index = -1
            count = 0
            for provider_row_number, cells in enumerate(reader, start=2):
                if len(cells) != len(HEADERS):
                    raise ValueError(f"provider row {provider_row_number} has a different column count")
                try:
                    provider_index = int(cells[0])
                except ValueError as exc:
                    raise ValueError(f"provider row {provider_row_number} has a noninteger row index") from exc
                if provider_index <= previous_index:
                    raise ValueError("provider row index must remain strictly increasing in source order")
                previous_index = provider_index
                timestamp = cells[1]
                if not timestamp.strip():
                    raise ValueError(f"provider row {provider_row_number} has an empty timestamp")
                raw = dict(zip(HEADERS[2:], cells[2:], strict=True))
                numeric: dict[str, float] = {}
                for name, token in raw.items():
                    try:
                        value = float(token)
                    except ValueError as exc:
                        raise ValueError(f"provider row {provider_row_number} signal {name} is not numeric") from exc
                    if not math.isfinite(value):
                        raise ValueError(f"provider row {provider_row_number} signal {name} is nonfinite")
                    numeric[name] = value
                yield MetroPT3Row(
                    archive_sha256=ARCHIVE_SHA256,
                    member_sha256=MEMBER_SHA256,
                    attribution=authorization.attribution,
                    authorization_sha256=authorization_sha256,
                    provider_row_number=provider_row_number,
                    provider_index=provider_index,
                    timestamp_text=timestamp,
                    raw_signal_cells=raw,
                    signal_values_provider_native=numeric,
                )
                count += 1
            if count != EXPECTED_DATA_ROWS:
                raise ValueError(f"MetroPT-3 row count {count} differs from expected {EXPECTED_DATA_ROWS}")


def audit_metropt3_archive(request: MetroPT3ArchiveAuditRequest) -> Calculation:
    """Return pinned file/member metadata only; the local path is never echoed."""
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY attribution must be nonempty")
    path = Path(request.local_archive_path)
    _verify_archive(path)
    return Calculation(values={
        "model_id": "data.uci_metropt3_process_history",
        "dataset_id": DATASET_ID,
        "provider_record": PROVIDER_RECORD,
        "rights_url": RIGHTS_URL,
        "license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "archive_sha256": ARCHIVE_SHA256,
        "archive_bytes": ARCHIVE_BYTES,
        "member_name": MEMBER_NAME,
        "member_sha256": MEMBER_SHA256,
        "member_bytes": MEMBER_BYTES,
        "expected_data_rows": EXPECTED_DATA_ROWS,
        "request_authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "raw_data_returned": False,
        "archive_extracted": False,
        "local_path_returned": False,
        "interpretation_limit": "compressor process/predictive-maintenance context data; not corrosion or degradation evidence",
    }, notes=("This checks an allowlisted local archive and returns metadata only. Use iter_metropt3_rows for lazy row streaming.",))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="data.uci_metropt3_process_history",
        input_type=MetroPT3ArchiveAuditRequest,
        evaluator=audit_metropt3_archive,
        units={"archive_bytes": "byte", "member_bytes": "byte", "expected_data_rows": "row"},
        assumptions=("Only the exact UCI archive/member digest and local path are accepted.", "The archive audit returns no provider measurements; raw rows are available only through a separate lazy iterator.", "Provider-native units and pressure reference remain unresolved and this dataset is not corrosion evidence."),
        source_ids=(SOURCE_ID,),
        qualification="data_import",
    )]

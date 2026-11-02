"""Read pinned controlled-source acoustic-emission text exports without localizing events."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field

from .contracts import Contract

DATASET_ID = "zenodo-22011152-controlled-wire-cut-ae"
PROVIDER_RECORD = "https://doi.org/10.5281/zenodo.22011152"
LICENSE_ID = "CC-BY-4.0"

SOURCE_FILES = {
    "C_A1_S09_TR_8923.txt": "4edf5c6e92ea72c4f3c9801cdae86c4bd8853ddd80f9947af48cef7790642ae6",
    "C_A1_S10_TR_8922.txt": "7d1cf296ec0eacc6d9e280ecc876da6bc8cb615a9bf2e96601c3275d72a79522",
    "C_A1_S11_TR_8921_.txt": "52fb9bd224ec263fe29713268eae3c346538d032b319f24c7d2a265bc9597727",
    "C_A1_S12_TR_8924.txt": "54651e44769cd3a2b0f550157bddbe8f8d8028d449039d75b7ab88f8de784a62",
    "C_A2_S09_TR_40124.txt": "ab2e1c4b2b103ef840ff1dfbcda7db181a1b37c20e5102183808743f490833e8",
    "C_A2_S11_TR_40123.txt": "7d02768491c687fc9d812e7f4a53444bccde68e48cf6eb12dd3ff10c4d6dd984",
    "C_A2_S12_TR_40125.txt": "7e99c941887cecdfa7ed1a785124fd55908c090af6a80d4dd1e5952bbd72856b",
    "C_I2_S09_TR_15725.txt": "1d2c143e2b64bae1f2cf06801f76e46f2e326b19825be349cba3ff2824c8d217",
    "C_I2_S10_TR_15724.txt": "ee35e66a58e0ee945a78466672267499e8b0cc81e41d889734d07ae95024eaba",
    "C_I2_S11_TR_15723.txt": "b630afb4519463a6bb815dd26bf50283189542dd435f361f964a4cf0a9424050",
    "C_I2_S12_TR_15726.txt": "71de917785a6fb12861f74bf471cc3eb7dfd1bd8bbddbf4981fadcc3ec278c0e",
}
COORDINATES_SHA256 = "02fc1eba8f5fa75f8bf605ecba5dd2bb165de5f62cd05a7d83de57eddda39d60"
HIT_TABLE_SHA256 = "07412a57d7c2eafab2ea004f22d71da58289d5b4b8c4146a8bc21a673b23bb2d"


class AEWaveformRecord(Contract):
    schema_version: Literal["matintegrity.controlled_ae_waveform.v1"] = (
        "matintegrity.controlled_ae_waveform.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    source_filename: str = Field(min_length=1)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_label_from_filename: str = Field(pattern=r"^C_[AI][0-9]$")
    sensor_channel: int = Field(ge=1)
    trace_index_from_filename: int = Field(ge=0)
    provider_set: int = Field(ge=0)
    provider_index: int = Field(ge=0)
    provider_time_text: str = Field(min_length=1)
    sample_rate_Hz: Literal[5000000]
    pretrigger_samples: Literal[2000]
    sample_count: Literal[16384]
    amplitude_unit: Literal["mV"] = "mV"
    minimum_amplitude_mV: float
    maximum_amplitude_mV: float
    localization_use_status: Literal["raw_waveform_no_arrival_pick"] = "raw_waveform_no_arrival_pick"


class AECoordinateRecord(Contract):
    schema_version: Literal["matintegrity.controlled_ae_coordinate.v1"] = (
        "matintegrity.controlled_ae_coordinate.v1"
    )
    coordinate_kind: Literal["sensor", "provider_wire_source"]
    identifier: str = Field(min_length=1)
    x_m: float
    y_m: float
    z_m: float


class ControlledAEDatasetAudit(Contract):
    schema_version: Literal["matintegrity.controlled_ae_dataset_audit.v1"] = (
        "matintegrity.controlled_ae_dataset_audit.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    coordinates_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    hit_table_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    waveforms: tuple[AEWaveformRecord, ...] = Field(min_length=11, max_length=11)
    coordinates: tuple[AECoordinateRecord, ...] = Field(min_length=6, max_length=6)
    waveform_count: Literal[11]
    total_waveform_samples: Literal[180224]
    event_feature_row_count: Literal[87]
    event_feature_channel_counts: dict[int, int]
    waveform_source_labels: tuple[Literal["C_A1", "C_A2", "C_I2"], ...]
    coordinate_source_labels: tuple[Literal["C_A1", "C_I1"], ...]
    waveform_sources_without_coordinates: tuple[Literal["C_A2", "C_I2"], ...]
    coordinate_sources_without_waveforms: tuple[Literal["C_I1"], ...]
    incomplete_waveform_channel_group: Literal["C_A2_missing_channel_10"]
    localization_use_status: Literal["withheld_missing_arrival_picks_and_source_coordinates"] = (
        "withheld_missing_arrival_picks_and_source_coordinates"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _field(lines: list[str], prefix: str) -> str:
    matches = [line[len(prefix) :].strip() for line in lines if line.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"acoustic-emission waveform requires one {prefix!r} field")
    return matches[0]


def read_controlled_ae_waveform(
    path: str | Path,
    *,
    expected_sha256: str | None = None,
) -> tuple[np.ndarray, AEWaveformRecord]:
    """Read one reviewed text waveform while withholding arrival-time inference."""
    source = Path(path)
    pinned = expected_sha256 or SOURCE_FILES.get(source.name)
    if pinned is None:
        raise ValueError("caller must pin SHA-256 for an unlisted acoustic-emission waveform")
    actual = _sha256(source)
    if actual != pinned:
        raise ValueError("acoustic-emission waveform SHA-256 differs from the pinned digest")
    match = re.fullmatch(r"(C_[AI]\d)_S(\d{2})_TR_(\d+)_?\.txt", source.name)
    if match is None:
        raise ValueError("acoustic-emission waveform filename identity is invalid")
    lines = source.read_text(encoding="utf-8-sig", errors="strict").splitlines()
    if not lines or lines[0] != "[FILEINFO]" or "[DATA]" not in lines or lines[-1] != "[ENDDATA]":
        raise ValueError("acoustic-emission waveform layout differs")
    start = lines.index("[DATA]") + 1
    try:
        values = np.asarray([float(value) for value in lines[start:-1]], dtype=float)
    except ValueError as exc:
        raise ValueError("acoustic-emission waveform contains a nonnumeric sample") from exc
    sample_rate = int(_field(lines[:start], "SampleRate[Hz]:"))
    declared_samples = int(_field(lines[:start], "Samples:"))
    channel = int(_field(lines[:start], "Channel:"))
    if sample_rate != 5_000_000 or declared_samples != 16_384 or values.size != declared_samples:
        raise ValueError("acoustic-emission waveform sample grid differs")
    if channel != int(match.group(2)):
        raise ValueError("acoustic-emission filename and header channels differ")
    if not np.all(np.isfinite(values)):
        raise ValueError("acoustic-emission waveform samples must be finite")
    record = AEWaveformRecord(
        source_filename=source.name,
        source_file_sha256=actual,
        source_label_from_filename=match.group(1),
        sensor_channel=channel,
        trace_index_from_filename=int(match.group(3)),
        provider_set=int(_field(lines[:start], "Set:")),
        provider_index=int(_field(lines[:start], "Index:")),
        provider_time_text=_field(lines[:start], "Time:"),
        sample_rate_Hz=sample_rate,
        pretrigger_samples=int(_field(lines[:start], "PreTriggerSamples:")),
        sample_count=declared_samples,
        minimum_amplitude_mV=float(np.min(values)),
        maximum_amplitude_mV=float(np.max(values)),
    )
    return values, record


def _read_coordinates(path: Path) -> tuple[AECoordinateRecord, ...]:
    if _sha256(path) != COORDINATES_SHA256:
        raise ValueError("acoustic-emission coordinates SHA-256 differs from the pinned digest")
    records = []
    for line in path.read_text(encoding="utf-8-sig", errors="strict").splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        identifier = parts[0]
        if identifier not in {"09", "10", "11", "12", "C_A1", "C_I1"}:
            continue
        records.append(
            AECoordinateRecord(
                coordinate_kind="sensor" if identifier.isdigit() else "provider_wire_source",
                identifier=identifier,
                x_m=float(parts[1]),
                y_m=float(parts[2]),
                z_m=float(parts[3]),
            )
        )
    if len(records) != 6:
        raise ValueError("acoustic-emission coordinate inventory differs")
    return tuple(records)


def _hit_counts(path: Path) -> Counter[int]:
    if _sha256(path) != HIT_TABLE_SHA256:
        raise ValueError("acoustic-emission event table SHA-256 differs from the pinned digest")
    counts: Counter[int] = Counter()
    for line in path.read_text(encoding="utf-8-sig", errors="strict").splitlines():
        if line.lstrip().startswith("Ht"):
            parts = line.split()
            if len(parts) < 3:
                raise ValueError("acoustic-emission event feature row is truncated")
            counts[int(parts[2])] += 1
    if sum(counts.values()) != 87:
        raise ValueError("acoustic-emission event feature row count differs")
    return counts


def audit_controlled_wire_cut_ae(directory: str | Path) -> ControlledAEDatasetAudit:
    """Audit selected public text assets without creating picks or localization claims."""
    root = Path(directory)
    waveforms = []
    for filename, digest in SOURCE_FILES.items():
        _, record = read_controlled_ae_waveform(root / filename, expected_sha256=digest)
        waveforms.append(record)
    coordinates = _read_coordinates(root / "Coordinates.txt")
    hit_counts = _hit_counts(root / "Schmidt_hammer_hit.txt")
    return ControlledAEDatasetAudit(
        coordinates_file_sha256=COORDINATES_SHA256,
        hit_table_file_sha256=HIT_TABLE_SHA256,
        waveforms=tuple(waveforms),
        coordinates=coordinates,
        waveform_count=11,
        total_waveform_samples=sum(row.sample_count for row in waveforms),
        event_feature_row_count=sum(hit_counts.values()),
        event_feature_channel_counts=dict(sorted(hit_counts.items())),
        waveform_source_labels=("C_A1", "C_A2", "C_I2"),
        coordinate_source_labels=("C_A1", "C_I1"),
        waveform_sources_without_coordinates=("C_A2", "C_I2"),
        coordinate_sources_without_waveforms=("C_I1",),
        incomplete_waveform_channel_group="C_A2_missing_channel_10",
    )

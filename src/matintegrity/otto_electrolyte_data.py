"""Rights-aware reader for the TRI aqueous-electrolyte dataset.

The measurements describe fixed-current electrochemical stability screening
on platinum. They are not corrosion-polarization curves and are never adapted
to the corrosion calculators by this reader.
"""

from __future__ import annotations

import hashlib
import json
import math
import zipfile
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator

from .contracts import Contract, Evidence, canonical_digest

DATASET_ID = "matr-aqueous-electrolytes"
DATASET_DOI = "10.1016/j.xcrp.2020.100264"
DATASET_URL = "https://data.matr.io/5/"
DATASET_LICENSE = "CC-BY-4.0"
DATASET_ATTRIBUTION = (
    "Dave et al. (2020), Autonomous Discovery of Battery Electrolytes with Robotic "
    "Experimentation and Machine Learning, Cell Reports Physical Science 1, 100264; "
    "dataset: TRI Energy & Materials Data, Aqueous electrolytes, https://data.matr.io/5/"
)
PINNED_ARCHIVE_BYTES = 1_252_996
PINNED_ARCHIVE_SHA256 = "4fd633243504316d48b5e42482e5b870a21f3a551010833abae4dc2762184744"
PINNED_JSON_MEMBER = "otto_data/otto_aqueous.json"
PINNED_JSON_MEMBER_BYTES = 5_547_706
PINNED_JSON_MEMBER_SHA256 = "7cd0b865cfdec2c10a048e6f16b50d2a0c5232db388645e5e215b062ce275adf"
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_JSON_MEMBER_BYTES = 12 * 1024 * 1024


class OttoElectrolyteObservation(Contract):
    """One source record, preserving provider-native values and test semantics."""

    schema_version: Literal["matintegrity.otto_electrolyte_observation.v1"] = (
        "matintegrity.otto_electrolyte_observation.v1"
    )
    dataset_id: Literal["matr-aqueous-electrolytes"] = DATASET_ID
    dataset_license: Literal["CC-BY-4.0"] = DATASET_LICENSE
    attribution: Literal[DATASET_ATTRIBUTION] = DATASET_ATTRIBUTION
    source_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_json_member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    normalized_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_id: str = Field(min_length=1)
    source_run_id: str = Field(min_length=1)
    run_type_as_reported: str = Field(min_length=1)
    timestamp_as_reported: str = Field(min_length=1)
    test_protocol_as_reported: str = Field(min_length=1)
    temperature_reported_value: float
    temperature_unit: str = "not encoded in JSON; caller review required"
    conductivity_reported_value: float
    conductivity_unit: str = "not encoded in JSON; caller review required"
    pH_reported_value: float
    feeder_volume_mL: dict[str, float]
    feeder_source_molality_as_reported: dict[str, float]
    feeder_source_density_as_reported: dict[str, float]
    time_s: list[float] = Field(min_length=2, max_length=2000)
    potential_V_as_reported: list[float] = Field(min_length=2, max_length=2000)
    signed_current_density_mA_cm2: list[float] = Field(min_length=2, max_length=2000)
    potential_reference_electrode: Literal["Ag/AgCl"] = "Ag/AgCl"
    working_counter_material: Literal["platinum"] = "platinum"
    reported_stability_metrics_V: dict[str, float]
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_native_trace(self):
        if len({len(self.time_s), len(self.potential_V_as_reported), len(self.signed_current_density_mA_cm2)}) != 1:
            raise ValueError("provider time, potential and current-density arrays must align")
        if any(right <= left for left, right in zip(self.time_s, self.time_s[1:], strict=False)):
            raise ValueError("provider elapsed-time samples must strictly increase")
        numeric = (
            self.temperature_reported_value,
            self.conductivity_reported_value,
            self.pH_reported_value,
            *self.time_s,
            *self.potential_V_as_reported,
            *self.signed_current_density_mA_cm2,
            *self.feeder_volume_mL.values(),
            *self.feeder_source_molality_as_reported.values(),
            *self.feeder_source_density_as_reported.values(),
            *self.reported_stability_metrics_V.values(),
        )
        if any(not math.isfinite(value) for value in numeric):
            raise ValueError("provider record contains a nonfinite numeric value")
        return self


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _finite_float(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a provider-supplied numeric value")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _numeric_mapping(value: Any, field: str) -> dict[str, float]:
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{field} must be a nonempty provider mapping")
    return {str(key): _finite_float(item, field) for key, item in value.items()}


def _evidence(archive_sha256: str) -> tuple[Evidence, ...]:
    return (Evidence(
        source_id=DATASET_ID,
        origin="open_dataset",
        citation=DATASET_ATTRIBUTION,
        license_id=DATASET_LICENSE,
        sha256=archive_sha256,
    ),)


def read_otto_electrolyte_archive(
    archive_path: str | Path,
    *,
    expected_archive_sha256: str = PINNED_ARCHIVE_SHA256,
    maximum_records: int = 1000,
) -> tuple[OttoElectrolyteObservation, ...]:
    """Read the pinned provider JSON member without extracting archive contents.

    The default digest pins this locally observed archive snapshot. The
    provider page does not publish a cryptographic checksum; this digest is not
    represented as a provider checksum.
    """
    path = Path(archive_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    size = path.stat().st_size
    if size <= 0 or size > MAX_ARCHIVE_BYTES:
        raise ValueError("dataset archive exceeds the bounded reader size")
    if isinstance(maximum_records, bool) or not isinstance(maximum_records, int) or maximum_records < 1 or maximum_records > 100_000:
        raise ValueError("maximum_records must be an integer from 1 through 100000")
    archive_digest = _sha256_file(path)
    if archive_digest != expected_archive_sha256:
        raise ValueError("dataset archive digest differs from the caller-pinned snapshot")

    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if archive.testzip() is not None:
            raise ValueError("dataset archive CRC check failed")
        if any(info.file_size > MAX_JSON_MEMBER_BYTES for info in infos):
            raise ValueError("dataset archive member exceeds the bounded reader size")
        try:
            info = archive.getinfo(PINNED_JSON_MEMBER)
        except KeyError as exc:
            raise ValueError("provider JSON member is missing; archive version changed") from exc
        if info.file_size != PINNED_JSON_MEMBER_BYTES:
            raise ValueError("provider JSON member size differs from the reviewed snapshot")
        json_bytes = archive.read(info)
    member_digest = hashlib.sha256(json_bytes).hexdigest()
    if member_digest != PINNED_JSON_MEMBER_SHA256:
        raise ValueError("provider JSON member digest differs from the reviewed snapshot")
    payload = json.loads(json_bytes)
    if not isinstance(payload, list) or not 1 <= len(payload) <= maximum_records:
        raise ValueError("provider record list is empty or exceeds the declared record budget")

    evidence = _evidence(archive_digest)
    records: list[OttoElectrolyteObservation] = []
    seen: set[str] = set()
    for row in payload:
        if not isinstance(row, dict):
            raise ValueError("provider dataset rows must be JSON objects")
        record_id = str(row.get("GUID", ""))
        if not record_id or record_id in seen:
            raise ValueError("provider GUID is empty or duplicated")
        seen.add(record_id)
        electrochemistry = row.get("electrochemistry")
        electrolyte = row.get("electrolyte")
        if not isinstance(electrochemistry, dict) or not isinstance(electrolyte, dict):
            raise ValueError(f"provider record {record_id} has missing electrochemistry/composition objects")
        derived = _numeric_mapping(electrochemistry.get("derived_quantities"), "derived_quantities")
        source = {
            "GUID": row.get("GUID"),
            "RUN_ID": row.get("RUN_ID"),
            "RUN_TYPE": row.get("RUN_TYPE"),
            "timestamp": row.get("timestamp"),
            "temperature": row.get("temperature"),
            "conductivity": row.get("conductivity"),
            "pH": row.get("pH"),
            "electrolyte": electrolyte,
            "electrochemistry": electrochemistry,
        }
        arrays = {
            "time_s": [_finite_float(value, "electrochemistry.t") for value in electrochemistry.get("t", [])],
            "potential_V_as_reported": [_finite_float(value, "electrochemistry.V") for value in electrochemistry.get("V", [])],
            "signed_current_density_mA_cm2": [_finite_float(value, "electrochemistry.i") for value in electrochemistry.get("i", [])],
        }
        record = OttoElectrolyteObservation(
            source_archive_sha256=archive_digest,
            source_json_member_sha256=member_digest,
            normalized_record_sha256=canonical_digest(source),
            record_id=record_id,
            source_run_id=str(row.get("RUN_ID", "")),
            run_type_as_reported=str(row.get("RUN_TYPE", "")),
            timestamp_as_reported=str(row.get("timestamp", "")),
            test_protocol_as_reported=str(electrochemistry.get("test_name", "")),
            temperature_reported_value=_finite_float(row.get("temperature"), "temperature"),
            conductivity_reported_value=_finite_float(row.get("conductivity"), "conductivity"),
            pH_reported_value=_finite_float(row.get("pH"), "pH"),
            feeder_volume_mL=_numeric_mapping(electrolyte.get("volumes"), "electrolyte.volumes"),
            feeder_source_molality_as_reported=_numeric_mapping(electrolyte.get("source molalities"), "electrolyte.source molalities"),
            feeder_source_density_as_reported=_numeric_mapping(electrolyte.get("source densities"), "electrolyte.source densities"),
            reported_stability_metrics_V=derived,
            **arrays,
            evidence=evidence,
        )
        records.append(record)
    return tuple(records)

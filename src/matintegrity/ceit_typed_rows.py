"""Typed, digest-pinned local observation rows for the CEIT field JSON reader."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import Field, StrictInt

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec
from .ultrasound_data import read_ceit_uniform_corrosion_field

DATASET_ID = "ceit-uniform-corrosion-field"
DATASET_DOI = "10.5281/zenodo.13897090"
LICENSE_ID = "CC-BY-4.0"
SOURCE_ID = "zenodo_ceit_uniform_corrosion_field_typed_rows"
MODEL_ID = "data.zenodo_ceit_uniform_corrosion_field_typed_rows"
SOURCE_FILENAME = "UniformCorrosionExperiment_Ceit.json"
SOURCE_MD5 = "6db405ab03922aeaf5560ed634cd94df"
SOURCE_SHA256 = "87033b35f7964eb34265e6e4e5f0e1252b2214480b6f39871029811e3e3dbf1b"
SOURCE_BYTES = 49_918_087


class CeitFieldReadAuthorization(Contract):
    """Caller attribution and local-only computational-use declaration."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class CeitFieldObservationRow(Contract):
    """One provider observation record with per-row and source-file provenance."""

    schema_version: Literal["matintegrity.zenodo_ceit_field_observation_row.v1"] = (
        "matintegrity.zenodo_ceit_field_observation_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_filename: Literal[SOURCE_FILENAME] = SOURCE_FILENAME
    source_file_bytes: StrictInt = Field(gt=0)
    source_file_md5: str = Field(pattern=r"^[a-f0-9]{32}$")
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    series_id: str = Field(min_length=1)
    source_order: StrictInt = Field(ge=0)
    provider_array_index: StrictInt = Field(ge=0)
    timestamp: datetime
    timestamp_basis: Literal["provider_naive_calendar_time_timezone_unresolved"] = (
        "provider_naive_calendar_time_timezone_unresolved"
    )
    node_id: str
    sample_id: str
    piezo_id: str
    reported_frequency_code: Any
    reported_pwm: Any
    reported_echo_index: Any
    reported_tof_reference: Any
    reported_tof: float
    reported_temperature: float
    reported_battery: Any
    reported_amplitude: Any
    reported_tof_unit: Literal["ns", "s"] | None
    tof_s: float | None
    reported_temperature_unit: Literal["degC", "K"] | None
    ambient_temperature_K: float | None
    sample_interval_s: float | None
    sample_time_s: tuple[float, ...] | None
    raw_signal: tuple[float, ...]
    filtered_signal: tuple[float, ...]
    correlation_signal: tuple[float, ...]
    envelope_signal: tuple[float, ...]
    signal_units: Literal["provider_adc_and_processed_scales_unresolved"] = (
        "provider_adc_and_processed_scales_unresolved"
    )
    raw_adc_rail_count: StrictInt = Field(ge=0)
    observation_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    wall_thickness_inferred: Literal[False] = False
    corrosion_rate_inferred: Literal[False] = False
    remaining_life_inferred: Literal[False] = False
    failure_probability_inferred: Literal[False] = False


class CeitFieldArchiveAuditRequest(Contract):
    local_json_path: str = Field(min_length=1)
    series_id: str = Field(min_length=1)
    reported_tof_unit: Literal["ns", "s"] | None = None
    reported_temperature_unit: Literal["degC", "K"] | None = None
    sample_interval_s: float | None = None
    authorization: CeitFieldReadAuthorization


def _verify_source(path: Path) -> tuple[str, str, int]:
    if path.name != SOURCE_FILENAME or not path.is_file():
        raise ValueError("only the catalogued local CEIT JSON source is accepted")
    size = path.stat().st_size
    if size != SOURCE_BYTES:
        raise ValueError("CEIT source byte count differs from the catalog pin")
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(block)
            sha256.update(block)
    actual_md5, actual_sha256 = md5.hexdigest(), sha256.hexdigest()
    if actual_md5 != SOURCE_MD5 or actual_sha256 != SOURCE_SHA256:
        raise ValueError("CEIT source digest differs from the catalogued acquisition pins")
    return actual_md5, actual_sha256, size


def iter_ceit_field_observation_rows(
    path: str | Path,
    *,
    series_id: str,
    authorization: CeitFieldReadAuthorization,
    reported_tof_unit: Literal["ns", "s"] | None = None,
    reported_temperature_unit: Literal["degC", "K"] | None = None,
    sample_interval_s: float | None = None,
) -> Iterator[CeitFieldObservationRow]:
    """Yield typed source observations in JSON array order using the established parser."""
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    source = Path(path)
    actual_md5, actual_sha256, size = _verify_source(source)
    parsed = read_ceit_uniform_corrosion_field(
        source,
        series_id=series_id,
        reported_tof_unit=reported_tof_unit,
        reported_temperature_unit=reported_temperature_unit,
        sample_interval_s=sample_interval_s,
    )
    auth_sha256 = canonical_digest(authorization.model_dump(mode="json"))
    for order, observation in enumerate(parsed["observations"]):
        signals = {
            name: tuple(float(value) for value in np.asarray(observation[name], dtype=float))
            for name in ("raw_signal", "filtered_signal", "correlation_signal", "envelope_signal")
        }
        sample_time = observation["sample_time_s"]
        sample_time_values = None if sample_time is None else tuple(float(value) for value in sample_time)
        values = {
            "series_id": series_id,
            "source_order": order,
            "provider_array_index": order,
            "timestamp": observation["timestamp"],
            "node_id": observation["node_id"],
            "sample_id": observation["sample_id"],
            "piezo_id": observation["piezo_id"],
            "reported_frequency_code": observation["reported_frequency_code"],
            "reported_pwm": observation["reported_pwm"],
            "reported_echo_index": observation["reported_echo_index"],
            "reported_tof_reference": observation["reported_tof_reference"],
            "reported_tof": observation["tof_reported"],
            "reported_temperature": observation["reported_temperature"],
            "reported_battery": observation["reported_battery"],
            "reported_amplitude": observation["reported_amplitude"],
            "reported_tof_unit": reported_tof_unit,
            "tof_s": observation["tof_s"],
            "reported_temperature_unit": reported_temperature_unit,
            "ambient_temperature_K": observation["ambient_temperature_K"],
            "sample_interval_s": sample_interval_s,
            "sample_time_s": sample_time_values,
            **signals,
            "raw_adc_rail_count": observation["raw_adc_rail_count"],
        }
        yield CeitFieldObservationRow(
            attribution=authorization.attribution,
            authorization_sha256=auth_sha256,
            source_file_bytes=size,
            source_file_md5=actual_md5,
            source_file_sha256=actual_sha256,
            **values,
            observation_row_sha256=canonical_digest({
                "dataset_id": DATASET_ID,
                "source_file_sha256": actual_sha256,
                "source_order": order,
                "observation": values | {"timestamp": observation["timestamp"].isoformat()},
            }),
            evidence=Evidence(
                source_id=DATASET_ID,
                origin="open_dataset",
                citation=f"{authorization.attribution}; https://doi.org/{DATASET_DOI}",
                license_id=LICENSE_ID,
                sha256=actual_sha256,
            ),
        )


def audit_ceit_field_archive(request: CeitFieldArchiveAuditRequest) -> Calculation:
    """Return metadata-only source and observation counts; omit local path and point values."""
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    source = Path(request.local_json_path)
    actual_md5, actual_sha256, size = _verify_source(source)
    parsed = read_ceit_uniform_corrosion_field(
        source,
        series_id=request.series_id,
        reported_tof_unit=request.reported_tof_unit,
        reported_temperature_unit=request.reported_temperature_unit,
        sample_interval_s=request.sample_interval_s,
    )
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "source_filename": SOURCE_FILENAME,
        "source_file_bytes": size,
        "source_file_md5": actual_md5,
        "source_file_sha256": actual_sha256,
        "series_id": request.series_id,
        "observation_count": len(parsed["observations"]),
        "source_order_preserved": True,
        "timestamp_basis": parsed["timestamp_basis"],
        "reported_tof_unit": request.reported_tof_unit,
        "reported_temperature_unit": request.reported_temperature_unit,
        "sample_interval_s": request.sample_interval_s,
        "sample_values_returned": False,
        "local_path_returned": False,
        "local_only": True,
        "thickness_computed": False,
        "corrosion_rate_computed": False,
    }, notes=(
        "Metadata-only audit; use iter_ceit_field_observation_rows for local point-level records.",
        "Device ToF and signal channels are not converted to wall thickness or corrosion loss without an independently reviewed path, wave speed, calibration and spatial basis.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CeitFieldArchiveAuditRequest,
        evaluator=audit_ceit_field_archive,
        units={"source_file_bytes": "byte", "observation_count": "row", "sample_interval_s": "s"},
        assumptions=(
            "Only the catalogued CEIT JSON filename, byte count, MD5 and acquisition SHA-256 are accepted before invoking the existing parser.",
            "Caller supplies attribution and computational/local-only authorization; every typed row retains source Evidence and authorization digest.",
            "JSON array order and unresolved provider signal units are preserved; ToF, temperature and sample-clock conversions require explicit caller units.",
            "No thickness, wall loss, corrosion rate, uncertainty, acceptance, remaining life or probability is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="data_import",
    )]

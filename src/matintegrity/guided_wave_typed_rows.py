"""Typed, provenance-pinned rows over the existing pipeline guided-wave reader."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .guided_wave_data import (
    GUIDED_WAVE_ARCHIVE_SHA256,
    read_guided_wave_acquisition,
)
from .registry import ModelSpec

DATASET_ID = "guided-wave-pipeline-shm"
DATASET_DOI = "10.17632/ttb63krg6d.1"
LICENSE_ID = "CC-BY-4.0"
SOURCE_ID = "mendeley_guided_wave_typed_sample_rows"
MODEL_ID = "data.mendeley_guided_wave_typed_sample_rows"
ARCHIVE_FILENAME = "ttb63krg6d-1.zip"
ARCHIVE_BYTES = 103_000_407
FREQUENCIES_HZ = (14_000.0, 18_000.0, 24_000.0, 30_000.0, 37_000.0)


class GuidedWaveReadAuthorization(Contract):
    """Caller attribution and local-only computational-use declaration."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class GuidedWaveSampleRow(Contract):
    """One signal-axis sample retaining acquisition, workbook, sheet, and row identity."""

    schema_version: Literal["matintegrity.guided_wave_sample_row.v1"] = (
        "matintegrity.guided_wave_sample_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    outer_archive_filename: Literal[ARCHIVE_FILENAME] = ARCHIVE_FILENAME
    outer_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    outer_archive_bytes: StrictInt = Field(gt=0)
    nested_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    acquisition_id: StrictInt = Field(ge=0)
    specimen_id: str = Field(min_length=1)
    workbook_member_path: str = Field(min_length=1)
    workbook_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_sheet_name: str = Field(min_length=1)
    source_sheet_index: StrictInt = Field(ge=0)
    sample_row_order: StrictInt = Field(ge=0)
    provider_source_row: StrictInt = Field(ge=3)
    excitation_frequency_Hz: Literal[14_000.0, 18_000.0, 24_000.0, 30_000.0, 37_000.0]
    excitation_cycles: float = Field(gt=0)
    raw_window_label: str = Field(min_length=1)
    distance_m: float
    torsional_voltage_V: float
    flexural_voltage_V: float
    provider_pure_dac_voltage_V: float
    machining_step_id: None = None
    timestamp: None = None
    temperature_K: None = None
    sample_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    wall_loss_inferred: Literal[False] = False
    corrosion_rate_inferred: Literal[False] = False
    defect_dimension_inferred: Literal[False] = False
    probability_of_detection_inferred: Literal[False] = False


class GuidedWaveArchiveAuditRequest(Contract):
    local_archive_path: str = Field(min_length=1)
    acquisition_id: StrictInt = Field(ge=0)
    specimen_id: str = Field(min_length=1)
    excitation_frequency_Hz: Literal[14_000.0, 18_000.0, 24_000.0, 30_000.0, 37_000.0]
    authorization: GuidedWaveReadAuthorization


def iter_guided_wave_sample_rows(
    path: str | Path,
    *,
    acquisition_id: int,
    specimen_id: str,
    excitation_frequency_Hz: float,
    authorization: GuidedWaveReadAuthorization,
) -> Iterator[GuidedWaveSampleRow]:
    """Yield one selected workbook sheet in provider row order; preserve duplicate distances."""
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    if excitation_frequency_Hz not in FREQUENCIES_HZ:
        raise ValueError("frequency must match one of the five reviewed source excitations")
    source = Path(path)
    record = read_guided_wave_acquisition(
        source,
        acquisition_id,
        specimen_id=specimen_id,
        require_pinned_hash=True,
        expected_archive_sha256=GUIDED_WAVE_ARCHIVE_SHA256,
        article_state_review=True,
    )
    signal_rows = [row for row in record["signals"] if row["frequency_Hz"] == excitation_frequency_Hz]
    if len(signal_rows) != 1:
        raise ValueError("selected frequency must occur exactly once in the acquisition")
    signal = signal_rows[0]
    authorization_sha256 = canonical_digest(authorization.model_dump(mode="json"))
    outer_sha256 = str(record["outer_archive_sha256"])
    nested_sha256 = str(record["nested_archive_sha256"])
    workbook_sha256 = str(record["workbook_sha256"])
    for order, (distance, torsional, flexural, dac) in enumerate(zip(
        signal["distance_m"],
        signal["torsional_V"],
        signal["flexural_V"],
        signal["provider_pure_dac_V"],
        strict=True,
    )):
        values = {
            "distance_m": float(distance),
            "torsional_voltage_V": float(torsional),
            "flexural_voltage_V": float(flexural),
            "provider_pure_dac_voltage_V": float(dac),
        }
        lineage = {
            "dataset_id": DATASET_ID,
            "outer_archive_sha256": outer_sha256,
            "nested_archive_sha256": nested_sha256,
            "workbook_member_path": record["member_path"],
            "workbook_sha256": workbook_sha256,
            "acquisition_id": acquisition_id,
            "specimen_id": specimen_id,
            "source_sheet_name": signal["source_sheet_name"],
            "source_sheet_index": signal["source_sheet_index"],
            "sample_row_order": order,
            "provider_source_row": order + 3,
            "excitation_frequency_Hz": excitation_frequency_Hz,
            "values": values,
        }
        yield GuidedWaveSampleRow(
            attribution=authorization.attribution,
            authorization_sha256=authorization_sha256,
            outer_archive_sha256=outer_sha256,
            outer_archive_bytes=source.stat().st_size,
            nested_archive_sha256=nested_sha256,
            acquisition_id=acquisition_id,
            specimen_id=specimen_id,
            workbook_member_path=record["member_path"],
            workbook_sha256=workbook_sha256,
            source_sheet_name=signal["source_sheet_name"],
            source_sheet_index=int(signal["source_sheet_index"]),
            sample_row_order=order,
            provider_source_row=order + 3,
            excitation_frequency_Hz=excitation_frequency_Hz,
            excitation_cycles=float(signal["excitation_cycles"]),
            raw_window_label=str(signal["raw_window_label"]),
            **values,
            sample_row_sha256=canonical_digest(lineage),
            evidence=Evidence(
                source_id=DATASET_ID,
                origin="open_dataset",
                citation=f"{authorization.attribution}; https://doi.org/{DATASET_DOI}",
                license_id=LICENSE_ID,
                sha256=outer_sha256,
            ),
        )


def audit_guided_wave_acquisition(request: GuidedWaveArchiveAuditRequest) -> Calculation:
    """Return pinned acquisition/sheet metadata and counts without point values."""
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    source = Path(request.local_archive_path)
    record = read_guided_wave_acquisition(
        source,
        request.acquisition_id,
        specimen_id=request.specimen_id,
        require_pinned_hash=True,
        expected_archive_sha256=GUIDED_WAVE_ARCHIVE_SHA256,
        article_state_review=True,
    )
    matches = [row for row in record["signals"] if row["frequency_Hz"] == request.excitation_frequency_Hz]
    if len(matches) != 1:
        raise ValueError("selected frequency must occur exactly once in the acquisition")
    signal = matches[0]
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "outer_archive_filename": ARCHIVE_FILENAME,
        "outer_archive_sha256": record["outer_archive_sha256"],
        "outer_archive_bytes": source.stat().st_size,
        "nested_archive_sha256": record["nested_archive_sha256"],
        "acquisition_id": record["acquisition_id"],
        "specimen_id": record["specimen_id"],
        "workbook_member_path": record["member_path"],
        "workbook_sha256": record["workbook_sha256"],
        "source_sheet_name": signal["source_sheet_name"],
        "source_sheet_index": signal["source_sheet_index"],
        "excitation_frequency_Hz": request.excitation_frequency_Hz,
        "excitation_cycles": signal["excitation_cycles"],
        "sample_count": signal["numeric_sample_rows"],
        "distance_axis_order": signal["distance_axis_order"],
        "repeated_distance_intervals": signal["repeated_distance_intervals"],
        "point_values_returned": False,
        "local_path_returned": False,
        "local_only": True,
        "machining_step_id": None,
        "timestamp": None,
        "temperature_K": None,
        "wall_loss_inferred": False,
        "corrosion_rate_inferred": False,
    }, notes=(
        "Metadata-only audit; use iter_guided_wave_sample_rows for selected local point access.",
        "The provider DAC column and voltage responses are preserved as signal fields, not direct wall thickness or corrosion measurements.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=GuidedWaveArchiveAuditRequest,
        evaluator=audit_guided_wave_acquisition,
        units={"outer_archive_bytes": "byte", "sample_count": "row", "excitation_frequency_Hz": "Hz"},
        assumptions=(
            "Only the catalogued outer archive SHA-256 and byte count are accepted; the existing bounded nested-archive parser is reused.",
            "Caller supplies attribution and computational/local-only authorization; each row retains authorization and archive evidence digests.",
            "One acquisition and source frequency are selected explicitly; workbook point order and repeated distances are preserved.",
            "Damage-step identity, timestamps, temperature, direct wall thickness, corrosion progression, POD and qualification are not inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="data_import",
    )]

"""Typed, digest-preserving local row view over the existing COQTEL parser."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec
from .signals import COQTEL_ARTICLE_DOI, COQTEL_DATASET_ID, coqtel_electrochemistry

DATASET_ID = "coqtel"
LICENSE_ID = "CC-BY-4.0"
SOURCE_ID = "coqtel_dataset_reader"
MODEL_ID = "data.coqtel_typed_electrochemistry_rows"


class CoqtelReadAuthorization(Contract):
    """Caller attribution and local-use declaration for row-level access."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    article_doi: Literal["10.1016/j.dib.2025.111393"] = COQTEL_ARTICLE_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class CoqtelElectrochemistryRow(Contract):
    """One original EC series row with source order and file/row provenance."""

    schema_version: Literal["matintegrity.coqtel_electrochemistry_row.v1"] = (
        "matintegrity.coqtel_electrochemistry_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    article_doi: Literal["10.1016/j.dib.2025.111393"] = COQTEL_ARTICLE_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_filename: str = Field(min_length=1)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_order: StrictInt = Field(ge=0)
    provider_source_row: StrictInt = Field(ge=1)
    state_index: StrictInt = Field(ge=1)
    experiment_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    time_s: float
    current_A: float
    potential_V: float
    duplicate_timestamp_from_previous_row: bool
    anomaly: Literal["none_reported", "reported_air_bubble_interval"]
    pit_dimension_per_state: None = None
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    corrosion_rate_inferred: Literal[False] = False
    wall_loss_inferred: Literal[False] = False
    failure_probability_inferred: Literal[False] = False


class CoqtelArchiveAuditRequest(Contract):
    local_hdf5_path: str = Field(min_length=1)
    authorization: CoqtelReadAuthorization


def iter_coqtel_electrochemistry_rows(
    path: str | Path,
    *,
    authorization: CoqtelReadAuthorization,
) -> Iterator[CoqtelElectrochemistryRow]:
    """Yield local electrochemistry rows in HDF5 source order without sorting or imputation.

    The established reader verifies the pinned archive digest by default and explicitly
    preserves identical repeated terminal timestamps when the caller selects that policy.
    """
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    source = Path(path)
    result = coqtel_electrochemistry(
        source,
        duplicate_policy="preserve_identical",
        require_pinned_hash=True,
    )
    auth_digest = canonical_digest(authorization.model_dump(mode="json"))
    repeated = {right for _, right in result["repeated_time_state_pairs"]}
    for order, (state, time_s, current_A, potential_V, anomaly) in enumerate(zip(
        result["state_index"],
        result["time_s"],
        result["current_A"],
        result["potential_V"],
        result["experimental_anomaly"],
        strict=True,
    )):
        row_identity = {
            "dataset_id": result["dataset_id"],
            "source_filename": source.name,
            "source_file_sha256": result["source_sha256"],
            "source_order": order,
            "provider_source_row": int(state),
            "time_s": float(time_s),
            "current_A": float(current_A),
            "potential_V": float(potential_V),
            "anomaly": str(anomaly),
        }
        yield CoqtelElectrochemistryRow(
            attribution=authorization.attribution,
            authorization_sha256=auth_digest,
            source_filename=source.name,
            source_file_sha256=result["source_sha256"],
            source_order=order,
            provider_source_row=int(state),
            state_index=int(state),
            experiment_id=result["experiment_id"],
            specimen_id=result["specimen_id"],
            time_s=float(time_s),
            current_A=float(current_A),
            potential_V=float(potential_V),
            duplicate_timestamp_from_previous_row=int(state) in repeated,
            anomaly=str(anomaly),
            source_row_sha256=canonical_digest(row_identity),
            evidence=Evidence(
                source_id=DATASET_ID,
                origin="open_dataset",
                citation=f"{authorization.attribution}; https://doi.org/{COQTEL_ARTICLE_DOI}",
                license_id=LICENSE_ID,
                sha256=result["source_sha256"],
            ),
        )


def audit_coqtel_archive(request: CoqtelArchiveAuditRequest) -> Calculation:
    """Return pinned archive and row-count metadata without paths or point values."""
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    source = Path(request.local_hdf5_path)
    result = coqtel_electrochemistry(
        source,
        duplicate_policy="preserve_identical",
        require_pinned_hash=True,
    )
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "article_doi": COQTEL_ARTICLE_DOI,
        "license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "source_filename": source.name,
        "source_file_sha256": result["source_sha256"],
        "source_file_bytes": source.stat().st_size,
        "experiment_id": result["experiment_id"],
        "specimen_id": result["specimen_id"],
        "row_count": int(len(result["state_index"])),
        "identical_repeated_time_interval_count": result["identical_duplicate_intervals"],
        "state_order_matches_source_order": True,
        "point_values_returned": False,
        "local_path_returned": False,
        "local_only": True,
        "pit_dimension_observations_per_state": 0,
        "corrosion_rate_inferred": False,
    }, notes=(
        "Metadata-only archive audit; use iter_coqtel_electrochemistry_rows for attributed local row access.",
        "Current, potential, charge and waveform changes are not relabelled as pit size, wall loss, corrosion rate or failure probability.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CoqtelArchiveAuditRequest,
        evaluator=audit_coqtel_archive,
        units={"source_file_bytes": "byte", "row_count": "row", "identical_repeated_time_interval_count": "interval"},
        assumptions=(
            "Only the two checksum-pinned COQTEL HDF5 assets are accepted through the existing source reader.",
            "Caller supplies attribution and confirms computational use within a local-only boundary; row lineage retains the authorization digest.",
            "Original order and identical repeated timestamps are preserved; no missing pit dimensions, corrosion metrics or performance are inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="data_import",
    )]

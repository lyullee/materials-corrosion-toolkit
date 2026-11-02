"""Rights-aware typed row view over the existing galvanized-polarization reader."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt

from .contracts import Calculation, Contract, canonical_digest
from .data import read_galvanized_polarization
from .registry import ModelSpec

DATASET_ID = "galvanized-polarization"
PROVIDER_RECORD = "https://doi.org/10.5281/zenodo.13886478"
LICENSE_ID = "CC-BY-4.0"
SOURCE_ID = "zenodo_galvanized_polarization_typed_rows"

# Provider MD5 and byte counts are the catalogued Zenodo asset identifiers.
# SHA-256 below is additionally calculated for row-level local lineage.
ASSETS = {
    "metals-3156094_potentiodynamic_polarization_HCl_data.xlsx": ("b6b314cc923aed381ac5dc5d06b7ac00", 97_931),
    "metals-3156094_potentiodynamic_polarization_H2SO4_data.xlsx": ("fb36966daeba2c6dc4ee76f22658db9b", 98_400),
    "metals-3156094_potentiodynamic_polarization_NaCl_data.xlsx": ("735fe2203dc995219334d6776f2455b3", 102_557),
}


class GalvanizedPolarizationReadAuthorization(Contract):
    """Attribution and local computational-use declaration for this row view."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class GalvanizedPolarizationArchiveAuditRequest(Contract):
    local_workbook_path: str = Field(min_length=1)
    authorization: GalvanizedPolarizationReadAuthorization


class GalvanizedPolarizationSample(Contract):
    """One signed polarization observation with file, source-row and authorization lineage."""

    schema_version: Literal["matintegrity.galvanized_polarization_sample.v1"] = (
        "matintegrity.galvanized_polarization_sample.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_filename: str = Field(min_length=1)
    source_file_md5: str = Field(pattern=r"^[a-f0-9]{32}$")
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_source_row: StrictInt = Field(ge=3)
    sample_index: StrictInt = Field(ge=0)
    specimen_id: str = Field(min_length=1)
    electrolyte_id: str = Field(min_length=1)
    potential_V_provider_reported_reference_unresolved: float
    current_density_provider_A_cm2: float
    signed_current_density_A_m2: float
    provider_current_conversion: Literal["A_cm-2_to_A_m-2_factor_10000"] = (
        "A_cm-2_to_A_m-2_factor_10000"
    )
    tafel_extrapolation_performed: Literal[False] = False
    corrosion_rate_inferred: Literal[False] = False


def _asset_identity(path: Path) -> tuple[str, int, str]:
    entry = ASSETS.get(path.name)
    if entry is None:
        raise ValueError("workbook filename is not one of the catalogued polarization assets")
    expected_md5, expected_bytes = entry
    if not path.is_file() or path.stat().st_size != expected_bytes:
        raise ValueError("local workbook size differs from the catalogued asset")
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(block)
            sha256.update(block)
    actual_md5 = md5.hexdigest()
    if actual_md5 != expected_md5:
        raise ValueError("local workbook MD5 differs from the catalogued Zenodo asset")
    return actual_md5, expected_bytes, sha256.hexdigest()


def iter_galvanized_polarization_samples(
    path: str | Path,
    *,
    authorization: GalvanizedPolarizationReadAuthorization,
) -> Iterator[GalvanizedPolarizationSample]:
    """Yield the existing parser's observations in source sheet/row/specimen order."""
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    source = Path(path)
    md5, _, sha256 = _asset_identity(source)
    authorization_sha256 = canonical_digest(authorization.model_dump(mode="json"))
    frame = read_galvanized_polarization(source)
    for sample_index, row in enumerate(frame.itertuples(index=False), start=0):
        # The existing parser reports source_row, specimen_id, electrolyte_id,
        # potential_V and signed_current_density_A_m2 in its fixed row schema.
        current_A_cm2 = float(row.signed_current_density_A_m2) / 10_000.0
        yield GalvanizedPolarizationSample(
            attribution=authorization.attribution,
            authorization_sha256=authorization_sha256,
            source_filename=source.name,
            source_file_md5=md5,
            source_file_sha256=sha256,
            provider_source_row=int(row.source_row),
            sample_index=sample_index,
            specimen_id=str(row.specimen_id),
            electrolyte_id=str(row.electrolyte_id),
            potential_V_provider_reported_reference_unresolved=float(row.potential_V),
            current_density_provider_A_cm2=current_A_cm2,
            signed_current_density_A_m2=float(row.signed_current_density_A_m2),
        )


def audit_galvanized_polarization_workbook(
    request: GalvanizedPolarizationArchiveAuditRequest,
) -> Calculation:
    """Return pinned source metadata only; do not return the local path or curve values."""
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    source = Path(request.local_workbook_path)
    md5, size, sha256 = _asset_identity(source)
    frame = read_galvanized_polarization(source)
    return Calculation(values={
        "model_id": "data.zenodo_galvanized_polarization_typed_rows",
        "dataset_id": DATASET_ID,
        "provider_record": PROVIDER_RECORD,
        "license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "source_filename": source.name,
        "source_file_md5": md5,
        "source_file_sha256": sha256,
        "source_file_bytes": size,
        "sample_count": int(len(frame)),
        "electrolyte_ids": sorted(str(value) for value in frame.electrolyte_id.unique()),
        "specimen_ids": sorted(str(value) for value in frame.specimen_id.unique()),
        "local_path_returned": False,
        "sample_values_returned": False,
        "local_only": True,
        "reference_electrode_subtype_resolved": False,
        "tafel_extrapolation_performed": False,
    }, notes=(
        "Metadata-only audit; use iter_galvanized_polarization_samples for attributed local row access.",
        "The reader preserves signed polarization observations and does not choose Tafel branches or infer corrosion rate.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="data.zenodo_galvanized_polarization_typed_rows",
        input_type=GalvanizedPolarizationArchiveAuditRequest,
        evaluator=audit_galvanized_polarization_workbook,
        units={"source_file_bytes": "byte", "sample_count": "row"},
        assumptions=(
            "Only the three catalogued polarization workbook assets with the declared file size and depositor MD5 are accepted.",
            "The caller supplies CC BY 4.0 attribution and computational/local-use authorization; output rows retain its digest and local-only boundary.",
            "Potential reference details remain unresolved; no Tafel extrapolation, corrosion rate, specimen ranking or acceptance is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="data_import",
    )]

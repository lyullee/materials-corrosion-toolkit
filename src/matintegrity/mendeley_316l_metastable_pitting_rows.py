"""Typed local adapter for Mendeley 316L metastable-pitting chronoamperometry.

BioLogic MPR decoding is injected by the caller. This module contains no MPR
parser implementation and does not bundle a parser with a conflicting license.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Callable, Iterable, Iterator, Mapping
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt, StrictStr

from .contracts import Contract, Evidence, canonical_digest

DATASET_ID = "mendeley-316l-metastable-pitting-chronoamperometry"
DATASET_DOI = "10.17632/z43xxs7hvv.1"
LICENSE_ID = "CC-BY-4.0"
SOURCE_ID = "mendeley_316l_metastable_pitting_rows"

_ASSETS = {
    "Sample_I_chronoamperometry.mpr": (
        924_922,
        "1675b5783474479b334ca8fac3c49cce1a8f3c5f6c5256ee95acca9b05c35984",
    ),
    "Sample_II_Chronoamperometry.mpr": (
        706_438,
        "d10c266318610e3b9fdb181544d47c2eaac9a2bf8a7a1008b13b5d780c9b001a",
    ),
    "Sample_III_Chronoamperometry.mpr": (
        110_989,
        "d52ea10ac9b389d37a6f48a9b0aca4784f50872d532e2c082ac556d3a0eb7b0c",
    ),
}
_FILE_IDS = {
    "Sample_I_chronoamperometry.mpr": "c10594d2-405b-4499-9294-d47790ddcbff",
    "Sample_II_Chronoamperometry.mpr": "02f6497c-1e55-4fe1-b6af-b1f29498167c",
    "Sample_III_Chronoamperometry.mpr": "c29fa3aa-947c-4460-ba39-ae7145e13cc2",
}


class MetastablePittingReadAuthorization(Contract):
    """Caller declaration for attribution and local computational reuse."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: StrictStr = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class MprDecodedRecord(Contract):
    """Minimal caller-decoder output; the reader preserves reported values and units."""

    time_value: float
    time_unit: StrictStr = Field(min_length=1)
    potential_value: float
    potential_unit: StrictStr = Field(min_length=1)
    current_value: float
    current_unit: StrictStr = Field(min_length=1)


class MetastablePittingMeasurementRow(Contract):
    """One typed decoded row tied to exact dataset asset, parser identity, and source order."""

    schema_version: Literal["matintegrity.mendeley_316l_metastable_pitting_row.v1"] = (
        "matintegrity.mendeley_316l_metastable_pitting_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: StrictStr = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    provider_filename: Literal[
        "Sample_I_chronoamperometry.mpr",
        "Sample_II_Chronoamperometry.mpr",
        "Sample_III_Chronoamperometry.mpr",
    ]
    provider_file_id: StrictStr
    provider_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_bytes: StrictInt = Field(gt=0)
    sample_label: Literal["I", "II", "III"]
    source_order: StrictInt = Field(ge=0)
    parser_name: StrictStr = Field(min_length=1)
    parser_version: StrictStr = Field(min_length=1)
    parsed_record: MprDecodedRecord
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    potential_reference_normalized: Literal[False] = False
    current_density_derived: Literal[False] = False
    pit_event_label_inferred: Literal[False] = False
    remaining_life_inferred: Literal[False] = False


MprDecoder = Callable[[Path], Iterable[MprDecodedRecord | Mapping[str, object]]]


def _sha256(path: Path) -> tuple[int, str]:
    expected = _ASSETS.get(path.name)
    if expected is None or not path.is_file():
        raise ValueError("only the three catalogued Mendeley MPR files are accepted")
    expected_size, expected_sha = expected
    size = path.stat().st_size
    if size != expected_size:
        raise ValueError(f"provider byte count mismatch for {path.name}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != expected_sha:
        raise ValueError(f"provider SHA-256 mismatch for {path.name}")
    return size, expected_sha


def iter_mendeley_316l_metastable_pitting_rows(
    directory: str | Path,
    *,
    authorization: MetastablePittingReadAuthorization,
    decoder: MprDecoder,
    parser_name: str,
    parser_version: str,
) -> Iterator[MetastablePittingMeasurementRow]:
    """Decode the three pinned MPR files with a caller-supplied, license-reviewed parser.

    The decoder must yield records with `time_value`, `time_unit`,
    `potential_value`, `potential_unit`, `current_value`, and `current_unit`.
    It is responsible for mapping native parser columns without changing values.
    """
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 attribution must be nonempty")
    if not parser_name.strip() or not parser_version.strip():
        raise ValueError("decoder name and version must be recorded")
    root = Path(directory)
    authorization_sha = canonical_digest(authorization.model_dump(mode="json"))
    for filename in _ASSETS:
        path = root / filename
        size, digest = _sha256(path)
        sample = filename.split("_", maxsplit=2)[1].upper()
        for order, item in enumerate(decoder(path)):
            record = item if isinstance(item, MprDecodedRecord) else MprDecodedRecord.model_validate(item)
            if not all(math.isfinite(value) for value in (
                record.time_value, record.potential_value, record.current_value
            )):
                raise ValueError(f"decoder produced a non-finite measurement in {filename}")
            row_data = record.model_dump(mode="json")
            row_digest = canonical_digest({
                "dataset_id": DATASET_ID,
                "provider_file_id": _FILE_IDS[filename],
                "provider_sha256": digest,
                "source_order": order,
                "record": row_data,
                "parser_name": parser_name,
                "parser_version": parser_version,
                "authorization_sha256": authorization_sha,
            })
            yield MetastablePittingMeasurementRow(
                attribution=authorization.attribution,
                authorization_sha256=authorization_sha,
                provider_filename=filename,
                provider_file_id=_FILE_IDS[filename],
                provider_sha256=digest,
                provider_bytes=size,
                sample_label=sample,
                source_order=order,
                parser_name=parser_name,
                parser_version=parser_version,
                parsed_record=record,
                source_row_sha256=row_digest,
                evidence=Evidence(
                    source_id=DATASET_ID,
                    origin="open_dataset",
                    citation=(
                        f"{authorization.attribution}; https://doi.org/{DATASET_DOI}; "
                        "https://doi.org/10.1016/j.corsci.2020.109004"
                    ),
                    license_id=LICENSE_ID,
                    sha256=digest,
                ),
            )

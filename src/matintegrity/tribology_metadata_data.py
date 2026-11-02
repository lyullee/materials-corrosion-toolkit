"""Audit pinned tribology RDF metadata without interpreting it as wear observations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract

DATASET_ID = "zenodo-7923128-sapphire-copper-tribology-metadata"
PROVIDER_RECORD = "https://doi.org/10.5281/zenodo.7923128"
LICENSE_ID = "CC-BY-4.0"


class TribologyMetadataFileAudit(Contract):
    filename: str = Field(min_length=1)
    bytes: int = Field(gt=0)
    provider_md5: str = Field(pattern=r"^[a-f0-9]{32}$")
    local_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    role: Literal["experiment_series", "equipment", "specimen", "consumables", "software"]


class TribologyMetadataDatasetAudit(Contract):
    schema_version: Literal["matintegrity.tribology_metadata_audit.v1"] = (
        "matintegrity.tribology_metadata_audit.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    files: tuple[TribologyMetadataFileAudit, ...] = Field(min_length=1)
    file_count: int = Field(gt=0)
    total_bytes: int = Field(gt=0)
    all_provider_md5_verified: Literal[True]
    numerical_use_status: Literal["metadata_only_linked_measurements_not_acquired"] = (
        "metadata_only_linked_measurements_not_acquired"
    )

    @model_validator(mode="after")
    def totals_match(self):
        if self.file_count != len(self.files):
            raise ValueError("tribology metadata file count does not match audited rows")
        if self.total_bytes != sum(row.bytes for row in self.files):
            raise ValueError("tribology metadata byte total does not match audited rows")
        return self


def _digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _packaged_manifest() -> tuple[dict, ...]:
    path = Path(__file__).with_name("catalog_data") / "datasets.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    dataset = next((row for row in catalog["datasets"] if row["id"] == DATASET_ID), None)
    if dataset is None:
        raise ValueError("packaged dataset catalog lacks the pinned tribology metadata manifest")
    return tuple(dataset["assets"])


def _role(filename: str) -> str:
    if filename.startswith("copper-under-"):
        return "experiment_series"
    return {
        "laboratory-equipment.ttl": "equipment",
        "tribological-specimen-flins.ttl": "specimen",
        "consumables.ttl": "consumables",
        "software.ttl": "software",
    }[filename]


def audit_tribology_metadata_dataset(
    directory: str | Path,
    *,
    manifest: tuple[dict, ...] | None = None,
) -> TribologyMetadataDatasetAudit:
    """Verify the complete caller-selected manifest and preserve metadata-only status."""
    root = Path(directory)
    expected = _packaged_manifest() if manifest is None else manifest
    if not expected:
        raise ValueError("tribology metadata manifest cannot be empty")
    names = [row["filename"] for row in expected]
    if len(names) != len(set(names)):
        raise ValueError("tribology metadata manifest filenames must be unique")
    actual_names = {path.name for path in root.iterdir() if path.is_file()}
    if actual_names != set(names):
        raise ValueError("tribology metadata directory differs from the complete pinned manifest")
    audited = []
    for asset in sorted(expected, key=lambda row: row["filename"]):
        path = root / asset["filename"]
        expected_md5 = asset["checksum"].removeprefix("md5:")
        if path.stat().st_size != asset["bytes"]:
            raise ValueError(f"tribology metadata byte count differs for {path.name}")
        actual_md5 = _digest(path, "md5")
        if actual_md5 != expected_md5:
            raise ValueError(f"tribology metadata provider MD5 differs for {path.name}")
        audited.append(
            TribologyMetadataFileAudit(
                filename=path.name,
                bytes=path.stat().st_size,
                provider_md5=actual_md5,
                local_sha256=_digest(path, "sha256"),
                role=_role(path.name),
            )
        )
    return TribologyMetadataDatasetAudit(
        files=tuple(audited),
        file_count=len(audited),
        total_bytes=sum(row.bytes for row in audited),
        all_provider_md5_verified=True,
    )

"""Local-only file inventory for a Mendeley AISI 1018 aerobic-corrosion dataset.

The mixed text and OPJ files do not provide one stable, fully explicit table
schema. This module verifies pinned assets and emits file-level lineage only;
it never reads or interprets file contents.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

DATASET_ID = "mendeley-aisi1018-aerobic-consortium-corrosion"
DATASET_DOI = "10.17632/zyy3yktzpf.1"
DATASET_URL = "https://data.mendeley.com/datasets/zyy3yktzpf/1"
LICENSE_ID = "CC-BY-4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
MODEL_ID = "data.mendeley_aisi1018_aerobic_corrosion_file_inventory"
SOURCE_ID = "mendeley_aisi1018_aerobic_corrosion_file_inventory"
MAPPING_SOURCE_ID = "caller_aisi1018_corrosion_file_mapping"

FILE_METADATA: dict[str, dict[str, object]] = {
    "Agua-oJ0CFP.txt": {"file_id": "95a9f68a-2932-4b9e-8ef1-ab5bbc7cbc4c", "bytes": 6287, "sha256": "e7ffb39384d92c3d4d2990ea8a1c640505fc50bc20b565a1f04b3934a0375b9d", "content_type": "text/plain"},
    "Agua.txt": {"file_id": "5eb7ae69-4f18-48e0-b0f5-2a6c743fb0e5", "bytes": 6287, "sha256": "e7ffb39384d92c3d4d2990ea8a1c640505fc50bc20b565a1f04b3934a0375b9d", "content_type": "text/plain"},
    "bacterias + cro  mediana.txt": {"file_id": "c31b8ece-0ad0-4517-b64c-6f4544d8a7fb", "bytes": 6316, "sha256": "9d6d1310035894a2b451f2c092f2adf44a3307b02e7327096181d74394dd3293", "content_type": "text/plain"},
    "Bacterias + CRO 2X.txt": {"file_id": "4e83ad88-7f23-448a-bb9f-c253c39a2816", "bytes": 6299, "sha256": "135212470f49cc4268348b20b6ce8adf50f6682a47b9517e2677e75e6731f566", "content_type": "text/plain"},
    "Bacterias + Muicle 2x.txt": {"file_id": "83b09c6c-3a8e-42b4-b6bc-abfed8ec2cd1", "bytes": 6321, "sha256": "9fffb12f297c2877e58fee8184b4180f385ce80a9a898a24ae1deaf2890f428f", "content_type": "text/plain"},
    "bacterias + muicle mediana.txt": {"file_id": "6aa59119-5df2-4742-8472-aba74ef31004", "bytes": 1493, "sha256": "2e87e0f6935d23223ea00082db4ecb0ba4cb85c97661bb6841555b8d3b0495ea", "content_type": "text/plain"},
    "BACTERIAS 2x.txt": {"file_id": "130d4cbe-b3de-4e32-9e33-d92e9636dbf7", "bytes": 6292, "sha256": "ffa913524c902a0715cc4de24c91c133b72b2f391b55b9c91d285dd184746225", "content_type": "text/plain"},
    "Bacterias mediana.txt": {"file_id": "4575320e-716e-45b1-a1b7-43a603dacf29", "bytes": 6308, "sha256": "32fe217209cba28f0307bbbb871ea0f4ab300a4f462a0fe8faeee680bf3dafc9", "content_type": "text/plain"},
    "CR WL high.opj": {"file_id": "d6c0b36a-ae62-48db-948a-b11f5ce07b75", "bytes": 51626, "sha256": "22cc76aedf4678bfbfef5c4b2548718c2366a674c330b0131e09b8e387a0fc29", "content_type": "application/octet-stream"},
    "CR WL medium.opj": {"file_id": "1aee831f-70cd-4653-8108-027fb10cb534", "bytes": 51575, "sha256": "ea043fce5092757a90ad0e2722b17e906e0b0df6fcf2e87996d48638e064f310", "content_type": "application/octet-stream"},
    "CR WL.opj": {"file_id": "ca6fcab9-e78b-4d69-b496-ed726b40454d", "bytes": 51581, "sha256": "dcf34b49f36e487ad8e2fe7ae79094a6786c0c0bf45c41a2351250c72649bdab", "content_type": "application/octet-stream"},
    "CRO 2X.txt": {"file_id": "efeea572-345a-4866-b906-7cabd1e32eeb", "bytes": 6308, "sha256": "59d9ac8c609e5430a0f8e49777c8472baf5610547aefcb13385aeec4a2eeebc1", "content_type": "text/plain"},
    "CRO mediana.txt": {"file_id": "b6d4de7b-4e79-4f19-b9cf-d567d24aeccb", "bytes": 6303, "sha256": "141bbd27ae1f801ae83b23c7f3f3418af921d7142748add492301b7e5c482b20", "content_type": "text/plain"},
    "eis AGUA + BACTERIAS + CRO.txt": {"file_id": "b70f9899-a22f-4348-8f94-b6eea3ed6bc8", "bytes": 4608, "sha256": "c2f9efc3740c8d1aceb3eb4557421478d705649c4bff680d02e534a07abba450", "content_type": "text/plain"},
    "eis AGUA + BACTERIAS + muicle.txt": {"file_id": "59f33483-a56c-418d-b8b1-642e120f694c", "bytes": 4601, "sha256": "fc13fbc4c55cea4619920d6e76d1f7d25d3f4dad210325556aa5aade40bb4f5c", "content_type": "text/plain"},
    "eis AGUA + BACTERIAS.txt": {"file_id": "929a5cca-0770-4d95-ac3f-6cbde5e3a373", "bytes": 4596, "sha256": "3135557733f63e549fcce52bd8da463071daeae84eb35e6a6d8979c7191f26de", "content_type": "text/plain"},
    "eis AGUA + CRO.txt": {"file_id": "3fc186d3-f014-4aa1-b195-bb0393af3e08", "bytes": 4604, "sha256": "cbfb7bac593ec1f4742ff015ed01ca462775082d4f45a0b05c353de62fb42d8b", "content_type": "text/plain"},
    "eis AGUA + muicle.txt": {"file_id": "0b890063-8209-4cca-8180-a9d3e68e18f2", "bytes": 4601, "sha256": "b4c5c5a255f0014f7ddda1df8f5587a1a543bd16b7dea03843e0bc657b228794", "content_type": "text/plain"},
    "EIS.opj": {"file_id": "ff98ed0e-b767-4f4a-b888-aadd9b7c80e1", "bytes": 82393, "sha256": "993a2cab9b2eff3e15a436424dcde7e1df0474c144049814e7decd5c3b76ab80", "content_type": "application/octet-stream"},
    "LPR.opj": {"file_id": "20c4957f-0c4b-49e3-9f52-d57fbf17b964", "bytes": 113508, "sha256": "666a0a0dda08a6a56c347f36ae590e86e13d006a898cc23a697c5b0d0cfaf678", "content_type": "application/octet-stream"},
    "Muicle 2x.txt": {"file_id": "bd44e2f2-ffc1-4584-88ba-0e742cf68ef3", "bytes": 6314, "sha256": "13b2fa3d8ef890c08f8c72be2e2f185fe1c3a6a957fea2a45e995a8b73127eef", "content_type": "text/plain"},
    "Muicle mediana.txt": {"file_id": "17b90cb4-f1ad-445f-8e87-cdc5a8ddaf85", "bytes": 6334, "sha256": "de0c565638928549519d5dd8c00b0bd256c6e228a7c878f790250a1be52a0565", "content_type": "text/plain"},
}


class AISI1018ReadAuthorization(Contract):
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]

    @model_validator(mode="after")
    def pin_attribution(self):
        if DATASET_DOI not in self.attribution:
            raise ValueError("attribution must identify Mendeley Data v1 DOI")
        return self


class AISI1018FileMapping(Contract):
    source_filename: str = Field(min_length=1, max_length=256)
    caller_label: str = Field(min_length=1, max_length=256)
    mapping_basis: str = Field(min_length=1, max_length=2000)
    evidence: Evidence

    @model_validator(mode="after")
    def require_caller_mapping_evidence(self):
        if self.source_filename not in FILE_METADATA:
            raise ValueError("mapping must target an exact pinned provider filename")
        if self.evidence.source_id != MAPPING_SOURCE_ID or self.evidence.origin != "user_declared":
            raise ValueError("mapping requires caller-declared mapping Evidence")
        return self


class AISI1018InventoryRequest(Contract):
    local_data_directory: str = Field(min_length=1)
    authorization: AISI1018ReadAuthorization
    include_filenames: tuple[str, ...] = Field(default_factory=lambda: tuple(FILE_METADATA), min_length=1, max_length=22)
    file_mappings: tuple[AISI1018FileMapping, ...] = Field(default=(), max_length=22)

    @model_validator(mode="after")
    def validate_selection_and_mapping(self):
        if len(set(self.include_filenames)) != len(self.include_filenames):
            raise ValueError("filename selection must be unique")
        if set(self.include_filenames) - set(FILE_METADATA):
            raise ValueError("only pinned version-1 filenames are accepted")
        mapped_names = [row.source_filename for row in self.file_mappings]
        if len(set(mapped_names)) != len(mapped_names) or set(mapped_names) - set(self.include_filenames):
            raise ValueError("caller mappings must be unique and target selected files")
        return self


class AISI1018InventoryItem(Contract):
    schema_version: Literal["matintegrity.mendeley_aisi1018_inventory_item.v1"] = (
        "matintegrity.mendeley_aisi1018_inventory_item.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    provider_filename: str = Field(min_length=1, max_length=256)
    provider_file_id: str = Field(min_length=1, max_length=128)
    content_type: str = Field(min_length=1, max_length=128)
    extension: str = Field(min_length=1, max_length=16)
    provider_bytes: StrictInt = Field(gt=0)
    provider_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_mapping: AISI1018FileMapping | None = None
    evidence: Evidence

    @model_validator(mode="after")
    def validate_lineage(self):
        meta = FILE_METADATA.get(self.provider_filename)
        if not meta or (self.provider_file_id != meta["file_id"] or self.provider_bytes != meta["bytes"]
                        or self.provider_sha256 != meta["sha256"] or self.content_type != meta["content_type"]):
            raise ValueError("asset identity differs from pinned Mendeley v1 metadata")
        if self.evidence.source_id != DATASET_ID or self.evidence.license_id != LICENSE_ID:
            raise ValueError("Evidence must retain dataset identity and CC BY license")
        if self.evidence.sha256 != self.provider_sha256 or DATASET_DOI not in self.evidence.citation:
            raise ValueError("Evidence must pin file digest and versioned dataset citation")
        if self.caller_mapping and self.caller_mapping.source_filename != self.provider_filename:
            raise ValueError("caller mapping filename must match the inventoried asset")
        return self


def audit_aisi1018_dataset_inventory(request: AISI1018InventoryRequest) -> Calculation:
    """Verify pinned files and return metadata only; file contents are never opened for parsing."""
    root = Path(request.local_data_directory)
    authorization_sha = canonical_digest(request.authorization.model_dump(mode="json"))
    mapping_by_name = {item.source_filename: item for item in request.file_mappings}
    items = []
    for filename in request.include_filenames:
        meta = FILE_METADATA[filename]
        path = root / filename
        if not path.is_file() or path.stat().st_size != meta["bytes"]:
            raise ValueError(f"missing file or provider byte-size mismatch: {filename}")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        sha256 = digest.hexdigest()
        if sha256 != meta["sha256"]:
            raise ValueError(f"provider SHA-256 mismatch: {filename}")
        mapping = mapping_by_name.get(filename)
        item = AISI1018InventoryItem(
            attribution=request.authorization.attribution,
            authorization_sha256=authorization_sha,
            provider_filename=filename,
            provider_file_id=str(meta["file_id"]),
            content_type=str(meta["content_type"]),
            extension=Path(filename).suffix.lower(),
            provider_bytes=int(meta["bytes"]),
            provider_sha256=sha256,
            caller_mapping=mapping,
            evidence=Evidence(
                source_id=DATASET_ID,
                origin="open_dataset",
                citation=f"{request.authorization.attribution}; {DATASET_URL}; CC BY 4.0",
                license_id=LICENSE_ID,
                sha256=sha256,
            ),
        )
        items.append(item.model_dump(mode="json"))
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "status": "computed",
        "authorization_sha256": authorization_sha,
        "inventory": items,
        "inventory_count": len(items),
        "content_parsed": False,
        "measurement_values_emitted": False,
        "column_meanings_inferred": False,
        "units_inferred_or_converted": False,
        "third_party_rights_separately_reviewed": False,
    }, notes=(
        "This file inventory confirms provider identity only; it does not interpret corrosion measurements.",
        "The dataset is provider-declared CC BY 4.0; embedded third-party content may require separate permission.",
    ))


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=AISI1018InventoryRequest,
        evaluator=audit_aisi1018_dataset_inventory,
        units={"inventory_count": "1", "provider_bytes": "byte"},
        assumptions=(
            "Only the exact 22 Mendeley Data v1 files, byte sizes and provider SHA-256 digests are accepted.",
            "The reader verifies bytes and emits filenames, content types, digests and optional caller mappings only.",
            "No text, OPJ, tabular measurements, units, specimen identities or conditions are parsed or inferred.",
            "Caller mappings are user-declared file labels, not scientific validation or measurement interpretation.",
            "Provider declares CC BY 4.0; identified third-party content may require separate permission; output is local-only.",
        ),
        source_ids=(SOURCE_ID, MAPPING_SOURCE_ID),
        version="1.0.0",
        qualification="data_import",
    ),)

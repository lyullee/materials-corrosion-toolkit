"""Local-only typed row access for versioned Mendeley CO2/MDEA EIS files."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

DATASET_ID = "mendeley-mdea-co2-protective-films-eis"
DATASET_DOI = "10.17632/6tscvfjycn.3"
ARTICLE_DOI = "10.1016/j.corsci.2022.110859"
RECORD_URL = "https://data.mendeley.com/datasets/6tscvfjycn/3"
FILES_API_URL = (
    "https://data.mendeley.com/public-api/datasets/6tscvfjycn/files"
    "?folder_id=root&version=3&$start=0&$limit=1000"
)
LICENSE_ID = "CC-BY-4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
MODEL_ID = "data.mendeley_mdea_co2_eis_typed_rows"
SOURCE_ID = "mendeley_mdea_co2_eis_version3"
LOCAL_MANIFEST_FILENAME = "local_manifest.json"
LOCAL_MANIFEST_SHA256 = "66a986fe60dc17d52941863a8ef5721a8c93edc70b076d81a37466063862e4bf"


class MDEAEISReadAuthorization(Contract):
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    article_doi: Literal[ARTICLE_DOI] = ARTICLE_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]

    @model_validator(mode="after")
    def attribution_pins_sources(self):
        value = self.attribution.strip()
        if not value or DATASET_DOI not in value or ARTICLE_DOI not in value:
            raise ValueError("attribution must cite both the versioned dataset and article DOI")
        return self


class MDEAEISCell(Contract):
    column_index: StrictInt = Field(ge=0, le=128)
    column_name: str
    raw_token: str
    numeric_value: float | None
    value_kind: Literal["numeric", "empty", "text", "nonfinite_numeric_text"]

    @model_validator(mode="after")
    def validate_cell(self):
        if self.value_kind == "numeric":
            if self.numeric_value is None or not math.isfinite(self.numeric_value):
                raise ValueError("finite parsed numeric cells must retain a finite numeric value")
        elif self.numeric_value is not None:
            raise ValueError("non-numeric cells must not carry converted numbers")
        return self


class MDEAEISPointRow(Contract):
    schema_version: Literal["matintegrity.mendeley_mdea_co2_eis_point_row.v1"] = (
        "matintegrity.mendeley_mdea_co2_eis_point_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    article_doi: Literal[ARTICLE_DOI] = ARTICLE_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_filename: str = Field(min_length=1, max_length=256)
    provider_file_id: str = Field(min_length=1, max_length=128)
    provider_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_file_bytes: StrictInt = Field(gt=0)
    data_kind: Literal["experimental", "simulated"]
    worksheet_name: Literal["text"] = "text"
    provider_line_number: StrictInt = Field(ge=2)
    ordered_header: tuple[str, ...] = Field(min_length=1, max_length=128)
    source_header_line: str = Field(min_length=1, max_length=4096)
    header_has_trailing_delimiter: Literal[True] = True
    ordered_cells: tuple[MDEAEISCell, ...] = Field(min_length=1, max_length=128)
    raw_line_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence

    @model_validator(mode="after")
    def validate_lineage(self):
        if len(self.ordered_header) != len(self.ordered_cells):
            raise ValueError("each source token must align to exactly one provider header")
        if tuple(cell.column_name for cell in self.ordered_cells) != self.ordered_header:
            raise ValueError("typed cell columns must preserve exact header order and labels")
        if self.evidence.source_id != DATASET_ID or self.evidence.license_id != LICENSE_ID:
            raise ValueError("Evidence must retain dataset identity and CC BY license")
        if self.evidence.sha256 != self.provider_sha256:
            raise ValueError("Evidence must pin the provider file SHA-256")
        if DATASET_DOI not in self.evidence.citation or ARTICLE_DOI not in self.evidence.citation:
            raise ValueError("Evidence citation must bind dataset and article DOIs")
        return self


class MDEAEISFolderAuditRequest(Contract):
    local_data_directory: str = Field(min_length=1)
    authorization: MDEAEISReadAuthorization


def _load_manifest(directory: Path) -> tuple[list[dict[str, Any]], str]:
    path = directory / LOCAL_MANIFEST_FILENAME
    if not path.is_file():
        raise ValueError("the pinned local Mendeley file manifest is missing")
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != LOCAL_MANIFEST_SHA256:
        raise ValueError("local file manifest differs from the reviewed provider metadata pin")
    manifest = json.loads(payload.decode("utf-8-sig"))
    if manifest.get("dataset_id") != DATASET_ID or manifest.get("dataset_doi") != DATASET_DOI:
        raise ValueError("local manifest identifies another dataset")
    if manifest.get("version") != 3 or manifest.get("license") != LICENSE_ID:
        raise ValueError("local manifest version or license differs from the pinned record")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("local manifest has no versioned file records")
    if len({row.get("filename") for row in files}) != len(files):
        raise ValueError("versioned filenames must be unique")
    return files, digest


def _file_digest(path: Path, expected: dict[str, Any]) -> str:
    if path.name != expected["filename"] or not path.is_file():
        raise ValueError("local EIS asset is missing or has an unexpected filename")
    if path.stat().st_size != expected["bytes"]:
        raise ValueError("local EIS asset size differs from the versioned provider metadata")
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    digest = sha.hexdigest()
    if digest != expected["sha256"]:
        raise ValueError("local EIS asset SHA-256 differs from the provider file metadata")
    return digest


def _typed_cell(index: int, name: str, token: str) -> MDEAEISCell:
    if token == "":
        return MDEAEISCell(column_index=index, column_name=name, raw_token=token,
                           numeric_value=None, value_kind="empty")
    try:
        value = float(token)
    except ValueError:
        return MDEAEISCell(column_index=index, column_name=name, raw_token=token,
                           numeric_value=None, value_kind="text")
    if not math.isfinite(value):
        return MDEAEISCell(column_index=index, column_name=name, raw_token=token,
                           numeric_value=None, value_kind="nonfinite_numeric_text")
    return MDEAEISCell(column_index=index, column_name=name, raw_token=token,
                       numeric_value=value, value_kind="numeric")


def iter_mendeley_mdea_eis_rows(
    directory: str | Path, *, authorization: MDEAEISReadAuthorization,
    include_simulated: bool = True,
) -> Iterator[MDEAEISPointRow]:
    """Yield locally authorized EIS rows in provider file and line order.

    Experimental and simulated files are marked from the provider filename prefix and are
    never merged. The parser preserves raw tokens and headers and does not fit impedance models.
    """
    folder = Path(directory)
    files, _manifest_digest = _load_manifest(folder)
    auth_digest = canonical_digest(authorization.model_dump(mode="json"))
    for metadata in files:
        if metadata.get("data_kind") == "simulated" and not include_simulated:
            continue
        if metadata.get("data_kind") not in {"experimental", "simulated"}:
            raise ValueError("unknown provider source type; refusing to merge or reinterpret files")
        source = folder / metadata["filename"]
        file_digest = _file_digest(source, metadata)
        with source.open("r", encoding="cp1252", newline="") as stream:
            header_line = stream.readline()
            if not header_line:
                raise ValueError("versioned EIS text file is empty")
            raw_header_line = header_line.rstrip("\r\n")
            header_fields = raw_header_line.split("\t")
            if not header_fields or header_fields[-1] != "":
                raise ValueError("provider EIS header lost its reviewed trailing-tab delimiter")
            header_fields = header_fields[:-1]
            header = tuple(header_fields)
            if not header or any(name == "" for name in header):
                raise ValueError("EIS column header has an empty field or no columns")
            if len(header) != len(set(header)):
                raise ValueError("EIS column names are not unique in this source file")
            for line_number, line in enumerate(stream, start=2):
                raw_line = line.rstrip("\r\n")
                if raw_line == "":
                    continue
                tokens = tuple(raw_line.split("\t"))
                if len(tokens) != len(header):
                    raise ValueError(f"provider line {line_number} does not match its header width")
                cells = tuple(_typed_cell(i, header[i], token) for i, token in enumerate(tokens))
                evidence = Evidence(
                    source_id=DATASET_ID,
                    origin="open_dataset",
                    citation=f"{authorization.attribution}; dataset DOI {DATASET_DOI}; article DOI {ARTICLE_DOI}; CC BY 4.0",
                    license_id=LICENSE_ID,
                    sha256=file_digest,
                )
                yield MDEAEISPointRow(
                    attribution=authorization.attribution,
                    authorization_sha256=auth_digest,
                    source_filename=metadata["filename"],
                    provider_file_id=metadata["file_id"],
                    provider_sha256=file_digest,
                    source_file_bytes=metadata["bytes"],
                    data_kind=metadata["data_kind"],
                    provider_line_number=line_number,
                    ordered_header=header,
                    source_header_line=raw_header_line,
                    ordered_cells=cells,
                    raw_line_sha256=hashlib.sha256(raw_line.encode("cp1252")).hexdigest(),
                    evidence=evidence,
                )


def audit_mendeley_mdea_eis_directory(request: MDEAEISFolderAuditRequest) -> Calculation:
    """Return pinned file and tabular schema metadata without numeric point values."""
    folder = Path(request.local_data_directory)
    files, manifest_digest = _load_manifest(folder)
    output = []
    for metadata in files:
        source = folder / metadata["filename"]
        sha = _file_digest(source, metadata)
        with source.open("r", encoding="cp1252", newline="") as stream:
            header_fields = stream.readline().rstrip("\r\n").split("\t")
            if not header_fields or header_fields[-1] != "":
                raise ValueError("provider EIS header lost its reviewed trailing-tab delimiter")
            header_fields = header_fields[:-1]
            header = tuple(header_fields)
            line_count = sum(1 for line in stream if line.rstrip("\r\n") != "")
        output.append({"filename": metadata["filename"], "provider_file_id": metadata["file_id"],
                       "bytes": metadata["bytes"], "sha256": sha, "data_kind": metadata["data_kind"],
                       "header": list(header), "data_rows": line_count})
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "article_doi": ARTICLE_DOI,
        "license_id": LICENSE_ID,
        "record_url": RECORD_URL,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "local_manifest_sha256": manifest_digest,
        "files": output,
        "experimental_and_simulated_rows_combined": False,
        "numeric_values_emitted": False,
        "impedance_model_fitted": False,
        "status": "audited_local_only",
    })


def specifications() -> tuple[ModelSpec, ...]:
    """Expose the metadata-only directory audit to a later central schema/registry sync."""
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=MDEAEISFolderAuditRequest,
        evaluator=audit_mendeley_mdea_eis_directory,
        units={"file_size": "byte", "potential": "V vs caller/source reference", "impedance": "Ohm"},
        assumptions=(
            "Read only pinned Mendeley Data version 3 assets after manifest and provider SHA-256 checks.",
            "Preserve experimental and simulated files as separate provenance groups.",
            "Metadata audit never emits numeric EIS point values or fits impedance models.",
            "Row iteration is caller-local and requires explicit attribution and local-use authorization.",
        ),
        source_ids=(SOURCE_ID,),
        version="1.0.0",
    ),)

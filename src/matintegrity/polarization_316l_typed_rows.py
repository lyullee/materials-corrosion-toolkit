"""Local, attribution-aware reader for the licensed 316L polarization archive.

The reader exposes original measured columns with their provider units. It does
not derive corrosion rates, current density, pit descriptors, or acceptance.
"""

from __future__ import annotations

import hashlib
import math
import re
import zipfile
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import Field, StrictInt, StrictStr

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

DATASET_ID = "zenodo-316l-naCl-potentiodynamic-polarization-v2"
DATASET_DOI = "10.5281/zenodo.15284154"
LICENSE_ID = "CC-BY-4.0"
SOURCE_ID = "zenodo_316l_polarization_typed_rows"
MODEL_ID = "data.zenodo_316l_polarization_typed_rows"
ARCHIVE_FILENAME = "zenodo-15284154-316l-pp.zip"
ARCHIVE_BYTES = 7_170_288
ARCHIVE_MD5 = "794769a9ba3698c2d0bcfd25c45c11b5"
ARCHIVE_SHA256 = "006cf12b8cd3e04ec4732114abdcef8cd4a78579add3319919256fe8c2fc8fd1"
_CONCENTRATIONS = {"0.005M NaCl": "0.005", "0.01M NaCl": "0.01", "0.05M NaCl": "0.05"}
_HEADER = "time/s\tEwe/V\t<I>/mA\t"
_CURVE_NAME = re.compile(r"([abc])(\d{1,2})\.txt\Z", re.IGNORECASE)


class Polarization316LReadAuthorization(Contract):
    """Caller declaration for attributed local computational use of the archive."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: StrictStr = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class Polarization316LRawRow(Contract):
    """One source-order acquisition row; original units and member identity are preserved."""

    schema_version: Literal["matintegrity.polarization_316l_raw_row.v1"] = (
        "matintegrity.polarization_316l_raw_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    attribution: StrictStr = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_archive_filename: Literal[ARCHIVE_FILENAME] = ARCHIVE_FILENAME
    source_archive_bytes: StrictInt = ARCHIVE_BYTES
    source_archive_md5: Literal[ARCHIVE_MD5] = ARCHIVE_MD5
    source_archive_sha256: Literal[ARCHIVE_SHA256] = ARCHIVE_SHA256
    provider_member_path: StrictStr = Field(min_length=1)
    concentration_mol_l: Literal["0.005", "0.01", "0.05"]
    provider_curve_label: StrictStr = Field(min_length=1)
    source_order: StrictInt = Field(ge=0)
    provider_line_number: StrictInt = Field(ge=2)
    elapsed_time_s: float
    working_electrode_potential_v: float
    measured_current_ma: float
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    current_density_derived: Literal[False] = False
    corrosion_rate_derived: Literal[False] = False
    failure_probability_derived: Literal[False] = False


class Polarization316LArchiveAuditRequest(Contract):
    local_archive_path: StrictStr = Field(min_length=1)
    authorization: Polarization316LReadAuthorization


def _archive_digest(path: Path) -> tuple[int, str, str]:
    if path.name != ARCHIVE_FILENAME or not path.is_file():
        raise ValueError("only the catalogued 316L archive filename is accepted")
    size = path.stat().st_size
    if size != ARCHIVE_BYTES:
        raise ValueError("316L archive byte count differs from the reviewed provider asset")
    md5 = hashlib.md5(usedforsecurity=False)
    sha256 = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(chunk)
            sha256.update(chunk)
    if md5.hexdigest() != ARCHIVE_MD5 or sha256.hexdigest() != ARCHIVE_SHA256:
        raise ValueError("316L archive digest differs from the reviewed provider asset")
    return size, md5.hexdigest(), sha256.hexdigest()


def _validated_members(archive: zipfile.ZipFile) -> list[tuple[zipfile.ZipInfo, str, str, str]]:
    members: list[tuple[zipfile.ZipInfo, str, str, str]] = []
    seen: set[str] = set()
    curve_counts = {concentration: 0 for concentration in _CONCENTRATIONS.values()}
    for info in archive.infolist():
        name = info.filename.replace("\\", "/")
        member = PurePosixPath(name)
        if member.is_absolute() or ".." in member.parts or name in seen:
            raise ValueError("316L archive contains an unsafe or duplicate member path")
        seen.add(name)
        if info.flag_bits & 0x1:
            raise ValueError("encrypted 316L archive members are unsupported")
        if info.is_dir() or member.suffix.lower() != ".txt":
            continue
        if len(member.parts) != 2 or member.parts[0] not in _CONCENTRATIONS:
            raise ValueError("unexpected raw-curve path in the reviewed 316L archive")
        match = _CURVE_NAME.fullmatch(member.name)
        if not match:
            raise ValueError("unexpected raw-curve filename in the reviewed 316L archive")
        label, replicate = match.groups()
        replicate_number = int(replicate)
        if not 1 <= replicate_number <= 28:
            raise ValueError("unexpected replicate number in the reviewed 316L archive")
        concentration = _CONCENTRATIONS[member.parts[0]]
        curve_counts[concentration] += 1
        members.append((info, concentration, label.lower(), str(replicate_number)))
    if len(members) != 84 or set(curve_counts.values()) != {28}:
        raise ValueError("reviewed archive must contain 28 raw curves at each of three concentrations")
    return sorted(members, key=lambda item: item[0].filename)


def iter_polarization_316l_raw_rows(
    path: str | Path,
    *,
    authorization: Polarization316LReadAuthorization,
) -> Iterator[Polarization316LRawRow]:
    """Stream the 84 raw curves in stable member and source-row order."""
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 requires nonempty attribution")
    archive_path = Path(path)
    size, _, _ = _archive_digest(archive_path)
    authorization_sha = canonical_digest(authorization.model_dump(mode="json"))
    source_order = 0
    with zipfile.ZipFile(archive_path) as archive:
        for info, concentration, label, replicate in _validated_members(archive):
            with archive.open(info) as stream:
                header = stream.readline().decode("utf-8-sig").rstrip("\r\n")
                if header != _HEADER:
                    raise ValueError(f"unexpected raw-curve header in {info.filename}")
                for line_number, raw in enumerate(stream, start=2):
                    line = raw.decode("utf-8-sig").rstrip("\r\n")
                    if not line:
                        continue
                    fields = line.split("\t")
                    if len(fields) != 3:
                        raise ValueError(f"raw-curve row does not have three measured columns: {info.filename}")
                    try:
                        time_s, potential_v, current_ma = (float(field.strip()) for field in fields)
                    except ValueError as exc:
                        raise ValueError(f"non-numeric raw-curve row in {info.filename}") from exc
                    if not all(math.isfinite(value) for value in (time_s, potential_v, current_ma)):
                        raise ValueError(f"non-finite raw-curve value in {info.filename}")
                    values = {
                        "dataset_id": DATASET_ID,
                        "archive_sha256": ARCHIVE_SHA256,
                        "member": info.filename,
                        "line_number": line_number,
                        "source_line": line,
                        "authorization_sha256": authorization_sha,
                    }
                    yield Polarization316LRawRow(
                        attribution=authorization.attribution,
                        authorization_sha256=authorization_sha,
                        source_archive_bytes=size,
                        provider_member_path=info.filename,
                        concentration_mol_l=concentration,
                        provider_curve_label=f"{label}{replicate}",
                        source_order=source_order,
                        provider_line_number=line_number,
                        elapsed_time_s=time_s,
                        working_electrode_potential_v=potential_v,
                        measured_current_ma=current_ma,
                        source_row_sha256=canonical_digest(values),
                        evidence=Evidence(
                            source_id=DATASET_ID,
                            origin="open_dataset",
                            citation=(f"{authorization.attribution}; https://doi.org/{DATASET_DOI} (CC BY 4.0); "
                                      "https://doi.org/10.1038/s41529-025-00594-7"),
                            license_id=LICENSE_ID,
                            sha256=ARCHIVE_SHA256,
                        ),
                    )
                    source_order += 1


def audit_polarization_316l_archive(request: Polarization316LArchiveAuditRequest) -> Calculation:
    """Return structural metadata only; raw measured values and local paths are excluded."""
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY 4.0 requires nonempty attribution")
    archive_path = Path(request.local_archive_path)
    size, md5, sha256 = _archive_digest(archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        members = _validated_members(archive)
    counts = {value: sum(item[1] == value for item in members) for value in _CONCENTRATIONS.values()}
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "archive_filename": ARCHIVE_FILENAME,
        "archive_bytes": size,
        "archive_md5": md5,
        "archive_sha256": sha256,
        "raw_curve_count": len(members),
        "curves_by_concentration_mol_l": counts,
        "raw_curve_rows_emitted": False,
        "local_only": True,
    }, notes=(
        "The archive includes 84 repeated polarization curves, 28 at each listed NaCl concentration; curve repetitions are not independent material specimens.",
        "Only the three provider acquisition columns are exposed; descriptor CSV files are not parsed as measured raw rows.",
        "The import does not infer current density, corrosion rate, pitting resistance thresholds, remaining life, acceptance, or failure probability.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=Polarization316LArchiveAuditRequest,
        evaluator=audit_polarization_316l_archive,
        units={"archive_bytes": "byte", "raw_curve_count": "curve"},
        assumptions=(
            "Only the catalogued archive filename, byte count, provider MD5 and SHA-256 are accepted.",
            "Caller supplies attribution and explicitly authorizes computational and local-only use.",
            "The reader preserves source order and provider units without converting to current density or corrosion rate.",
            "Repeated curves within the deposited study are not treated as independent specimens or qualification replicates.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="data_import",
    )]

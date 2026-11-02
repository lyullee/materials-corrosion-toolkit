"""Typed local row access to the pinned fracture-toughness temperature compilation."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, StrictInt

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .fracture_toughness_data import read_fracture_toughness_temperature
from .registry import ModelSpec

DATASET_ID = "fracture-toughness-temperature"
DATASET_DOI = "10.17632/2vkgrbsy8j.1"
LICENSE_ID = "CC-BY-4.0"
LICENSE_SCOPE = "compilation_only_underlying_observation_rights_unresolved"
SOURCE_ID = "mendeley_fracture_toughness_temperature_typed_rows"
MODEL_ID = "data.mendeley_fracture_toughness_temperature_typed_rows"
ARCHIVE_FILENAME = "2vkgrbsy8j-1.zip"
ARCHIVE_BYTES = 2_666_905
ARCHIVE_SHA256 = "d1007e9b3a3802594f169a15e72a94353a674cb72daf2faef93f9ae9fabdf66f"
WORKBOOK_MEMBER_SHA256 = "647de2626f39a83ccc35f2a00248e033724d52052cfbb8bd4d8ff0439993b0d2"


class FractureToughnessReadAuthorization(Contract):
    """Caller attribution, unit-review, and local-only computational-use declaration."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    license_scope: Literal[LICENSE_SCOPE] = LICENSE_SCOPE
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]
    parser_unit_interpretations_reviewed: Literal[True]


class FractureToughnessObservationRow(Contract):
    """One parser-emitted source observation with row, unit, and rights lineage."""

    schema_version: Literal["matintegrity.mendeley_fracture_toughness_observation_row.v1"] = (
        "matintegrity.mendeley_fracture_toughness_observation_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    compilation_license_id: Literal[LICENSE_ID] = LICENSE_ID
    compilation_license_scope: Literal[LICENSE_SCOPE] = LICENSE_SCOPE
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_archive_filename: Literal[ARCHIVE_FILENAME] = ARCHIVE_FILENAME
    source_archive_bytes: StrictInt = Field(gt=0)
    source_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_workbook_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_order: StrictInt = Field(ge=0)
    source_partition: Literal["training", "test"]
    source_sheet: str = Field(min_length=1)
    provider_source_row: StrictInt = Field(ge=5)
    reported_record_id: StrictInt = Field(gt=0)
    observation_id: str = Field(min_length=1)
    material_label: str = Field(min_length=1)
    carbon_wt_percent: float
    carbon_mass_fraction: float
    reported_temperature: float
    reported_temperature_unit_label: Literal["K"]
    temperature_K: float | None
    temperature_unit_override: Literal["degC", "K"] | None
    temperature_unit_basis: str = Field(min_length=1)
    yield_strength_MPa: float
    yield_strength_Pa: float
    specimen_type: Literal["CT", "SEB", "PCCv"]
    reported_CT_flag: StrictInt
    reported_SEB_flag: StrictInt
    reported_PCCv_flag: StrictInt
    reported_W: float
    reported_B: float
    reported_a: float
    reported_dimension_unit_label: None = None
    W_m: float | None
    B_m: float | None
    a_m: float | None
    dimension_unit_override: Literal["mm", "m"] | None
    dimension_unit_basis: str = Field(min_length=1)
    reported_KJc_MPa_sqrt_m: float
    reported_KJc_Pa_sqrt_m: float
    physical_specimen_id: None = None
    underlying_literature_id: None = None
    article_source_group_id: str | None
    article_source_group_status: str
    article_source_material_label: str | None
    article_reference_bibliographic_id: str | None
    article_reference_identity_status: str
    article_reference_publication_license_id: str | None
    article_reference_observation_rights_status: str
    condition_group_id: str | None
    condition_group_status: str
    condition_group_W_center_m: float | None
    condition_group_B_center_m: float | None
    condition_group_physical_independence_reviewed: Literal[False] = False
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    underlying_observation_rights_status: Literal["unresolved"] = "unresolved"
    evidence: Evidence
    toughness_validity_inferred: Literal[False] = False
    service_lower_bound_inferred: Literal[False] = False
    acceptance_inferred: Literal[False] = False


class FractureToughnessArchiveAuditRequest(Contract):
    local_archive_path: str = Field(min_length=1)
    temperature_unit_override: Literal["degC", "K"] | None = None
    dimension_unit_override: Literal["mm", "m"] | None = None
    apply_article_dimension_review: bool = True
    condition_group_relative_tolerance: float = Field(default=0.03, ge=0)
    condition_group_absolute_tolerance_m: float = Field(default=1e-4, ge=0)
    authorization: FractureToughnessReadAuthorization


def _verify_archive(path: Path) -> tuple[str, int]:
    if path.name != ARCHIVE_FILENAME or not path.is_file():
        raise ValueError("only the catalogued Mendeley fracture archive is accepted")
    size = path.stat().st_size
    if size != ARCHIVE_BYTES:
        raise ValueError("fracture archive byte count differs from the catalog pin")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    actual = digest.hexdigest()
    if actual != ARCHIVE_SHA256:
        raise ValueError("fracture archive SHA-256 differs from the acquired Mendeley revision")
    return actual, size


def _plain(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    return value


def iter_fracture_toughness_observation_rows(
    path: str | Path,
    *,
    authorization: FractureToughnessReadAuthorization,
    temperature_unit_override: Literal["degC", "K"] | None = None,
    dimension_unit_override: Literal["mm", "m"] | None = None,
    apply_article_dimension_review: bool = True,
    condition_group_relative_tolerance: float = 0.03,
    condition_group_absolute_tolerance_m: float = 1e-4,
) -> Iterator[FractureToughnessObservationRow]:
    """Yield existing parser records in source sheet/row order; do not decide toughness validity."""
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 compilation attribution must be nonempty")
    source = Path(path)
    archive_sha256, archive_bytes = _verify_archive(source)
    frame = read_fracture_toughness_temperature(
        source,
        temperature_unit_override=temperature_unit_override,
        dimension_unit_override=dimension_unit_override,
        apply_article_dimension_review=apply_article_dimension_review,
        condition_group_relative_tolerance=condition_group_relative_tolerance,
        condition_group_absolute_tolerance_m=condition_group_absolute_tolerance_m,
    )
    if (
        frame.attrs.get("source_archive_sha256") != archive_sha256
        or frame.attrs.get("source_member_sha256") != WORKBOOK_MEMBER_SHA256
    ):
        raise ValueError("existing parser archive/member lineage differs from the acquired pin")
    auth_sha256 = canonical_digest(authorization.model_dump(mode="json"))
    parser_options = {
        "temperature_unit_override": temperature_unit_override,
        "dimension_unit_override": dimension_unit_override,
        "apply_article_dimension_review": apply_article_dimension_review,
        "condition_group_relative_tolerance": condition_group_relative_tolerance,
        "condition_group_absolute_tolerance_m": condition_group_absolute_tolerance_m,
    }
    for source_order, row in enumerate(frame.itertuples(index=False), start=0):
        values = {
            "source_partition": str(row.source_partition),
            "source_sheet": str(row.source_sheet),
            "provider_source_row": int(row.source_row),
            "reported_record_id": int(row.reported_record_id),
            "observation_id": str(row.observation_id),
            "material_label": str(row.material_label),
            "carbon_wt_percent": float(row.carbon_wt_percent),
            "carbon_mass_fraction": float(row.carbon_mass_fraction),
            "reported_temperature": float(row.reported_temperature),
            "reported_temperature_unit_label": str(row.reported_temperature_unit_label),
            "temperature_K": _plain(row.temperature_K),
            "temperature_unit_override": _plain(row.temperature_unit_override),
            "temperature_unit_basis": str(row.temperature_unit_basis),
            "yield_strength_MPa": float(row.yield_strength_MPa),
            "yield_strength_Pa": float(row.yield_strength_Pa),
            "specimen_type": str(row.specimen_type),
            "reported_CT_flag": int(row.reported_CT_flag),
            "reported_SEB_flag": int(row.reported_SEB_flag),
            "reported_PCCv_flag": int(row.reported_PCCv_flag),
            "reported_W": float(row.reported_W),
            "reported_B": float(row.reported_B),
            "reported_a": float(row.reported_a),
            "W_m": _plain(row.W_m),
            "B_m": _plain(row.B_m),
            "a_m": _plain(row.a_m),
            "dimension_unit_override": _plain(row.dimension_unit_override),
            "dimension_unit_basis": str(row.dimension_unit_basis),
            "reported_KJc_MPa_sqrt_m": float(row.reported_KJc_MPa_sqrt_m),
            "reported_KJc_Pa_sqrt_m": float(row.reported_KJc_Pa_sqrt_m),
            "article_source_group_id": _plain(row.article_source_group_id),
            "article_source_group_status": str(row.article_source_group_status),
            "article_source_material_label": _plain(row.article_source_material_label),
            "article_reference_bibliographic_id": _plain(row.article_reference_bibliographic_id),
            "article_reference_identity_status": str(row.article_reference_identity_status),
            "article_reference_publication_license_id": _plain(row.article_reference_publication_license_id),
            "article_reference_observation_rights_status": str(row.article_reference_observation_rights_status),
            "condition_group_id": _plain(row.condition_group_id),
            "condition_group_status": str(row.condition_group_status),
            "condition_group_W_center_m": _plain(row.condition_group_W_center_m),
            "condition_group_B_center_m": _plain(row.condition_group_B_center_m),
        }
        yield FractureToughnessObservationRow(
            attribution=authorization.attribution,
            authorization_sha256=auth_sha256,
            source_archive_bytes=archive_bytes,
            source_archive_sha256=archive_sha256,
            source_workbook_sha256=str(frame.attrs["source_member_sha256"]),
            source_order=source_order,
            **values,
            source_row_sha256=canonical_digest({
                "dataset_id": DATASET_ID,
                "source_archive_sha256": archive_sha256,
                "source_workbook_sha256": frame.attrs["source_member_sha256"],
                "source_order": source_order,
                "record": values,
                "parser_options": parser_options,
                "underlying_observation_rights_status": "unresolved",
            }),
            evidence=Evidence(
                source_id=DATASET_ID,
                origin="open_dataset",
                citation=f"{authorization.attribution}; https://doi.org/{DATASET_DOI} (CC BY 4.0 compilation only)",
                license_id=LICENSE_ID,
                sha256=archive_sha256,
            ),
        )


def audit_fracture_toughness_archive(request: FractureToughnessArchiveAuditRequest) -> Calculation:
    """Return pinned archive/partition metadata without pointwise values or local paths."""
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY 4.0 compilation attribution must be nonempty")
    source = Path(request.local_archive_path)
    archive_sha256, archive_bytes = _verify_archive(source)
    frame = read_fracture_toughness_temperature(
        source,
        temperature_unit_override=request.temperature_unit_override,
        dimension_unit_override=request.dimension_unit_override,
        apply_article_dimension_review=request.apply_article_dimension_review,
        condition_group_relative_tolerance=request.condition_group_relative_tolerance,
        condition_group_absolute_tolerance_m=request.condition_group_absolute_tolerance_m,
    )
    if (
        frame.attrs.get("source_archive_sha256") != archive_sha256
        or frame.attrs.get("source_member_sha256") != WORKBOOK_MEMBER_SHA256
    ):
        raise ValueError("existing parser archive/member lineage differs from the acquired pin")
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "compilation_license_id": LICENSE_ID,
        "compilation_license_scope": LICENSE_SCOPE,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "source_archive_filename": ARCHIVE_FILENAME,
        "source_archive_bytes": archive_bytes,
        "source_archive_sha256": archive_sha256,
        "source_workbook_sha256": frame.attrs["source_member_sha256"],
        "observation_count": int(len(frame)),
        "training_partition_rows": int((frame.source_partition == "training").sum()),
        "test_partition_rows": int((frame.source_partition == "test").sum()),
        "underlying_observation_rights_status": "unresolved",
        "source_order_preserved": True,
        "point_values_returned": False,
        "local_path_returned": False,
        "local_only": True,
        "toughness_validity_inferred": False,
        "acceptance_inferred": False,
    }, notes=(
        "The CC BY declaration is for the compilation; rights to individual underlying observations remain unresolved.",
        "Metadata-only audit; use iter_fracture_toughness_observation_rows for authorized local row access.",
        "Parser output is source compilation data, not a validated toughness lower bound, material qualification or acceptance result.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=FractureToughnessArchiveAuditRequest,
        evaluator=audit_fracture_toughness_archive,
        units={
            "source_archive_bytes": "byte",
            "observation_count": "row",
            "training_partition_rows": "row",
            "test_partition_rows": "row",
        },
        assumptions=(
            "Only the exact catalogued Mendeley archive name, byte count, SHA-256 and workbook member digest are accepted.",
            "Caller supplies compilation attribution, unit interpretation review, computational authorization and a local-only boundary.",
            "The CC BY 4.0 dataset license does not resolve any of the 640 compiled underlying observation rights; each row keeps this status unresolved.",
            "Reported and parser-normalized quantities are preserved with their unit bases; no toughness validity, specimen identity, service lower bound or acceptance is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="data_import",
    )]

"""Typed local row access for the CC BY corrosion-alloy metrics compilation."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterator
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, StrictInt

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .corrosion_metrics_data import read_corrosion_alloy_metrics
from .registry import ModelSpec

DATASET_ID = "corrosion-resistant-alloy-metrics"
DATASET_DOI = "10.6084/m9.figshare.13038257.v2"
LICENSE_ID = "CC-BY-4.0"
LICENSE_SCOPE = "compilation_only_underlying_observation_rights_unresolved"
SOURCE_ID = "figshare_corrosion_alloy_metrics_typed_rows"
MODEL_ID = "data.figshare_corrosion_alloy_metrics_typed_rows"
SOURCE_FILENAME = "CRA_database_Scientific_Data_Publication_12102020.xlsx"
SOURCE_MD5 = "719900ece651461def03a2cb54a33b33"
SOURCE_SHA256 = "d0ce5e9c4b42e0b5a20dbd5c4896791703c5f433ae19bc032674d5848d9d1438"
SOURCE_BYTES = 305_468


class CorrosionMetricsReadAuthorization(Contract):
    """Caller attribution and local-only computational-use declaration."""

    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    license_scope: Literal[LICENSE_SCOPE] = LICENSE_SCOPE
    attribution: str = Field(min_length=1)
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]


class CorrosionMetricObservationRow(Contract):
    """One parser-emitted long-form metric row with explicit unresolved rights lineage."""

    schema_version: Literal["matintegrity.figshare_corrosion_metric_observation_row.v1"] = (
        "matintegrity.figshare_corrosion_metric_observation_row.v1"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    dataset_doi: Literal[DATASET_DOI] = DATASET_DOI
    compilation_license_id: Literal[LICENSE_ID] = LICENSE_ID
    compilation_license_scope: Literal[LICENSE_SCOPE] = LICENSE_SCOPE
    attribution: str = Field(min_length=1)
    authorization_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_only: Literal[True] = True
    source_filename: Literal[SOURCE_FILENAME] = SOURCE_FILENAME
    source_file_bytes: StrictInt = Field(gt=0)
    source_file_md5: str = Field(pattern=r"^[a-f0-9]{32}$")
    source_workbook_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_order: StrictInt = Field(ge=0)
    source_sheet: str = Field(min_length=1)
    provider_source_row: StrictInt = Field(ge=3)
    source_number: StrictInt = Field(ge=0)
    observation_id: str = Field(min_length=1)
    source_observation_id: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    statistic: str = Field(min_length=1)
    raw_value: Any
    value_status: Literal["exact", "missing", "lower_bound", "upper_bound", "exact_text_numeric", "qualitative"]
    qualifier: str | None
    reported_value: float | None
    source_unit: str = Field(min_length=1)
    normalized_value: float | None
    normalized_unit: str = Field(min_length=1)
    potential_reference: str | None
    composition_wt_percent: dict[str, float]
    composition_raw: dict[str, Any]
    material_class: Any
    conditions: dict[str, Any]
    reference_number: StrictInt | None
    underlying_reference_doi: str | None
    underlying_reference_citation: str | None
    source_group_id: str | None
    physical_specimen_id: None = None
    underlying_observation_rights_status: Literal["unresolved"] = "unresolved"
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    ranking_inferred: Literal[False] = False
    acceptance_inferred: Literal[False] = False
    failure_probability_inferred: Literal[False] = False


class CorrosionMetricsArchiveAuditRequest(Contract):
    local_workbook_path: str = Field(min_length=1)
    authorization: CorrosionMetricsReadAuthorization


def _verify_workbook(path: Path) -> tuple[str, str, int]:
    if path.name != SOURCE_FILENAME or not path.is_file():
        raise ValueError("only the catalogued local Figshare workbook is accepted")
    size = path.stat().st_size
    if size != SOURCE_BYTES:
        raise ValueError("corrosion-metrics workbook byte count differs from the catalog pin")
    md5, sha256 = hashlib.md5(), hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(block)
            sha256.update(block)
    actual_md5, actual_sha256 = md5.hexdigest(), sha256.hexdigest()
    if actual_md5 != SOURCE_MD5 or actual_sha256 != SOURCE_SHA256:
        raise ValueError("corrosion-metrics workbook digest differs from catalog/acquisition pins")
    return actual_md5, actual_sha256, size


def _clean_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value.item() if hasattr(value, "item") else value


def _clean_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("parser emitted a malformed source mapping")
    return {str(key): _clean_scalar(item) for key, item in value.items()}


def iter_corrosion_metric_observation_rows(
    path: str | Path,
    *,
    authorization: CorrosionMetricsReadAuthorization,
) -> Iterator[CorrosionMetricObservationRow]:
    """Yield parser rows in its existing long-form sheet/row/metric order."""
    if not authorization.attribution.strip():
        raise ValueError("CC BY 4.0 compilation attribution must be nonempty")
    source = Path(path)
    file_md5, file_sha256, file_bytes = _verify_workbook(source)
    frame = read_corrosion_alloy_metrics(source, require_pinned_hash=True)
    if frame.attrs.get("source_workbook_sha256") != file_sha256:
        raise ValueError("existing parser workbook digest differs from the catalogued source")
    auth_sha256 = canonical_digest(authorization.model_dump(mode="json"))
    for order, row in enumerate(frame.itertuples(index=False), start=0):
        comp = {str(key): float(value) for key, value in _clean_mapping(row.composition_wt_percent).items()}
        composition_raw = _clean_mapping(row.composition_raw)
        conditions = _clean_mapping(row.conditions)
        values = {
            "source_order": order,
            "source_sheet": str(row.source_sheet),
            "provider_source_row": int(row.source_row),
            "source_number": int(row.source_number),
            "observation_id": str(row.observation_id),
            "source_observation_id": str(row.source_observation_id),
            "metric": str(row.metric),
            "statistic": str(row.statistic),
            "raw_value": _clean_scalar(row.raw_value),
            "value_status": str(row.value_status),
            "qualifier": _clean_scalar(row.qualifier),
            "reported_value": _clean_scalar(row.reported_value),
            "source_unit": str(row.source_unit),
            "normalized_value": _clean_scalar(row.normalized_value),
            "normalized_unit": str(row.normalized_unit),
            "potential_reference": _clean_scalar(row.potential_reference),
            "composition_wt_percent": comp,
            "composition_raw": composition_raw,
            "material_class": _clean_scalar(row.material_class),
            "conditions": conditions,
            "reference_number": _clean_scalar(row.reference_number),
            "underlying_reference_doi": _clean_scalar(row.underlying_reference_doi),
            "underlying_reference_citation": _clean_scalar(row.underlying_reference_citation),
            "source_group_id": _clean_scalar(row.source_group_id),
        }
        yield CorrosionMetricObservationRow(
            attribution=authorization.attribution,
            authorization_sha256=auth_sha256,
            source_file_bytes=file_bytes,
            source_file_md5=file_md5,
            source_workbook_sha256=file_sha256,
            **values,
            source_row_sha256=canonical_digest({
                "dataset_id": DATASET_ID,
                "source_workbook_sha256": file_sha256,
                "source_order": order,
                "record": values,
                "underlying_observation_rights_status": "unresolved",
            }),
            evidence=Evidence(
                source_id=DATASET_ID,
                origin="open_dataset",
                citation=f"{authorization.attribution}; https://doi.org/{DATASET_DOI} (CC BY 4.0 compilation license only)",
                license_id=LICENSE_ID,
                sha256=file_sha256,
            ),
        )


def audit_corrosion_metrics_workbook(request: CorrosionMetricsArchiveAuditRequest) -> Calculation:
    """Return row-count and pin metadata without exposing compiled observations."""
    if not request.authorization.attribution.strip():
        raise ValueError("CC BY 4.0 compilation attribution must be nonempty")
    source = Path(request.local_workbook_path)
    file_md5, file_sha256, file_bytes = _verify_workbook(source)
    frame = read_corrosion_alloy_metrics(source, require_pinned_hash=True)
    if frame.attrs.get("source_workbook_sha256") != file_sha256:
        raise ValueError("existing parser workbook digest differs from the catalogued source")
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "dataset_doi": DATASET_DOI,
        "compilation_license_id": LICENSE_ID,
        "compilation_license_scope": LICENSE_SCOPE,
        "attribution": request.authorization.attribution,
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "source_filename": SOURCE_FILENAME,
        "source_file_bytes": file_bytes,
        "source_file_md5": file_md5,
        "source_workbook_sha256": file_sha256,
        "long_form_metric_row_count": int(len(frame)),
        "source_observation_count": int(frame.source_observation_id.nunique()),
        "source_order_preserved": True,
        "underlying_observation_rights_status": "unresolved",
        "point_values_returned": False,
        "local_path_returned": False,
        "local_only": True,
        "material_ranking_inferred": False,
    }, notes=(
        "The dataset CC BY 4.0 declaration applies to the compilation; underlying publication observation rights remain unresolved.",
        "Metadata-only workbook audit; use iter_corrosion_metric_observation_rows for local attributed records.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CorrosionMetricsArchiveAuditRequest,
        evaluator=audit_corrosion_metrics_workbook,
        units={"source_file_bytes": "byte", "long_form_metric_row_count": "row", "source_observation_count": "row"},
        assumptions=(
            "Only the pinned CC BY compilation workbook is accepted; publisher MD5 and acquisition SHA-256 are checked before reusing the existing parser.",
            "The CC BY 4.0 declaration is limited to the compilation; underlying observation rights are explicitly unresolved and all row access stays local-only.",
            "Reported and parser-normalized values, qualifiers, source units, potential reference, conditions, citations and source order are preserved without additional fitting.",
            "No material ranking, source specimen identity, test validity, acceptance or failure probability is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="data_import",
    )]

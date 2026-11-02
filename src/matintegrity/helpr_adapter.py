"""Strict, dependency-free ingestion of reviewed Sandia HELPR life-criteria CSV output."""

from __future__ import annotations

import csv
import hashlib
import io
import math
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative

HELPR_LIFE_CRITERIA_COLUMNS = (
    "a(crit)",
    "Cycles to a(crit)",
    "Cycles to 25% a(crit)",
    "Cycles to 1/2 Nc",
    "Cycles to FAD line",
)


class HelprLifeCriteriaRecord(Contract):
    """One HELPR output row with identities missing from the provider CSV restored."""

    schema_version: Literal["matintegrity.helpr_life_criteria.v1"] = "matintegrity.helpr_life_criteria.v1"
    provider_id: Literal["sandia.helpr"] = "sandia.helpr"
    provider_version: str = Field(min_length=1)
    provider_revision: str = Field(pattern=r"^[a-f0-9]{40}$")
    analysis_id: str = Field(min_length=1)
    study_type: Literal["nominal", "probabilistic"]
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    provider_row_index: int = Field(ge=0)
    provider_reported_a_crit_m: Nonnegative | None
    provider_reported_cycles_to_a_crit: Nonnegative | None
    provider_reported_cycles_to_25_percent_a_crit: Nonnegative | None
    provider_reported_cycles_to_half_nc: Nonnegative | None
    provider_reported_cycles_to_fad_line: Nonnegative | None
    provider_a_crit_interpretation: str = Field(min_length=1)
    provider_run_warning_codes: tuple[str, ...]
    provider_run_warnings_reviewed: Literal[True]
    source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    units_reviewed: Literal[True]
    missing_value_semantics: str = Field(min_length=1)
    endpoint_semantics: Literal["model_criterion_not_observed_failure"] = (
        "model_criterion_not_observed_failure"
    )
    probability_semantics: Literal["none"] = "none"

    @model_validator(mode="after")
    def nominal_rows_are_explicit(self):
        if self.study_type == "nominal" and self.provider_row_index != 0:
            raise ValueError("nominal HELPR output must contain exactly the declared row zero")
        return self


def _optional_nonnegative(raw: str, *, column: str, row_number: int) -> float | None:
    text = raw.strip()
    if not text or text.casefold() in {"nan", "na", "n/a"}:
        return None
    try:
        value = float(text)
    except ValueError as exc:
        raise ValueError(f"HELPR row {row_number} column {column!r} is not numeric") from exc
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"HELPR row {row_number} column {column!r} must be finite and nonnegative")
    return value


def read_helpr_life_criteria_csv(
    path: str | Path,
    *,
    provider_version: str,
    provider_revision: str,
    analysis_id: str,
    study_type: Literal["nominal", "probabilistic"],
    asset_id: str,
    location_id: str,
    material_condition_id: str,
    load_case_id: str,
    sample_ids: list[str],
    provider_configuration_digest: str,
    units_reviewed: Literal[True],
    missing_value_semantics: str,
    provider_a_crit_interpretation: str,
    provider_run_warning_codes: tuple[str, ...],
    provider_run_warnings_reviewed: Literal[True],
) -> tuple[HelprLifeCriteriaRecord, ...]:
    """Read the stable v2.1.0 life-criteria export without importing HELPR.

    The provider CSV alone does not contain asset, location, material, load-case,
    sample, software revision, or configuration identities. Callers must supply
    those reviewed values; the adapter never manufactures physical specimen IDs.
    """

    source = Path(path)
    payload = source.read_bytes()
    source_digest = hashlib.sha256(payload).hexdigest()
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("HELPR life-criteria CSV must be UTF-8 text") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None:
        raise ValueError("HELPR life-criteria CSV has no header")
    if tuple(reader.fieldnames) != HELPR_LIFE_CRITERIA_COLUMNS:
        raise ValueError(
            "unsupported HELPR life-criteria header; review the provider version and output schema"
        )
    rows = list(reader)
    if not rows:
        raise ValueError("HELPR life-criteria CSV contains no result rows")
    if study_type == "nominal" and len(rows) != 1:
        raise ValueError("nominal HELPR life-criteria output must contain exactly one row")
    if len(sample_ids) != len(rows):
        raise ValueError("caller-supplied sample IDs must align one-to-one with HELPR rows")
    if len(set(sample_ids)) != len(sample_ids) or any(not value for value in sample_ids):
        raise ValueError("caller-supplied sample IDs must be nonempty and unique")

    records = []
    for index, (row, sample_id) in enumerate(zip(rows, sample_ids, strict=True)):
        parsed = {
            column: _optional_nonnegative(row[column], column=column, row_number=index)
            for column in HELPR_LIFE_CRITERIA_COLUMNS
        }
        records.append(
            HelprLifeCriteriaRecord(
                provider_version=provider_version,
                provider_revision=provider_revision,
                analysis_id=analysis_id,
                study_type=study_type,
                asset_id=asset_id,
                location_id=location_id,
                material_condition_id=material_condition_id,
                load_case_id=load_case_id,
                sample_id=sample_id,
                provider_row_index=index,
                provider_reported_a_crit_m=parsed["a(crit)"],
                provider_reported_cycles_to_a_crit=parsed["Cycles to a(crit)"],
                provider_reported_cycles_to_25_percent_a_crit=parsed["Cycles to 25% a(crit)"],
                provider_reported_cycles_to_half_nc=parsed["Cycles to 1/2 Nc"],
                provider_reported_cycles_to_fad_line=parsed["Cycles to FAD line"],
                provider_a_crit_interpretation=provider_a_crit_interpretation,
                provider_run_warning_codes=provider_run_warning_codes,
                provider_run_warnings_reviewed=provider_run_warnings_reviewed,
                source_content_sha256=source_digest,
                provider_configuration_digest=provider_configuration_digest,
                units_reviewed=units_reviewed,
                missing_value_semantics=missing_value_semantics,
            )
        )
    return tuple(records)

"""Typed access to the openly licensed CT110 weld/base corrosion-rate example."""

from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Positive
from .models.corrosion import MaterialCorrosionRateContrast


class CT110ProviderFile(Contract):
    name: str = Field(min_length=1)
    provider_md5: str = Field(pattern=r"^[a-f0-9]{32}$")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bytes: int = Field(gt=0)


class CT110Source(Contract):
    citation: str = Field(min_length=1)
    article_doi: str = Field(min_length=1)
    supplement_dois: tuple[str, ...] = Field(min_length=2)
    license: Literal["CC BY 4.0"]
    license_url: str = Field(min_length=1)
    attribution: str = Field(min_length=1)
    provider_files: tuple[CT110ProviderFile, ...] = Field(min_length=2)


class CT110WeldCorrosionObservation(Contract):
    comparison_id: str = Field(min_length=1)
    condition_group_id: str = Field(min_length=1)
    condition_signature: dict[str, str | float | int | bool]
    weld_rate_mm_year: Positive
    base_rate_mm_year: Positive
    weld_rate_m_s: Positive
    base_rate_m_s: Positive
    reported_ratio_rounded: Positive

    @model_validator(mode="after")
    def validate_rates(self):
        if not self.condition_signature or any(not key.strip() for key in self.condition_signature):
            raise ValueError("condition signature must contain non-empty field names and values")
        if any(type(value) not in {str, int, float, bool} for value in self.condition_signature.values()):
            raise ValueError("condition signature values must be flat JSON scalars")
        year_seconds = 365.25 * 24 * 60 * 60
        if abs(self.weld_rate_m_s - self.weld_rate_mm_year * 1e-3 / year_seconds) > 1e-20:
            raise ValueError("weld SI rate does not match the recorded Julian-year conversion")
        if abs(self.base_rate_m_s - self.base_rate_mm_year * 1e-3 / year_seconds) > 1e-20:
            raise ValueError("base-metal SI rate does not match the recorded Julian-year conversion")
        return self


class CT110WeldCorrosionDataset(Contract):
    schema_id: Literal["matintegrity.ct110_weld_corrosion_rate_observations.v1"]
    dataset_id: Literal["experimental-ct110-weld-corrosion-rates"]
    source: CT110Source
    material: str = Field(min_length=1)
    numerator_material_id: str = Field(min_length=1)
    reference_material_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    measurement_method: Literal["weight_loss"]
    reported_rate_unit: Literal["mm/year"]
    normalized_rate_unit: Literal["m/s"]
    physical_specimen_ids_available: Literal[False]
    replicate_counts_available: Literal[False]
    uncertainty_available: Literal[False]
    observations: tuple[CT110WeldCorrosionObservation, ...] = Field(min_length=1)
    limitations: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_identity(self):
        if self.numerator_material_id == self.reference_material_id:
            raise ValueError("dataset numerator and reference materials must differ")
        if len({row.comparison_id for row in self.observations}) != len(self.observations):
            raise ValueError("comparison IDs must be unique within the dataset")
        return self

    def contrast_input(self, comparison_id: str) -> MaterialCorrosionRateContrast:
        """Create a registry-ready descriptive contrast while retaining condition/source identity."""
        row = next((item for item in self.observations if item.comparison_id == comparison_id), None)
        if row is None:
            raise KeyError(comparison_id)
        return MaterialCorrosionRateContrast(
            comparison_id=row.comparison_id,
            numerator_material_id=self.numerator_material_id,
            reference_material_id=self.reference_material_id,
            numerator_rate_m_s=row.weld_rate_m_s,
            reference_rate_m_s=row.base_rate_m_s,
            condition_signature=row.condition_signature,
            condition_group_id=row.condition_group_id,
            source_group_id=self.source_group_id,
            measurement_method=self.measurement_method,
        )


def read_ct110_weld_corrosion_dataset(path: str | Path | None = None) -> CT110WeldCorrosionDataset:
    """Load and validate the bundled public example, or a caller-supplied compatible JSON file."""
    if path is None:
        root = files("matintegrity").joinpath("catalog_data")
        payload = root.joinpath("ct110_weld_corrosion_rates.json").read_bytes()
        catalog = json.loads(root.joinpath("datasets.json").read_text(encoding="utf-8"))
        entry = next(
            row for row in catalog["datasets"] if row["id"] == "experimental-ct110-weld-corrosion-rates"
        )
        expected = entry["derived_public_fixture"]["sha256"]
        if hashlib.sha256(payload).hexdigest() != expected:
            raise ValueError("bundled CT110 example does not match its dataset-catalog digest")
    else:
        payload = Path(path).read_bytes()
    return CT110WeldCorrosionDataset.model_validate_json(payload)

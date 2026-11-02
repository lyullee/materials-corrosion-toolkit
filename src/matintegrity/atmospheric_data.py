"""Rights-aware reader for first-year atmospheric carbon-steel corrosion data."""

from __future__ import annotations

import csv
import hashlib
import io
import math
import zipfile
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, Positive
from .units import SECONDS_PER_YEAR

DATASET_ID = "atmospheric-carbon-steel-first-year"
PINNED_ARCHIVE_SHA256 = "a1accd1ad324f7b2cc0cf9776bf60839c3f7368a8c65c7e6ea71a494e6a0ca35"

COMMON_COLUMNS = {
    "site",
    "country",
    "lat",
    "lon",
    "r_um_per_yr",
    "Cl_dep_mg_m2_d",
    "SO2_dep_mg_m2_d",
    "era5_cell",
    "T_era5_corrected_C",
    "RH_era5_pct",
    "lapse_correction_K",
    "tw80_h",
    "Tw80_C",
    "precipitation_mm",
}
PROGRAMME_COLUMNS = COMMON_COLUMNS | {
    "source",
    "programme",
    "exposure_period",
    "site_id",
    "Cl_assumed_zero",
}
INDEPENDENT_COLUMNS = COMMON_COLUMNS | {
    "study",
    "exposure_years",
    "tier",
    "rate_source",
    "doi",
    "note",
}


class AtmosphericCorrosionObservation(Contract):
    schema_version: Literal["matintegrity.atmospheric_corrosion_observation.v1"] = (
        "matintegrity.atmospheric_corrosion_observation.v1"
    )
    dataset_id: Literal["atmospheric-carbon-steel-first-year"] = DATASET_ID
    observation_id: str = Field(min_length=1)
    provider_partition: Literal["programme", "independent"]
    provider_source_row: int = Field(ge=2)
    source_group_id: str = Field(min_length=1)
    provider_source_id: str = Field(min_length=1)
    programme_id: str | None = None
    provider_site_id: str | None = None
    physical_specimen_id: str | None = None
    country: str = Field(min_length=1)
    site: str = Field(min_length=1)
    latitude_deg: float = Field(ge=-90.0, le=90.0)
    longitude_deg: float = Field(ge=-180.0, le=180.0)
    exposure_label: str | None = None
    reported_first_year_rate_um_year: Positive
    first_year_loss_m: Positive
    equivalent_first_year_rate_m_s: Positive
    chloride_deposition_mg_m2_day: Nonnegative | None = None
    sulfur_dioxide_deposition_mg_m2_day: Nonnegative | None = None
    chloride_assumed_zero_by_provider: bool | None = None
    provider_tier: Literal["A", "B", "C"] | None = None
    provider_rate_source: Literal["table", "figure"] | None = None
    underlying_source_doi: str | None = None
    provider_note: str | None = None
    era5_cell_id: str = Field(min_length=1)
    era5_corrected_temperature_K: Positive
    era5_relative_humidity_fraction: float = Field(ge=0.0, le=1.0)
    era5_wet_hours_rh80_per_year: Nonnegative
    era5_wet_hour_mean_temperature_K: Positive
    era5_annual_precipitation_m: Nonnegative
    climate_covariate_origin: Literal["ERA5 via Open-Meteo; provider harmonisation"] = (
        "ERA5 via Open-Meteo; provider harmonisation"
    )
    source_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    observation_redistribution_status: Literal["source_specific_review_required"] = (
        "source_specific_review_required"
    )

    @model_validator(mode="after")
    def partition_fields(self):
        if self.provider_partition == "programme":
            if self.programme_id is None or self.provider_site_id is None:
                raise ValueError("programme observations require programme and provider site identifiers")
            if self.provider_tier is not None or self.provider_rate_source is not None:
                raise ValueError("provider tier and rate source belong only to independent records")
        else:
            if self.programme_id is not None or self.chloride_assumed_zero_by_provider is not None:
                raise ValueError("programme fields cannot be assigned to independent records")
            if self.provider_tier is None or self.provider_rate_source is None:
                raise ValueError("independent observations require provider tier and rate source")
        if not math.isclose(
            self.first_year_loss_m,
            self.reported_first_year_rate_um_year * 1e-6,
            rel_tol=1e-12,
            abs_tol=0.0,
        ):
            raise ValueError("first-year loss must preserve the provider micrometre-per-year value")
        return self


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _member(archive: zipfile.ZipFile, suffix: str) -> zipfile.ZipInfo:
    candidates = []
    seen = set()
    for info in archive.infolist():
        path = PurePosixPath(info.filename.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts or info.filename in seen:
            raise ValueError("atmospheric archive contains an unsafe or duplicate member path")
        seen.add(info.filename)
        if info.flag_bits & 0x1:
            raise ValueError("encrypted atmospheric archive members are unsupported")
        if not info.is_dir() and path.name == suffix:
            candidates.append(info)
    if len(candidates) != 1:
        raise ValueError(f"atmospheric archive must contain exactly one {suffix}")
    if candidates[0].file_size > 8 * 1024 * 1024:
        raise ValueError("atmospheric table exceeds the bounded reader size")
    return candidates[0]


def _required_text(row: dict[str, str], name: str) -> str:
    value = row[name].strip()
    if not value:
        raise ValueError(f"atmospheric source field {name} is required")
    return value


def _number(row: dict[str, str], name: str, *, optional: bool = False) -> float | None:
    raw = row[name].strip()
    if optional and not raw:
        return None
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError(f"atmospheric source field {name} must be numeric") from error
    if not math.isfinite(value):
        raise ValueError(f"atmospheric source field {name} must be finite")
    return value


def _boolean(row: dict[str, str], name: str) -> bool:
    value = row[name].strip().lower()
    if value not in {"true", "false"}:
        raise ValueError(f"atmospheric source field {name} must be true or false")
    return value == "true"


def _read_rows(archive: zipfile.ZipFile, name: str, required: set[str]) -> list[dict[str, str]]:
    info = _member(archive, name)
    text = archive.read(info).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or not required <= set(reader.fieldnames):
        raise ValueError(f"atmospheric {name} schema changed")
    rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError(f"atmospheric {name} contains overflow columns")
    return rows


def _observation(
    row: dict[str, str],
    *,
    partition: Literal["programme", "independent"],
    source_row: int,
    archive_sha256: str,
) -> AtmosphericCorrosionObservation:
    rate = _number(row, "r_um_per_yr")
    temperature = _number(row, "T_era5_corrected_C")
    wet_temperature = _number(row, "Tw80_C") + _number(row, "lapse_correction_K")
    if partition == "programme":
        source = _required_text(row, "source")
        programme = _required_text(row, "programme")
        site_id = _required_text(row, "site_id")
        source_group = f"programme:{source}"
        exposure_label = row["exposure_period"].strip() or None
        tier = rate_source = doi = note = None
        assumed_zero = _boolean(row, "Cl_assumed_zero")
        observation_id = f"programme-row-{source_row}"
    else:
        source = _required_text(row, "study")
        programme = site_id = None
        source_group = f"independent-study:{source}"
        exposure_label = row["exposure_years"].strip() or None
        tier = _required_text(row, "tier")
        rate_source = _required_text(row, "rate_source")
        doi = row["doi"].strip() or None
        note = row["note"].strip() or None
        assumed_zero = None
        observation_id = f"independent-row-{source_row}"
    return AtmosphericCorrosionObservation(
        observation_id=observation_id,
        provider_partition=partition,
        provider_source_row=source_row,
        source_group_id=source_group,
        provider_source_id=source,
        programme_id=programme,
        provider_site_id=site_id,
        country=_required_text(row, "country"),
        site=_required_text(row, "site"),
        latitude_deg=_number(row, "lat"),
        longitude_deg=_number(row, "lon"),
        exposure_label=exposure_label,
        reported_first_year_rate_um_year=rate,
        first_year_loss_m=rate * 1e-6,
        equivalent_first_year_rate_m_s=rate * 1e-6 / SECONDS_PER_YEAR,
        chloride_deposition_mg_m2_day=_number(row, "Cl_dep_mg_m2_d", optional=True),
        sulfur_dioxide_deposition_mg_m2_day=_number(row, "SO2_dep_mg_m2_d", optional=True),
        chloride_assumed_zero_by_provider=assumed_zero,
        provider_tier=tier,
        provider_rate_source=rate_source,
        underlying_source_doi=doi,
        provider_note=note,
        era5_cell_id=_required_text(row, "era5_cell"),
        era5_corrected_temperature_K=temperature + 273.15,
        era5_relative_humidity_fraction=_number(row, "RH_era5_pct") / 100.0,
        era5_wet_hours_rh80_per_year=_number(row, "tw80_h"),
        era5_wet_hour_mean_temperature_K=wet_temperature + 273.15,
        era5_annual_precipitation_m=_number(row, "precipitation_mm") / 1000.0,
        source_archive_sha256=archive_sha256,
    )


def read_atmospheric_corrosion_observations(
    path: str | Path,
    *,
    partition: Literal["programme", "independent", "both"] = "both",
    require_pinned_hash: bool = True,
) -> tuple[AtmosphericCorrosionObservation, ...]:
    """Read provider programme and independent rows without merging their evidence roles."""

    source = Path(path)
    archive_sha256 = _sha256(source)
    if require_pinned_hash and archive_sha256 != PINNED_ARCHIVE_SHA256:
        raise ValueError("atmospheric archive hash differs from the reviewed dataset revision")
    observations = []
    with zipfile.ZipFile(source) as archive:
        if partition in {"programme", "both"}:
            rows = _read_rows(archive, "programme_records_617.csv", PROGRAMME_COLUMNS)
            observations.extend(
                _observation(
                    row,
                    partition="programme",
                    source_row=index,
                    archive_sha256=archive_sha256,
                )
                for index, row in enumerate(rows, 2)
            )
        if partition in {"independent", "both"}:
            rows = _read_rows(archive, "independent_records_106.csv", INDEPENDENT_COLUMNS)
            observations.extend(
                _observation(
                    row,
                    partition="independent",
                    source_row=index,
                    archive_sha256=archive_sha256,
                )
                for index, row in enumerate(rows, 2)
            )
    return tuple(observations)

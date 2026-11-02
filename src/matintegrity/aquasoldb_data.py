"""Rights-aware local reader for the versioned AquaSolDB gas-solubility compilation."""

from __future__ import annotations

import csv
import hashlib
import io
import math
import zipfile
from pathlib import Path
from typing import Iterable, Iterator, Literal

from pydantic import Field, field_validator, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from .models.co2_fixed_fugacity_equilibrium import Co2HenrySolubilityRecord

DATASET_ID = "aquasoldb-gas-solubility-v2-1"
DATASET_VERSION_DOI = "10.5281/zenodo.23470595"
DATASET_LICENSE = "CC-BY-4.0 compilation only"
PINNED_ARCHIVE_SHA256 = "dd78394582ed1d41745976d0a631c976a460d1d777122a1c600e2a4c04c550bf"
PINNED_ARCHIVE_MD5 = "d96c914f8335a3678b47b90e45eed7a2"
PINNED_ARCHIVE_BYTES = 3_348_667
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 64 * 1024 * 1024
MAX_MEMBER_BYTES = 8 * 1024 * 1024
SOLUBILITY_COLUMNS = (
    "point_id",
    "gas",
    "temperature_K",
    "pressure_MPa",
    "pressure_basis",
    "salt",
    "salt_molality",
    "salt_composition",
    "m_Na",
    "m_Cl",
    "m_K",
    "m_Ca",
    "m_Mg",
    "m_SO4",
    "solubility_mol_per_kgw",
    "status",
    "status_reason",
    "flags",
    "method",
    "source_id",
)


class AquaSolDBCo2SolubilityObservation(Contract):
    """One caller-selected CO2 solubility row; not a Henry coefficient or corrosion rate."""

    schema_version: Literal["matintegrity.aquasoldb_co2_solubility_observation.v1"] = (
        "matintegrity.aquasoldb_co2_solubility_observation.v1"
    )
    dataset_id: Literal["aquasoldb-gas-solubility-v2-1"] = DATASET_ID
    dataset_version_doi: Literal["10.5281/zenodo.23470595"] = DATASET_VERSION_DOI
    dataset_license_scope: Literal["CC-BY-4.0 compilation only"] = DATASET_LICENSE
    compilation_attribution: Literal["Abd and Abushaikha (2026), AquaSolDB v2.1"] = (
        "Abd and Abushaikha (2026), AquaSolDB v2.1"
    )
    source_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    point_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    temperature_K: Positive | None = None
    pressure_MPa: Nonnegative | None = None
    pressure_basis: str = Field(min_length=1)
    salt: str = Field(min_length=1)
    salt_molality_mol_per_kgw: Nonnegative | None = None
    salt_composition_as_reported: str | None = None
    sodium_molality_mol_per_kgw: Nonnegative | None = None
    chloride_molality_mol_per_kgw: Nonnegative | None = None
    potassium_molality_mol_per_kgw: Nonnegative | None = None
    calcium_molality_mol_per_kgw: Nonnegative | None = None
    magnesium_molality_mol_per_kgw: Nonnegative | None = None
    sulfate_molality_mol_per_kgw: Nonnegative | None = None
    solubility_mol_per_kg_water: Nonnegative | None
    status: Literal["measured", "calculated", "no_value"]
    flags: tuple[str, ...]
    method: str = Field(min_length=1)
    source_specific_original_paper_citation_required: Literal[True] = True
    source_specific_rights_review_required: Literal[True] = True
    henry_coefficient_derived: Literal[False] = False
    corrosion_calibration_ready: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @field_validator("flags")
    @classmethod
    def unique_nonblank_flags(cls, value):
        if any(not flag.strip() for flag in value) or len(set(value)) != len(value):
            raise ValueError("AquaSolDB flags must be nonblank and unique")
        return value

    @model_validator(mode="after")
    def row_consistency(self):
        if self.status == "no_value" and self.solubility_mol_per_kg_water is not None:
            raise ValueError("no-value source records cannot carry a numeric solubility")
        if self.status != "no_value" and self.solubility_mol_per_kg_water is None:
            raise ValueError("numeric-status source records require a solubility value")
        return self


class AquaSolDBCo2SolubilityQuery(Contract):
    """Explicit filters for selecting caller-reviewed CO2 records from the local compilation."""

    temperature_range_K: tuple[Positive, Positive] | None = None
    pressure_range_MPa: tuple[Nonnegative, Nonnegative] | None = None
    pressure_basis: str | None = None
    salt: str | None = None
    source_ids: tuple[str, ...] | None = None
    allowed_statuses: tuple[Literal["measured", "calculated", "no_value"], ...] = ("measured",)
    exclude_any_flagged_records: bool = True
    required_flags: tuple[str, ...] = ()
    require_temperature_and_pressure: bool = True
    maximum_records: int = Field(default=500, ge=1, le=100_000)

    @model_validator(mode="after")
    def valid_selection(self):
        if self.temperature_range_K and self.temperature_range_K[0] > self.temperature_range_K[1]:
            raise ValueError("temperature range lower bound must not exceed its upper bound")
        if self.pressure_range_MPa and self.pressure_range_MPa[0] > self.pressure_range_MPa[1]:
            raise ValueError("pressure range lower bound must not exceed its upper bound")
        if not self.allowed_statuses or len(set(self.allowed_statuses)) != len(self.allowed_statuses):
            raise ValueError("at least one unique row status must be allowed")
        if self.required_flags and self.exclude_any_flagged_records:
            raise ValueError("required_flags cannot be combined with exclude_any_flagged_records")
        for values_name in ("source_ids", "required_flags"):
            values = getattr(self, values_name)
            if values is not None and (
                any(not value.strip() for value in values) or len(set(values)) != len(values)
            ):
                raise ValueError(f"{values_name} entries must be nonblank and unique")
        return self


class AquaSolDBFixedFugacityComparisonInput(Contract):
    """Compare one measured compilation observation with an independent caller-supplied Henry model."""

    observation: AquaSolDBCo2SolubilityObservation
    henry: Co2HenrySolubilityRecord
    co2_fugacity_Pa: Positive
    fugacity_temperature_K: Positive
    fugacity_provider_id: str = Field(min_length=1)
    fugacity_provider_revision: str = Field(min_length=1)
    fugacity_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    fugacity_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    solvent_composition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    solvent_water_mass_concentration_kg_per_L: Positive
    expanded_comparison_uncertainty_mol_L: Positive
    expanded_comparison_uncertainty_basis: str = Field(min_length=1)
    temperature_match_tolerance_K: Nonnegative = 0.0
    comparison_review_id: str = Field(min_length=1)
    observation_record_reviewed: bool
    pressure_and_fugacity_basis_reviewed: bool
    solvent_composition_and_water_mass_concentration_reviewed: bool
    Henry_record_independence_reviewed: bool
    Henry_convention_and_activity_basis_reviewed: bool
    original_source_citation_and_rights_reviewed: bool
    observation_flags_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_identity_fields(self):
        for field_name in (
            "fugacity_provider_id",
            "fugacity_provider_revision",
            "expanded_comparison_uncertainty_basis",
            "comparison_review_id",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} cannot be blank")
        return self


def select_aquasoldb_co2_records(
    observations: Iterable[AquaSolDBCo2SolubilityObservation],
    query: AquaSolDBCo2SolubilityQuery,
) -> tuple[AquaSolDBCo2SolubilityObservation, ...]:
    """Apply exact inclusive filters; fail on overflow rather than silently truncating results."""

    if not isinstance(query, AquaSolDBCo2SolubilityQuery):
        raise TypeError("an explicit AquaSolDBCo2SolubilityQuery is required")
    selected = []
    seen_point_ids = set()
    source_ids = set(query.source_ids) if query.source_ids is not None else None
    for observation in observations:
        if not isinstance(observation, AquaSolDBCo2SolubilityObservation):
            raise TypeError("AquaSolDB selection accepts only typed observation records")
        if observation.point_id in seen_point_ids:
            raise ValueError("duplicate AquaSolDB point_id in selection input")
        seen_point_ids.add(observation.point_id)
        if observation.status not in query.allowed_statuses:
            continue
        if query.exclude_any_flagged_records and observation.flags:
            continue
        if not set(query.required_flags).issubset(observation.flags):
            continue
        if query.pressure_basis is not None and observation.pressure_basis != query.pressure_basis:
            continue
        if query.salt is not None and observation.salt != query.salt:
            continue
        if source_ids is not None and observation.source_id not in source_ids:
            continue
        if query.require_temperature_and_pressure and (
            observation.temperature_K is None or observation.pressure_MPa is None
        ):
            continue
        if query.temperature_range_K is not None:
            if observation.temperature_K is None or not (
                query.temperature_range_K[0] <= observation.temperature_K <= query.temperature_range_K[1]
            ):
                continue
        if query.pressure_range_MPa is not None:
            if observation.pressure_MPa is None or not (
                query.pressure_range_MPa[0] <= observation.pressure_MPa <= query.pressure_range_MPa[1]
            ):
                continue
        selected.append(observation)
        if len(selected) > query.maximum_records:
            raise ValueError(
                "selection exceeds maximum_records; narrow the query or raise its explicit limit"
            )
    return tuple(selected)


def compare_aquasoldb_to_fixed_fugacity_model(x: AquaSolDBFixedFugacityComparisonInput) -> Calculation:
    """Compare measured molality to an independent Henry/fugacity concentration without fitting."""

    review_fields = (
        "observation_record_reviewed",
        "pressure_and_fugacity_basis_reviewed",
        "solvent_composition_and_water_mass_concentration_reviewed",
        "Henry_record_independence_reviewed",
        "Henry_convention_and_activity_basis_reviewed",
        "original_source_citation_and_rights_reviewed",
        "observation_flags_reviewed",
    )
    missing_reviews = [field for field in review_fields if not getattr(x, field)]
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values={"point_id": x.observation.point_id, "missing_reviews": missing_reviews},
            notes=("All source, pressure-basis, solvent, independence and flag reviews are required.",),
        )

    row = x.observation
    if row.status != "measured" or row.solubility_mol_per_kg_water is None:
        return Calculation(
            status="needs_data",
            values={"point_id": row.point_id, "reason": "numeric_measured_observation_required"},
            notes=("Calculated and no-value compilation rows are not used as measured comparison targets.",),
        )
    if row.pressure_basis != "partial_CO2":
        return Calculation(
            status="needs_data",
            values={"point_id": row.point_id, "reason": "CO2_partial_pressure_basis_required"},
            notes=(
                "A total-pressure row does not identify CO2 fugacity without source-specific gas composition.",
            ),
        )
    if row.temperature_K is None or row.pressure_MPa is None:
        return Calculation(
            status="needs_data",
            values={"point_id": row.point_id, "reason": "temperature_and_pressure_required"},
            notes=("Missing provider temperature or pressure is preserved and blocks this comparison.",),
        )
    if abs(x.henry.temperature_K - row.temperature_K) > x.temperature_match_tolerance_K:
        return Calculation(
            status="needs_data",
            values={"point_id": row.point_id, "reason": "Henry_temperature_mismatch"},
            notes=("No Henry coefficient temperature interpolation or extrapolation is performed.",),
        )
    if abs(x.fugacity_temperature_K - row.temperature_K) > x.temperature_match_tolerance_K:
        return Calculation(
            status="needs_data",
            values={"point_id": row.point_id, "reason": "fugacity_temperature_mismatch"},
            notes=(
                "The fugacity state must match the measurement temperature within the declared tolerance.",
            ),
        )
    if x.henry.convention != "aqueous_CO2star_concentration_over_gas_fugacity":
        return Calculation(
            status="needs_data",
            values={"point_id": row.point_id, "reason": "unsupported_Henry_convention"},
            notes=(
                "The comparison requires the explicit aqueous CO2-star concentration over gas-fugacity convention.",
            ),
        )
    if x.solvent_composition_sha256 != x.henry.solvent_composition_sha256:
        return Calculation(
            status="needs_data",
            values={"point_id": row.point_id, "reason": "solvent_or_source_context_not_matched"},
            notes=("The caller must identify and review the exact solvent represented by the Henry record.",),
        )

    measured_mol_L = row.solubility_mol_per_kg_water * x.solvent_water_mass_concentration_kg_per_L
    predicted_mol_L = x.henry.coefficient_mol_L_Pa * x.co2_fugacity_Pa
    residual = predicted_mol_L - measured_mol_L
    normalized_residual = abs(residual) / x.expanded_comparison_uncertainty_mol_L
    return Calculation(
        values={
            "dataset_id": row.dataset_id,
            "dataset_version_doi": row.dataset_version_doi,
            "compilation_attribution": row.compilation_attribution,
            "source_archive_sha256": row.source_archive_sha256,
            "point_id": row.point_id,
            "original_source_id": row.source_id,
            "original_source_citation_and_rights_reviewed": x.original_source_citation_and_rights_reviewed,
            "observation_flags": row.flags,
            "temperature_K": row.temperature_K,
            "pressure_MPa": row.pressure_MPa,
            "pressure_basis": row.pressure_basis,
            "salt": row.salt,
            "solvent_composition_sha256": x.solvent_composition_sha256,
            "solubility_mol_per_kg_water": row.solubility_mol_per_kg_water,
            "solvent_water_mass_concentration_kg_per_L": x.solvent_water_mass_concentration_kg_per_L,
            "measured_co2_concentration_mol_L": measured_mol_L,
            "co2_fugacity_Pa": x.co2_fugacity_Pa,
            "fugacity_provider_id": x.fugacity_provider_id,
            "fugacity_provider_revision": x.fugacity_provider_revision,
            "fugacity_configuration_digest": x.fugacity_configuration_digest,
            "fugacity_record_digest": x.fugacity_record_digest,
            "henry_coefficient_mol_L_Pa": x.henry.coefficient_mol_L_Pa,
            "henry_provider_id": x.henry.provider_id,
            "henry_provider_revision": x.henry.provider_revision,
            "henry_record_digest": x.henry.record_digest,
            "predicted_co2_concentration_mol_L": predicted_mol_L,
            "predicted_minus_measured_mol_L": residual,
            "expanded_comparison_uncertainty_mol_L": x.expanded_comparison_uncertainty_mol_L,
            "expanded_comparison_uncertainty_basis": x.expanded_comparison_uncertainty_basis,
            "absolute_residual_over_declared_expanded_uncertainty": normalized_residual,
            "comparison_review_id": x.comparison_review_id,
            "evaluation_method": "caller_supplied_Henry_coefficient_times_caller_supplied_CO2_fugacity",
        },
        notes=(
            "The comparison checks one reported solubility record against an independently supplied Henry/fugacity state; it does not fit or revise the Henry coefficient.",
            "The caller supplies the water mass per solution volume conversion and the combined expanded comparison uncertainty; no CoolProp density or uncertainty assumptions are inserted.",
            "This single-record comparison is not broad validation, a corrosion-rate model, lifetime estimate, risk probability or acceptance decision.",
        ),
    )


def _optional_number(row: dict[str, str], column: str) -> float | None:
    raw = row.get(column, "")
    if raw == "":
        return None
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError(f"non-finite value in AquaSolDB column {column}")
    return value


def _archive_members(archive: zipfile.ZipFile) -> tuple[str, str]:
    members = [member for member in archive.infolist() if not member.is_dir()]
    if sum(member.file_size for member in members) > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
        raise ValueError("AquaSolDB archive exceeds the uncompressed size limit")
    for member in members:
        path = Path(member.filename)
        if path.is_absolute() or ".." in path.parts or "\\" in member.filename:
            raise ValueError("AquaSolDB archive contains an unsafe member path")
        if member.file_size > MAX_MEMBER_BYTES:
            raise ValueError("AquaSolDB archive contains a member larger than the configured limit")
        if member.flag_bits & 0x1:
            raise ValueError("encrypted AquaSolDB archive members are unsupported")
        if (member.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError("symbolic-link AquaSolDB archive members are unsupported")
    candidates = [member.filename for member in members if member.filename.endswith("/csv/solubility.csv")]
    if len(candidates) != 1:
        raise ValueError("AquaSolDB archive must contain exactly one csv/solubility.csv")
    return candidates[0], candidates[0].split("/csv/", 1)[0]


def iter_aquasoldb_co2_solubility(
    archive_path: str | Path,
) -> Iterator[AquaSolDBCo2SolubilityObservation]:
    """Read CO2 records from a caller-held exact archive; never extract or export it."""

    path = Path(archive_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    archive_sha256 = hasher.hexdigest()
    if archive_sha256 != PINNED_ARCHIVE_SHA256:
        raise ValueError("AquaSolDB archive SHA-256 does not match the pinned v2.1 release")

    with zipfile.ZipFile(path) as archive:
        member_name, _ = _archive_members(archive)
        with archive.open(member_name) as binary_stream:
            text_stream = io.TextIOWrapper(binary_stream, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(text_stream)
            if tuple(reader.fieldnames or ()) != SOLUBILITY_COLUMNS:
                raise ValueError("AquaSolDB solubility table schema does not match the pinned reader")
            evidence = (
                Evidence(
                    source_id=DATASET_ID,
                    origin="open_dataset",
                    citation=(
                        "Abd, A.; Abushaikha, A. (2026), AquaSolDB v2.1, "
                        "https://doi.org/10.5281/zenodo.23470595; cite the original source paper by source_id"
                    ),
                    license_id=DATASET_LICENSE,
                    sha256=archive_sha256,
                ),
            )
            for index, row in enumerate(reader, start=2):
                if None in row:
                    raise ValueError(f"unexpected extra cells in AquaSolDB solubility row {index}")
                if row.get("gas") != "CO2":
                    continue
                raw_flags = row.get("flags", "")
                flags = tuple(part.strip() for part in raw_flags.split(";") if part.strip())
                solubility = _optional_number(row, "solubility_mol_per_kgw")
                yield AquaSolDBCo2SolubilityObservation(
                    source_archive_sha256=archive_sha256,
                    point_id=row["point_id"],
                    source_id=row["source_id"],
                    temperature_K=_optional_number(row, "temperature_K"),
                    pressure_MPa=_optional_number(row, "pressure_MPa"),
                    pressure_basis=row["pressure_basis"],
                    salt=row["salt"],
                    salt_molality_mol_per_kgw=_optional_number(row, "salt_molality"),
                    salt_composition_as_reported=row["salt_composition"] or None,
                    sodium_molality_mol_per_kgw=_optional_number(row, "m_Na"),
                    chloride_molality_mol_per_kgw=_optional_number(row, "m_Cl"),
                    potassium_molality_mol_per_kgw=_optional_number(row, "m_K"),
                    calcium_molality_mol_per_kgw=_optional_number(row, "m_Ca"),
                    magnesium_molality_mol_per_kgw=_optional_number(row, "m_Mg"),
                    sulfate_molality_mol_per_kgw=_optional_number(row, "m_SO4"),
                    solubility_mol_per_kg_water=solubility,
                    status=row["status"],
                    flags=flags,
                    method=row["method"],
                    evidence=evidence,
                )

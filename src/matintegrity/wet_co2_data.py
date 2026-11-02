"""Rights- and provenance-aware contracts for a wet-CO2 compilation."""

from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, field_validator, model_validator

from .contracts import Calculation, Contract, Evidence, Fraction, Nonnegative, Positive

DATASET_ID = "heterogeneous-wet-co2-corrosion"
PINNED_SHA256 = "8581f6e29e12956f2fbf4fb1d46cd659540bf6878bf30beb48f340e4c9ca546e"
SIMULATION_DATASET_ID = "norsok-m506-simulation-grid"
SIMULATION_DATASET_DOI = "10.17632/4nydhxjymw.1"
SIMULATION_PINNED_SHA256 = "da4548f34ffb9c4fac2516b9d40eab18d57f6111f48f3aeb051ab092ccba2eae"
SIMULATION_SOURCE_GROUP_ID = f"doi:{SIMULATION_DATASET_DOI}"
ASSOCIATED_PAPER_DOI = "10.21203/rs.3.rs-8896642/v1"
ASSOCIATED_PAPER_UNIT_BASIS_ID = f"doi:{ASSOCIATED_PAPER_DOI}#table-1"
JULIAN_YEAR_SECONDS = 365.25 * 24.0 * 60.0 * 60.0
HEADERS = (
    "Temperature",
    "Flow velocity",
    "CO2 pressure",
    "Internal pressure",
    "Corrosion Inhibitor efficiency",
    "Shear stress",
    "pH",
    "Corrosion rate",
)
SIMULATION_UNIT_TABLE = (
    ("Parameter", "Unit"),
    ("Temperature", "oC"),
    ("Flow velocity", "m/s"),
    ("CO2 pressure", "bar"),
    ("Internal pressure", "bar"),
    ("Inhibitor efficiency", "%"),
    ("Shear stress", "Pa"),
    ("Corrosion rate", "mm/yr"),
)


class UnresolvedWetCo2CompilationRow(Contract):
    """One provider row without invented units, specimen identity or data type."""

    schema_version: Literal["matintegrity.unresolved_wet_co2_compilation_row.v1"] = (
        "matintegrity.unresolved_wet_co2_compilation_row.v1"
    )
    dataset_id: Literal["heterogeneous-wet-co2-corrosion"] = DATASET_ID
    provider_source_row: int = Field(ge=2)
    observation_id: str = Field(min_length=1)
    source_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    raw_temperature: float
    raw_flow_velocity: Nonnegative
    raw_co2_pressure: Nonnegative
    raw_internal_pressure: Nonnegative | None = None
    raw_corrosion_inhibitor_efficiency: float | None = None
    raw_shear_stress: Nonnegative | None = None
    raw_ph: float
    raw_corrosion_rate: Nonnegative
    provider_units_status: Literal["not_supplied"] = "not_supplied"
    provider_data_type: Literal["unresolved_field_simulated_or_experimental"] = (
        "unresolved_field_simulated_or_experimental"
    )
    provider_source_group_id: None = None
    physical_specimen_id: None = None
    material_condition_id: None = None
    exposure_duration_s: None = None
    mechanistic_calibration_ready: Literal[False] = False
    observation_redistribution_status: Literal["underlying_source_review_required"] = (
        "underlying_source_review_required"
    )

    @model_validator(mode="after")
    def unresolved_semantics(self):
        if not 0.0 <= self.raw_ph <= 14.0:
            raise ValueError("raw wet-CO2 pH must remain in the conventional zero-to-fourteen range")
        if self.raw_corrosion_inhibitor_efficiency is not None and not (
            0.0 <= self.raw_corrosion_inhibitor_efficiency <= 100.0
        ):
            raise ValueError("raw inhibitor efficiency must remain between zero and one hundred")
        return self


class WetCo2SimulationSourceMatch(Contract):
    """Exact crosswalk from a compilation row to the licensed simulation workbook."""

    schema_version: Literal["matintegrity.wet_co2_simulation_source_match.v1"] = (
        "matintegrity.wet_co2_simulation_source_match.v1"
    )
    compilation_dataset_id: Literal["heterogeneous-wet-co2-corrosion"] = DATASET_ID
    compilation_provider_source_row: int = Field(ge=2)
    compilation_observation_id: str = Field(min_length=1)
    compilation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_dataset_id: Literal["norsok-m506-simulation-grid"] = SIMULATION_DATASET_ID
    source_dataset_doi: Literal["10.17632/4nydhxjymw.1"] = SIMULATION_DATASET_DOI
    source_provider_row: int = Field(ge=2)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_license: Literal["CC-BY-4.0"] = "CC-BY-4.0"
    source_group_id: Literal["doi:10.17632/4nydhxjymw.1"] = SIMULATION_SOURCE_GROUP_ID
    match_basis: Literal["exact_position_header_and_eight_numeric_values"] = (
        "exact_position_header_and_eight_numeric_values"
    )
    provider_data_type: Literal["simulated_model_output"] = "simulated_model_output"
    generator_basis: Literal["provider_reported_norsok_m506_monte_carlo"] = (
        "provider_reported_norsok_m506_monte_carlo"
    )
    physical_specimen_id: None = None
    independent_physical_observation: Literal[False] = False
    physical_corrosion_calibration_ready: Literal[False] = False
    public_surrogate_release_review_required: Literal[True] = True


class WetCo2SimulationGridRow(Contract):
    """One attributed SI row from the licensed model-generated NORSOK dataset."""

    schema_version: Literal["matintegrity.wet_co2_simulation_grid_row.v1"] = (
        "matintegrity.wet_co2_simulation_grid_row.v1"
    )
    dataset_id: Literal["norsok-m506-simulation-grid"] = SIMULATION_DATASET_ID
    dataset_doi: Literal["10.17632/4nydhxjymw.1"] = SIMULATION_DATASET_DOI
    provider_row: int = Field(ge=2)
    source_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_data_type: Literal["simulated_model_output"] = "simulated_model_output"
    source_group_id: Literal["doi:10.17632/4nydhxjymw.1"] = SIMULATION_SOURCE_GROUP_ID
    temperature_K: Positive
    flow_velocity_m_s: Nonnegative
    co2_pressure_Pa: Nonnegative
    internal_pressure_Pa: Nonnegative
    corrosion_inhibitor_efficiency_fraction: Nonnegative
    shear_stress_Pa: Nonnegative
    ph: float
    corrosion_rate_m_s: Nonnegative
    physical_specimen_id: None = None
    independent_physical_observation: Literal[False] = False
    empirical_calibration_ready: Literal[False] = False
    physical_corrosion_calibration_ready: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_simulation_row(self):
        if not 0.0 <= self.corrosion_inhibitor_efficiency_fraction <= 1.0:
            raise ValueError("inhibitor efficiency fraction must be between zero and one")
        if not 0.0 <= self.ph <= 14.0:
            raise ValueError("wet-CO2 pH must remain in the conventional zero-to-fourteen range")
        if not any(
            item.source_id == self.dataset_id
            and item.origin == "open_dataset"
            and item.license_id == "CC-BY-4.0"
            and item.sha256 == self.source_archive_sha256
            for item in self.evidence
        ):
            raise ValueError(
                "simulation row source_archive_sha256 must match its dataset evidence SHA-256 and CC-BY-4.0 source"
            )
        return self


class WetCo2SimulationGridSummary(Contract):
    """Descriptive equal-row statistics for a caller-selected subset of model outputs."""

    rows: tuple[WetCo2SimulationGridRow, ...] = Field(min_length=1, max_length=243)
    quantile_levels: tuple[Fraction, ...] = (0.05, 0.25, 0.5, 0.75, 0.95)

    @model_validator(mode="after")
    def coherent_provider_subset(self):
        if len({row.provider_row for row in self.rows}) != len(self.rows):
            raise ValueError("simulation summary provider rows must be unique")
        for field in ("dataset_id", "source_group_id", "source_archive_sha256"):
            if len({getattr(row, field) for row in self.rows}) != 1:
                raise ValueError(f"simulation summary rows must share {field}")
        if any(
            not any(
                item.source_id == row.dataset_id
                and item.origin == "open_dataset"
                and item.license_id == "CC-BY-4.0"
                and item.sha256 == row.source_archive_sha256
                for item in row.evidence
            )
            for row in self.rows
        ):
            raise ValueError("every summarized row needs matching CC-BY source evidence and digest")
        if any(a >= b for a, b in zip(self.quantile_levels, self.quantile_levels[1:], strict=False)):
            raise ValueError("summary quantile levels must be strictly increasing")
        return self


def summarize_wet_co2_simulation_grid(x: WetCo2SimulationGridSummary) -> Calculation:
    """Summarize supplied model-output rows without assigning probability semantics."""

    fields = (
        "temperature_K",
        "flow_velocity_m_s",
        "co2_pressure_Pa",
        "internal_pressure_Pa",
        "corrosion_inhibitor_efficiency_fraction",
        "shear_stress_Pa",
        "ph",
        "corrosion_rate_m_s",
    )
    summaries = {}
    for field in fields:
        values = np.asarray([getattr(row, field) for row in x.rows], dtype=float)
        summaries[field] = {
            "minimum": float(np.min(values)),
            "maximum": float(np.max(values)),
            "arithmetic_mean": float(np.mean(values)),
            "equal_row_quantiles": [
                float(value) for value in np.quantile(values, x.quantile_levels, method="linear")
            ],
        }
    return Calculation(
        values={
            "dataset_id": x.rows[0].dataset_id,
            "dataset_doi": x.rows[0].dataset_doi,
            "source_group_id": x.rows[0].source_group_id,
            "source_archive_sha256": x.rows[0].source_archive_sha256,
            "provider_rows": [row.provider_row for row in x.rows],
            "row_count": len(x.rows),
            "quantile_levels": x.quantile_levels,
            "summary_basis": "unweighted_descriptive_summary_of_supplied_provider_model_rows",
            "summaries": summaries,
            "physical_observation_inferred": False,
            "failure_probability_inferred": False,
            "physical_calibration_inferred": False,
        },
        notes=(
            "Statistics describe only the caller-supplied provider simulation rows with equal row weight.",
            "Quantiles do not imply a validated probability distribution, independent Monte Carlo sample, experiment, corrosion-rate calibration, or material qualification.",
            "No interpolation, fitting, wall-loss projection, remaining-life calculation, or failure-probability calculation is performed.",
        ),
    )


class WetCo2LiteratureEvidenceRow(Contract):
    """Caller-supplied row evidence without redistributing a literature table."""

    schema_version: Literal["matintegrity.wet_co2_literature_evidence_row.v1"] = (
        "matintegrity.wet_co2_literature_evidence_row.v1"
    )
    evidence_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    source_locator: str = Field(min_length=1)
    bibliographic_id: str = Field(min_length=1)
    bibliographic_link_status: Literal[
        "primary_source_row",
        "secondary_reproduction_row",
        "candidate_only",
    ]
    compilation_row_link_status: Literal[
        "provider_explicit",
        "bibliographically_supported_numeric_sequence",
        "candidate_only",
    ]
    compilation_row_link_basis_id: str = Field(min_length=1)
    evidence_asset_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_values: dict[str, float | None] = Field(min_length=1)
    source_data_role: Literal[
        "experimental_autoclave_observation",
        "field_observation",
        "simulated_model_output",
        "unresolved",
    ]
    publication_license_id: str | None = None
    observation_redistribution_status: Literal["not_verified", "permission_confirmed"]
    data_dictionary_status: Literal["complete", "partial", "unreviewed"]
    physical_specimen_identity_status: Literal["confirmed", "unresolved", "not_applicable"]
    physical_specimen_id: str | None = None
    material_condition_id: str | None = None
    exposure_duration_s: Nonnegative | None = None

    @field_validator("source_values")
    @classmethod
    def valid_source_value_names(cls, value):
        if any(not name.strip() for name in value):
            raise ValueError("wet-CO2 literature source-value names must not be empty")
        return value

    @model_validator(mode="after")
    def consistent_specimen_identity(self):
        if self.physical_specimen_identity_status == "confirmed" and not self.physical_specimen_id:
            raise ValueError("confirmed specimen identity requires physical_specimen_id")
        if self.physical_specimen_identity_status != "confirmed" and self.physical_specimen_id is not None:
            raise ValueError("unconfirmed specimen identity must not carry physical_specimen_id")
        return self


class WetCo2LiteratureFieldMap(Contract):
    """Reviewed numeric transformation from literature fields to one compilation field."""

    schema_version: Literal["matintegrity.wet_co2_literature_field_map.v1"] = (
        "matintegrity.wet_co2_literature_field_map.v1"
    )
    compilation_field: Literal[
        "raw_temperature",
        "raw_flow_velocity",
        "raw_co2_pressure",
        "raw_internal_pressure",
        "raw_corrosion_inhibitor_efficiency",
        "raw_shear_stress",
        "raw_ph",
        "raw_corrosion_rate",
    ]
    source_fields: tuple[str, ...] = Field(min_length=1)
    operation: Literal["single_value_affine", "arithmetic_mean_affine"]
    scale: float = 1.0
    offset: float = 0.0
    absolute_tolerance: Nonnegative = 0.0
    reviewed_transform_basis_id: str = Field(min_length=1)
    unit_transform_reviewed: Literal[True] = True

    @model_validator(mode="after")
    def valid_operation(self):
        if len(set(self.source_fields)) != len(self.source_fields):
            raise ValueError("wet-CO2 literature mapping source fields must be unique")
        if any(not name.strip() for name in self.source_fields):
            raise ValueError("wet-CO2 literature mapping source fields must not be empty")
        if self.operation == "single_value_affine" and len(self.source_fields) != 1:
            raise ValueError("single-value wet-CO2 mapping requires exactly one source field")
        if self.operation == "arithmetic_mean_affine" and len(self.source_fields) < 2:
            raise ValueError("mean wet-CO2 mapping requires at least two source fields")
        return self


class WetCo2LiteratureFieldComparison(Contract):
    """One transparent transformed-value comparison; mismatches remain first-class."""

    schema_version: Literal["matintegrity.wet_co2_literature_field_comparison.v1"] = (
        "matintegrity.wet_co2_literature_field_comparison.v1"
    )
    compilation_field: str = Field(min_length=1)
    source_fields: tuple[str, ...] = Field(min_length=1)
    source_values: tuple[float | None, ...] = Field(min_length=1)
    operation: Literal["single_value_affine", "arithmetic_mean_affine"]
    scale: float
    offset: float
    absolute_tolerance: Nonnegative
    reviewed_transform_basis_id: str = Field(min_length=1)
    transformed_source_value: float | None
    compilation_value: float | None
    absolute_difference: Nonnegative | None
    status: Literal["match", "mismatch", "source_missing", "compilation_missing"]


class WetCo2LiteratureCrosswalkAudit(Contract):
    """Result of an explicit single-row literature comparison, not an automatic correction."""

    schema_version: Literal["matintegrity.wet_co2_literature_crosswalk_audit.v1"] = (
        "matintegrity.wet_co2_literature_crosswalk_audit.v1"
    )
    compilation_dataset_id: Literal["heterogeneous-wet-co2-corrosion"] = DATASET_ID
    compilation_provider_source_row: int = Field(ge=2)
    compilation_observation_id: str = Field(min_length=1)
    compilation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    source_locator: str = Field(min_length=1)
    bibliographic_id: str = Field(min_length=1)
    bibliographic_link_status: Literal[
        "primary_source_row",
        "secondary_reproduction_row",
        "candidate_only",
    ]
    compilation_row_link_status: Literal[
        "provider_explicit",
        "bibliographically_supported_numeric_sequence",
        "candidate_only",
    ]
    compilation_row_link_basis_id: str = Field(min_length=1)
    evidence_asset_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_data_role: Literal[
        "experimental_autoclave_observation",
        "field_observation",
        "simulated_model_output",
        "unresolved",
    ]
    publication_license_id: str | None
    observation_redistribution_status: Literal["not_verified", "permission_confirmed"]
    data_dictionary_status: Literal["complete", "partial", "unreviewed"]
    physical_specimen_identity_status: Literal["confirmed", "unresolved", "not_applicable"]
    physical_specimen_id: str | None
    material_condition_id: str | None
    exposure_duration_s: Nonnegative | None
    comparisons: tuple[WetCo2LiteratureFieldComparison, ...] = Field(min_length=1)
    crosswalk_status: Literal["all_declared_fields_match", "numeric_mismatch", "incomplete"]
    all_declared_fields_match: bool
    automatic_correction_performed: Literal[False] = False
    empirical_calibration_ready: Literal[False] = False
    mechanistic_calibration_ready: Literal[False] = False


class WetCo2SiObservation(Contract):
    """SI view using the associated paper's unit declarations, not CSV labels."""

    schema_version: Literal["matintegrity.wet_co2_si_observation.v1"] = (
        "matintegrity.wet_co2_si_observation.v1"
    )
    dataset_id: Literal["heterogeneous-wet-co2-corrosion"] = DATASET_ID
    provider_source_row: int = Field(ge=2)
    observation_id: str = Field(min_length=1)
    source_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_file_units_status: Literal["not_supplied"] = "not_supplied"
    unit_basis_id: Literal["doi:10.21203/rs.3.rs-8896642/v1#table-1"] = ASSOCIATED_PAPER_UNIT_BASIS_ID
    unit_basis_license: Literal["CC-BY-4.0"] = "CC-BY-4.0"
    unit_basis_reviewed: Literal[True] = True
    year_definition: Literal["julian_year_365.25_days"] = "julian_year_365.25_days"
    temperature_k: float = Field(gt=0.0)
    flow_velocity_m_s: Nonnegative
    co2_pressure_pa: Nonnegative
    internal_pressure_pa: Nonnegative | None = None
    corrosion_inhibitor_efficiency_fraction: float | None = None
    shear_stress_pa: Nonnegative | None = None
    ph: float
    corrosion_rate_m_s: Nonnegative
    provider_data_type: Literal["unresolved_field_simulated_or_experimental"] = (
        "unresolved_field_simulated_or_experimental"
    )
    provider_source_group_id: None = None
    physical_specimen_id: None = None
    material_condition_id: None = None
    exposure_duration_s: None = None
    row_level_source_mapping_status: Literal["not_provided_by_associated_paper"] = (
        "not_provided_by_associated_paper"
    )
    empirical_calibration_ready: Literal[False] = False
    mechanistic_calibration_ready: Literal[False] = False
    observation_redistribution_status: Literal["underlying_source_review_required"] = (
        "underlying_source_review_required"
    )

    @model_validator(mode="after")
    def reviewed_semantics(self):
        if not 0.0 <= self.ph <= 14.0:
            raise ValueError("wet-CO2 pH must remain in the conventional zero-to-fourteen range")
        if self.corrosion_inhibitor_efficiency_fraction is not None and not (
            0.0 <= self.corrosion_inhibitor_efficiency_fraction <= 1.0
        ):
            raise ValueError("inhibitor efficiency fraction must remain between zero and one")
        return self


def wet_co2_si_observation_from_compilation_row(
    row: UnresolvedWetCo2CompilationRow, *, reviewed_unit_basis_id: str
) -> WetCo2SiObservation:
    """Convert declared paper units to SI after an exact, explicit basis review."""

    if reviewed_unit_basis_id != ASSOCIATED_PAPER_UNIT_BASIS_ID:
        raise ValueError("wet-CO2 SI conversion requires the reviewed associated-paper Table 1 unit basis")
    return WetCo2SiObservation(
        provider_source_row=row.provider_source_row,
        observation_id=row.observation_id,
        source_archive_sha256=row.source_archive_sha256,
        temperature_k=row.raw_temperature + 273.15,
        flow_velocity_m_s=row.raw_flow_velocity,
        co2_pressure_pa=row.raw_co2_pressure * 100_000.0,
        internal_pressure_pa=(
            None if row.raw_internal_pressure is None else row.raw_internal_pressure * 100_000.0
        ),
        corrosion_inhibitor_efficiency_fraction=(
            None
            if row.raw_corrosion_inhibitor_efficiency is None
            else row.raw_corrosion_inhibitor_efficiency / 100.0
        ),
        shear_stress_pa=row.raw_shear_stress,
        ph=row.raw_ph,
        corrosion_rate_m_s=row.raw_corrosion_rate * 1.0e-3 / JULIAN_YEAR_SECONDS,
    )


def _simulation_source_values(workbook) -> list[tuple[float, ...]]:
    if workbook.sheetnames != ["Sheet1"]:
        raise ValueError("wet-CO2 simulation workbook sheet structure changed")
    sheet = workbook["Sheet1"]
    header = tuple(sheet.cell(row=1, column=column).value for column in range(1, 9))
    if header != HEADERS:
        raise ValueError("wet-CO2 simulation workbook header or column order changed")
    unit_table = tuple(
        (sheet.cell(row=row, column=10).value, sheet.cell(row=row, column=11).value) for row in range(3, 11)
    )
    if unit_table != SIMULATION_UNIT_TABLE:
        raise ValueError("wet-CO2 simulation workbook unit table changed")
    source_values = []
    for source_row in range(2, 245):
        values = tuple(sheet.cell(row=source_row, column=column).value for column in range(1, 9))
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
            raise ValueError("wet-CO2 simulation workbook contains a nonnumeric source value")
        numeric = tuple(float(value) for value in values)
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("wet-CO2 simulation workbook contains a nonfinite source value")
        source_values.append(numeric)
    return source_values


def match_wet_co2_simulation_source(
    compilation_rows: list[UnresolvedWetCo2CompilationRow],
    source_workbook_path: str | Path,
    *,
    require_pinned_hash: bool = True,
) -> list[WetCo2SimulationSourceMatch]:
    """Match the licensed 243-row workbook to a compilation prefix without inference."""

    try:
        from openpyxl import load_workbook
    except ImportError as error:  # pragma: no cover - optional dependency path
        raise RuntimeError("openpyxl is required to review the wet-CO2 simulation workbook") from error

    source = Path(source_workbook_path)
    content_hash = _digest(source)
    if require_pinned_hash and content_hash != SIMULATION_PINNED_SHA256:
        raise ValueError("wet-CO2 simulation workbook hash differs from the reviewed revision")
    if source.stat().st_size > 1024 * 1024:
        raise ValueError("wet-CO2 simulation workbook exceeds the bounded reader size")
    workbook = load_workbook(source, read_only=True, data_only=True, keep_links=False)
    try:
        source_values = _simulation_source_values(workbook)
    finally:
        workbook.close()
    if len(compilation_rows) < len(source_values):
        raise ValueError("wet-CO2 compilation has fewer rows than the reviewed simulation source")

    matches = []
    for index, (row, source_row_values) in enumerate(
        zip(compilation_rows[:243], source_values, strict=True), start=2
    ):
        compilation_values = (
            row.raw_temperature,
            row.raw_flow_velocity,
            row.raw_co2_pressure,
            row.raw_internal_pressure,
            row.raw_corrosion_inhibitor_efficiency,
            row.raw_shear_stress,
            row.raw_ph,
            row.raw_corrosion_rate,
        )
        if (
            any(value is None for value in compilation_values)
            or tuple(compilation_values) != source_row_values
        ):
            raise ValueError(
                f"wet-CO2 compilation row {row.provider_source_row} does not exactly match "
                f"simulation workbook row {index}"
            )
        matches.append(
            WetCo2SimulationSourceMatch(
                compilation_provider_source_row=row.provider_source_row,
                compilation_observation_id=row.observation_id,
                compilation_sha256=row.source_archive_sha256,
                source_provider_row=index,
                source_sha256=content_hash,
            )
        )
    return matches


def read_wet_co2_simulation_grid(
    source_workbook_path: str | Path, *, require_pinned_hash: bool = True
) -> list[WetCo2SimulationGridRow]:
    """Read the licensed 243-row simulation table into attributed SI records."""

    try:
        from openpyxl import load_workbook
    except ImportError as error:  # pragma: no cover - optional dependency path
        raise RuntimeError("openpyxl is required to read the wet-CO2 simulation grid") from error

    source = Path(source_workbook_path)
    content_hash = _digest(source)
    if require_pinned_hash and content_hash != SIMULATION_PINNED_SHA256:
        raise ValueError("wet-CO2 simulation workbook hash differs from the reviewed revision")
    if source.stat().st_size > 1024 * 1024:
        raise ValueError("wet-CO2 simulation workbook exceeds the bounded reader size")
    workbook = load_workbook(source, read_only=True, data_only=True, keep_links=False)
    try:
        source_values = _simulation_source_values(workbook)
    finally:
        workbook.close()

    evidence = (
        Evidence(
            source_id=SIMULATION_DATASET_ID,
            origin="open_dataset",
            citation=f"Khakzad and Khakzad, 2021, {SIMULATION_DATASET_DOI}",
            license_id="CC-BY-4.0",
            sha256=content_hash,
        ),
    )
    rows = []
    for source_row, values in enumerate(source_values, start=2):
        temperature_c, velocity, co2_bar, internal_bar, inhibitor_percent, shear_pa, ph, rate_mm_year = values
        rows.append(
            WetCo2SimulationGridRow(
                provider_row=source_row,
                source_archive_sha256=content_hash,
                temperature_K=temperature_c + 273.15,
                flow_velocity_m_s=velocity,
                co2_pressure_Pa=co2_bar * 100_000.0,
                internal_pressure_Pa=internal_bar * 100_000.0,
                corrosion_inhibitor_efficiency_fraction=inhibitor_percent / 100.0,
                shear_stress_Pa=shear_pa,
                ph=ph,
                corrosion_rate_m_s=rate_mm_year * 1.0e-3 / JULIAN_YEAR_SECONDS,
                evidence=evidence,
            )
        )
    return rows


def audit_wet_co2_literature_row(
    compilation_row: UnresolvedWetCo2CompilationRow,
    evidence_row: WetCo2LiteratureEvidenceRow,
    field_maps: tuple[WetCo2LiteratureFieldMap, ...],
) -> WetCo2LiteratureCrosswalkAudit:
    """Compare a declared source row while retaining missing values and discrepancies."""

    if not field_maps:
        raise ValueError("wet-CO2 literature audit requires at least one field mapping")
    compilation_fields = [mapping.compilation_field for mapping in field_maps]
    if len(set(compilation_fields)) != len(compilation_fields):
        raise ValueError("wet-CO2 literature audit cannot map one compilation field more than once")

    comparisons = []
    for mapping in field_maps:
        absent = [name for name in mapping.source_fields if name not in evidence_row.source_values]
        if absent:
            raise ValueError(f"wet-CO2 literature evidence omits mapped source fields: {absent}")
        source_values = tuple(evidence_row.source_values[name] for name in mapping.source_fields)
        compilation_value = getattr(compilation_row, mapping.compilation_field)
        transformed = None
        difference = None
        if any(value is None for value in source_values):
            status = "source_missing"
        else:
            numeric_values = tuple(float(value) for value in source_values if value is not None)
            if mapping.operation == "single_value_affine":
                aggregate = numeric_values[0]
            else:
                aggregate = sum(numeric_values) / len(numeric_values)
            transformed = mapping.scale * aggregate + mapping.offset
            if compilation_value is None:
                status = "compilation_missing"
            else:
                difference = abs(transformed - compilation_value)
                status = "match" if difference <= mapping.absolute_tolerance else "mismatch"
        comparisons.append(
            WetCo2LiteratureFieldComparison(
                compilation_field=mapping.compilation_field,
                source_fields=mapping.source_fields,
                source_values=source_values,
                operation=mapping.operation,
                scale=mapping.scale,
                offset=mapping.offset,
                absolute_tolerance=mapping.absolute_tolerance,
                reviewed_transform_basis_id=mapping.reviewed_transform_basis_id,
                transformed_source_value=transformed,
                compilation_value=compilation_value,
                absolute_difference=difference,
                status=status,
            )
        )

    statuses = {comparison.status for comparison in comparisons}
    if statuses == {"match"}:
        crosswalk_status = "all_declared_fields_match"
        all_declared_fields_match = True
    elif "mismatch" in statuses:
        crosswalk_status = "numeric_mismatch"
        all_declared_fields_match = False
    else:
        crosswalk_status = "incomplete"
        all_declared_fields_match = False
    return WetCo2LiteratureCrosswalkAudit(
        compilation_provider_source_row=compilation_row.provider_source_row,
        compilation_observation_id=compilation_row.observation_id,
        compilation_sha256=compilation_row.source_archive_sha256,
        evidence_id=evidence_row.evidence_id,
        source_group_id=evidence_row.source_group_id,
        source_record_id=evidence_row.source_record_id,
        source_locator=evidence_row.source_locator,
        bibliographic_id=evidence_row.bibliographic_id,
        bibliographic_link_status=evidence_row.bibliographic_link_status,
        compilation_row_link_status=evidence_row.compilation_row_link_status,
        compilation_row_link_basis_id=evidence_row.compilation_row_link_basis_id,
        evidence_asset_sha256=evidence_row.evidence_asset_sha256,
        source_data_role=evidence_row.source_data_role,
        publication_license_id=evidence_row.publication_license_id,
        observation_redistribution_status=evidence_row.observation_redistribution_status,
        data_dictionary_status=evidence_row.data_dictionary_status,
        physical_specimen_identity_status=evidence_row.physical_specimen_identity_status,
        physical_specimen_id=evidence_row.physical_specimen_id,
        material_condition_id=evidence_row.material_condition_id,
        exposure_duration_s=evidence_row.exposure_duration_s,
        comparisons=tuple(comparisons),
        crosswalk_status=crosswalk_status,
        all_declared_fields_match=all_declared_fields_match,
    )


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _number(row: dict[str, str], field: str, *, optional: bool = False) -> float | None:
    raw = row[field].strip()
    if optional and not raw:
        return None
    if not raw:
        raise ValueError(f"wet-CO2 source field {field} is required")
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError(f"wet-CO2 source field {field} must be numeric") from error
    if not math.isfinite(value):
        raise ValueError(f"wet-CO2 source field {field} must be finite")
    return value


def read_unresolved_wet_co2_compilation(
    path: str | Path, *, require_pinned_hash: bool = True
) -> list[UnresolvedWetCo2CompilationRow]:
    source = Path(path)
    content_hash = _digest(source)
    if require_pinned_hash and content_hash != PINNED_SHA256:
        raise ValueError("wet-CO2 compilation hash differs from the reviewed revision")
    if source.stat().st_size > 1024 * 1024:
        raise ValueError("wet-CO2 compilation exceeds the bounded reader size")
    with source.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != HEADERS:
            raise ValueError("wet-CO2 compilation schema or column order changed")
        records = []
        for source_row, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError("wet-CO2 compilation contains overflow columns")
            records.append(
                UnresolvedWetCo2CompilationRow(
                    provider_source_row=source_row,
                    observation_id=f"provider-row-{source_row}",
                    source_archive_sha256=content_hash,
                    raw_temperature=_number(row, "Temperature"),
                    raw_flow_velocity=_number(row, "Flow velocity"),
                    raw_co2_pressure=_number(row, "CO2 pressure"),
                    raw_internal_pressure=_number(row, "Internal pressure", optional=True),
                    raw_corrosion_inhibitor_efficiency=_number(
                        row, "Corrosion Inhibitor efficiency", optional=True
                    ),
                    raw_shear_stress=_number(row, "Shear stress", optional=True),
                    raw_ph=_number(row, "pH"),
                    raw_corrosion_rate=_number(row, "Corrosion rate"),
                )
            )
    if not records:
        raise ValueError("wet-CO2 compilation is empty")
    return records

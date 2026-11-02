"""Caller-parameterized Specific Ion Interaction Theory activity coefficients.

This module evaluates a bounded molality-scale SIT expression from explicit,
caller-owned interaction coefficients. It does not ship a parameter database,
infer missing interactions, or qualify a chemical system.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

SOURCE_ID = "nea_thermochemical_database_sit_method"
IMPLEMENTATION_SOURCE_ID = "usgs_phreeqc_sit_model_documentation"


class SITSpecies(Contract):
    species_id: str = Field(min_length=1)
    species_label: str = Field(min_length=1)
    charge_number: int = Field(ge=-8, le=8)
    molality_mol_kg: Nonnegative


class SITInteraction(Contract):
    """One directional epsilon coefficient and digest-bound source record."""

    target_species_id: str = Field(min_length=1)
    counter_species_id: str = Field(min_length=1)
    epsilon_kg_mol: float
    evidence_source_id: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class SITActivityCoefficientInput(Contract):
    schema_version: Literal["matintegrity.sit_activity_coefficient_input.v2"] = (
        "matintegrity.sit_activity_coefficient_input.v2"
    )
    assessment_id: str = Field(min_length=1)
    solution_id: str = Field(min_length=1)
    temperature_K: Positive
    ionic_strength_limit_mol_kg: Positive = Field(le=6.0)
    debye_huckel_A_at_temperature: Positive
    A_evidence_source_id: str = Field(min_length=1)
    A_provider_id: str = Field(min_length=1)
    A_provider_revision: str = Field(min_length=1)
    A_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    A_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    species: tuple[SITSpecies, ...] = Field(min_length=1, max_length=1000)
    interactions: tuple[SITInteraction, ...] = Field(default=(), max_length=100_000)
    charge_balance_absolute_tolerance_mol_kg: Nonnegative
    complete_ionic_inventory_reviewed: bool
    charge_balance_reviewed: bool
    ionic_strength_convention_reviewed: bool
    interaction_parameter_set_complete_and_applicable_reviewed: bool
    temperature_solvent_A_lineage_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_inventory_and_interactions(self):
        ids = [row.species_id for row in self.species]
        if len(ids) != len(set(ids)):
            raise ValueError("SIT species identifiers must be unique")
        species_by_id = {row.species_id: row for row in self.species}
        keys = [(row.target_species_id, row.counter_species_id) for row in self.interactions]
        if len(keys) != len(set(keys)):
            raise ValueError("SIT directional interaction pairs must be unique")
        evidence_id_list = [record.source_id for record in self.evidence]
        if len(evidence_id_list) != len(set(evidence_id_list)):
            raise ValueError("SIT Evidence source IDs must be unique")
        evidence_ids = set(evidence_id_list)
        if self.A_evidence_source_id not in evidence_ids:
            raise ValueError("the temperature-specific Debye-Huckel parameter must reference declared Evidence.source_id")
        for row in self.interactions:
            if row.target_species_id == row.counter_species_id:
                raise ValueError("SIT self-interaction terms are not accepted")
            if row.target_species_id not in species_by_id or row.counter_species_id not in species_by_id:
                raise ValueError("each SIT interaction must reference two declared species")
            if not math.isfinite(row.epsilon_kg_mol):
                raise ValueError("SIT interaction coefficients must be finite")
            if row.evidence_source_id not in evidence_ids:
                raise ValueError("each SIT interaction must reference a declared Evidence.source_id")
            if not any(
                evidence.source_id == row.evidence_source_id
                and evidence.sha256 == row.evidence_sha256
                for evidence in self.evidence
            ):
                raise ValueError("each SIT interaction record digest must match its declared Evidence")
        finite = (
            self.temperature_K,
            self.ionic_strength_limit_mol_kg,
            self.debye_huckel_A_at_temperature,
            self.charge_balance_absolute_tolerance_mol_kg,
        )
        if any(not math.isfinite(value) for value in finite):
            raise ValueError("SIT conditions and tolerances must be finite")
        return self


def sit_activity_coefficients(x: SITActivityCoefficientInput) -> Calculation:
    """Evaluate the declared SIT expression without extrapolation or parameter inference."""
    digest = canonical_digest(x.model_dump(mode="json"))
    ionic_strength = 0.5 * math.fsum(
        row.molality_mol_kg * row.charge_number**2 for row in x.species
    )
    charge_residual = math.fsum(row.molality_mol_kg * row.charge_number for row in x.species)
    base = {
        "assessment_id": x.assessment_id,
        "solution_id": x.solution_id,
        "temperature_K": x.temperature_K,
        "ionic_strength_mol_kg": ionic_strength,
        "ionic_strength_limit_mol_kg": x.ionic_strength_limit_mol_kg,
        "charge_balance_residual_mol_kg": charge_residual,
        "debye_huckel_A_at_temperature": x.debye_huckel_A_at_temperature,
        "A_evidence_source_id": x.A_evidence_source_id,
        "A_provider_id": x.A_provider_id,
        "A_provider_revision": x.A_provider_revision,
        "A_configuration_sha256": x.A_configuration_sha256,
        "A_record_sha256": x.A_record_sha256,
        "input_sha256": digest,
        "activity_standard_state": "molality_relative_to_1_mol_per_kg_water",
        "interaction_records": [
            {
                "target_species_id": row.target_species_id,
                "counter_species_id": row.counter_species_id,
                "epsilon_kg_mol": row.epsilon_kg_mol,
                "evidence_source_id": row.evidence_source_id,
                "source_record_id": row.source_record_id,
                "evidence_sha256": row.evidence_sha256,
            }
            for row in x.interactions
        ],
    }
    reviews = {
        "complete_ionic_inventory_reviewed": x.complete_ionic_inventory_reviewed,
        "charge_balance_reviewed": x.charge_balance_reviewed,
        "ionic_strength_convention_reviewed": x.ionic_strength_convention_reviewed,
        "interaction_parameter_set_complete_and_applicable_reviewed": x.interaction_parameter_set_complete_and_applicable_reviewed,
        "temperature_solvent_A_lineage_reviewed": x.temperature_solvent_A_lineage_reviewed,
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing}, notes=(
            "SIT evaluation requires reviewed complete inventory, interaction coverage, applicability and temperature-specific Debye-Huckel parameter lineage.",
        ))
    if ionic_strength > x.ionic_strength_limit_mol_kg:
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": "ionic_strength_exceeds_caller_declared_sit_limit",
        }, notes=("The declared SIT limit is caller-selected and capped at 6 mol/kg; concentrated-mixture qualification is not inferred.",))
    if abs(charge_residual) > x.charge_balance_absolute_tolerance_mol_kg:
        return Calculation(status="needs_data", values=base | {
            "out_of_scope_reason": "charge_balance_tolerance_exceeded",
        }, notes=("The supplied complete ionic inventory exceeds its declared charge-balance tolerance.",))

    epsilon_by_pair = {(row.target_species_id, row.counter_species_id): row.epsilon_kg_mol for row in x.interactions}
    root_i = math.sqrt(ionic_strength)
    debye_term = x.debye_huckel_A_at_temperature * root_i / (1.0 + 1.5 * root_i)
    output = []
    for target in x.species:
        short_range = math.fsum(
            epsilon_by_pair.get((target.species_id, counter.species_id), 0.0) * counter.molality_mol_kg
            for counter in x.species
            if counter.species_id != target.species_id
        )
        log10_gamma = -target.charge_number**2 * debye_term + short_range
        try:
            gamma = 10.0**log10_gamma
        except OverflowError:
            gamma = math.inf
        if not math.isfinite(log10_gamma) or not math.isfinite(gamma) or gamma <= 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "out_of_scope_reason": "activity_coefficient_not_numerically_representable",
                "species_id": target.species_id,
            }, notes=("At least one computed SIT coefficient is outside finite positive binary64 support.",))
        output.append({
            "species_id": target.species_id,
            "species_label": target.species_label,
            "charge_number": target.charge_number,
            "molality_mol_kg": target.molality_mol_kg,
            "debye_huckel_log10_contribution": -target.charge_number**2 * debye_term,
            "specific_interaction_log10_contribution": short_range,
            "log10_activity_coefficient": log10_gamma,
            "activity_coefficient": gamma,
            "dimensionless_activity": gamma * target.molality_mol_kg,
        })
    return Calculation(values=base | {"species": output}, notes=(
        "The SIT expression uses the caller-provided directional epsilon table and temperature-specific A parameter; absent directional pairs contribute zero only under the explicit completeness review.",
        "No parameter fitting, speciation, phase discovery, pressure correction or corrosion-rate inference is performed; any neutral-species term must be explicitly supplied and reviewed by the caller.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "chemistry.sit_activity_coefficients",
        SITActivityCoefficientInput,
        sit_activity_coefficients,
        {
            "ionic_strength_mol_kg": "mol/kg",
            "charge_balance_residual_mol_kg": "mol/kg",
            "activity_standard_state": "1",
            "species.activity_coefficient": "1",
            "species.dimensionless_activity": "1",
            "species.log10_activity_coefficient": "1",
            "species.debye_huckel_log10_contribution": "1",
            "species.specific_interaction_log10_contribution": "1",
        },
        (
            "The caller provides every used directional interaction coefficient and reviews completeness, units, temperature and applicability.",
            "The Debye-Huckel parameter is caller-supplied and evidence-linked; missing epsilon pairs contribute zero under the completeness review.",
            "The implementation does not infer neutral-species salting parameters or represent phase transitions and corrosion kinetics.",
        ),
        (SOURCE_ID, IMPLEMENTATION_SOURCE_ID),
    )]

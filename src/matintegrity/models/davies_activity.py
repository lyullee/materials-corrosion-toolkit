"""Caller-parameterized Davies activity coefficients for aqueous species."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

SOURCE_ID = "usgs_phreeqc_davies_activity_coefficients"
LIMIT_SOURCE_ID = "usgs_davies_ionic_strength_approximation"


class DaviesActivitySpecies(Contract):
    species_id: str = Field(min_length=1)
    species_label: str = Field(min_length=1)
    charge_number: int = Field(ge=-8, le=8)
    molality_mol_kg: Nonnegative


class DaviesActivityCoefficientInput(Contract):
    assessment_id: str = Field(min_length=1)
    solution_id: str = Field(min_length=1)
    temperature_K: Positive
    ionic_strength_limit_mol_kg: Positive = Field(le=0.5)
    davies_A_at_temperature: Positive
    A_provider_id: str = Field(min_length=1)
    A_provider_revision: str = Field(min_length=1)
    A_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    A_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    charge_balance_absolute_tolerance_mol_kg: Nonnegative
    species: tuple[DaviesActivitySpecies, ...] = Field(min_length=1)
    complete_ionic_inventory_reviewed: bool
    charge_balance_reviewed: bool
    ionic_strength_convention_reviewed: bool
    davies_scope_reviewed: bool
    temperature_solvent_A_lineage_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_species(self):
        identities = [row.species_id for row in self.species]
        if len(identities) != len(set(identities)):
            raise ValueError("Davies species identifiers must be unique")
        return self


def davies_activity_coefficients(x: DaviesActivityCoefficientInput) -> Calculation:
    """Calculate charge-based activity coefficients from a complete molal ion inventory.

    Neutral solutes use gamma=1 by convention; this is not a salting-out model.
    The temperature-specific Davies A parameter is caller supplied and evidenced.
    """

    input_digest = canonical_digest(x.model_dump(mode="json"))
    reviews = {
        "complete_ionic_inventory_reviewed": x.complete_ionic_inventory_reviewed,
        "charge_balance_reviewed": x.charge_balance_reviewed,
        "ionic_strength_convention_reviewed": x.ionic_strength_convention_reviewed,
        "davies_scope_reviewed": x.davies_scope_reviewed,
        "temperature_solvent_A_lineage_reviewed": x.temperature_solvent_A_lineage_reviewed,
    }
    missing_reviews = [name for name, reviewed in reviews.items() if not reviewed]
    ionic_strength = 0.5 * math.fsum(row.molality_mol_kg * row.charge_number**2 for row in x.species)
    charge_residual = math.fsum(row.molality_mol_kg * row.charge_number for row in x.species)
    base = {
        "assessment_id": x.assessment_id,
        "solution_id": x.solution_id,
        "temperature_K": x.temperature_K,
        "ionic_strength_mol_kg": ionic_strength,
        "charge_balance_residual_mol_kg": charge_residual,
        "ionic_strength_limit_mol_kg": x.ionic_strength_limit_mol_kg,
        "davies_A_at_temperature": x.davies_A_at_temperature,
        "A_provider_id": x.A_provider_id,
        "A_provider_revision": x.A_provider_revision,
        "A_configuration_digest": x.A_configuration_digest,
        "A_record_digest": x.A_record_digest,
        "input_digest": input_digest,
        "activity_standard_state": "molality_relative_to_1_mol_per_kg_water",
    }
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": missing_reviews},
            notes=(
                "A reviewed complete molal inventory, charge balance, Davies scope, and temperature-specific A parameter are required.",
            ),
        )
    if ionic_strength > x.ionic_strength_limit_mol_kg:
        return Calculation(
            status="out_of_scope",
            values=base | {"out_of_scope_reason": "ionic_strength_exceeds_declared_davies_limit"},
            notes=(
                "The classic Davies approximation is limited here to the caller-declared range, which cannot exceed 0.5 mol/kg water; concentrated-brine models are not substituted automatically.",
            ),
        )
    if abs(charge_residual) > x.charge_balance_absolute_tolerance_mol_kg:
        return Calculation(
            status="needs_data",
            values=base | {"out_of_scope_reason": "charge_balance_tolerance_exceeded"},
            notes=(
                "The supplied complete ionic inventory does not meet its declared electroneutrality tolerance.",
            ),
        )

    root_strength = math.sqrt(ionic_strength)
    davies_term = root_strength / (1.0 + root_strength) - 0.3 * ionic_strength
    rows = []
    for species in x.species:
        log10_gamma = -x.davies_A_at_temperature * species.charge_number**2 * davies_term
        gamma = 10.0**log10_gamma
        if not math.isfinite(gamma) or gamma <= 0.0:
            return Calculation(
                status="out_of_scope",
                values=base
                | {
                    "out_of_scope_reason": "activity_coefficient_not_numerically_representable",
                    "species_id": species.species_id,
                },
                notes=(
                    "At least one activity coefficient is outside finite positive binary64 representation.",
                ),
            )
        rows.append(
            {
                "species_id": species.species_id,
                "species_label": species.species_label,
                "charge_number": species.charge_number,
                "molality_mol_kg": species.molality_mol_kg,
                "log10_activity_coefficient": log10_gamma,
                "activity_coefficient": gamma,
                "dimensionless_activity": gamma * species.molality_mol_kg,
                "neutral_gamma_convention": "unity" if species.charge_number == 0 else None,
            }
        )
    return Calculation(
        values=base | {"species": rows},
        notes=(
            "Charged-species coefficients use the caller-provided temperature-specific Davies A parameter and supplied complete molal ionic inventory.",
            "The declared Davies ionic-strength limit is capped at 0.5 mol/kg water; this calculation does not provide concentrated-electrolyte Pitzer/SIT corrections, gas solubility, or corrosion rate.",
            "Neutral-species gamma is set to unity by explicit convention and does not model salting effects; align activity standard states before using coefficients with other chemistry models.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "chemistry.davies_activity_coefficients",
            DaviesActivityCoefficientInput,
            davies_activity_coefficients,
            {
                "ionic_strength_mol_kg": "mol/kg",
                "charge_balance_residual_mol_kg": "mol/kg",
                "activity_standard_state": "1",
                "species.activity_coefficient": "1",
                "species.dimensionless_activity": "1",
                "species.log10_activity_coefficient": "1",
            },
            (
                "Ionic strength is calculated from the caller-reviewed complete molal species inventory; electroneutrality is checked against an explicit tolerance.",
                "Davies A is a caller-supplied, evidenced value for the declared temperature and solvent; the declared applicability ceiling cannot exceed 0.5 mol/kg water.",
                "Neutral-species gamma is unity by convention; no salting-out, concentrated-brine correction, gas equilibrium, or corrosion-rate inference is included.",
            ),
            (SOURCE_ID, LIMIT_SOURCE_ID),
        )
    ]

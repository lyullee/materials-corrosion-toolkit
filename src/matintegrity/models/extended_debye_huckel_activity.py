"""Caller-parameterized extended Debye-Hückel activity coefficients."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

MODEL_ID = "chemistry.aqueous_extended_debye_huckel_activity"
SOURCE_ID = "caller_extended_debye_huckel_activity_parameters"
METHOD_SOURCE_ID = "usgs_phreeqc_extended_debye_huckel_method"


class ExtendedDebyeHuckelSpecies(Contract):
    species_id: str = Field(min_length=1)
    species_label: str = Field(min_length=1)
    charge_number: int = Field(ge=-8, le=8)
    molality_mol_kg: Nonnegative
    ion_size_parameter_nm: Positive | None = None
    ion_size_evidence_source_id: str | None = Field(default=None, min_length=1)


class ExtendedDebyeHuckelActivityInput(Contract):
    """Complete molal inventory and caller-supplied model parameters.

    ``A`` is expressed in (kg/mol)^0.5. ``B`` is expressed in
    nm^-1 (kg/mol)^0.5, and each species ion-size parameter is in nm.
    Thus ``B * a * sqrt(I)`` is dimensionless for I in mol/kg water.
    """

    assessment_id: str = Field(min_length=1)
    solution_id: str = Field(min_length=1)
    temperature_K: Positive
    ionic_strength_limit_mol_kg: Positive
    debye_huckel_A_at_temperature: Positive
    debye_huckel_B_at_temperature: Positive
    parameter_provider_id: str = Field(min_length=1)
    parameter_provider_revision: str = Field(min_length=1)
    parameter_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parameter_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    species: tuple[ExtendedDebyeHuckelSpecies, ...] = Field(min_length=1, max_length=1000)
    charge_balance_absolute_tolerance_mol_kg: Nonnegative
    complete_ionic_inventory_reviewed: bool
    charge_balance_reviewed: bool
    ionic_strength_convention_reviewed: bool
    extended_debye_huckel_scope_reviewed: bool
    parameter_temperature_solvent_lineage_reviewed: bool
    activity_standard_state_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_parameters_and_species(self):
        species_ids = [row.species_id for row in self.species]
        if len(species_ids) != len(set(species_ids)):
            raise ValueError("species identifiers must be unique")
        evidence_by_id = {row.source_id: row for row in self.evidence}
        if len(evidence_by_id) != len(self.evidence):
            raise ValueError("Evidence source IDs must be unique")
        parameter_evidence = evidence_by_id.get(self.parameter_provider_id)
        if parameter_evidence is None or parameter_evidence.sha256 != self.parameter_record_sha256:
            raise ValueError("temperature/solvent parameters must match Evidence for the declared provider and record digest")
        if not math.isfinite(self.ionic_strength_limit_mol_kg):
            raise ValueError("ionic-strength limit must be finite")
        for species in self.species:
            if species.charge_number == 0:
                if species.ion_size_parameter_nm is not None or species.ion_size_evidence_source_id is not None:
                    raise ValueError("neutral solutes use the explicit unit-gamma convention; no ion-size term is accepted")
                continue
            if species.ion_size_parameter_nm is None or species.ion_size_evidence_source_id is None:
                raise ValueError("each charged species needs a source-linked positive ion-size parameter")
            if species.ion_size_evidence_source_id not in evidence_by_id:
                raise ValueError("each ion-size parameter must reference a declared Evidence source")
            if evidence_by_id[species.ion_size_evidence_source_id].sha256 is None:
                raise ValueError("ion-size Evidence must pin its source SHA-256")
        return self


def extended_debye_huckel_activity_coefficients(
    request: ExtendedDebyeHuckelActivityInput,
) -> Calculation:
    """Evaluate log10(gamma_i) = -A z_i^2 sqrt(I)/(1 + B a_i sqrt(I)).

    No parameters are inferred or defaulted. The requested support limit and
    temperature/solvent-specific A and B values must come from caller evidence.
    """
    try:
        ionic_strength = 0.5 * math.fsum(
            row.molality_mol_kg * row.charge_number**2 for row in request.species
        )
        charge_residual = math.fsum(
            row.molality_mol_kg * row.charge_number for row in request.species
        )
    except (OverflowError, ValueError):
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": request.assessment_id,
                "solution_id": request.solution_id,
                "out_of_scope_reason": "ionic_inventory_arithmetic_not_finite",
            },
        )
    if not math.isfinite(ionic_strength) or not math.isfinite(charge_residual):
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": request.assessment_id,
                "solution_id": request.solution_id,
                "out_of_scope_reason": "ionic_inventory_arithmetic_not_finite",
            },
        )
    input_sha256 = canonical_digest(request.model_dump(mode="json"))
    evidence_by_id = {row.source_id: row for row in request.evidence}
    missing_reviews = [
        name for name, reviewed in (
            ("complete_ionic_inventory_reviewed", request.complete_ionic_inventory_reviewed),
            ("charge_balance_reviewed", request.charge_balance_reviewed),
            ("ionic_strength_convention_reviewed", request.ionic_strength_convention_reviewed),
            ("extended_debye_huckel_scope_reviewed", request.extended_debye_huckel_scope_reviewed),
            ("parameter_temperature_solvent_lineage_reviewed", request.parameter_temperature_solvent_lineage_reviewed),
            ("activity_standard_state_reviewed", request.activity_standard_state_reviewed),
        ) if not reviewed
    ]
    base = {
        "assessment_id": request.assessment_id,
        "solution_id": request.solution_id,
        "temperature_K": request.temperature_K,
        "ionic_strength_mol_kg": ionic_strength,
        "ionic_strength_limit_mol_kg": request.ionic_strength_limit_mol_kg,
        "charge_balance_residual_mol_kg": charge_residual,
        "debye_huckel_A_at_temperature": request.debye_huckel_A_at_temperature,
        "debye_huckel_B_at_temperature": request.debye_huckel_B_at_temperature,
        "parameter_provider_id": request.parameter_provider_id,
        "parameter_provider_revision": request.parameter_provider_revision,
        "parameter_configuration_sha256": request.parameter_configuration_sha256,
        "parameter_record_sha256": request.parameter_record_sha256,
        "input_sha256": input_sha256,
        "activity_standard_state": "molality_relative_to_1_mol_per_kg_water",
        "source_evidence": [row.model_dump(mode="json") for row in request.evidence],
    }
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": missing_reviews},
            notes=("Complete inventory, electroneutrality, parameter applicability, and activity standard-state reviews are required.",),
        )
    if ionic_strength > request.ionic_strength_limit_mol_kg:
        return Calculation(
            status="out_of_scope",
            values=base | {"out_of_scope_reason": "ionic_strength_exceeds_caller_supported_limit"},
            notes=("No activity-model substitution or extrapolation is performed beyond the caller-declared support limit.",),
        )
    if abs(charge_residual) > request.charge_balance_absolute_tolerance_mol_kg:
        return Calculation(
            status="needs_data",
            values=base | {"out_of_scope_reason": "ionic_inventory_charge_balance_tolerance_exceeded"},
            notes=("The supplied complete ionic inventory does not satisfy its declared charge-balance tolerance.",),
        )

    sqrt_ionic_strength = math.sqrt(ionic_strength)
    species_results = []
    for species in request.species:
        if species.charge_number == 0:
            log10_gamma = 0.0
            gamma = 1.0
            convention = "neutral_solute_gamma_set_to_unity_no_salt_effect_modelled"
        else:
            # Charged-species size fields are guaranteed by the request validator.
            ion_size_nm = species.ion_size_parameter_nm
            if ion_size_nm is None:
                return Calculation(
                    status="needs_data",
                    values=base | {"out_of_scope_reason": "charged_species_ion_size_missing", "species_id": species.species_id},
                )
            denominator = 1.0 + request.debye_huckel_B_at_temperature * ion_size_nm * sqrt_ionic_strength
            if not math.isfinite(denominator) or denominator <= 0.0:
                return Calculation(
                    status="out_of_scope",
                    values=base | {"out_of_scope_reason": "extended_debye_huckel_denominator_not_positive_finite", "species_id": species.species_id},
                )
            log10_gamma = (
                -request.debye_huckel_A_at_temperature
                * species.charge_number**2
                * sqrt_ionic_strength
                / denominator
            )
            try:
                gamma = 10.0**log10_gamma
            except OverflowError:
                gamma = math.inf
            convention = None
        activity = gamma * species.molality_mol_kg
        if not all(math.isfinite(value) for value in (log10_gamma, gamma, activity)) or gamma <= 0.0:
            return Calculation(
                status="out_of_scope",
                values=base | {"out_of_scope_reason": "activity_coefficient_not_numerically_representable", "species_id": species.species_id},
                notes=("At least one activity coefficient or activity exceeds finite positive binary64 representation.",),
            )
        species_results.append({
            "species_id": species.species_id,
            "species_label": species.species_label,
            "charge_number": species.charge_number,
            "molality_mol_kg": species.molality_mol_kg,
            "ion_size_parameter_nm": species.ion_size_parameter_nm,
            "ion_size_evidence_source_id": species.ion_size_evidence_source_id,
            "log10_activity_coefficient": log10_gamma,
            "activity_coefficient": gamma,
            "dimensionless_activity": activity,
            "neutral_species_convention": convention,
        })
    return Calculation(
        values=base | {"species": species_results},
        notes=(
            "A, B, ion-size parameters and ionic-strength support are caller supplied; the model includes no coefficient database.",
            "The neutral-species convention is gamma=1 and has no salting correction; this result alone does not qualify aqueous CO2 solubility or corrosion kinetics.",
            "The expression is a single-ion activity approximation. Parameter support, solvent, temperature and standard-state consistency require independent review.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            MODEL_ID,
            ExtendedDebyeHuckelActivityInput,
            extended_debye_huckel_activity_coefficients,
            {
                "ionic_strength_mol_kg": "mol/kg",
                "charge_balance_residual_mol_kg": "mol/kg",
                "activity_coefficient": "1",
                "dimensionless_activity": "1",
            },
            (
                "All Debye-Huckel A/B coefficients, ionic-strength support, and charged-species ion-size parameters are caller supplied and Evidence-bound.",
                "The result is a single-ion extended Debye-Huckel approximation within explicit reviewed temperature, solvent, ionic-strength and activity standard-state support.",
                "Neutral species use unit activity coefficient with no salting correction; this model does not infer CO2 solubility, phase equilibrium or corrosion kinetics.",
            ),
            (SOURCE_ID, METHOD_SOURCE_ID),
        )
    ]

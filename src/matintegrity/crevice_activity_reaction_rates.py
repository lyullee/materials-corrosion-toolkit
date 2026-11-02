"""Caller-calibrated reversible reaction rates on dimensionless activities."""

from __future__ import annotations

import math

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "chemistry.crevice_activity_based_reaction_rates"
SPECIES_SOURCE_ID = "caller_crevice_activity_rate_state_and_gamma"
NETWORK_SOURCE_ID = "caller_crevice_activity_rate_reaction_records"
METHOD_SOURCE_ID = "reversible_mass_action_rates_on_dimensionless_activities"


class CreviceActivityRateSpecies(Contract):
    species_id: str = Field(min_length=1)
    charge_number: StrictInt = Field(ge=-8, le=8)
    elemental_composition: dict[str, StrictInt] = Field(min_length=1, max_length=16)
    concentration_mol_m3: Positive
    activity_coefficient: Positive

    @model_validator(mode="after")
    def validate_formula(self):
        if any(not key.strip() or count < 0 for key, count in self.elemental_composition.items()):
            raise ValueError("elemental formula must use nonempty element names and nonnegative integer counts")
        return self


class CreviceActivityRateTerm(Contract):
    species_id: str = Field(min_length=1)
    coefficient: StrictInt = Field(ge=1, le=16)


class CreviceActivityRateReaction(Contract):
    reaction_id: str = Field(min_length=1)
    reactants: tuple[CreviceActivityRateTerm, ...] = Field(min_length=1, max_length=24)
    products: tuple[CreviceActivityRateTerm, ...] = Field(min_length=1, max_length=24)
    forward_rate_constant_mol_m3_s: Positive
    reverse_rate_constant_mol_m3_s: Positive
    equilibrium_constant_dimensionless: Positive
    parameter_record_id: str = Field(min_length=1)
    parameter_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    rate_record_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=32)


class CreviceActivityRateRequest(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    state_id: str = Field(min_length=1)
    temperature_K: Positive
    concentration_standard_state_mol_m3: Positive = 1000.0
    species: tuple[CreviceActivityRateSpecies, ...] = Field(min_length=2, max_length=64)
    reactions: tuple[CreviceActivityRateReaction, ...] = Field(min_length=1, max_length=128)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    rights_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    activity_standard_state_and_single_ion_convention_reviewed: bool
    kinetic_rate_basis_and_units_reviewed: bool
    detailed_balance_and_equilibrium_constant_reviewed: bool
    temperature_and_parameter_support_reviewed: bool
    single_liquid_no_phase_change_interval_reviewed: bool
    local_electroneutrality_reviewed: bool
    computational_use_authorized: bool
    detailed_balance_relative_tolerance: Positive = Field(default=1e-6, le=1e-2)

    @model_validator(mode="after")
    def validate_chemistry(self):
        if not all((
            self.activity_standard_state_and_single_ion_convention_reviewed,
            self.kinetic_rate_basis_and_units_reviewed,
            self.detailed_balance_and_equilibrium_constant_reviewed,
            self.temperature_and_parameter_support_reviewed,
            self.single_liquid_no_phase_change_interval_reviewed,
            self.local_electroneutrality_reviewed,
            self.computational_use_authorized,
        )):
            raise ValueError("all activity, kinetic, thermodynamic, applicability and authorization reviews are required")
        ids = [row.species_id for row in self.species]
        if len(ids) != len(set(ids)):
            raise ValueError("species identifiers must be unique")
        species_by_id = {row.species_id: row for row in self.species}
        charge = math.fsum(row.charge_number * row.concentration_mol_m3 for row in self.species)
        charge_scale = math.fsum(abs(row.charge_number) * row.concentration_mol_m3 for row in self.species)
        if charge_scale <= 0 or abs(charge) > 1e-9 * charge_scale:
            raise ValueError("reaction-rate state must be locally electroneutral")
        reaction_ids = [row.reaction_id for row in self.reactions]
        if len(reaction_ids) != len(set(reaction_ids)):
            raise ValueError("reaction IDs must be unique")
        for reaction in self.reactions:
            terms = (*reaction.reactants, *reaction.products)
            if any(term.species_id not in species_by_id for term in terms):
                raise ValueError("reaction terms must reference declared species")
            if len({term.species_id for term in reaction.reactants}) != len(reaction.reactants) or len(
                {term.species_id for term in reaction.products}
            ) != len(reaction.products):
                raise ValueError("species may occur only once on each side of a reaction")
            net: dict[str, int] = {}
            for term in reaction.reactants:
                net[term.species_id] = net.get(term.species_id, 0) - term.coefficient
            for term in reaction.products:
                net[term.species_id] = net.get(term.species_id, 0) + term.coefficient
            if not any(net.values()):
                raise ValueError("reaction must have a nonzero net stoichiometric vector")
            charge = sum(net.get(row.species_id, 0) * row.charge_number for row in self.species)
            if charge != 0:
                raise ValueError("reaction must conserve electric charge")
            elements = set().union(*(row.elemental_composition.keys() for row in self.species))
            for element in elements:
                if sum(net.get(row.species_id, 0) * row.elemental_composition.get(element, 0)
                       for row in self.species) != 0:
                    raise ValueError(f"reaction must conserve element {element!r}")
            log_ratio_error = (
                math.log(reaction.forward_rate_constant_mol_m3_s)
                - math.log(reaction.reverse_rate_constant_mol_m3_s)
                - math.log(reaction.equilibrium_constant_dimensionless)
            )
            if abs(log_ratio_error) > math.log1p(self.detailed_balance_relative_tolerance):
                raise ValueError(f"reaction {reaction.reaction_id!r} rate constants are inconsistent with its equilibrium constant")
            if not any(row.source_id == self.provider_id and row.sha256 == self.provider_configuration_sha256
                       for row in self.provider_evidence):
                raise ValueError("provider Evidence must bind provider ID and configuration digest")
            if not any(row.source_id == reaction.parameter_record_id
                       and row.sha256 == reaction.parameter_record_sha256 and row.license_id
                       for row in reaction.rate_record_evidence):
                raise ValueError("licensed Evidence must match each reaction parameter record ID and digest")
        if not any(row.license_id for row in self.rights_evidence):
            raise ValueError("rights Evidence must specify a license or permitted-use basis")
        return self


def evaluate_crevice_activity_reaction_rates(request: CreviceActivityRateRequest) -> Calculation:
    """Evaluate caller reversible mass-action rates from dimensionless species activities."""
    digest = canonical_digest(request.model_dump(mode="json"))
    activity = {
        row.species_id: row.activity_coefficient * row.concentration_mol_m3 /
        request.concentration_standard_state_mol_m3
        for row in request.species
    }
    if any(value <= 0 or not math.isfinite(value) for value in activity.values()):
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "reason": "nonpositive_or_nonfinite_species_activity", "input_sha256": digest,
        })
    rate_by_reaction = {}
    net_source = {row.species_id: 0.0 for row in request.species}
    for reaction in request.reactions:
        log_forward_product = math.fsum(term.coefficient * math.log(activity[term.species_id])
                                        for term in reaction.reactants)
        log_reverse_product = math.fsum(term.coefficient * math.log(activity[term.species_id])
                                        for term in reaction.products)
        try:
            forward = reaction.forward_rate_constant_mol_m3_s * math.exp(log_forward_product)
            reverse = reaction.reverse_rate_constant_mol_m3_s * math.exp(log_reverse_product)
        except OverflowError:
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "reason": "activity_mass_action_rate_overflow",
                "reaction_id": reaction.reaction_id, "input_sha256": digest,
            })
        if not math.isfinite(forward) or not math.isfinite(reverse):
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "reason": "nonfinite_activity_mass_action_rate",
                "reaction_id": reaction.reaction_id, "input_sha256": digest,
            })
        net_rate = forward - reverse
        extent = {
            row.species_id: sum(t.coefficient for t in reaction.products if t.species_id == row.species_id)
            - sum(t.coefficient for t in reaction.reactants if t.species_id == row.species_id)
            for row in request.species
        }
        for species_id, coefficient in extent.items():
            net_source[species_id] += coefficient * net_rate
        log_q_over_k = log_reverse_product - log_forward_product - math.log(
            reaction.equilibrium_constant_dimensionless
        )
        rate_by_reaction[reaction.reaction_id] = {
            "forward_extent_rate_mol_m3_s": forward,
            "reverse_extent_rate_mol_m3_s": reverse,
            "net_extent_rate_mol_m3_s": net_rate,
            "log10_reaction_quotient_over_equilibrium_constant": log_q_over_k / math.log(10.0),
            "parameter_record_id": reaction.parameter_record_id,
            "parameter_record_sha256": reaction.parameter_record_sha256,
        }
    return Calculation(status="computed", values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "physical_scope_id": request.physical_scope_id,
        "state_id": request.state_id,
        "temperature_K": request.temperature_K,
        "provider_id": request.provider_id,
        "provider_revision": request.provider_revision,
        "provider_configuration_sha256": request.provider_configuration_sha256,
        "input_sha256": digest,
        "dimensionless_activity_by_species": activity,
        "reaction_rates": rate_by_reaction,
        "net_species_source_mol_m3_s_by_species": net_source,
        "interpretation": "caller_parameterized_nonideal_activity_mass_action_rate_snapshot",
        "limitations": [
            "A single caller-defined state and caller reversible kinetic records are evaluated; no time evolution or transport is integrated.",
            "Activities use caller single-ion gamma and one declared concentration standard state; provider thermodynamics are not independently qualified.",
            "Detailed balance is required through the caller's kf/kr and equilibrium constant relation, but parameter calibration and temperature transfer remain caller responsibilities.",
            "No equilibrium/speciation solve, pH, phase selection, precipitation, dissolution, wall kinetics, corrosion rate or damage acceptance is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceActivityRateRequest,
        evaluator=evaluate_crevice_activity_reaction_rates,
        units={
            "temperature_K": "K",
            "reaction_rates.*.forward_extent_rate_mol_m3_s": "mol/(m^3*s)",
            "reaction_rates.*.reverse_extent_rate_mol_m3_s": "mol/(m^3*s)",
            "reaction_rates.*.net_extent_rate_mol_m3_s": "mol/(m^3*s)",
            "reaction_rates.*.log10_reaction_quotient_over_equilibrium_constant": "1",
            "net_species_source_mol_m3_s_by_species.*": "mol/(m^3*s)",
            "dimensionless_activity_by_species.*": "1",
        },
        assumptions=(
            "Caller supplies one positive single-liquid state, single-ion activity coefficients and reversible rate records on a dimensionless activity basis.",
            "Forward and reverse constants share mol/(m^3*s) units and their ratio is checked against the caller dimensionless equilibrium constant.",
            "No state integration, speciation, phase equilibrium or corrosion calculation is performed.",
        ),
        source_ids=(SPECIES_SOURCE_ID, NETWORK_SOURCE_ID, METHOD_SOURCE_ID),
    )]

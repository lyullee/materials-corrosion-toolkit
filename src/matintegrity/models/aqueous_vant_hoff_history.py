"""Temperature-dependent caller-supplied aqueous equilibrium constants."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec
from .aqueous_mass_action import AqueousMassActionSystem, aqueous_mass_action_speciation

MOLAR_GAS_CONSTANT_J_MOL_K = 8.31446261815324


class ReactionEnthalpyReference(Contract):
    reaction_id: str = Field(min_length=1)
    delta_h_reference_J_mol: float
    delta_cp_reference_J_mol_K: float | None = None
    delta_cp_slope_J_mol_K2: float | None = None
    minimum_valid_temperature_K: Positive
    maximum_valid_temperature_K: Positive
    source_record_id: str = Field(min_length=1)
    evidence: Evidence

    @model_validator(mode="after")
    def valid_source_and_support(self):
        if not math.isfinite(self.delta_h_reference_J_mol) or any(
            value is not None and not math.isfinite(value)
            for value in (self.delta_cp_reference_J_mol_K, self.delta_cp_slope_J_mol_K2)
        ):
            raise ValueError("reference reaction enthalpy and optional heat-capacity change must be finite")
        if self.delta_cp_slope_J_mol_K2 is not None and self.delta_cp_reference_J_mol_K is None:
            raise ValueError("a heat-capacity slope requires an explicit reference heat-capacity change")
        if self.minimum_valid_temperature_K >= self.maximum_valid_temperature_K:
            raise ValueError("thermochemical temperature support must be strictly increasing")
        if self.evidence.origin in {"measured", "open_dataset"} and self.evidence.sha256 is None:
            raise ValueError("measured/open thermochemistry must identify its source-file SHA-256")
        if self.evidence.origin == "open_dataset" and not self.evidence.license_id:
            raise ValueError("open-dataset thermochemistry requires its declared license identifier")
        return self


class ActivityCoefficientKnot(Contract):
    """Caller-supplied activity coefficients in the reference species order."""

    activity_coefficients: tuple[Positive, ...] = Field(min_length=2, max_length=100)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_record_id: str = Field(min_length=1)
    evidence: Evidence

    @model_validator(mode="after")
    def valid_source_rights(self):
        if self.evidence.origin in {"measured", "open_dataset"} and self.evidence.sha256 is None:
            raise ValueError("measured/open activity coefficients must identify their source-file SHA-256")
        if self.evidence.origin == "open_dataset" and not self.evidence.license_id:
            raise ValueError("open-dataset activity coefficients require their declared license identifier")
        return self


class AqueousMassActionVanTHoffHistory(Contract):
    history_id: str = Field(min_length=1)
    reference_temperature_K: Positive
    reaction_enthalpy_standard_state: Literal["same_as_mass_action_equilibrium_standard_state"]
    times_s: tuple[float, ...] = Field(min_length=2, max_length=1000)
    temperatures_K: tuple[Positive, ...] = Field(min_length=2, max_length=1000)
    mass_action_system_at_reference: AqueousMassActionSystem
    reaction_enthalpies: tuple[ReactionEnthalpyReference, ...] = Field(min_length=1, max_length=100)
    activity_coefficients_by_knot: tuple[ActivityCoefficientKnot, ...] | None = Field(default=None, min_length=2, max_length=1000)
    maximum_absolute_log10_equilibrium_constant: Positive = Field(default=300.0, le=1000)
    reaction_thermochemistry_temperature_model_reviewed: bool
    constant_reaction_heat_capacity_change_reviewed: bool = False
    temperature_dependent_reaction_heat_capacity_reviewed: bool = False
    fixed_activity_coefficients_temperature_applicability_reviewed: bool
    activity_coefficient_temperature_history_reviewed: bool = False
    temperature_support_and_time_mapping_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def aligned_reference_network(self):
        if not isinstance(self.mass_action_system_at_reference, AqueousMassActionSystem):
            raise ValueError("a validated aqueous mass-action system at the reference temperature is required")
        system = self.mass_action_system_at_reference
        if system.temperature_K != self.reference_temperature_K:
            raise ValueError("reference temperature must exactly match the mass-action system temperature")
        if self.reaction_enthalpy_standard_state != "same_as_mass_action_equilibrium_standard_state":
            raise ValueError("reaction enthalpy and equilibrium constants must use the same declared standard state")
        if len(self.times_s) != len(self.temperatures_K):
            raise ValueError("time and temperature histories must have equal length")
        if self.activity_coefficients_by_knot is not None:
            if len(self.activity_coefficients_by_knot) != len(self.temperatures_K):
                raise ValueError("activity-coefficient history must have one row per temperature knot")
            if any(len(row.activity_coefficients) != len(system.species) for row in self.activity_coefficients_by_knot):
                raise ValueError("each activity-coefficient row must match the exact ordered system species count")
            if len({row.source_record_id for row in self.activity_coefficients_by_knot}) != len(self.activity_coefficients_by_knot):
                raise ValueError("activity-coefficient source record IDs must be unique per knot")
            provider_contracts = {
                (row.provider_id, row.provider_revision, row.provider_configuration_sha256)
                for row in self.activity_coefficients_by_knot
            }
            if len(provider_contracts) != 1:
                raise ValueError("activity-coefficient history must retain one provider revision and configuration digest")
        if self.times_s[0] != 0 or any(not math.isfinite(value) for value in self.times_s) or any(
            right <= left for left, right in zip(self.times_s[:-1], self.times_s[1:], strict=True)
        ):
            raise ValueError("temperature history requires finite, zero-based, strictly increasing times")
        reaction_ids = [row.reaction_id for row in system.reactions]
        record_ids = [row.reaction_id for row in self.reaction_enthalpies]
        if len(set(record_ids)) != len(record_ids) or set(record_ids) != set(reaction_ids):
            raise ValueError("reaction enthalpy records must cover the exact mass-action reaction ID set")
        if len({row.source_record_id for row in self.reaction_enthalpies}) != len(self.reaction_enthalpies):
            raise ValueError("thermochemical source record IDs must be unique per reaction")
        for record in self.reaction_enthalpies:
            if any(
                temperature < record.minimum_valid_temperature_K
                or temperature > record.maximum_valid_temperature_K
                for temperature in self.temperatures_K
            ):
                raise ValueError("temperature history extends beyond a reaction enthalpy record's stated support")
        return self


def evaluate_aqueous_mass_action_vant_hoff_history(
    x: AqueousMassActionVanTHoffHistory,
) -> Calculation:
    """Re-solve the existing single-phase mass-action system at each declared knot.

    Reaction enthalpies are assumed constant over their caller-declared validity
    support. Activity coefficients are either caller-supplied per knot or retained
    from the reference system after an explicit fixed-gamma applicability review.
    """
    system = x.mass_action_system_at_reference
    digest = canonical_digest(x.model_dump(mode="json"))
    records = {row.reaction_id: row for row in x.reaction_enthalpies}
    base = {
        "history_id": x.history_id,
        "input_sha256": digest,
        "reference_temperature_K": x.reference_temperature_K,
        "times_s": list(x.times_s),
        "temperatures_K": list(x.temperatures_K),
        "reference_mass_action_system_sha256": canonical_digest(system.model_dump(mode="json")),
        "reaction_enthalpy_source_records": [
            {
                "reaction_id": row.reaction_id,
                "source_record_id": row.source_record_id,
                "source_id": row.evidence.source_id,
                "evidence_origin": row.evidence.origin,
                "evidence_file_sha256": row.evidence.sha256,
                "license_id": row.evidence.license_id,
                "delta_h_reference_J_mol": row.delta_h_reference_J_mol,
                "delta_cp_reference_J_mol_K": row.delta_cp_reference_J_mol_K,
                "delta_cp_slope_J_mol_K2": row.delta_cp_slope_J_mol_K2,
                "valid_temperature_support_K": [
                    row.minimum_valid_temperature_K, row.maximum_valid_temperature_K
                ],
            }
            for row in x.reaction_enthalpies
        ],
        "activity_coefficient_source_records": [] if x.activity_coefficients_by_knot is None else [
            {
                "knot_index": index,
                "source_record_id": row.source_record_id,
                "provider_id": row.provider_id,
                "provider_revision": row.provider_revision,
                "provider_configuration_sha256": row.provider_configuration_sha256,
                "source_id": row.evidence.source_id,
                "evidence_origin": row.evidence.origin,
                "evidence_file_sha256": row.evidence.sha256,
                "license_id": row.evidence.license_id,
                "activity_coefficients": list(row.activity_coefficients),
            }
            for index, row in enumerate(x.activity_coefficients_by_knot)
        ],
    }
    reviews = {
        "reaction_thermochemistry_temperature_model_reviewed": x.reaction_thermochemistry_temperature_model_reviewed,
        "temperature_support_and_time_mapping_reviewed": x.temperature_support_and_time_mapping_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    if any(
        row.delta_cp_reference_J_mol_K is not None and row.delta_cp_slope_J_mol_K2 is None
        for row in x.reaction_enthalpies
    ):
        reviews["constant_reaction_heat_capacity_change_reviewed"] = x.constant_reaction_heat_capacity_change_reviewed
    if any(row.delta_cp_slope_J_mol_K2 is not None for row in x.reaction_enthalpies):
        reviews["temperature_dependent_reaction_heat_capacity_reviewed"] = (
            x.temperature_dependent_reaction_heat_capacity_reviewed
        )
    if x.activity_coefficients_by_knot is None:
        reviews["fixed_activity_coefficients_temperature_applicability_reviewed"] = (
            x.fixed_activity_coefficients_temperature_applicability_reviewed
        )
    else:
        reviews["activity_coefficient_temperature_history_reviewed"] = x.activity_coefficient_temperature_history_reviewed
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing,
            "equilibrium_history": [],
        })

    rows = []
    statuses = []
    ln10 = math.log(10.0)
    for index, (time_s, temperature_K) in enumerate(zip(x.times_s, x.temperatures_K, strict=True)):
        updated_reactions = []
        constants = []
        too_large = False
        for reaction in system.reactions:
            thermo = records[reaction.reaction_id]
            correction_ln_k = thermo.delta_h_reference_J_mol / MOLAR_GAS_CONSTANT_J_MOL_K * (
                1.0 / x.reference_temperature_K - 1.0 / temperature_K
            )
            if thermo.delta_cp_reference_J_mol_K is not None:
                correction_ln_k += thermo.delta_cp_reference_J_mol_K / MOLAR_GAS_CONSTANT_J_MOL_K * (
                    math.log(temperature_K / x.reference_temperature_K)
                    + x.reference_temperature_K / temperature_K - 1.0
                )
            if thermo.delta_cp_slope_J_mol_K2 is not None:
                ratio = temperature_K / x.reference_temperature_K
                integrated_linear_cp = (
                    temperature_K - x.reference_temperature_K
                    - 2.0 * x.reference_temperature_K * math.log(ratio)
                    + x.reference_temperature_K**2 * (1.0 / x.reference_temperature_K - 1.0 / temperature_K)
                )
                correction_ln_k += (
                    0.5 * thermo.delta_cp_slope_J_mol_K2
                    / MOLAR_GAS_CONSTANT_J_MOL_K * integrated_linear_cp
                )
            correction = correction_ln_k / ln10
            log_k = reaction.log10_equilibrium_constant + correction
            constants.append({
                "reaction_id": reaction.reaction_id,
                "reference_log10_K": reaction.log10_equilibrium_constant,
                "delta_h_reference_J_mol": thermo.delta_h_reference_J_mol,
                "delta_cp_reference_J_mol_K": thermo.delta_cp_reference_J_mol_K,
                "delta_cp_slope_J_mol_K2": thermo.delta_cp_slope_J_mol_K2,
                "temperature_log10_K": log_k if math.isfinite(log_k) else None,
                "source_record_id": thermo.source_record_id,
            })
            if not math.isfinite(log_k) or abs(log_k) > x.maximum_absolute_log10_equilibrium_constant:
                too_large = True
                continue
            updated_reactions.append(reaction.model_copy(update={"log10_equilibrium_constant": log_k}))
        row_base = {
            "time_s": time_s,
            "temperature_K": temperature_K,
            "reaction_log10_equilibrium_constants": constants,
        }
        if too_large:
            row = row_base | {
                "status": "out_of_scope",
                "reason": "temperature_corrected_equilibrium_constant_exceeds_numeric_budget",
            }
            statuses.append("out_of_scope")
            rows.append(row)
            continue

        evidence = {canonical_digest(item.model_dump(mode="json")): item for item in system.evidence}
        for thermo in x.reaction_enthalpies:
            evidence[canonical_digest(thermo.evidence.model_dump(mode="json"))] = thermo.evidence
        species = system.species
        activity_provider_id = system.activity_provider_id
        activity_provider_revision = system.activity_provider_revision
        activity_configuration_digest = system.activity_configuration_digest
        activity_record_digest = system.activity_record_digest
        if x.activity_coefficients_by_knot is not None:
            activity_row = x.activity_coefficients_by_knot[index]
            evidence[canonical_digest(activity_row.evidence.model_dump(mode="json"))] = activity_row.evidence
            species = tuple(
                species_row.model_copy(update={"activity_coefficient": coefficient})
                for species_row, coefficient in zip(
                    system.species, activity_row.activity_coefficients, strict=True
                )
            )
            activity_provider_id = activity_row.provider_id
            activity_provider_revision = activity_row.provider_revision
            activity_configuration_digest = activity_row.provider_configuration_sha256
            activity_record_digest = canonical_digest({
                "source_record_id": activity_row.source_record_id,
                "provider_id": activity_row.provider_id,
                "provider_revision": activity_row.provider_revision,
                "provider_configuration_sha256": activity_row.provider_configuration_sha256,
                "time_s": time_s,
                "temperature_K": temperature_K,
                "species_order": [row.species_id for row in system.species],
                "activity_coefficients": list(activity_row.activity_coefficients),
                "evidence_sha256": activity_row.evidence.sha256,
            })
        configuration_digest = canonical_digest({
            "method": "integrated_vant_hoff_caller_reaction_enthalpy_and_heat_capacity_model",
            "reference_temperature_K": x.reference_temperature_K,
            "temperature_K": temperature_K,
            "reference_equilibrium_configuration_digest": system.equilibrium_configuration_digest,
            "thermochemical_records": base["reaction_enthalpy_source_records"],
        })
        knot_system = system.model_copy(update={
            "assessment_id": f"{system.assessment_id}:{index}",
            "solution_id": f"{system.solution_id}:{index}",
            "temperature_K": temperature_K,
            "species": species,
            "reactions": tuple(updated_reactions),
            "activity_provider_id": activity_provider_id,
            "activity_provider_revision": activity_provider_revision,
            "activity_configuration_digest": activity_configuration_digest,
            "activity_record_digest": activity_record_digest,
            "equilibrium_provider_id": "matintegrity.vant_hoff_temperature_transform",
            "equilibrium_provider_revision": "1",
            "equilibrium_configuration_digest": configuration_digest,
            "equilibrium_record_digest": canonical_digest(constants),
            "evidence": tuple(evidence.values()),
        })
        calculation = aqueous_mass_action_speciation(knot_system)
        statuses.append(calculation.status)
        rows.append(row_base | {
            "status": calculation.status,
            "calculation": calculation.model_dump(mode="json"),
        })

    overall = "computed" if all(status == "computed" for status in statuses) else (
        "needs_data" if any(status == "needs_data" for status in statuses) else "out_of_scope"
    )
    return Calculation(status=overall, values=base | {
        "equilibrium_history": rows,
        "activity_coefficients_are_temperature_invariant_within_reviewed_scope": x.activity_coefficients_by_knot is None,
        "activity_coefficients_by_knot": base["activity_coefficient_source_records"],
        "reaction_thermochemistry_model": (
            "caller-supplied linearly temperature-dependent reaction heat capacity"
            if any(row.delta_cp_slope_J_mol_K2 is not None for row in x.reaction_enthalpies)
            else "constant caller-supplied reaction heat-capacity change"
            if any(row.delta_cp_reference_J_mol_K is not None for row in x.reaction_enthalpies)
            else "constant caller-supplied reaction enthalpy"
        ),
        "formulas": {
            "constant_enthalpy": "lnK(T)-lnK(Tref)=DeltaH_ref/R*(1/Tref-1/T)",
            "constant_heat_capacity_change": (
                "lnK(T)-lnK(Tref)=DeltaH_ref/R*(1/Tref-1/T)+DeltaCp_ref/R*(ln(T/Tref)+Tref/T-1)"
            ),
            "linear_heat_capacity_change": (
                "DeltaCp(T)=DeltaCp_ref+slope*(T-Tref); add slope/(2R)*[(T-Tref)-2*Tref*ln(T/Tref)+Tref^2*(1/Tref-1/T)] to lnK(T)-lnK(Tref)"
            ),
        },
    }, notes=(
        "The integrated van't Hoff relation updates only caller-supplied equilibrium constants; the existing mass-action solver recomputes each single-phase state independently at every declared temperature knot.",
        "Reaction thermochemical parameters, activity-coefficient source data/applicability, source support and time/temperature correspondence remain caller-owned inputs and reviews. Constant and linearly temperature-dependent reaction heat-capacity options have separate review gates. No phase discovery, precipitation, kinetics or corrosion rate is inferred.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.aqueous_mass_action_vant_hoff_history",
        AqueousMassActionVanTHoffHistory,
        evaluate_aqueous_mass_action_vant_hoff_history,
        {
            "times_s": "s",
            "temperatures_K": "K",
            "equilibrium_history[].reaction_log10_equilibrium_constants[].temperature_log10_K": "1",
            "equilibrium_history[].calculation.values.species[].concentration_mol_L": "mol/L",
            "activity_coefficients_by_knot[].activity_coefficients[]": "1",
            "reaction_enthalpy_source_records[].delta_h_reference_J_mol": "J/mol",
            "reaction_enthalpy_source_records[].delta_cp_reference_J_mol_K": "J/(mol K)",
            "reaction_enthalpy_source_records[].delta_cp_slope_J_mol_K2": "J/(mol K^2)",
        },
        (
            "Integrate the van't Hoff relation with caller-supplied reference reaction enthalpy, then solve the existing single-phase aqueous mass-action system independently at aligned temperature knots.",
            "A reviewed caller-supplied reaction thermochemistry model is required. Optional constant or linearly temperature-dependent reaction heat-capacity models require separate review gates. Activity coefficients are supplied per knot or retained as fixed only after review. No temperature extrapolation, phase discovery, precipitation, kinetics, gas-liquid equilibrium or corrosion validity is inferred.",
        ),
        (
            "caller_vant_hoff_aqueous_mass_action_history",
            "idaes_van_t_hoff_equilibrium_constant",
            "nist_molar_gas_constant",
            "iupac_standard_equilibrium_constant",
            "oecd_nea_reaction_heat_capacity_temperature_correction",
        ),
        qualification="user_model",
    )]

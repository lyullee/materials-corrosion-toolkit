"""Composition-history adapter to caller-supplied aqueous mass-action systems."""

from __future__ import annotations

import math
import json
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Positive, RunContext, canonical_digest
from ..registry import ModelSpec
from .aqueous_mass_action import (
    AqueousMassActionSystem,
    aqueous_mass_action_speciation,
)


class CreviceCompositionToMassActionHistory(Contract):
    schema_version: Literal["matintegrity.crevice_composition_to_mass_action_history.v1"] = (
        "matintegrity.crevice_composition_to_mass_action_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    composition_result: AssessmentResult
    composition_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    mass_action_systems_by_knot: tuple[AqueousMassActionSystem, ...] = Field(min_length=2, max_length=5000)
    composition_derived_constraint_ids: tuple[str, ...] = ()
    zero_concentration_initial_activity_guess: Positive | None = None
    composition_mapping_and_constraint_basis_reviewed: bool
    composition_derived_constraint_semantics_reviewed: bool
    zero_concentration_seed_is_numerical_only_reviewed: bool
    each_temperature_specific_parameter_set_reviewed: bool
    no_automatic_phase_change_or_kinetic_interpretation_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_composition_and_system_alignment(self):
        result = self.composition_result
        if result.model_id != "integration.crevice_electrochemical_composition_history" or result.status != "computed":
            raise ValueError("a computed digest-pinned crevice composition history is required")
        expected_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_digest:
            raise ValueError("composition assessment input digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != self.composition_result_sha256:
            raise ValueError("composition result digest mismatch")
        history = result.values.get("composition_history")
        if not isinstance(history, list) or len(history) < 2:
            raise ValueError("composition history must contain at least two exact knots")
        if result.values.get("composition_history_sha256") != canonical_digest(history):
            raise ValueError("composition-history digest mismatch")
        if len(self.mass_action_systems_by_knot) != len(history):
            raise ValueError("one caller-supplied mass-action parameter system is required at each composition knot")
        first_system = self.mass_action_systems_by_knot[0]
        first_species_ids = tuple(sorted(row.species_id for row in first_system.species))
        first_species_signature = {
            row.species_id: (
                row.charge_number,
                tuple(sorted((row.elemental_composition or {}).items()))
                if row.elemental_composition is not None else None,
            )
            for row in first_system.species
        }
        first_reactions = tuple(
            (row.reaction_id, tuple((term.species_id, term.coefficient) for term in row.terms))
            for row in first_system.reactions
        )
        first_constraints = tuple(
            (row.constraint_id, tuple((term.species_id, term.coefficient) for term in row.terms))
            for row in first_system.constraints
        )
        constraint_ids = {row.constraint_id for row in first_system.constraints}
        if len(self.composition_derived_constraint_ids) != len(set(self.composition_derived_constraint_ids)):
            raise ValueError("composition-derived constraint IDs must be unique")
        if set(self.composition_derived_constraint_ids) - constraint_ids:
            raise ValueError("composition-derived constraint IDs must exist in every supplied system")
        for state, system in zip(history, self.mass_action_systems_by_knot, strict=True):
            if system.temperature_K != state.get("temperature_K"):
                raise ValueError("temperature-specific mass-action parameters must match the composition knot")
            if system.activity_standard_state != "molarity_1_mol_L":
                raise ValueError("the composition adapter requires the declared 1 mol/L activity standard state")
            if tuple(sorted(row.species_id for row in system.species)) != first_species_ids:
                raise ValueError("aqueous species IDs must remain fixed across the supplied knot systems")
            species_signature = {
                row.species_id: (
                    row.charge_number,
                    tuple(sorted((row.elemental_composition or {}).items()))
                    if row.elemental_composition is not None else None,
                )
                for row in system.species
            }
            if species_signature != first_species_signature:
                raise ValueError("species charges and elemental formulas must remain fixed across knots")
            if tuple(
                (row.reaction_id, tuple((term.species_id, term.coefficient) for term in row.terms))
                for row in system.reactions
            ) != first_reactions:
                raise ValueError("reaction identities and stoichiometry must remain fixed across knots")
            if tuple(
                (row.constraint_id, tuple((term.species_id, term.coefficient) for term in row.terms))
                for row in system.constraints
            ) != first_constraints:
                raise ValueError("constraint identities and stoichiometry must remain fixed across knots")
            composition_species = state.get("species")
            if not isinstance(composition_species, list):
                raise ValueError("each composition knot must contain a species list")
            concentrations = {row.get("species_id"): row.get("concentration_mol_m3") for row in composition_species}
            if set(concentrations) != set(first_species_ids):
                raise ValueError("composition species IDs must exactly match the aqueous network species")
            if any(
                isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0.0
                for value in concentrations.values()
            ):
                raise ValueError("composition concentrations must be finite and nonnegative")
            if any(value == 0.0 for value in concentrations.values()):
                if self.zero_concentration_initial_activity_guess is None:
                    raise ValueError("zero concentration requires an explicit positive numerical initial-activity seed")
                if not self.zero_concentration_seed_is_numerical_only_reviewed:
                    raise ValueError("zero-concentration numerical seeding requires explicit review")
        return self


def _build_knot_system(
    system: AqueousMassActionSystem,
    composition_row: dict,
    zero_seed: float | None,
    composition_derived_constraint_ids: frozenset[str],
) -> AqueousMassActionSystem:
    concentrations_mol_L = {
        row["species_id"]: row["concentration_mol_m3"] / 1000.0
        for row in composition_row["species"]
    }
    species_rows = []
    for species in system.species:
        concentration = concentrations_mol_L[species.species_id]
        activity_guess = species.activity_coefficient * concentration
        if concentration == 0.0:
            if zero_seed is None:
                raise ValueError("zero concentration has no positive initial activity guess")
            activity_guess = zero_seed
        if not math.isfinite(activity_guess) or activity_guess <= 0.0:
            raise ArithmeticError("composition-derived activity is outside positive finite support")
        species_rows.append(species.model_dump(mode="python") | {"initial_activity": activity_guess})
    constraints = []
    for constraint in system.constraints:
        if constraint.constraint_id in composition_derived_constraint_ids:
            target = math.fsum(
                term.coefficient * concentrations_mol_L[term.species_id]
                for term in constraint.terms
            )
            if not math.isfinite(target):
                raise ArithmeticError("composition-derived analytical constraint exceeds finite support")
        else:
            target = constraint.target_mol_L
        constraints.append(constraint.model_dump(mode="python") | {"target_mol_L": target})
    payload = system.model_dump(mode="python")
    knot_tag = f"knot-{composition_row['time_s']:.12g}s"
    payload["assessment_id"] = f"{system.assessment_id}-{knot_tag}"
    payload["species"] = species_rows
    payload["constraints"] = constraints
    return AqueousMassActionSystem.model_validate_json(json.dumps(payload))


def evaluate_crevice_composition_to_mass_action_history(
    x: CreviceCompositionToMassActionHistory,
) -> Calculation:
    source = x.composition_result
    history = source.values["composition_history"]
    reviews = {
        "composition_mapping_and_constraint_basis_reviewed": x.composition_mapping_and_constraint_basis_reviewed,
        "composition_derived_constraint_semantics_reviewed": x.composition_derived_constraint_semantics_reviewed,
        "each_temperature_specific_parameter_set_reviewed": x.each_temperature_specific_parameter_set_reviewed,
        "no_automatic_phase_change_or_kinetic_interpretation_reviewed": x.no_automatic_phase_change_or_kinetic_interpretation_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
        "zero_concentration_seed_is_numerical_only_reviewed": (
            x.zero_concentration_seed_is_numerical_only_reviewed
            if x.zero_concentration_initial_activity_guess is not None else True
        ),
    }
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": source.values["asset_id"],
        "location_id": source.values["location_id"],
        "physical_scope_id": source.values["physical_scope_id"],
        "clock_id": source.values["clock_id"],
        "composition_result_sha256": x.composition_result_sha256,
        "composition_history_sha256": source.values["composition_history_sha256"],
        "activity_standard_state": "1 mol/L",
        "concentration_conversion": "mol/m3 divided by 1000 = mol/L",
        "composition_derived_constraint_ids": list(x.composition_derived_constraint_ids),
        "constraint_target_policy": "rebuild_only_explicitly_selected_constraint_targets_from_current_composition; preserve_all_other_caller_targets",
        "temperature_policy": "one_caller_parameter_system_per_exact_composition_knot",
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    results = []
    for index, (state, template) in enumerate(zip(history, x.mass_action_systems_by_knot, strict=True)):
        try:
            system = _build_knot_system(
                template,
                state,
                x.zero_concentration_initial_activity_guess,
                frozenset(x.composition_derived_constraint_ids),
            )
            calculation = aqueous_mass_action_speciation(system)
        except (ArithmeticError, OverflowError, ValueError) as error:
            return Calculation(status="out_of_scope", values=base | {
                "failed_knot_index": index,
                "failed_time_s": state["time_s"],
                "failure_reason": str(error),
                "computed_prefix": results,
            })
        results.append({
            "time_s": state["time_s"],
            "temperature_K": system.temperature_K,
            "aqueous_system_input_sha256": canonical_digest(system.model_dump(mode="json")),
            "status": calculation.status,
            "values": calculation.values,
            "notes": calculation.notes,
        })
        if calculation.status != "computed":
            return Calculation(
                status=calculation.status,
                values=base | {"knot_results": results, "first_noncomputed_knot_index": index},
                notes=("Knotwise speciation stopped at the first solver result that was not computed.",),
            )
    return Calculation(values=base | {
        "knot_results": results,
        "knot_results_sha256": canonical_digest(results),
        "computed_knot_count": len(results),
    }, notes=(
        "Each mass-action system is a caller-supplied temperature-specific network. Composition concentrations seed positive activities using fixed gamma values; only constraint IDs explicitly selected by the caller are reconstructed from composition, while all other targets remain unchanged.",
        "The adapter does not infer reactions, equilibrium constants, activity coefficients, constraint meaning or temperature dependence. Precipitation, gas exchange, transport, kinetic sources and wall-loss interpretation remain outside scope.",
    ))


def _validate_context(x: CreviceCompositionToMassActionHistory, context: RunContext) -> None:
    source = x.composition_result.values
    if context.asset_id != source.get("asset_id"):
        raise ValueError("run context asset must match the upstream crevice composition")
    if context.location_id != source.get("location_id"):
        raise ValueError("run context location must match the upstream crevice composition")
    if context.time_basis != source.get("clock_id"):
        raise ValueError("run context time basis must match the upstream crevice clock ID")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.crevice_composition_to_aqueous_mass_action_history",
        CreviceCompositionToMassActionHistory,
        evaluate_crevice_composition_to_mass_action_history,
        {
            "knot_results[].time_s": "s",
            "knot_results[].temperature_K": "K",
            "knot_results[].values.species.concentration_mol_L": "mol/L",
            "knot_results[].values.species.dimensionless_activity": "1",
            "knot_results[].values.constraint_closure.residual_mol_L": "mol/L",
        },
        (
            "Every composition knot binds to a caller-supplied aqueous reaction/constraint network and exact-temperature parameter set.",
            "The transfer composition is in mol/m3 and is converted to mol/L; fixed activity coefficients map concentrations to positive dimensionless initial activity guesses under a 1 mol/L standard state.",
            "Only explicitly caller-selected linear constraint IDs are rebuilt from the current composition; unselected targets such as a reviewed zero-charge condition are preserved. The network is solved as a single aqueous phase without phase-change or wall-loss inference.",
        ),
        ("crevice_composition_to_caller_aqueous_mass_action_knot_history",),
        qualification="user_model",
        context_validator=_validate_context,
    )]

"""Exact-knot aqueous speciation histories using caller-supplied B-dot records."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, RunContext, canonical_digest
from ..registry import ModelSpec
from .aqueous_activity_iteration import AqueousBdotIteration, aqueous_bdot_self_consistent_speciation


class AqueousBdotSpeciationHistory(Contract):
    """Independently solve one complete B-dot/mass-action request at each exact knot."""

    schema_version: Literal["matintegrity.aqueous_bdot_speciation_history.v1"] = (
        "matintegrity.aqueous_bdot_speciation_history.v1"
    )
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    elapsed_time_s: tuple[float, ...] = Field(min_length=2, max_length=5000)
    knot_requests: tuple[AqueousBdotIteration, ...] = Field(min_length=2, max_length=5000)
    exact_time_temperature_parameter_mapping_reviewed: bool
    stable_species_reaction_constraint_topology_reviewed: bool
    no_interpolation_or_extrapolation_between_knots_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_exact_knot_inputs(self):
        if len(self.elapsed_time_s) != len(self.knot_requests):
            raise ValueError("each exact history time requires one complete B-dot request")
        if any(not math.isfinite(value) or value < 0.0 for value in self.elapsed_time_s):
            raise ValueError("history times must be finite nonnegative seconds")
        if self.elapsed_time_s[0] != 0.0 or any(
            right <= left for left, right in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)
        ):
            raise ValueError("history must start at zero and increase strictly")

        first = self.knot_requests[0]
        species_signature = tuple(
            (row.species_id, row.charge_number,
             tuple(sorted((row.elemental_composition or {}).items()))
             if row.elemental_composition is not None else None)
            for row in first.system.species
        )
        reaction_signature = tuple(
            (row.reaction_id, tuple((term.species_id, term.coefficient) for term in row.terms))
            for row in first.system.reactions
        )
        constraint_signature = tuple(
            (row.constraint_id, tuple((term.species_id, term.coefficient) for term in row.terms))
            for row in first.system.constraints
        )
        provider_signature = (first.parameter_provider_id, first.parameter_provider_revision)

        for request in self.knot_requests:
            current_species = tuple(
                (row.species_id, row.charge_number,
                 tuple(sorted((row.elemental_composition or {}).items()))
                 if row.elemental_composition is not None else None)
                for row in request.system.species
            )
            current_reactions = tuple(
                (row.reaction_id, tuple((term.species_id, term.coefficient) for term in row.terms))
                for row in request.system.reactions
            )
            current_constraints = tuple(
                (row.constraint_id, tuple((term.species_id, term.coefficient) for term in row.terms))
                for row in request.system.constraints
            )
            if (current_species, current_reactions, current_constraints) != (
                species_signature, reaction_signature, constraint_signature
            ):
                raise ValueError("species order and reaction/constraint topology must remain fixed across knots")
            if (request.parameter_provider_id, request.parameter_provider_revision) != provider_signature:
                raise ValueError("B-dot parameter provider identity and revision must remain fixed across the history")

        return self


def aqueous_bdot_speciation_history(request: AqueousBdotSpeciationHistory) -> Calculation:
    """Solve exact knot requests sequentially and retain a diagnostic prefix on failure."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "history_id": request.history_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "clock_id": request.time_basis,
        "elapsed_time_s": list(request.elapsed_time_s),
        "temperature_K": [row.system.temperature_K for row in request.knot_requests],
        "parameter_temperature_K": [row.parameter_temperature_K for row in request.knot_requests],
        "input_sha256": digest,
        "inter_knot_policy": "each_exact_knot_solved_independently_without_interpolation_or_extrapolation",
    }
    reviews = {
        "exact_time_temperature_parameter_mapping_reviewed": request.exact_time_temperature_parameter_mapping_reviewed,
        "stable_species_reaction_constraint_topology_reviewed": request.stable_species_reaction_constraint_topology_reviewed,
        "no_interpolation_or_extrapolation_between_knots_reviewed": request.no_interpolation_or_extrapolation_between_knots_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing,
            "computed_prefix": [],
        }, notes=("Review exact knot-to-input mapping, stable network topology, parameter support and computational-use rights before solving.",))

    knots = []
    for index, (time_s, knot_request) in enumerate(zip(request.elapsed_time_s, request.knot_requests, strict=True)):
        result = aqueous_bdot_self_consistent_speciation(knot_request)
        knot = {
            "knot_index": index,
            "time_s": time_s,
            "temperature_K": knot_request.system.temperature_K,
            "parameter_temperature_K": knot_request.parameter_temperature_K,
            "request_sha256": canonical_digest(knot_request.model_dump(mode="json")),
            "result_sha256": canonical_digest(result.model_dump(mode="json")),
            "status": result.status,
            "values": result.values,
            "notes": list(result.notes),
        }
        if result.status != "computed":
            return Calculation(status=result.status, values=base | {
                "computed_prefix": knots,
                "computed_prefix_sha256": canonical_digest(knots),
                "failed_knot_index": index,
                "failed_knot_time_s": time_s,
                "failed_knot_status": result.status,
                "failed_knot_result": knot,
                "failure_policy": "no_incomplete_history_promoted_as_computed",
            }, notes=("The exact-knot B-dot history stopped at its first non-computed state; earlier knots remain diagnostic prefix only.",))
        knots.append(knot)

    first = request.knot_requests[0]
    return Calculation(values=base | {
        "knot_results": knots,
        "knot_results_sha256": canonical_digest(knots),
        "computed_knot_count": len(knots),
        "complete_history": True,
        "parameter_provider_id": first.parameter_provider_id,
        "parameter_provider_revision": first.parameter_provider_revision,
        "parameter_configuration_sha256_by_knot": [
            row.parameter_configuration_sha256 for row in request.knot_requests
        ],
        "parameter_record_sha256_by_knot": [
            row.parameter_record_sha256 for row in request.knot_requests
        ],
    }, notes=(
        "Each supplied time knot was solved independently using its own evidence-bound temperature and B-dot parameter record.",
        "No interpolation, kinetic reaction model, phase discovery, precipitation history or corrosion qualification is inferred between knots.",
    ))


def _validate_context(request: AqueousBdotSpeciationHistory, context: RunContext) -> None:
    if (context.asset_id, context.location_id, context.time_basis) != (
        request.asset_id, request.location_id, request.time_basis
    ):
        raise ValueError("RunContext asset, location and time basis must match the B-dot history")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.aqueous_bdot_speciation_history",
        AqueousBdotSpeciationHistory,
        aqueous_bdot_speciation_history,
        {
            "elapsed_time_s[]": "s",
            "temperature_K[]": "K",
            "parameter_temperature_K[]": "K",
            "knot_results[].time_s": "s",
            "knot_results[].values.ionic_strength_mol_kg": "mol/kg_water",
        },
        (
            "Each exact time knot carries a complete caller-reviewed mass-action system and B-dot parameter record matched to that knot's temperature.",
            "Species ordering and reaction/constraint topology remain fixed; constants, solution constraints, activity coefficients and evidence-bound B-dot records may vary only through explicit knot inputs.",
            "The adapter does not interpolate, extrapolate, infer kinetics, discover phases or qualify a corrosion rate.",
        ),
        (
            "caller_general_aqueous_mass_action_speciation",
            "usgs_phreeqc_llnl_bdot_activity",
            "molality_to_molarity_activity_standard_state_bridge",
        ),
        qualification="user_model",
        context_validator=_validate_context,
    )]

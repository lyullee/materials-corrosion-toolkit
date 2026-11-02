"""Exact-knot histories for caller-owned composition-dependent activity providers."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, RunContext, canonical_digest
from ..registry import ModelSpec
from .aqueous_external_activity import (
    ExternalAqueousActivityIteration,
    aqueous_external_activity_self_consistent_speciation,
)


class ExternalAqueousActivityHistory(Contract):
    """Run one self-consistent external-activity solve at each supplied knot."""

    schema_version: Literal["matintegrity.external_aqueous_activity_history.v1"] = (
        "matintegrity.external_aqueous_activity_history.v1"
    )
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    elapsed_time_s: tuple[float, ...] = Field(min_length=2, max_length=5000)
    knot_requests: tuple[ExternalAqueousActivityIteration, ...] = Field(min_length=2, max_length=5000)
    exact_time_temperature_parameter_mapping_reviewed: bool
    stable_species_reaction_topology_reviewed: bool
    no_interpolation_or_extrapolation_between_knots_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_history_topology(self):
        if len(self.elapsed_time_s) != len(self.knot_requests):
            raise ValueError("one external-activity request is required for each exact history knot")
        if any(not math.isfinite(t) or t < 0.0 for t in self.elapsed_time_s):
            raise ValueError("history times must be finite nonnegative seconds")
        if self.elapsed_time_s[0] != 0.0 or any(
            right <= left for left, right in zip(self.elapsed_time_s, self.elapsed_time_s[1:])
        ):
            raise ValueError("history must start at zero and increase strictly")
        first = self.knot_requests[0]
        species_signature = tuple(sorted((
            row.species_id, row.charge_number,
            tuple(sorted((row.elemental_composition or {}).items()))
            if row.elemental_composition is not None else None,
        ) for row in first.system.species))
        reaction_signature = tuple(sorted((
            row.reaction_id, tuple(sorted((term.species_id, term.coefficient) for term in row.terms)),
        ) for row in first.system.reactions))
        constraint_signature = tuple(sorted((
            row.constraint_id, tuple(sorted((term.species_id, term.coefficient) for term in row.terms)),
        ) for row in first.system.constraints))
        provider_signature = (
            first.activity_provider_id, first.activity_provider_revision,
            first.activity_configuration_sha256, first.single_ion_activity_convention_id,
        )
        for time_s, request in zip(self.elapsed_time_s, self.knot_requests, strict=True):
            if not math.isfinite(request.system.temperature_K) or request.system.temperature_K <= 0.0:
                raise ValueError("each knot must have a finite positive absolute temperature")
            current_species = tuple(sorted((
                row.species_id, row.charge_number,
                tuple(sorted((row.elemental_composition or {}).items()))
                if row.elemental_composition is not None else None,
            ) for row in request.system.species))
            current_reactions = tuple(sorted((
                row.reaction_id, tuple(sorted((term.species_id, term.coefficient) for term in row.terms)),
            ) for row in request.system.reactions))
            current_constraints = tuple(sorted((
                row.constraint_id, tuple(sorted((term.species_id, term.coefficient) for term in row.terms)),
            ) for row in request.system.constraints))
            if (current_species, current_reactions, current_constraints) != (
                species_signature, reaction_signature, constraint_signature
            ):
                raise ValueError("species identities and reaction/constraint topology must remain fixed across knots")
            if (request.activity_provider_id, request.activity_provider_revision,
                request.activity_configuration_sha256, request.single_ion_activity_convention_id) != provider_signature:
                raise ValueError("activity provider identity, revision, configuration and convention must remain fixed")
            if request.system.temperature_K <= 0.0:
                raise ValueError("knot temperature must be positive")
        return self


def aqueous_external_activity_speciation_history(
    request: ExternalAqueousActivityHistory, *, activity_provider
) -> Calculation:
    """Solve each exact time/temperature knot and retain only a complete history."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "history_id": request.history_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "clock_id": request.time_basis,
        "elapsed_time_s": list(request.elapsed_time_s),
        "temperature_K": [row.system.temperature_K for row in request.knot_requests],
        "input_sha256": digest,
        "inter_knot_policy": "no_interpolation_or_extrapolation_each_exact_knot_solved_independently",
    }
    reviews = {
        "exact_time_temperature_parameter_mapping_reviewed": request.exact_time_temperature_parameter_mapping_reviewed,
        "stable_species_reaction_topology_reviewed": request.stable_species_reaction_topology_reviewed,
        "no_interpolation_or_extrapolation_between_knots_reviewed": request.no_interpolation_or_extrapolation_between_knots_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [key for key, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing, "computed_prefix": []})
    if not callable(activity_provider):
        return Calculation(status="needs_data", values=base | {
            "reason": "external_activity_provider_callback_is_unavailable", "computed_prefix": [],
        })
    knots = []
    for index, (time_s, knot_request) in enumerate(zip(request.elapsed_time_s, request.knot_requests, strict=True)):
        result = aqueous_external_activity_self_consistent_speciation(
            knot_request, activity_provider=activity_provider
        )
        knot = {
            "knot_index": index,
            "time_s": time_s,
            "temperature_K": knot_request.system.temperature_K,
            "request_sha256": canonical_digest(knot_request.model_dump(mode="json")),
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
            }, notes=(
                "The exact-knot activity history stopped at its first non-computed state; prior knots are diagnostic prefix only.",
            ))
        knots.append(knot)
    return Calculation(values=base | {
        "knot_results": knots,
        "knot_results_sha256": canonical_digest(knots),
        "computed_knot_count": len(knots),
        "complete_history": True,
        "provider_id": request.knot_requests[0].activity_provider_id,
        "provider_revision": request.knot_requests[0].activity_provider_revision,
        "provider_configuration_sha256": request.knot_requests[0].activity_configuration_sha256,
        "activity_parameter_record_sha256_by_knot": [
            row.activity_parameter_record_sha256 for row in request.knot_requests
        ],
    }, notes=(
        "Each supplied knot was solved independently with the caller provider; no thermodynamic values were interpolated between knots.",
        "This sequential equilibrium history is not transient reaction kinetics, transport coupling, phase selection or corrosion qualification.",
    ))


def _validate_context(request: ExternalAqueousActivityHistory, context: RunContext) -> None:
    if (context.asset_id, context.location_id, context.time_basis) != (
        request.asset_id, request.location_id, request.time_basis
    ):
        raise ValueError("RunContext asset, location and time basis must match the aqueous activity history")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.aqueous_external_activity_speciation_history",
        ExternalAqueousActivityHistory,
        aqueous_external_activity_speciation_history,
        {
            "elapsed_time_s[]": "s",
            "temperature_K[]": "K",
            "knot_results[].time_s": "s",
            "knot_results[].temperature_K": "K",
            "knot_results[].values.ionic_strength_mol_kg": "mol/kg_water",
        },
        (
            "Every exact time knot carries a separately reviewed mass-action system and caller-owned composition-dependent activity provider record.",
            "Species identities and reaction/constraint topology remain fixed; per-knot constants and provider parameter records may vary explicitly.",
            "No interpolation, kinetic interpretation, phase selection or corrosion qualification is performed.",
        ),
        ("caller_external_aqueous_activity_speciation_history",),
        qualification="user_model",
        context_validator=_validate_context,
        runtime_dependency_names=("activity_provider",),
    )]

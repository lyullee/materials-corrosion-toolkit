"""Finite alternative-reaction-network response envelope at one fixed aqueous state."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .models.aqueous_mass_action import AqueousMassActionSystem, aqueous_mass_action_speciation
from .registry import ModelSpec


class AqueousMassActionTopologyCase(Contract):
    """One complete, independently sourced alternative reaction topology."""

    topology_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    request: AqueousMassActionSystem


class AqueousMassActionTopologyEnvelope(Contract):
    """Compare finite caller-owned alternative reaction networks with fixed species/balances."""

    schema_version: Literal["matintegrity.aqueous_mass_action_topology_envelope.v1"] = (
        "matintegrity.aqueous_mass_action_topology_envelope.v1"
    )
    comparison_id: str = Field(min_length=1)
    topologies: tuple[AqueousMassActionTopologyCase, ...] = Field(min_length=2, max_length=64)
    alternative_networks_are_complete_caller_systems_reviewed: bool
    fixed_species_inventory_and_solution_state_reviewed: bool
    common_balance_constraints_and_standard_state_reviewed: bool
    provider_revisions_and_topology_comparability_reviewed: bool
    finite_topology_set_and_no_probability_interpretation_reviewed: bool

    @model_validator(mode="after")
    def alternative_topology_contract(self):
        ids = [row.topology_id for row in self.topologies]
        if len(ids) != len(set(ids)):
            raise ValueError("topology IDs must be unique")
        requests = [row.request for row in self.topologies]
        if len({row.solution_id for row in requests}) != 1:
            raise ValueError("alternative topologies must share one caller solution identity")
        if len({row.temperature_K for row in requests}) != 1:
            raise ValueError("alternative topologies must use the same declared temperature")
        if len({row.activity_standard_state for row in requests}) != 1:
            raise ValueError("alternative topologies must use the same activity standard state")
        if len({(row.activity_provider_id, row.activity_provider_revision, row.activity_record_digest) for row in requests}) != 1:
            raise ValueError("alternative topologies must share one digest-pinned activity-provider record")
        if len({(row.equilibrium_provider_id, row.equilibrium_provider_revision) for row in requests}) != 1:
            raise ValueError("alternative topologies must share one equilibrium-provider family and revision")

        def species_state(request: AqueousMassActionSystem):
            return tuple(row.model_dump(mode="json") for row in request.species)

        def constraints(request: AqueousMassActionSystem):
            return tuple(row.model_dump(mode="json") for row in request.constraints)

        if any(species_state(row) != species_state(requests[0]) for row in requests[1:]):
            raise ValueError("species order, charge, formula, fixed activities and initial guesses must be identical")
        if any(constraints(row) != constraints(requests[0]) for row in requests[1:]):
            raise ValueError("the same exact balance-constraint identities, coefficients, targets and scales are required")

        def reaction_topology(request: AqueousMassActionSystem):
            return tuple(
                (row.reaction_id, tuple((term.species_id, term.coefficient) for term in row.terms))
                for row in request.reactions
            )

        topologies = [reaction_topology(row) for row in requests]
        if len(set(topologies)) < 2:
            raise ValueError("at least two distinct reaction topologies are required")
        return self


def _species_envelope(rows: list[dict]) -> list[dict]:
    species_ids = [row["species_id"] for row in rows[0]["species"]]
    output = []
    for species_id in species_ids:
        samples = []
        for topology in rows:
            species = next(row for row in topology["species"] if row["species_id"] == species_id)
            samples.append((topology["topology_id"], species))
        activity = [(topology_id, row["dimensionless_activity"]) for topology_id, row in samples]
        concentration = [(topology_id, row["concentration_mol_L"]) for topology_id, row in samples]
        min_activity, max_activity = min(activity, key=lambda row: row[1]), max(activity, key=lambda row: row[1])
        min_concentration = min(concentration, key=lambda row: row[1])
        max_concentration = max(concentration, key=lambda row: row[1])
        output.append({
            "species_id": species_id,
            "dimensionless_activity_min": min_activity[1],
            "dimensionless_activity_min_topology_id": min_activity[0],
            "dimensionless_activity_max": max_activity[1],
            "dimensionless_activity_max_topology_id": max_activity[0],
            "activity_span_dimensionless": max_activity[1] - min_activity[1],
            "concentration_min_mol_L": min_concentration[1],
            "concentration_min_topology_id": min_concentration[0],
            "concentration_max_mol_L": max_concentration[1],
            "concentration_max_topology_id": max_concentration[0],
            "concentration_span_mol_L": max_concentration[1] - min_concentration[1],
        })
    return output


def evaluate_aqueous_mass_action_topology_envelope(request: AqueousMassActionTopologyEnvelope) -> Calculation:
    """Solve each complete caller reaction network independently and summarize exact alternatives."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "comparison_id": request.comparison_id,
        "input_sha256": input_digest,
        "solution_id": request.topologies[0].request.solution_id,
        "temperature_K": request.topologies[0].request.temperature_K,
        "activity_standard_state": request.topologies[0].request.activity_standard_state,
        "species_inventory_sha256": canonical_digest([
            row.model_dump(mode="json") for row in request.topologies[0].request.species
        ]),
        "common_balance_constraints_sha256": canonical_digest([
            row.model_dump(mode="json") for row in request.topologies[0].request.constraints
        ]),
        "alternative_set_kind": "finite_caller_declared_reaction_topologies_only",
    }
    reviews = {
        "alternative_networks_are_complete_caller_systems_reviewed": request.alternative_networks_are_complete_caller_systems_reviewed,
        "fixed_species_inventory_and_solution_state_reviewed": request.fixed_species_inventory_and_solution_state_reviewed,
        "common_balance_constraints_and_standard_state_reviewed": request.common_balance_constraints_and_standard_state_reviewed,
        "provider_revisions_and_topology_comparability_reviewed": request.provider_revisions_and_topology_comparability_reviewed,
        "finite_topology_set_and_no_probability_interpretation_reviewed": request.finite_topology_set_and_no_probability_interpretation_reviewed,
    }
    missing = [key for key, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "completed_topology_count": 0,
            "topology_results": [],
            "missing_reviews": missing,
            "probability_or_distribution": None,
        })

    completed = []
    for case in request.topologies:
        result = aqueous_mass_action_speciation(case.request)
        row = {
            "topology_id": case.topology_id,
            "description": case.description,
            "request_sha256": canonical_digest(case.request.model_dump(mode="json")),
            "result_sha256": canonical_digest(result.model_dump(mode="json")),
            "status": result.status,
            "equilibrium_configuration_digest": case.request.equilibrium_configuration_digest,
            "equilibrium_record_digest": case.request.equilibrium_record_digest,
            "equilibrium_provider_id": case.request.equilibrium_provider_id,
            "equilibrium_provider_revision": case.request.equilibrium_provider_revision,
            "reaction_definitions": [reaction.model_dump(mode="json") for reaction in case.request.reactions],
            "evidence": [item.model_dump(mode="json") for item in case.request.evidence],
            "result_values": result.values,
        }
        if result.status != "computed":
            return Calculation(status=result.status, values=base | {
                "completed_topology_count": len(completed),
                "computed_topology_prefix": completed,
                "first_incomplete_topology": row,
                "species_envelope": None,
                "failed_case_is_not_omitted": True,
            }, notes=(
                "A topology envelope is withheld unless every caller-declared complete network computes; prior successful topologies remain in input order.",
            ))
        species = result.values.get("species")
        if not isinstance(species, list) or len(species) != len(case.request.species):
            return Calculation(status="out_of_scope", values=base | {
                "completed_topology_count": len(completed),
                "computed_topology_prefix": completed,
                "first_incomplete_topology": row,
                "failure_reason": "mass_action_result_lacks_complete_species_outputs",
            })
        row["species"] = species
        completed.append(row)

    envelope = _species_envelope(completed)
    for item in envelope:
        if not all(math.isfinite(value) for value in (
            item["dimensionless_activity_min"], item["dimensionless_activity_max"],
            item["activity_span_dimensionless"], item["concentration_min_mol_L"],
            item["concentration_max_mol_L"], item["concentration_span_mol_L"],
        )):
            return Calculation(status="out_of_scope", values=base | {
                "completed_topology_count": len(completed),
                "topology_results": completed,
                "failure_reason": "topology_envelope_exceeds_finite_numeric_support",
            })
    return Calculation(values=base | {
        "completed_topology_count": len(completed),
        "topology_results": completed,
        "species_envelope": envelope,
        "topology_weights": None,
        "probability_or_confidence": None,
        "distribution_interpretation": "none",
        "not_inferred": ["network_completeness_beyond_provided_alternatives", "phase_selection", "kinetics", "precipitation", "corrosion_rate", "qualification"],
    }, notes=(
        "Each distinct caller reaction topology is solved independently at the same species, solution, temperature, activity state and balance constraints.",
        "The extrema describe only this finite set of complete caller networks; they are not a probability distribution, confidence range, global chemistry bound or evidence that any topology is correct.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="chemistry.aqueous_mass_action_topology_envelope",
        input_type=AqueousMassActionTopologyEnvelope,
        evaluator=evaluate_aqueous_mass_action_topology_envelope,
        units={
            "temperature_K": "K",
            "topology_results[].result_values.species[].dimensionless_activity": "1",
            "topology_results[].result_values.species[].concentration_mol_L": "mol/L",
            "species_envelope[].dimensionless_activity_min": "1",
            "species_envelope[].dimensionless_activity_max": "1",
            "species_envelope[].activity_span_dimensionless": "1",
            "species_envelope[].concentration_min_mol_L": "mol/L",
            "species_envelope[].concentration_max_mol_L": "mol/L",
            "species_envelope[].concentration_span_mol_L": "mol/L",
        },
        assumptions=(
            "Each case is a complete caller-declared single-liquid mass-action network using the same solution identity, temperature, species inventory, fixed activities, provider record, standard state and balance constraints.",
            "Only reaction IDs, stoichiometric topology, configuration and equilibrium record values distinguish alternatives; each network is independently charge/formula validated and solved by the existing mass-action model.",
            "Report unweighted extrema over the supplied finite reaction-topology alternatives only; no probability, confidence, global completeness or network selection is provided.",
            "If any network fails, withhold the complete envelope and retain the successful input-order prefix and first failure.",
        ),
        source_ids=("caller_aqueous_mass_action_topology_envelope",),
        qualification="user_model",
    )]

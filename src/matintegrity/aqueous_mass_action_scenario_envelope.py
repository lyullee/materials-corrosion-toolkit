"""Finite caller-declared response envelope for one fixed aqueous network topology."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .models.aqueous_mass_action import AqueousMassActionSystem, aqueous_mass_action_speciation
from .registry import ModelSpec


class AqueousMassActionScenario(Contract):
    """One complete caller-provided parameter case for the same equation topology."""

    scenario_id: str = Field(min_length=1)
    scenario_label: str = Field(min_length=1)
    request: AqueousMassActionSystem


class AqueousMassActionScenarioEnvelope(Contract):
    """Solve and summarize a finite set of independently declared mass-action cases."""

    schema_version: Literal["matintegrity.aqueous_mass_action_scenario_envelope.v1"] = (
        "matintegrity.aqueous_mass_action_scenario_envelope.v1"
    )
    envelope_id: str = Field(min_length=1)
    scenarios: tuple[AqueousMassActionScenario, ...] = Field(min_length=2, max_length=256)
    solution_identity_and_fixed_network_topology_reviewed: bool
    finite_scenario_set_is_caller_owned_and_complete_for_comparison_reviewed: bool
    provider_family_and_revision_are_comparable_reviewed: bool
    no_probability_or_distribution_interpretation_reviewed: bool

    @model_validator(mode="after")
    def scenarios_share_topology(self):
        scenario_ids = [row.scenario_id for row in self.scenarios]
        if len(set(scenario_ids)) != len(scenario_ids):
            raise ValueError("scenario IDs must be unique")
        requests = [row.request for row in self.scenarios]
        identities = {
            (
                request.solution_id,
                request.activity_standard_state,
                request.activity_provider_id,
                request.activity_provider_revision,
                request.equilibrium_provider_id,
                request.equilibrium_provider_revision,
            )
            for request in requests
        }
        if len(identities) != 1:
            raise ValueError("scenario cases must share solution, standard-state and provider family/revision identities")

        def topology(request: AqueousMassActionSystem):
            return (
                tuple((row.species_id, row.charge_number, row.elemental_composition) for row in request.species),
                tuple(
                    (row.reaction_id, tuple((term.species_id, term.coefficient) for term in row.terms))
                    for row in request.reactions
                ),
                tuple(
                    (row.constraint_id, tuple((term.species_id, term.coefficient) for term in row.terms))
                    for row in request.constraints
                ),
            )

        if any(topology(request) != topology(requests[0]) for request in requests[1:]):
            raise ValueError("scenario equations must retain exact species order, reaction stoichiometry and balance-constraint topology")
        return self


def _summarize_species(rows: list[dict]) -> list[dict]:
    species_ids = [row["species_id"] for row in rows[0]["species"]]
    envelope = []
    for species_id in species_ids:
        samples = []
        for scenario in rows:
            species = next(item for item in scenario["species"] if item["species_id"] == species_id)
            samples.append((scenario["scenario_id"], species))
        activity = [(sid, values["dimensionless_activity"]) for sid, values in samples]
        concentration = [(sid, values["concentration_mol_L"]) for sid, values in samples]
        min_activity = min(activity, key=lambda item: item[1])
        max_activity = max(activity, key=lambda item: item[1])
        min_concentration = min(concentration, key=lambda item: item[1])
        max_concentration = max(concentration, key=lambda item: item[1])
        envelope.append({
            "species_id": species_id,
            "dimensionless_activity_min": min_activity[1],
            "dimensionless_activity_min_scenario_id": min_activity[0],
            "dimensionless_activity_max": max_activity[1],
            "dimensionless_activity_max_scenario_id": max_activity[0],
            "concentration_min_mol_L": min_concentration[1],
            "concentration_min_scenario_id": min_concentration[0],
            "concentration_max_mol_L": max_concentration[1],
            "concentration_max_scenario_id": max_concentration[0],
            "concentration_span_mol_L": max_concentration[1] - min_concentration[1],
            "activity_span_dimensionless": max_activity[1] - min_activity[1],
        })
    return envelope


def evaluate_aqueous_mass_action_scenario_envelope(
    request: AqueousMassActionScenarioEnvelope,
) -> Calculation:
    """Solve each caller scenario independently and return its unweighted finite envelope."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    reviews = {
        "solution_identity_and_fixed_network_topology_reviewed": request.solution_identity_and_fixed_network_topology_reviewed,
        "finite_scenario_set_is_caller_owned_and_complete_for_comparison_reviewed": request.finite_scenario_set_is_caller_owned_and_complete_for_comparison_reviewed,
        "provider_family_and_revision_are_comparable_reviewed": request.provider_family_and_revision_are_comparable_reviewed,
        "no_probability_or_distribution_interpretation_reviewed": request.no_probability_or_distribution_interpretation_reviewed,
    }
    base = {
        "envelope_id": request.envelope_id,
        "input_sha256": input_digest,
        "solution_id": request.scenarios[0].request.solution_id,
        "activity_standard_state": request.scenarios[0].request.activity_standard_state,
        "fixed_topology_sha256": canonical_digest({
            "species": [row.model_dump(mode="json") | {"activity_coefficient": None, "initial_activity": None} for row in request.scenarios[0].request.species],
            "reactions": [row.model_dump(mode="json") | {"log10_equilibrium_constant": None} for row in request.scenarios[0].request.reactions],
            "constraints": [row.model_dump(mode="json") | {"target_mol_L": None, "residual_scale_mol_L": None} for row in request.scenarios[0].request.constraints],
        }),
        "scenario_set_kind": "finite_caller_declared_unweighted_cases",
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "completed_scenario_count": 0,
            "scenario_results": [],
            "missing_reviews": missing,
            "distribution_interpretation": "none",
        })

    computed = []
    for scenario in request.scenarios:
        result = aqueous_mass_action_speciation(scenario.request)
        scenario_input_digest = canonical_digest(scenario.request.model_dump(mode="json"))
        result_digest = canonical_digest(result.model_dump(mode="json"))
        row = {
            "scenario_id": scenario.scenario_id,
            "scenario_label": scenario.scenario_label,
            "request_sha256": scenario_input_digest,
            "result_sha256": result_digest,
            "status": result.status,
            "temperature_K": scenario.request.temperature_K,
            "activity_provider_id": scenario.request.activity_provider_id,
            "activity_provider_revision": scenario.request.activity_provider_revision,
            "activity_configuration_digest": scenario.request.activity_configuration_digest,
            "activity_record_digest": scenario.request.activity_record_digest,
            "equilibrium_provider_id": scenario.request.equilibrium_provider_id,
            "equilibrium_provider_revision": scenario.request.equilibrium_provider_revision,
            "equilibrium_configuration_digest": scenario.request.equilibrium_configuration_digest,
            "equilibrium_record_digest": scenario.request.equilibrium_record_digest,
            "evidence": [item.model_dump(mode="json") for item in scenario.request.evidence],
            "activity_coefficients_and_initial_activities": [
                {
                    "species_id": species.species_id,
                    "activity_coefficient": species.activity_coefficient,
                    "initial_activity": species.initial_activity,
                }
                for species in scenario.request.species
            ],
            "reaction_log10_equilibrium_constants": [
                {"reaction_id": reaction.reaction_id, "log10_equilibrium_constant": reaction.log10_equilibrium_constant}
                for reaction in scenario.request.reactions
            ],
            "constraint_targets_mol_L": [
                {"constraint_id": constraint.constraint_id, "target_mol_L": constraint.target_mol_L}
                for constraint in scenario.request.constraints
            ],
            "result_values": result.values,
        }
        if result.status != "computed":
            return Calculation(status=result.status, values=base | {
                "completed_scenario_count": len(computed),
                "computed_scenario_prefix": computed,
                "first_incomplete_scenario": row,
                "envelope": None,
                "failed_scenario_is_not_omitted": True,
            }, notes=(
                "A finite response envelope is withheld when any declared scenario does not compute; prior completed cases remain visible as an ordered prefix.",
            ))
        result_species = result.values.get("species")
        if not isinstance(result_species, list) or len(result_species) != len(scenario.request.species):
            return Calculation(status="out_of_scope", values=base | {
                "completed_scenario_count": len(computed),
                "computed_scenario_prefix": computed,
                "first_incomplete_scenario": row,
                "failure_reason": "computed_mass_action_result_lacks_complete_species_outputs",
            })
        row["species"] = result_species
        computed.append(row)

    envelope = _summarize_species(computed)
    for species in envelope:
        if not all(math.isfinite(value) for value in (
            species["dimensionless_activity_min"], species["dimensionless_activity_max"],
            species["concentration_min_mol_L"], species["concentration_max_mol_L"],
            species["activity_span_dimensionless"], species["concentration_span_mol_L"],
        )):
            return Calculation(status="out_of_scope", values=base | {
                "completed_scenario_count": len(computed),
                "scenario_results": computed,
                "failure_reason": "scenario_envelope_exceeds_finite_numeric_support",
            })
    return Calculation(values=base | {
        "completed_scenario_count": len(computed),
        "scenario_results": computed,
        "species_envelope": envelope,
        "minimum_maximum_basis": "exact_declared_finite_cases_only",
        "scenario_weights": None,
        "probability_or_confidence": None,
        "distribution_interpretation": "none",
        "not_inferred": ["intermediate_parameter_cases", "unprovided_topologies", "phase_selection", "kinetics", "precipitation", "corrosion_rate", "qualification"],
    }, notes=(
        "Each provided fixed-topology mass-action system is solved independently; no case is sampled, weighted, omitted or interpolated.",
        "The output extrema describe only the exact finite cases supplied by the caller, not a global uncertainty bound, distribution, probability, confidence interval or model qualification.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="chemistry.aqueous_mass_action_scenario_envelope",
        input_type=AqueousMassActionScenarioEnvelope,
        evaluator=evaluate_aqueous_mass_action_scenario_envelope,
        units={
            "scenario_results[].temperature_K": "K",
            "scenario_results[].result_values.species[].dimensionless_activity": "1",
            "scenario_results[].result_values.species[].concentration_mol_L": "mol/L",
            "species_envelope[].dimensionless_activity_min": "1",
            "species_envelope[].dimensionless_activity_max": "1",
            "species_envelope[].activity_span_dimensionless": "1",
            "species_envelope[].concentration_min_mol_L": "mol/L",
            "species_envelope[].concentration_max_mol_L": "mol/L",
            "species_envelope[].concentration_span_mol_L": "mol/L",
        },
        assumptions=(
            "Each complete scenario is caller-provided and solved independently by the existing fixed-topology aqueous mass-action solver.",
            "All scenarios share exact species order, charge/formula declarations, reaction stoichiometry, balance topology, solution identity, standard state, and provider family/revisions; numerical data such as temperature, fixed activities, equilibrium constants and constraint targets may differ.",
            "Report unweighted minima and maxima among exactly the supplied finite cases only; no sampling, probability, confidence, interpolation, omitted-case treatment or global bound is provided.",
            "A failed case prevents a complete envelope and is preserved with the successfully computed input-order prefix; no phase, kinetics, precipitation or corrosion is inferred.",
        ),
        source_ids=("caller_aqueous_mass_action_finite_scenario_envelope",),
        qualification="user_model",
    )]
